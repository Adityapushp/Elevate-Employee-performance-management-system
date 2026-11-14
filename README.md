# Elevate — Employee Performance Management System

A three-tier employee performance management web application backed by a reproducible synthetic-data pipeline. It supports goals and measurable key results, check-ins with evidence, competency feedback, review-cycle reporting, development plans and approval decisions. All bundled employee data is synthetic.

## 1. Traditional three-tier architecture

```text
┌───────────────────────────────────────────────────────────────┐
│ TIER 1 — PRESENTATION / FRONTEND                              │
│ React + TypeScript + Vite                                     │
│ Dashboards · Goals · Check-ins · Reviews · Feedback · People  │
└──────────────────────────────┬────────────────────────────────┘
                               │ HTTPS / JSON / JWT
┌──────────────────────────────▼────────────────────────────────┐
│ TIER 2 — APPLICATION / BACKEND                                │
│ Node.js + Express + JWT                                       │
│ REST API · Authentication · RBAC · Workflow rules · Services  │
└──────────────────────────────┬────────────────────────────────┘
                               │ SQL / transactions
┌──────────────────────────────▼────────────────────────────────┐
│ TIER 3 — DATA / DATABASE                                      │
│ PostgreSQL 16                                                 │
│ Relational entities · constraints · foreign keys · audit trail│
└───────────────────────────────────────────────────────────────┘

Independent data engineering pipeline:
Python generator → CSV / JSON / SQL → PostgreSQL import
                       └────────────→ ground_truth.csv (kept separate)
```

The browser never connects directly to PostgreSQL. React communicates only with the Express REST API. The API authenticates users, validates requests and applies business rules before accessing PostgreSQL. Python is used for deterministic synthetic data generation and validation; it is not a second runtime backend.

## 2. Technology stack

| Tier / concern | Technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite | Interactive HR/manager/employee workspace |
| Backend | Node.js, Express | REST endpoints and request orchestration |
| Authentication | JWT | Signed sessions and password-hash verification |
| Database | PostgreSQL 16, `pg` | Persistent relational data and transactions |
| Data generation | Python standard library | Deterministic synthetic records and validation |
| Quality | Node Test Runner, Pytest, GitHub Actions | Unit tests and CI |
| Deployment | Docker, Docker Compose | Reproducible local environment |

Pandas and Spring Boot are not used.

## 3. Features

- Organization overview with employee, goal, check-in, review and development-plan metrics.
- People directory with employee role and reporting information.
- Goal creation with a measurable key result created alongside each goal.
- Goal approval restricted to the employee's current manager (or system administrator).
- Check-in submission validates goal ownership, approved goal state, cycle state and key-result membership.
- Key-result progress is calculated from baseline, target and reported value; goal progress is calculated as a weighted average.
- Evidence must use HTTPS and is required when the reported key-result progress reaches 80%.
- Self, manager and peer feedback is linked to review assignments and competency ratings.
- Development plans support manager approval and conditional HR approval when the budget exceeds USD 1,500.
- Mutations create append-only state-event records; review finalization is blocked until all required reviewer inputs are received and a manager rating exists.
- Analytics summarize goal status, review status, department progress and feedback type.

## 4. Demo credentials

The Docker seed script creates four local demo accounts. All use the same development-only password:

| Role | Email | Password |
|---|---|---|
| System administrator / HR demo | `hr.admin@example.test` | `DemoPass123!` |
| Manager | `manager@example.test` | `DemoPass123!` |
| Employee / reviewee | `employee@example.test` | `DemoPass123!` |
| Peer reviewer | `peer@example.test` | `DemoPass123!` |

These are local demo credentials only. Change them and set a strong `JWT_SECRET` before any deployment. Do not use real employee data in this demo environment.

## 5. Run with Docker Compose (recommended)

Prerequisites: Docker Desktop (Windows/macOS) or Docker Engine + Compose (Linux).

From the repository root:

```bash
docker compose up --build
```

Open:
- Frontend: http://localhost: and responsive UI |5173
- Backend health: http://localhost:8000/api/health
- API base: http://localhost:8000/api
- PostgreSQL: `localhost:5432` (database/user `epms`; development password `epms_dev_password`)

Stop the stack:

```bash
docker compose down
```

Remove the local database volume (this deletes local DB data):

```bash
docker compose down -v
```

## 6. Run without Docker

You need Node.js 20+, PostgreSQL 16+, and Python 3.10+.

1. Create a PostgreSQL database and user, then set the environment variables:

```bash
# Example PowerShell values; use your own secure values outside local development
$env:DATABASE_URL = "postgresql://epms:epms_dev_password@localhost:5432/epms"
$env:JWT_SECRET = "replace-with-a-long-random-secret"
$env:CORS_ORIGINS = "http://localhost:5173"
```

2. Install and initialize the backend:

