"""
Unit Tests for Offline Multilingual Triage NLP and Probability Calibration
"""
import pytest
from services.nlp.triage import OfflineTriageClassifier
from services.nlp.calibration import CalibrationEvaluator

def test_hinglish_code_mixed_triage():
    classifier = OfflineTriageClassifier()
    text = "paani aa raha hai ghar mein bahut tez bachao chhat par 4 log phanse hain"

    res = classifier.classify(text)
    assert res.category == "FLOOD"
    assert res.urgency == "CRITICAL"
    assert res.people_affected == 4
    assert res.detected_language == "hinglish"
    assert res.confidence >= 0.70
    assert res.needs_clarification is False
    assert res.source_span in ("paani", "paani aa raha hai")

def test_hindi_devanagari_triage():
    classifier = OfflineTriageClassifier()
    text = "सिलेंडर विस्फोट से भयंकर आग लग गई है तुरंत मदद चाहिए 3 लोग अंदर फंसे हैं"

    res = classifier.classify(text)
    assert res.category == "FIRE"
    assert res.urgency == "CRITICAL"
    assert res.people_affected == 3
    assert res.detected_language == "hi"
    assert res.confidence >= 0.70
    assert res.needs_clarification is False

def test_english_triage_extraction():
    classifier = OfflineTriageClassifier()
    text = "Wall collapsed after earthquake, 2 people trapped under heavy rubble urgently"

    res = classifier.classify(text)
    assert res.category in ("COLLAPSE", "TRAPPED")
    assert res.urgency == "CRITICAL"
    assert res.people_affected == 2
    assert res.detected_language == "en"
    assert res.confidence >= 0.70
    assert res.needs_clarification is False

def test_zero_hallucination_ambiguity_clarification():
    classifier = OfflineTriageClassifier()
    # Vague message with no clear category
    text = "yahan bahut mushkil hai please help"

    res = classifier.classify(text)
    assert res.needs_clarification is True
    assert res.clarification_prompt != ""
    assert "batayein" in res.clarification_prompt or "clarify" in res.clarification_prompt

def test_calibration_evaluator_metrics():
    # Simulated model confidence outputs vs ground truth outcomes
    predictions = [0.90, 0.85, 0.75, 0.60, 0.40, 0.20, 0.10, 0.95]
    ground_truth = [1, 1, 1, 0, 0, 0, 0, 1]

    brier = CalibrationEvaluator.calculate_brier_score(predictions, ground_truth)
    assert 0.0 <= brier <= 0.25 # Well-calibrated model produces low Brier score

    ece_res = CalibrationEvaluator.calculate_expected_calibration_error(
        predictions, ground_truth, num_bins=4
    )
    assert "ece" in ece_res
    assert ece_res["ece"] >= 0.0
    assert len(ece_res["bins"]) == 4
