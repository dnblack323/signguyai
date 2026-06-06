/**
 * PlatformAdminAnalytics.js
 * Platform-admin only analytics dashboard.
 * Route: /platform-admin/analytics
 */
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Users, ShoppingCart, FileText, Store, Shield, Globe, AlertTriangle,
  ArrowLeft, RefreshCw, Calendar, TrendingUp, Activity, Eye, Wifi,
  WifiOff, Info, Bot, UserCheck, UserX, Zap, ChevronDown, ChevronUp,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND = process.env.REACT_APP_BACKEND_URL;

// ── date range configs ────────────────────────────────────────────────────────
const DATE_RANGES = [
  { key: 'today',     label: 'Today' },
  { key: 'yesterday', label: 'Yesterday' },
  { key: '7d',        label: '7 Days' },
  { key: '14d',       label: '14 Days' },
  { key: '30d',       label: '30 Days' },
  { key: 'custom',    label: 'Custom' },
];

// ── helpers ───────────────────────────────────────────────────────────────────
const fmtDate  = (iso) => iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—';
const fmtTime  = (iso) => iso ? new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—';
const pctBar   = (v, total) => `${Math.round((v / Math.max(total, 1)) * 100)}%`;

function StatCard({ icon: Icon, label, value, sub, color = 'text-blue-600', badge, isNew }) {
  return (
    <Card className="relative overflow-hidden" data-testid={`stat-card-${label.toLowerCase().replace(/\s+/g, '-')}`}>
      {isNew && (
        <span className="absolute top-2 right-2 text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full font-medium">
          collecting
        </span>
      )}
      <CardContent className="pt-5 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide truncate">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value ?? '—'}</p>
            {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
          </div>
          <div className={`p-2 rounded-lg bg-muted/50 shrink-0 ml-2`}>
            <Icon className={`h-4 w-4 ${color}`} />
          </div>
        </div>
        {badge && <Badge variant="secondary" className="mt-2 text-xs">{badge}</Badge>}
      </CardContent>
    </Card>
  );
}

function SectionHeader({ icon: Icon, title, description }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="p-2 rounded-lg bg-muted">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div>
        <h3 className="font-semibold text-sm">{title}</h3>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-4 bg-muted rounded-full mb-3">
        <Icon className="h-6 w-6 text-muted-foreground" />
      </div>
      <p className="font-medium text-sm">{title}</p>
      <p className="text-xs text-muted-foreground mt-1 max-w-xs">{description}</p>
    </div>
  );
}

