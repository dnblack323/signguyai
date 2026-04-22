import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { ShieldCheck, Loader2, RefreshCcw, ChevronDown, ChevronRight, CheckCircle2, XCircle, Clock, AlertTriangle, FileJson } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { getAuthToken } from '../../lib/authStorage';
import { useSetPageContext } from '../../context/PageContext';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ACTION_TYPE_OPTIONS = [
  { value: '', label: 'All action types' },
  { value: 'create_order', label: 'Create Order' },
  { value: 'create_job', label: 'Create Job' },
  { value: 'create_invoice', label: 'Create Invoice' },
  { value: 'create_calendar_event', label: 'Create Appointment' },
  { value: 'update_job_status', label: 'Update Job Status' },
  { value: 'assign_employee', label: 'Assign Employee' },
  { value: 'log_time_entry', label: 'Log Time Entry' },
  { value: 'add_material', label: 'Add Material' },
  { value: 'update_material_cost', label: 'Update Material Cost' },
  { value: 'categorize_expense', label: 'Categorize Expense' },
];

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'executed', label: 'Executed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'pending_confirmation', label: 'Pending Confirmation' },
];

const STATUS_BADGE = {
  executed: { icon: CheckCircle2, className: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  failed: { icon: XCircle, className: 'bg-rose-100 text-rose-800 border-rose-200' },
  cancelled: { icon: XCircle, className: 'bg-slate-100 text-slate-700 border-slate-200' },
  pending_confirmation: { icon: Clock, className: 'bg-amber-100 text-amber-800 border-amber-200' },
};

export default function AIAuditLog() {
  const { user } = useAuth();
  const navigate = useNavigate();
  useSetPageContext({ page: 'ai_audit_log' });

  const [entries, setEntries] = useState([]);
  const [totals, setTotals] = useState({ total: 0, executed: 0, failed: 0, cancelled: 0, pending: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ action_type: '', status: '', start_date: '', end_date: '' });
  const [expandedId, setExpandedId] = useState(null);

  const isAdmin = useMemo(() => user?.role === 'owner' || user?.role === 'admin', [user?.role]);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('limit', '200');
      if (filters.action_type) params.set('action_type', filters.action_type);
      if (filters.status) params.set('status', filters.status);
      if (filters.start_date) params.set('start_date', filters.start_date);
      if (filters.end_date) params.set('end_date', filters.end_date);
      const res = await axios.get(`${API_URL}/ai/assistant/actions/audit?${params.toString()}`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setEntries(res.data?.audit_log || []);
      setTotals(res.data?.totals || { total: 0, executed: 0, failed: 0, cancelled: 0, pending: 0 });
    } catch (e) {
      if (e.response?.status === 403) {
        toast.error('Admin access required to view AI audit log');
      } else {
        toast.error('Failed to load audit log');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, filters.action_type, filters.status, filters.start_date, filters.end_date]);

  if (!isAdmin) {
    return (
      <div className="max-w-2xl mx-auto mt-16 p-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-rose-500" /> Admin access required
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-600">
            The AI Audit Log is visible to Owner and Admin roles only.
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-4" data-testid="ai-audit-log-page">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-violet-100 text-violet-700 flex items-center justify-center">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-900">AI Audit Log</h1>
          <p className="text-xs text-slate-500">Every write action the Business Assistant performed, who triggered it, what record it touched, and whether it succeeded.</p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading} className="ml-auto" data-testid="ai-audit-refresh">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCcw className="h-3.5 w-3.5" />}
          <span className="ml-1.5">Refresh</span>
        </Button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        <KpiTile label="Total Actions" value={totals.total} />
        <KpiTile label="Executed" value={totals.executed} tone="emerald" />
        <KpiTile label="Failed" value={totals.failed} tone="rose" />
        <KpiTile label="Cancelled" value={totals.cancelled} tone="slate" />
        <KpiTile label="Pending" value={totals.pending} tone="amber" />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-3 flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <Label className="text-xs">Action Type</Label>
            <Select value={filters.action_type || 'all'} onValueChange={(v) => setFilters({ ...filters, action_type: v === 'all' ? '' : v })}>
              <SelectTrigger className="h-8 w-56" data-testid="ai-audit-filter-action-type"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ACTION_TYPE_OPTIONS.map(o => <SelectItem key={o.value || 'all'} value={o.value || 'all'}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label className="text-xs">Status</Label>
            <Select value={filters.status || 'all'} onValueChange={(v) => setFilters({ ...filters, status: v === 'all' ? '' : v })}>
              <SelectTrigger className="h-8 w-48" data-testid="ai-audit-filter-status"><SelectValue /></SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map(o => <SelectItem key={o.value || 'all'} value={o.value || 'all'}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label className="text-xs">From</Label>
            <Input type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} className="h-8 w-44" data-testid="ai-audit-filter-start" />
          </div>
          <div className="flex flex-col gap-1">
            <Label className="text-xs">To</Label>
            <Input type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} className="h-8 w-44" data-testid="ai-audit-filter-end" />
          </div>
          <Button size="sm" variant="ghost" onClick={() => setFilters({ action_type: '', status: '', start_date: '', end_date: '' })} className="ml-auto">Clear</Button>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="py-12 flex justify-center"><Loader2 className="h-6 w-6 text-slate-400 animate-spin" /></div>
          ) : entries.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              <AlertTriangle className="h-6 w-6 mx-auto text-slate-300 mb-2" />
              No AI actions match these filters yet.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2 text-left w-8"></th>
                  <th className="px-3 py-2 text-left">When</th>
                  <th className="px-3 py-2 text-left">User</th>
                  <th className="px-3 py-2 text-left">Action</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Summary</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {entries.map(e => {
                  const isOpen = expandedId === e.id;
                  const StatusIcon = (STATUS_BADGE[e.status] || {}).icon || Clock;
                  const statusClass = (STATUS_BADGE[e.status] || {}).className || 'bg-slate-100 text-slate-700 border-slate-200';
                  return (
                    <Row key={e.id} e={e} isOpen={isOpen} onToggle={() => setExpandedId(isOpen ? null : e.id)} StatusIcon={StatusIcon} statusClass={statusClass} navigate={navigate} />
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function KpiTile({ label, value, tone = 'violet' }) {
  const toneMap = {
    violet: 'bg-violet-50 text-violet-700 border-violet-100',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    rose: 'bg-rose-50 text-rose-700 border-rose-100',
    slate: 'bg-slate-50 text-slate-700 border-slate-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
  };
  return (
    <div className={`rounded-md border px-3 py-2 ${toneMap[tone]}`}>
      <div className="text-[10px] uppercase tracking-wide font-semibold">{label}</div>
      <div className="text-lg font-bold text-slate-900">{value}</div>
    </div>
  );
}

function Row({ e, isOpen, onToggle, StatusIcon, statusClass, navigate }) {
  const summary = buildSummary(e);
  const navRoute = buildOpenRoute(e);
  return (
    <>
      <tr className="border-t border-slate-100 hover:bg-slate-50/50" data-testid={`ai-audit-row-${e.id}`}>
        <td className="px-3 py-2 align-top">
          <button type="button" onClick={onToggle} className="text-slate-400 hover:text-slate-700">
            {isOpen ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </td>
        <td className="px-3 py-2 align-top whitespace-nowrap text-xs text-slate-600">
          {new Date(e.created_at).toLocaleString()}
        </td>
        <td className="px-3 py-2 align-top text-xs">{e.user_name || e.user_id || '—'}</td>
        <td className="px-3 py-2 align-top text-xs font-medium text-slate-800">{prettyAction(e.action_type)}</td>
        <td className="px-3 py-2 align-top">
          <Badge className={`${statusClass} border text-[10px] font-semibold gap-1 inline-flex items-center`}>
            <StatusIcon className="h-3 w-3" /> {e.status.replace(/_/g, ' ')}
          </Badge>
        </td>
        <td className="px-3 py-2 align-top text-xs text-slate-700">{summary}</td>
        <td className="px-3 py-2 align-top text-right">
          {navRoute && (
            <Button size="sm" variant="outline" className="h-7 text-[11px]" onClick={() => navigate(navRoute)} data-testid={`ai-audit-open-${e.id}`}>
              Open
            </Button>
          )}
        </td>
      </tr>
      {isOpen && (
        <tr className="bg-slate-50/80">
          <td colSpan={7} className="px-8 py-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
              <DetailSection title="Parameters">
                <PrettyJson value={e.parameters} />
              </DetailSection>
              <DetailSection title={e.error ? 'Error' : 'Result'}>
                <PrettyJson value={e.error || e.result} />
              </DetailSection>
            </div>
            <div className="mt-2 text-[10px] text-slate-500">
              audit id: <code className="bg-slate-100 px-1 rounded">{e.id}</code>
              {e.action_id && <> · action_id: <code className="bg-slate-100 px-1 rounded">{e.action_id}</code></>}
              {e.source && <> · source: <code className="bg-slate-100 px-1 rounded">{e.source}</code></>}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function DetailSection({ title, children }) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-slate-500 font-semibold mb-1">
        <FileJson className="h-3 w-3" /> {title}
      </div>
      <div className="rounded border border-slate-200 bg-white px-2 py-1.5 overflow-auto max-h-64">
        {children}
      </div>
    </div>
  );
}

function PrettyJson({ value }) {
  if (value === null || value === undefined) return <span className="text-slate-400">—</span>;
  if (typeof value === 'string') return <span className="text-slate-700">{value}</span>;
  return (
    <pre className="text-[11px] text-slate-800 whitespace-pre-wrap break-all font-mono">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function prettyAction(type) {
  if (!type) return '—';
  return type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function buildSummary(e) {
  const p = e.parameters || {};
  const r = e.result || {};
  if (e.action_type === 'create_order') {
    return `${r.order_number || 'Order'} for ${p.customer_name || p.company_name || 'customer'}`;
  }
  if (e.action_type === 'create_invoice') {
    return `${r.invoice_number || 'Invoice'} · ${r.total ? `$${r.total}` : p.notes || ''}`;
  }
  if (e.action_type === 'create_calendar_event') {
    return `${p.title || 'Event'} @ ${p.scheduled_at || p.date || ''}`;
  }
  if (e.action_type === 'log_time_entry') {
    return `${p.hours || ''} hrs · ${p.task || p.job_name || ''}`;
  }
  return Object.entries(p).slice(0, 2).map(([k, v]) => `${k}: ${typeof v === 'object' ? '…' : v}`).join(' · ');
}

function buildOpenRoute(e) {
  const r = e.result || {};
  if (r.navigate_to) return r.navigate_to;
  if (r.order_id) return `/orders/${r.order_id}`;
  if (r.invoice_id) return `/invoices`;
  return null;
}
