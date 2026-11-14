import bcrypt from 'bcryptjs';
import { pool } from './pool.js';
const now = new Date().toISOString();
const demoEmployees = [
    ['EMP-000001', 'Aarav Mehta', 'aarav.mehta@example.test', 'Engineering', 'L3', 'Software Engineer', 'Hyderabad', '2022-04-11', null, 'active', 'employee', 'MGR-000001'],
    ['EMP-000002', 'Mira Kapoor', 'mira.kapoor@example.test', 'Engineering', 'L5', 'Engineering Manager', 'Hyderabad', '2018-02-12', null, 'active', 'manager', null],
    ['EMP-000003', 'Kabir Rao', 'kabir.rao@example.test', 'Product', 'L5', 'Product Manager', 'Bengaluru', '2019-07-08', null, 'active', 'manager', 'MGR-000001'],
    ['EMP-000004', 'Anaya Iyer', 'anaya.iyer@example.test', 'Engineering', 'L2', 'Frontend Engineer', 'Hyderabad', '2023-08-21', null, 'active', 'employee', 'MGR-000001'],
    ['EMP-000005', 'Ishaan Shah', 'ishaan.shah@example.test', 'Product', 'L3', 'Product Analyst', 'Bengaluru', '2021-11-15', null, 'active', 'employee', 'MGR-000002']
];
try {
    const c = await pool.connect();
    try {
        await c.query('BEGIN');
        const count = await c.query('SELECT COUNT(*)::int AS n FROM employees');
        if (count.rows[0].n === 0) {
            for (const e of demoEmployees) await c.query(`INSERT INTO employees(employee_id,full_name,email,department,job_level,job_title,location,hire_date,termination_date,employment_status,system_role,manager_id) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)`, e);
            await c.query(`INSERT INTO managers(manager_id,employee_id,parent_manager_id,department,org_level,effective_from,status) VALUES
        ('MGR-000001','EMP-000002',NULL,'Engineering',1,'2018-02-12','active'),
        ('MGR-000002','EMP-000003','MGR-000001','Product',2,'2019-07-08','active')`);
            await c.query(`INSERT INTO manager_assignments(assignment_id,employee_id,manager_id,effective_from,effective_to,change_reason) VALUES
        ('MA-000001','EMP-000001','MGR-000001','2022-04-11',NULL,'initial_hire'),
        ('MA-000002','EMP-000004','MGR-000001','2023-08-21',NULL,'initial_hire'),
        ('MA-000003','EMP-000005','MGR-000002','2021-11-15',NULL,'initial_hire'),
        ('MA-000004','EMP-000003','MGR-000001','2019-07-08',NULL,'initial_hire')`);
            await c.query(`INSERT INTO review_cycles(cycle_id,cycle_name,start_date,end_date,goal_setting_deadline,review_window_start,review_window_end,closed_at,status,max_progress_pct)
        VALUES('CYCLE-2026-H2','2026 Half-Year Review','2026-07-01','2026-12-31','2026-07-31','2026-11-01','2026-12-20',NULL,'open',120)`);
            await c.query(`INSERT INTO competencies(competency_id,competency_name,category,description,rating_scale_min,rating_scale_max) VALUES
        ('COMP-01','Execution','Execution','Delivers reliable outcomes against commitments.',1,5),
        ('COMP-02','Collaboration','Collaboration','Works effectively across teams.',1,5),
        ('COMP-03','Leadership','Leadership','Creates clarity and supports others.',1,5),
        ('COMP-04','Craft','Craft','Demonstrates strong role-specific skills.',1,5)`);
            await c.query(`INSERT INTO goals(goal_id,employee_id,cycle_id,title,description,category,weight_pct,start_date,due_date,status,version,created_at,approved_by,approved_at,updated_at,progress_pct,cancelled_reason) VALUES
        ('GOAL-EMP-000001-001','EMP-000001','CYCLE-2026-H2','Improve API reliability','Reduce service errors and improve operational reliability.','performance',60,'2026-07-01','2026-12-15','active',1,$1,'MGR-000001',$1,$1,62,NULL),
        ('GOAL-EMP-000001-002','EMP-000001','CYCLE-2026-H2','Improve engineering documentation','Create and maintain onboarding and API documentation.','development',40,'2026-07-01','2026-12-15','draft',1,$1,NULL,NULL,$1,0,NULL),
        ('GOAL-EMP-000004-001','EMP-000004','CYCLE-2026-H2','Deliver accessible UI components','Improve accessibility coverage across shared components.','performance',100,'2026-07-01','2026-12-15','active',1,$1,'MGR-000001',$1,$1,78,NULL)`, [now]);
            await c.query(`INSERT INTO key_results(kr_id,goal_id,description,metric_type,unit,direction,baseline_value,target_value,weight,current_value,progress_pct,scoring_progress_pct,over_achievement_rationale,max_progress_pct) VALUES
        ('KR-GOAL-EMP-000001-001-01','GOAL-EMP-000001-001','Reduce 5xx error rate','percentage','percent','decrease',5,1,0.6,2.52,62,62,NULL,120),
        ('KR-GOAL-EMP-000001-001-02','GOAL-EMP-000001-001','Increase integration test coverage','percentage','percent','increase',50,90,0.4,74.8,62,62,NULL,120),
        ('KR-GOAL-EMP-000001-002-01','GOAL-EMP-000001-002','Publish core API guides','count','guides','increase',0,8,1,0,0,0,NULL,120),
        ('KR-GOAL-EMP-000004-001-01','GOAL-EMP-000004-001','Accessible component coverage','percentage','percent','increase',60,95,1,87.3,78,78,NULL,120)`);
            await c.query(`INSERT INTO check_ins(checkin_id,goal_id,employee_id,submitted_by,checkin_date,checkin_type,cumulative_progress_pct,expected_progress_pct,confidence,comment,evidence_required,evidence_count) VALUES
        ('CHK-000001','GOAL-EMP-000001-001','EMP-000001','EMP-000001','2026-10-28','self_update',62,65,'on_track','Reduced error rate after retry and timeout improvements.',FALSE,0),
        ('CHK-000002','GOAL-EMP-000004-001','EMP-000004','EMP-000004','2026-11-02','self_update',78,70,'on_track','Added keyboard navigation and accessible labels.',FALSE,0)`);
            await c.query(`INSERT INTO check_in_kr_values(value_id,checkin_id,kr_id,reported_value,progress_pct) VALUES
        ('CKV-000001','CHK-000001','KR-GOAL-EMP-000001-001-01',2.52,62),
        ('CKV-000002','CHK-000002','KR-GOAL-EMP-000004-001-01',87.3,78)`);
            await c.query(`INSERT INTO evidence_links(evidence_id,checkin_id,evidence_type,url,added_at) VALUES('EVD-000001','CHK-000002','pull_request','https://evidence.example.test/pr/204',$1)`, [now]);
            await c.query(`INSERT INTO reviews(review_id,employee_id,cycle_id,manager_id,status,manager_changed_in_cycle,goal_count,goal_progress_score,avg_self_rating,avg_manager_rating,avg_peer_rating,required_inputs,received_inputs,completion_pct,feedback_conflict_flag,final_rating,rating_band,score_as_of)
        VALUES('REV-2026-000001','EMP-000001','CYCLE-2026-H2','MGR-000001','manager_submitted',FALSE,2,62,4.2,4.1,4.5,4,4,100,FALSE,NULL,NULL,CURRENT_DATE),
              ('REV-2026-000002','EMP-000004','CYCLE-2026-H2','MGR-000001','not_started',FALSE,1,78,NULL,NULL,NULL,4,0,0,FALSE,NULL,NULL,CURRENT_DATE)`);
            await c.query(`INSERT INTO reviewer_assignments(assignment_id,review_id,reviewee_id,reviewer_id,relationship_type,relationship_basis,approved_by,status,requested_at,due_date,responded_at) VALUES
        ('RA-000001','REV-2026-000001','EMP-000001','EMP-000001','self','self',NULL,'submitted',$1,'2026-12-10',$1),
        ('RA-000002','REV-2026-000001','EMP-000001','EMP-000002','manager','direct_manager','MGR-000001','submitted',$1,'2026-12-10',NULL),
        ('RA-000003','REV-2026-000001','EMP-000001','EMP-000004','peer','same_team','MGR-000001','submitted',$1,'2026-12-10',$1),
        ('RA-000004','REV-2026-000001','EMP-000001','EMP-000005','peer','cross_functional_approved','MGR-000001','submitted',$1,'2026-12-10',$1)`, [now]);
            await c.query(`INSERT INTO feedback(feedback_id,review_id,assignment_id,reviewee_id,reviewer_id,feedback_type,competency_id,rating,comment,evidence_ref_type,evidence_ref_id,submitted_at,submission_channel)
        VALUES('FB-000001','REV-2026-000001','RA-000001','EMP-000001','EMP-000001','self','COMP-01',4,'I consistently met sprint commitments and improved service reliability.',NULL,NULL,$1,'app'),
              ('FB-000002','REV-2026-000001','RA-000003','EMP-000001','EMP-000004','peer','COMP-02',4,'Collaborates well and shares context during reviews.',NULL,NULL,$1,'app'),
              ('FB-000003','REV-2026-000001','RA-000002','EMP-000001','EMP-000002','manager','COMP-03',4,'Demonstrates ownership and communicates delivery risks early.',NULL,NULL,$1,'app'),
              ('FB-000004','REV-2026-000001','RA-000004','EMP-000001','EMP-000005','peer','COMP-04',5,'Brings strong technical judgment and helps unblock cross-functional work.',NULL,NULL,$1,'app')`, [now]);
            await c.query(`INSERT INTO development_plans(dev_plan_id,review_id,employee_id,competency_id,plan_type,activity_type,action_description,budget_usd,created_at,submitted_at,manager_approver_id,manager_decision,manager_decided_at,requires_hr_approval,hr_approver_id,hr_decision,hr_decided_at,start_date,target_date,completed_at,status)
        VALUES('DP-000001','REV-2026-000001','EMP-000001','COMP-03','voluntary','mentoring','Complete a cross-team technical leadership rotation.',500,$1,$1,'MGR-000001',NULL,NULL,FALSE,NULL,NULL,NULL,'2026-11-15','2027-02-28',NULL,'pending_manager')`, [now]);
            await c.query(`INSERT INTO state_events(event_id,entity_type,entity_id,event_type,from_state,to_state,field_changed,old_value,new_value,actor_id,approved_by,approval_status,reason,occurred_at) VALUES
        ('EVT-000001','Goal','GOAL-EMP-000001-001','approved','draft','active','status','draft','active','EMP-000002','MGR-000001','approved','Manager approved initial goal.',$1)`, [now]);
        }
        const users = [
            { email: 'hr.admin@example.test', password: 'DemoPass123!', role: 'sysadmin', employeeId: 'EMP-000002' },
            { email: 'manager@example.test', password: 'DemoPass123!', role: 'manager', employeeId: 'EMP-000002' },
            { email: 'employee@example.test', password: 'DemoPass123!', role: 'employee', employeeId: 'EMP-000001' },
            { email: 'peer@example.test', password: 'DemoPass123!', role: 'employee', employeeId: 'EMP-000004' }
        ];
        for (const u of users) {
            const hash = await bcrypt.hash(u.password, 10);
            await c.query(`INSERT INTO app_users(employee_id,email,password_hash,role) VALUES($1,$2,$3,$4) ON CONFLICT(email) DO NOTHING`, [u.employeeId, u.email, hash, u.role]);
        }
        await c.query('COMMIT');
        console.log('Demo data and demo users are ready.');
    } catch (e) { await c.query('ROLLBACK'); throw e; } finally { c.release(); }
} finally { await pool.end(); }