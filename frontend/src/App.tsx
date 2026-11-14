
import React, {useEffect, useMemo, useState} from 'react';
import {
  Activity, ArrowUpRight, Bell, BookOpenCheck, CheckCircle2,
  ChevronDown, CircleHelp, ClipboardCheck, FileText, Flag,
  Gauge, LayoutDashboard, MessageSquareText, Plus, Search,
  Settings, Sparkles, Target, Users, X
} from 'lucide-react';
import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer,
  Tooltip, XAxis, YAxis, BarChart, Bar
} from 'recharts';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const TOKEN_KEY = 'epms_access_token';

type AnyRow = Record<string, any>;

type SearchResult = {
  title: string;
  detail: string;
  tab: string;
  id: string;
  searchText: string;
};

async function get(path: string) {
  const token = localStorage.getItem(TOKEN_KEY);
  const r = await fetch(API + path, {
    headers: token ? {Authorization: `Bearer ${token}`} : {}
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY) || '');
  const [tab, setTab] = useState('Overview');
  const [overview, setOverview] = useState<AnyRow | null>(null);
  const [goals, setGoals] = useState<AnyRow[]>([]);
  const [reviews, setReviews] = useState<AnyRow[]>([]);
  const [checkins, setCheckins] = useState<AnyRow[]>([]);
  const [feedback, setFeedback] = useState<AnyRow[]>([]);
  const [plans, setPlans] = useState<AnyRow[]>([]);
  const [analytics, setAnalytics] = useState<AnyRow | null>(null);
  const [employees, setEmployees] = useState<AnyRow[]>([]);
  const [cycles, setCycles] = useState<AnyRow[]>([]);
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modal, setModal] = useState('');

  const load = async () => {
    setLoading(true);

    try {
      const [o, g, r, c, f, p, a, e, cy] = await Promise.all([
        get('/overview'),
        get('/goals?limit=250'),
        get('/reviews?limit=150'),
        get('/checkins?limit=150'),
        get('/feedback?limit=150'),
        get('/development-plans?limit=100'),
        get('/analytics'),
        get('/employees?limit=1000'),
        get('/cycles')
      ]);

      setOverview(o);
      setGoals(g);
      setReviews(r);
      setCheckins(c);
      setFeedback(f);
      setPlans(p);
      setAnalytics(a);
      setEmployees(e);
      setCycles(cy);
      setError('');
    } catch (e: any) {
      setError(e.message || 'Could not connect to API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) load();
    else setLoading(false);
  }, [token]);

  // Global search across all loaded sections
  const searchResults = useMemo<SearchResult[]>(() => {
    const q = query.trim().toLowerCase();

    if (!q) return [];

    const items: SearchResult[] = [
      ...employees.map(e => ({
        title: e.full_name || e.employee_id || 'Employee',
        detail: `${e.department || ''} · ${e.job_title || 'Employee'}`,
        tab: 'People',
        id: String(e.employee_id || ''),
        searchText: `${e.full_name || ''} ${e.employee_id || ''} ${e.department || ''} ${e.job_title || ''} ${e.location || ''}`
      })),

      ...goals.map(g => ({
        title: g.title || g.goal_id || 'Goal',
        detail: `${g.employee_name || g.employee_id || ''} · Goal`,
        tab: 'Goals & OKRs',
        id: String(g.goal_id || ''),
        searchText: `${g.title || ''} ${g.employee_name || ''} ${g.employee_id || ''} ${g.goal_id || ''} ${g.status || ''}`
      })),

      ...reviews.map(r => ({
        title: r.employee_name || r.review_id || 'Review',
        detail: `${r.cycle_name || ''} · Performance review`,
        tab: 'Reviews',
        id: String(r.review_id || ''),
        searchText: `${r.employee_name || ''} ${r.review_id || ''} ${r.cycle_name || ''} ${r.status || ''}`
      })),

      ...checkins.map(c => ({
        title: c.goal_title || c.checkin_id || 'Check-in',
        detail: `${c.employee_name || c.employee_id || ''} · Check-in`,
        tab: 'Check-ins',
        id: String(c.checkin_id || ''),
        searchText: `${c.goal_title || ''} ${c.employee_name || ''} ${c.employee_id || ''} ${c.checkin_id || ''} ${c.comment || ''}`
      })),

      ...feedback.map(f => ({
        title: f.reviewee_name || f.feedback_id || 'Feedback',
        detail: `${f.competency_name || ''} · Feedback`,
        tab: 'Feedback',
        id: String(f.feedback_id || ''),
        searchText: `${f.reviewee_name || ''} ${f.feedback_id || ''} ${f.competency_name || ''} ${f.feedback_type || ''} ${f.comment || ''}`
      })),

      ...plans.map(p => ({
        title: p.action_description || p.dev_plan_id || 'Development plan',
        detail: `${p.employee_name || p.employee_id || ''} · Development plan`,
        tab: 'Development',
        id: String(p.dev_plan_id || ''),
        searchText: `${p.action_description || ''} ${p.employee_name || ''} ${p.employee_id || ''} ${p.dev_plan_id || ''} ${p.competency_name || ''} ${p.status || ''}`
      }))
    ];

    return items
      .filter(item => item.searchText.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, employees, goals, reviews, checkins, feedback, plans]);

  // Keep the Goals & OKRs tab filter working independently
  const filtered = useMemo(
    () =>
      goals.filter(g =>
        `${g.title} ${g.employee_name} ${g.goal_id}`
          .toLowerCase()
          .includes(query.toLowerCase())
      ),
    [goals, query]
  );

  const selectSearchResult = (result: SearchResult) => {
    setTab(result.tab);
    setQuery('');
    setSearchOpen(false);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken('');
    setQuery('');
    setSearchOpen(false);
    setTab('Overview');
  };

  const nav = [
    ['Overview', LayoutDashboard],
    ['Goals & OKRs', Target],
    ['Check-ins', Activity],
    ['Reviews', ClipboardCheck],
    ['Feedback', MessageSquareText],
    ['Development', BookOpenCheck],
    ['People', Users]
  ] as const;

  if (!token) {
    return (
      <Login
        onLogin={t => {
          localStorage.setItem(TOKEN_KEY, t);
          setToken(t);
        }}
      />
    );
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandmark"><Sparkles size={20}/></div>
          <div>
            <b>elevate</b>
            <small>PEOPLE PERFORMANCE</small>
          </div>
        </div>

        {/* Workspace section intentionally unchanged */}
        <div className="workspace">
          <div className="workspace-icon">N</div>
          <div>
            <b>Northstar Labs</b>
            <small>Workspace</small>
          </div>
          <ChevronDown size={15}/>
        </div>

        <div className="navlabel">WORKSPACE</div>

        <nav>
          {nav.map(([n, I]) => (
            <button
              key={n}
              onClick={() => setTab(n)}
              className={tab === n ? 'active' : ''}
            >
              <I size={18}/>
              {n}

              {n === 'Reviews' && Number(overview?.open_reviews ?? 0) > 0 && (
                <span className="navcount">
                  {overview?.open_reviews ?? 0}
                </span>
              )}
            </button>
          ))}
        </nav>

        <div className="navlabel manage">MANAGE</div>

        <button className="navbutton">
          <Settings size={18}/>Settings
        </button>

        <button className="navbutton">
          <CircleHelp size={18}/>Help & support
        </button>

        <button
          type="button"
          className="profile profilebutton"
          onClick={logout}
          title="Sign out"
        >
          <div className="avatar">AP</div>
          <div>
            <b>HR Administrator</b>
            <small>Sign out</small>
          </div>
          <ChevronDown size={15}/>
        </button>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">
            Workspace <span>/</span> <b>{tab}</b>
          </div>

          <div className="top-actions">
            {/* Global search */}
            <div
              className="search-container"
              style={{position: 'relative', width: 'min(375px, 42vw)'}}
            >
              <div className="search">
                <Search size={16}/>

                <input
                  placeholder="Search employees, goals, reviews..."
                  value={query}
                  onChange={e => {
                    setQuery(e.target.value);
                    setSearchOpen(true);
                  }}
                  onFocus={() => setSearchOpen(true)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && searchResults.length > 0) {
                      selectSearchResult(searchResults[0]);
                    }

                    if (e.key === 'Escape') {
                      setSearchOpen(false);
                    }
                  }}
                />

                {query && (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery('');
                      setSearchOpen(false);
                    }}
                    aria-label="Clear search"
                    style={{
                      border: 0,
                      background: 'transparent',
                      cursor: 'pointer',
                      color: '#9299a8',
                      display: 'grid',
                      placeItems: 'center'
                    }}
                  >
                    <X size={15}/>
                  </button>
                )}

                <kbd>Enter</kbd>
              </div>

              {searchOpen && query.trim() && (
                <div
                  className="search-results"
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 10px)',
                    left: 0,
                    width: '100%',
                    maxHeight: 390,
                    overflowY: 'auto',
                    background: '#fff',
                    border: '1px solid #e7eaf0',
                    borderRadius: 12,
                    boxShadow: '0 12px 32px rgba(20,30,60,0.13)',
                    zIndex: 100,
                    padding: 8
                  }}
                >
                  {searchResults.length > 0 ? (
                    <>
                      <div
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          letterSpacing: '0.08em',
                          color: '#9299a8',
                          padding: '6px 8px'
                        }}
                      >
                        SEARCH RESULTS
                      </div>

                      {searchResults.map(result => (
                        <button
                          type="button"
                          className="search-result"
                          key={`${result.tab}-${result.id}`}
                          onClick={() => selectSearchResult(result)}
                          style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                            padding: 10,
                            border: 0,
                            background: 'transparent',
                            borderRadius: 8,
                            textAlign: 'left',
                            cursor: 'pointer',
                            color: '#273047'
                          }}
                        >
                          <span
                            style={{
                              width: 30,
                              height: 30,
                              display: 'grid',
                              placeItems: 'center',
                              background: '#f0f2fa',
                              color: '#6570c9',
                              borderRadius: 8,
                              flexShrink: 0
                            }}
                          >
                            <Search size={15}/>
                          </span>

                          <span style={{flex: 1, minWidth: 0}}>
                            <b
                              style={{
                                display: 'block',
                                fontSize: 13,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {result.title}
                            </b>
                            <small
                              style={{
                                display: 'block',
                                color: '#9299a8',
                                fontSize: 11,
                                marginTop: 3,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              {result.detail}
                            </small>
                          </span>

                          <span
                            style={{
                              color: '#737d91',
                              fontSize: 10,
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {result.tab}
                          </span>
                        </button>
                      ))}
                    </>
                  ) : (
                    <div
                      style={{
                        padding: '22px 12px',
                        textAlign: 'center',
                        fontSize: 13,
                        color: '#9299a8'
                      }}
                    >
                      No matching records found.
                    </div>
                  )}
                </div>
              )}
            </div>

            <button className="iconbtn" type="button" title="Notifications">
              <Bell size={18}/>
              <i/>
            </button>

            {/* Top-right avatar now logs out */}
            <button
              type="button"
              className="avatar small"
              title="Sign out"
              aria-label="Sign out"
              onClick={logout}
              style={{cursor: 'pointer'}}
            >
              AP
            </button>
          </div>
        </header>

        <div
          className="content"
          onClick={() => {
            if (searchOpen) setSearchOpen(false);
          }}
        >
          <div className="pagehead">
            <div>
              <div className="eyebrow">SATURDAY, NOVEMBER 14, 2026</div>
              <h1>
                {tab === 'Overview' ? 'Good afternoon, Aditya' : tab}
              </h1>
              <p>
                {tab === 'Overview'
                  ? 'Here’s what’s happening across your organization.'
                  : `Manage and track ${tab.toLowerCase()} across your organization.`}
              </p>
            </div>

            <div className="headbuttons">
              <button className="btn secondary" onClick={() => load()}>
                <Activity size={16}/> Refresh
              </button>

              {['Goals & OKRs', 'Check-ins', 'Feedback', 'Development'].includes(tab) && (
                <button
                  className="btn primary"
                  onClick={() =>
                    setModal(
                      tab === 'Goals & OKRs'
                        ? 'goal'
                        : tab === 'Check-ins'
                          ? 'checkin'
                          : tab === 'Development'
                            ? 'development'
                            : 'feedback'
                    )
                  }
                >
                  <Plus size={17}/> Create new
                </button>
              )}
            </div>
          </div>

          {error && (
            <div className="error">
              <b>Backend connection issue:</b> {error}. Start the Express API and refresh.
            </div>
          )}

          {loading ? (
            <div className="loading">Loading performance data…</div>
          ) : (
            <>
              {tab === 'Overview' && (
                <>
                  <div className="metricgrid">
                    {[
                      ['Total employees', overview?.employees, 'People in your organization', Users],
                      ['Active goals', overview?.goals, 'Across all review cycles', Target],
                      ['Average goal progress', `${overview?.avg_goal_progress ?? 0}%`, 'Calculated from key results', Gauge],
                      ['Reviews in progress', overview?.open_reviews, 'Awaiting required inputs', ClipboardCheck]
                    ].map(([label, val, sub, I]: any) => (
                      <div className="metric card" key={label}>
                        <div className="metric-top">
                          <span>{label}</span>
                          <I size={18}/>
                        </div>
                        <div className="metric-value">
                          {val?.toLocaleString?.() ?? val ?? 0}
                        </div>
                        <div className="metric-sub">
                          <span className="dot"/> {sub}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="twocol">
                    <section className="card chartcard">
                      <div className="sectionhead">
                        <div>
                          <h3>Goal progress by department</h3>
                          <p>Average progress across active goals</p>
                        </div>
                        <button
                          className="textbtn"
                          onClick={() => setTab('Goals & OKRs')}
                        >
                          View goals <ArrowUpRight size={14}/>
                        </button>
                      </div>

                      <div className="chart">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={analytics?.department_progress || []}
                            margin={{top: 8, right: 10, left: -18, bottom: 0}}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                              vertical={false}
                              stroke="#edf0f4"
                            />
                            <XAxis
                              dataKey="label"
                              tick={{fontSize: 11, fill: '#818a99'}}
                              axisLine={false}
                              tickLine={false}
                            />
                            <YAxis
                              domain={[0, 100]}
                              tick={{fontSize: 11, fill: '#818a99'}}
                              axisLine={false}
                              tickLine={false}
                            />
                            <Tooltip/>
                            <Bar
                              dataKey="value"
                              fill="#5b67d8"
                              radius={[5, 5, 0, 0]}
                              barSize={30}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </section>

                    <section className="card reviewcard">
                      <div className="sectionhead">
                        <div>
                          <h3>Review cycle snapshot</h3>
                          <p>Current cycle overview</p>
                        </div>
                        <span className="pill green">Live data</span>
                      </div>

                      {cycles.slice(0, 3).map(c => (
                        <div className="cycle" key={c.cycle_id}>
                          <div className="cycleline">
                            <b>{c.cycle_name}</b>
                            <span className={`pill ${c.status === 'open' ? 'green' : 'gray'}`}>
                              {c.status}
                            </span>
                          </div>
                          <div className="muted">
                            {c.start_date} — {c.end_date}
                          </div>
                          <div className="progress">
                            <span
                              style={{
                                width: `${Math.min(100, Number(overview?.avg_goal_progress) || 0)}%`
                              }}
                            />
                          </div>
                        </div>
                      ))}

                      <div className="reviewfoot">
                        <div>
                          <b>{overview?.reviews?.toLocaleString?.() ?? 0}</b>
                          <small>Total reviews</small>
                        </div>
                        <div>
                          <b>{overview?.feedback?.toLocaleString?.() ?? 0}</b>
                          <small>Feedback entries</small>
                        </div>
                        <div>
                          <b>{overview?.development_plans?.toLocaleString?.() ?? 0}</b>
                          <small>Growth plans</small>
                        </div>
                      </div>
                    </section>
                  </div>

                  <section className="card tablecard">
                    <div className="sectionhead">
                      <div>
                        <h3>Goals needing attention</h3>
                        <p>Latest goals across your organization</p>
                      </div>
                      <button
                        className="textbtn"
                        onClick={() => setTab('Goals & OKRs')}
                      >
                        View all <ArrowUpRight size={14}/>
                      </button>
                    </div>
                    <GoalTable data={goals.slice(0, 6)} onRefresh={load}/>
                  </section>
                </>
              )}

              {tab === 'Goals & OKRs' && (
                <section className="card tablecard">
                  <div className="sectionhead">
                    <div>
                      <h3>Goals & key results</h3>
                      <p>Progress is derived from measurable key results.</p>
                    </div>
                    <span className="pill blue">{filtered.length} shown</span>
                  </div>
                  <GoalTable data={filtered.slice(0, 100)} onRefresh={load}/>
                </section>
              )}

              {tab === 'Check-ins' && (
                <DataTable
                  title="Recent check-ins"
                  subtitle="Employee progress updates and evidence activity"
                  rows={checkins}
                  cols={[
                    'checkin_id',
                    'employee_name',
                    'goal_title',
                    'checkin_date',
                    'cumulative_progress_pct',
                    'confidence'
                  ]}
                />
              )}

              {tab === 'Reviews' && (
                <ReviewTable rows={reviews} onRefresh={load}/>
              )}

              {tab === 'Feedback' && (
                <DataTable
                  title="Competency feedback"
                  subtitle="Self, manager and peer feedback records"
                  rows={feedback}
                  cols={[
                    'feedback_id',
                    'reviewee_name',
                    'feedback_type',
                    'competency_name',
                    'rating',
                    'submitted_at'
                  ]}
                />
              )}

              {tab === 'Development' && (
                <DevelopmentTable rows={plans} onRefresh={load}/>
              )}

              {tab === 'People' && (
                <DataTable
                  title="People directory"
                  subtitle="Employees, roles and reporting information"
                  rows={employees}
                  cols={[
                    'employee_id',
                    'full_name',
                    'department',
                    'job_title',
                    'location',
                    'employment_status'
                  ]}
                />
              )}
            </>
          )}

          <footer>
            Elevate Performance Management <span>•</span> Synthetic dataset <span>•</span> API-connected workspace
          </footer>
        </div>
      </main>

      {modal && (
        <Modal
          type={modal}
          employees={employees}
          goals={goals}
          cycles={cycles}
          reviews={reviews}
          onClose={() => setModal('')}
          onDone={() => {
            setModal('');
            load();
          }}
        />
      )}
    </div>
  );
}

function GoalTable({
  data,
  onRefresh
}: {
  data: AnyRow[];
  onRefresh: () => void;
}) {
  const approve = async (id: string) => {
    const token = localStorage.getItem(TOKEN_KEY) || '';

    const r = await fetch(`${API}/goals/${id}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({})
    });

    if (!r.ok) {
      const d = await r.json();
      window.alert(d.detail || 'Approval failed');
      return;
    }

    onRefresh();
  };

  return (
    <div className="tablewrap">
      <table>
        <thead>
          <tr>
            <th>GOAL</th>
            <th>OWNER</th>
            <th>CYCLE</th>
            <th>PROGRESS</th>
            <th>STATUS</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          {data.map(g => (
            <tr key={g.goal_id}>
              <td>
                <div className="goalname">{g.title}</div>
                <small>{g.goal_id}</small>
              </td>
              <td>{g.employee_name || g.employee_id}</td>
              <td>{g.cycle_name || g.cycle_id}</td>
              <td>
                <div className="progresscell">
                  <div className="progress">
                    <span
                      style={{
                        width: `${Math.min(100, Math.max(0, g.progress_pct || 0))}%`
                      }}
                    />
                  </div>
                  <b>{Math.round(g.progress_pct || 0)}%</b>
                </div>
              </td>
              <td>
                <span
                  className={`pill ${
                    g.status === 'active'
                      ? 'blue'
                      : g.status === 'completed'
                        ? 'green'
                        : 'gray'
                  }`}
                >
                  {g.status}
                </span>
              </td>
              <td>
                {g.status === 'draft' ? (
                  <button
                    className="table-action"
                    onClick={() => approve(g.goal_id)}
                  >
                    Approve
                  </button>
                ) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {!data.length && <div className="empty">No goals found.</div>}
    </div>
  );
}

function DataTable({
  title,
  subtitle,
  rows,
  cols
}: {
  title: string;
  subtitle: string;
  rows: AnyRow[];
  cols: string[];
}) {
  return (
    <section className="card tablecard">
      <div className="sectionhead">
        <div>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
        <span className="pill blue">{rows.length} records</span>
      </div>

      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              {cols.map(c => (
                <th key={c}>{c.replaceAll('_', ' ').toUpperCase()}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 100).map((r, i) => (
              <tr key={r[cols[0]] || i}>
                {cols.map(c => (
                  <td key={c}>
                    {c === 'status'
                      ? <span className="pill gray">{r[c] || '—'}</span>
                      : r[c] ?? '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {!rows.length && <div className="empty">No records available.</div>}
      </div>
    </section>
  );
}

function Modal({
  type,
  employees,
  goals,
  cycles,
  reviews,
  onClose,
  onDone
}: {
  type: string;
  employees: AnyRow[];
  goals: AnyRow[];
  cycles: AnyRow[];
  reviews: AnyRow[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [form, setForm] = useState<any>({});
  const [krs, setKrs] = useState<AnyRow[]>([]);
  const [competencies, setCompetencies] = useState<AnyRow[]>([]);

  useEffect(() => {
    if (type === 'checkin' && form.goal_id) {
      get(`/goals/${form.goal_id}/key-results`)
        .then(setKrs)
        .catch(() => setKrs([]));
    }
  }, [type, form.goal_id]);

  useEffect(() => {
    if (type === 'feedback' || type === 'development') {
      get('/competencies')
        .then(setCompetencies)
        .catch(() => setCompetencies([]));
    }
  }, [type]);

  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (k: string, v: any) =>
    setForm((p: any) => ({...p, [k]: v}));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      const endpoint =
        type === 'checkin'
          ? '/checkins'
          : type === 'goal'
            ? '/goals'
            : type === 'development'
              ? '/development-plans'
              : '/feedback';

      const body =
        type === 'checkin'
          ? {...form, reported_value: Number(form.reported_value)}
          : type === 'goal'
            ? {...form, weight_pct: Number(form.weight_pct)}
            : type === 'development'
              ? {...form, budget_usd: Number(form.budget_usd || 0)}
              : {...form, rating: Number(form.rating)};

      const r = await fetch(API + endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}`
        },
        body: JSON.stringify(body)
      });

      if (!r.ok) throw new Error((await r.json()).detail || 'Request failed');

      onDone();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={e => e.stopPropagation()}>
        <div className="modalhead">
          <div>
            <h2>
              {type === 'checkin'
                ? 'Add a check-in'
                : type === 'goal'
                  ? 'Create a goal'
                  : type === 'development'
                    ? 'Create a development plan'
                    : 'Submit competency feedback'}
            </h2>
            <p>Changes are validated and persisted by the backend.</p>
          </div>
          <button className="iconbtn" onClick={onClose}>
            <X size={18}/>
          </button>
        </div>

        <form onSubmit={submit}>
          {type === 'goal' ? (
            <>
              <label>Employee
                <select
                  required
                  value={form.employee_id || ''}
                  onChange={e => set('employee_id', e.target.value)}
                >
                  <option value="">Select employee</option>
                  {employees.map(x => (
                    <option key={x.employee_id} value={x.employee_id}>
                      {x.full_name} — {x.department}
                    </option>
                  ))}
                </select>
              </label>

              <label>Review cycle
                <select
                  required
                  value={form.cycle_id || ''}
                  onChange={e => set('cycle_id', e.target.value)}
                >
                  <option value="">Select cycle</option>
                  {cycles.filter(x => x.status !== 'closed').map(x => (
                    <option key={x.cycle_id} value={x.cycle_id}>
                      {x.cycle_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Goal title
                <input
                  required
                  minLength={3}
                  value={form.title || ''}
                  onChange={e => set('title', e.target.value)}
                />
              </label>

              <label>Description
                <textarea
                  required
                  minLength={5}
                  value={form.description || ''}
                  onChange={e => set('description', e.target.value)}
                />
              </label>

              <label>Category
                <select
                  value={form.category || 'performance'}
                  onChange={e => set('category', e.target.value)}
                >
                  <option>performance</option>
                  <option>development</option>
                  <option>strategic</option>
                </select>
              </label>

              <label>Weight (%)
                <input
                  type="number"
                  min="5"
                  max="100"
                  required
                  value={form.weight_pct || ''}
                  onChange={e => set('weight_pct', e.target.value)}
                />
              </label>

              <label>Due date
                <input
                  type="date"
                  required
                  value={form.due_date || ''}
                  onChange={e => set('due_date', e.target.value)}
                />
              </label>

              <div className="formdivider">MEASURABLE KEY RESULT</div>

              <label>Key result description
                <input
                  required
                  minLength={3}
                  value={form.key_result_description || ''}
                  onChange={e => set('key_result_description', e.target.value)}
                  placeholder="e.g. Improve customer response time"
                />
              </label>

              <div className="formrow">
                <label>Baseline
                  <input
                    type="number"
                    value={form.baseline_value ?? 0}
                    onChange={e => set('baseline_value', Number(e.target.value))}
                  />
                </label>
                <label>Target
                  <input
                    type="number"
                    min="0.01"
                    required
                    value={form.target_value || ''}
                    onChange={e => set('target_value', e.target.value)}
                  />
                </label>
              </div>

              <div className="formrow">
                <label>Unit
                  <input
                    required
                    value={form.unit || 'count'}
                    onChange={e => set('unit', e.target.value)}
                  />
                </label>
                <label>Over-achievement rationale (optional)
                  <input
                    value={form.over_achievement_rationale || ''}
                    onChange={e => set('over_achievement_rationale', e.target.value)}
                    placeholder="Required if progress exceeds 100%"
                  />
                </label>
                <label>Direction
                  <select
                    value={form.direction || 'increase'}
                    onChange={e => set('direction', e.target.value)}
                  >
                    <option>increase</option>
                    <option>decrease</option>
                  </select>
                </label>
              </div>
            </>
          ) : type === 'checkin' ? (
            <>
              <label>Goal
                <select
                  required
                  value={form.goal_id || ''}
                  onChange={e => {
                    const g = goals.find(x => x.goal_id === e.target.value);
                    set('goal_id', e.target.value);
                    set('employee_id', g?.employee_id || '');
                  }}
                >
                  <option value="">Select goal</option>
                  {goals.slice(0, 500).map(g => (
                    <option key={g.goal_id} value={g.goal_id}>
                      {g.title} — {g.employee_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Key result
                <select
                  required
                  value={form.kr_id || ''}
                  onChange={e => set('kr_id', e.target.value)}
                >
                  <option value="">Select key result</option>
                  {krs.map(k => (
                    <option key={k.kr_id} value={k.kr_id}>
                      {k.description} · target {k.target_value} {k.unit}
                    </option>
                  ))}
                </select>
              </label>

              <label>Reported current value
                <input
                  type="number"
                  required
                  value={form.reported_value ?? ''}
                  onChange={e => set('reported_value', e.target.value)}
                />
              </label>

              <label>Evidence URL (optional)
                <input
                  type="url"
                  placeholder="https://..."
                  value={form.evidence_url || ''}
                  onChange={e => set('evidence_url', e.target.value)}
                />
              </label>

              <label>Update
                <textarea
                  required
                  minLength={3}
                  value={form.comment || ''}
                  onChange={e => set('comment', e.target.value)}
                  placeholder="What progress have you made?"
                />
              </label>
            </>
          ) : type === 'development' ? (
            <>
              <label>Review
                <select
                  required
                  value={form.review_id || ''}
                  onChange={e => {
                    const r = reviews.find(x => x.review_id === e.target.value);
                    set('review_id', e.target.value);
                    set('employee_id', r?.employee_id || '');
                  }}
                >
                  <option value="">Select review</option>
                  {reviews.map(r => (
                    <option key={r.review_id} value={r.review_id}>
                      {r.employee_name} — {r.cycle_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Competency
                <select
                  required
                  value={form.competency_id || ''}
                  onChange={e => set('competency_id', e.target.value)}
                >
                  <option value="">Select competency</option>
                  {competencies.map(x => (
                    <option key={x.competency_id} value={x.competency_id}>
                      {x.competency_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Plan type
                <select
                  value={form.plan_type || 'voluntary'}
                  onChange={e => set('plan_type', e.target.value)}
                >
                  <option value="voluntary">Voluntary</option>
                  <option value="mandatory">Mandatory</option>
                </select>
              </label>

              <label>Activity
                <select
                  value={form.activity_type || 'mentoring'}
                  onChange={e => set('activity_type', e.target.value)}
                >
                  <option value="course">Course</option>
                  <option value="mentoring">Mentoring</option>
                  <option value="stretch_assignment">Stretch assignment</option>
                  <option value="certification">Certification</option>
                  <option value="coaching">Coaching</option>
                </select>
              </label>

              <label>Action description
                <textarea
                  required
                  minLength={5}
                  value={form.action_description || ''}
                  onChange={e => set('action_description', e.target.value)}
                />
              </label>

              <div className="formrow">
                <label>Budget (USD)
                  <input
                    type="number"
                    min="0"
                    value={form.budget_usd ?? 0}
                    onChange={e => set('budget_usd', e.target.value)}
                  />
                </label>
                <label>Target date
                  <input
                    type="date"
                    required
                    value={form.target_date || ''}
                    onChange={e => set('target_date', e.target.value)}
                  />
                </label>
              </div>
            </>
          ) : (
            <>
              <label>Review
                <select
                  required
                  value={form.review_id || ''}
                  onChange={e => {
                    const r = reviews.find(x => x.review_id === e.target.value);
                    set('review_id', e.target.value);
                    set('reviewee_id', r?.employee_id || '');
                  }}
                >
                  <option value="">Select review</option>
                  {reviews.map(r => (
                    <option key={r.review_id} value={r.review_id}>
                      {r.employee_name} — {r.cycle_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Reviewer
                <select
                  required
                  value={form.reviewer_id || ''}
                  onChange={e => set('reviewer_id', e.target.value)}
                >
                  <option value="">Select reviewer</option>
                  {employees.map(x => (
                    <option key={x.employee_id} value={x.employee_id}>
                      {x.full_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Feedback type
                <select
                  value={form.feedback_type || 'manager'}
                  onChange={e => set('feedback_type', e.target.value)}
                >
                  <option value="self">Self</option>
                  <option value="manager">Manager</option>
                  <option value="peer">Peer</option>
                </select>
              </label>

              <label>Competency
                <select
                  required
                  value={form.competency_id || ''}
                  onChange={e => set('competency_id', e.target.value)}
                >
                  <option value="">Select competency</option>
                  {competencies.map(x => (
                    <option key={x.competency_id} value={x.competency_id}>
                      {x.competency_name}
                    </option>
                  ))}
                </select>
              </label>

              <label>Rating
                <select
                  value={form.rating || 5}
                  onChange={e => set('rating', e.target.value)}
                >
                  {[1, 2, 3, 4, 5].map(x => (
                    <option key={x} value={x}>{x}</option>
                  ))}
                </select>
              </label>

              <label>Feedback
                <textarea
                  required
                  minLength={3}
                  value={form.comment || ''}
                  onChange={e => set('comment', e.target.value)}
                />
              </label>
            </>
          )}

          {error && <div className="error">{error}</div>}

          <div className="modalactions">
            <button
              type="button"
              className="btn secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button className="btn primary" disabled={saving}>
              {saving ? 'Saving…' : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DevelopmentTable({
  rows,
  onRefresh
}: {
  rows: AnyRow[];
  onRefresh: () => void;
}) {
  const decide = async (
    id: string,
    stage: 'manager-decision' | 'hr-decision',
    decision: 'approved' | 'rejected'
  ) => {
    const reason = window.prompt(`Reason for ${decision}:`);
    if (!reason || reason.trim().length < 3) return;

    const token = localStorage.getItem(TOKEN_KEY) || '';

    const r = await fetch(`${API}/development-plans/${id}/${stage}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({decision, reason})
    });

    if (!r.ok) {
      const d = await r.json();
      window.alert(d.detail || 'Decision failed');
      return;
    }

    onRefresh();
  };

  return (
    <section className="card tablecard">
      <div className="sectionhead">
        <div>
          <h3>Development plans</h3>
          <p>Growth activities and manager / HR approval workflow</p>
        </div>
        <span className="pill blue">{rows.length} records</span>
      </div>

      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              {['PLAN', 'EMPLOYEE', 'COMPETENCY', 'TYPE', 'STATUS', 'BUDGET', 'ACTIONS'].map(x => (
                <th key={x}>{x}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.dev_plan_id}>
                <td>
                  <b>{r.dev_plan_id}</b>
                  <small>{r.action_description}</small>
                </td>
                <td>{r.employee_name || r.employee_id}</td>
                <td>{r.competency_name || '—'}</td>
                <td>{r.plan_type}</td>
                <td><span className="pill gray">{r.status}</span></td>
                <td>${Number(r.budget_usd || 0).toLocaleString()}</td>
                <td>
                  {r.status === 'pending_manager' ? (
                    <>
                      <button
                        className="table-action"
                        onClick={() => decide(r.dev_plan_id, 'manager-decision', 'approved')}
                      >
                        Approve
                      </button>
                      <button
                        className="table-action reject"
                        onClick={() => decide(r.dev_plan_id, 'manager-decision', 'rejected')}
                      >
                        Reject
                      </button>
                    </>
                  ) : r.status === 'pending_hr' ? (
                    <>
                      <button
                        className="table-action"
                        onClick={() => decide(r.dev_plan_id, 'hr-decision', 'approved')}
                      >
                        HR approve
                      </button>
                      <button
                        className="table-action reject"
                        onClick={() => decide(r.dev_plan_id, 'hr-decision', 'rejected')}
                      >
                        Reject
                      </button>
                    </>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!rows.length && (
          <div className="empty">No development plans available.</div>
        )}
      </div>
    </section>
  );
}

function ReviewTable({
  rows,
  onRefresh
}: {
  rows: AnyRow[];
  onRefresh: () => void;
}) {
  const finalize = async (id: string) => {
    if (!window.confirm('Finalize this review? This records a final rating and audit event.')) {
      return;
    }

    const token = localStorage.getItem(TOKEN_KEY) || '';

    const r = await fetch(`${API}/reviews/${id}/finalize`, {
      method: 'POST',
      headers: {Authorization: `Bearer ${token}`}
    });

    if (!r.ok) {
      const d = await r.json();
      window.alert(d.detail || 'Finalization failed');
      return;
    }

    onRefresh();
  };

  return (
    <section className="card tablecard">
      <div className="sectionhead">
        <div>
          <h3>Performance reviews</h3>
          <p>Review completion, required inputs and finalization</p>
        </div>
        <span className="pill blue">{rows.length} records</span>
      </div>

      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              {[
                'REVIEW', 'EMPLOYEE', 'CYCLE', 'STATUS',
                'COMPLETION', 'FINAL RATING', 'ACTION'
              ].map(x => <th key={x}>{x}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.review_id}>
                <td>{r.review_id}</td>
                <td>{r.employee_name}</td>
                <td>{r.cycle_name}</td>
                <td><span className="pill gray">{r.status}</span></td>
                <td>{Math.round(Number(r.completion_pct || 0))}%</td>
                <td>
                  {r.final_rating ?? '—'} {r.rating_band ? `(${r.rating_band})` : ''}
                </td>
                <td>
                  {r.status === 'manager_submitted' && Number(r.completion_pct) >= 100 ? (
                    <button
                      className="table-action"
                      onClick={() => finalize(r.review_id)}
                    >
                      Finalize
                    </button>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!rows.length && <div className="empty">No reviews available.</div>}
      </div>
    </section>
  );
}

function Login({onLogin}: {onLogin: (token: string) => void}) {
  const [email, setEmail] = useState('hr.admin@example.test');
  const [password, setPassword] = useState('DemoPass123!');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError('');

    try {
      const r = await fetch(API + '/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
      });

      const data = await r.json();

      if (!r.ok) throw new Error(data.detail || 'Sign-in failed');

      onLogin(data.token);
    } catch (err: any) {
      setError(err.message || 'Unable to sign in');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="brandmark login-mark">
          <Sparkles size={22}/>
        </div>

        <div className="eyebrow">PEOPLE PERFORMANCE PLATFORM</div>
        <h1>Welcome back</h1>
        <p>Sign in to manage goals, check-ins and performance reviews.</p>

        <form onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <div className="error">{error}</div>}

          <button className="btn primary login-submit" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="demo-hint">
          <b>Demo HR account</b>
          <br/>
          hr.admin@example.test / DemoPass123!
        </div>
      </div>
    </div>
  );
}
