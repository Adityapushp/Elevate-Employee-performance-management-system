# Synthetic Performance-Management Dataset

Goals, key results, check-ins, competency feedback, reviews and development plans with evidence-based progress tracking.
Fixed seed **20261022**, scale **1.0** (3,000 employees, 500 managers, 10,000 goals, 20,000 check-ins). **All data is synthetic.**

## Reproduce
```
python generate.py --seed 20261022 --scale 1.0 --out full --verify-repro
```
Same generator for every size: `--scale 1.0` is the full dataset (3,000 / 500 / 10,000 / 20,000), `--scale 0.05` is the starter set.
Standard library only (Python 3.9+). Reproducibility check (two runs, same seed, sha256 of every CSV/JSON/SQL file): **PASS - identical row counts and sha256 for all 34 files across two runs** (`reproducibility_report.json`).
Dates are anchored to an as-of date of **2026-10-22**; no wall-clock time is used.

## Contents
| Folder / file | Purpose |
|---|---|
| `csv/`, `json/` | One file per table (identical content) |
| `sql/schema.sql`, `sql/seed_data.sql` | SQLite-compatible DDL (PK/FK/UNIQUE/NOT NULL, deferred FKs) and INSERTs |
| `csv/ground_truth.csv` | Labels for injected anomalies and natural scenarios. **Never use as input features.** |
| `data_dictionary.md/.csv` | Every field: type, required, allowed values, unit, uniqueness, validation rule, FK |
| `validation_summary.md/.json` | 278/278 checks passed, distributions, label counts |
| `source_manifest.json`, `reproducibility_report.json`, `checksums_sha256.json` | Provenance, reproducibility, row counts and hashes |

### Row counts
| Table | Rows |
|---|---|
| employees | 3000 |
| managers | 500 |
| manager_assignments | 3178 |
| review_cycles | 2 |
| competencies | 12 |
| goals | 10000 |
| key_results | 18923 |
| check_ins | 20000 |
| check_in_kr_values | 33775 |
| evidence_links | 12293 |
| reviews | 5837 |
| reviewer_assignments | 12284 |
| feedback | 27278 |
| development_plans | 1162 |
| state_events | 45533 |
| ground_truth | 2002 |

## Entities, keys and cardinality
| Relationship | Cardinality | Notes |
|---|---|---|
| managers -> employees (role) | 1:1 optional | A manager is an employee (`managers.employee_id` unique) |
| managers -> managers (`parent_manager_id`) | 1:N, optional | Acyclic org tree; root has no parent |
| employees <-> managers via `manager_assignments` | N:M over time (bridge, effective-dated) | Transfers add a row and close the old one; `employees.manager_id` mirrors the open row |
| review_cycles -> goals | 1:N | Goal ids `GOAL-<employee-id>-NNN` embed the owner |
| employees -> goals | 1:N | |
| goals -> key_results | 1:N (1-3) | KR weights sum to 1 |
| goals -> check_ins | 1:N (optional) | |
| check_ins <-> key_results via `check_in_kr_values` | N:M (bridge) | One reported value per KR per check-in |
| check_ins -> evidence_links | 1:N (optional) | Mandatory when any reported KR is >= 80% |
| review_cycles + employees -> reviews | 1:1 per (employee, cycle) | `REV-2026-NNNNNN` |
| reviews <-> employees via `reviewer_assignments` | N:M (bridge) | Self, manager of record, peers (team / department / approved cross-functional) |
| reviewer_assignments -> feedback | 1:N | One row per competency rated; `assignment_id` is the traceability link |
| competencies -> feedback | 1:N | 12 competencies, 1-5 scale |
| reviews -> development_plans | 1:N (optional) | Finalized reviews only |
| any entity -> state_events | 1:N (append-only) | Goals, reviews and plans; history is never overwritten |

### Lifecycle states
* **Goal**: `draft -> active -> completed | not_achieved | cancelled`. Changes (target, title, due date) are approved events and bump `version`. After a cycle closes, content changes need an approved reopen.
* **Review**: `not_started -> self_submitted -> manager_submitted -> finalized`, or `closed_incomplete` when the cycle closes without self + manager + at least one peer input. The manager review cannot precede the self review.
* **Development plan**: `draft -> pending_manager -> (pending_hr if budget > 1500) -> approved -> in_progress -> completed`, or `rejected`. Mandatory when a competency is rated <= 2 by the manager or the band is Needs Improvement; otherwise voluntary.
* **Cycles**: `CYCLE-2026-H1` is closed (2026-08-15); `CYCLE-2026-H2` is open at the as-of date, so its reviews are provisioned as `not_started` and the review window (Dec 2026) has not opened (no assignments or feedback yet; goals and check-ins are live).

## Derived values (computed from source records, never drawn independently)
* KR `current_value` = latest reported value; `progress_pct = (current - baseline) / (target - baseline)`, floored at 0 (works for decrease-is-better KRs).
* `scoring_progress_pct` caps at 100, or at 120 when an over-achievement rationale exists.
* Goal progress = sum(KR weight x scoring progress). Goal status follows progress (>= 70 completed) and cycle state.
* Review goal score = weight-weighted mean of goal progress; ratings averaged from permitted feedback; `final_rating = 0.6 x (1 + 4 x min(score,120)/120) + 0.4 x manager average`; bands at 2 / 3 / 4 / 4.5.
* `completion_pct = min(received / 4, 1)`; conflict flag when self vs manager averages differ by >= 1.5 or any competency's ratings spread >= 3.
* Feedback without an assignment is excluded from scores, so injected anomalies do not silently change unrelated results.

## Injected anomalies and scenarios (`ground_truth`)
| issue_type | Rows |
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

Injected: goal owner mismatch (stored owner differs from the id embedded in `goal_id`), progress above scale without rationale, reviewer without a relationship (no assignment, unrelated reviewer), silent edit after cycle close (unapproved event after `closed_at`), untraceable feedback (no reviewer and no assignment). Natural scenarios arise from the rules: changed goals, manager transfers, incomplete reviews and conflicting feedback. Validation contains independent detectors that rediscover each injected label exactly (precision and recall of 1.0 against the labels) without reading the ground truth.

## Validation
278 of 278 checks pass: primary-key uniqueness, foreign-key integrity (also via a SQLite load with `PRAGMA foreign_key_check`), enums, required fields, date ordering, arithmetic reconciliation, lifecycle transitions, event-chain continuity, duplicates and anomaly reconciliation. Details in `validation_summary.md`.

## Provenance and lawful use
No external data. Names are random combinations of common first/last names and do not refer to real people; e-mail uses the reserved `example.test` domain; evidence URLs are non-resolvable. See `source_manifest.json`.

## Known simplifications
* Two cycles (H1 closed, H2 open); the organisation root is not reviewed (no manager).
* `reviewer_assignments` for H2 do not exist yet because the H2 review window has not opened.
* Check-in values follow a smooth progress curve with noise; peer selection is random within team/department pools.
