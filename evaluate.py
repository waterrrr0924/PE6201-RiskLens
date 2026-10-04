"""Reproducible category/abstention evaluation; errors are never dropped.

Raw accuracy counts best candidates on classifiable rows before abstention.
Accepted accuracy excludes review cases; coverage/recall prevent cherry-picking.
Review precision is agreement with gold-review labels. Error-catch precision is
the fraction of abstentions whose counterfactual candidate would be wrong.
"""
import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from risklens import ROOT, TAXONOMY, analyze, config


def percent(a, b):
    return round(100*a/b, 2) if b else None


def wilson(k, n):
    if not n:
        return None
    z = 1.96
    p = k/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [round(100*(center-half),2), round(100*(center+half),2)]


def score(rows):
    valid = [r for r in rows if not r["gold_review"]]
    accepted = [r for r in rows if not r["prediction"]["needs_review"]]
    abstained = [r for r in rows if r["prediction"]["needs_review"]]
    raw_correct = lambda r: r["gold_category"] is not None and r["prediction"].get("category") == r["gold_category"]
    accepted_correct = [r for r in accepted if raw_correct(r)]
    gold_review = sum(r["gold_review"] for r in rows)
    tp = sum(r["gold_review"] for r in abstained)
    confusion = {g: {p: 0 for p in [*TAXONOMY, "REVIEW", "ERROR"]} for g in [*TAXONOMY, "REVIEW"]}
    for r in rows:
        g = r["gold_category"] or "REVIEW"
        p = "ERROR" if r["prediction"].get("error") else ("REVIEW" if r["prediction"]["needs_review"] else r["prediction"]["category"])
        confusion[g][p] += 1
    recalls = []
    for cat in TAXONOMY:
        cases = [r for r in valid if r["gold_category"] == cat]
        if cases:
            recalls.append(sum(raw_correct(r) and not r["prediction"]["needs_review"] for r in cases)/len(cases))
    majority = Counter(r["gold_category"] for r in valid)
    return {
        "n": len(rows), "classifiable_n": len(valid), "gold_review_n": gold_review,
        "raw_accuracy_pct": percent(sum(raw_correct(r) for r in valid), len(valid)),
        "raw_accuracy_wilson_95_pct": wilson(sum(raw_correct(r) for r in valid), len(valid)),
        "majority_class_accuracy_pct": percent(max(majority.values(),default=0),len(valid)),
        "selective_accuracy_pct": percent(len(accepted_correct),len(accepted)),
        "accepted_n": len(accepted), "abstained_n": len(abstained),
        "coverage_pct": percent(len(accepted),len(rows)),
        "correct_accepted_recall_pct": percent(len(accepted_correct),len(valid)),
        "macro_accepted_recall_pct": round(100*sum(recalls)/len(recalls),2) if recalls else None,
        "abstention_rate_pct": percent(len(abstained),len(rows)),
        "review_precision_pct": percent(tp,len(abstained)),
        "review_recall_pct": percent(tp,gold_review),
        "error_catch_precision_pct": percent(sum(not raw_correct(r) for r in abstained),len(abstained)),
        "error_catch_recall_pct": percent(sum(not raw_correct(r) for r in abstained),sum(not raw_correct(r) for r in rows)),
        "schema_valid_pct": percent(sum(r["prediction"].get("schema_valid",False) for r in rows),len(rows)),
        "evidence_valid_pct": percent(sum(r["prediction"].get("evidence_valid",False) for r in rows),len(rows)),
        "api_errors": sum(bool(r["prediction"].get("error")) for r in rows),
        "total_cost_usd": round(sum(r["prediction"].get("cost_usd",0) for r in rows),8),
        "mean_latency_seconds": round(sum(r["prediction"].get("latency_seconds",0) for r in rows)/len(rows),3),
        "confusion_matrix": confusion,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=["baseline", "llm"], default="baseline")
    parser.add_argument("--dataset", choices=["synthetic", "real"], default="synthetic")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test")
    args = parser.parse_args()
    path = ROOT / "data" / (args.dataset + ".json")
    raw = path.read_bytes()
    rows = json.loads(raw)
    rows = [r for r in rows if args.split == "all" or r["split"] == args.split]
    if args.engine == "llm" and not config().get("api_key"):
        raise SystemExit("No API key. No LLM evaluation was run or fabricated.")
    if not rows:
        raise SystemExit("No cases for requested split")
    outputs = []
    for i, r in enumerate(rows):
        try:
            prediction = analyze(r["text"],args.engine)
        except Exception as exc:
            prediction = {"needs_review":True,"category":None,"error":str(exc),"schema_valid":False,"evidence_valid":False}
        outputs.append({**r,"prediction":prediction})
        print("%s/%s %s %s" % (i+1,len(rows),r["id"],"ERROR" if prediction.get("error") else "ok"),flush=True)
        if prediction.get("error") and args.engine == "llm" and i == 0:
            raise SystemExit("First API call failed; evaluation stopped to avoid repeated failures. " + prediction["error"])
    name = "%s_%s_%s" % (args.engine,args.dataset,args.split)
    resultdir = ROOT / "evals/results"
    resultdir.mkdir(parents=True,exist_ok=True)
    (resultdir / (name+"_cases.json")).write_text(json.dumps(outputs,indent=2),encoding="utf-8")
    metrics = score(outputs)
    metrics.update({"dataset_sha256":hashlib.sha256(raw).hexdigest(),"engine":args.engine,"model":config()["model"] if args.engine=="llm" else None,"run_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"prompt_sha256":hashlib.sha256(__import__('risklens').PROMPT.encode()).hexdigest()})
    mpath = resultdir / "metrics.json"
    allmetrics = json.loads(mpath.read_text()) if mpath.exists() else {}
    allmetrics[name] = metrics
    mpath.write_text(json.dumps(allmetrics,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in metrics.items() if k!="confusion_matrix"},indent=2))

if __name__ == "__main__":
    main()
