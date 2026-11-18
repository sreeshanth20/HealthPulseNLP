"""Synthetic dataset builder for HealthPulse AI.

Generates the clearly-labelled DEMONSTRATION datasets used for:
- training the classical complaint classifier (TF-IDF + LogisticRegression)
- evaluating it on a held-out split
- a sentence-pair dataset for future Sentence-Transformer fine-tuning
- NER-span-annotated symptom reports for future BioClinicalBERT fine-tuning

Everything here is SYNTHETIC. No real patient records, no real civic data.
Deterministic (seed=42) so runs are reproducible.

Usage:  python -m ml.datasets.build_datasets
Output: ml/datasets/data/*.jsonl
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ml.preprocessing.gazetteer import ALL_DISTRICTS, GAZETTEER
from ml.preprocessing.lexicons import SYMPTOM_LEXICON

DATA_DIR = Path(__file__).resolve().parent / "data"
SEED = 42

CATEGORIES = [
    "water_contamination", "garbage_sanitation", "drainage_sewage",
    "mosquito menace", "road_infrastructure", "street_lighting",
    "public_sanitation", "noise_pollution", "animal_nuisance",
]

COMPLAINT_TEMPLATES: dict[str, list[str]] = {
    "water_contamination": [
        "The {source} water in {place} has been {water_issue} for {duration}. We cannot use it for drinking or cooking.",
        "Dirty water is coming from the {source} near {place}. The water is {water_issue} and smells terrible.",
        "{place} {source} water supply is contaminated, {water_issue}. Several families already have stomach problems.",
        "Water from the {source} in {place} looks {water_issue}. Someone got sick after drinking it.",
    ],
    "garbage_sanitation": [
        "Garbage has not been collected in {place} for {duration}. The bins are {bin_state} and the stench is unbearable.",
        "Overflowing dustbins near {place}. Waste is {bin_state}. Please schedule a pickup.",
        "There is a huge garbage dump on the street next to {place}. It has been {bin_state} since last week and flies are everywhere.",
        "Nobody is collecting wet waste around {place}, bins are {bin_state} and attracting dogs and flies.",
    ],
    "drainage_sewage": [
        "The drain near {place} is {drain_state}. Sewage water is spreading onto the road for {duration}.",
        "Open sewage overflowing right in front of {place}, it is {drain_state} and children cannot walk to school.",
        "Drainage line is choked at {place}. {drain_state} with stagnant water, terrible smell all day.",
        "Sewer overflow behind {place} has made the entire lane {drain_state}. Requesting immediate cleaning.",
    ],
    "mosquito menace": [
        "Severe mosquito problem in {place} for {duration}. Stagnant water in the drains is a breeding ground, people are getting dengue.",
        "Too many mosquitoes around {place} in the evenings. Larvae visible in the {drain_state} drain. No fogging done so far.",
        "Mosquito breeding in the garbage pile near {place}. Three neighbours already diagnosed with dengue this month.",
        "Please arrange fogging in {place}, mosquito menace is {mosquito_level}, children are getting bitten constantly.",
    ],
    "road_infrastructure": [
        "Large potholes on the road near {place}. Two-wheeler riders are falling, it has been like this for {duration}.",
        "The road to {place} is broken and muddy after the rains, completely damaged, needs re-laying.",
        "Deep pothole in front of {place} school gate. Dangerous for children, several accidents reported.",
        "Footpath tiles near {place} are broken and the road surface is damaged for {duration}.",
    ],
    "street_lighting": [
        "Street lights are not working near {place} for {duration}. The entire stretch is dark at night, unsafe for women.",
        "The lamp post outside {place} has been {light_state}. Lots of chain snatching incidents reported.",
        "No street lighting between {place} and the main road, it is pitch dark after 7pm.",
        "Streetlight pole is hanging dangerously near {place}, {light_state}, risk of electric shock during rain.",
    ],
    "public_sanitation": [
        "The public toilet near {place} is {toilet_state} and has not been cleaned for {duration}.",
        "No functional public toilet around {place}, people are forced to defecate in the open near the field.",
        "Public urinal opposite {place} is {toilet_state}, the whole corner smells of urine.",
        "Community toilet block at {place} is {toilet_state}, water supply broken, unusable.",
    ],
    "noise_pollution": [
        "Loudspeakers till midnight near {place} every day for {duration}. Students and elderly cannot sleep.",
        "Construction work at {place} runs all night with heavy machinery noise. No permits displayed.",
        "Constant honking and DJ noise around {place} market. Request noise monitoring.",
        "Factory generators near {place} run through the night, extreme noise pollution for {duration}.",
    ],
    "animal_nuisance": [
        "Stray dogs near {place} have become aggressive for {duration}. Two children were chased yesterday.",
        "There is a pack of stray dogs around {place} creating problems at night, please sterilize and vaccinate them.",
        "Cattle blocking the road near {place} every morning, traffic chaos and dung everywhere.",
        "Monkey troop troubling residents near {place}, snatching bags, one child bitten last week.",
    ],
}

VARIABLES = {
    "source": ["tap", "borewell", "municipal", "pipeline", "hand pump"],
    "water_issue": ["muddy", "smelling like sewage", "blackish", "yellowish", "worm-infested", "salty and foul"],
    "bin_state": ["overflowing", "not emptied for days", "broken and spilling", "rotting in the sun"],
    "drain_state": ["choked", "overflowing", "completely blocked", "leaking sewage"],
    "mosquito_level": ["unbearable", "extreme", "out of control", "getting worse every day"],
    "light_state": ["dead for weeks", "flickering", "hanging broken", "not working"],
    "toilet_state": ["blocked", "filthy", "overflowing", "broken"],
    "duration": ["2 days", "4 days", "a week", "two weeks", "10 days", "almost a month", "3 days"],
    "place": ALL_DISTRICTS,
}

# Symptom bundles by theme (canonical symptoms + surface forms)
SYMPTOM_BUNDLES = {
    "gastrointestinal": [
        ["diarrhea", "stomach_pain", "vomiting"],
        ["diarrhea", "stomach_pain", "fever"],
        ["diarrhea", "vomiting", "body_ache"],
        ["stomach_pain", "blood_in_stool", "fever"],
    ],
    "febrile": [
        ["fever", "headache", "body_ache"],
        ["fever", "chills", "body_ache"],
        ["fever", "headache", "vomiting"],
    ],
    "vector_borne": [
        ["fever", "rash", "body_ache"],
        ["fever", "rash", "eye_irritation"],
    ],
    "respiratory": [
        ["cough", "sore_throat", "cold"],
        ["breathlessness", "chest_pain", "cough"],
    ],
    "dermal": [
        ["rash", "skin_infection", "eye_irritation"],
        ["rash", "skin_infection"],
    ],
}

SEVERITY_PHRASES = ["mild", "persistent", "severe", "unbearable", "worsening"]
PERSON_ANGLES = [
    "My {age}-year-old {relative} has had {symptoms} for {duration}.",
    "Since the water issue started, {count} people in our building are suffering from {symptoms}.",
    "I have been experiencing {symptoms} since {duration}, it is {severity}.",
    "{relative} was admitted to hospital with {symptoms}. The doctor asked about our water source.",
    "Multiple neighbours report {symptoms}. It started after the {trigger}.",
]
RELATIVES = ["son", "daughter", "father", "mother", "wife", "husband", "brother"]
TRIGGERS = ["drain overflow", "garbage pile", "tap water problem", "sewage leak"]

HINDI_FLAVOUR = [
    "{place} me {h} ho raha hai, please help.",
    "Sir, {place} me {h} bahut din se hai, koi action nahi.",
]
HINDI_MAP = {
    "water_contamination": "pani me badboo aur gandagi",
    "garbage_sanitation": "kachra nahi uthaya ja raha",
    "drainage_sewage": "nali me peechab jama hai",
    "mosquito menace": "machhar bahut hai",
    "road_infrastructure": "sadak me gadhe ho gaye",
    "street_lighting": "street light nahi jal rahi",
    "public_sanitation": "public toilet ganda hai",
    "noise_pollution": "loudspeaker ki awaz bahut hai",
    "animal_nuisance": "stray dogs pareshan kar rahe",
}


def _pick(rng: random.Random, seq: list[str]) -> str:
    return rng.choice(seq)


def generate_complaints(rng: random.Random, n: int) -> list[dict]:
    rows: list[dict] = []
    per_cat = max(1, n // len(CATEGORIES))
    for category in CATEGORIES:
        for i in range(per_cat):
            if rng.random() < 0.15:  # romanized Hindi flavour subset
                text = HINDI_FLAVOUR[rng.randrange(len(HINDI_FLAVOUR))].format(
                    place=_pick(rng, VARIABLES["place"]),
                    h=HINDI_MAP[category],
                )
                label = category
            else:
                text = _pick(rng, COMPLAINT_TEMPLATES[category]).format(
                    source=_pick(rng, VARIABLES["source"]),
                    water_issue=_pick(rng, VARIABLES["water_issue"]),
                    bin_state=_pick(rng, VARIABLES["bin_state"]),
                    drain_state=_pick(rng, VARIABLES["drain_state"]),
                    mosquito_level=_pick(rng, VARIABLES["mosquito_level"]),
                    light_state=_pick(rng, VARIABLES["light_state"]),
                    toilet_state=_pick(rng, VARIABLES["toilet_state"]),
                    duration=_pick(rng, VARIABLES["duration"]),
                    place=_pick(rng, VARIABLES["place"]),
                )
                label = category
            rows.append({"id": len(rows) + 1, "text": text, "category": label})
    rng.shuffle(rows)
    return rows


def generate_symptom_reports(rng: random.Random, n: int) -> list[dict]:
    """Reports with entity span annotations for future NER fine-tuning."""
    rows: list[dict] = []
    district_names = list(GAZETTEER.keys())
    for i in range(n):
        theme = _pick(rng, list(SYMPTOM_BUNDLES.keys()))
        bundle = _pick(rng, SYMPTOM_BUNDLES[theme])
        surface = [_pick(rng, SYMPTOM_LEXICON[s]) for s in bundle]
        symptoms_phrase = ", ".join(surface[:-1]) + f" and {surface[-1]}"
        template = _pick(rng, PERSON_ANGLES)
        text = template.format(
            age=rng.randrange(3, 78),
            relative=_pick(rng, RELATIVES),
            symptoms=symptoms_phrase,
            duration=_pick(rng, VARIABLES["duration"]),
            count=rng.randrange(2, 12),
            severity=_pick(rng, SEVERITY_PHRASES),
            trigger=_pick(rng, TRIGGERS),
        )
        # compute spans by locating the surface phrases sequentially
        spans: list[dict] = []
        cursor = 0
        lowered = text.lower()
        for surface_form, canonical in zip(surface, bundle):
            idx = lowered.find(surface_form.lower(), cursor)
            if idx >= 0:
                spans.append({"text": surface_form, "canonical": canonical,
                              "type": "SYMPTOM", "start": idx,
                              "end": idx + len(surface_form)})
                cursor = idx + len(surface_form)
        place = _pick(rng, district_names)
        text += f" We live in {place.replace('-', ' ').title()}."
        rows.append({
            "id": i + 1,
            "text": text,
            "symptoms": bundle,
            "theme": theme,
            "district": place.title(),
            "entities": spans,
        })
    rng.shuffle(rows)
    return rows


def generate_cross_domain_pairs(rng: random.Random, n: int) -> list[dict]:
    """Positive/negative sentence pairs for embedding fine-tuning."""
    positives: list[tuple[str, str]] = []
    complaints = generate_complaints(rng, n)
    reports = generate_symptom_reports(rng, n)
    for c, r in zip(complaints, reports):
        positives.append((c["text"], r["text"]))
    negatives: list[tuple[str, str]] = []
    for i in range(0, min(len(complaints) - 2, n // 2), 2):
        negatives.append((complaints[i]["text"], reports[min(i + 2, len(reports) - 1)]["text"]))
        negatives.append((complaints[i]["text"], complaints[i + 1]["text"]))
    rows = []
    for a, b in positives:
        rows.append({"text_a": a, "text_b": b, "label": 1})
    for a, b in negatives:
        rows.append({"text_a": a, "text_b": b, "label": 0})
    rng.shuffle(rows)
    return rows


def build_all() -> dict:
    """Generate and write all datasets; returns summary counts."""
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    complaints = generate_complaints(rng, 1500)
    eval_complaints = generate_complaints(random.Random(SEED + 1), 320)
    reports = generate_symptom_reports(rng, 420)
    pairs = generate_cross_domain_pairs(rng, 900)

    counts = {}
    for name, rows in [
        ("complaints_train.jsonl", complaints),
        ("complaints_eval.jsonl", eval_complaints),
        ("symptom_reports_ner.jsonl", reports),
        ("cross_domain_pairs.jsonl", pairs),
    ]:
        path = DATA_DIR / name
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        counts[name] = len(rows)

    meta = {
        "generator_seed": SEED,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_notice": (
            "All rows are SYNTHETIC demonstration data generated from hand-written "
            "templates. They do not contain real patient records or real civic "
            "complaints and must never be presented as real-world evidence."
        ),
        "files": counts,
    }
    with open(DATA_DIR / "README.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


if __name__ == "__main__":
    meta = build_all()
    print("Synthetic demo datasets generated:")
    for name, count in meta["files"].items():
        print(f"  {name}: {count} rows")
    print(f"Seed: {meta['generator_seed']} (deterministic)")
