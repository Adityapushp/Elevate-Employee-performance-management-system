# Business rules

- Goals are created in non-closed cycles, have a valid employee owner, and fit within the employee/cycle 100% weight allocation.
- Goals begin as `draft`; the current manager approves them before check-ins are accepted.
- Key-result progress derives from baseline, target, current value and metric direction. Goal progress is the weighted average of key-result scoring progress.
- Progress above 100% requires an approved over-achievement rationale; progress is capped by the review cycle scale.
- Check-ins are rejected for closed cycles, draft goals, mismatched owners or key results belonging to another goal.
- Evidence links must use HTTPS. Evidence is required when progress reaches 80%.
- Feedback is tied to a review, competency and reviewer assignment. Self feedback must be authored by the reviewee; manager/peer feedback must have a valid assignment.
- Development plans require manager approval. Plans with a budget above USD 1,500 additionally require HR approval.
- Goal/check-in/development-plan actions append state events. The synthetic data generator separately injects and labels anomaly examples; labels are not application features.

- Review completion is based on distinct submitted reviewer assignments against required inputs. A manager-submitted review can be finalized only when completion is 100% and manager competency feedback exists; finalization records a final rating and state event.
- Feedback conflict is derived when self and manager averages differ by at least 1.5 points or competency ratings for the same competency have a spread of at least 3 points.
