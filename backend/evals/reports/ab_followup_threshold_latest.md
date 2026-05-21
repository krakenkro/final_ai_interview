# A/B Test Report

- Generated at: `2026-05-21T15:30:54.205420+00:00`
- Dataset: `backend/evals/answer_evaluation_golden_dataset.jsonl`
- Experiment: `follow_up_threshold_ab`

## Variants

- threshold `<7`: follow_up_accuracy=94.44%, score_range_accuracy=88.89%, primary_pass_rate=88.89%, false_positive=0, false_negative=1
- threshold `<8`: follow_up_accuracy=94.44%, score_range_accuracy=88.89%, primary_pass_rate=88.89%, false_positive=0, false_negative=1

## Decision

- Winner: `threshold <7`
- Rationale: Порог follow-up `7` выбран как baseline, потому что он даёт лучшую точность follow-up без роста false positive.
