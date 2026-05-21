# Golden Dataset Eval Report

- Generated at: `2026-05-21T15:30:54.206529+00:00`
- Dataset: `backend/evals/answer_evaluation_golden_dataset.jsonl`
- Total cases: `18`
- Score range accuracy: `88.89%`
- Follow-up accuracy: `94.44%`
- Primary pass rate: `88.89%`
- Gap exact match rate: `88.89%`
- Avg gap recall: `0.9333`
- Avg gap precision: `0.9444`
- Avg score distance: `0.1111`
- Avg predicted score: `6.78`

## Follow-up Confusion

- true_positive: `7`
- true_negative: `10`
- false_positive: `0`
- false_negative: `1`

## Breakdowns

### by_role

- `Frontend Developer`: score_range_accuracy=88.89%, follow_up_accuracy=94.44%, primary_pass_rate=88.89%, gap_exact_match_rate=88.89%, avg_gap_recall=0.9333, avg_predicted_score=6.78

### by_interview_type

- `Behavioural`: score_range_accuracy=100.0%, follow_up_accuracy=100.0%, primary_pass_rate=100.0%, gap_exact_match_rate=100.0%, avg_gap_recall=1.0, avg_predicted_score=7.0
- `Mixed`: score_range_accuracy=66.67%, follow_up_accuracy=66.67%, primary_pass_rate=66.67%, gap_exact_match_rate=33.33%, avg_gap_recall=0.6, avg_predicted_score=6.67
- `Technical Core`: score_range_accuracy=88.89%, follow_up_accuracy=100.0%, primary_pass_rate=88.89%, gap_exact_match_rate=100.0%, avg_gap_recall=1.0, avg_predicted_score=6.67

### by_seniority

- `Junior`: score_range_accuracy=80.0%, follow_up_accuracy=100.0%, primary_pass_rate=80.0%, gap_exact_match_rate=80.0%, avg_gap_recall=0.96, avg_predicted_score=2.0
- `Middle`: score_range_accuracy=92.31%, follow_up_accuracy=92.31%, primary_pass_rate=92.31%, gap_exact_match_rate=92.31%, avg_gap_recall=0.9231, avg_predicted_score=8.62

### by_answer_quality_label

- `medium`: score_range_accuracy=75.0%, follow_up_accuracy=75.0%, primary_pass_rate=75.0%, gap_exact_match_rate=75.0%, avg_gap_recall=0.75, avg_predicted_score=6.5
- `strong`: score_range_accuracy=100.0%, follow_up_accuracy=100.0%, primary_pass_rate=100.0%, gap_exact_match_rate=100.0%, avg_gap_recall=1.0, avg_predicted_score=9.5
- `weak`: score_range_accuracy=75.0%, follow_up_accuracy=100.0%, primary_pass_rate=75.0%, gap_exact_match_rate=75.0%, avg_gap_recall=0.95, avg_predicted_score=0.25

## Failed Cases

- `frontend_003`: score=0 expected=[1, 2], follow_up=True expected_follow_up=True
- `frontend_011`: score=10 expected=[8, 9], follow_up=False expected_follow_up=True
