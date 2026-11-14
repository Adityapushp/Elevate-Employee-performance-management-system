-- PostgreSQL schema generated from the canonical synthetic-data dictionary.

BEGIN;

CREATE TABLE IF NOT EXISTS "employees" (
  "employee_id" TEXT PRIMARY KEY,
  "full_name" TEXT NOT NULL,
  "email" TEXT NOT NULL UNIQUE,
  "department" TEXT NOT NULL CHECK ("department" IN ('Engineering', 'Product', 'Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'Customer Success')),
  "job_level" TEXT NOT NULL CHECK ("job_level" IN ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7')),
  "job_title" TEXT NOT NULL,
  "location" TEXT NOT NULL CHECK ("location" IN ('Hyderabad', 'Bengaluru', 'Pune', 'Mumbai', 'Delhi NCR', 'Remote')),
  "hire_date" DATE NOT NULL,
  "termination_date" DATE,
  "employment_status" TEXT NOT NULL CHECK ("employment_status" IN ('active', 'on_leave', 'terminated')),
  "system_role" TEXT NOT NULL CHECK ("system_role" IN ('employee', 'manager', 'hr_partner', 'it_ops', 'sysadmin')),
  "manager_id" TEXT
);

CREATE TABLE IF NOT EXISTS "managers" (
  "manager_id" TEXT PRIMARY KEY,
  "employee_id" TEXT NOT NULL UNIQUE,
  "parent_manager_id" TEXT,
  "department" TEXT NOT NULL,
  "org_level" INTEGER NOT NULL,
  "effective_from" DATE NOT NULL,
  "status" TEXT NOT NULL CHECK ("status" IN ('active', 'inactive'))
);

CREATE TABLE IF NOT EXISTS "manager_assignments" (
  "assignment_id" TEXT PRIMARY KEY,
  "employee_id" TEXT NOT NULL,
  "manager_id" TEXT NOT NULL,
  "effective_from" DATE NOT NULL,
  "effective_to" DATE,
  "change_reason" TEXT NOT NULL CHECK ("change_reason" IN ('initial_hire', 'transfer', 'reorg'))
);

CREATE TABLE IF NOT EXISTS "review_cycles" (
  "cycle_id" TEXT PRIMARY KEY,
  "cycle_name" TEXT NOT NULL,
  "start_date" DATE NOT NULL,
  "end_date" DATE NOT NULL,
  "goal_setting_deadline" DATE NOT NULL,
  "review_window_start" DATE NOT NULL,
  "review_window_end" DATE NOT NULL,
  "closed_at" TIMESTAMPTZ,
  "status" TEXT NOT NULL CHECK ("status" IN ('planned', 'open', 'closed')),
  "max_progress_pct" DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS "competencies" (
  "competency_id" TEXT PRIMARY KEY,
  "competency_name" TEXT NOT NULL UNIQUE,
  "category" TEXT NOT NULL CHECK ("category" IN ('Execution', 'Collaboration', 'Leadership', 'Craft')),
  "description" TEXT NOT NULL,
  "rating_scale_min" INTEGER NOT NULL,
  "rating_scale_max" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "goals" (
  "goal_id" TEXT PRIMARY KEY,
  "employee_id" TEXT NOT NULL,
  "cycle_id" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "category" TEXT NOT NULL CHECK ("category" IN ('performance', 'development', 'strategic')),
  "weight_pct" DOUBLE PRECISION NOT NULL,
  "start_date" DATE NOT NULL,
  "due_date" DATE NOT NULL,
  "status" TEXT NOT NULL CHECK ("status" IN ('draft', 'active', 'completed', 'not_achieved', 'cancelled')),
  "version" INTEGER NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL,
  "approved_by" TEXT,
  "approved_at" TIMESTAMPTZ,
  "updated_at" TIMESTAMPTZ NOT NULL,
  "progress_pct" DOUBLE PRECISION NOT NULL,
  "cancelled_reason" TEXT
);

CREATE TABLE IF NOT EXISTS "key_results" (
  "kr_id" TEXT PRIMARY KEY,
  "goal_id" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "metric_type" TEXT NOT NULL CHECK ("metric_type" IN ('percentage', 'count', 'currency_usd', 'score', 'duration_days', 'defect_rate_pct')),
  "unit" TEXT NOT NULL,
  "direction" TEXT NOT NULL CHECK ("direction" IN ('increase', 'decrease')),
  "baseline_value" DOUBLE PRECISION NOT NULL,
  "target_value" DOUBLE PRECISION NOT NULL,
  "weight" DOUBLE PRECISION NOT NULL,
  "current_value" DOUBLE PRECISION NOT NULL,
  "progress_pct" DOUBLE PRECISION NOT NULL,
  "scoring_progress_pct" DOUBLE PRECISION NOT NULL,
  "over_achievement_rationale" TEXT,
  "max_progress_pct" DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS "check_ins" (
  "checkin_id" TEXT PRIMARY KEY,
  "goal_id" TEXT NOT NULL,
  "employee_id" TEXT NOT NULL,
  "submitted_by" TEXT NOT NULL,
  "checkin_date" DATE NOT NULL,
  "checkin_type" TEXT NOT NULL CHECK ("checkin_type" IN ('self_update', 'manager_review')),
  "cumulative_progress_pct" DOUBLE PRECISION NOT NULL,
  "expected_progress_pct" DOUBLE PRECISION NOT NULL,
  "confidence" TEXT NOT NULL CHECK ("confidence" IN ('on_track', 'at_risk', 'off_track')),
  "comment" TEXT NOT NULL,
  "evidence_required" BOOLEAN NOT NULL,
  "evidence_count" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "check_in_kr_values" (
  "value_id" TEXT PRIMARY KEY,
  "checkin_id" TEXT NOT NULL,
  "kr_id" TEXT NOT NULL,
  "reported_value" DOUBLE PRECISION NOT NULL,
  "progress_pct" DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS "evidence_links" (
  "evidence_id" TEXT PRIMARY KEY,
  "checkin_id" TEXT NOT NULL,
  "evidence_type" TEXT NOT NULL CHECK ("evidence_type" IN ('document', 'dashboard', 'ticket', 'pull_request', 'report', 'presentation')),
  "url" TEXT NOT NULL UNIQUE,
  "added_at" TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS "reviews" (
  "review_id" TEXT PRIMARY KEY,
  "employee_id" TEXT NOT NULL,
  "cycle_id" TEXT NOT NULL,
  "manager_id" TEXT NOT NULL,
  "status" TEXT NOT NULL CHECK ("status" IN ('not_started', 'self_submitted', 'manager_submitted', 'finalized', 'closed_incomplete')),
  "manager_changed_in_cycle" BOOLEAN NOT NULL,
  "self_submitted_at" TIMESTAMPTZ,
  "manager_submitted_at" TIMESTAMPTZ,
  "finalized_at" TIMESTAMPTZ,
  "goal_count" INTEGER NOT NULL,
  "goal_progress_score" DOUBLE PRECISION,
  "avg_self_rating" DOUBLE PRECISION,
  "avg_manager_rating" DOUBLE PRECISION,
  "avg_peer_rating" DOUBLE PRECISION,
  "required_inputs" INTEGER NOT NULL,
  "received_inputs" INTEGER NOT NULL,
  "completion_pct" DOUBLE PRECISION NOT NULL,
  "feedback_conflict_flag" BOOLEAN NOT NULL,
  "final_rating" DOUBLE PRECISION,
  "rating_band" TEXT CHECK ("rating_band" IN ('Needs Improvement', 'Developing', 'Meets Expectations', 'Exceeds Expectations', 'Outstanding')),
  "score_as_of" DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS "reviewer_assignments" (
  "assignment_id" TEXT PRIMARY KEY,
  "review_id" TEXT NOT NULL,
  "reviewee_id" TEXT NOT NULL,
  "reviewer_id" TEXT NOT NULL,
  "relationship_type" TEXT NOT NULL CHECK ("relationship_type" IN ('self', 'manager', 'peer')),
  "relationship_basis" TEXT NOT NULL CHECK ("relationship_basis" IN ('self', 'direct_manager', 'same_team', 'same_department', 'cross_functional_approved')),
  "approved_by" TEXT,
  "status" TEXT NOT NULL CHECK ("status" IN ('requested', 'submitted', 'declined', 'expired')),
  "requested_at" TIMESTAMPTZ NOT NULL,
  "due_date" DATE NOT NULL,
  "responded_at" TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS "feedback" (
  "feedback_id" TEXT PRIMARY KEY,
  "review_id" TEXT NOT NULL,
  "assignment_id" TEXT,
  "reviewee_id" TEXT NOT NULL,
  "reviewer_id" TEXT,
  "feedback_type" TEXT NOT NULL CHECK ("feedback_type" IN ('self', 'manager', 'peer')),
  "competency_id" TEXT NOT NULL,
  "rating" INTEGER NOT NULL,
  "comment" TEXT NOT NULL,
  "evidence_ref_type" TEXT CHECK ("evidence_ref_type" IN ('goal', 'check_in')),
  "evidence_ref_id" TEXT,
  "submitted_at" TIMESTAMPTZ NOT NULL,
  "submission_channel" TEXT NOT NULL CHECK ("submission_channel" IN ('app', 'import'))
);

CREATE TABLE IF NOT EXISTS "development_plans" (
  "dev_plan_id" TEXT PRIMARY KEY,
  "review_id" TEXT NOT NULL,
  "employee_id" TEXT NOT NULL,
  "competency_id" TEXT NOT NULL,
  "plan_type" TEXT NOT NULL CHECK ("plan_type" IN ('mandatory', 'voluntary')),
  "activity_type" TEXT NOT NULL CHECK ("activity_type" IN ('course', 'mentoring', 'stretch_assignment', 'certification', 'coaching')),
  "action_description" TEXT NOT NULL,
  "budget_usd" INTEGER NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL,
  "submitted_at" TIMESTAMPTZ,
  "manager_approver_id" TEXT,
  "manager_decision" TEXT CHECK ("manager_decision" IN ('approved', 'rejected')),
  "manager_decided_at" TIMESTAMPTZ,
  "requires_hr_approval" BOOLEAN NOT NULL,
  "hr_approver_id" TEXT,
  "hr_decision" TEXT CHECK ("hr_decision" IN ('approved', 'rejected')),
  "hr_decided_at" TIMESTAMPTZ,
  "start_date" DATE NOT NULL,
  "target_date" DATE NOT NULL,
  "completed_at" DATE,
  "status" TEXT NOT NULL CHECK ("status" IN ('draft', 'pending_manager', 'pending_hr', 'rejected', 'approved', 'in_progress', 'completed'))
);

CREATE TABLE IF NOT EXISTS "state_events" (
  "event_id" TEXT PRIMARY KEY,
  "entity_type" TEXT NOT NULL CHECK ("entity_type" IN ('Goal', 'Review', 'DevelopmentPlan', 'CheckIn')),
  "entity_id" TEXT NOT NULL,
  "event_type" TEXT NOT NULL CHECK ("event_type" IN ('created', 'approved', 'submitted', 'status_change', 'target_changed', 'title_changed', 'due_date_changed', 'cancelled', 'edit_after_close', 'manager_decision', 'hr_decision', 'finalized', 'closed_incomplete')),
  "from_state" TEXT,
  "to_state" TEXT,
  "field_changed" TEXT,
  "old_value" TEXT,
  "new_value" TEXT,
  "actor_id" TEXT,
  "approved_by" TEXT,
  "approval_status" TEXT NOT NULL CHECK ("approval_status" IN ('approved', 'not_required', 'none')),
  "reason" TEXT,
  "occurred_at" TIMESTAMPTZ NOT NULL
);

ALTER TABLE "employees" DROP CONSTRAINT IF EXISTS "fk_employees_manager_id";

ALTER TABLE "employees" ADD CONSTRAINT "fk_employees_manager_id" FOREIGN KEY ("manager_id") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "managers" DROP CONSTRAINT IF EXISTS "fk_managers_employee_id";

ALTER TABLE "managers" ADD CONSTRAINT "fk_managers_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "managers" DROP CONSTRAINT IF EXISTS "fk_managers_parent_manager_id";

ALTER TABLE "managers" ADD CONSTRAINT "fk_managers_parent_manager_id" FOREIGN KEY ("parent_manager_id") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "manager_assignments" DROP CONSTRAINT IF EXISTS "fk_manager_assignments_employee_id";

ALTER TABLE "manager_assignments" ADD CONSTRAINT "fk_manager_assignments_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "manager_assignments" DROP CONSTRAINT IF EXISTS "fk_manager_assignments_manager_id";

ALTER TABLE "manager_assignments" ADD CONSTRAINT "fk_manager_assignments_manager_id" FOREIGN KEY ("manager_id") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "goals" DROP CONSTRAINT IF EXISTS "fk_goals_employee_id";

ALTER TABLE "goals" ADD CONSTRAINT "fk_goals_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "goals" DROP CONSTRAINT IF EXISTS "fk_goals_cycle_id";

ALTER TABLE "goals" ADD CONSTRAINT "fk_goals_cycle_id" FOREIGN KEY ("cycle_id") REFERENCES "review_cycles"("cycle_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "goals" DROP CONSTRAINT IF EXISTS "fk_goals_approved_by";

ALTER TABLE "goals" ADD CONSTRAINT "fk_goals_approved_by" FOREIGN KEY ("approved_by") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "key_results" DROP CONSTRAINT IF EXISTS "fk_key_results_goal_id";

ALTER TABLE "key_results" ADD CONSTRAINT "fk_key_results_goal_id" FOREIGN KEY ("goal_id") REFERENCES "goals"("goal_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "check_ins" DROP CONSTRAINT IF EXISTS "fk_check_ins_goal_id";

ALTER TABLE "check_ins" ADD CONSTRAINT "fk_check_ins_goal_id" FOREIGN KEY ("goal_id") REFERENCES "goals"("goal_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "check_ins" DROP CONSTRAINT IF EXISTS "fk_check_ins_employee_id";

ALTER TABLE "check_ins" ADD CONSTRAINT "fk_check_ins_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "check_ins" DROP CONSTRAINT IF EXISTS "fk_check_ins_submitted_by";

ALTER TABLE "check_ins" ADD CONSTRAINT "fk_check_ins_submitted_by" FOREIGN KEY ("submitted_by") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "check_in_kr_values" DROP CONSTRAINT IF EXISTS "fk_check_in_kr_values_checkin_id";

ALTER TABLE "check_in_kr_values" ADD CONSTRAINT "fk_check_in_kr_values_checkin_id" FOREIGN KEY ("checkin_id") REFERENCES "check_ins"("checkin_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "check_in_kr_values" DROP CONSTRAINT IF EXISTS "fk_check_in_kr_values_kr_id";

ALTER TABLE "check_in_kr_values" ADD CONSTRAINT "fk_check_in_kr_values_kr_id" FOREIGN KEY ("kr_id") REFERENCES "key_results"("kr_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "evidence_links" DROP CONSTRAINT IF EXISTS "fk_evidence_links_checkin_id";

ALTER TABLE "evidence_links" ADD CONSTRAINT "fk_evidence_links_checkin_id" FOREIGN KEY ("checkin_id") REFERENCES "check_ins"("checkin_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviews" DROP CONSTRAINT IF EXISTS "fk_reviews_employee_id";

ALTER TABLE "reviews" ADD CONSTRAINT "fk_reviews_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviews" DROP CONSTRAINT IF EXISTS "fk_reviews_cycle_id";

ALTER TABLE "reviews" ADD CONSTRAINT "fk_reviews_cycle_id" FOREIGN KEY ("cycle_id") REFERENCES "review_cycles"("cycle_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviews" DROP CONSTRAINT IF EXISTS "fk_reviews_manager_id";

ALTER TABLE "reviews" ADD CONSTRAINT "fk_reviews_manager_id" FOREIGN KEY ("manager_id") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviewer_assignments" DROP CONSTRAINT IF EXISTS "fk_reviewer_assignments_review_id";

ALTER TABLE "reviewer_assignments" ADD CONSTRAINT "fk_reviewer_assignments_review_id" FOREIGN KEY ("review_id") REFERENCES "reviews"("review_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviewer_assignments" DROP CONSTRAINT IF EXISTS "fk_reviewer_assignments_reviewee_id";

ALTER TABLE "reviewer_assignments" ADD CONSTRAINT "fk_reviewer_assignments_reviewee_id" FOREIGN KEY ("reviewee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviewer_assignments" DROP CONSTRAINT IF EXISTS "fk_reviewer_assignments_reviewer_id";

ALTER TABLE "reviewer_assignments" ADD CONSTRAINT "fk_reviewer_assignments_reviewer_id" FOREIGN KEY ("reviewer_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "reviewer_assignments" DROP CONSTRAINT IF EXISTS "fk_reviewer_assignments_approved_by";

ALTER TABLE "reviewer_assignments" ADD CONSTRAINT "fk_reviewer_assignments_approved_by" FOREIGN KEY ("approved_by") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "feedback" DROP CONSTRAINT IF EXISTS "fk_feedback_review_id";

ALTER TABLE "feedback" ADD CONSTRAINT "fk_feedback_review_id" FOREIGN KEY ("review_id") REFERENCES "reviews"("review_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "feedback" DROP CONSTRAINT IF EXISTS "fk_feedback_assignment_id";

ALTER TABLE "feedback" ADD CONSTRAINT "fk_feedback_assignment_id" FOREIGN KEY ("assignment_id") REFERENCES "reviewer_assignments"("assignment_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "feedback" DROP CONSTRAINT IF EXISTS "fk_feedback_reviewee_id";

ALTER TABLE "feedback" ADD CONSTRAINT "fk_feedback_reviewee_id" FOREIGN KEY ("reviewee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "feedback" DROP CONSTRAINT IF EXISTS "fk_feedback_reviewer_id";

ALTER TABLE "feedback" ADD CONSTRAINT "fk_feedback_reviewer_id" FOREIGN KEY ("reviewer_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "feedback" DROP CONSTRAINT IF EXISTS "fk_feedback_competency_id";

ALTER TABLE "feedback" ADD CONSTRAINT "fk_feedback_competency_id" FOREIGN KEY ("competency_id") REFERENCES "competencies"("competency_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "development_plans" DROP CONSTRAINT IF EXISTS "fk_development_plans_review_id";

ALTER TABLE "development_plans" ADD CONSTRAINT "fk_development_plans_review_id" FOREIGN KEY ("review_id") REFERENCES "reviews"("review_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "development_plans" DROP CONSTRAINT IF EXISTS "fk_development_plans_employee_id";

ALTER TABLE "development_plans" ADD CONSTRAINT "fk_development_plans_employee_id" FOREIGN KEY ("employee_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "development_plans" DROP CONSTRAINT IF EXISTS "fk_development_plans_competency_id";

ALTER TABLE "development_plans" ADD CONSTRAINT "fk_development_plans_competency_id" FOREIGN KEY ("competency_id") REFERENCES "competencies"("competency_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "development_plans" DROP CONSTRAINT IF EXISTS "fk_development_plans_manager_approver_id";

ALTER TABLE "development_plans" ADD CONSTRAINT "fk_development_plans_manager_approver_id" FOREIGN KEY ("manager_approver_id") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "development_plans" DROP CONSTRAINT IF EXISTS "fk_development_plans_hr_approver_id";

ALTER TABLE "development_plans" ADD CONSTRAINT "fk_development_plans_hr_approver_id" FOREIGN KEY ("hr_approver_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "state_events" DROP CONSTRAINT IF EXISTS "fk_state_events_actor_id";

ALTER TABLE "state_events" ADD CONSTRAINT "fk_state_events_actor_id" FOREIGN KEY ("actor_id") REFERENCES "employees"("employee_id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "state_events" DROP CONSTRAINT IF EXISTS "fk_state_events_approved_by";

ALTER TABLE "state_events" ADD CONSTRAINT "fk_state_events_approved_by" FOREIGN KEY ("approved_by") REFERENCES "managers"("manager_id") DEFERRABLE INITIALLY DEFERRED;

CREATE TABLE IF NOT EXISTS app_users (
  user_id BIGSERIAL PRIMARY KEY,
  employee_id TEXT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('employee','manager','hr_partner','it_ops','sysadmin')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_goals_employee_cycle ON goals(employee_id, cycle_id);
CREATE INDEX IF NOT EXISTS idx_checkins_goal_date ON check_ins(goal_id, checkin_date);
CREATE INDEX IF NOT EXISTS idx_feedback_reviewee ON feedback(reviewee_id, submitted_at);
CREATE INDEX IF NOT EXISTS idx_state_events_entity ON state_events(entity_type, entity_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_manager_assignments_current ON manager_assignments(employee_id, effective_to);


COMMIT;
