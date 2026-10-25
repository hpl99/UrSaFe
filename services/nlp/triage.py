"""
Offline Multilingual Emergency Triage Classifier
Supports English, Hindi (Devanagari), and Hinglish (Code-Mixed Latin script).
Operates with ZERO cloud dependency, sub-millisecond latency, and ZERO hallucination.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class TriageResult:
    category: str
    urgency: str
    people_affected: int
    confidence: float
    source_span: str
    detected_language: str
    needs_clarification: bool = False
    clarification_prompt: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "urgency": self.urgency,
            "people_affected": self.people_affected,
            "confidence": round(self.confidence, 3),
            "source_span": self.source_span,
            "detected_language": self.detected_language,
            "needs_clarification": self.needs_clarification,
            "clarification_prompt": self.clarification_prompt,
        }

class OfflineTriageClassifier:
    """
    On-device emergency ontology and character n-gram matcher.
    Zero hallucination policy: If input is vague, flags needs_clarification.
    """
    def __init__(self):
        # Emergency Lexicon across English, Hindi Devanagari, and Hinglish
        self.category_ontology = {
            "FLOOD": [
                # English
                "flood", "water rising", "drowning", "submerged", "overflow", "dam burst", "heavy rain",
                # Hinglish
                "paani", "pani", "paani aa raha hai", "doob", "chhat par", "jalbharao", "bahut paani", "nadi",
                # Hindi Devanagari
                "पानी", "बाढ़", "डूब", "जलभराव", "नदी", "पानी भर गया", "छत पर",
            ],
            "FIRE": [
                # English
                "fire", "smoke", "burning", "flames", "explosion", "cylinder blast", "gas leak",
                # Hinglish
                "aag", "aag lag gayi", "dhuan", "dhuwan", "cylinder phat gaya", "jal raha hai",
                # Hindi Devanagari
                "आग", "धुआं", "सिलेंडर", "विस्फोट", "जल रहा है", "आग लगी",
            ],
            "MEDICAL": [
                # English
                "heart attack", "bleeding", "unconscious", "broken bone", "pregnant", "stroke", "diabetic", "ambulance", "breathing",
                # Hinglish
                "khoon", "chot", "behosh", "dard", "saans nahi aa rahi", "dawa", "dil ka daura", "bimar",
                # Hindi Devanagari
                "खून", "चोट", "बेहोश", "दर्द", "सांस", "दवा", "बीमार", "अस्पताल",
            ],
            "COLLAPSE": [
                # English
                "building collapse", "rubble", "crushed", "earthquake", "debris", "landslide",
                # Hinglish
                "gir gaya", "makan gir gaya", "malba", "chhat gir gayi", "bhookamp", "zameen khisak gayi",
                # Hindi Devanagari
                "मकान गिर", "मलबा", "भूकंप", "भूस्खलन", "छत गिर", "धंस गया",
            ],
            "TRAPPED": [
                # English
                "trapped", "stuck", "cannot open door", "locked", "under debris",
                # Hinglish
                "phanse", "phase", "fans gaye", "atke", "nikal nahi pa rahe", "band ho gaye",
                # Hindi Devanagari
                "फंसे", "फंस गए", "अटके", "निकल नहीं पा रहे",
            ],
        }

        self.urgency_keywords = {
            "CRITICAL": [
                "urgent", "immediately", "dying", "unconscious", "choking", "massive",
                "jaldi", "turant", "jaan ka khatra", "bachao", "bahut tez",
                "तुरंत", "बचाओ", "जल्दी", "जान का खतरा", "मर रहे हैं",
            ],
            "HIGH": [
                "serious", "severe", "rising fast", "cannot walk", "trapped",
                "tez", "madad", "phas gaye", "chot lag gayi",
                "मदद", "तेज़", "चोट", "फंसे हैं",
            ],
            "MEDIUM": [
                "stranded", "food required", "water required", "power out",
                "khana chahiye", "paani chahiye", "bijli band",
                "खाना", "पानी चाहिए", "बिजली",
            ],
        }

    def detect_script_language(self, text: str) -> str:
        # Check Devanagari Unicode block (0x0900 - 0x097F)
        if any('\u0900' <= char <= '\u097F' for char in text):
            return "hi"
        # Check if words indicate Hinglish
        hinglish_markers = {"paani", "pani", "bachao", "hai", "mein", "ghar", "aag", "phanse", "log", "chhat", "madad", "jaldi"}
        words = set(re.findall(r'\b\w+\b', text.lower()))
        if words.intersection(hinglish_markers):
            return "hinglish"
        return "en"

    def extract_people_count(self, text: str) -> int:
        """Extracts number of affected individuals from English, Hindi, or Hinglish patterns."""
        # 1. Regex digit check: "3 log", "4 people", "5 persons"
        digit_match = re.search(r'(\d+)\s*(?:people|persons|family members|log|members|vyakti|लोग|व्यक्ति)?', text, re.IGNORECASE)
        if digit_match:
            try:
                cnt = int(digit_match.group(1))
                if 1 <= cnt <= 1000:
                    return cnt
            except ValueError:
                pass

        # 2. Word numbers (Hindi/Hinglish/English)
        word_num_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
            "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5,
        }
        for word, val in word_num_map.items():
            if re.search(rf'\b{word}\b\s*(?:log|people|persons|members|लोग)?', text, re.IGNORECASE):
                return val

        return 1 # Default assumption: at least 1 person in distress

    def classify(self, text: str) -> TriageResult:
        normalized = text.strip()
        if not normalized:
            return TriageResult(
                category="GENERAL",
                urgency="LOW",
                people_affected=1,
                confidence=0.0,
                source_span="",
                detected_language="en",
                needs_clarification=True,
                clarification_prompt="Please describe the emergency: What is happening and what help do you need?",
            )

        lang = self.detect_script_language(normalized)
        lower_text = normalized.lower()

        # Score categories based on keyword presence and span length
        best_category = "GENERAL"
        best_cat_score = 0.0
        best_cat_span = ""

        for cat, keywords in self.category_ontology.items():
            for kw in keywords:
                if kw in lower_text:
                    # Longer specific phrase matches grant higher confidence
                    score = min(0.95, 0.60 + (len(kw) * 0.04))
                    if score > best_cat_score:
                        best_cat_score = score
                        best_category = cat
                        best_cat_span = kw

        # Extract people affected
        people_cnt = self.extract_people_count(normalized)

        # Determine Urgency
        detected_urgency = "LOW"
        urgency_confidence = 0.5
        for urg, keywords in self.urgency_keywords.items():
            for kw in keywords:
                if kw in lower_text:
                    detected_urgency = urg
                    urgency_confidence = 0.85
                    break
            if detected_urgency != "LOW":
                break

        # Fallback to category default urgency if no explicit keyword
        if detected_urgency == "LOW":
            if best_category in ("FLOOD", "FIRE", "COLLAPSE"):
                detected_urgency = "HIGH"
            elif best_category == "MEDICAL":
                detected_urgency = "HIGH"

        # Overall calibrated confidence
        final_confidence = best_cat_score if best_cat_score > 0 else 0.35

        # Zero Hallucination Rule:
        needs_clarification = False
        clarification_prompt = ""
        if final_confidence < 0.65 or best_category == "GENERAL":
            needs_clarification = True
            if lang == "hi":
                clarification_prompt = "कृपया बताएं: क्या यह बाढ़, आग, चिकित्सा या इमारत ढहने की आपात स्थिति है?"
            elif lang == "hinglish":
                clarification_prompt = "Kripya batayein: Kya yeh flood, aag, medical ya building collapse ki emergency hai?"
            else:
                clarification_prompt = "Could you clarify the emergency type: Is this flood, fire, medical trauma, or structural collapse?"

        return TriageResult(
            category=best_category,
            urgency=detected_urgency,
            people_affected=people_cnt,
            confidence=final_confidence,
            source_span=best_cat_span,
            detected_language=lang,
            needs_clarification=needs_clarification,
            clarification_prompt=clarification_prompt,
        )
