"""Extract eight fixed short, attributed excerpts from Apple's 2025 10-K.

Usage: python data/prepare_real.py path/to/downloaded/apple.pdf
Requires optional pypdf. The PDF is intentionally not redistributed.
Line ranges are fixed to the pypdf extraction of PDF pages 6-18 (zero-based 5:18).
Gold labels are AI-assisted provisional annotations requiring human review.
"""
import hashlib
import json
import sys
from pathlib import Path
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
URL = "https://s2.q4cdn.com/470004039/files/doc_financials/2025/ar/_10-K-2025-As-Filed.pdf"
# Inclusive one-based line numbers, selected before LLM evaluation.
RANGES = [(116,120,"Market",5), (125,128,"Financial",5),
          (167,169,"Environmental",6), (177,179,"Operational",6),
          (195,198,"Market",7), (424,425,"Cybersecurity",11),
          (462,465,"LegalRegulatory",12), (633,636,"Financial",15)]


def main():
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    reader = PdfReader(path)
    lines = "\n".join(page.extract_text() for page in reader.pages[5:18]).splitlines()
    rows = []
    for i,(start,end,category,page) in enumerate(RANGES):
        text = " ".join(" ".join(lines[start-1:end]).split())
        # The last extracted line can begin the next sentence; keep complete sentences.
        text = text[:text.rfind(".")+1]
        assert text.endswith(".") and len(text) > 50
        rows.append({"id":"AAPL-%02d"%(i+1),"text":text,"gold_category":category,
                     "gold_review":False,"split":"test","source":"Apple 2025 Form 10-K",
                     "source_url":URL,"printed_page":page,
                     "label_provenance":"AI-assisted provisional label; not independently human-validated"})
    (HERE / "real.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
    (HERE / "real_source.json").write_text(json.dumps({"url":URL,"sha256":hashlib.sha256(raw).hexdigest(),"pdf_pages":len(reader.pages),"extraction":"pypdf pages[5:18], whitespace normalized", "ranges":RANGES},indent=2),encoding="utf-8")
    demo = [{"name":"Apple 2025 - "+r["gold_category"]+" - "+r["id"],"text":r["text"],"source":"Apple 2025 Form 10-K, printed page %s. %s"%(r["printed_page"],URL)} for r in rows]
    synthetic = json.loads((HERE / "synthetic.json").read_text())
    demo += [{"name":"Synthetic - needs human review","text":synthetic[-8]["text"],"source":"AI-authored synthetic insufficient-context test"},
             {"name":"Synthetic - prompt injection","text":synthetic[-5]["text"],"source":"AI-authored synthetic adversarial test"}]
    (HERE / "demo.json").write_text(json.dumps(demo,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Prepared",len(rows),"real-source cases. Inspect text and labels before evaluating.")
    for r in rows:
        print(r["id"],r["gold_category"],r["text"][:95].encode("ascii","replace").decode())

if __name__ == "__main__":
    main()
