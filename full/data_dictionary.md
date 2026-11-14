# Data dictionary

Generated from `schema.py` (single source of truth for exports, SQL DDL and validation).

## employees  (3000 rows, PK `employee_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| employee_id | str | Y | EMP-NNNNNN | - | Y | Zero-padded 6 digits; immutable |
| full_name | str | Y | synthetic name | - | N | Synthetic combination of common first/last names; not a real person |
| email | str | Y | first.last.<n>@example.test | - | Y | Lower-case; reserved example.test domain; unique |
| department | str | Y | enum:Engineering,Product,Sales,Marketing,Finance,HR,Operations,Customer Success | - | N | Home department (does not change on manager transfer) |
| job_level | str | Y | enum:L1,L2,L3,L4,L5,L6,L7 | - | N | Managers must be L4 or above; level follows org depth |
| job_title | str | Y | free text | - | N | Derived from level + department |
| location | str | Y | enum:Hyderabad,Bengaluru,Pune,Mumbai,Delhi NCR,Remote | - | N | Work location |
| hire_date | date | Y | 2012-01-02..2026-10-01 | - | N | <= as-of date (2026-10-22) |
| termination_date | date | N | date | - | N | Present iff employment_status=terminated; > hire_date |
| employment_status | str | Y | enum:active,on_leave,terminated | - | N | Terminated employees are excluded from open-cycle participation |
| system_role | str | Y | enum:employee,manager,hr_partner,it_ops,sysadmin | - | N | 'manager' iff the employee has a row in managers |
| manager_id | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id; equals the open row of manager_assignments; NULL only for organisation root |

## managers  (500 rows, PK `manager_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| manager_id | str | Y | MGR-NNNNNN | - | Y | Immutable; one manager role per employee |
| employee_id | str | Y | EMP-NNNNNN | - | Y | FK:employees.employee_id; the employee who holds the manager role; unique (1:1) |
| parent_manager_id | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id; NULL only for root; hierarchy must be acyclic |
| department | str | Y | department names | - | N | Home department of the manager |
| org_level | int | Y | 1..6 | level | N | 1 = root; child level = parent level + 1 |
| effective_from | date | Y | date | - | N | >= manager's hire_date |
| status | str | Y | enum:active,inactive | - | N | All generated managers are active |

## manager_assignments  (3178 rows, PK `assignment_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| assignment_id | str | Y | MA-NNNNNN | - | Y | Immutable |
| employee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id; reportee |
| manager_id | str | Y | MGR-NNNNNN | - | N | FK:managers.manager_id; may not be the employee's own manager role |
| effective_from | date | Y | date | - | N | Start of reporting line (>= hire_date) |
| effective_to | date | N | date | - | N | NULL = current line; intervals per employee must not overlap; exactly one open row per reportee |
| change_reason | str | Y | enum:initial_hire,transfer,reorg | - | N | Transfers create a new row; history is never overwritten |

## review_cycles  (2 rows, PK `cycle_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| cycle_id | str | Y | CYCLE-YYYY-Hn | - | Y | Immutable |
| cycle_name | str | Y | free text | - | N |  |
| start_date | date | Y | date | - | N | < end_date |
| end_date | date | Y | date | - | N |  |
| goal_setting_deadline | date | Y | date | - | N | >= start_date |
| review_window_start | date | Y | date | - | N | >= start_date |
| review_window_end | date | Y | date | - | N | >= review_window_start |
| closed_at | datetime | N | ISO-8601 | - | N | NULL while open; after closed_at goals are locked (changes need an approved reopen) |
| status | str | Y | enum:planned,open,closed | - | N | closed iff closed_at is not NULL |
| max_progress_pct | float | Y | 120 | percent | N | Defined progress scale cap; progress > 100 requires a rationale |

## competencies  (12 rows, PK `competency_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| competency_id | str | Y | COMP-NN | - | Y | Immutable |
| competency_name | str | Y | free text | - | Y |  |
| category | str | Y | enum:Execution,Collaboration,Leadership,Craft | - | N |  |
| description | str | Y | free text | - | N |  |
| rating_scale_min | int | Y | 1 | rating | N |  |
| rating_scale_max | int | Y | 5 | rating | N |  |

