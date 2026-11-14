"""Core generation logic. Deterministic for a given (seed, scale)."""
import datetime as dt
import math
import random
from collections import defaultdict

from schema import DEPTS, LOCS

AS_OF = dt.date(2026, 10, 22)
CAP = 120.0
COMPLETE = 70.0   # goal counts as completed at >= 70% weighted progress
D = dt.date

FIRST = ["Aarav", "Vivaan", "Aditya", "Arjun", "Sai", "Reyansh", "Krishna", "Ishaan", "Rohan", "Karan", "Ananya", "Diya", "Isha",
         "Kavya", "Meera", "Neha", "Priya", "Riya", "Sneha", "Tanvi", "Aisha", "Fatima", "Zoya", "Imran", "Farhan", "Sameer",
         "Nikhil", "Pooja", "Divya", "Manish", "Suresh", "Lakshmi", "Deepak", "Anjali", "Varun", "Harsh", "Naina", "Tarun", "Swati", "Rahul"]
LAST = ["Sharma", "Verma", "Reddy", "Nair", "Iyer", "Patel", "Gupta", "Singh", "Khan", "Das", "Mishra", "Rao", "Menon", "Joshi", "Kulkarni",
        "Desai", "Bose", "Chatterjee", "Pillai", "Naidu", "Banerjee", "Mehta", "Kapoor", "Malhotra", "Saxena", "Yadav", "Shetty", "Ghosh", "Jain", "Thakur"]
NOUN = {"Engineering": "Engineer", "Product": "Product Analyst", "Sales": "Sales Executive", "Marketing": "Marketing Specialist",
        "Finance": "Finance Analyst", "HR": "HR Generalist", "Operations": "Operations Analyst", "Customer Success": "Success Associate"}
MGR_TITLE = {4: "{d} Team Lead", 5: "{d} Manager", 6: "Director, {d}", 7: "VP, {d}"}
IC_TITLE = {1: "Associate {n}", 2: "{n}", 3: "Senior {n}", 4: "Staff {n}"}
GOALS = {
    "Engineering": ["Improve service reliability", "Reduce release cycle time", "Raise automated test coverage", "Retire legacy components"],
    "Product": ["Ship the planned roadmap features", "Increase feature adoption", "Improve customer research cadence", "Raise product quality score"],
    "Sales": ["Grow qualified pipeline", "Increase closed revenue", "Improve win rate in target segment", "Expand key accounts"],
    "Marketing": ["Grow qualified leads", "Improve campaign conversion", "Increase brand engagement", "Strengthen content programme"],
    "Finance": ["Shorten month-end close", "Improve forecast accuracy", "Reduce outstanding receivables", "Automate recurring reporting"],
    "HR": ["Reduce time to hire", "Improve onboarding satisfaction", "Raise training completion", "Improve retention in critical roles"],
    "Operations": ["Cut order fulfilment time", "Reduce process defects", "Improve vendor on-time delivery", "Lower operating cost per unit"],
    "Customer Success": ["Raise customer satisfaction", "Reduce ticket resolution time", "Increase renewal rate", "Improve onboarding completion"],
}
NOUNS = {d: [g.lower() for g in v] for d, v in GOALS.items()}
KR_TPL = {"percentage": "Raise rate for: {n}", "count": "Deliver items for: {n}", "currency_usd": "Achieve value for: {n}",
          "score": "Lift quality score for: {n}", "duration_days": "Reduce cycle time for: {n}", "defect_rate_pct": "Reduce error rate for: {n}"}
UNITS = {"percentage": "%", "count": "count", "currency_usd": "USD", "score": "score (1-5)", "duration_days": "days", "defect_rate_pct": "%"}
RATIONALE = ["Delivered ahead of plan after scope was extended by the sponsor.", "Unplanned customer demand raised volume beyond target.",
             "Reused existing components, enabling faster completion.", "Cross-team support allowed the stretch outcome.",
             "Market conditions improved results beyond forecast."]
CANCEL = ["Priority replaced by a higher-impact initiative", "Dependency removed from the roadmap", "Team re-organisation changed scope"]
CHK_COMMENT = {"on_track": ["Progress is on plan.", "Milestones met this period.", "Good momentum, no blockers."],
               "at_risk": ["Some slippage; mitigation agreed.", "Dependency delay is a risk.", "Behind plan, recovery under way."],
               "off_track": ["Significantly behind; support requested.", "Blocked on external input.", "Scope needs re-planning."]}
PHRASE = {1: ["Significant gaps observed", "Rarely demonstrates this"], 2: ["Below expectations in places", "Inconsistent in this area"],
          3: ["Meets expectations", "Solid and dependable"], 4: ["Often exceeds expectations", "Strong, visible strength"],
          5: ["Role-model level", "Exceptional and consistently outstanding"]}
ACTIVITY = ["course", "mentoring", "stretch_assignment", "certification", "coaching"]
COMPS = [("Delivery Focus", "Execution"), ("Quality of Work", "Execution"), ("Problem Solving", "Execution"),
         ("Teamwork", "Collaboration"), ("Communication", "Collaboration"), ("Customer Orientation", "Collaboration"),
         ("Ownership", "Leadership"), ("Mentoring", "Leadership"), ("Decision Making", "Leadership"),
         ("Technical Depth", "Craft"), ("Learning Agility", "Craft"), ("Innovation", "Craft")]
EVID_TYPES = ["document", "dashboard", "ticket", "pull_request", "report", "presentation"]


def ts(d, rng):
    return "%sT%02d:%02d:%02d" % (d.isoformat(), rng.randint(9, 18), rng.randint(0, 59), rng.randint(0, 59))


def rnd_metric(metric, v):
    if metric == "count":
        return int(round(v))
    if metric == "currency_usd":
        return int(round(v / 100.0) * 100)
    if metric in ("percentage", "duration_days"):
        return round(v, 1)
    return round(v, 2)


def mk_kr(rng, metric):
    if metric == "percentage":
        b = round(rng.uniform(0, 40), 1); t = round(b + rng.uniform(15, 55), 1); direction = "increase"
    elif metric == "count":
        b = rng.randint(0, 20); t = b + rng.randint(8, 200); direction = "increase"
    elif metric == "currency_usd":
        b = 0; t = int(round(rng.uniform(20000, 600000), -3)); direction = "increase"
    elif metric == "score":
        b = round(rng.uniform(2.8, 3.8), 1); t = round(min(5.0, b + rng.uniform(0.5, 1.0)), 1); direction = "increase"
    elif metric == "duration_days":
        b = float(rng.randint(20, 60)); t = round(b * rng.uniform(0.5, 0.8), 1); direction = "decrease"
    else:
        b = round(rng.uniform(5, 12), 2); t = round(b * rng.uniform(0.4, 0.7), 2); direction = "decrease"
    return b, t, direction


def safe_val(kr, frac):
    v = rnd_metric(kr["metric_type"], kr["baseline_value"] + frac * (kr["target_value"] - kr["baseline_value"]))
    while frac > 0 and (v - kr["baseline_value"]) / (kr["target_value"] - kr["baseline_value"]) * 100.0 > 119.5:
        frac -= 0.02
        v = rnd_metric(kr["metric_type"], kr["baseline_value"] + frac * (kr["target_value"] - kr["baseline_value"]))
    return v


