# Evaluation explanation

All results in `results/` were executed on 4 October 2026. `metrics.json` records UTC timestamp, model, prompt hash, data hash, denominators, confusion matrices, API errors, latency and token-price cost. Per-case files include the input, gold label, candidate, accepted category, check failures and provider usage. No mocked LLM outputs or omitted failed calls are included.

## Definitions

- **Raw category accuracy:** correct candidate categories / gold-classifiable cases (36 synthetic or 8 real). This is measured before abstention.
- **Majority baseline:** always predict the most frequent category among those classifiable cases. Ties do not affect the score.
- **Accepted accuracy:** correct accepted outputs / all accepted outputs. An answer to a gold-review case is incorrect.
- **Coverage and abstention rate:** accepted / all cases and reviewed / all cases. Their sum is 100%.
- **Correct accepted recall:** correctly accepted classifiable cases / all gold-classifiable cases. Correct candidates rejected for bad evidence reduce recall.
- **Macro accepted recall:** mean accepted recall across the six represented categories.
- **Review precision:** gold-review cases / all abstentions. **Review recall:** gold-review cases caught / all gold-review cases. On the real set there are no gold-review cases, so recall is N/A.
- **Error-catch precision (abstention accuracy):** abstentions whose candidate would be wrong / all abstentions. **Error-catch recall:** those intercepted candidate errors / all candidate errors. Cases without a gold category count as wrong candidates. N/A when there are no relevant errors/denominators.
- **schema_valid_pct:** historical field name for ALL local output-contract checks passing, including semantic evidence/numeric checks and review reason, not merely parseable JSON or provider schema conformance. **evidence_valid_pct:** quote is a normalized contiguous input substring of 12-220 characters.
- **Wilson interval:** approximate 95% binomial interval for raw accuracy. It quantifies small sample uncertainty, not annotation bias or correlated-data uncertainty.

## Actual findings

Synthetic: the keyword candidate was correct on 25/36 (69.44%) versus 36/36 for the LLM. Keyword abstention was 19/44 (43.18%), review precision 7/19 (36.84%) and review recall 7/8 (87.5%). LLM abstention was 8/44 (18.18%), review precision/recall 8/8. However 3/44 LLM outputs required review but supplied an empty reason, causing a fail-closed rejection. All three are committed and discussed, not repaired or hidden. Local output-contract pass rate was 41/44 (93.18%).

Real: keyword candidate accuracy was 4/8 (50%), majority 2/8 (25%), LLM candidate accuracy 8/8 (100%; Wilson interval 67.56%-100%). The LLM accepted only 4/8; other candidates were correctly classified but failed quote checks. AAPL-01 and AAPL-07 paraphrased/shortened quotations, so they were not exact source substrings. AAPL-03 and AAPL-08 quotes exceeded 220 characters. Error-catch precision was 0/4: none of these abstentions intercepted a wrong CATEGORY, although they blocked defective EVIDENCE. This metric distinction matters. Correct accepted recall was 4/8, so the coverage goal failed.

Total estimated token cost across the 52 LLM evaluation calls: $0.00578025. Mean synthetic latency was 1.768 seconds; real latency 1.954 seconds. Provider-reported `usage.cost` is preserved for audit and matched the configured token-rate estimates on these calls. Baseline latency is not instrumented (stored zero); do not interpret that as measured zero execution time. Cost excludes human time, credits/purchase fees, document/video preparation and this assistant's usage.

## Acceptance targets and scope

Target raw accuracy >85%, zero accepted output-contract failures, and review precision/recall >=80% on the synthetic adversarial slice. A diagnostic useful-coverage goal is >=80% of classifiable real excerpts. Raw target passed in these small tests; real coverage failed. Guardrails blocked invalid outputs, but summary semantic fidelity, severity validity and analyst time saving were not independently measured. There is no full-report extraction-recall score because full-report extraction is outside this prototype's scope.

No numerical model confidence threshold is used. The rejected 0.7 self-confidence gate was uncalibrated. Review now uses an explicit model decision plus deterministic validity checks, which still needs a domain-reviewed validation set. There is no trained model, retrieval index, LLM judge, confidence calibration or model-based grading loop.

Development tuning consisted of making the taxonomy/routing explicit and enforcing quote, field, number and materiality checks before the frozen run. No post-test threshold optimization was performed. No heading-present versus heading-stripped performance experiment is claimed: headings are excluded by construction. This avoids one leakage route but does not rule out pretrained-model familiarity with Apple filings.
