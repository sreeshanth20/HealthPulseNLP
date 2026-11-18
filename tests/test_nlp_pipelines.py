"""Unit tests for the NLP pipelines (no DB needed)."""

from __future__ import annotations

from ml.classification.complaint_classifier import ComplaintClassifier
from ml.classification.urgency import score_urgency
from ml.extraction.location_extractor import extract_location
from ml.extraction.medical_ner import MedicalNER
from ml.inference.pipeline import get_pipeline
from ml.preprocessing.gazetteer import haversine_km
from ml.preprocessing.lexicons import SYMPTOM_LEXICON
from ml.preprocessing.text import detect_language, normalize_text, romanize_to_english
from ml.summarization.summarizer import summarize, summarize_medical_report


class TestPreprocessing:
    def test_normalize(self):
        assert normalize_text("  Hello   WORLD  ") == "hello world"

    def test_language_detection(self):
        assert detect_language("The tap water smells bad") == "en"
        assert detect_language("पानी में बदबू आ रही है") == "hi"
        assert detect_language("நீர் மாசு அதிகம்") == "ta"

    def test_romanized_mapping(self):
        out = romanize_to_english("pani me badboo hai, bukhar ho raha")
        assert "water" in out and "smell" in out and "fever" in out

    def test_haversine_sane(self):
        # ~1.5 km apart within the demo city
        d = haversine_km(17.6968, 83.2204, 17.6968, 83.2404)
        assert 1.0 < d < 3.0


class TestComplaintClassifier:
    def test_trained_artifact_loaded(self):
        clf = ComplaintClassifier()
        assert clf.method in ("tfidf-logreg", "hf-transformer")

    def test_classification_across_categories(self):
        clf = ComplaintClassifier()
        cases = {
            "Tap water smells like sewage and is muddy in Millbrook": "water_contamination",
            "Garbage not collected for two weeks, bins overflowing": "garbage_sanitation",
            "Choked drain with stagnant water and sewage overflow": "drainage_sewage",
            "Severe mosquito problem, larvae in the drain, dengue": "mosquito menace",
            "Deep pothole on the road, accidents reported": "road_infrastructure",
        }
        for text, expected in cases.items():
            assert clf.predict(text)["label"] == expected, text
            assert clf.predict(text)["confidence"] > 0.3

    def test_confidence_scores_sum_to_one(self):
        clf = ComplaintClassifier()
        scores = clf.predict("Street lights not working, dark street")["scores"]
        assert abs(sum(scores.values()) - 1.0) < 0.01


class TestUrgency:
    def test_critical_terms_push_urgency(self):
        out = score_urgency("Vomiting blood, unbearable pain, admitted in emergency")
        assert out["label"] in ("HIGH", "CRITICAL")
        assert out["score"] >= 0.6
        assert out["reasons"]

    def test_mild_text_is_low(self):
        out = score_urgency("Very mild cold, slight sneezing in the morning, feels okay")
        assert out["label"] == "LOW"

    def test_explainable_reasons(self):
        out = score_urgency("Many people in our colony have severe diarrhea from "
                            "drinking contaminated water since three days")
        assert any("risk" in r or "serious" in r for r in out["reasons"])
        assert any("duration" in r or "people" in r for r in out["reasons"])


class TestMedicalNER:
    def test_symptom_extraction_with_spans(self):
        ner = MedicalNER()
        result = ner.extract("Patient has diarrhea, stomach pain and vomiting for three "
                             "days with fever of 102.")
        symptoms = result["symptoms"]
        assert {"diarrhea", "stomach_pain", "vomiting"} <= set(symptoms)
        for ent in result["entities"]:
            assert 0 <= ent["start"] < ent["end"]
        types = {e["type"] for e in result["entities"]}
        assert "SYMPTOM" in types
        assert "DURATION" in types  # "for three days"
        assert "VITAL" in types     # 102

    def test_medication_and_body_part(self):
        ner = MedicalNER()
        result = ner.extract("Take paracetamol and apply an ice pack on the arm and "
                             "back for the swelling.")
        types = {e["type"] for e in result["entities"]}
        assert "MEDICATION" in types
        assert "BODY_PART" in types

    def test_lexicon_covers_core_symptoms(self):
        for canonical in ("fever", "diarrhea", "vomiting", "dengue_symptoms"):
            assert canonical in SYMPTOM_LEXICON


class TestLocationExtraction:
    def test_gazetteer_district(self):
        out = extract_location("Water problem in Millbrook ward 3")
        assert out["district"] == "Millbrook"
        assert out["confidence"] > 0.5

    def test_pincode(self):
        out = extract_location("Issue near the market, pincode 530002")
        assert out["district"] == "Millbrook"
        assert out["pincode"] == "530002"

    def test_coordinates_win(self):
        out = extract_location("Somewhere", lat=17.7120, lng=83.2188)
        assert out["district"] == "Northgate"
        assert out["source"] == "coordinates"


class TestSummarizer:
    def test_extractive_summary(self):
        text = ("Severe diarrhea since four days. Stomach pain with vomiting at night. "
                "Fever 102 and worsening since yesterday. We contacted the clinic. "
                "Many neighbours have the same symptoms.")
        out = summarize(text, max_sentences=2)
        assert len(out["key_sentences"]) == 2
        assert out["method"] == "extractive-v1"

    def test_medical_digest_has_disclaimer(self):
        ner = MedicalNER()
        analysis = ner.extract("Diarrhea and vomiting for three days, fever 102.")
        urgency = score_urgency("Diarrhea and vomiting for three days, fever 102.")
        out = summarize_medical_report("Diarrhea and vomiting for three days, fever 102.",
                                       analysis["entities"], urgency)
        assert "not a diagnosis" in out["digest"]


class TestPipelineFacade:
    def test_health_reports_backends(self):
        health = get_pipeline().health()
        assert health["embedder"] in ("hashing-v1",) or health["embedder"].startswith("sentence-transformers")
        assert health["ner"] in ("lexicon-v1", "bioclinicalbert-hf")

    def test_analyze_complaint_end_to_end(self):
        out = get_pipeline().analyze_complaint(
            "Mosquitoes breeding in the choked drain near Riverside park, dengue cases rising")
        assert out["category"] == "mosquito menace"
        assert out["location"]["district"] == "Riverside"
        assert out["urgency"]["score"] > 0.2
        assert len(out["embedding"]) == 384

    def test_analyze_symptom_report_end_to_end(self):
        out = get_pipeline().analyze_symptom_report(
            "Whole family has diarrhea and vomiting since the water turned dirty. "
            "Two children admitted with severe dehydration.")
        assert "diarrhea" in out["symptoms"]
        assert "gastrointestinal" in out["symptom_categories"]
        assert out["urgency"]["label"] in ("HIGH", "CRITICAL")