def kr_progress(kr, v):
    raw = (v - kr["baseline_value"]) / (kr["target_value"] - kr["baseline_value"]) * 100.0
    return round(max(raw, 0.0), 2)


def kr_scoring(raw, has_rationale):
    return round(min(raw, CAP if has_rationale else 100.0), 2)


def split_weights(rng, k):
    pats = {1: [[100]], 2: [[60, 40], [50, 50], [70, 30]], 3: [[50, 30, 20], [40, 40, 20], [40, 30, 30]],
            4: [[40, 30, 20, 10], [25, 25, 25, 25], [30, 30, 20, 20]]}
    w = list(rng.choice(pats[k])); rng.shuffle(w)
    return [float(x) for x in w]


def generate(seed, scale, anomaly_scale=None):
    rng = random.Random(seed)
    n_emp = max(60, round(3000 * scale)); n_mgr = max(8, round(500 * scale))
    n_goal = round(10000 * scale); n_chk = round(20000 * scale)
    asc = scale if anomaly_scale is None else anomaly_scale
    n_an = {k: max(2, round(v * asc)) for k, v in dict(owner=30, overshoot=50, lacks=50, silent=40, untrace=40).items()}
    P = dict(seed=seed, scale=scale, employees=n_emp, managers=n_mgr, goals=n_goal, check_ins=n_chk, anomalies=n_an)

    # ---------------- cycles / competencies
    cycles = [
        dict(cycle_id="CYCLE-2026-H1", cycle_name="2026 H1 Performance Cycle", start_date=D(2026, 1, 1), end_date=D(2026, 6, 30),
             goal_setting_deadline=D(2026, 1, 31), review_window_start=D(2026, 7, 1), review_window_end=D(2026, 7, 31),
             closed_at="2026-08-15T18:00:00", status="closed", max_progress_pct=CAP),
        dict(cycle_id="CYCLE-2026-H2", cycle_name="2026 H2 Performance Cycle", start_date=D(2026, 7, 1), end_date=D(2026, 12, 31),
             goal_setting_deadline=D(2026, 7, 31), review_window_start=D(2026, 12, 1), review_window_end=D(2026, 12, 31),
             closed_at=None, status="open", max_progress_pct=CAP),
    ]
    cyc = {c["cycle_id"]: c for c in cycles}
    competencies = [dict(competency_id="COMP-%02d" % (i + 1), competency_name=n, category=c,
                         description="Observable behaviours for %s." % n.lower(), rating_scale_min=1, rating_scale_max=5)
                    for i, (n, c) in enumerate(COMPS)]
    comp_name = {c["competency_id"]: c["competency_name"] for c in competencies}
    comp_ids = [c["competency_id"] for c in competencies]

    # ---------------- org hierarchy
    ids = list(range(1, n_emp + 1))
    mgr_emp = sorted(rng.sample(ids, n_mgr)); mgr_set = set(mgr_emp)
    parent = [None] * n_mgr; level = [1] * n_mgr; kids = [0] * n_mgr; cands = [0]
    for i in range(1, n_mgr):
        if not cands:
            cands = [k for k in range(i) if level[k] <= 5]
        j = rng.choice(cands); parent[i] = j; level[i] = level[j] + 1; kids[j] += 1
        if kids[j] >= 8 and j in cands:
            cands.remove(j)
        if level[i] <= 5:
            cands.append(i)
    mdept = [rng.choice(DEPTS) for _ in range(n_mgr)]
    non_mgr = [e for e in ids if e not in mgr_set]
    wts = [rng.lognormvariate(0, 0.5) for _ in range(n_mgr)]
    emp_mi = {}
    pool = non_mgr[:]; rng.shuffle(pool)
    for i in range(n_mgr):
        if kids[i] == 0 and pool:
            emp_mi[pool.pop()] = i
    for e in pool:
        emp_mi[e] = rng.choices(range(n_mgr), weights=wts)[0]
    for i, e in enumerate(mgr_emp):
        if parent[i] is not None:
            emp_mi[e] = parent[i]
    eid = lambda n: "EMP-%06d" % n
    mid = lambda i: "MGR-%06d" % (i + 1)
    mgr_of_emp = {e: i for i, e in enumerate(mgr_emp)}

    def hire(latest):
        lo = D(2012, 1, 2); span = (latest - lo).days
        return lo + dt.timedelta(days=int(span * (rng.random() ** 0.7)))

    perf = {}; emps = {}
    for n in ids:
        perf[n] = rng.betavariate(5, 2)
        is_m = n in mgr_set
        h = hire(D(2025, 6, 30) if is_m else D(2026, 10, 1))
        if is_m:
            lv = {1: 7, 2: 6, 3: 5}.get(level[mgr_of_emp[n]], 4); dept = mdept[mgr_of_emp[n]]
            title = MGR_TITLE[lv].format(d=dept)
        else:
            dept = mdept[emp_mi[n]]; lv = rng.choices([1, 2, 3, 4], [.3, .3, .25, .15])[0]
            title = IC_TITLE[lv].format(n=NOUN[dept])
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        term = None; status = "active"
        if not is_m and h < D(2026, 4, 1) and rng.random() < 0.03:
            term = D(2026, 7, 20) + dt.timedelta(days=rng.randint(0, 92)); status = "terminated"
        elif rng.random() < 0.02:
            status = "on_leave"
        emps[n] = dict(employee_id=eid(n), full_name="%s %s" % (fn, ln), email="%s.%s.%d@example.test" % (fn.lower(), ln.lower(), n),
                       department=dept, job_level="L%d" % lv, job_title=title, location=rng.choice(LOCS), hire_date=h,
                       termination_date=term, employment_status=status, system_role="manager" if is_m else "employee", manager_id=None)
    live = [n for n in non_mgr if emps[n]["employment_status"] != "terminated"]
    for role, cnt in (("hr_partner", max(2, round(.015 * n_emp))), ("it_ops", max(1, round(.01 * n_emp))), ("sysadmin", max(1, round(.002 * n_emp)))):
        for n in rng.sample([x for x in live if emps[x]["system_role"] == "employee"], cnt):
            emps[n]["system_role"] = role
    hr_partners = [eid(n) for n in ids if emps[n]["system_role"] == "hr_partner"]
    ops_actors = [eid(n) for n in ids if emps[n]["system_role"] in ("it_ops", "sysadmin")]

    # manager rows + assignments (with transfers)
    managers = []
    for i, e in enumerate(mgr_emp):
        eff = min(emps[e]["hire_date"] + dt.timedelta(days=rng.randint(0, 1000)), D(2025, 6, 30))
        managers.append(dict(manager_id=mid(i), employee_id=eid(e), parent_manager_id=mid(parent[i]) if parent[i] is not None else None,
                             department=mdept[i], org_level=level[i], effective_from=eff, status="active"))
    asg = defaultdict(list); asg_rows = []; k = 0
    def add_asg(e, mi, fr, to, why):
        nonlocal k
        k += 1
        asg_rows.append(dict(assignment_id="MA-%06d" % k, employee_id=eid(e), manager_id=mid(mi), effective_from=fr, effective_to=to, change_reason=why))
        asg[e].append((fr, to, mi))
    for e in ids:
        if e not in emp_mi:
            continue
        h = emps[e]["hire_date"]; cur = emp_mi[e]; tdate = None
        if e not in mgr_set and h < D(2026, 1, 1) and rng.random() < 0.08:
            td = D(2026, 2, 15) + dt.timedelta(days=rng.randint(0, 237))
            if emps[e]["termination_date"] is None or td < emps[e]["termination_date"]:
                tdate = td
        add_asg(e, cur, h, tdate, "initial_hire")
        if tdate:
            new = rng.choice([x for x in range(n_mgr) if x != cur])
            add_asg(e, new, tdate, None, rng.choices(["transfer", "reorg"], [.7, .3])[0]); cur = new
        emps[e]["manager_id"] = mid(cur)

    def mgr_idx_at(e, d):
        lst = asg.get(e)
        if not lst:
            return None
        for fr, to, mi in lst:
            if fr <= d and (to is None or d < to):
                return mi
        return lst[0][2] if d < lst[0][0] else lst[-1][2]

    mgr_empid = lambda mi: eid(mgr_emp[mi])

    # ---------------- participation and goals
    def participants(c):
        out = []
        root = mgr_emp[0]
        for n in ids:
            if n == root or n not in emp_mi:
                continue
            e = emps[n]
            if c == "CYCLE-2026-H1" and e["hire_date"] <= D(2026, 5, 31):
                out.append(n)
            elif c == "CYCLE-2026-H2" and e["hire_date"] <= D(2026, 9, 15) and e["employment_status"] != "terminated":
                out.append(n)
        return out
    part = [(c, n) for c in ("CYCLE-2026-H1", "CYCLE-2026-H2") for n in participants(c)]
    cnt = [rng.choices([1, 2, 3, 4], [.45, .38, .14, .03])[0] for _ in part]
    tot = sum(cnt)
    assert n_goal >= len(part), "scale too small"
    while tot > n_goal:
        i = rng.randrange(len(cnt))
        if cnt[i] > 1:
            cnt[i] -= 1; tot -= 1
    while tot < n_goal:
        i = rng.randrange(len(cnt))
        if cnt[i] < 4:
            cnt[i] += 1; tot += 1

    goals = []; gaux = {}; krs = []; seq = defaultdict(int); events = []; evc = [0]
    def ev(**kw):
        evc[0] += 1; kw["_o"] = evc[0]; events.append(kw)
    krs_by_goal = defaultdict(list)
    for (c, n), g_cnt in zip(part, cnt):
        cy = cyc[c]; e = emps[n]; ws = split_weights(rng, g_cnt)
        ok_goals = 0
        for gi in range(g_cnt):
            seq[n] += 1
            gid = "GOAL-%s-%03d" % (eid(n), seq[n])
            state = "ok"
            if gi > 0:
                u = rng.random()
                if c == "CYCLE-2026-H2" and u < 0.03:
                    state = "draft"
                elif u < 0.04:
                    state = "cancelled"
            if state == "draft":
                created = D(2026, 10, 1) + dt.timedelta(days=rng.randint(0, 19)); start = created; approved = None
            else:
                start = max(cy["start_date"] + dt.timedelta(days=rng.randint(0, 21)), e["hire_date"] + dt.timedelta(days=7))
                created = max(e["hire_date"], start - dt.timedelta(days=rng.randint(0, 3)))
                approved = created + dt.timedelta(days=rng.randint(1, 7))
                start = max(start, approved)
            due = cy["end_date"]
            if rng.random() < 0.4:
                due = max(start + dt.timedelta(days=45), cy["end_date"] - dt.timedelta(days=rng.randint(7, 75)))
                due = min(due, cy["end_date"])
            title = rng.choice(GOALS[e["department"]])
            kk = rng.choices([1, 2, 3], [.3, .5, .2])[0]
            kw = {1: [1.0], 2: rng.choice([[.6, .4], [.5, .5]]), 3: rng.choice([[.5, .3, .2], [.4, .3, .3]])}[kk]
            mi_app = mgr_idx_at(n, approved) if approved else None
            g = dict(goal_id=gid, employee_id=eid(n), cycle_id=c, title=title,
                     description="%s. Measured through %d key result(s)." % (title, kk),
                     category=rng.choices(["performance", "strategic", "development"], [.6, .25, .15])[0], weight_pct=ws[gi],
                     start_date=start, due_date=due, status="active" if state != "draft" else "draft", version=1,
                     created_at=ts(created, rng), approved_by=mid(mi_app) if mi_app is not None else None,
                     approved_at=ts(approved, rng) if approved else None, updated_at=None, progress_pct=0.0, cancelled_reason=None)
            gaux[gid] = dict(state=state, owner=n, created=created, approved=approved, perf=perf[n])
            goals.append(g)
            ev(entity_type="Goal", entity_id=gid, event_type="created", from_state=None, to_state="draft", field_changed=None, old_value=None,
               new_value=None, actor_id=eid(n), approved_by=None, approval_status="not_required", reason=None, occurred_at=g["created_at"])
            if approved:
                ev(entity_type="Goal", entity_id=gid, event_type="approved", from_state="draft", to_state="active", field_changed=None,
                   old_value=None, new_value=None, actor_id=mgr_empid(mi_app), approved_by=g["approved_by"], approval_status="approved",
                   reason=None, occurred_at=g["approved_at"])
            for j in range(kk):
                metric = rng.choice(list(KR_TPL))
                b, t, dr = mk_kr(rng, metric)
                kr = dict(kr_id="KR-%s-%02d" % (gid, j + 1), goal_id=gid, description=KR_TPL[metric].format(n=rng.choice(NOUNS[e["department"]])),
                          metric_type=metric, unit=UNITS[metric], direction=dr, baseline_value=b, target_value=t, weight=kw[j],
                          current_value=b, progress_pct=0.0, scoring_progress_pct=0.0, over_achievement_rationale=None, max_progress_pct=CAP)
                krs.append(kr); krs_by_goal[gid].append(kr)
            if state == "ok":
                ok_goals += 1
    gmap = {g["goal_id"]: g for g in goals}
    # cancellation events (before check-ins so cancelled goals carry none)
    for g in goals:
        a = gaux[g["goal_id"]]
        if a["state"] == "cancelled":
            cy = cyc[g["cycle_id"]]
            lo = a["approved"] + dt.timedelta(days=10); hi = min(g["due_date"], AS_OF)
            if lo > hi:
                a["state"] = "ok"; continue
            d = lo + dt.timedelta(days=rng.randint(0, (hi - lo).days))
            g["status"] = "cancelled"; g["cancelled_reason"] = rng.choice(CANCEL)
            mi = mgr_idx_at(a["owner"], d)
            ev(entity_type="Goal", entity_id=g["goal_id"], event_type="cancelled", from_state="active", to_state="cancelled", field_changed=None,
               old_value=None, new_value=None, actor_id=mgr_empid(mi), approved_by=mid(mi), approval_status="approved", reason=g["cancelled_reason"],
               occurred_at=ts(d, rng)); a["cancel_ts"] = d
    # approved changes
    for g in goals:
        a = gaux[g["goal_id"]]
        if a["state"] != "ok" or rng.random() >= 0.12:
            continue
        cy = cyc[g["cycle_id"]]
        for _ in range(rng.choice([1, 1, 2])):
            lo = a["approved"] + dt.timedelta(days=7); hi = min(g["due_date"], cy["end_date"], AS_OF) - dt.timedelta(days=7)
            if lo > hi:
                break
            d = lo + dt.timedelta(days=rng.randint(0, (hi - lo).days)); mi = mgr_idx_at(a["owner"], d)
            typ = rng.choices(["target_changed", "title_changed", "due_date_changed"], [.5, .25, .25])[0]
            if typ == "target_changed":
                kr = rng.choice(krs_by_goal[g["goal_id"]]); old = rnd_metric(kr["metric_type"], kr["target_value"] * rng.uniform(.75, 1.35))
                if old == kr["target_value"] or old == kr["baseline_value"]:
                    continue
                fld, ov, nv = "kr.%s.target_value" % kr["kr_id"], old, kr["target_value"]
            elif typ == "title_changed":
                fld, ov, nv = "goal.title", g["title"], g["title"] + " (scope revised)"; g["title"] = nv
            else:
                nd = g["due_date"] + dt.timedelta(days=rng.choice([-30, -15, 15, 30]))
                nd = min(nd, cy["end_date"])
                if nd <= g["start_date"] + dt.timedelta(days=30) or nd == g["due_date"]:
                    continue
                fld, ov, nv = "goal.due_date", g["due_date"].isoformat(), nd.isoformat(); g["due_date"] = nd
            g["version"] += 1
            ev(entity_type="Goal", entity_id=g["goal_id"], event_type=typ, from_state=None, to_state=None, field_changed=fld, old_value=str(ov),
               new_value=str(nv), actor_id=eid(a["owner"]), approved_by=mid(mi), approval_status="approved", reason="Scope adjustment agreed with manager",
               occurred_at=ts(d, rng))

    # ---------------- check-ins
    ok_goals_l = [g for g in goals if gaux[g["goal_id"]]["state"] == "ok"]
    capg = {}; ndict = {}
    for g in ok_goals_l:
        cy = cyc[g["cycle_id"]]; h1 = g["cycle_id"] == "CYCLE-2026-H1"
        s = g["start_date"] + dt.timedelta(days=5); eff = min(g["due_date"], cy["end_date"], AS_OF)
        days = (eff - s).days
        c_ = min(6 if h1 else 4, days // 10) if days >= 10 else 0
        capg[g["goal_id"]] = (c_, s, eff)
        n = rng.choices([0, 1, 2, 3, 4, 5], [.02, .12, .26, .30, .20, .10] if h1 else [.12, .28, .30, .22, .08, 0])[0]
        ndict[g["goal_id"]] = min(n, c_)
    gl = [g["goal_id"] for g in ok_goals_l]
    tot = sum(ndict.values())
    assert sum(capg[x][0] for x in gl) >= n_chk
    while tot > n_chk:
        x = rng.choice(gl)
        if ndict[x] > 1 or (ndict[x] == 1 and rng.random() < 0.05):
            ndict[x] -= 1; tot -= 1
    while tot < n_chk:
        x = rng.choice(gl)
        if ndict[x] < capg[x][0]:
            ndict[x] += 1; tot += 1

    chk = []; ckv = []; final_frac = {}
    for g in ok_goals_l:
        gid = g["goal_id"]; n = ndict[gid]
        if n == 0:
            continue
        a = gaux[gid]; _, s, eff = capg[gid]; days = (eff - s).days
        bw = (days + 1) / float(n); runmax = defaultdict(float)
        for kr in krs_by_goal[gid]:
            final_frac[kr["kr_id"]] = min(1.17, max(0.02, rng.gauss(a["perf"] * 1.15, 0.2)))
        for i in range(n):
            lo_ = int(bw * i); hi_ = max(lo_, int(bw * (i + 1)) - 1); d = min(eff, s + dt.timedelta(days=rng.randint(lo_, hi_)))
            span = max(1, (g["due_date"] - g["start_date"]).days)
            e_i = min(1.0, max(0.0, (d - g["start_date"]).days / float(span)))
            inc = list(krs_by_goal[gid]) if i == n - 1 else ([kr for kr in krs_by_goal[gid] if rng.random() < 0.75] or [rng.choice(krs_by_goal[gid])])
            c = dict(goal_id=gid, employee_id=eid(a["owner"]), checkin_date=d, _date=d)
            vals = []
            for kr in inc:
                fr = final_frac[kr["kr_id"]] * (e_i ** 0.7) * (1 + rng.gauss(0, 0.04))
                fr = min(1.19, max(0.0, fr)); runmax[kr["kr_id"]] = max(runmax[kr["kr_id"]], fr)
                vals.append(dict(kr=kr, value=safe_val(kr, runmax[kr["kr_id"]])))
            mi = mgr_idx_at(a["owner"], d)
            if rng.random() < 0.12:
                c["submitted_by"] = mgr_empid(mi); c["checkin_type"] = "manager_review"
            else:
                c["submitted_by"] = eid(a["owner"]); c["checkin_type"] = "self_update"
            c["_vals"] = vals; chk.append(c)
    chk.sort(key=lambda c: (c["checkin_date"], c["goal_id"]))
    for i, c in enumerate(chk):
        c["checkin_id"] = "CHK-%06d" % (i + 1)

    # anomaly: progress exceeds scale without rationale
    last_by_kr = {}
    for c in chk:
        for v in c["_vals"]:
            last_by_kr[v["kr"]["kr_id"]] = (c, v)
    elig = [k_ for k_ in last_by_kr if last_by_kr[k_][1]["kr"]["metric_type"] != "score"
            and (last_by_kr[k_][1]["value"] - last_by_kr[k_][1]["kr"]["baseline_value"]) / (last_by_kr[k_][1]["kr"]["target_value"] - last_by_kr[k_][1]["kr"]["baseline_value"]) <= 1.0]
    over_kr = rng.sample(elig, min(n_an["overshoot"], len(elig)))
    over_set = set(over_kr)
    for k_ in over_kr:
        c, v = last_by_kr[k_]; kr = v["kr"]
        v["value"] = rnd_metric(kr["metric_type"], kr["baseline_value"] + rng.uniform(1.25, 1.6) * (kr["target_value"] - kr["baseline_value"]))
    # anomaly: goal owner mismatch (stored owner differs from owner embedded in goal_id)
    cnt_ok = defaultdict(int)
    for g in goals:
        if gaux[g["goal_id"]]["state"] == "ok":
            cnt_ok[(g["employee_id"], g["cycle_id"])] += 1
    part_by_c = {c: [eid(n) for n in participants(c)] for c in cyc}
    cand = [g for g in goals if gaux[g["goal_id"]]["state"] == "ok" and cnt_ok[(g["employee_id"], g["cycle_id"])] >= 2]
    owner_bad = []
    for g in rng.sample(cand, min(n_an["owner"], len(cand))):
        a_ = g["employee_id"]
        if cnt_ok[(a_, g["cycle_id"])] < 2:
            continue
        b_ = rng.choice(part_by_c[g["cycle_id"]])
        if b_ == a_:
            continue
        cnt_ok[(a_, g["cycle_id"])] -= 1; g["employee_id"] = b_; owner_bad.append(g["goal_id"])

    # ---------------- derive KR / check-in / goal values
    ckv_n = 0; kr_cur = {}
    for c in chk:
        for v in c["_vals"]:
            kr_cur[v["kr"]["kr_id"]] = v["value"]
    for kr in krs:
        kr["current_value"] = kr_cur.get(kr["kr_id"], kr["baseline_value"])
        raw = kr_progress(kr, kr["current_value"]); kr["progress_pct"] = raw
        if raw > 100.0 and kr["kr_id"] not in over_set:
            kr["over_achievement_rationale"] = rng.choice(RATIONALE)
        kr["scoring_progress_pct"] = kr_scoring(raw, kr["over_achievement_rationale"] is not None)
    for g in goals:
        g["progress_pct"] = round(sum(k_["weight"] * k_["scoring_progress_pct"] for k_ in krs_by_goal[g["goal_id"]]), 2) if gaux[g["goal_id"]]["state"] == "ok" else 0.0
    # cumulative progress per check-in
    state = defaultdict(dict); chk_by_goal = defaultdict(list)
    cross_date = {}
    for c in chk:
        gid = c["goal_id"]; g = gmap[gid]
        for v in c["_vals"]:
            ckv_n += 1
            ckv.append(dict(value_id="CKV-%06d" % ckv_n, checkin_id=c["checkin_id"], kr_id=v["kr"]["kr_id"], reported_value=v["value"],
                            progress_pct=kr_progress(v["kr"], v["value"])))
            state[gid][v["kr"]["kr_id"]] = v["value"]
        cum = 0.0
        for kr in krs_by_goal[gid]:
            val = state[gid].get(kr["kr_id"], kr["baseline_value"])
            cum += kr["weight"] * kr_scoring(kr_progress(kr, val), kr["over_achievement_rationale"] is not None)
        c["cumulative_progress_pct"] = round(cum, 2)
        span = max(1, (g["due_date"] - g["start_date"]).days)
        c["expected_progress_pct"] = round(min(100.0, max(0.0, (c["checkin_date"] - g["start_date"]).days / float(span) * 100)), 2)
        ratio = c["cumulative_progress_pct"] / max(c["expected_progress_pct"], 1.0)
        c["confidence"] = "on_track" if ratio >= .9 else ("at_risk" if ratio >= .6 else "off_track")
        c["comment"] = rng.choice(CHK_COMMENT[c["confidence"]])
        c["evidence_required"] = 1 if any(kr_progress(v["kr"], v["value"]) >= 80.0 for v in c["_vals"]) else 0
        chk_by_goal[gid].append(c)
        if gid not in cross_date and c["cumulative_progress_pct"] >= COMPLETE:
            cross_date[gid] = c
    evid = []
    for c in chk:
        nev = rng.choice([1, 1, 2]) if c["evidence_required"] else rng.choices([0, 1, 2], [.55, .4, .05])[0]
        c["evidence_count"] = nev
        for _ in range(nev):
            et = rng.choice(EVID_TYPES); eidn = len(evid) + 1
            evid.append(dict(evidence_id="EVD-%06d" % eidn, checkin_id=c["checkin_id"], evidence_type=et,
                             url="https://evidence.example.test/%s/%06d" % (et, eidn), added_at=ts(c["checkin_date"], rng)))
    for c in chk:
        for k_ in ("_vals", "_date"):
            c.pop(k_, None)
    # goal statuses + status events
    for g in goals:
        a = gaux[g["goal_id"]]; cy = cyc[g["cycle_id"]]
        if a["state"] != "ok":
            continue
        if g["progress_pct"] >= COMPLETE:
            g["status"] = "completed"; c = cross_date.get(g["goal_id"])
            # status can only complete when a check-in crossed the threshold
            d = c["checkin_date"] if c else g["start_date"]
            ev(entity_type="Goal", entity_id=g["goal_id"], event_type="status_change", from_state="active", to_state="completed", field_changed=None,
               old_value=None, new_value=None, actor_id=eid(a["owner"]), approved_by=None, approval_status="not_required", reason=None, occurred_at=ts(d, rng))
        elif cy["status"] == "closed":
            g["status"] = "not_achieved"
            ev(entity_type="Goal", entity_id=g["goal_id"], event_type="status_change", from_state="active", to_state="not_achieved", field_changed=None,
               old_value=None, new_value=None, actor_id=None, approved_by=None, approval_status="not_required", reason="Cycle closed", occurred_at=cy["closed_at"])
    # anomaly: closed-cycle silent edit (unapproved content change after closed_at)
    h1_ok = [g for g in goals if g["cycle_id"] == "CYCLE-2026-H1" and gaux[g["goal_id"]]["state"] == "ok"]
    silent = []
    for g in rng.sample(h1_ok, min(n_an["silent"], len(h1_ok))):
        d = D(2026, 8, 16) + dt.timedelta(days=rng.randint(0, (AS_OF - D(2026, 8, 16)).days))
        if rng.random() < .5:
            fld, ov, nv = "goal.title", g["title"], g["title"] + " - reworded"; g["title"] = nv
        else:
            fld, ov, nv = "goal.description", g["description"], g["description"] + " Wording adjusted."; g["description"] = nv
        t = ts(d, rng)
        ev(entity_type="Goal", entity_id=g["goal_id"], event_type="edit_after_close", from_state=None, to_state=None, field_changed=fld, old_value=ov,
           new_value=nv, actor_id=rng.choice(ops_actors + [eid(gaux[g["goal_id"]]["owner"])]), approved_by=None, approval_status="none", reason=None, occurred_at=t)
        gaux[g["goal_id"]]["silent_ts"] = t; silent.append(g["goal_id"])
    for g in goals:
        ts_list = [g["created_at"]] + ([g["approved_at"]] if g["approved_at"] else [])
        g["updated_at"] = g["created_at"]
    evts_goal = defaultdict(list)
    for e_ in events:
        if e_["entity_type"] == "Goal" and e_["event_type"] in ("created", "approved", "target_changed", "title_changed", "due_date_changed", "cancelled", "edit_after_close"):
            evts_goal[e_["entity_id"]].append(e_["occurred_at"])
    for g in goals:
        g["updated_at"] = max(evts_goal[g["goal_id"]])

    # ---------------- reviews / assignments / feedback
    reviews = []; ras = []; fbs = []; rev_aux = {}
    gl_by = defaultdict(list)
    for g in goals:
        if gaux[g["goal_id"]]["state"] == "ok":
            gl_by[(g["employee_id"], g["cycle_id"])].append(g)
    h1c = cyc["CYCLE-2026-H1"]; closed_at = h1c["closed_at"]
    h1_part = participants("CYCLE-2026-H1"); h1_set = set(h1_part)
    team_pool = defaultdict(list); dept_pool = defaultdict(list)
    for n in h1_part:
        team_pool[mgr_idx_at(n, h1c["end_date"])].append(n); dept_pool[emps[n]["department"]].append(n)
    rev_n = 0; fb_n = 0; ra_n = 0
    def new_ra(rv, reviewee, reviewer, rtype, basis, appr, status, req, due, resp):
        nonlocal ra_n
        ra_n += 1
        r = dict(assignment_id="RA-%06d" % ra_n, review_id=rv, reviewee_id=eid(reviewee), reviewer_id=eid(reviewer) if isinstance(reviewer, int) else reviewer,
                 relationship_type=rtype, relationship_basis=basis, approved_by=appr, status=status, requested_at=req, due_date=due, responded_at=resp)
        ras.append(r); return r
    def rating_from(L, bias, sd):
        return int(min(5, max(1, round(L + rng.gauss(bias, sd)))))
    def day(base, off, hi=None):
        d = base + dt.timedelta(days=off)
        return min(d, hi) if hi else d
    for c in ("CYCLE-2026-H1", "CYCLE-2026-H2"):
        cy = cyc[c]; end_eff = min(cy["end_date"], AS_OF)
        for n in participants(c):
            rev_n += 1; rid = "REV-2026-%06d" % rev_n
            mi = mgr_idx_at(n, end_eff)
            rev = dict(review_id=rid, employee_id=eid(n), cycle_id=c, manager_id=mid(mi), status="not_started", manager_changed_in_cycle=0,
                       self_submitted_at=None, manager_submitted_at=None, finalized_at=None, goal_count=0, goal_progress_score=None,
                       avg_self_rating=None, avg_manager_rating=None, avg_peer_rating=None, required_inputs=4, received_inputs=0, completion_pct=0.0,
                       feedback_conflict_flag=0, final_rating=None, rating_band=None, score_as_of=end_eff)
            rev["manager_changed_in_cycle"] = 1 if any(fr > emps[n]["hire_date"] and cy["start_date"] <= fr <= cy["end_date"] for fr, to, m_ in asg[n]) else 0
            gl_ = gl_by.get((eid(n), c), [])
            rev["goal_count"] = len(gl_)
            if gl_:
                wsum = sum(g["weight_pct"] for g in gl_)
                rev["goal_progress_score"] = round(sum(g["weight_pct"] * g["progress_pct"] for g in gl_) / wsum, 2)
            reviews.append(rev)
            ev(entity_type="Review", entity_id=rid, event_type="created", from_state=None, to_state="not_started", field_changed=None, old_value=None,
               new_value=None, actor_id=None, approved_by=None, approval_status="not_required", reason=None, occurred_at=ts(cy["start_date"], rng))
            rev_aux[rid] = dict(n=n, mi=mi, cycle=c)
            if c != "CYCLE-2026-H1":
                continue
            # ----- H1 review lifecycle
            u = rng.random(); w0 = cy["review_window_start"]
            if u < 0.91:
                stage = "finalized"
            else:
                stage = rng.choices(["not_started", "self_submitted", "manager_submitted"], [.2, .45, .35])[0]
            self_ok = stage in ("finalized", "self_submitted", "manager_submitted")
            mgr_ok = stage in ("finalized", "manager_submitted")
            req_at = "%sT09:00:00" % w0.isoformat()
            s_off = min(28, 1 + int(rng.expovariate(1 / 7.0))); m_off = min(40, s_off + 1 + int(rng.expovariate(1 / 6.0)))
            s_ts = ts(day(w0, s_off), rng); m_ts = ts(day(w0, m_off), rng)
            if m_ts <= s_ts:
                m_ts = ts(day(w0, m_off + 1), rng)
            ra_self = new_ra(rid, n, n, "self", "self", None, "submitted" if self_ok else "expired", req_at, D(2026, 7, 15), s_ts if self_ok else None)
            mgr_e = mgr_emp[mi]
            ra_mgr = new_ra(rid, n, mgr_e, "manager", "direct_manager", None, "submitted" if mgr_ok else "expired", req_at, D(2026, 7, 31), m_ts if mgr_ok else None)
            npeer = rng.choices([2, 3], [.8, .2])[0]; used = {n, mgr_e}; peers = []
            for _ in range(npeer):
                for _try in range(30):
                    uu = rng.random()
                    if uu < .6 and len(team_pool[mi]) > 1:
                        p = rng.choice(team_pool[mi]); basis = "same_team"; appr = None
                    elif uu < .95:
                        p = rng.choice(dept_pool[emps[n]["department"]]); basis = "same_department"; appr = None
                    else:
                        p = rng.choice(h1_part); basis = "cross_functional_approved"; appr = mid(mi)
                    if p not in used:
                        used.add(p); peers.append((p, basis, appr)); break
            # peer outcomes
            pst = []
            for _ in peers:
                if stage == "finalized":
                    pst.append("submitted" if rng.random() < .85 else rng.choice(["declined", "expired", "expired"]))
                elif stage == "manager_submitted":
                    pst.append(rng.choice(["declined", "expired", "expired"]))
                else:
                    pst.append("submitted" if rng.random() < .5 else "expired")
            if stage == "finalized" and "submitted" not in pst and pst:
                pst[0] = "submitted"
            pra = []
            for (p, basis, appr), st in zip(peers, pst):
                resp = ts(day(w0, rng.randint(2, 24)), rng) if st in ("submitted", "declined") else None
                pra.append(new_ra(rid, n, p, "peer", basis, appr, st, req_at, D(2026, 7, 25), resp))
            L = {cid: min(5.0, max(1.0, 1 + 4 * min(1, max(0, rng.gauss(perf[n] * 0.92, .13))))) for cid in comp_ids}
            cs = sorted(rng.sample(comp_ids, 3))
            conflict_kind = rng.choices([None, "self_up", "mgr_down", "peer_split"], [.93, .03, .02, .02])[0]
            rows = []
            def fb_row(ra, ftype, cid, rating):
                nonlocal fb_n
                fb_n += 1
                refs = [None, None]
                if gl_ and rng.random() < (.3 if ftype == "self" else .6):
                    g = rng.choice(gl_); cks = chk_by_goal.get(g["goal_id"], [])
                    if cks and rng.random() < .5:
                        refs = ["check_in", rng.choice(cks)["checkin_id"]]
                    else:
                        refs = ["goal", g["goal_id"]]
                rows.append(dict(feedback_id="FB-%06d" % fb_n, review_id=rid, assignment_id=ra["assignment_id"], reviewee_id=eid(n), reviewer_id=ra["reviewer_id"],
                                 feedback_type=ftype, competency_id=cid, rating=rating, comment="%s: %s." % (comp_name[cid], rng.choice(PHRASE[rating])),
                                 evidence_ref_type=refs[0], evidence_ref_id=refs[1], submitted_at=ra["responded_at"], submission_channel="app"))
            if self_ok:
                for cid in cs:
                    fb_row(ra_self, "self", cid, rating_from(L[cid] + (1.8 if conflict_kind == "self_up" else 0), .35, .6))
            if mgr_ok:
                for cid in cs:
                    fb_row(ra_mgr, "manager", cid, rating_from(L[cid] - (1.8 if conflict_kind == "mgr_down" else 0), 0, .5))
            for pi, ra in enumerate(pra):
                if ra["status"] == "submitted":
                    off = 0
                    if conflict_kind == "peer_split":
                        off = 2.0 if pi % 2 == 0 else -2.0
                    for cid in rng.sample(cs, 2):
                        fb_row(ra, "peer", cid, rating_from(L[cid] + off, 0, .7))
            fbs.extend(rows)
            # derived
            def avg(t):
                v = [r["rating"] for r in rows if r["feedback_type"] == t]
                return round(sum(v) / len(v), 2) if v else None
            rev["avg_self_rating"] = avg("self"); rev["avg_manager_rating"] = avg("manager"); rev["avg_peer_rating"] = avg("peer")
            sub = [r for r in [ra_self, ra_mgr] + pra if r["status"] == "submitted"]
            rev["received_inputs"] = len(sub); rev["completion_pct"] = round(min(1.0, len(sub) / 4.0) * 100, 2)
            byc = defaultdict(list)
            for r in rows:
                byc[r["competency_id"]].append(r["rating"])
            conf = any(max(v) - min(v) >= 3 for v in byc.values() if len(v) > 1)
            if rev["avg_self_rating"] is not None and rev["avg_manager_rating"] is not None and abs(rev["avg_self_rating"] - rev["avg_manager_rating"]) >= 1.5:
                conf = True
            rev["feedback_conflict_flag"] = 1 if conf else 0
            rev["status"] = {"finalized": "finalized", "not_started": "closed_incomplete", "self_submitted": "closed_incomplete", "manager_submitted": "closed_incomplete"}[stage]
            if self_ok:
                rev["self_submitted_at"] = s_ts
            if mgr_ok:
                rev["manager_submitted_at"] = m_ts
            chain = [(None, "not_started", "created", None, None)]
            if self_ok:
                chain.append(("not_started", "self_submitted", "submitted", eid(n), s_ts))
            if mgr_ok:
                chain.append(("self_submitted", "manager_submitted", "submitted", mgr_empid(mi), m_ts))
            if stage == "finalized":
                f_ts = ts(day(w0, m_off + rng.randint(1, 5), D(2026, 8, 14)), rng)
                if f_ts <= m_ts:
                    f_ts = m_ts[:10] + "T23:00:00"
                rev["finalized_at"] = f_ts
                gr = 1 + 4 * min(rev["goal_progress_score"], CAP) / CAP
                rev["final_rating"] = round(.6 * gr + .4 * rev["avg_manager_rating"], 2)
                fr = rev["final_rating"]
                rev["rating_band"] = "Needs Improvement" if fr < 2 else "Developing" if fr < 3 else "Meets Expectations" if fr < 4 else "Exceeds Expectations" if fr < 4.5 else "Outstanding"
                chain.append(("manager_submitted", "finalized", "finalized", rng.choice(hr_partners), f_ts))
            else:
                prev = {"not_started": "not_started", "self_submitted": "self_submitted", "manager_submitted": "manager_submitted"}[stage]
                chain.append((prev, "closed_incomplete", "closed_incomplete", None, closed_at))
            for fs, ts_, et, actor, when in chain[1:]:
                ev(entity_type="Review", entity_id=rid, event_type=et, from_state=fs, to_state=ts_, field_changed=None, old_value=None, new_value=None,
                   actor_id=actor, approved_by=None, approval_status="not_required", reason=None, occurred_at=when)
            rev_aux[rid].update(cs=cs, rows=rows)
            for r in rows:
                pass
            rev_aux[rid]["peer_ids"] = [p[0] for p in peers]

    # anomalies in feedback: reviewer lacks relationship / untraceable
    fb_bad_rel = []; fb_untrace = []
    h1_reviews = [r for r in reviews if r["cycle_id"] == "CYCLE-2026-H1" and r["status"] == "finalized"]
    for rv in rng.sample(h1_reviews, min(n_an["lacks"], len(h1_reviews))):
        a = rev_aux[rv["review_id"]]; n = a["n"]; reviewee_mgr = a["mi"]
        for _t in range(100):
            p = rng.choice(h1_part)
            if emps[p]["department"] != emps[n]["department"] and mgr_idx_at(p, h1c["end_date"]) != reviewee_mgr and p != mgr_emp[reviewee_mgr]:
                break
        else:
            continue
        fb_n += 1; cid = rng.choice(a["cs"]); rt = rng.randint(1, 5)
        fbs.append(dict(feedback_id="FB-%06d" % fb_n, review_id=rv["review_id"], assignment_id=None, reviewee_id=eid(n), reviewer_id=eid(p), feedback_type="peer",
                        competency_id=cid, rating=rt, comment="%s: %s." % (comp_name[cid], rng.choice(PHRASE[rt])), evidence_ref_type=None, evidence_ref_id=None,
                        submitted_at=ts(D(2026, 7, 1) + dt.timedelta(days=rng.randint(2, 24)), rng), submission_channel="app"))
        fb_bad_rel.append(fbs[-1]["feedback_id"])
    for rv in rng.sample(h1_reviews, min(n_an["untrace"], len(h1_reviews))):
        a = rev_aux[rv["review_id"]]; n = a["n"]
        fb_n += 1; cid = rng.choice(a["cs"]); rt = rng.randint(1, 5)
        fbs.append(dict(feedback_id="FB-%06d" % fb_n, review_id=rv["review_id"], assignment_id=None, reviewee_id=eid(n), reviewer_id=None, feedback_type=rng.choice(["peer", "manager"]),
                        competency_id=cid, rating=rt, comment="%s: %s." % (comp_name[cid], rng.choice(PHRASE[rt])), evidence_ref_type=None, evidence_ref_id=None,
                        submitted_at=ts(D(2026, 7, 1) + dt.timedelta(days=rng.randint(2, 24)), rng), submission_channel="import"))
        fb_untrace.append(fbs[-1]["feedback_id"])

    # ---------------- development plans
    dps = []; dp_n = 0
    for rv in reviews:
        if rv["status"] != "finalized":
            continue
        a = rev_aux[rv["review_id"]]
        mrows = {}
        for r in a["rows"]:
            if r["feedback_type"] == "manager":
                mrows[r["competency_id"]] = r["rating"]
        plans = [(cid, "mandatory") for cid, v in sorted(mrows.items(), key=lambda x: (x[1], x[0])) if v <= 2][:2]
        if not plans and rv["rating_band"] == "Needs Improvement":
            plans = [(min(mrows, key=lambda k_: (mrows[k_], k_)), "mandatory")]
        if not plans and rng.random() < 0.12:
            plans = [(rng.choice(a["cs"]), "voluntary")]
        for cid, ptype in plans:
            dp_n += 1
            fin = dt.date.fromisoformat(rv["finalized_at"][:10])
            created = fin + dt.timedelta(days=1)
            budget = rng.choices([0, 250, 500, 1000, 1500, 2000, 2500, 3000], [.1, .15, .2, .2, .15, .1, .05, .05])[0]
            plan = dict(dev_plan_id="DP-%06d" % dp_n, review_id=rv["review_id"], employee_id=rv["employee_id"], competency_id=cid, plan_type=ptype,
                        activity_type=rng.choice(ACTIVITY), action_description="Targeted development on %s." % comp_name[cid].lower(), budget_usd=budget,
                        created_at=ts(created, rng), submitted_at=None, manager_approver_id=None, manager_decision=None, manager_decided_at=None,
                        requires_hr_approval=1 if budget > 1500 else 0, hr_approver_id=None, hr_decision=None, hr_decided_at=None, start_date=None,
                        target_date=None, completed_at=None, status="draft")
            sev = [("created", None, "draft", eid(int(rv["employee_id"][4:])), plan["created_at"])]
            last_d = created
            sub_d = created + dt.timedelta(days=rng.randint(1, 60))
            if rng.random() > .08 and sub_d <= AS_OF:
                plan["submitted_at"] = ts(sub_d, rng); plan["manager_approver_id"] = rv["manager_id"]; plan["status"] = "pending_manager"; last_d = sub_d
                sev.append(("submitted", "draft", "pending_manager", rv["employee_id"], plan["submitted_at"]))
                md = sub_d + dt.timedelta(days=rng.randint(1, 45))
                if md <= AS_OF:
                    plan["manager_decision"] = "rejected" if rng.random() < .08 else "approved"; plan["manager_decided_at"] = ts(md, rng); last_d = md
                    mgr_actor = mgr_empid(int(rv["manager_id"][4:]) - 1)
                    if plan["manager_decision"] == "rejected":
                        plan["status"] = "rejected"; to = "rejected"
                    elif plan["requires_hr_approval"]:
                        plan["status"] = "pending_hr"; to = "pending_hr"
                    else:
                        plan["status"] = "approved"; to = "approved"
                    sev.append(("manager_decision", "pending_manager", to, mgr_actor, plan["manager_decided_at"]))
                    if plan["status"] == "pending_hr":
                        hd = md + dt.timedelta(days=rng.randint(1, 30))
                        plan["hr_approver_id"] = rng.choice(hr_partners)
                        if hd <= AS_OF:
                            plan["hr_decision"] = "rejected" if rng.random() < .10 else "approved"; plan["hr_decided_at"] = ts(hd, rng); last_d = hd
                            plan["status"] = "rejected" if plan["hr_decision"] == "rejected" else "approved"
                            sev.append(("hr_decision", "pending_hr", plan["status"], plan["hr_approver_id"], plan["hr_decided_at"]))
            start = last_d + dt.timedelta(days=rng.randint(3, 14)); target = start + dt.timedelta(days=rng.randint(60, 180))
            plan["start_date"] = start; plan["target_date"] = target
            if plan["status"] == "approved" and start <= AS_OF:
                plan["status"] = "in_progress"
                sev.append(("status_change", "approved", "in_progress", None, ts(start, rng)))
                if target <= AS_OF and rng.random() < .6:
                    cd = max(start + dt.timedelta(days=1), target - dt.timedelta(days=rng.randint(0, 14)))
                    plan["completed_at"] = cd; plan["status"] = "completed"
                    sev.append(("status_change", "in_progress", "completed", eid(int(rv["employee_id"][4:])), ts(cd, rng)))
            dps.append(plan)
            for et, fs, tos, actor, when in sev:
                ev(entity_type="DevelopmentPlan", entity_id=plan["dev_plan_id"], event_type=et, from_state=fs, to_state=tos, field_changed=None, old_value=None,
                   new_value=None, actor_id=actor, approved_by=None, approval_status="not_required", reason=None, occurred_at=when)

    # ---------------- state_events numbering + ground truth
    events.sort(key=lambda e: (e["occurred_at"], e["_o"]))
    st = []
    for i, e in enumerate(events):
        e.pop("_o"); st.append(dict(event_id="EVT-%06d" % (i + 1), **e))
    gt = []
    def add_gt(et, ent, issue, cls, dec, rule, rel=None):
        gt.append(dict(gt_id="GT-%06d" % (len(gt) + 1), entity_type=et, entity_id=ent, issue_type=issue, label_class=cls, expected_decision=dec, rule_violated=rule, related_entity_id=rel))
    for g in owner_bad:
        add_gt("goals", g, "goal_owner_mismatch", "injected_anomaly", "reject", "goals.employee_id must equal the owner id embedded in goal_id")
    for k_ in over_kr:
        add_gt("key_results", k_, "progress_exceeds_scale_no_rationale", "injected_anomaly", "flag_for_review", "progress_pct > 100 requires over_achievement_rationale (cap 120)", k_.rsplit("-", 1)[0][3:])
    for f in fb_bad_rel:
        add_gt("feedback", f, "reviewer_lacks_relationship", "injected_anomaly", "reject", "Reviewer must hold a reviewer_assignment (manager of record, team, department or approved cross-functional)")
    for g in silent:
        add_gt("goals", g, "closed_cycle_silent_edit", "injected_anomaly", "flag_for_review", "Content edits after cycle closed_at require an approved reopen event")
    for f in fb_untrace:
        add_gt("feedback", f, "feedback_untraceable", "injected_anomaly", "reject", "Feedback must reference a reviewer_assignment and a reviewer")
    for r in reviews:
        if r["status"] == "closed_incomplete":
            add_gt("reviews", r["review_id"], "incomplete_review", "natural_exception", "accept_with_note", "Closed cycle without self, manager and >=1 peer input")
        if r["feedback_conflict_flag"]:
            add_gt("reviews", r["review_id"], "conflicting_feedback", "natural_exception", "accept_with_note", "Self/manager gap >=1.5 or rating spread >=3 on one competency")
        if r["manager_changed_in_cycle"]:
            add_gt("reviews", r["review_id"], "manager_transfer_mid_cycle", "natural_exception", "accept_with_note", "Reviewee changed manager during the cycle")
    for g in goals:
        if g["version"] > 1:
            add_gt("goals", g["goal_id"], "goal_changed", "natural_exception", "accept_with_note", "Approved change after initial approval (version > 1)")
    # rounding display types
    for c in cycles:
        pass
    tables = dict(employees=[emps[n] for n in ids], managers=managers, manager_assignments=asg_rows, review_cycles=cycles, competencies=competencies,
                  goals=goals, key_results=krs, check_ins=chk, check_in_kr_values=ckv, evidence_links=evid, reviews=reviews, reviewer_assignments=ras,
                  feedback=fbs, development_plans=dps, state_events=st, ground_truth=gt)
    return tables, P
