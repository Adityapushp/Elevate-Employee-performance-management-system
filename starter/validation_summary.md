# Validation summary

**278 / 278 checks passed.**

| Category | Passed |
|---|---|
| A. Primary keys | 16 / 16 |
| B. Foreign keys | 38 / 38 |
| C. Allowed values | 35 / 35 |
| C. Required fields | 141 / 141 |
| D. Date ordering | 9 / 9 |
| F. Arithmetic / derived | 16 / 16 |
| G. Lifecycle | 7 / 7 |
| H. Duplicates | 7 / 7 |
| I. Anomaly reconciliation | 9 / 9 |

## Anomaly / scenario labels (ground_truth)

| issue_type | rows |
|---|---|
| goal_owner_mismatch | 2 |
| progress_exceeds_scale_no_rationale | 2 |
| reviewer_lacks_relationship | 2 |
| closed_cycle_silent_edit | 2 |
| feedback_untraceable | 2 |
| incomplete_review | 13 |
| conflicting_feedback | 10 |
| manager_transfer_mid_cycle | 8 |
| goal_changed | 63 |

## Distribution summary

```json
{
 "goals_by_status": {
  "completed": 131,
  "not_achieved": 137,
  "cancelled": 3,
  "active": 228,
  "draft": 1
 },
 "goals_per_employee_cycle_mean": 1.69,
 "goal_progress_mean": 50.0,
 "goal_progress_median": 49.8,
 "goal_progress_stdev": 28.6,
 "kr_per_goal_mean": 1.92,
 "checkins_per_goal_mean": 2.0,
 "checkin_confidence": {
  "on_track": 589,
  "off_track": 150,
  "at_risk": 261
 },
 "feedback_rating_distribution": {
  "1": 40,
  "2": 133,
  "3": 387,
  "4": 529,
  "5": 294
 },
 "review_status_by_cycle": {
  "CYCLE-2026-H1": {
   "closed_incomplete": 13,
   "finalized": 133
  },
  "CYCLE-2026-H2": {
   "not_started": 149
  }
 },
 "final_rating_bands": {
  "Developing": 37,
  "Outstanding": 3,
  "Meets Expectations": 67,
  "Needs Improvement": 7,
  "Exceeds Expectations": 19
 },
 "kr_over_100_with_rationale": 44,
 "kr_over_100_without_rationale": 2,
 "kr_zero_progress": 82,
 "kr_max_progress": 156.52,
 "span_of_control_mean": 6.0,
 "transfers": 8,
 "dev_plan_status": {
  "in_progress": 50,
  "draft": 6,
  "rejected": 7,
  "pending_hr": 3,
  "pending_manager": 2,
  "approved": 1
 },
 "corr_goal_score_vs_manager_rating": 0.456
}
```
