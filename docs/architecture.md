# Architecture

## Strict three-tier structure

1. **Presentation:** `frontend/` contains React + TypeScript screens and calls the REST API. It does not contain database credentials or SQL.
2. **Application:** `backend/` contains Express routes, JWT middleware, Zod request validation and business services. It owns permissions, lifecycle decisions, calculations and transaction orchestration.
3. **Data:** `database/schema.sql` defines PostgreSQL tables, keys, constraints and indexes. Only the backend connects to PostgreSQL.

The Python generator is a separate data-engineering utility. It produces synthetic CSV/JSON/SQL and validation evidence. The importer maps operational CSV files into PostgreSQL. It intentionally skips `ground_truth.csv`.

## Request path

`React UI → HTTP/JSON + bearer JWT → Express route → service/business rule → PostgreSQL transaction → JSON response → React state refresh`.

## Main cardinalities

- Employee 1:N Goals; ReviewCycle 1:N Goals.
- Goal 1:N KeyResults; Goal 1:N CheckIns.
- CheckIn N:M KeyResult through `check_in_kr_values`.
- Employee N:M Manager over time through effective-dated `manager_assignments`.
- Review N:M Employee reviewers through `reviewer_assignments`.
- ReviewerAssignment 1:N Feedback; Competency 1:N Feedback.
- Review 1:N DevelopmentPlans.
- Goal / CheckIn / DevelopmentPlan 1:N state events (polymorphic entity reference).

## Persistence and traceability

Business mutations execute in PostgreSQL transactions. Key-result progress and weighted goal progress are calculated from source values. State events are appended rather than overwriting prior event history. Goal approval increments the version counter. Ground-truth anomaly labels are not loaded into application tables by the provided importer.
