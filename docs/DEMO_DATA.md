# HealthPulse AI — Demo Data

**Everything in this directory tree is SYNTHETIC demonstration data.** No real patient
records, no real civic complaints, no real geography. It exists to demonstrate the
complete application end-to-end and to train/evaluate the classical models. It must
never be presented as real clinical or public-health evidence.

## 1. Demo city: Riverton (fictional)

| District | lat | lng | pincode |
| --- | --- | --- | --- |
| Harbourview | 17.6901 | 83.2105 | 530001 |
| Millbrook | 17.6968 | 83.2204 | 530002 |
| Eastfields | 17.6849 | 83.2318 | 530003 |
| Old Town | 17.7032 | 83.2091 | 530004 |
| Northgate | 17.7120 | 83.2188 | 530005 |
| Riverside | 17.6790 | 83.2002 | 530006 |
| Greenhills | 17.7058 | 83.2325 | 530007 |
| Southbay | 17.6735 | 83.2189 | 530008 |

Defined in `ml/preprocessing/gazetteer.py`. Coordinates are synthetic.

## 2. Generated datasets (`ml/datasets/data/`, seed 42, deterministic)

| File | Rows | Purpose |
| --- | --- | --- |
| `complaints_train.jsonl` | 1,494 | train the TF-IDF+LogReg classifier |
| `complaints_eval.jsonl` | 315 | held-out evaluation |
| `symptom_reports_ner.jsonl` | 420 | span-annotated symptom reports (for NER fine-tuning) |
| `cross_domain_pairs.jsonl` | 1,350 | positive/negative pairs for embedding fine-tuning |

Generator: `python -m ml.datasets.build_datasets` — templates × categories × languages
(English + romanized Hindi) with a fixed RNG; `README.json` beside the files records the
seed and the synthetic-data notice.

## 3. Curated demo corpus (`ml/datasets/demo_corpus.py`)

Hand-tuned for a coherent demonstration narrative (clock pinned to 2026-11-10):

- **Scenario A — Millbrook water contamination:** complaints 101/102 (sewage-smell and
  muddy borewell water), 103 (open sewage near school), 104 (mosquito breeding in drain,
  3 dengue diagnoses), 105/116 (uncollected garbage near school) — paired with symptom
  reports 201–203, 208, 209 (childhood diarrhea/vomiting with fever 102, hospitalized
  dehydration, suspected dengue rash, typhoid admission at Riverside).
- **Scenario B — Riverside sewage:** complaints 106–108 + reports 204–205 (family GI
  illness, typhoid admission).
- **Scenario C — Southbay mosquitoes:** complaints 109/110 + reports 206/210.
- **Duplicate ground truth:** 114 & 115 duplicate 101 (re-reported sewage smell);
  116 duplicates 105 (second reminder for garbage). Verification: 114 scores 0.80
  (flagged at threshold 0.75); 115 scores 0.54 (correctly kept as "related", not duplicate).
- **Infrastructure filler:** potholes, street lighting, noise, animal nuisance,
  public sanitation — categories that should NOT trigger health alerts.

## 4. What the seeder creates (`backend/scripts/seed_demo.py`)

```bash
cd backend && python -m scripts.seed_demo [--reset]
```

| Artifact | Count |
| --- | --- |
| Role accounts (password `HealthPulse!2026`) | 6 |
| Complaints (NLP-analyzed, geocoded, embedded) | 19 |
| Medical reports (entities, urgency, summaries) | 10 |
| Alerts (from a real engine scan) | 3 |
| Investigations (demo workflow on alert #1) | 1 |

The seeder is idempotent-safe (skips existing rows) and `--reset` wipes demo rows.
It runs the **actual intelligence engine** at seed time, so the alert list reflects the
live thresholds in `ml/config.py`.

## 5. Ethical guardrails baked in

- Every alert row stores the full disclaimer text (`ml.config.DISCLAIMER`).
- Every medical summary states it is not a diagnosis.
- The report CSV export is de-identified (no patient ids, no free text).
- The UI labels demo accounts and disclaims signals in the sidebar, landing page and
  alert detail panels.