```bash
cd backend
npm install
node src/db/migrate.js
node src/db/seed-demo.js
npm run dev
```

3. In another terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

4. Open http://localhost:5173.

## 7. Synthetic data generation and PostgreSQL import

The deterministic Python generator is retained. Full scale uses the requested volumes: 3,000 employees, 500 managers, 10,000 goals and 20,000 check-ins, plus dependent records and labelled edge cases.

Generate the full dataset:

```bash
python generator/generate.py --seed 20261022 --scale 1.0 --out out/full --verify-repro
```

Generate a smaller dataset using the same generator logic:

```bash
python generator/generate.py --seed 20261022 --scale 0.05 --out out/starter --verify-repro
```

Install the PostgreSQL importer dependency:

```bash
python -m pip install -r scripts/requirements.txt
```

Import generated operational tables into the running PostgreSQL database (this replaces existing operational demo rows):

```bash
python scripts/import_generated_data.py --input out/starter/csv --replace
```

Use `out/full/csv` for the full dataset. The importer deliberately excludes `ground_truth.csv`; that file is an evaluation artifact and must not be loaded into application feature tables. Keep it separate when evaluating anomaly detection.

## 8. REST API

All endpoints except `/api/health` and `/api/auth/login` require a bearer token.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Authenticate and receive JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/health` | Database health |
| GET | `/api/overview` | Dashboard metrics |
| GET | `/api/cycles` | Review cycles |
| GET | `/api/competencies` | Competency catalogue |
| GET | `/api/employees` | Employee directory / search |
| GET | `/api/goals` | Goals and owner/cycle names |
| GET | `/api/goals/:goalId/key-results` | Goal key results |
| POST | `/api/goals` | Create goal and key result |
| POST | `/api/goals/:goalId/approve` | Current manager approval |
| GET | `/api/checkins` | Check-in history |
| POST | `/api/checkins` | Submit check-in and evidence |
| GET | `/api/reviews` | Review status and completion |
| GET | `/api/feedback` | Competency feedback |
| POST | `/api/feedback` | Submit traceable feedback |
| GET | `/api/development-plans` | Development plan list |
| POST | `/api/development-plans` | Create plan and request approval |
| POST | `/api/development-plans/:planId/manager-decision` | Manager approval / rejection |
| POST | `/api/development-plans/:planId/hr-decision` | Conditional HR approval / rejection |
| POST | `/api/reviews/:reviewId/finalize` | Finalize a complete manager-submitted review |
| GET | `/api/analytics` | Aggregated performance metrics |

## 9. Business rules and exceptions

- A goal must belong to an existing employee and a non-closed review cycle.
- Goal due date must be within the cycle; employee/cycle goal weights cannot exceed 100%.
- A check-in is accepted only for the goal owner and an active, manager-approved goal in an open cycle.
- Key-result progress is derived from baseline/target/current value; lower-is-better metrics use inverse progress arithmetic.
- Progress above 100% requires an approved rationale; progress cannot exceed the configured cycle scale.
- Evidence is required at 80% key-result progress and must be HTTPS.
- Feedback must match the reviewee and an approved reviewer relationship (except self feedback).
- Development plans move through `pending_manager`, optionally `pending_hr`, then `approved` or `rejected`. Budgets above USD 1,500 require HR approval.
- Goal, check-in and development-plan mutations write state events; ground-truth labels remain separate.

## 10. Tests and validation

Backend unit tests:

```bash
cd backend
npm install
npm test
```

Synthetic generator tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Frontend production build:

```bash
cd frontend
npm install
npm run build
```

CI runs backend unit tests, generator tests and the frontend production build on pushes and pull requests. For an end-to-end environment check, use `docker compose up --build` and sign in with the demo HR account.

## 11. Data model and documentation

The generator's `schema.py` is the canonical field dictionary for the synthetic entities. PostgreSQL schema is in `database/schema.sql`. Additional documentation:

- `docs/architecture.md`
- `docs/business-rules.md`
- `full/data_dictionary.md` and `starter/data_dictionary.md`
- `full/validation_summary.md` and `starter/validation_summary.md`
- `full/source_manifest.json` and `starter/source_manifest.json`

Core entities include Employee, Manager, manager assignments, ReviewCycle, Goal, KeyResult, CheckIn, check-in/KR bridge, evidence links, Competency, Review, reviewer assignments, Feedback, DevelopmentPlan and state events.

## 12. Lawful provenance and security note

All included employee names, emails and work records are synthetic. Emails use the reserved `example.test` domain and evidence links use non-resolvable example URLs. No confidential employee data or external personal dataset is used. This is an interview/assignment prototype, not a production HR system. Before production use, add managed secrets, TLS termination, stronger account provisioning, password reset, SSO/MFA, audit retention policies, CSRF protections where cookie auth is used, backups, monitoring and a security review.
