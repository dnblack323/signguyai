import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import OnboardingChecklistTab from '../components/OnboardingChecklistTab';
import {
  ArrowLeft,
  Building2,
  Mail,
  Phone,
  Globe,
  MapPin,
  Users,
  LogIn,
  Shield,
  Calendar,
  ClipboardCheck,
  Ban,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  DollarSign,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken, setAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PlatformAdminTenantDetail() {
  const { tenantId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState(null);
  const [users, setUsers] = useState([]);
  const [emailSummary, setEmailSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState(false);
  const [promoting, setPromoting] = useState(null); // userId currently being promoted
  const [showSuspendDialog, setShowSuspendDialog] = useState(false);
  const [showReactivateDialog, setShowReactivateDialog] = useState(false);
  const [showMarkPaidDialog, setShowMarkPaidDialog] = useState(false);
  const [showThresholdDialog, setShowThresholdDialog] = useState(false);
  const [suspensionReason, setSuspensionReason] = useState('');
  const [reactivationNote, setReactivationNote] = useState('');
  const [markPaidNote, setMarkPaidNote] = useState('');
  const [thresholdValue, setThresholdValue] = useState('');
  const [notifyOwnerOnReactivate, setNotifyOwnerOnReactivate] = useState(true);
  const [suspending, setSuspending] = useState(false);
  const [reactivating, setReactivating] = useState(false);
  const [markingPaid, setMarkingPaid] = useState(false);
  const [savingThreshold, setSavingThreshold] = useState(false);

  // Redirect if not platform admin
  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied: Platform Admin privileges required');
      navigate('/');
    }
  }, [user, navigate]);

  // Fetch tenant details
  useEffect(() => {
    if (user?.role === 'platform_admin' && tenantId) {
      fetchTenantDetail();
    }
  }, [user, tenantId]);

  const fetchTenantDetail = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        navigate('/login');
        return;
      }
      
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch tenant details');
      }

      const data = await response.json();
      setTenant(data.tenant);
      setUsers(data.users);

      // Best-effort email deliverability summary for this tenant
      try {
        const sumRes = await fetch(
          `${BACKEND_URL}/api/platform-admin/email-logs/summary?tenant_id=${tenantId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (sumRes.ok) {
          const sum = await sumRes.json();
          setEmailSummary(sum);
        }
      } catch (e) {
        /* non-fatal */
      }
    } catch (error) {
      console.error('Error fetching tenant details:', error);
      toast.error('Failed to load tenant details');
    } finally {
      setLoading(false);
    }
  };

  const handleImpersonate = async (userId) => {
    if (!confirm('Are you sure you want to impersonate this user?')) {
      return;
    }
    setImpersonating(true);
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        return;
      }
      
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/impersonate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ target_user_id: userId }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to start impersonation');
      }

      const data = await response.json();

      // Store the original platform admin token
      localStorage.setItem('platform_admin_token', token);
      localStorage.setItem('impersonation_active', 'true');
      
      // Store the new impersonation token using authStorage
      setAuthToken(data.access_token, false);

      toast.success(
        `Now viewing as ${data.target_user.full_name} (${data.tenant.name})`
      );

      // Redirect to main dashboard
      window.location.href = '/';
    } catch (error) {
      console.error('Error starting impersonation:', error);
      toast.error('Failed to start impersonation');
      setImpersonating(false);
    }
  };

  // Promote a user out of this tenant into their own brand-new tenant.
  // Used when someone signed up via an invite link by mistake but should
  // have been their own tenant (e.g. a separate shop owner who clicked
  // an invite). NO order / customer / invoice data moves — only the user's
  // identity record. They keep their email + password.
  const handlePromoteToTenant = async (u) => {
    const newTenantName = prompt(
      `Create a new tenant for ${u.full_name || u.email}?\n\nEnter the tenant (company) name:`,
      u.full_name ? `${u.full_name}'s Shop` : ''
    );
    if (!newTenantName || !newTenantName.trim()) return;
    if (!confirm(
      `This will:\n` +
      `  • Create a new tenant called "${newTenantName.trim()}"\n` +
      `  • Move ${u.email} into the new tenant as its owner\n` +
      `  • NOT touch any orders, customers, invoices, or other data\n` +
      `     (those stay on this tenant — ${u.full_name || u.email} is starting fresh)\n\n` +
      `Continue?`
    )) return;

    setPromoting(u.id);
    try {
      const token = getAuthToken();
      const res = await fetch(`${BACKEND_URL}/api/platform-admin/users/${u.id}/promote-to-tenant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ new_tenant_name: newTenantName.trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Promote failed (HTTP ${res.status})`);
      }
      const data = await res.json();
      toast.success(`${u.email} is now the owner of "${data.tenant.name}"`);
      // Refresh this tenant page (the user just disappeared from our user list)
      fetchTenantDetails();
    } catch (error) {
      console.error('Error promoting user:', error);
      toast.error(error.message || 'Failed to promote user');
    } finally {
      setPromoting(null);
    }
  };

  const handleSuspend = async () => {
    if (!suspensionReason.trim()) {
      toast.error('Please provide a reason');
      return;
    }
    setSuspending(true);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/suspend`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ reason: suspensionReason.trim() }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          (data?.detail && (typeof data.detail === 'string' ? data.detail : data.detail.message)) ||
            'Failed to suspend tenant'
        );
      }
      toast.success('Tenant suspended');
      if (data.tenant) setTenant(data.tenant);
      setShowSuspendDialog(false);
      setSuspensionReason('');
    } catch (err) {
      console.error('Suspend error:', err);
      toast.error(err.message || 'Failed to suspend tenant');
    } finally {
      setSuspending(false);
    }
  };

  const handleReactivate = async () => {
    setReactivating(true);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/reactivate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            note: reactivationNote.trim() || null,
            notify_owner: notifyOwnerOnReactivate,
          }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          (data?.detail && (typeof data.detail === 'string' ? data.detail : data.detail.message)) ||
            'Failed to reactivate tenant'
        );
      }
      const emailMsg = notifyOwnerOnReactivate
        ? (data?.email_status?.success
            ? ' (welcome-back email sent)'
            : data?.email_status?.error
              ? ' (email not sent — see audit metadata)'
              : '')
        : '';
      toast.success(`Tenant reactivated${emailMsg}`);
      if (data.tenant) setTenant(data.tenant);
      setShowReactivateDialog(false);
      setReactivationNote('');
      setNotifyOwnerOnReactivate(true);
    } catch (err) {
      console.error('Reactivate error:', err);
      toast.error(err.message || 'Failed to reactivate tenant');
    } finally {
      setReactivating(false);
    }
  };

  const handleMarkPaid = async () => {
    setMarkingPaid(true);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/mark-paid`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ note: markPaidNote.trim() || null }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          (data?.detail && (typeof data.detail === 'string' ? data.detail : data.detail.message)) ||
            'Failed to mark tenant as paid'
        );
      }
      toast.success(
        data.auto_reactivated
          ? 'Marked as paid — tenant auto-reactivated'
          : 'Marked as paid — counters reset'
      );
      if (data.tenant) setTenant(data.tenant);
      setShowMarkPaidDialog(false);
      setMarkPaidNote('');
    } catch (err) {
      console.error('Mark paid error:', err);
      toast.error(err.message || 'Failed to mark tenant as paid');
    } finally {
      setMarkingPaid(false);
    }
  };

  const handleSaveThreshold = async () => {
    setSavingThreshold(true);
    try {
      const token = getAuthToken();
      const trimmed = thresholdValue.trim();
      const parsed = trimmed === '' ? null : parseInt(trimmed, 10);
      if (parsed !== null && (Number.isNaN(parsed) || parsed < 1)) {
        toast.error('Threshold must be a positive integer (or empty to clear)');
        setSavingThreshold(false);
        return;
      }
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/dunning-threshold`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ threshold: parsed }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          (data?.detail && (typeof data.detail === 'string' ? data.detail : data.detail.message)) ||
            'Failed to update threshold'
        );
      }
      toast.success(
        parsed === null
          ? 'Threshold cleared — using global default'
          : `Threshold set to ${parsed}`
      );
      if (data.tenant) setTenant(data.tenant);
      setShowThresholdDialog(false);
    } catch (err) {
      console.error('Threshold save error:', err);
      toast.error(err.message || 'Failed to update threshold');
    } finally {
      setSavingThreshold(false);
    }
  };

  if (user?.role !== 'platform_admin') {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading tenant details...</p>
        </div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Tenant not found</p>
          <Button
            onClick={() => navigate('/platform-admin')}
            className="mt-4"
          >
            Back to Platform Admin
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/platform-admin')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tenant List
          </Button>
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <div>
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-3xl font-bold text-gray-900">{tenant.name}</h1>
                  {tenant.is_active === false && (
                    <Badge
                      variant="outline"
                      className="bg-red-100 text-red-900 border-red-300"
                      data-testid="tenant-suspended-badge"
                    >
                      Suspended
                    </Badge>
                  )}
                </div>
                <p className="text-gray-600">Tenant Details & Management</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  const owner = users.find((u) => u.role === 'owner' && u.is_active !== false)
                    || users.find((u) => u.email === tenant.owner_email)
                    || users.find((u) => u.is_active !== false);
                  if (!owner) {
                    toast.error('No active owner found for this tenant');
                    return;
                  }
                  handleImpersonate(owner.id);
                }}
                disabled={impersonating || tenant.is_active === false || users.length === 0}
                data-testid="tenant-impersonate-owner-btn"
              >
                <LogIn className="w-4 h-4 mr-2" />
                {impersonating ? 'Starting...' : 'Impersonate Tenant Owner'}
              </Button>
              {tenant.is_active === false ? (
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => setShowReactivateDialog(true)}
                  data-testid="tenant-reactivate-btn"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Reactivate Tenant
                </Button>
              ) : (
                <Button
                  variant="destructive"
                  onClick={() => setShowSuspendDialog(true)}
                  data-testid="tenant-suspend-btn"
                >
                  <Ban className="w-4 h-4 mr-2" />
                  Suspend Tenant
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Suspension banner */}
        {tenant.is_active === false && (
          <div
            className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 flex items-start gap-3"
            data-testid="tenant-suspended-banner"
          >
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <div className="flex-1">
              <div className="font-semibold text-red-900">This tenant is suspended</div>
              <div className="text-sm text-red-800 mt-1">
                <span className="font-medium">Reason:</span>{' '}
                {tenant.suspension_reason || '—'}
              </div>
              <div className="text-xs text-red-700 mt-1">
                Suspended {tenant.suspended_at ? new Date(tenant.suspended_at).toLocaleString() : '—'}
                {tenant.suspended_by_email && ` by ${tenant.suspended_by_email}`}
              </div>
            </div>
          </div>
        )}

        {/* Billing & Dunning card */}
        {(tenant.payment_failed_count > 0 ||
          tenant.auto_suspended_for_payment ||
          tenant.last_payment_succeeded_at ||
          tenant.dunning_failure_threshold ||
          tenant.is_founder) && (
          <Card
            className={`mb-6 ${
              tenant.auto_suspended_for_payment
                ? 'border-red-200'
                : tenant.grace_period_until
                ? 'border-amber-300'
                : tenant.payment_failed_count > 0
                ? 'border-amber-200'
                : 'border-emerald-200'
            }`}
            data-testid="tenant-billing-card"
          >
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base flex-wrap">
                <CreditCard className="w-4 h-4" /> Billing & Dunning
                {tenant.auto_suspended_for_payment && (
                  <Badge
                    variant="outline"
                    className="bg-red-100 text-red-900 border-red-300"
                    data-testid="tenant-auto-suspended-badge"
                  >
                    Auto-suspended for non-payment
                  </Badge>
                )}
                {tenant.is_founder && (
                  <Badge
                    variant="outline"
                    className="bg-purple-100 text-purple-900 border-purple-300"
                    data-testid="tenant-founder-badge"
                  >
                    Founder · 24h grace applies
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">
                    Failed attempts
                  </div>
                  <div
                    className={`text-2xl font-bold ${
                      tenant.payment_failed_count >= 3
                        ? 'text-red-600'
                        : tenant.payment_failed_count > 0
                        ? 'text-amber-600'
                        : 'text-gray-900'
                    }`}
                    data-testid="tenant-failed-attempts-count"
                  >
                    {tenant.payment_failed_count || 0}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Threshold: <strong>{tenant.dunning_failure_threshold || 'default (3)'}</strong>
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">
                    Last failure
                  </div>
                  <div className="text-gray-900">
                    {tenant.last_payment_failure_at
                      ? new Date(tenant.last_payment_failure_at).toLocaleString()
                      : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">
                    Last success
                  </div>
                  <div className="text-gray-900">
                    {tenant.last_payment_succeeded_at
                      ? new Date(tenant.last_payment_succeeded_at).toLocaleString()
                      : '—'}
                  </div>
                </div>
                <div className="flex flex-col gap-2 items-stretch">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowMarkPaidDialog(true)}
                    data-testid="tenant-mark-paid-btn"
                  >
                    <DollarSign className="w-4 h-4 mr-1" />
                    Mark as Paid
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setThresholdValue(
                        tenant.dunning_failure_threshold
                          ? String(tenant.dunning_failure_threshold)
                          : ''
                      );
                      setShowThresholdDialog(true);
                    }}
                    data-testid="tenant-threshold-btn"
                  >
                    Set Threshold
                  </Button>
                </div>
              </div>
              {tenant.grace_period_until && (
                <p
                  className="text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded p-2 mt-3"
                  data-testid="tenant-grace-banner"
                >
                  <strong>In grace period:</strong> auto-suspend held until{' '}
                  {new Date(tenant.grace_period_until).toLocaleString()}.
                  Next failed payment after that time will suspend the tenant.
                </p>
              )}
              {tenant.payment_failed_count > 0 &&
                !tenant.auto_suspended_for_payment &&
                !tenant.grace_period_until && (
                  <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 mt-3">
                    <strong>Heads up:</strong>{' '}
                    {tenant.is_founder
                      ? 'Reaching the threshold will start a 24-hour grace window before suspension.'
                      : 'The next failed payment attempt at or above the threshold will auto-suspend this tenant.'}
                  </p>
                )}
            </CardContent>
          </Card>
        )}

        {/* Email Deliverability mini-tile */}
        {emailSummary && emailSummary.total > 0 && (
          <Card
            className={`mb-6 ${
              emailSummary.bounced + emailSummary.complaints > 0
                ? 'border-red-200'
                : 'border-emerald-200'
            }`}
            data-testid="tenant-email-deliverability-card"
          >
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Mail className="w-4 h-4" /> Email Deliverability (this tenant)
                {emailSummary.bounced + emailSummary.complaints > 0 && (
                  <Badge
                    variant="outline"
                    className="bg-red-100 text-red-900 border-red-300"
                  >
                    Issues detected
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-sm">
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">Total</div>
                  <div className="text-xl font-bold">{emailSummary.total}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">Delivered</div>
                  <div className="text-xl font-bold text-emerald-700">{emailSummary.delivered}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">Pending</div>
                  <div className="text-xl font-bold text-amber-700">{emailSummary.pending}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">Bounced</div>
                  <div className={`text-xl font-bold ${emailSummary.bounced > 0 ? 'text-red-700' : 'text-gray-400'}`}>
                    {emailSummary.bounced}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-gray-500">Complaints</div>
                  <div className={`text-xl font-bold ${emailSummary.complaints > 0 ? 'text-red-700' : 'text-gray-400'}`}>
                    {emailSummary.complaints}
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    navigate(`/platform-admin/email-logs?tenant=${tenantId}`)
                  }
                  data-testid="tenant-view-email-logs-btn"
                >
                  View detailed email logs →
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs for different sections */}
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview & Users</TabsTrigger>
            <TabsTrigger value="checklist">
              <ClipboardCheck className="w-4 h-4 mr-2" />
              Onboarding Checklist
            </TabsTrigger>
            <TabsTrigger value="notes">Notes</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6 mt-6">
            {/* Tenant Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Business Information</CardTitle>
              </CardHeader>
              <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <Building2 className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Business Name</p>
                  <p className="text-gray-900">{tenant.name}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Owner Email</p>
                  <p className="text-gray-900">{tenant.owner_email}</p>
                </div>
              </div>

              {tenant.phone && (
                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Phone</p>
                    <p className="text-gray-900">{tenant.phone}</p>
                  </div>
                </div>
              )}

              {tenant.website && (
                <div className="flex items-start gap-3">
                  <Globe className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Website</p>
                    <a
                      href={tenant.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {tenant.website}
                    </a>
                  </div>
                </div>
              )}

              {(tenant.address || tenant.city || tenant.state) && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Address</p>
                    <p className="text-gray-900">
                      {tenant.address && <>{tenant.address}<br /></>}
                      {tenant.city && tenant.state && `${tenant.city}, ${tenant.state}`}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Plan</p>
                  <p className="text-gray-900 capitalize">
                    {tenant.plan.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Created</p>
                  <p className="text-gray-900">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Users List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Users ({users.length})
            </CardTitle>
            <p className="text-xs text-gray-500 mt-1">
              To impersonate someone, use the "Impersonate Tenant Owner" button at the top. If a user listed here should actually have their own tenant (e.g. they signed up via an invite by mistake), click "Promote to Own Tenant" next to their name.
            </p>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No users found</p>
            ) : (
              <div className="space-y-2">
                {users.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{u.full_name}</h3>
                        <span
                          className={`text-xs px-2 py-1 rounded-full font-medium ${
                            u.role === 'owner'
                              ? 'bg-purple-100 text-purple-800'
                              : u.role === 'admin'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {u.role}
                        </span>
                        {!u.is_active && (
                          <span className="text-xs px-2 py-1 rounded-full font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{u.email}</p>
                    </div>
                    {/* Promote-to-own-tenant: only shown for non-owner users — the owner
                        IS this tenant, so promoting them would be a no-op. */}
                    {u.email !== tenant.owner_email && (
                      <Button
                        onClick={() => handlePromoteToTenant(u)}
                        disabled={promoting || !u.is_active}
                        variant="outline"
                        size="sm"
                        className="ml-4"
                        data-testid={`promote-user-${u.id}-btn`}
                      >
                        <Shield className="w-4 h-4 mr-2" />
                        {promoting === u.id ? 'Promoting…' : 'Promote to Own Tenant'}
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
          </TabsContent>

          {/* Onboarding Checklist Tab */}
          <TabsContent value="checklist" className="mt-6">
            <OnboardingChecklistTab tenantId={tenantId} />
          </TabsContent>

          {/* Notes Tab (placeholder) */}
          <TabsContent value="notes" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Internal Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">Notes feature coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Suspend Tenant Dialog */}
      <Dialog open={showSuspendDialog} onOpenChange={setShowSuspendDialog}>
        <DialogContent data-testid="tenant-suspend-dialog">
          <DialogHeader>
            <DialogTitle className="text-red-700 flex items-center gap-2">
              <Ban className="w-5 h-5" /> Suspend {tenant?.name}?
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <p className="text-gray-700">
              Suspending will <strong>immediately</strong> log out every user in this
              tenant and block new logins. Their data is preserved and can be
              restored at any time by reactivating.
            </p>
            <div>
              <label className="text-xs font-medium text-gray-700 block mb-1">
                Reason for suspension <span className="text-red-600">*</span>
              </label>
              <Textarea
                value={suspensionReason}
                onChange={(e) => setSuspensionReason(e.target.value)}
                placeholder="e.g., Failed payment - card declined 3x"
                rows={3}
                data-testid="tenant-suspend-reason-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                The reason is logged to the audit trail and shown to the user on the
                "Account Suspended" screen.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowSuspendDialog(false)}
              disabled={suspending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleSuspend}
              disabled={suspending || !suspensionReason.trim()}
              data-testid="tenant-suspend-confirm-btn"
            >
              {suspending ? 'Suspending…' : 'Suspend Tenant'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reactivate Tenant Dialog */}
      <Dialog open={showReactivateDialog} onOpenChange={setShowReactivateDialog}>
        <DialogContent data-testid="tenant-reactivate-dialog">
          <DialogHeader>
            <DialogTitle className="text-emerald-700 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5" /> Reactivate {tenant?.name}?
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <p className="text-gray-700">
              Reactivating will restore login access for all users in this tenant
              and clear the suspension reason.
            </p>
            <div>
              <label className="text-xs font-medium text-gray-700 block mb-1">
                Note (optional)
              </label>
              <Textarea
                value={reactivationNote}
                onChange={(e) => setReactivationNote(e.target.value)}
                placeholder="e.g., Customer paid invoice 5012"
                rows={2}
                data-testid="tenant-reactivate-note-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                The note is recorded on the audit trail entry for this action.
              </p>
            </div>
            <label
              className="flex items-start gap-3 p-3 border rounded-md bg-emerald-50/40 border-emerald-100 cursor-pointer"
              htmlFor="notify-owner-checkbox"
            >
              <input
                id="notify-owner-checkbox"
                type="checkbox"
                checked={notifyOwnerOnReactivate}
                onChange={(e) => setNotifyOwnerOnReactivate(e.target.checked)}
                className="mt-1"
                data-testid="tenant-reactivate-notify-owner-checkbox"
              />
              <span className="flex-1">
                <span className="font-medium text-gray-900 block">
                  Send the owner a "Welcome back" email
                </span>
                <span className="text-xs text-gray-600">
                  Optional. If your note above is filled in, it will be included
                  in the email so the owner knows why their account is active again.
                </span>
              </span>
            </label>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowReactivateDialog(false)}
              disabled={reactivating}
            >
              Cancel
            </Button>
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={handleReactivate}
              disabled={reactivating}
              data-testid="tenant-reactivate-confirm-btn"
            >
              {reactivating ? 'Reactivating…' : 'Reactivate Tenant'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Mark as Paid Dialog */}
      <Dialog open={showMarkPaidDialog} onOpenChange={setShowMarkPaidDialog}>
        <DialogContent data-testid="tenant-mark-paid-dialog">
          <DialogHeader>
            <DialogTitle className="text-emerald-700 flex items-center gap-2">
              <DollarSign className="w-5 h-5" /> Mark {tenant?.name} as paid?
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <p className="text-gray-700">
              This is a manual override for cases Stripe can't tell us about
              (NET-60 invoices, wire transfers, manually cleared chargebacks, etc.).
            </p>
            <ul className="text-xs text-gray-600 list-disc pl-5 space-y-1">
              <li>Resets the failed-payment counter to 0.</li>
              <li>
                If the tenant was auto-suspended for non-payment, it will be
                reactivated immediately and the owner will receive a "welcome back"
                email.
              </li>
              <li>The action is recorded on the audit log.</li>
            </ul>
            <div>
              <label className="text-xs font-medium text-gray-700 block mb-1">
                Note (optional)
              </label>
              <Textarea
                value={markPaidNote}
                onChange={(e) => setMarkPaidNote(e.target.value)}
                placeholder="e.g., Wire transfer received - invoice 5012"
                rows={2}
                data-testid="tenant-mark-paid-note-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowMarkPaidDialog(false)}
              disabled={markingPaid}
            >
              Cancel
            </Button>
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={handleMarkPaid}
              disabled={markingPaid}
              data-testid="tenant-mark-paid-confirm-btn"
            >
              {markingPaid ? 'Saving…' : 'Mark as Paid'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Set Dunning Threshold Dialog */}
      <Dialog open={showThresholdDialog} onOpenChange={setShowThresholdDialog}>
        <DialogContent data-testid="tenant-threshold-dialog">
          <DialogHeader>
            <DialogTitle>Set dunning threshold</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <p className="text-gray-700">
              Override how many consecutive failed payments are allowed before
              this tenant is auto-suspended. Leave blank to use the global default.
            </p>
            <div>
              <label className="text-xs font-medium text-gray-700 block mb-1">
                Threshold (positive integer or empty)
              </label>
              <input
                type="number"
                min={1}
                value={thresholdValue}
                onChange={(e) => setThresholdValue(e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm"
                placeholder="e.g., 5"
                data-testid="tenant-threshold-input"
              />
              <p className="text-xs text-gray-500 mt-1">
                Tip: enterprise / NET-60 customers often need 5–7 attempts. Founders
                additionally get a 24-hour grace window after the threshold is hit.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              onClick={() => setShowThresholdDialog(false)}
              disabled={savingThreshold}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSaveThreshold}
              disabled={savingThreshold}
              data-testid="tenant-threshold-save-btn"
            >
              {savingThreshold ? 'Saving…' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
