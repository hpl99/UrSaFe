# ADR-013: Offline Multilingual NLP Triage & Calibrated Probability Validation

## Status
Approved

## Context
Victims in distress communicate in colloquial, code-mixed language (English, Hindi, Hinglish). Cloud translation and large language models are inaccessible during total blackouts and cannot run on low-power smartphones. Furthermore, uncalibrated AI classifiers frequently report high confidence on false classifications, creating life-safety hazards.

## Decision
1. Implement an on-device offline triage NLP pipeline using character n-grams, phonetic transliteration matching, and a curated emergency ontology for English, Hindi, and Hinglish.
2. The pipeline extracts:
   - `category`: `FLOOD`, `FIRE`, `MEDICAL`, `TRAPPED`, `COLLAPSE`, `EVACUATION`
   - `people_affected`: Extracted count (e.g. "3 log" $\rightarrow 3$)
   - `urgency`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
   - `confidence`: Calibrated probability $[0.0, 1.0]$
   - `source_span`: Substring justifying extraction
3. Zero-Hallucination Policy: Confidence $< 0.65$ triggers `NEEDS_CLARIFICATION` prompts.
4. Scientific Probability Calibration: Models are evaluated using Brier Score and Expected Calibration Error (ECE) against labeled disaster datasets.

## Consequences
- **Positive:** Sub-10ms execution on smartphone CPUs; zero internet requirement; zero hallucinations.
- **Trade-off:** Vocabulary is bounded to emergency domains; open-ended conversation requires human intervention.
