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
  ScrollText,
  Search,
  RefreshCw,
  Filter,
  Eye,
  ShieldCheck,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_COLORS = {
  impersonation: 'bg-amber-100 text-amber-900 border-amber-300',
  onboarding: 'bg-blue-100 text-blue-900 border-blue-300',
  tenant: 'bg-purple-100 text-purple-900 border-purple-300',
  billing: 'bg-emerald-100 text-emerald-900 border-emerald-300',
  security: 'bg-red-100 text-red-900 border-red-300',
  other: 'bg-gray-100 text-gray-700 border-gray-300',
};

function formatDateTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function PlatformAdminAuditLog() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [actorEmail, setActorEmail] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [tenantIdFilter, setTenantIdFilter] = useState('');
  const [selectedEntry, setSelectedEntry] = useState(null);

  // Redirect if not platform admin
  useEffect(() => {
    if (user && user.role !== 'platform_admin' && user.role !== 'platform_creator') {
      toast.error('Access denied: Platform Admin privileges required');
      navigate('/');
    }
  }, [user, navigate]);

  const fetchActions = useCallback(async () => {
    try {
      const token = getAuthToken();
      if (!token) return;
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/audit-log/actions`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) return;
      const data = await response.json();
      setActions(data.actions || []);
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to fetch audit actions', err);
    }
  }, []);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        navigate('/login');
        return;
      }
      const params = new URLSearchParams();
      params.set('limit', '300');
      if (actionFilter && actionFilter !== 'all') params.set('action', actionFilter);
      if (categoryFilter && categoryFilter !== 'all') params.set('action_category', categoryFilter);
      if (actorEmail.trim()) params.set('actor_email', actorEmail.trim());
      if (tenantIdFilter.trim()) params.set('tenant_id', tenantIdFilter.trim());

      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/audit-log?${params.toString()}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) {
        throw new Error('Failed to load audit log');
      }
      const data = await response.json();
      setEntries(data.entries || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load audit log');
    } finally {
      setLoading(false);
    }
  }, [actionFilter, categoryFilter, actorEmail, tenantIdFilter, navigate]);

  useEffect(() => {
    if (user?.role === 'platform_admin' || user?.role === 'platform_creator') {
      fetchActions();
      fetchEntries();
    }
  }, [user, fetchActions, fetchEntries]);

  const handleClearFilters = () => {
    setActionFilter('all');
    setCategoryFilter('all');
    setActorEmail('');
    setTenantIdFilter('');
  };

  if (user?.role !== 'platform_admin' && user?.role !== 'platform_creator') return null;

  return (
    <div className="min-h-screen bg-gray-50 p-6" data-testid="platform-admin-audit-log-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/platform-admin')}
              data-testid="audit-log-back-btn"
              className="mb-2"
            >
              <ArrowLeft className="w-4 h-4 mr-1" />
              Back to Platform Admin
            </Button>
            <div className="flex items-center gap-3">
              <ScrollText className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Admin Audit Log</h1>
            </div>
            <p className="text-gray-600 mt-1">
              Permanent record of every privileged Platform Admin action.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={fetchEntries}
            data-testid="audit-log-refresh-btn"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Filter className="w-4 h-4" /> Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Actor email contains
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    value={actorEmail}
                    onChange={(e) => setActorEmail(e.target.value)}
                    placeholder="admin@..."
                    className="pl-9"
                    data-testid="audit-log-actor-email-filter"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Category
                </label>
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger data-testid="audit-log-category-filter">
                    <SelectValue placeholder="All categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All categories</SelectItem>
                    {categories.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700 block mb-1">
                  Action
                </label>
                <Select value={actionFilter} onValueChange={setActionFilter}>
                  <SelectTrigger data-testid="audit-log-action-filter">
                    <SelectValue placeholder="All actions" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All actions</SelectItem>
                    {actions.map((a) => (
                      <SelectItem key={a} value={a}>
                        {a}
                      </SelectItem>
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
                  data-testid="audit-log-tenant-id-filter"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button
                size="sm"
                onClick={fetchEntries}
                data-testid="audit-log-apply-filters-btn"
              >
                Apply
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleClearFilters}
                data-testid="audit-log-clear-filters-btn"
              >
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Entries */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Recent Activity</span>
              <span className="text-sm font-normal text-gray-500">
                {loading ? 'Loading…' : `${entries.length} entries`}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
                <p className="mt-3 text-gray-500 text-sm">Loading audit log…</p>
              </div>
            ) : entries.length === 0 ? (
              <div className="text-center py-12">
                <ShieldCheck className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No audit entries match these filters.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm" data-testid="audit-log-table">
                  <thead className="border-b bg-gray-50">
                    <tr className="text-left text-gray-600">
                      <th className="px-3 py-2 font-medium">When</th>
                      <th className="px-3 py-2 font-medium">Actor</th>
                      <th className="px-3 py-2 font-medium">Action</th>
                      <th className="px-3 py-2 font-medium">Target</th>
                      <th className="px-3 py-2 font-medium">Tenant</th>
                      <th className="px-3 py-2 font-medium">IP</th>
                      <th className="px-3 py-2 font-medium" />
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((e) => (
                      <tr
                        key={e.id}
                        className="border-b hover:bg-gray-50"
                        data-testid={`audit-log-row-${e.id}`}
                      >
                        <td className="px-3 py-2 text-gray-700 whitespace-nowrap">
                          {formatDateTime(e.created_at)}
                        </td>
                        <td className="px-3 py-2 text-gray-700">
                          <div className="font-medium">{e.actor_email || '—'}</div>
                          <div className="text-xs text-gray-500">{e.actor_role}</div>
                        </td>
                        <td className="px-3 py-2">
                          <Badge
                            variant="outline"
                            className={
                              CATEGORY_COLORS[e.action_category] ||
                              CATEGORY_COLORS.other
                            }
                          >
                            {e.action}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-gray-700">
                          <div className="font-medium">{e.target_label || '—'}</div>
                          <div className="text-xs text-gray-500">{e.target_type}</div>
                        </td>
                        <td className="px-3 py-2 text-gray-700">
                          {e.tenant_name || (e.tenant_id ? e.tenant_id.slice(0, 8) : '—')}
                        </td>
                        <td className="px-3 py-2 text-gray-500 text-xs">
                          {e.ip_address || '—'}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setSelectedEntry(e)}
                            data-testid={`audit-log-view-btn-${e.id}`}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Entry Detail Dialog */}
      <Dialog open={!!selectedEntry} onOpenChange={(o) => !o && setSelectedEntry(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit Entry Details</DialogTitle>
          </DialogHeader>
          {selectedEntry && (
            <div className="space-y-3 text-sm" data-testid="audit-log-detail-dialog">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-xs text-gray-500">When</div>
                  <div className="font-medium">{formatDateTime(selectedEntry.created_at)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Status</div>
                  <div className="font-medium capitalize">{selectedEntry.status || 'success'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Actor</div>
                  <div className="font-medium">{selectedEntry.actor_email}</div>
                  <div className="text-xs text-gray-500">{selectedEntry.actor_role}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Action</div>
                  <div className="font-medium">{selectedEntry.action}</div>
                  <div className="text-xs text-gray-500">{selectedEntry.action_category}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Target</div>
                  <div className="font-medium">{selectedEntry.target_label || '—'}</div>
                  <div className="text-xs text-gray-500">
                    {selectedEntry.target_type} · {selectedEntry.target_id || '—'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Tenant</div>
                  <div className="font-medium">{selectedEntry.tenant_name || '—'}</div>
                  <div className="text-xs text-gray-500">{selectedEntry.tenant_id || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">IP</div>
                  <div className="font-medium">{selectedEntry.ip_address || '—'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">User Agent</div>
                  <div className="text-xs text-gray-700 break-all">
                    {selectedEntry.user_agent || '—'}
                  </div>
                </div>
              </div>
              {selectedEntry.summary && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Summary</div>
                  <div className="bg-gray-50 border rounded p-3 text-gray-800">
                    {selectedEntry.summary}
                  </div>
                </div>
              )}
              {selectedEntry.metadata && Object.keys(selectedEntry.metadata).length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Metadata</div>
                  <pre className="bg-gray-900 text-gray-100 rounded p-3 text-xs overflow-x-auto">
                    {JSON.stringify(selectedEntry.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
