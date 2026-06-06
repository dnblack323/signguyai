import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  ArrowLeft,
  Mail,
  Search,
  RefreshCw,
  Filter,
  Eye,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLORS = {
  delivered: 'bg-emerald-100 text-emerald-900 border-emerald-300',
  sent: 'bg-blue-100 text-blue-900 border-blue-300',
  deferred: 'bg-amber-100 text-amber-900 border-amber-300',
  bounce: 'bg-red-100 text-red-900 border-red-300',
  dropped: 'bg-red-100 text-red-900 border-red-300',
  blocked: 'bg-red-100 text-red-900 border-red-300',
  spamreport: 'bg-purple-100 text-purple-900 border-purple-300',
  failed: 'bg-rose-100 text-rose-900 border-rose-300',
};

const STATUS_OPTIONS = [
  'delivered', 'sent', 'deferred', 'bounce', 'dropped', 'blocked',
  'spamreport', 'failed',
];

function formatDateTime(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function StatCard({ label, value, tone, testId }) {
  const toneClass =
    tone === 'good'
      ? 'border-emerald-200 bg-emerald-50/50'
      : tone === 'warn'
      ? 'border-amber-200 bg-amber-50/50'
      : tone === 'bad'
      ? 'border-red-200 bg-red-50/50'
      : 'border-gray-200';
  return (
    <Card className={`${toneClass}`} data-testid={testId}>
      <CardContent className="pt-5 pb-4">
        <div className="text-xs uppercase tracking-wide text-gray-600">
          {label}
        </div>
        <div className="text-3xl font-bold text-gray-900 mt-1">
          {value ?? 0}
        </div>
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminEmailLogs() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [emailFilter, setEmailFilter] = useState('');
  const [tenantIdFilter, setTenantIdFilter] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (user && user.role !== 'platform_admin' && user.role !== 'platform_creator') {
      toast.error('Access denied');
      navigate('/');
    }
  }, [user, navigate]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        navigate('/login');
        return;
      }
      const params = new URLSearchParams();
      params.set('limit', '300');
      if (statusFilter && statusFilter !== 'all') params.set('delivery_status', statusFilter);
      if (emailFilter.trim()) params.set('to_email', emailFilter.trim());
      if (tenantIdFilter.trim()) params.set('tenant_id', tenantIdFilter.trim());

      const summaryParams = new URLSearchParams();
      if (tenantIdFilter.trim()) summaryParams.set('tenant_id', tenantIdFilter.trim());

      const [logRes, sumRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/platform-admin/email-logs?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${BACKEND_URL}/api/platform-admin/email-logs/summary?${summaryParams.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);
      if (!logRes.ok) throw new Error('Failed to load email logs');
      if (!sumRes.ok) throw new Error('Failed to load summary');
      const logs = await logRes.json();
      const sum = await sumRes.json();
      setEntries(logs.entries || []);
      setSummary(sum);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load email deliverability data');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, emailFilter, tenantIdFilter, navigate]);

  useEffect(() => {
    if (user?.role === 'platform_admin' || user?.role === 'platform_creator') fetchData();
  }, [user, fetchData]);

  const handleClear = () => {
    setStatusFilter('all');
    setEmailFilter('');
    setTenantIdFilter('');
  };

  if (user?.role !== 'platform_admin' && user?.role !== 'platform_creator') return null;

  return (
    <div
      className="min-h-screen bg-gray-50 p-6"
      data-testid="platform-admin-email-logs-page"
    >
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/platform-admin')}
              className="mb-2"
              data-testid="email-logs-back-btn"
            >
              <ArrowLeft className="w-4 h-4 mr-1" /> Back to Platform Admin
            </Button>
            <div className="flex items-center gap-3">
              <Mail className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">
                Email Deliverability
              </h1>
            </div>
            <p className="text-gray-600 mt-1">
              Tracks every email sent through SendGrid plus bounce / spam events
              from the SendGrid Event Webhook.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={fetchData}
            data-testid="email-logs-refresh-btn"
          >
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
        </div>

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <StatCard label="Total" value={summary.total} testId="email-summary-total" />
            <StatCard label="Delivered" value={summary.delivered} tone="good" testId="email-summary-delivered" />
            <StatCard label="Pending" value={summary.pending} tone="warn" testId="email-summary-pending" />
            <StatCard label="Bounced" value={summary.bounced} tone="bad" testId="email-summary-bounced" />
            <StatCard label="Complaints" value={summary.complaints} tone="bad" testId="email-summary-complaints" />
          </div>
        )}

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Filter className="w-4 h-4" /> Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Recipient email contains
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    value={emailFilter}
                    onChange={(e) => setEmailFilter(e.target.value)}
                    placeholder="e.g. @gmail.com"
                    className="pl-9"
                    data-testid="email-logs-email-filter"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Delivery status
                </label>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger data-testid="email-logs-status-filter">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statuses</SelectItem>
                    {STATUS_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Tenant ID
                </label>
                <Input
                  value={tenantIdFilter}
                  onChange={(e) => setTenantIdFilter(e.target.value)}
                  placeholder="tenant id"
                  data-testid="email-logs-tenant-filter"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button size="sm" onClick={fetchData} data-testid="email-logs-apply-btn">
                Apply
              </Button>
              <Button size="sm" variant="ghost" onClick={handleClear} data-testid="email-logs-clear-btn">
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Recent emails</span>
              <span className="text-sm font-normal text-gray-500">
                {loading ? 'Loading…' : `${entries.length} entries`}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
                <p className="mt-3 text-gray-500 text-sm">Loading…</p>
              </div>
            ) : entries.length === 0 ? (
              <div className="text-center py-12 text-gray-600">
                No emails match these filters.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="email-logs-table">
                  <thead className="border-b bg-gray-50">
                    <tr className="text-left text-gray-600">
                      <th className="px-3 py-2 font-medium">Sent</th>
                      <th className="px-3 py-2 font-medium">To</th>
                      <th className="px-3 py-2 font-medium">Subject</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                      <th className="px-3 py-2 font-medium">Tenant</th>
                      <th className="px-3 py-2 font-medium" />
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e) => {
                      const status = e.delivery_status || e.status || 'sent';
                      return (
                        <tr
                          key={e.id}
                          className="border-b hover:bg-gray-50"
                          data-testid={`email-logs-row-${e.id}`}
                        >
                          <td className="px-3 py-2 whitespace-nowrap text-gray-700">
                            {formatDateTime(e.sent_at)}
                          </td>
                          <td className="px-3 py-2 text-gray-900">{e.to_email}</td>
                          <td className="px-3 py-2 text-gray-700">
                            <div className="max-w-md truncate">{e.subject}</div>
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              variant="outline"
                              className={STATUS_COLORS[status] || 'bg-gray-100 text-gray-700'}
                            >
                              {status}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-gray-500 text-xs">
                            {e.tenant_id ? e.tenant_id.slice(0, 8) : '—'}
                          </td>
                          <td className="px-3 py-2 text-right">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => setSelected(e)}
                              data-testid={`email-logs-view-btn-${e.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detail dialog */}
      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Email details</DialogTitle>
          </DialogHeader>
          {selected && (
            <div className="space-y-3 text-sm" data-testid="email-logs-detail-dialog">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-xs text-gray-500">Sent</div>
                  <div>{formatDateTime(selected.sent_at)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Status</div>
                  <Badge
                    variant="outline"
                    className={STATUS_COLORS[selected.delivery_status || selected.status] || 'bg-gray-100 text-gray-700'}
                  >
                    {selected.delivery_status || selected.status}
                  </Badge>
                </div>
                <div>
                  <div className="text-xs text-gray-500">To</div>
                  <div>{selected.to_email}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Tenant</div>
                  <div className="font-mono text-xs">{selected.tenant_id || '—'}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-gray-500">Subject</div>
                  <div>{selected.subject}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-gray-500">SendGrid Message ID</div>
                  <div className="font-mono text-xs break-all">
                    {selected.sg_message_id || 'Not captured'}
                  </div>
                </div>
                {selected.error && (
                  <div className="col-span-2">
                    <div className="text-xs text-gray-500">Error</div>
                    <pre className="bg-red-50 border border-red-200 text-red-900 rounded p-2 text-xs whitespace-pre-wrap">
                      {selected.error}
                    </pre>
                  </div>
                )}
              </div>
              {selected.events && selected.events.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">SendGrid events</div>
                  <div className="space-y-1">
                    {selected.events.map((ev, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-xs bg-gray-50 border rounded p-2"
                      >
                        <span className="font-semibold text-gray-700">
                          {ev.event}
                        </span>
                        {ev.reason && (
                          <span className="text-red-700">{ev.reason}</span>
                        )}
                        <span className="ml-auto text-gray-500">
                          {formatDateTime(ev.received_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
