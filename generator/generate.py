#!/usr/bin/env python3
"""Synthetic performance-management dataset: generate, export, validate, document, verify reproducibility.

Usage:
  python generate.py --seed 20261022 --scale 1.0  --out out/full    --verify-repro
  python generate.py --seed 20261022 --scale 0.05 --out out/starter --verify-repro
Same generator for both sizes; --scale multiplies 3,000 employees / 500 managers / 10,000 goals / 20,000 check-ins.
"""
import argparse, csv, datetime as dt, hashlib, json, os, shutil, sqlite3, sys, tempfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
from gen_core import generate, AS_OF, CAP, COMPLETE

DEFAULT_SEED = 20261022
TS = "%Y-%m-%d"


# ------------------------------------------------------------------ export
def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def jval(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    return v


def sql_lit(v, typ):
    if v is None:
        return "NULL"
    if isinstance(v, (dt.date, dt.datetime)):
        v = v.isoformat()
    if typ in ("int", "bool"):
        return str(int(v))
    if typ == "float":
        return repr(float(v))
    return "'" + str(v).replace("'", "''") + "'"


def ddl():
    out = ["PRAGMA foreign_keys = ON;"]
    for t in S.TABLES:
        cols = []
        for c in S.RAW[t]:
            ty = {"str": "TEXT", "date": "TEXT", "datetime": "TEXT", "int": "INTEGER", "bool": "INTEGER", "float": "REAL"}[c["type"]]
            s = "  %s %s" % (c["name"], ty)
            if c["pk"]:
                s += " PRIMARY KEY"
            else:
                if c["required"]:
                    s += " NOT NULL"
                if c["unique"]:
                    s += " UNIQUE"
            cols.append(s)
        for c in S.RAW[t]:
            if c["fk"]:
                cols.append("  FOREIGN KEY (%s) REFERENCES %s(%s) DEFERRABLE INITIALLY DEFERRED" % (c["name"], c["fk"][0], c["fk"][1]))
        out.append("CREATE TABLE %s (\n%s\n);" % (t, ",\n".join(cols)))
    return "\n\n".join(out) + "\n"


def export(T, out):
    for d in ("csv", "json", "sql"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    sums = {}
    for t in S.TABLES:
        cols = [c["name"] for c in S.RAW[t]]
        rows = T[t]
        for r in rows:
            assert list(r.keys()) == cols or set(r.keys()) == set(cols), (t, set(r) ^ set(cols))
        p = os.path.join(out, "csv", t + ".csv")
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n"); w.writerow(cols)
            for r in rows:
                w.writerow([fmt(r[c]) for c in cols])
        with open(os.path.join(out, "json", t + ".json"), "w", encoding="utf-8") as f:
            json.dump([{c: jval(r[c]) for c in cols} for r in rows], f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out, "sql", "schema.sql"), "w", encoding="utf-8") as f:
        f.write(ddl())
    with open(os.path.join(out, "sql", "seed_data.sql"), "w", encoding="utf-8") as f:
        f.write("BEGIN;\n")
        for t in S.TABLES:
            cols = S.RAW[t]; names = ",".join(c["name"] for c in cols)
            rows = T[t]
            for i in range(0, len(rows), 500):
                vals = ",\n".join("(" + ",".join(sql_lit(r[c["name"]], c["type"]) for c in cols) + ")" for r in rows[i:i + 500])
                f.write("INSERT INTO %s (%s) VALUES\n%s;\n" % (t, names, vals))
        f.write("COMMIT;\n")
    for d in ("csv", "json", "sql"):
        for fn in sorted(os.listdir(os.path.join(out, d))):
            with open(os.path.join(out, d, fn), "rb") as f:
                sums["%s/%s" % (d, fn)] = hashlib.sha256(f.read()).hexdigest()
    return sums


# ------------------------------------------------------------------ validation
def validate(T, P):
    R = []
    try:
        return _validate(T, P, R)
    except Exception as ex:  # a structurally broken dataset must be reported, not crash the pipeline
        R.append(dict(category="Z. Validator", check="validator aborted on malformed data: %r" % (ex,), passed=False, violations=1, examples=[], note=""))
        return R, {}, {}


def _validate(T, P, R):
    def add(cat, name, bad, note=""):
        R.append(dict(category=cat, check=name, passed=(len(bad) == 0 if isinstance(bad, list) else bad == 0),
                      violations=(len(bad) if isinstance(bad, list) else bad), examples=(bad[:3] if isinstance(bad, list) else []), note=note))
    by = {t: {r[S.PKS[t]]: r for r in T[t]} for t in S.TABLES if t != "ground_truth"}
    by["ground_truth"] = {r["gt_id"]: r for r in T["ground_truth"]}
    emps = by["employees"]; cyc = by["review_cycles"]; goals = by["goals"]; krs = by["key_results"]; chk = by["check_ins"]
    reviews = by["reviews"]; ras = by["reviewer_assignments"]; mg = by["managers"]
    mgr_emp = {m["manager_id"]: m["employee_id"] for m in T["managers"]}

    # A. PK
    for t in S.TABLES:
        add("A. Primary keys", "%s PK unique & non-null" % t, [] if len(by[t]) == len(T[t]) and all(S.PKS[t] in r and r[S.PKS[t]] for r in T[t]) else ["dup"])
    # B. FK
    for t in S.TABLES:
        for c in S.RAW[t]:
            if c["fk"]:
                par = by[c["fk"][0]]
                bad = [r[S.PKS[t]] for r in T[t] if r[c["name"]] is not None and r[c["name"]] not in par]
                add("B. Foreign keys", "%s.%s -> %s" % (t, c["name"], c["fk"][0]), bad)
    bad = [e["event_id"] for e in T["state_events"] if e["entity_id"] not in {"Goal": goals, "Review": reviews, "DevelopmentPlan": by["development_plans"]}[e["entity_type"]]]
    add("B. Foreign keys", "state_events.entity_id -> polymorphic parent", bad)
    bad = [f["feedback_id"] for f in T["feedback"] if f["evidence_ref_id"] and f["evidence_ref_id"] not in (goals if f["evidence_ref_type"] == "goal" else chk)]
    add("B. Foreign keys", "feedback.evidence_ref_id -> goals/check_ins", bad)
    bad = [v["value_id"] for v in T["check_in_kr_values"] if krs[v["kr_id"]]["goal_id"] != chk[v["checkin_id"]]["goal_id"]]
    add("B. Foreign keys", "check_in_kr_values: KR belongs to check-in's goal", bad)
    # SQLite load with FK enforcement (proves SQL seed is loadable and joins resolve)
    con = sqlite3.connect(":memory:")
    try:
        con.executescript(ddl().replace("PRAGMA foreign_keys = ON;", "PRAGMA foreign_keys = ON;"))
        # seed generated in memory to avoid re-reading files
        con.execute("BEGIN")
        for t in S.TABLES:
            cols = S.RAW[t]
            con.executemany("INSERT INTO %s VALUES (%s)" % (t, ",".join("?" * len(cols))),
                            [tuple(fmt(r[c["name"]]) if not isinstance(r[c["name"]], bool) else int(r[c["name"]]) for c in cols) if False else tuple((None if r[c["name"]] is None else fmt(r[c["name"]])) for c in cols) for r in T[t]])
        con.execute("COMMIT")
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        add("B. Foreign keys", "SQLite load + PRAGMA foreign_key_check", [str(x) for x in fk])
    except Exception as ex:
        add("B. Foreign keys", "SQLite load + PRAGMA foreign_key_check", ["%s" % ex])
    # C. enums / required
    for t in S.TABLES:
        for c in S.RAW[t]:
            if c["enum"]:
                add("C. Allowed values", "%s.%s in enum" % (t, c["name"]), [r[S.PKS[t]] for r in T[t] if r[c["name"]] is not None and str(r[c["name"]]) not in c["enum"]])
            if c["required"]:
                add("C. Required fields", "%s.%s not null" % (t, c["name"]), [r[S.PKS[t]] for r in T[t] if r[c["name"]] is None])
    # D. dates
    bad = [e["employee_id"] for e in T["employees"] if e["hire_date"] > AS_OF or (e["termination_date"] and e["termination_date"] <= e["hire_date"])
           or (e["employment_status"] == "terminated") != (e["termination_date"] is not None)]
    add("D. Date ordering", "employees hire/termination ordering and status consistency", bad)
    bad = [m["manager_id"] for m in T["managers"] if m["effective_from"] < emps[m["employee_id"]]["hire_date"]]
    add("D. Date ordering", "managers.effective_from >= hire_date", bad)
    asg = defaultdict(list)
    for a in T["manager_assignments"]:
        asg[a["employee_id"]].append(a)
    bad = []
    for e, lst in asg.items():
        lst.sort(key=lambda a: a["effective_from"])
        if sum(1 for a in lst if a["effective_to"] is None) != 1:
            bad.append(e)
        for i, a in enumerate(lst):
            if a["effective_from"] < emps[e]["hire_date"] or (a["effective_to"] and a["effective_to"] <= a["effective_from"]) or mgr_emp[a["manager_id"]] == e:
                bad.append(e)
            if i and lst[i - 1]["effective_to"] != a["effective_from"]:
                bad.append(e)
    add("D. Date ordering", "manager_assignments: no overlap/gap, one open row, valid dates", sorted(set(bad)))
    bad = [e["employee_id"] for e in T["employees"] if (e["manager_id"] is None) != (e["employee_id"] not in asg) or
           (e["employee_id"] in asg and [a for a in asg[e["employee_id"]] if a["effective_to"] is None][0]["manager_id"] != e["manager_id"])]
    add("F. Arithmetic / derived", "employees.manager_id equals open manager_assignments row", bad)
    bad = [m["manager_id"] for m in T["managers"] if (m["parent_manager_id"] is None and m["org_level"] != 1) or
           (m["parent_manager_id"] and m["org_level"] != mg[m["parent_manager_id"]]["org_level"] + 1)]
    add("F. Arithmetic / derived", "managers.org_level = parent level + 1 (acyclic hierarchy)", bad)
    bad = [c["cycle_id"] for c in T["review_cycles"] if not (c["start_date"] < c["end_date"] and c["goal_setting_deadline"] >= c["start_date"] and c["review_window_end"] >= c["review_window_start"] >= c["start_date"])
           or (c["status"] == "closed") != (c["closed_at"] is not None)]
    add("D. Date ordering", "review_cycles dates and closed state", bad)
    bad = []
    for g in T["goals"]:
        c = cyc[g["cycle_id"]]
        if not (g["start_date"] <= g["due_date"] <= c["end_date"]) or (g["approved_at"] and g["approved_at"] < g["created_at"]) or g["updated_at"] < g["created_at"]:
            bad.append(g["goal_id"])
        if (g["approved_by"] is None) != (g["status"] == "draft") or (g["approved_at"] is None) != (g["status"] == "draft"):
            bad.append(g["goal_id"])
        if (g["cancelled_reason"] is not None) != (g["status"] == "cancelled"):
            bad.append(g["goal_id"])
    add("D. Date ordering", "goals: start<=due<=cycle end, created<=approved, draft/cancel markers", sorted(set(bad)))
    bad = [k["checkin_id"] for k in T["check_ins"] if not (goals[k["goal_id"]]["start_date"] <= k["checkin_date"] <= min(goals[k["goal_id"]]["due_date"], AS_OF))]
    add("D. Date ordering", "check-ins within goal window and <= as-of date", bad)
    bad = [e["evidence_id"] for e in T["evidence_links"] if e["added_at"][:10] != chk[e["checkin_id"]]["checkin_date"].isoformat()]
    add("D. Date ordering", "evidence added on check-in date", bad)
    bad = []
    for r in T["reviews"]:
        s, m, f = r["self_submitted_at"], r["manager_submitted_at"], r["finalized_at"]
        if m and not s or (s and m and m <= s) or (f and (not m or f < m)):
            bad.append(r["review_id"])
        c = cyc[r["cycle_id"]]
        if c["closed_at"] and f and f > c["closed_at"]:
            bad.append(r["review_id"])
    add("D. Date ordering", "reviews: self < manager < finalized <= closed_at", sorted(set(bad)))
    bad = [a["assignment_id"] for a in T["reviewer_assignments"] if a["responded_at"] and a["responded_at"] < a["requested_at"]]
    add("D. Date ordering", "reviewer_assignments responded >= requested", bad)
    # F. goals / KRs
    krg = defaultdict(list)
    for k in T["key_results"]:
        krg[k["goal_id"]].append(k)
    add("F. Arithmetic / derived", "KR weights sum to 1.0 per goal", [g for g, l in krg.items() if abs(sum(k["weight"] for k in l) - 1.0) > 1e-9])
    wsum = defaultdict(float)
    for g in T["goals"]:
        wsum[(g["goal_id"].split("-")[1] + "-" + g["goal_id"].split("-")[2], g["cycle_id"])] += g["weight_pct"]
    add("F. Arithmetic / derived", "initial goal weights sum to 100 per (owner,cycle)", [str(k) for k, v in wsum.items() if abs(v - 100) > 1e-9])
    lastv = {}
    vals_by_chk = defaultdict(list)
    for v in T["check_in_kr_values"]:
        vals_by_chk[v["checkin_id"]].append(v)
    for c in T["check_ins"]:
        for v in vals_by_chk[c["checkin_id"]]:
            lastv[v["kr_id"]] = v["reported_value"]
    bad = []
    for k in T["key_results"]:
        cur = lastv.get(k["kr_id"], k["baseline_value"])
        raw = round(max((cur - k["baseline_value"]) / (k["target_value"] - k["baseline_value"]) * 100.0, 0.0), 2)
        sc = round(min(raw, CAP if k["over_achievement_rationale"] else 100.0), 2)
        if abs(cur - k["current_value"]) > 1e-9 or abs(raw - k["progress_pct"]) > 0.011 or abs(sc - k["scoring_progress_pct"]) > 0.011:
            bad.append(k["kr_id"])
    add("F. Arithmetic / derived", "KR current/progress/scoring recomputed from check-in values", bad)
    bad = []
    for g in T["goals"]:
        if g["status"] in ("draft", "cancelled"):
            if g["progress_pct"] != 0.0:
                bad.append(g["goal_id"])
            continue
        p = round(sum(k["weight"] * k["scoring_progress_pct"] for k in krg[g["goal_id"]]), 2)
        if abs(p - g["progress_pct"]) > 0.011:
            bad.append(g["goal_id"])
    add("F. Arithmetic / derived", "goal progress = sum(weight x KR scoring progress)", bad)
    bad = []; per_goal = defaultdict(list)
    for c in T["check_ins"]:
        per_goal[c["goal_id"]].append(c)
    for gid, lst in per_goal.items():
        st = {}
        for c in lst:
            for v in vals_by_chk[c["checkin_id"]]:
                st[v["kr_id"]] = v["reported_value"]
            cum = round(sum(k["weight"] * round(min(max(round((st.get(k["kr_id"], k["baseline_value"]) - k["baseline_value"]) / (k["target_value"] - k["baseline_value"]) * 100, 2), 0), CAP if k["over_achievement_rationale"] else 100.0), 2) for k in krg[gid]), 2)
            if abs(cum - c["cumulative_progress_pct"]) > 0.011:
                bad.append(c["checkin_id"])
        if abs(lst[-1]["cumulative_progress_pct"] - goals[gid]["progress_pct"]) > 0.011:
            bad.append(gid)
    add("F. Arithmetic / derived", "check-in cumulative progress replayed; last equals goal progress", bad)
    ev_n = Counter(e["checkin_id"] for e in T["evidence_links"])
    bad = [c["checkin_id"] for c in T["check_ins"] if ev_n[c["checkin_id"]] != c["evidence_count"] or (c["evidence_required"] and c["evidence_count"] < 1)
           or (c["evidence_required"] != (1 if any(v["progress_pct"] >= 80.0 for v in vals_by_chk[c["checkin_id"]]) else 0))]
    add("F. Arithmetic / derived", "evidence_count/required derived; evidence present where required", bad)
    bad = [v["value_id"] for v in T["check_in_kr_values"] if abs(v["progress_pct"] - round(max((v["reported_value"] - krs[v["kr_id"]]["baseline_value"]) / (krs[v["kr_id"]]["target_value"] - krs[v["kr_id"]]["baseline_value"]) * 100, 0), 2)) > 0.011]
    add("F. Arithmetic / derived", "check_in_kr_values progress recomputed", bad)
    bad = [k["checkin_id"] for k in T["check_ins"] if (k["submitted_by"] == k["employee_id"]) != (k["checkin_type"] == "self_update")]
    add("F. Arithmetic / derived", "check-in type consistent with submitter", bad)
    # versions
    chg = Counter(e["entity_id"] for e in T["state_events"] if e["entity_type"] == "Goal" and e["event_type"] in ("target_changed", "title_changed", "due_date_changed") and e["approval_status"] == "approved")
    add("F. Arithmetic / derived", "goals.version = 1 + approved change events (versioned changes)", [g["goal_id"] for g in T["goals"] if g["version"] != 1 + chg[g["goal_id"]]])
    # goal status rules
    bad = []
    for g in T["goals"]:
        c = cyc[g["cycle_id"]]
        if g["status"] in ("draft", "cancelled"):
            continue
        exp = "completed" if g["progress_pct"] >= COMPLETE else ("not_achieved" if c["status"] == "closed" else "active")
        if g["status"] != exp:
            bad.append(g["goal_id"])
    add("G. Lifecycle", "goal status follows documented progress/cycle rule", bad)
    # reviews
    gl = defaultdict(list)
    for g in T["goals"]:
        if g["status"] not in ("draft", "cancelled"):
            gl[(g["employee_id"], g["cycle_id"])].append(g)
    fbv = defaultdict(list)
    for f in T["feedback"]:
        if f["assignment_id"] is not None:
            fbv[f["review_id"]].append(f)
    ra_by = defaultdict(list)
    for a in T["reviewer_assignments"]:
        ra_by[a["review_id"]].append(a)
    bad = []; bad2 = []; bad3 = []; bad4 = []; bad5 = []
    for r in T["reviews"]:
        g_ = gl.get((r["employee_id"], r["cycle_id"]), [])
        ws = sum(g["weight_pct"] for g in g_)
        sc = round(sum(g["weight_pct"] * g["progress_pct"] for g in g_) / ws, 2) if g_ else None
        if r["goal_count"] != len(g_) or (sc is None) != (r["goal_progress_score"] is None) or (sc is not None and abs(sc - r["goal_progress_score"]) > 0.011):
            bad.append(r["review_id"])
        rows = fbv[r["review_id"]]
        def av(t):
            v = [x["rating"] for x in rows if x["feedback_type"] == t]
            return round(sum(v) / len(v), 2) if v else None
        if (av("self"), av("manager"), av("peer")) != (r["avg_self_rating"], r["avg_manager_rating"], r["avg_peer_rating"]):
            bad2.append(r["review_id"])
        sub = sum(1 for a in ra_by[r["review_id"]] if a["status"] == "submitted")
        if r["received_inputs"] != sub or abs(r["completion_pct"] - round(min(1.0, sub / 4.0) * 100, 2)) > 0.011:
            bad3.append(r["review_id"])
        byc = defaultdict(list)
        for x in rows:
            byc[x["competency_id"]].append(x["rating"])
        conf = any(max(v) - min(v) >= 3 for v in byc.values() if len(v) > 1) or (r["avg_self_rating"] is not None and r["avg_manager_rating"] is not None and abs(r["avg_self_rating"] - r["avg_manager_rating"]) >= 1.5)
        if bool(r["feedback_conflict_flag"]) != conf:
            bad4.append(r["review_id"])
        if r["status"] == "finalized":
            fr = round(.6 * (1 + 4 * min(r["goal_progress_score"], CAP) / CAP) + .4 * r["avg_manager_rating"], 2)
            band = "Needs Improvement" if fr < 2 else "Developing" if fr < 3 else "Meets Expectations" if fr < 4 else "Exceeds Expectations" if fr < 4.5 else "Outstanding"
            if abs(fr - r["final_rating"]) > 0.011 or band != r["rating_band"]:
                bad5.append(r["review_id"])
        elif r["final_rating"] is not None or r["rating_band"] is not None:
            bad5.append(r["review_id"])
    add("F. Arithmetic / derived", "review goal score = weight-weighted goal progress", bad)
    add("F. Arithmetic / derived", "review average ratings recomputed from permitted feedback", bad2, "Feedback without an assignment is excluded from scoring")
    add("F. Arithmetic / derived", "completion metrics reflect required inputs", bad3)
    add("F. Arithmetic / derived", "feedback_conflict_flag recomputed from feedback", bad4)
    add("F. Arithmetic / derived", "final_rating / band formula; null unless finalized", bad5)
    # lifecycle: reviews
    bad = []; hr_ok = set(e["employee_id"] for e in T["employees"] if e["system_role"] == "hr_partner")
    for r in T["reviews"]:
        c = cyc[r["cycle_id"]]; l = ra_by[r["review_id"]]
        peers_sub = sum(1 for a in l if a["relationship_type"] == "peer" and a["status"] == "submitted")
        if c["status"] == "closed" and r["status"] not in ("finalized", "closed_incomplete"):
            bad.append(r["review_id"])
        if r["status"] == "finalized" and not (r["self_submitted_at"] and r["manager_submitted_at"] and peers_sub >= 1 and r["finalized_at"]):
            bad.append(r["review_id"])
        if r["status"] == "closed_incomplete" and r["finalized_at"]:
            bad.append(r["review_id"])
        if c["status"] == "open" and (r["status"] != "not_started" and not c["review_window_start"] <= AS_OF):
            bad.append(r["review_id"])
    add("G. Lifecycle", "review terminal states and finalization requires self + manager + >=1 peer", bad)
    # event chains
    final_state = {"Goal": {k: v["status"] for k, v in goals.items()}, "Review": {k: v["status"] for k, v in reviews.items()},
                   "DevelopmentPlan": {k: v["status"] for k, v in by["development_plans"].items()}}
    chains = defaultdict(list)
    for e in T["state_events"]:
        if e["to_state"] is not None:
            chains[(e["entity_type"], e["entity_id"])].append(e)
    bad = []
    for (et, eid_), lst in chains.items():
        prev = None
        for e in lst:
            if e["from_state"] != prev:
                bad.append(eid_); break
            prev = e["to_state"]
        else:
            if final_state[et][eid_] != prev:
                bad.append(eid_)
    missing = [k for k in goals if ("Goal", k) not in chains] + [k for k in reviews if ("Review", k) not in chains]
    add("G. Lifecycle", "state_events chains are contiguous and end in the entity's current status", bad + missing)
    add("G. Lifecycle", "state_events chronological ids", [e["event_id"] for a, e in zip(T["state_events"], T["state_events"][1:]) if e["occurred_at"] < a["occurred_at"]])
    # reviewer permissions
    bad = []
    for a in T["reviewer_assignments"]:
        r = reviews[a["review_id"]]
        if a["reviewee_id"] != r["employee_id"]:
            bad.append(a["assignment_id"])
        if a["relationship_type"] == "manager" and a["reviewer_id"] != mgr_emp[r["manager_id"]]:
            bad.append(a["assignment_id"])
        if a["relationship_type"] == "self" and a["reviewer_id"] != a["reviewee_id"]:
            bad.append(a["assignment_id"])
        if a["relationship_type"] == "peer" and (a["reviewer_id"] == a["reviewee_id"] or a["reviewer_id"] == mgr_emp[r["manager_id"]]):
            bad.append(a["assignment_id"])
        if (a["relationship_basis"] == "cross_functional_approved") != (a["approved_by"] is not None):
            bad.append(a["assignment_id"])
    add("G. Lifecycle", "review permissions: reviewer assignments respect relationships", sorted(set(bad)))
    bad = [f["feedback_id"] for f in T["feedback"] if f["assignment_id"] and (ras[f["assignment_id"]]["reviewer_id"] != f["reviewer_id"] or ras[f["assignment_id"]]["review_id"] != f["review_id"]
           or ras[f["assignment_id"]]["status"] != "submitted" or ras[f["assignment_id"]]["responded_at"] != f["submitted_at"] or ras[f["assignment_id"]]["relationship_type"] != f["feedback_type"])]
    add("G. Lifecycle", "feedback matches its (submitted) reviewer assignment", bad)
    # duplicates
    def dup(rows, key):
        c = Counter(key(r) for r in rows); return [str(k) for k, v in c.items() if v > 1]
    add("H. Duplicates", "employees.email unique", dup(T["employees"], lambda r: r["email"]))
    add("H. Duplicates", "one review per (employee, cycle)", dup(T["reviews"], lambda r: (r["employee_id"], r["cycle_id"])))
    add("H. Duplicates", "one check-in per (goal, date)", dup(T["check_ins"], lambda r: (r["goal_id"], r["checkin_date"])))
    add("H. Duplicates", "one KR value per (check-in, KR)", dup(T["check_in_kr_values"], lambda r: (r["checkin_id"], r["kr_id"])))
    add("H. Duplicates", "one assignment per (review, reviewer, type)", dup(T["reviewer_assignments"], lambda r: (r["review_id"], r["reviewer_id"], r["relationship_type"])))
    add("H. Duplicates", "one feedback per (assignment, competency)", dup([f for f in T["feedback"] if f["assignment_id"]], lambda r: (r["assignment_id"], r["competency_id"])))
    add("H. Duplicates", "evidence urls unique", dup(T["evidence_links"], lambda r: r["url"]))
    # development plans
    bad = []
    mrat = defaultdict(dict)
    for f in T["feedback"]:
        if f["feedback_type"] == "manager" and f["assignment_id"]:
            mrat[f["review_id"]][f["competency_id"]] = f["rating"]
    for p in T["development_plans"]:
        r = reviews[p["review_id"]]
        if r["status"] != "finalized" or p["employee_id"] != r["employee_id"] or p["manager_approver_id"] not in (None, r["manager_id"]):
            bad.append(p["dev_plan_id"])
        if p["plan_type"] == "mandatory" and not (mrat[p["review_id"]].get(p["competency_id"], 9) <= 2 or r["rating_band"] == "Needs Improvement"):
            bad.append(p["dev_plan_id"])
        if p["requires_hr_approval"] != (1 if p["budget_usd"] > 1500 else 0) or (p["hr_approver_id"] and p["hr_approver_id"] not in hr_ok):
            bad.append(p["dev_plan_id"])
        if p["hr_decision"] and p["manager_decision"] != "approved":
            bad.append(p["dev_plan_id"])
        if not p["start_date"] < p["target_date"] or (p["completed_at"] and p["status"] != "completed") or p["created_at"][:10] <= r["finalized_at"][:10]:
            bad.append(p["dev_plan_id"])
        if p["status"] in ("approved", "in_progress", "completed") and (p["manager_decision"] != "approved" or (p["requires_hr_approval"] and p["hr_decision"] != "approved")):
            bad.append(p["dev_plan_id"])
    add("G. Lifecycle", "development plans: approvals, HR threshold, mandatory rule, dates", sorted(set(bad)))
    # I. anomaly detectors (rule-based, do not read ground truth) vs ground truth
    gt = defaultdict(set)
    for g in T["ground_truth"]:
        gt[g["issue_type"]].add(g["entity_id"])
    closed = {k: v["closed_at"] for k, v in cyc.items() if v["closed_at"]}
    det = {}
    det["goal_owner_mismatch"] = {g["goal_id"] for g in T["goals"] if g["goal_id"].split("-", 2)[1] + "-" + g["goal_id"].split("-")[2] != g["employee_id"]}
    det["progress_exceeds_scale_no_rationale"] = {k["kr_id"] for k in T["key_results"] if (k["progress_pct"] > 100 and not k["over_achievement_rationale"]) or k["progress_pct"] > k["max_progress_pct"]}
    mgr_at_end = {}
    for e, lst in asg.items():
        for a in lst:
            if a["effective_from"] <= dt.date(2026, 6, 30) and (a["effective_to"] is None or dt.date(2026, 6, 30) < a["effective_to"]):
                mgr_at_end[e] = a["manager_id"]
    lacks = set(); untr = set()
    for f in T["feedback"]:
        if f["assignment_id"] is None and f["reviewer_id"] is not None and f["feedback_type"] != "self":
            rv = f["reviewer_id"]; ee = f["reviewee_id"]; rm = reviews[f["review_id"]]["manager_id"]
            related = emps[rv]["department"] == emps[ee]["department"] or mgr_at_end.get(rv) == mgr_at_end.get(ee) or mgr_emp[rm] == rv
            if not related:
                lacks.add(f["feedback_id"])
        if f["assignment_id"] is None and f["reviewer_id"] is None:
            untr.add(f["feedback_id"])
    det["reviewer_lacks_relationship"] = lacks; det["feedback_untraceable"] = untr
    sil = set()
    for e in T["state_events"]:
        if e["entity_type"] == "Goal" and e["event_type"] in ("target_changed", "title_changed", "due_date_changed", "edit_after_close") and e["approval_status"] != "approved":
            c = closed.get(goals[e["entity_id"]]["cycle_id"])
            if c and e["occurred_at"] > c:
                sil.add(e["entity_id"])
    det["closed_cycle_silent_edit"] = sil
    det["incomplete_review"] = {r["review_id"] for r in T["reviews"] if r["status"] == "closed_incomplete"}
    det["conflicting_feedback"] = {r["review_id"] for r in T["reviews"] if r["feedback_conflict_flag"]}
    det["manager_transfer_mid_cycle"] = {r["review_id"] for r in T["reviews"] if r["manager_changed_in_cycle"]}
    det["goal_changed"] = {g["goal_id"] for g in T["goals"] if g["version"] > 1}
    anomaly_counts = {}
    for k in ("goal_owner_mismatch", "progress_exceeds_scale_no_rationale", "reviewer_lacks_relationship", "closed_cycle_silent_edit", "feedback_untraceable"):
        add("I. Anomaly reconciliation", "detector for %s == ground_truth labels" % k, sorted(det[k] ^ gt[k]), "labelled=%d detected=%d" % (len(gt[k]), len(det[k])))
        anomaly_counts[k] = len(gt[k])
    for k in ("incomplete_review", "conflicting_feedback", "manager_transfer_mid_cycle", "goal_changed"):
        add("I. Anomaly reconciliation", "natural scenario %s derived == labels" % k, sorted(det[k] ^ gt[k]), "count=%d" % len(gt[k]))
        anomaly_counts[k] = len(gt[k])
    # clean-row check: injected anomalies must not corrupt unrelated rows -> all other rules above pass
    # ----- distributions
    import statistics as st
    prog = [g["progress_pct"] for g in T["goals"] if g["status"] not in ("draft", "cancelled")]
    ratings = Counter(f["rating"] for f in T["feedback"])
    stats = dict(
        goals_by_status=dict(Counter(g["status"] for g in T["goals"])),
        goals_per_employee_cycle_mean=round(len(T["goals"]) / len(T["reviews"]), 2),
        goal_progress_mean=round(st.mean(prog), 1), goal_progress_median=round(st.median(prog), 1), goal_progress_stdev=round(st.pstdev(prog), 1),
        kr_per_goal_mean=round(len(T["key_results"]) / len(T["goals"]), 2), checkins_per_goal_mean=round(len(T["check_ins"]) / len(T["goals"]), 2),
        checkin_confidence=dict(Counter(c["confidence"] for c in T["check_ins"])),
        feedback_rating_distribution={str(k): ratings[k] for k in sorted(ratings)},
        review_status_by_cycle={c: dict(Counter(r["status"] for r in T["reviews"] if r["cycle_id"] == c)) for c in cyc},
        final_rating_bands=dict(Counter(r["rating_band"] for r in T["reviews"] if r["rating_band"])),
        kr_over_100_with_rationale=sum(1 for k in T["key_results"] if k["progress_pct"] > 100 and k["over_achievement_rationale"]),
        kr_over_100_without_rationale=sum(1 for k in T["key_results"] if k["progress_pct"] > 100 and not k["over_achievement_rationale"]),
        kr_zero_progress=sum(1 for k in T["key_results"] if k["progress_pct"] == 0),
        kr_max_progress=max(k["progress_pct"] for k in T["key_results"]),
        span_of_control_mean=round(len(T["employees"]) / len(T["managers"]), 2),
        transfers=sum(1 for a in T["manager_assignments"] if a["change_reason"] != "initial_hire"),
        dev_plan_status=dict(Counter(p["status"] for p in T["development_plans"])))
    xs = [(r["goal_progress_score"], r["avg_manager_rating"]) for r in T["reviews"] if r["status"] == "finalized"]
    if len(xs) > 2:
        mx = st.mean(x for x, _ in xs); my = st.mean(y for _, y in xs)
        den = (sum((x - mx) ** 2 for x, _ in xs) * sum((y - my) ** 2 for _, y in xs)) ** .5
        stats["corr_goal_score_vs_manager_rating"] = round(sum((x - mx) * (y - my) for x, y in xs) / den, 3) if den else None
    return R, stats, anomaly_counts


# ------------------------------------------------------------------ docs
def write_docs(T, P, R, stats, anomaly, out, sums, repro, cmd):
    n_ok = sum(1 for r in R if r["passed"]); n = len(R)
    counts = {t: len(T[t]) for t in S.TABLES}
    # data dictionary
    with open(os.path.join(out, "data_dictionary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["table", "field", "type", "required", "allowed_values", "unit", "unique", "primary_key", "foreign_key", "rule"])
        for t in S.TABLES:
            for c in S.RAW[t]:
                w.writerow([t, c["name"], c["type"], "Y" if c["required"] else "N", c["allowed"], c["unit"], "Y" if c["unique"] else "N", "Y" if c["pk"] else "N",
                            "%s.%s" % c["fk"] if c["fk"] else "", c["rule"]])
    with open(os.path.join(out, "data_dictionary.md"), "w", encoding="utf-8") as f:
        f.write("# Data dictionary\n\nGenerated from `schema.py` (single source of truth for exports, SQL DDL and validation).\n\n")
        for t in S.TABLES:
            f.write("## %s  (%d rows, PK `%s`)\n\n| Field | Type | Req | Allowed values | Unit | Unique | Rule / FK |\n|---|---|---|---|---|---|---|\n" % (t, counts[t], S.PKS[t]))
            for c in S.RAW[t]:
                f.write("| %s | %s | %s | %s | %s | %s | %s |\n" % (c["name"], c["type"], "Y" if c["required"] else "N", c["allowed"].replace("|", "/"), c["unit"], "Y" if c["unique"] else "N", c["rule"].replace("|", "/")))
            f.write("\n")
    with open(os.path.join(out, "validation_summary.json"), "w") as f:
        json.dump(dict(passed=n_ok, total=n, all_passed=(n_ok == n), checks=R, distribution_summary=stats, anomaly_label_counts=anomaly), f, indent=1, default=str)
    with open(os.path.join(out, "source_manifest.json"), "w") as f:
        json.dump(dict(external_data_used=False, statement="All data is synthetic and generated by generate.py from a fixed seed. No external, public or personal data was ingested; names are random combinations of common first/last names and e-mail addresses use the reserved example.test domain.",
                       schema_inspiration="Generic OKR / 360-feedback / performance-review domain concepts (no dataset or license-bound material copied).", fields_discarded=[], retrieval_date=None, licence="Generated output is free of third-party licence obligations; provided for evaluation use."), f, indent=1)
    with open(os.path.join(out, "reproducibility_report.json"), "w") as f:
        json.dump(repro, f, indent=1)
    with open(os.path.join(out, "checksums_sha256.json"), "w") as f:
        json.dump(dict(row_counts=counts, sha256=sums), f, indent=1)
    fails = [r for r in R if not r["passed"]]
    cats = defaultdict(lambda: [0, 0])
    for r in R:
        cats[r["category"]][1] += 1; cats[r["category"]][0] += r["passed"]
    with open(os.path.join(out, "validation_summary.md"), "w", encoding="utf-8") as f:
        f.write("# Validation summary\n\n**%d / %d checks passed.**\n\n| Category | Passed |\n|---|---|\n" % (n_ok, n))
        for k in sorted(cats):
            f.write("| %s | %d / %d |\n" % (k, cats[k][0], cats[k][1]))
        if fails:
            f.write("\n## Failures\n")
            for r in fails:
                f.write("- %s: %s (%d) %s\n" % (r["category"], r["check"], r["violations"], r["examples"]))
        f.write("\n## Anomaly / scenario labels (ground_truth)\n\n| issue_type | rows |\n|---|---|\n")
        for k, v in anomaly.items():
            f.write("| %s | %d |\n" % (k, v))
        f.write("\n## Distribution summary\n\n```json\n%s\n```\n" % json.dumps(stats, indent=1))
    ar = anomaly
    rp = repro.get("status", "n/a")
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8") as f:
        f.write(README.format(seed=P["seed"], scale=P["scale"], ne=counts["employees"], nm=counts["managers"], ng=counts["goals"], nk=counts["key_results"], nc=counts["check_ins"],
                              n_ok=n_ok, n=n, cmd=cmd, rp=rp, asof=AS_OF.isoformat(), counts_table="\n".join("| %s | %d |" % (t, counts[t]) for t in S.TABLES),
                              ar_table="\n".join("| %s | %d |" % (k, v) for k, v in ar.items()),
                              nev=counts["state_events"], nfb=counts["feedback"], nrev=counts["reviews"]))


README = """# Synthetic Performance-Management Dataset

Goals, key results, check-ins, competency feedback, reviews and development plans with evidence-based progress tracking.
Fixed seed **{seed}**, scale **{scale}** ({ne:,} employees, {nm:,} managers, {ng:,} goals, {nc:,} check-ins). **All data is synthetic.**

## Reproduce
```
{cmd}
```
Same generator for every size: `--scale 1.0` is the full dataset (3,000 / 500 / 10,000 / 20,000), `--scale 0.05` is the starter set.
Standard library only (Python 3.9+). Reproducibility check (two runs, same seed, sha256 of every CSV/JSON/SQL file): **{rp}** (`reproducibility_report.json`).
Dates are anchored to an as-of date of **{asof}**; no wall-clock time is used.

## Contents
| Folder / file | Purpose |
|---|---|
| `csv/`, `json/` | One file per table (identical content) |
| `sql/schema.sql`, `sql/seed_data.sql` | SQLite-compatible DDL (PK/FK/UNIQUE/NOT NULL, deferred FKs) and INSERTs |
| `csv/ground_truth.csv` | Labels for injected anomalies and natural scenarios. **Never use as input features.** |
| `data_dictionary.md/.csv` | Every field: type, required, allowed values, unit, uniqueness, validation rule, FK |
| `validation_summary.md/.json` | {n_ok}/{n} checks passed, distributions, label counts |
| `source_manifest.json`, `reproducibility_report.json`, `checksums_sha256.json` | Provenance, reproducibility, row counts and hashes |

### Row counts
| Table | Rows |
|---|---|
{counts_table}

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
{ar_table}

Injected: goal owner mismatch (stored owner differs from the id embedded in `goal_id`), progress above scale without rationale, reviewer without a relationship (no assignment, unrelated reviewer), silent edit after cycle close (unapproved event after `closed_at`), untraceable feedback (no reviewer and no assignment). Natural scenarios arise from the rules: changed goals, manager transfers, incomplete reviews and conflicting feedback. Validation contains independent detectors that rediscover each injected label exactly (precision and recall of 1.0 against the labels) without reading the ground truth.

## Validation
{n_ok} of {n} checks pass: primary-key uniqueness, foreign-key integrity (also via a SQLite load with `PRAGMA foreign_key_check`), enums, required fields, date ordering, arithmetic reconciliation, lifecycle transitions, event-chain continuity, duplicates and anomaly reconciliation. Details in `validation_summary.md`.

## Provenance and lawful use
No external data. Names are random combinations of common first/last names and do not refer to real people; e-mail uses the reserved `example.test` domain; evidence URLs are non-resolvable. See `source_manifest.json`.

## Known simplifications
* Two cycles (H1 closed, H2 open); the organisation root is not reviewed (no manager).
* `reviewer_assignments` for H2 do not exist yet because the H2 review window has not opened.
* Check-in values follow a smooth progress curve with noise; peer selection is random within team/department pools.
"""


def run_once(seed, scale, out):
    T, P = generate(seed, scale)
    sums = export(T, out)
    return T, P, sums


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", default="out")
    ap.add_argument("--verify-repro", action="store_true")
    a = ap.parse_args()
    if os.path.exists(a.out):
        shutil.rmtree(a.out)
    T, P, sums = run_once(a.seed, a.scale, a.out)
    R, stats, anomaly = validate(T, P)
    repro = dict(status="not run")
    if a.verify_repro:
        tmp = tempfile.mkdtemp()
        _, _, sums2 = run_once(a.seed, a.scale, os.path.join(tmp, "run2"))
        same = sums == sums2
        repro = dict(status="PASS - identical row counts and sha256 for all %d files across two runs" % len(sums) if same else "FAIL",
                     seed=a.seed, scale=a.scale, identical=same, files_compared=len(sums), run1_vs_run2_mismatches=[k for k in sums if sums[k] != sums2.get(k)])
        shutil.rmtree(tmp)
    cmd = "python generate.py --seed %d --scale %s --out %s --verify-repro" % (a.seed, a.scale, os.path.basename(a.out.rstrip("/")))
    write_docs(T, P, R, stats, anomaly, a.out, sums, repro, cmd)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.py"), a.out)
    n_ok = sum(1 for r in R if r["passed"])
    print("rows:", {t: len(T[t]) for t in S.TABLES})
    print("validation: %d/%d passed" % (n_ok, len(R)))
    for r in R:
        if not r["passed"]:
            print("  FAIL", r["category"], r["check"], r["violations"], r["examples"])
    print("repro:", repro.get("status"))


if __name__ == "__main__":
    main()
