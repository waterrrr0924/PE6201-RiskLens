# RiskLens product documentation

## Persona and value

Alex is a junior equity research analyst reading a public filing before a review meeting. Alex knows financial terminology but does not program. The task is to locate the dominant risk and a short evidence-backed explanation in an already selected disclosure. The interface reduces the distance between a paragraph and a reviewable structured output. The actual benefit is an organization aid; hours saved have not been measured. One paragraph needs one call; a batch is limited to six paragraphs to make spend and failures visible.

## Input and output

Input: public English Item 1A text, 20-6000 characters per paragraph, up to six blank-line-separated paragraphs. It is the user's responsibility to select Item 1A and preserve paragraph context. PDF/OCR and automatic complete-10-K extraction, historical comparisons, multilingual support, market forecasting and investment advice are outside scope.

Output: dominant category, severity of disclosure language (High/Medium/Unspecified), two summary sentences, a verbatim evidence quote, needs_review plus reason, accepted_category (null if reviewed), local-check errors, engine, latency, token usage and cost. A candidate category remains available in JSON solely for audit/counterfactual evaluation. The UI shows no accepted category on a review case. Invalid summaries are not shown as accepted content.

## Fixed taxonomy

| Category | Dominant initiating cause | Boundary |
|---|---|---|
| Operational | Suppliers, manufacturing, logistics, people, defects, continuity | Disaster cause goes to Environmental; attacks go to Cybersecurity |
| Cybersecurity | Unauthorized system access, malware, confidential-data theft | Consequent penalties do not change the initiating cause |
| LegalRegulatory | Litigation, government action, tax, compliance, IP disputes | Financial loss alone does not make a risk Financial |
| Financial | Funding, liquidity, credit/default, FX, instruments | Macroeconomic demand effects belong to Market |
| Market | Competition, demand, price pressure, macroeconomic sales exposure | Supply production problems belong to Operational |
| Environmental | Climate, natural disasters, water/weather constraints | Environmental compliance enforcement belongs to LegalRegulatory |

Equally dominant risks, absent context, non-risk text and model-directed instructions require review. Severity is expressly not calibrated likelihood or an investment rating. High requires explicit material adverse wording in the input. Lower severity classifications have no independent label validation.

## Architecture

```
Public risk text --> Local browser --> Input/blank-line rules
                                          |
                            +-------------+-------------+
                            |                           |
                    Keyword baseline              Prompt + JSON schema
                                                        |
                                              OpenRouter / GPT-4o-mini
                            |                           |
                            +--------> Local checks <----+
                                         |
                              Accept or human review
                                         |
                              Evidence + JSON export

Frozen data + gold labels --> evaluate.py --> per-case logs + metrics
```

`architecture.png` is the corresponding box diagram. The LLM is the only external intelligence; no agent/tool loop or RAG is needed because the paragraph is already in the request. Deterministic code owns parsing boundaries, cost arithmetic, output validation and evaluation. OpenRouter serves the model; it does not host this app.

## Build versus buy by layer

| Layer | Decision | Reason and trade-off |
|---|---|---|
| Interface and serving | Own HTML and Python loopback server | No deployment/account/database overhead; single-user prototype only |
| Orchestration | Own one-call pipeline | Transparent checks and spend; explicit errors, no retries |
| Model | Rent OpenAI GPT-4o-mini through OpenRouter | Low-cost semantic classification; vendor/network dependence |
| Data and retrieval | Own fixed fixtures and source extractor; no retrieval | Auditable input scope; cannot search full filings |
| Evaluation | Own script, labelled files, confusion matrices | No opaque LLM judge; labels still need independent human review |
| Observability | Own local per-case metrics | Auditable spend/failures; no continuous production monitoring |

Straight-to-code was chosen because schema, key handling, fail-closed checks and eval denominators fit a small standard-library program. The old proposal mentioned a Zapier experiment, but no trial evidence is available; this submission does not claim that experiment occurred. Low-code is optional. Building a production-grade service or training narrow ML would take longer; the chosen prototype needs only Python and an optional key.

## Metrics targeted and reached

| Metric | Target | Actual |
|---|---|---|
| Raw categorization accuracy | >85% | LLM 36/36 synthetic and 8/8 real; label/sample caveats apply |
| Correct accepted recall on real excerpts | >=80% | 4/8 = 50%, NOT met |
| Accepted local-contract violations | 0 | 0 by fail-closed construction; does not guarantee semantic correctness |
| Synthetic review precision / recall | >=80% each | 8/8 and 8/8 |
| Estimated evaluation API cost | <$1 | $0.00578025 for 52 calls |

See evals/README.md for all denominators and keyword/majority baselines. The original time-saving claim was removed. Illustrative projection: 500 calls at 1000 input + 250 output tokens each cost $0.15 at $0.15/$0.60 per million; at 5000 input + 250 output tokens cost $0.45. This is a scenario, not a measured 500-paragraph workload, and excludes other fees/labour. Rates checked 4 October 2026: https://openrouter.ai/openai/gpt-4o-mini and https://developers.openai.com/api/docs/models/gpt-4o-mini.

## Risks paired with implemented mitigations

| Risk | Implemented mitigation | Residual limitation |
|---|---|---|
| Hallucinated evidence or figures | Exact normalized quote substring check; input-number presence check | A genuine quote can support a misleading summary; number-presence is not numeric entailment |
| Silent wrong category or materiality | Original text, quote and candidate audit; materiality wording check for High | No complete automated semantic correctness detector; human must check all accepted outputs |
| Over-reliance | Human-review state and source-first presentation; intended/non-use stated | Warning alone is not sufficient; enforced rejection is the concrete control |
| Prompt injection | Instructions separated from untrusted JSON text; no model tools or execution; injection test | Model can still mishandle text; semantic attacks require more tests |
| Private data/key leakage | Local key file ignored/excluded; loopback binding; Host/Origin checks; no request-text logging | Pasted text goes to external inference providers; use public disclosures only |
| Runaway calls or unsupported input | Six-paragraph cap, 6000-char cap, max output tokens, single-flight and two-second request interval | No account-wide spending cap implemented |
| Misleading evaluation | Frozen labels/hashes, errors retained, coverage and caveats | AI-assisted labels and one issuer are not independent evidence |

Responsible-use design relates to OWASP LLM prompt-injection/improper-output-handling concerns and the IMDA Model AI Governance Framework's human involvement and transparency themes. This is a design reference, not a legal compliance certification. No trading decisions, personalized investment recommendations, or financial risk ratings are supported.
