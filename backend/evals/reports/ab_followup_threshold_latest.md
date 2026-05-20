# A/B Test Report

- Generated at: `2026-05-20T12:59:25.896554+00:00`
- Dataset: `backend/evals/golden_dataset.jsonl`
- Experiment: `follow_up_threshold_ab`

## Variants

- threshold `<7`: follow_up_accuracy=94.44%, score_range_accuracy=91.67%, primary_pass_rate=91.67%, false_positive=0, false_negative=2
- threshold `<8`: follow_up_accuracy=100.0%, score_range_accuracy=91.67%, primary_pass_rate=91.67%, false_positive=0, false_negative=0

## Decision

- Winner: `threshold <8`
- Rationale: Порог follow-up `8` выбран как baseline, потому что он даёт лучшую точность follow-up без роста false positive.
