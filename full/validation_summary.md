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
| goal_owner_mismatch | 30 |
| progress_exceeds_scale_no_rationale | 50 |
| reviewer_lacks_relationship | 50 |
| closed_cycle_silent_edit | 40 |
| feedback_untraceable | 40 |
| incomplete_review | 291 |
| conflicting_feedback | 265 |
| manager_transfer_mid_cycle | 179 |
| goal_changed | 1057 |

## Distribution summary

```json
{
 "goals_by_status": {
  "completed": 2703,
  "not_achieved": 2684,
  "cancelled": 100,
  "active": 4440,
  "draft": 73
 },
 "goals_per_employee_cycle_mean": 1.71,
 "goal_progress_mean": 52.1,
 "goal_progress_median": 53.2,
 "goal_progress_stdev": 27.8,
 "kr_per_goal_mean": 1.89,
 "checkins_per_goal_mean": 2.0,
 "checkin_confidence": {
  "on_track": 12323,
  "at_risk": 5134,
  "off_track": 2543
 },
 "feedback_rating_distribution": {
  "1": 508,
  "2": 2622,
  "3": 7697,
  "4": 10047,
  "5": 6404
 },
 "review_status_by_cycle": {
  "CYCLE-2026-H1": {
   "finalized": 2634,
   "closed_incomplete": 291
  },
  "CYCLE-2026-H2": {
   "not_started": 2912
  }
 },
 "final_rating_bands": {
  "Meets Expectations": 1424,
  "Exceeds Expectations": 345,
  "Developing": 752,
  "Outstanding": 42,
  "Needs Improvement": 71
 },
 "kr_over_100_with_rationale": 907,
 "kr_over_100_without_rationale": 50,
 "kr_zero_progress": 1779,
 "kr_max_progress": 159.85,
 "span_of_control_mean": 6.0,
 "transfers": 179,
 "dev_plan_status": {
  "rejected": 103,
  "approved": 70,
  "in_progress": 858,
  "draft": 82,
  "pending_manager": 27,
  "pending_hr": 17,
  "completed": 5
 },
 "corr_goal_score_vs_manager_rating": 0.42
}
```