## goals  (10000 rows, PK `goal_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| goal_id | str | Y | GOAL-<employee-id>-NNN | - | Y | Embeds owner employee id; sequence is per employee across cycles |
| employee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id; owner; must equal the id embedded in goal_id |
| cycle_id | str | Y | CYCLE-YYYY-Hn | - | N | FK:review_cycles.cycle_id |
| title | str | Y | free text | - | N | Current title (history in state_events) |
| description | str | Y | free text | - | N |  |
| category | str | Y | enum:performance,development,strategic | - | N |  |
| weight_pct | float | Y | 5..100 | percent | N | Initial weights per employee+cycle sum to 100 |
| start_date | date | Y | date | - | N | <= due_date |
| due_date | date | Y | date | - | N | <= cycle end_date |
| status | str | Y | enum:draft,active,completed,not_achieved,cancelled | - | N | completed if progress_pct >= 70; not_achieved = closed cycle with progress < 70 |
| version | int | Y | >=1 | count | N | 1 + number of approved change events (target/title/due-date) in state_events |
| created_at | datetime | Y | ISO-8601 | - | N |  |
| approved_by | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id; manager of record on approval date; NULL for draft |
| approved_at | datetime | N | ISO-8601 | - | N | >= created_at |
| updated_at | datetime | Y | ISO-8601 | - | N | Last content change; > cycle closed_at only for silent-edit anomalies |
| progress_pct | float | Y | 0..120 | percent | N | DERIVED: sum(kr.weight * kr.scoring_progress_pct) |
| cancelled_reason | str | N | free text | - | N | Present iff status=cancelled |

## key_results  (18923 rows, PK `kr_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| kr_id | str | Y | KR-<goal-id>-NN | - | Y | Immutable |
| goal_id | str | Y | GOAL-... | - | N | FK:goals.goal_id |
| description | str | Y | free text | - | N |  |
| metric_type | str | Y | enum:percentage,count,currency_usd,score,duration_days,defect_rate_pct | - | N |  |
| unit | str | Y | free text | - | N |  |
| direction | str | Y | enum:increase,decrease | - | N | decrease = lower is better |
| baseline_value | float | Y | number | metric unit | N |  |
| target_value | float | Y | number != baseline | metric unit | N | Current definition; changes are in state_events |
| weight | float | Y | 0..1 | ratio | N | Weights per goal sum to 1.0 |
| current_value | float | Y | number | metric unit | N | DERIVED: latest reported value in check_in_kr_values, else baseline |
| progress_pct | float | Y | >=0 | percent | N | DERIVED raw: (current-baseline)/(target-baseline)*100, floored at 0 |
| scoring_progress_pct | float | Y | 0..120 | percent | N | DERIVED: min(progress_pct,120) if rationale present else min(progress_pct,100) |
| over_achievement_rationale | str | N | free text | - | N | Required when progress_pct > 100 |
| max_progress_pct | float | Y | 120 | percent | N | Defined scale cap |

## check_ins  (20000 rows, PK `checkin_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| checkin_id | str | Y | CHK-NNNNNN | - | Y | Numbered in chronological order |
| goal_id | str | Y | GOAL-... | - | N | FK:goals.goal_id |
| employee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id; goal owner at creation time |
| submitted_by | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id; owner or the manager of record on checkin_date |
| checkin_date | date | Y | date | - | N | Within goal start/cycle window and <= as-of date |
| checkin_type | str | Y | enum:self_update,manager_review | - | N | manager_review iff submitted_by is not the owner |
| cumulative_progress_pct | float | Y | 0..120 | percent | N | DERIVED: weighted scoring progress after applying this check-in |
| expected_progress_pct | float | Y | 0..100 | percent | N | DERIVED: linear time elapsed between goal start and due date |
| confidence | str | Y | enum:on_track,at_risk,off_track | - | N | DERIVED: cumulative/expected >=0.9 on_track, >=0.6 at_risk, else off_track |
| comment | str | Y | free text | - | N |  |
| evidence_required | bool | Y | 0/1 | - | N | DERIVED: 1 if any KR reported >= 80% progress |
| evidence_count | int | Y | >=0 | count | N | DERIVED: rows in evidence_links; must be >=1 when evidence_required |

## check_in_kr_values  (33775 rows, PK `value_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| value_id | str | Y | CKV-NNNNNN | - | Y | Bridge: check_ins N:M key_results |
| checkin_id | str | Y | CHK-NNNNNN | - | N | FK:check_ins.checkin_id |
| kr_id | str | Y | KR-... | - | N | FK:key_results.kr_id; KR must belong to the check-in's goal |
| reported_value | float | Y | number | metric unit | N |  |
| progress_pct | float | Y | >=0 | percent | N | DERIVED raw progress at this check-in |

