# Golden Dataset Eval Report

- Generated at: `2026-05-20T12:59:25.898722+00:00`
- Dataset: `backend/evals/golden_dataset.jsonl`
- Total cases: `36`
- Score range accuracy: `91.67%`
- Follow-up accuracy: `100.0%`
- Primary pass rate: `91.67%`
- Gap exact match rate: `91.67%`
- Avg gap recall: `0.9583`
- Avg gap precision: `1.0`
- Avg score distance: `0.0833`
- Avg predicted score: `6.39`

## Follow-up Confusion

- true_positive: `20`
- true_negative: `16`
- false_positive: `0`
- false_negative: `0`

## Breakdowns

### by_role

- `Frontend Developer`: score_range_accuracy=94.44%, follow_up_accuracy=100.0%, primary_pass_rate=94.44%, gap_exact_match_rate=88.89%, avg_gap_recall=0.9444, avg_predicted_score=6.22
- `Java Backend Developer`: score_range_accuracy=88.89%, follow_up_accuracy=100.0%, primary_pass_rate=88.89%, gap_exact_match_rate=94.44%, avg_gap_recall=0.9722, avg_predicted_score=6.56

### by_interview_type

- `Behavioural`: score_range_accuracy=88.89%, follow_up_accuracy=100.0%, primary_pass_rate=88.89%, gap_exact_match_rate=88.89%, avg_gap_recall=0.9444, avg_predicted_score=6.0
- `Mixed`: score_range_accuracy=100.0%, follow_up_accuracy=100.0%, primary_pass_rate=100.0%, gap_exact_match_rate=83.33%, avg_gap_recall=0.9167, avg_predicted_score=7.0
- `Technical Core`: score_range_accuracy=90.48%, follow_up_accuracy=100.0%, primary_pass_rate=90.48%, gap_exact_match_rate=95.24%, avg_gap_recall=0.9762, avg_predicted_score=6.38

### by_seniority

- `Junior`: score_range_accuracy=90.91%, follow_up_accuracy=100.0%, primary_pass_rate=90.91%, gap_exact_match_rate=90.91%, avg_gap_recall=0.9545, avg_predicted_score=1.91
- `Middle`: score_range_accuracy=92.0%, follow_up_accuracy=100.0%, primary_pass_rate=92.0%, gap_exact_match_rate=92.0%, avg_gap_recall=0.96, avg_predicted_score=8.36

### by_answer_quality_label

- `medium`: score_range_accuracy=75.0%, follow_up_accuracy=100.0%, primary_pass_rate=75.0%, gap_exact_match_rate=75.0%, avg_gap_recall=0.875, avg_predicted_score=5.67
- `strong`: score_range_accuracy=100.0%, follow_up_accuracy=100.0%, primary_pass_rate=100.0%, gap_exact_match_rate=100.0%, avg_gap_recall=1.0, avg_predicted_score=9.88
- `weak`: score_range_accuracy=100.0%, follow_up_accuracy=100.0%, primary_pass_rate=100.0%, gap_exact_match_rate=100.0%, avg_gap_recall=1.0, avg_predicted_score=0.5

## Failed Cases

- `frontend_016`: score=7 expected=[4, 6], follow_up=True expected_follow_up=True
- `java_002`: score=7 expected=[5, 6], follow_up=True expected_follow_up=True
- `java_005`: score=4 expected=[5, 6], follow_up=True expected_follow_up=True
