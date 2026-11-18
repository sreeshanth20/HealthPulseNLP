"""Hand-crafted synthetic demonstration corpus (seed=42 adjacent, hand-tuned).

This is the curated demo dataset loaded by scripts/seed_demo.py and exercised
by the integration tests. Every row is synthetic and internally consistent:
a cross-domain scenario links water/drainage/mosquito complaints in Millbrook
and Riverside with gastrointestinal/febrile symptom reports in the same wards.

FICTIONAL DEMO DATA — not real patients, not real complaints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Base "now" is fixed so duplicate/temporal logic is reproducible.
DEMO_NOW = datetime(2026, 11, 10, 9, 0, 0, tzinfo=timezone.utc)


def _d(days_ago: int, hour: int = 9, minute: int = 0) -> datetime:
    return DEMO_NOW - timedelta(days=days_ago, hours=DEMO_NOW.hour - hour, minutes=minute)


# ---------------------------------------------------------------------------
# Civic complaints  (id, days_ago, category, title, text, district, lat, lng,
#                    reporter_role)
# ---------------------------------------------------------------------------

_COMPLAINT_ROWS = [
    # --- Millbrook water contamination cluster (cross-domain scenario A) ---
    (101, 12, "water_contamination", "Tap water smells like sewage in Millbrook",
     "The tap water in Millbrook ward 3 has been smelling like sewage since three days. "
     "The water is dirty and blackish. Several families already have stomach problems "
     "after drinking it. Please test the pipeline near Millbrook market.",
     "Millbrook", 17.6968, 83.2204),
    (102, 10, "water_contamination", "Millbrook borewell water is muddy",
     "Borewell water near Millbrook market is muddy and worm-infested for a week now. "
     "Children in our colony are getting diarrhea after drinking this water.",
     "Millbrook", 17.6975, 83.2197),
    (103, 8, "drainage_sewage", "Open sewage overflowing near Millbrook school",
     "Open sewage overflowing right in front of Millbrook school, it is choked and the "
     "smell is unbearable. Children cannot walk to school safely.",
     "Millbrook", 17.6959, 83.2218),
    (104, 6, "mosquito menace", "Mosquitoes breeding in Millbrook drain",
     "Severe mosquito problem in Millbrook for two weeks. Stagnant water in the "
     "overflowing drain is a breeding ground, larvae visible. Three neighbours already "
     "diagnosed with dengue this month.",
     "Millbrook", 17.6981, 83.2210),
    (105, 4, "garbage_sanitation", "Garbage not collected in Millbrook ward 4",
     "Garbage has not been collected in Millbrook ward 4 for 10 days. Bins are "
     "overflowing and rotting in the sun next to the school. Flies everywhere.",
     "Millbrook", 17.6944, 83.2225),

    # --- Riverside sewage + GI cluster (cross-domain scenario B) ---
    (106, 9, "drainage_sewage", "Sewer overflow behind Riverside park",
     "Sewer overflow behind Riverside park has made the entire lane choked with sewage. "
     "The stagnated water smells terrible all day and people are vomiting and getting "
     "loose motions.",
     "Riverside", 17.6790, 83.2002),
    (107, 7, "water_contamination", "Riverside pipeline water contaminated",
     "Municipal pipeline water in Riverside has turned yellowish and smells terrible. "
     "My whole family got stomach pain and fever after drinking it since four days.",
     "Riverside", 17.6795, 83.2010),
    (108, 5, "garbage_sanitation", "Garbage dump near Riverside beach road",
     "There is a huge garbage dump on the street next to Riverside beach road. It has "
     "been rotting in the sun since last week and attracting dogs and flies.",
     "Riverside", 17.6785, 83.1996),

    # --- Southbay mosquito cluster ---
    (109, 6, "mosquito menace", "Dengue cases rising in Southbay",
     "Too many mosquitoes around Southbay in the evenings. Larvae visible in the "
     "choked drain near Southbay market. Please arrange fogging, it is unbearable and "
     "children are getting bitten constantly.",
     "Southbay", 17.6735, 83.2189),
    (110, 3, "drainage_sewage", "Choked drain in Southbay lane 2",
     "Drainage line is choked in Southbay lane 2. Completely blocked with stagnant "
     "water for a week, terrible smell all day.",
     "Southbay", 17.6742, 83.2180),

    # --- Old Town infrastructure (non-health) ---
    (111, 5, "road_infrastructure", "Deep pothole near Old Town school gate",
     "Deep pothole in front of Old Town school gate. Dangerous for children, several "
     "two-wheeler accidents reported this week.",
     "Old Town", 17.7032, 83.2091),
    (112, 2, "street_lighting", "Street lights dead near Old Town market",
     "Street lights are not working near Old Town market for two weeks. The entire "
     "stretch is dark at night, unsafe for women returning from work.",
     "Old Town", 17.7040, 83.2085),
    (113, 1, "noise_pollution", "Loudspeakers till midnight near Northgate",
     "Loudspeakers till midnight near Northgate community hall every day for a week. "
     "Students and elderly cannot sleep.",
     "Northgate", 17.7120, 83.2188),

    # --- deliberate near-duplicate rows (repeated reporting) ---
    (114, 11, "water_contamination", "Water smells like sewage in Millbrook 3",
     "The tap water in Millbrook ward 3 has been smelling like sewage since three days. "
     "Water is blackish and dirty, families have stomach problems after drinking it.",
     "Millbrook", 17.6970, 83.2200),
    (115, 9, "water_contamination", "Same sewage smell in Millbrook water again",
     "Reporting again: tap water in Millbrook ward 3 still smells like sewage. Nobody "
     "came to test the pipeline near Millbrook market. Children keep getting diarrhea.",
     "Millbrook", 17.6971, 83.2202),
    (116, 4, "garbage_sanitation", "Please collect garbage in Millbrook ward 4",
     "Second reminder: garbage not collected in Millbrook ward 4 for 10 days, bins "
     "overflowing near the school, rotting waste and flies everywhere.",
     "Millbrook", 17.6946, 83.2223),

    # --- Eastfields & Harbourview filler (variety) ---
    (117, 3, "public_sanitation", "Public toilet blocked near Eastfields bus stop",
     "The public toilet near Eastfields bus stop is blocked and filthy, has not been "
     "cleaned for two weeks. The whole corner smells of urine.",
     "Eastfields", 17.6849, 83.2318),
    (118, 2, "animal_nuisance", "Stray dogs aggressive in Harbourview lane 5",
     "Stray dogs near Harbourview lane 5 have become aggressive for a week. Two "
     "children were chased yesterday evening. Please sterilize and vaccinate them.",
     "Harbourview", 17.6901, 83.2105),
    (119, 1, "road_infrastructure", "Broken footpath tiles in Greenhills",
     "Footpath tiles near Greenhills park are broken and the road surface is damaged "
     "for two weeks after the cable laying work.",
     "Greenhills", 17.7058, 83.2325),
]

# ---------------------------------------------------------------------------
# Medical symptom reports (voluntary, synthetic)
# (id, days_ago, patient_alias, text, district, lat, lng, urgency_hint)
# ---------------------------------------------------------------------------

_REPORT_ROWS = [
    (201, 9, "R. Sharma", "My 6-year-old son has had diarrhea and stomach pain with "
     "vomiting for three days. Fever is 102 and worsening. He is very weak and not "
     "eating. We drink the tap water in Millbrook.",
     "Millbrook", 17.6965, 83.2208, "HIGH"),
    (202, 8, "A. Fernandes", "Whole family suffering from loose motions and stomach "
     "cramps since the water became dirty. My wife was admitted to hospital with "
     "severe dehydration yesterday.",
     "Millbrook", 17.6978, 83.2193, "HIGH"),
    (203, 7, "M. Rao", "Persistent fever, headache and body ache for five days, "
     "high fever 103 in the evenings with chills. Doctor suspects dengue because of "
     "the mosquitoes in our area. Rash appeared this morning.",
     "Millbrook", 17.6985, 83.2212, "HIGH"),
    (204, 6, "S. Khan", "Vomiting and diarrhea since two days after drinking tap "
     "water in Riverside. Severe stomach pain and weakness, ORS not helping much.",
     "Riverside", 17.6792, 83.2005, "HIGH"),
    (205, 5, "P. Nair", "My mother has typhoid symptoms: continuous fever for ten "
     "days, headache, loss of appetite and stomach pain. She is admitted in the "
     "hospital since yesterday. We live near Riverside park where sewage is "
     "overflowing.",
     "Riverside", 17.6788, 83.2000, "CRITICAL"),
    (206, 5, "K. Das", "High fever with body ache and rash for four days in "
     "Southbay. Doctor said platelets are dropping, suspect dengue. Mosquito "
     "problem in our lane is extreme.",
     "Southbay", 17.6738, 83.2185, "HIGH"),
    (207, 3, "L. Pereira", "Mild fever and cold for two days, cough at night. "
     "Recovering with rest and paracetamol.",
     "Harbourview", 17.6905, 83.2100, "MEDIUM"),
    (208, 2, "T. Reddy", "Itching and red rash on arms since three days, doctor "
     "said fungal infection, likely from the stagnant sewage water in our lane in "
     "Millbrook.",
     "Millbrook", 17.6950, 83.2220, "MEDIUM"),
    (209, 8, "J. Mathew", "Stomach pain and diarrhea for four days, two children "
     "in the same building have the same symptoms. We all use the borewell water "
     "near Millbrook market.",
     "Millbrook", 17.6972, 83.2199, "HIGH"),
    (210, 4, "V. Iyer", "Fever 101 with headache since three days. Mild, resting "
     "at home in Southbay. Noticed lots of mosquito larvae in the drain outside.",
     "Southbay", 17.6733, 83.2192, "MEDIUM"),
]

# ---------------------------------------------------------------------------
# Duplicate groups (explicit ground truth for tests/demo)
# ---------------------------------------------------------------------------

DUPLICATE_GROUPS = [
    {"original": 101, "duplicates": [114, 115],
     "note": "Repeated reports of the same sewage-smell water issue in Millbrook ward 3."},
    {"original": 105, "duplicates": [116],
     "note": "Second reminder for the same uncollected garbage complaint."},
]

COMPLAINTS = [
    {
        "id": row[0], "created_at": _d(row[1]), "category": row[2], "title": row[3],
        "text": row[4], "district": row[5], "lat": row[6], "lng": row[7],
    }
    for row in _COMPLAINT_ROWS
]

MEDICAL_REPORTS = [
    {
        "id": row[0], "created_at": _d(row[1]), "patient_alias": row[2], "text": row[3],
        "district": row[4], "lat": row[5], "lng": row[6], "urgency_hint": row[7],
    }
    for row in _REPORT_ROWS
]
