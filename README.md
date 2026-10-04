# RiskLens categorizes public 10-K risk disclosures

PE6201 final project · Zhang Yizhuo · Group B · 4 October 2026.

RiskLens is a small, local reading assistant for a junior equity analyst. Paste an already selected English Item 1A paragraph; receive a category, disclosure severity, two summary sentences, a source quote and a review decision. It does not make investment recommendations or automatically extract an entire annual report.

## Run on another machine

1. Install Python 3.10 or later. No runtime pip packages are required.
2. Open a terminal in this folder and run `python app.py` (Windows: `py -3 app.py` or double-click `run.bat`).
3. Visit `http://127.0.0.1:8765/`. Offline keyword baseline works immediately.
4. For LLM mode, copy `config.example.json` to `config.local.json`. Set your own API key, HTTPS endpoint and model. For OpenRouter use `https://openrouter.ai/api/v1` and `openai/gpt-4o-mini`. Keep `structured: true`. The submitted package contains no key. Alternatively set `OPENAI_API_KEY`, `RISK_API_BASE`, `RISK_MODEL`, or point `RISK_CONFIG_FILE` at a private JSON file.
5. Click an example, choose the engine and Analyze. Review original text and evidence. Download JSON if desired.

For another provider update both token prices. A compatible chat-completions API and JSON schema support are needed; set `structured: false` only for JSON-object compatibility (local validation still runs). Unexpected failures are displayed instead of silently switching to rules. This prototype has a 60-second API timeout and no automatic retries. API usage incurs your provider's charges.

## Reproduce measured results

```
python data/generate_data.py
python evaluate.py --engine baseline --dataset synthetic
python evaluate.py --engine baseline --dataset real
python evaluate.py --engine llm --dataset synthetic
python evaluate.py --engine llm --dataset real
python -m unittest discover -s tests -v
```

The synthetic generator is deterministic; regeneration produces the same labels and SHA256. The real excerpts are included, so an evaluator need not download the PDF. To reproduce their extraction, optionally install `pypdf`, download Apple's PDF using the source link in `data/README.md`, and run `python data/prepare_real.py path/to/apple.pdf`.

Committed results are actual API runs, not mocked outputs. Re-running an LLM can change outputs despite temperature zero. Inputs and labels are frozen; prompt and data hashes identify the run. The main target was >85% raw category accuracy, with coverage reported alongside it. A diagnostic coverage target of >=80% on classifiable real excerpts was not met: the LLM accepted only 4/8 cases because its evidence failed checks on the others.

| Test | Majority class | Keyword raw accuracy | LLM raw accuracy | LLM accepted accuracy | LLM coverage |
|---|---:|---:|---:|---:|---:|
| Synthetic, 36 classified + 8 review cases | 16.67% | 69.44% | 100% | 100% | 36/44 = 81.82% |
| Apple, 8 classified excerpts | 25% | 50% | 100% | 100% | 4/8 = 50% |

Raw accuracy uses only classifiable cases and the candidate category before abstention. Accepted accuracy includes every accepted case (including an inappropriate answer on a review case). Coverage uses all cases. High accepted accuracy at low coverage is not sufficient for usefulness. Gold labels are AI-assisted, provisional and not an independent human benchmark. Do not infer deployment accuracy from this table.

## Files and module responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Loopback HTTP serving, Host/Origin checks, request size, single-flight/rate guardrails |
| `risklens.py` | Taxonomy, frozen keyword baseline, prompt/schema, API adapter, evidence/number validation |
| `index.html` | Input, examples, results, export and measured metrics; untrusted output uses textContent |
| `evaluate.py` | Frozen-case evaluation, confusion matrix, abstention metrics, errors, latency and cost |
| `data/` | Synthetic generator, labels, real excerpts, sources, extraction script and demo inputs |
| `evals/` | Evaluation definitions and per-case measured outputs |
| `docs/PRODUCT.md` | Persona, input/output, architecture, build-vs-buy, targets and actuals, risks |
| `tests/` | Regression tests of acceptance checks and metric denominators |

See `docs/PRODUCT.md`, `data/README.md` and `evals/README.md` for the product, data and evaluation explainers. Development and document/video preparation used AI assistance; see `docs/AI_ASSISTANCE.md`. I make no claim that an unverified Zapier trial, independent hand labelling, or a 70% time-saving experiment occurred.

## Limitations and troubleshooting

Use public information only; LLM text is sent to OpenRouter and its upstream model provider. No confidential uploads, no trading signals, no calibrated probabilities. The model may classify correctly while quoting incorrectly. Quotes and numeric checks only cover specific failure modes; semantic distortion can still pass. Humans must confirm accepted summaries. Severity is disclosure wording, not economic probability or a validated financial rating.

If the port is busy, stop another RiskLens process and try again. If a key is missing, baseline remains available. If the API fails, check endpoint, credits, model and network connectivity. If results need human review, read the original paragraph rather than treating the candidate category as accepted.