function InfoBanner() {
  const [open, setOpen] = useState(true);
  if (!open) return (
    <Button variant="ghost" size="sm" className="text-xs text-muted-foreground mb-4" onClick={() => setOpen(true)}>
      <Info className="h-3.5 w-3.5 mr-1" /> About these numbers
    </Button>
  );
  return (
    <div className="flex gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl mb-6" data-testid="analytics-info-banner">
      <Info className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
      <div className="flex-1 text-sm text-blue-900">
        <strong>Total requests ≠ total people.</strong> One user can generate many requests from page loads, API
        calls, images, background checks, and retries. <strong>Logged-in users</strong> and{' '}
        <strong>meaningful actions</strong> (orders, quotes, webstores, logins) are the best indicators of real
        app usage. Cards marked <span className="bg-amber-100 text-amber-700 text-xs px-1.5 py-0.5 rounded-full">collecting</span> start recording data from deploy and will be empty on first load.
      </div>
      <button onClick={() => setOpen(false)} className="text-blue-400 hover:text-blue-600 shrink-0">×</button>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function PlatformAdminAnalytics() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeRange, setActiveRange] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd,   setCustomEnd]   = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const [overview,    setOverview]    = useState(null);
  const [chartData,   setChartData]   = useState([]);
  const [users,       setUsers]       = useState([]);
  const [routes,      setRoutes]      = useState([]);
  const [sessions,    setSessions]    = useState([]);
  const [referrers,   setReferrers]   = useState([]);
  const [errors,      setErrors]      = useState(null);
  const [suspicious,  setSuspicious]  = useState(null);

  const [loading,  setLoading]  = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Redirect if not platform admin
  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied');
      navigate('/');
    }
  }, [user, navigate]);

  const authHeader = () => ({ Authorization: `Bearer ${getAuthToken()}` });

  const rangeParams = useCallback(() => {
    const p = new URLSearchParams({ range: activeRange });
    if (activeRange === 'custom') {
      if (customStart) p.set('custom_start', customStart);
      if (customEnd)   p.set('custom_end',   customEnd);
    }
    return p.toString();
  }, [activeRange, customStart, customEnd]);

  const fetchAll = useCallback(async () => {
    if (user?.role !== 'platform_admin') return;
    setLoading(true);
    setLoadError(null);
    const q = rangeParams();
    try {
      const [ovRes, chartRes, usersRes] = await Promise.all([
        fetch(`${BACKEND}/api/admin/analytics/overview?${q}`,      { headers: authHeader() }),
        fetch(`${BACKEND}/api/admin/analytics/activity-chart?${q}`, { headers: authHeader() }),
        fetch(`${BACKEND}/api/admin/analytics/users?${q}`,          { headers: authHeader() }),
      ]);
      if (!ovRes.ok) throw new Error('Failed to load analytics');
      const [ov, chart, usersData] = await Promise.all([ovRes.json(), chartRes.json(), usersRes.json()]);
      setOverview(ov);
      setChartData(chart.days || []);
      setUsers(usersData.users || []);
    } catch (e) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, [user, rangeParams]);

  const fetchTab = useCallback(async (tab) => {
    if (user?.role !== 'platform_admin') return;
    const q = rangeParams();
    const headers = authHeader();
    try {
      if (tab === 'routes') {
        const r = await fetch(`${BACKEND}/api/admin/analytics/routes?${q}`, { headers });
        setRoutes((await r.json()).routes || []);
      } else if (tab === 'sessions') {
        const r = await fetch(`${BACKEND}/api/admin/analytics/sessions?${q}`, { headers });
        setSessions((await r.json()).sessions || []);
      } else if (tab === 'referrers') {
        const r = await fetch(`${BACKEND}/api/admin/analytics/referrers?${q}`, { headers });
        setReferrers((await r.json()).referrers || []);
      } else if (tab === 'errors') {
        const r = await fetch(`${BACKEND}/api/admin/analytics/errors?${q}`, { headers });
        setErrors(await r.json());
      } else if (tab === 'suspicious') {
        const r = await fetch(`${BACKEND}/api/admin/analytics/suspicious?${q}`, { headers });
        setSuspicious(await r.json());
      }
    } catch {}
  }, [user, rangeParams]);

  useEffect(() => { if (user?.role === 'platform_admin') fetchAll(); }, [user, fetchAll]);

  useEffect(() => {
    if (activeTab !== 'overview' && activeTab !== 'users' && activeTab !== 'charts') {
      fetchTab(activeTab);
    }
  }, [activeTab, fetchTab]);

  // ── Render ───────────────────────────────────────────────────────────────

  if (loadError) {
    return (
      <div className="p-8 text-center">
        <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
        <p className="text-red-600 font-medium">{loadError}</p>
        <Button className="mt-3" onClick={fetchAll}>Retry</Button>
      </div>
    );
  }

  const ov = overview || {};

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1400px] mx-auto px-4 py-6 space-y-6">

        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => navigate('/platform-admin')} data-testid="analytics-back-btn">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-600" />
                <h1 className="text-xl font-bold">Admin Analytics</h1>
                <Badge variant="secondary" className="text-xs">Platform Admin</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Global usage across all tenants
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={fetchAll} disabled={loading} data-testid="analytics-refresh-btn">
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading…' : 'Refresh'}
          </Button>
        </div>

        {/* Date range selector */}
        <div className="flex flex-wrap items-center gap-2" data-testid="date-range-selector">
          {DATE_RANGES.map((r) => (
            <Button
              key={r.key}
              size="sm"
              variant={activeRange === r.key ? 'default' : 'outline'}
              onClick={() => { setActiveRange(r.key); }}
              data-testid={`range-btn-${r.key}`}
            >
              {r.label}
            </Button>
          ))}
          {activeRange === 'custom' && (
            <div className="flex gap-2 items-center ml-2">
              <Input type="date" className="h-8 text-xs w-36" value={customStart} onChange={(e) => setCustomStart(e.target.value)} />
              <span className="text-xs text-muted-foreground">to</span>
              <Input type="date" className="h-8 text-xs w-36" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} />
              <Button size="sm" onClick={fetchAll}>Apply</Button>
            </div>
          )}
        </div>

        <InfoBanner />

        {/* Main tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} data-testid="analytics-tabs">
          <TabsList className="flex-wrap h-auto gap-1">
            {[
              { key: 'overview',   label: 'Overview',   icon: Activity },
              { key: 'charts',     label: 'Charts',     icon: TrendingUp },
              { key: 'users',      label: 'Users',      icon: Users },
              { key: 'routes',     label: 'Routes',     icon: Globe },
              { key: 'sessions',   label: 'Sessions',   icon: Eye },
              { key: 'referrers',  label: 'Referrers',  icon: Zap },
              { key: 'errors',     label: 'Errors',     icon: AlertTriangle },
              { key: 'suspicious', label: 'Suspicious', icon: Bot },
            ].map(({ key, label, icon: Icon }) => (
              <TabsTrigger key={key} value={key} className="text-xs gap-1.5" data-testid={`analytics-tab-${key}`}>
                <Icon className="h-3.5 w-3.5" />{label}
              </TabsTrigger>
            ))}
          </TabsList>

          {/* ── OVERVIEW ──────────────────────────────────────────────────── */}
          <TabsContent value="overview" className="mt-4 space-y-6">

            {/* Business metrics (real, existing data) */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                Business Metrics — Real Data
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                <StatCard icon={Users}       label="New Accounts"   value={ov.new_users}    sub={`${ov.total_users} total`}     color="text-blue-600" />
                <StatCard icon={ShoppingCart} label="Orders Created"  value={ov.new_orders}   sub={`${ov.total_orders} total`}    color="text-emerald-600" />
                <StatCard icon={FileText}    label="Quotes Created"  value={ov.new_quotes}                                       color="text-violet-600" />
                <StatCard icon={Store}       label="Webstores"       value={ov.new_webstores} sub={`${ov.total_webstores} total`} color="text-amber-600" />
                <StatCard icon={Shield}      label="Admin Actions"   value={ov.audit_actions} sub="in audit log"                 color="text-rose-600" />
              </div>
            </div>

            {/* Forward-collecting metrics */}
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                Usage Tracking — Collecting from Deploy
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                <StatCard icon={Activity}  label="Total Events"     value={ov.total_events}       color="text-blue-600"    isNew />
                <StatCard icon={Eye}       label="Page Views"       value={ov.page_views}          color="text-teal-600"    isNew />
                <StatCard icon={Globe}     label="Sessions"         value={ov.total_sessions}      color="text-indigo-600"  isNew />
                <StatCard icon={Globe}     label="Unique Visitors"  value={ov.total_visitors}      color="text-cyan-600"    isNew />
                <StatCard icon={UserCheck} label="Logged-in Visits" value={ov.logged_in_visits}    color="text-emerald-600" isNew />
                <StatCard icon={UserX}     label="Anonymous Visits" value={ov.anonymous_visits}    color="text-gray-500"    isNew />
                <StatCard icon={Bot}       label="Bot Events"       value={ov.bot_events}          color="text-red-500"     isNew />
                <StatCard icon={AlertTriangle} label="Errors"       value={ov.error_events}        color="text-orange-500"  isNew />
                <StatCard icon={TrendingUp} label="Avg Req/Session" value={ov.avg_req_per_session} color="text-purple-600"  isNew />
              </div>
            </div>

            {/* Real Usage Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Real Usage Breakdown</CardTitle>
                <CardDescription className="text-xs">
                  Separates meaningful usage from infrastructure noise. Forward-collecting sections start empty.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { label: 'Logged-in App Users',       value: ov.logged_in_visits  || 0, color: 'bg-emerald-500', tag: 'collecting' },
                    { label: 'Anonymous Visitors',        value: ov.anonymous_visits   || 0, color: 'bg-blue-400',   tag: 'collecting' },
                    { label: 'Bot / Crawler Traffic',     value: ov.bot_events         || 0, color: 'bg-red-400',    tag: 'collecting' },
                    { label: 'New Accounts Created',      value: ov.new_users          || 0, color: 'bg-violet-500', tag: 'real' },
                    { label: 'Business Actions (O+Q+W)',  value: (ov.new_orders||0)+(ov.new_quotes||0)+(ov.new_webstores||0), color: 'bg-amber-500', tag: 'real' },
                    { label: 'Error Events',              value: ov.error_events       || 0, color: 'bg-orange-400', tag: 'collecting' },
                  ].map((row) => {
                    const total = Math.max(ov.total_events || 1, row.value);
                    const pct = Math.round(row.value / total * 100);
                    return (
                      <div key={row.label} className="space-y-1">
                        <div className="flex justify-between items-center text-xs">
                          <div className="flex items-center gap-2">
                            <span className={`inline-block w-2 h-2 rounded-full ${row.color}`} />
                            <span>{row.label}</span>
                            {row.tag === 'collecting' && (
                              <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 rounded-full">collecting</span>
                            )}
                          </div>
                          <span className="font-mono font-medium">{row.value.toLocaleString()}</span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div className={`h-full ${row.color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

          </TabsContent>

          {/* ── CHARTS ──────────────────────────────────────────────────────── */}
          <TabsContent value="charts" className="mt-4 space-y-6">
            {/* Business activity over time */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Business Activity Over Time</CardTitle>
                <CardDescription className="text-xs">Orders, quotes, webstores and new users — real data from existing records</CardDescription>
              </CardHeader>
              <CardContent>
                {chartData.length === 0 ? (
                  <EmptyState icon={TrendingUp} title="No data" description="Loading chart data…" />
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={chartData} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="gOrders"    x1="0" y1="0" x2="0" y2="1"><stop offset="5%"  stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
                        <linearGradient id="gQuotes"    x1="0" y1="0" x2="0" y2="1"><stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.3}/><stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/></linearGradient>
                        <linearGradient id="gWebstores" x1="0" y1="0" x2="0" y2="1"><stop offset="5%"  stopColor="#f59e0b" stopOpacity={0.3}/><stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/></linearGradient>
                        <linearGradient id="gUsers"     x1="0" y1="0" x2="0" y2="1"><stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3}/><stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Area type="monotone" dataKey="orders"    name="Orders"    stroke="#10b981" fill="url(#gOrders)"    strokeWidth={2} />
                      <Area type="monotone" dataKey="quotes"    name="Quotes"    stroke="#8b5cf6" fill="url(#gQuotes)"    strokeWidth={2} />
                      <Area type="monotone" dataKey="webstores" name="Webstores" stroke="#f59e0b" fill="url(#gWebstores)" strokeWidth={2} />
                      <Area type="monotone" dataKey="new_users" name="New Users" stroke="#3b82f6" fill="url(#gUsers)"     strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Page views / errors (forward-collecting) */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Page Views &amp; Errors
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
                <CardDescription className="text-xs">Starts empty — will fill as users visit the app after this feature is deployed</CardDescription>
              </CardHeader>
              <CardContent>
                {chartData.every(d => d.page_views === 0 && d.errors === 0) ? (
                  <EmptyState
                    icon={Activity}
                    title="No page view data yet"
                    description="Page view and error tracking begins collecting after this analytics feature is deployed. Check back after your first real user session."
                  />
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={chartData} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={{ fontSize: 12 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      <Line type="monotone" dataKey="page_views" name="Page Views" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="errors"     name="Errors"     stroke="#ef4444" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── USERS ─────────────────────────────────────────────────────── */}
          <TabsContent value="users" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Logged-in User Activity</CardTitle>
                <CardDescription className="text-xs">All tenant users. Orders/quotes/webstores counted within the selected date range.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {users.length === 0 ? (
                  <EmptyState icon={Users} title="No users found" description="No non-admin users in the system." />
                ) : (
                  <Table data-testid="users-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Name</TableHead>
                        <TableHead className="text-xs">Email</TableHead>
                        <TableHead className="text-xs">Role</TableHead>
                        <TableHead className="text-xs">Company</TableHead>
                        <TableHead className="text-xs text-right">Orders</TableHead>
                        <TableHead className="text-xs text-right">Quotes</TableHead>
                        <TableHead className="text-xs text-right">Webstores</TableHead>
                        <TableHead className="text-xs text-right">Admin Actions</TableHead>
                        <TableHead className="text-xs">Joined</TableHead>
                        <TableHead className="text-xs">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((u) => (
                        <TableRow key={u.id} data-testid={`user-row-${u.id}`}>
                          <TableCell className="text-xs font-medium whitespace-nowrap">{u.full_name || '—'}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{u.email}</TableCell>
                          <TableCell className="text-xs">
                            <Badge variant="outline" className="text-[10px] capitalize">{u.role?.replace('_', ' ')}</Badge>
                          </TableCell>
                          <TableCell className="text-xs">{u.company_name || '—'}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{u.orders}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{u.quotes}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{u.webstores}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{u.admin_actions}</TableCell>
                          <TableCell className="text-xs text-muted-foreground whitespace-nowrap">{fmtDate(u.created_at)}</TableCell>
                          <TableCell>
                            <Badge variant={u.is_active ? 'default' : 'destructive'} className="text-[10px]">
                              {u.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── ROUTES ────────────────────────────────────────────────────── */}
          <TabsContent value="routes" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Top Pages &amp; Routes
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
                <CardDescription className="text-xs">Ranked by page view events received. Starts collecting after deploy.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {routes.length === 0 ? (
                  <EmptyState
                    icon={Globe}
                    title="No route data yet"
                    description="Page view tracking begins after this feature is deployed. Routes will appear here as users navigate the app."
                  />
                ) : (
                  <Table data-testid="routes-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Route</TableHead>
                        <TableHead className="text-xs text-right">Views</TableHead>
                        <TableHead className="text-xs text-right">Unique Users</TableHead>
                        <TableHead className="text-xs text-right">Unique Visitors</TableHead>
                        <TableHead className="text-xs">Last Accessed</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {routes.map((r, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-xs font-mono">{r.route || '/'}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.requests}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.unique_users}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.unique_visitors}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(r.last_accessed)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── SESSIONS ──────────────────────────────────────────────────── */}
          <TabsContent value="sessions" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Visitor Sessions
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {sessions.length === 0 ? (
                  <EmptyState
                    icon={Eye}
                    title="No session data yet"
                    description="Sessions are created when visitors browse the app. Check back after your first post-deploy user session."
                  />
                ) : (
                  <Table data-testid="sessions-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Session ID</TableHead>
                        <TableHead className="text-xs">IP</TableHead>
                        <TableHead className="text-xs">Device/Browser</TableHead>
                        <TableHead className="text-xs">Referrer</TableHead>
                        <TableHead className="text-xs">First Seen</TableHead>
                        <TableHead className="text-xs">Last Seen</TableHead>
                        <TableHead className="text-xs text-right">Requests</TableHead>
                        <TableHead className="text-xs">Logged In</TableHead>
                        <TableHead className="text-xs">Bot</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sessions.map((s) => (
                        <TableRow key={s.session_id}>
                          <TableCell className="text-xs font-mono">{s.session_id?.slice(0, 8)}…</TableCell>
                          <TableCell className="text-xs font-mono">{s.ip_address || '—'}</TableCell>
                          <TableCell className="text-xs max-w-[180px] truncate" title={s.user_agent}>{s.user_agent?.slice(0, 50) || '—'}</TableCell>
                          <TableCell className="text-xs max-w-[140px] truncate" title={s.referrer}>{s.referrer || 'Direct'}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(s.first_seen)}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(s.last_seen)}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{s.requests}</TableCell>
                          <TableCell>
                            {s.is_logged_in
                              ? <Badge className="text-[10px] bg-emerald-100 text-emerald-700 border-0">Yes</Badge>
                              : <Badge variant="outline" className="text-[10px]">No</Badge>}
                          </TableCell>
                          <TableCell>
                            {s.is_bot
                              ? <Badge className="text-[10px] bg-red-100 text-red-700 border-0">Bot</Badge>
                              : <Badge variant="outline" className="text-[10px]">Human</Badge>}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── REFERRERS ─────────────────────────────────────────────────── */}
          <TabsContent value="referrers" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Traffic Sources &amp; Referrers
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {referrers.length === 0 ? (
                  <EmptyState
                    icon={Zap}
                    title="No referrer data yet"
                    description="Traffic source breakdown starts collecting after deploy."
                  />
                ) : (
                  <Table data-testid="referrers-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Source</TableHead>
                        <TableHead className="text-xs text-right">Requests</TableHead>
                        <TableHead className="text-xs text-right">Unique Visitors</TableHead>
                        <TableHead className="text-xs text-right">Logged In</TableHead>
                        <TableHead className="text-xs text-right">% of Traffic</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {referrers.map((r) => (
                        <TableRow key={r.source}>
                          <TableCell className="text-xs font-medium">{r.source}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.requests}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.unique_visitors}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.logged_in}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{r.pct}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── ERRORS ────────────────────────────────────────────────────── */}
          <TabsContent value="errors" className="mt-4 space-y-4">
            {errors && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard icon={AlertTriangle} label="Total Errors"     value={errors.total_errors}    color="text-red-500"    isNew />
                <StatCard icon={WifiOff}       label="Frontend Errors"  value={errors.frontend_errors} color="text-orange-500" isNew />
                <StatCard icon={Activity}      label="API Errors"       value={errors.api_errors}      color="text-amber-500"  isNew />
              </div>
            )}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Error Log
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
                <CardDescription className="text-xs">Frontend crashes, API failures, and unhandled errors. Includes black screen/render errors.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {!errors || errors.errors?.length === 0 ? (
                  <EmptyState
                    icon={AlertTriangle}
                    title="No errors recorded yet"
                    description="Error tracking starts collecting after deploy. This is the first place to check if users report blank screens or broken pages."
                  />
                ) : (
                  <Table data-testid="errors-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">Type</TableHead>
                        <TableHead className="text-xs">Route</TableHead>
                        <TableHead className="text-xs">Message</TableHead>
                        <TableHead className="text-xs text-right">Count</TableHead>
                        <TableHead className="text-xs text-right">Affected</TableHead>
                        <TableHead className="text-xs">Last Occurred</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {errors.errors.map((e, i) => (
                        <TableRow key={i}>
                          <TableCell>
                            <Badge variant="destructive" className="text-[10px]">{e.event_type}</Badge>
                          </TableCell>
                          <TableCell className="text-xs font-mono">{e.route || '—'}</TableCell>
                          <TableCell className="text-xs max-w-[220px] truncate" title={e.message}>{e.message}</TableCell>
                          <TableCell className="text-xs text-right font-mono font-bold text-red-600">{e.count}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{e.affected_users}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(e.last_occurred)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── SUSPICIOUS ────────────────────────────────────────────────── */}
          <TabsContent value="suspicious" className="mt-4 space-y-4">
            {suspicious && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard icon={Bot}          label="Bot Events"     value={suspicious.total_bot}       color="text-red-500"    isNew />
                <StatCard icon={AlertTriangle} label="Suspicious"    value={suspicious.total_suspicious} color="text-orange-500" isNew />
                <StatCard icon={Activity}     label="Bot % of Traffic" value={`${suspicious.bot_pct ?? 0}%`} color="text-amber-500" isNew />
              </div>
            )}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  Bot &amp; Suspicious Traffic
                  <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">collecting from deploy</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Flagged based on user-agent strings, suspicious path patterns (/wp-admin, /.env, /phpmyadmin), and high-frequency behaviour.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                {!suspicious || suspicious.suspicious?.length === 0 ? (
                  <EmptyState
                    icon={Bot}
                    title="No suspicious traffic detected"
                    description="Bot and suspicious path detection starts after deploy. Any flagged sessions will appear here with their user-agent and reason."
                  />
                ) : (
                  <Table data-testid="suspicious-table">
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-xs">IP</TableHead>
                        <TableHead className="text-xs">Label</TableHead>
                        <TableHead className="text-xs">User Agent</TableHead>
                        <TableHead className="text-xs text-right">Requests</TableHead>
                        <TableHead className="text-xs text-right">Sessions</TableHead>
                        <TableHead className="text-xs">First Seen</TableHead>
                        <TableHead className="text-xs">Last Seen</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {suspicious.suspicious.map((s, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-xs font-mono">{s.ip_address || '—'}</TableCell>
                          <TableCell>
                            <Badge
                              className={`text-[10px] ${s.is_bot ? 'bg-red-100 text-red-700 border-0' : 'bg-orange-100 text-orange-700 border-0'}`}
                            >
                              {s.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs max-w-[200px] truncate" title={s.user_agent}>{s.user_agent || '—'}</TableCell>
                          <TableCell className="text-xs text-right font-mono font-bold">{s.requests}</TableCell>
                          <TableCell className="text-xs text-right font-mono">{s.session_count}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(s.first_seen)}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{fmtTime(s.last_seen)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </div>
    </div>
  );
}
