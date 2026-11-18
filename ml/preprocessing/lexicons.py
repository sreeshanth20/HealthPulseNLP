"""Domain lexicons: symptoms, medications, severity terms, complaint keywords.

All surface forms were written by hand for this project (synthetic demo
vocabulary); they are intentionally small but cover the demo scenario
categories end to end.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Medical lexicon
# ---------------------------------------------------------------------------

# canonical symptom -> surface forms (English, romanized Hindi, common typos)
SYMPTOM_LEXICON: dict[str, list[str]] = {
    "fever": ["fever", "feverish", "high temperature", "bukhar", "pyrexia", "temperature"],
    "diarrhea": ["diarrhea", "diarrhoea", "loose motions", "loose motion", "watery stool",
                 "dast", "loosemotion"],
    "vomiting": ["vomiting", "vomit", "throwing up", "nausea", "puking", "ulti"],
    "stomach_pain": ["stomach pain", "stomach ache", "abdominal pain", "belly pain",
                     "cramps", "pet dard", "tummy pain"],
    "headache": ["headache", "head ache", "migraine", "sardard"],
    "cough": ["cough", "coughing", "khansi", "persistent cough"],
    "cold": ["cold", "runny nose", "blocked nose", "sneezing", "zukam", "sardi"],
    "sore_throat": ["sore throat", "throat pain", "throat infection", "difficulty swallowing"],
    "breathlessness": ["breathlessness", "shortness of breath", "difficulty breathing",
                       "hard to breathe", "wheezing", "saans lene"],
    "chest_pain": ["chest pain", "chest tightness", "pain in chest"],
    "body_ache": ["body ache", "body pain", "muscle pain", "joint pain", "weakness",
                  "fatigue", "tiredness", "kamzori"],
    "dizziness": ["dizziness", "dizzy", "lightheaded", "chakkar"],
    "rash": ["rash", "skin rash", "itching", "red spots", "daane", "khujli", "hives"],
    "jaundice": ["jaundice", "yellow eyes", "yellow skin", "pilia", "peela"],
    "blood_in_stool": ["blood in stool", "bloody stool", "dysentery", "khoon in stool"],
    "dehydration": ["dehydrated", "dehydration", "dry mouth", "not urinating"],
    "chills": ["chills", "shivering", "rigors"],
    "eye_irritation": ["eye irritation", "red eyes", "itchy eyes", "burning eyes"],
    "skin_infection": ["skin infection", "boil", "abscess", "wound infection", "fungal infection"],
    "loss_of_appetite": ["loss of appetite", "no appetite", "not eating"],
    "typhoid_symptoms": ["typhoid", "enteric fever"],
    "dengue_symptoms": ["dengue", "dengue fever"],
    "malaria_symptoms": ["malaria"],
}

# Environmental-exposure symptoms that link complaints <-> health reports.
SYMPTOM_CATEGORY_MAP: dict[str, list[str]] = {
    "gastrointestinal": [
        "diarrhea", "vomiting", "stomach_pain", "blood_in_stool", "dehydration",
        "jaundice", "typhoid_symptoms", "loss_of_appetite", "fever",
    ],
    "respiratory": ["cough", "cold", "sore_throat", "breathlessness", "chest_pain"],
    "febrile": ["fever", "chills", "body_ache", "dengue_symptoms", "malaria_symptoms",
                "typhoid_symptoms", "headache"],
    "vector_borne": ["dengue_symptoms", "malaria_symptoms", "fever", "rash", "body_ache"],
    "dermal": ["rash", "skin_infection", "eye_irritation", "itching"],
    "neurological": ["headache", "dizziness"],
}

# Reverse index: symptom -> categories
SYMPTOM_TO_CATEGORIES: dict[str, list[str]] = {}
for _cat, _symptoms in SYMPTOM_CATEGORY_MAP.items():
    for _s in _symptoms:
        SYMPTOM_TO_CATEGORIES.setdefault(_s, [])
        if _cat not in SYMPTOM_TO_CATEGORIES[_s]:
            SYMPTOM_TO_CATEGORIES[_s].append(_cat)

MEDICATION_TERMS: list[str] = [
    "paracetamol", "crocin", "calpol", "dolo", "ors", "orenge", "electral",
    "metronidazole", "azithromycin", "ofloxacin", "ibuprofen", "combiflam",
    "cetirizine", "allegra", "doxycycline", "insulin", "asthalin", "inhaler",
]

BODY_PART_TERMS: list[str] = [
    "stomach", "abdomen", "head", "chest", "throat", "eyes", "skin", "arm",
    "leg", "back", "tooth", "ear", "hand", "foot", "belly",
]

SEVERITY_TERMS: dict[str, float] = {
    "mild": 0.15, "slight": 0.15, "moderate": 0.4, "severe": 0.75, "serious": 0.7,
    "unbearable": 0.9, "extreme": 0.85, "worst": 0.85, "constant": 0.6,
    "continuous": 0.6, "persistent": 0.55, "worsening": 0.65, "blood": 0.8,
    "hospital": 0.8, "admitted": 0.85, "admission": 0.85, "emergency": 0.95,
    "critical": 0.95, "high fever": 0.7, "103": 0.65, "104": 0.75, "102": 0.55,
}

# ---------------------------------------------------------------------------
# Civic complaint lexicon (category -> keyword features)
# ---------------------------------------------------------------------------

COMPLAINT_KEYWORDS: dict[str, list[str]] = {
    "water_contamination": [
        "water", "drinking water", "tap water", "borewell", "water supply", "pipeline",
        "contaminated", "dirty water", "muddy water", "smell", "taste", "colour",
        "black water", "yellow water", "worms in water", "sewage mixed", "sediment",
    ],
    "garbage_sanitation": [
        "garbage", "trash", "waste", "dump", "dustbin", "not collected", "overflowing",
        "garbage truck", "litter", "rubbish", "kachra", "thrown", "stink", "foul smell",
        "wet waste", "plastic waste",
    ],
    "drainage_sewage": [
        "drain", "drainage", "sewage", "sewer", "open drain", "choked", "blocked drain",
        "overflowing drain", "waterlogging", "water logging", "stagnant", "manhole",
        "nali", "gutter", "overflow",
    ],
    "mosquito menace": [
        "mosquito", "mosquitoes", "larvae", "dengue", "malaria", "fogging", "breeding",
        "machhar", "insect", "wrigglers", "mosquito breeding",
    ],
    "road_infrastructure": [
        "road", "pothole", "potholes", "broken road", "footpath", "divider", "speed breaker",
        "repair", "asphalt", "street", "manhole open",
    ],
    "street_lighting": [
        "street light", "streetlight", "dark", "no light", "bulb", "lamp post", "lights not working",
        "pole", "electric shock",
    ],
    "public_sanitation": [
        "toilet", "public toilet", "urinal", "sanitation", "open defecation", "cleaning",
        "sulabh", "bio toilet", "wet floor",
    ],
    "noise_pollution": [
        "noise", "loud", "loudspeaker", "construction noise", "dj", "honking", "night noise",
    ],
    "animal_nuisance": [
        "dog", "dogs", "stray", "cattle", "monkey", "pig", "barking", "bite", "sterilization",
    ],
    "other": [],
}

CATEGORY_LABELS: dict[str, str] = {
    "water_contamination": "Water contamination",
    "garbage_sanitation": "Garbage & sanitation",
    "drainage_sewage": "Drainage & sewage",
    "mosquito menace": "Mosquito menace",
    "road_infrastructure": "Road infrastructure",
    "street_lighting": "Street lighting",
    "public_sanitation": "Public sanitation",
    "noise_pollution": "Noise pollution",
    "animal_nuisance": "Animal nuisance",
    "other": "Other",
}

# Environmental complaint category -> symptom categories it could plausibly affect.
# Used ONLY as an explainable co-occurrence prior, never as causation.
ENV_TO_HEALTH_THEME: dict[str, list[str]] = {
    "water_contamination": ["gastrointestinal", "febrile"],
    "garbage_sanitation": ["gastrointestinal", "dermal", "vector_borne"],
    "drainage_sewage": ["gastrointestinal", "dermal", "vector_borne"],
    "mosquito menace": ["vector_borne", "febrile"],
    "public_sanitation": ["gastrointestinal", "dermal", "vector_borne"],
    "street_lighting": [],
    "road_infrastructure": [],
    "noise_pollution": [],
    "animal_nuisance": ["dermal"],
    "other": [],
}
