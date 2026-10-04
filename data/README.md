# Data explanation

## Synthetic cases

`synthetic.json` contains 56 fixed AI-authored cases. There are 8 distinct texts for each of six categories (48), plus 8 cases requiring review. The first 2/category are development cases (12); the test slice has 36 classifiable and 8 review cases (44). Short and longer descriptions, indirect phrasing, operational consequences, non-risk text, mixed causes, insufficient context and prompt injection are represented.

`generate_data.py` includes the literal texts and gold labels. It does not call a model; regeneration is deterministic. Labels were committed before the first evaluation, not changed to match predictions. `synthetic.sha256` records the complete file hash. No category names, labels or IDs are passed to the tested LLM: only each `text` string is sent.

These inputs are AI-generated, and their authorship overlaps with the prompt/system design. The split prevents directly reusing development examples, but is not an independently authored holdout. The 100% raw LLM score is diagnostic evidence only. Synthetic data cannot establish performance across real issuers or long disclosures. The original AI-authored proposal's 20-company/500-paragraph dataset was a plan, not an acquired dataset.

## Real-source sanity check

`real.json` contains eight short, complete-sentence excerpts from Apple Inc.'s 2025 Form 10-K, Item 1A, with original source URL and printed page per row. Source PDF has 80 physical pages. Printed pages differ from PDF page indices. Categories are 2 Market, 2 Financial and one each Operational, Environmental, Cybersecurity and LegalRegulatory. There are no gold-review cases; review recall is therefore undefined, not zero.

Source: https://s2.q4cdn.com/470004039/files/doc_financials/2025/ar/_10-K-2025-As-Filed.pdf

SEC copy: https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm

`prepare_real.py` documents fixed line ranges, whitespace normalization, removal of a trailing unfinished sentence, source digest and page references. Only body text is classified: original category/section headings are removed to avoid obvious heading leakage. `real_source.json` records extraction provenance. The eight gold categories were assigned with AI assistance using the dominant initiating-cause rule before the real LLM run. They have not been independently checked by a domain expert. The real text is external to the synthetic author, but this is not an independently labelled benchmark.

The complete PDF is not bundled. Public availability of issuer-authored material does not automatically mean public-domain licensing. These short attributed excerpts are included for classroom analysis; no broad redistribution licence is asserted. For broader distribution, use your own permissioned text or retain only a downloader and source references. The newly authored synthetic dataset can be regenerated freely for this project. No personal/confidential data was collected; Singapore personal-data consent requirements were not invoked by this public-text dataset.

## Label policy

Use the taxonomy in `docs/PRODUCT.md`. Classify the initiating cause: cybersecurity is not LegalRegulatory merely because fines follow; foreign-exchange exposure is Financial rather than Market; natural-disaster damage is Environmental rather than Operational. If two causes are expressly equally dominant, there is insufficient context, the text is not a risk, or it contains model-directed instructions, gold_review=true and gold_category=null. No gold severity or summary-fidelity labels are claimed.

Recommended next validation: have the student review all 8 real labels and at least 10 synthetic labels, record disagreements before any new model run, then obtain independently labelled disclosures from additional issuers. Do not retrospectively relabel committed cases after seeing scores.
