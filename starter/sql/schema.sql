PRAGMA foreign_keys = ON;

CREATE TABLE employees (
  employee_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  department TEXT NOT NULL,
  job_level TEXT NOT NULL,
  job_title TEXT NOT NULL,
  location TEXT NOT NULL,
  hire_date TEXT NOT NULL,
  termination_date TEXT,
  employment_status TEXT NOT NULL,
  system_role TEXT NOT NULL,
  manager_id TEXT,
  FOREIGN KEY (manager_id) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE managers (
  manager_id TEXT PRIMARY KEY,
  employee_id TEXT NOT NULL UNIQUE,
  parent_manager_id TEXT,
  department TEXT NOT NULL,
  org_level INTEGER NOT NULL,
  effective_from TEXT NOT NULL,
  status TEXT NOT NULL,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (parent_manager_id) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE manager_assignments (
  assignment_id TEXT PRIMARY KEY,
  employee_id TEXT NOT NULL,
  manager_id TEXT NOT NULL,
  effective_from TEXT NOT NULL,
  effective_to TEXT,
  change_reason TEXT NOT NULL,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (manager_id) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE review_cycles (
  cycle_id TEXT PRIMARY KEY,
  cycle_name TEXT NOT NULL,
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  goal_setting_deadline TEXT NOT NULL,
  review_window_start TEXT NOT NULL,
  review_window_end TEXT NOT NULL,
  closed_at TEXT,
  status TEXT NOT NULL,
  max_progress_pct REAL NOT NULL
);

CREATE TABLE competencies (
  competency_id TEXT PRIMARY KEY,
  competency_name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  description TEXT NOT NULL,
  rating_scale_min INTEGER NOT NULL,
  rating_scale_max INTEGER NOT NULL
);

CREATE TABLE goals (
  goal_id TEXT PRIMARY KEY,
  employee_id TEXT NOT NULL,
  cycle_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  weight_pct REAL NOT NULL,
  start_date TEXT NOT NULL,
  due_date TEXT NOT NULL,
  status TEXT NOT NULL,
  version INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  approved_by TEXT,
  approved_at TEXT,
  updated_at TEXT NOT NULL,
  progress_pct REAL NOT NULL,
  cancelled_reason TEXT,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (cycle_id) REFERENCES review_cycles(cycle_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (approved_by) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE key_results (
  kr_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  description TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  unit TEXT NOT NULL,
  direction TEXT NOT NULL,
  baseline_value REAL NOT NULL,
  target_value REAL NOT NULL,
  weight REAL NOT NULL,
  current_value REAL NOT NULL,
  progress_pct REAL NOT NULL,
  scoring_progress_pct REAL NOT NULL,
  over_achievement_rationale TEXT,
  max_progress_pct REAL NOT NULL,
  FOREIGN KEY (goal_id) REFERENCES goals(goal_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE check_ins (
  checkin_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  employee_id TEXT NOT NULL,
  submitted_by TEXT NOT NULL,
  checkin_date TEXT NOT NULL,
  checkin_type TEXT NOT NULL,
  cumulative_progress_pct REAL NOT NULL,
  expected_progress_pct REAL NOT NULL,
  confidence TEXT NOT NULL,
  comment TEXT NOT NULL,
  evidence_required INTEGER NOT NULL,
  evidence_count INTEGER NOT NULL,
  FOREIGN KEY (goal_id) REFERENCES goals(goal_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (submitted_by) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE check_in_kr_values (
  value_id TEXT PRIMARY KEY,
  checkin_id TEXT NOT NULL,
  kr_id TEXT NOT NULL,
  reported_value REAL NOT NULL,
  progress_pct REAL NOT NULL,
  FOREIGN KEY (checkin_id) REFERENCES check_ins(checkin_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (kr_id) REFERENCES key_results(kr_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE evidence_links (
  evidence_id TEXT PRIMARY KEY,
  checkin_id TEXT NOT NULL,
  evidence_type TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  added_at TEXT NOT NULL,
  FOREIGN KEY (checkin_id) REFERENCES check_ins(checkin_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE reviews (
  review_id TEXT PRIMARY KEY,
  employee_id TEXT NOT NULL,
  cycle_id TEXT NOT NULL,
  manager_id TEXT NOT NULL,
  status TEXT NOT NULL,
  manager_changed_in_cycle INTEGER NOT NULL,
  self_submitted_at TEXT,
  manager_submitted_at TEXT,
  finalized_at TEXT,
  goal_count INTEGER NOT NULL,
  goal_progress_score REAL,
  avg_self_rating REAL,
  avg_manager_rating REAL,
  avg_peer_rating REAL,
  required_inputs INTEGER NOT NULL,
  received_inputs INTEGER NOT NULL,
  completion_pct REAL NOT NULL,
  feedback_conflict_flag INTEGER NOT NULL,
  final_rating REAL,
  rating_band TEXT,
  score_as_of TEXT NOT NULL,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (cycle_id) REFERENCES review_cycles(cycle_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (manager_id) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE reviewer_assignments (
  assignment_id TEXT PRIMARY KEY,
  review_id TEXT NOT NULL,
  reviewee_id TEXT NOT NULL,
  reviewer_id TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  relationship_basis TEXT NOT NULL,
  approved_by TEXT,
  status TEXT NOT NULL,
  requested_at TEXT NOT NULL,
  due_date TEXT NOT NULL,
  responded_at TEXT,
  FOREIGN KEY (review_id) REFERENCES reviews(review_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (reviewee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (reviewer_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (approved_by) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE feedback (
  feedback_id TEXT PRIMARY KEY,
  review_id TEXT NOT NULL,
  assignment_id TEXT,
  reviewee_id TEXT NOT NULL,
  reviewer_id TEXT,
  feedback_type TEXT NOT NULL,
  competency_id TEXT NOT NULL,
  rating INTEGER NOT NULL,
  comment TEXT NOT NULL,
  evidence_ref_type TEXT,
  evidence_ref_id TEXT,
  submitted_at TEXT NOT NULL,
  submission_channel TEXT NOT NULL,
  FOREIGN KEY (review_id) REFERENCES reviews(review_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (assignment_id) REFERENCES reviewer_assignments(assignment_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (reviewee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (reviewer_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (competency_id) REFERENCES competencies(competency_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE development_plans (
  dev_plan_id TEXT PRIMARY KEY,
  review_id TEXT NOT NULL,
  employee_id TEXT NOT NULL,
  competency_id TEXT NOT NULL,
  plan_type TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  action_description TEXT NOT NULL,
  budget_usd INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  submitted_at TEXT,
  manager_approver_id TEXT,
  manager_decision TEXT,
  manager_decided_at TEXT,
  requires_hr_approval INTEGER NOT NULL,
  hr_approver_id TEXT,
  hr_decision TEXT,
  hr_decided_at TEXT,
  start_date TEXT NOT NULL,
  target_date TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL,
  FOREIGN KEY (review_id) REFERENCES reviews(review_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (employee_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (competency_id) REFERENCES competencies(competency_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (manager_approver_id) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (hr_approver_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE state_events (
  event_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  from_state TEXT,
  to_state TEXT,
  field_changed TEXT,
  old_value TEXT,
  new_value TEXT,
  actor_id TEXT,
  approved_by TEXT,
  approval_status TEXT NOT NULL,
  reason TEXT,
  occurred_at TEXT NOT NULL,
  FOREIGN KEY (actor_id) REFERENCES employees(employee_id) DEFERRABLE INITIALLY DEFERRED,
  FOREIGN KEY (approved_by) REFERENCES managers(manager_id) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE ground_truth (
  gt_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  issue_type TEXT NOT NULL,
  label_class TEXT NOT NULL,
  expected_decision TEXT NOT NULL,
  rule_violated TEXT NOT NULL,
  related_entity_id TEXT
);