## evidence_links  (12293 rows, PK `evidence_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| evidence_id | str | Y | EVD-NNNNNN | - | Y |  |
| checkin_id | str | Y | CHK-NNNNNN | - | N | FK:check_ins.checkin_id |
| evidence_type | str | Y | enum:document,dashboard,ticket,pull_request,report,presentation | - | N |  |
| url | str | Y | https://evidence.example.test/... | - | Y | Synthetic non-resolvable URL |
| added_at | datetime | Y | ISO-8601 | - | N | Same day as the check-in |

## reviews  (5837 rows, PK `review_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| review_id | str | Y | REV-YYYY-NNNNNN | - | Y | Counter is continuous within a year |
| employee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id; reviewee; unique per cycle |
| cycle_id | str | Y | CYCLE-YYYY-Hn | - | N | FK:review_cycles.cycle_id |
| manager_id | str | Y | MGR-NNNNNN | - | N | FK:managers.manager_id; manager of record at min(cycle end, as-of) |
| status | str | Y | enum:not_started,self_submitted,manager_submitted,finalized,closed_incomplete | - | N | Terminal in a closed cycle: finalized or closed_incomplete |
| manager_changed_in_cycle | bool | Y | 0/1 | - | N | DERIVED: a manager_assignments row starts inside the cycle |
| self_submitted_at | datetime | N | ISO-8601 | - | N |  |
| manager_submitted_at | datetime | N | ISO-8601 | - | N | > self_submitted_at |
| finalized_at | datetime | N | ISO-8601 | - | N | >= manager_submitted_at; <= cycle closed_at |
| goal_count | int | Y | >=0 | count | N | DERIVED: goals owned (stored owner) in cycle excluding draft/cancelled |
| goal_progress_score | float | N | 0..120 | percent | N | DERIVED: weight_pct-weighted mean of goals.progress_pct |
| avg_self_rating | float | N | 1..5 | rating | N | DERIVED from feedback |
| avg_manager_rating | float | N | 1..5 | rating | N | DERIVED from feedback |
| avg_peer_rating | float | N | 1..5 | rating | N | DERIVED from feedback |
| required_inputs | int | Y | 4 | count | N | Self + manager + 2 peers |
| received_inputs | int | Y | >=0 | count | N | DERIVED: submitted reviewer_assignments |
| completion_pct | float | Y | 0..100 | percent | N | DERIVED: min(received/required,1)*100 |
| feedback_conflict_flag | bool | Y | 0/1 | - | N | DERIVED: abs(avg_self-avg_manager)>=1.5 or any competency rating spread >=3 |
| final_rating | float | N | 1..5 | rating | N | DERIVED (finalized only): 0.6*(1+4*min(score,120)/120)+0.4*avg_manager_rating |
| rating_band | str | N | enum:Needs Improvement,Developing,Meets Expectations,Exceeds Expectations,Outstanding | - | N | DERIVED from final_rating thresholds 2/3/4/4.5 |
| score_as_of | date | Y | date | - | N | min(cycle end, as-of date) |

## reviewer_assignments  (12284 rows, PK `assignment_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| assignment_id | str | Y | RA-NNNNNN | - | Y | Authorises a reviewer to give feedback (bridge reviews N:M employees) |
| review_id | str | Y | REV-... | - | N | FK:reviews.review_id |
| reviewee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id |
| reviewer_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id |
| relationship_type | str | Y | enum:self,manager,peer | - | N | manager reviewer must be the manager of record |
| relationship_basis | str | Y | enum:self,direct_manager,same_team,same_department,cross_functional_approved | - | N | Peers need a documented basis |
| approved_by | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id; required for cross_functional_approved |
| status | str | Y | enum:requested,submitted,declined,expired | - | N |  |
| requested_at | datetime | Y | ISO-8601 | - | N |  |
| due_date | date | Y | date | - | N |  |
| responded_at | datetime | N | ISO-8601 | - | N | NULL when expired |

## feedback  (27278 rows, PK `feedback_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| feedback_id | str | Y | FB-NNNNNN | - | Y |  |
| review_id | str | Y | REV-... | - | N | FK:reviews.review_id |
| assignment_id | str | N | RA-NNNNNN | - | N | FK:reviewer_assignments.assignment_id; NULL only for labelled anomalies |
| reviewee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id |
| reviewer_id | str | N | EMP-NNNNNN | - | N | FK:employees.employee_id; NULL only for untraceable anomalies |
| feedback_type | str | Y | enum:self,manager,peer | - | N |  |
| competency_id | str | Y | COMP-NN | - | N | FK:competencies.competency_id |
| rating | int | Y | 1..5 | rating | N |  |
| comment | str | Y | free text | - | N |  |
| evidence_ref_type | str | N | enum:goal,check_in | - | N | Optional link to evidence |
| evidence_ref_id | str | N | GOAL-... or CHK-... | - | N | Must exist in the referenced table when present |
| submitted_at | datetime | Y | ISO-8601 | - | N |  |
| submission_channel | str | Y | enum:app,import | - | N | import only for untraceable anomalies |

## development_plans  (1162 rows, PK `dev_plan_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| dev_plan_id | str | Y | DP-NNNNNN | - | Y |  |
| review_id | str | Y | REV-... | - | N | FK:reviews.review_id; only finalized reviews |
| employee_id | str | Y | EMP-NNNNNN | - | N | FK:employees.employee_id |
| competency_id | str | Y | COMP-NN | - | N | FK:competencies.competency_id |
| plan_type | str | Y | enum:mandatory,voluntary | - | N | mandatory when manager rating <= 2 on a competency or band = Needs Improvement |
| activity_type | str | Y | enum:course,mentoring,stretch_assignment,certification,coaching | - | N |  |
| action_description | str | Y | free text | - | N |  |
| budget_usd | int | Y | 0..3000 | USD | N | budget > 1500 requires HR approval |
| created_at | datetime | Y | ISO-8601 | - | N | > review finalized_at |
| submitted_at | datetime | N | ISO-8601 | - | N | >= created_at |
| manager_approver_id | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id; manager of record |
| manager_decision | str | N | enum:approved,rejected | - | N |  |
| manager_decided_at | datetime | N | ISO-8601 | - | N | >= submitted_at |
| requires_hr_approval | bool | Y | 0/1 | - | N | DERIVED: budget_usd > 1500 |
| hr_approver_id | str | N | EMP-NNNNNN | - | N | FK:employees.employee_id; must hold system_role hr_partner |
| hr_decision | str | N | enum:approved,rejected | - | N | Only after manager approval |
| hr_decided_at | datetime | N | ISO-8601 | - | N | >= manager_decided_at |
| start_date | date | Y | date | - | N |  |
| target_date | date | Y | date | - | N | > start_date |
| completed_at | date | N | date | - | N | Only for status completed |
| status | str | Y | enum:draft,pending_manager,pending_hr,rejected,approved,in_progress,completed | - | N | DERIVED from decisions and dates |

## state_events  (45533 rows, PK `event_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| event_id | str | Y | EVT-NNNNNN | - | Y | Append-only; numbered in chronological order |
| entity_type | str | Y | enum:Goal,Review,DevelopmentPlan | - | N | Polymorphic reference with entity_id |
| entity_id | str | Y | GOAL-/REV-/DP- id | - | N | Must exist in the entity's table |
| event_type | str | Y | enum:created,approved,submitted,status_change,target_changed,title_changed,due_date_changed,cancelled,edit_after_close,manager_decision,hr_decision,finalized,closed_incomplete | - | N |  |
| from_state | str | N | status | - | N | NULL for creation or pure field edits |
| to_state | str | N | status | - | N |  |
| field_changed | str | N | free text | - | N |  |
| old_value | str | N | free text | - | N |  |
| new_value | str | N | free text | - | N |  |
| actor_id | str | N | EMP-NNNNNN | - | N | FK:employees.employee_id; NULL = system |
| approved_by | str | N | MGR-NNNNNN | - | N | FK:managers.manager_id |
| approval_status | str | Y | enum:approved,not_required,none | - | N | none on a post-close content edit = silent edit |
| reason | str | N | free text | - | N |  |
| occurred_at | datetime | Y | ISO-8601 | - | N |  |

## ground_truth  (2002 rows, PK `gt_id`)

| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |
|---|---|---|---|---|---|---|
| gt_id | str | Y | GT-NNNNNN | - | Y | Kept in a separate file; never an input feature |
| entity_type | str | Y | table name | - | N | Table holding the labelled row |
| entity_id | str | Y | PK value | - | N | Primary key of the labelled row |
| issue_type | str | Y | enum:goal_owner_mismatch,progress_exceeds_scale_no_rationale,reviewer_lacks_relationship,closed_cycle_silent_edit,feedback_untraceable,incomplete_review,conflicting_feedback,manager_transfer_mid_cycle,goal_changed | - | N |  |
| label_class | str | Y | enum:injected_anomaly,natural_exception | - | N | injected = deliberate rule violation |
| expected_decision | str | Y | enum:reject,flag_for_review,accept_with_note | - | N | Expected system/HR decision |
| rule_violated | str | Y | free text | - | N | Documented rule |
| related_entity_id | str | N | id | - | N | Parent or counterpart record |

