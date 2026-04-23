import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  CreditCard, Check, X, ExternalLink, AlertCircle, 
  Loader2, Shield, DollarSign, TrendingUp, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PaymentSettings() {
  const [loading, setLoading] = useState(true);
  const [connectStatus, setConnectStatus] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    const initialize = async () => {
      const status = await fetchConnectStatus();
      if (status?.connected) {
        await fetchTenantDashboard();
      }

      // Check for return from Stripe onboarding
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('stripe_return') === 'true') {
        toast.success('Stripe account setup updated');
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    };

    initialize();
  }, []);

  const fetchConnectStatus = async () => {
    try {
      const token = getAuthToken();
      const response = await axios.get(`${API_URL}/api/stripe-connect/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConnectStatus(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch Stripe status:', err);
      toast.error('Failed to load payment settings');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const fetchTenantDashboard = async () => {
    setDashboardLoading(true);
    try {
      const token = getAuthToken();
      const response = await axios.get(`${API_URL}/api/stripe-connect/tenant-dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch Stripe dashboard data:', err);
      toast.error('Failed to load Stripe operations dashboard');
      return null;
    } finally {
      setDashboardLoading(false);
    }
  };

  const handleRefreshAll = async () => {
    const status = await fetchConnectStatus();
    if (status?.connected) {
      await fetchTenantDashboard();
    } else {
      setDashboardData(null);
    }
    toast.success('Stripe status refreshed');
  };

  const handleConnectStripe = async () => {
    setConnecting(true);
    try {
      const token = getAuthToken();
      const currentUrl = window.location.origin;
      
      const response = await axios.post(
        `${API_URL}/api/stripe-connect/create-account`,
        {
          return_url: `${currentUrl}/admin/payments?stripe_return=true`,
          refresh_url: `${currentUrl}/admin/payments?stripe_refresh=true`
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Redirect to Stripe onboarding
      window.location.href = response.data.url;
    } catch (err) {
      console.error('Failed to create Stripe account:', err);
      const detail = err.response?.data?.detail || '';
      if (detail.includes('signed up for Connect')) {
        toast.error('Stripe Connect is not enabled yet. The platform admin needs to enable Stripe Connect at dashboard.stripe.com/connect first.', { duration: 8000 });
      } else {
        toast.error(detail || 'Failed to start Stripe setup');
      }
      setConnecting(false);
    }
  };

  const handleRefreshOnboarding = async () => {
    setConnecting(true);
    try {
      const token = getAuthToken();
      const currentUrl = window.location.origin;
      
      const response = await axios.post(
        `${API_URL}/api/stripe-connect/refresh-link`,
        {
          return_url: `${currentUrl}/admin/payments?stripe_return=true`,
          refresh_url: `${currentUrl}/admin/payments?stripe_refresh=true`
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      window.location.href = response.data.url;
    } catch (err) {
      console.error('Failed to refresh onboarding:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail || '';
      if (status === 409) {
        // Stale / wrong-mode account was auto-scrubbed on the backend — refresh
        // the status so the UI flips to "Connect Stripe" and the tenant can
        // start fresh.
        toast.error(
          detail || 'Your previous Stripe link is no longer valid. Please reconnect.',
          { duration: 8000 }
        );
        await fetchConnectStatus();
      } else {
        toast.error(detail || 'Failed to continue setup');
      }
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Are you sure you want to disconnect your Stripe account? You will not be able to accept payments until you reconnect.')) {
      return;
    }
    
    try {
      const token = getAuthToken();
      await axios.delete(`${API_URL}/api/stripe-connect/disconnect`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Stripe account disconnected');
      fetchConnectStatus();
    } catch (err) {
      toast.error('Failed to disconnect');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="payment-settings">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Payment Settings</h1>
        <p className="text-gray-500">
          Connect your Stripe account to accept payments for invoices and webstore orders
        </p>
      </div>

      {/* Platform Fee Info */}
      <Alert className="border-primary/20 bg-primary/5">
        <DollarSign className="h-4 w-4 text-primary" />
        <AlertDescription>
          <strong>Platform fee: 2.2% + $0.20</strong> per transaction.
          <span className="text-gray-500 ml-2">
            Founders Edition — locked-in rate
          </span>
        </AlertDescription>
      </Alert>

      <Alert className={connectStatus?.stripe_mode === 'live' ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'} data-testid="stripe-mode-alert">
        <AlertCircle className={`h-4 w-4 ${connectStatus?.stripe_mode === 'live' ? 'text-green-600' : 'text-amber-600'}`} />
        <AlertDescription className={connectStatus?.stripe_mode === 'live' ? 'text-green-800' : 'text-amber-800'}>
          <strong>Platform Stripe mode:</strong> {connectStatus?.stripe_mode === 'live' ? 'Live payments' : 'Test payments'}.
          {connectStatus?.stripe_mode === 'test'
            ? ' Test mode means Stripe uses test cards and test data only — no real money moves until live mode is enabled.'
            : ' Live mode means real customer charges and payouts can be processed once onboarding is complete.'}
        </AlertDescription>
      </Alert>

      {/* Connection Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${connectStatus?.connected ? 'bg-green-500/10' : 'bg-gray-50'}`}>
                <CreditCard className={`h-5 w-5 ${connectStatus?.connected ? 'text-green-500' : 'text-gray-500'}`} />
              </div>
              <div>
                <CardTitle className="text-lg">Stripe Account</CardTitle>
                <CardDescription>
                  {connectStatus?.connected 
                    ? 'Your Stripe account is connected' 
                    : 'Connect Stripe to accept payments'}
                </CardDescription>
              </div>
            </div>
            <Badge 
              variant={connectStatus?.connected ? 'default' : 'secondary'}
              className={connectStatus?.connected ? 'bg-green-500' : ''}
            >
              {connectStatus?.connected ? 'Connected' : 'Not Connected'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {connectStatus?.connected ? (
            <>
              {/* Status indicators */}
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                  {connectStatus.charges_enabled ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm">
                    Payments {connectStatus.charges_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-lg bg-gray-50">
                  {connectStatus.payouts_enabled ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm">
                    Payouts {connectStatus.payouts_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>

              {/* Warning if onboarding incomplete */}
              {!connectStatus.onboarding_complete && (
                <Alert variant="warning" className="border-amber-500/50 bg-amber-500/10">
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                  <AlertDescription className="text-amber-700">
                    Your Stripe account setup is incomplete. Complete the setup to start accepting payments.
                  </AlertDescription>
                </Alert>
              )}

              {connectStatus.mode_mismatch && (
                <Alert className="border-amber-200 bg-amber-50" data-testid="stripe-mode-mismatch-alert">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800">
                    This connected Stripe account is in <strong>{connectStatus.account_mode}</strong> mode while the platform is using <strong>{connectStatus.stripe_mode}</strong> mode.
                    Reconnect Stripe to create the correct onboarding session for this tenant.
                  </AlertDescription>
                </Alert>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50" data-testid="stripe-platform-mode-card">
                  <span className="text-sm text-gray-600">Platform Mode</span>
                  <Badge variant="outline">{connectStatus.stripe_mode}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50" data-testid="stripe-account-mode-card">
                  <span className="text-sm text-gray-600">Connected Account</span>
                  <Badge variant="outline">{connectStatus.account_mode || 'unknown'}</Badge>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button variant="outline" onClick={handleRefreshAll} data-testid="stripe-refresh-all-button">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
                {connectStatus.mode_mismatch && (
                  <Button onClick={handleConnectStripe} disabled={connecting} data-testid="reconnect-stripe-live-button">
                    {connecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Reconnect Stripe
                  </Button>
                )}
                {!connectStatus.onboarding_complete && (
                  <Button onClick={handleRefreshOnboarding} disabled={connecting}>
                    {connecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Complete Setup
                  </Button>
                )}
                <Button variant="outline" asChild>
                  <a href="https://dashboard.stripe.com" target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Open Stripe Dashboard
                  </a>
                </Button>
                <Button variant="ghost" className="text-destructive" onClick={handleDisconnect}>
                  Disconnect
                </Button>
              </div>
            </>
          ) : (
            <>
              {/* Benefits of connecting */}
              <div className="grid sm:grid-cols-3 gap-4 py-4">
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-gray-50">
                  <CreditCard className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Accept Cards</h4>
                  <p className="text-xs text-gray-500">Credit & debit cards</p>
                </div>
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-gray-50">
                  <Shield className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Secure Payments</h4>
                  <p className="text-xs text-gray-500">PCI compliant</p>
                </div>
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-gray-50">
                  <TrendingUp className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Fast Payouts</h4>
                  <p className="text-xs text-gray-500">Direct to your bank</p>
                </div>
              </div>

              <Button 
                size="lg" 
                onClick={handleConnectStripe} 
                disabled={connecting}
                className="w-full sm:w-auto"
                data-testid="connect-stripe-btn"
              >
                {connecting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <CreditCard className="mr-2 h-4 w-4" />
                Connect with Stripe
              </Button>

              <p className="text-xs text-gray-500 mt-3">
                Stripe Connect must be enabled on the platform's Stripe account first.
                If you see an error, visit{' '}
                <a href="https://dashboard.stripe.com/connect" target="_blank" rel="noopener noreferrer" className="text-violet-600 underline">
                  dashboard.stripe.com/connect
                </a>{' '}
                to enable it, then try again.
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {connectStatus?.connected && (
        <Card data-testid="stripe-tenant-operations-dashboard-card">
          <CardHeader>
            <CardTitle className="text-lg">Tenant Stripe Operations Dashboard</CardTitle>
            <CardDescription>
              Live reconciliation for payments, payouts, failures, disputes, and invoice sync.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {dashboardLoading ? (
              <div className="flex items-center gap-2 text-sm text-gray-500" data-testid="stripe-dashboard-loading-state">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading Stripe operations…
              </div>
            ) : (
              <>
                <div className="grid md:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg bg-gray-50" data-testid="stripe-summary-paid-total">
                    <p className="text-xs text-gray-500">Total Paid</p>
                    <p className="text-lg font-semibold">${dashboardData?.payments_summary?.paid_total?.toFixed?.(2) || '0.00'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-50" data-testid="stripe-summary-pending-total">
                    <p className="text-xs text-gray-500">Pending</p>
                    <p className="text-lg font-semibold">${dashboardData?.payments_summary?.pending_total?.toFixed?.(2) || '0.00'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-50" data-testid="stripe-summary-available-balance">
                    <p className="text-xs text-gray-500">Available Balance</p>
                    <p className="text-lg font-semibold">${dashboardData?.balances?.available_usd?.toFixed?.(2) || '0.00'}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-50" data-testid="stripe-summary-pending-balance">
                    <p className="text-xs text-gray-500">Pending Balance</p>
                    <p className="text-lg font-semibold">${dashboardData?.balances?.pending_usd?.toFixed?.(2) || '0.00'}</p>
                  </div>
                </div>

                <div className="grid lg:grid-cols-2 gap-4">
                  <div className="space-y-2" data-testid="stripe-recent-payments-table">
                    <h4 className="font-medium">Recent Payments</h4>
                    <div className="max-h-64 overflow-auto rounded-lg border">
                      {(dashboardData?.recent_payments || []).slice(0, 20).map((payment) => (
                        <div key={payment.session_id} className="grid grid-cols-4 gap-2 p-2 text-xs border-b">
                          <span className="font-mono">{payment.session_id?.slice(0, 10)}...</span>
                          <span>${Number(payment.amount || 0).toFixed(2)}</span>
                          <span className={payment.status === 'paid' ? 'text-green-600' : 'text-amber-600'}>{payment.status}</span>
                          <span>{payment.invoice_status || '-'}</span>
                        </div>
                      ))}
                      {(dashboardData?.recent_payments || []).length === 0 && (
                        <div className="p-3 text-sm text-gray-500">No payment records yet.</div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2" data-testid="stripe-recent-payouts-table">
                    <h4 className="font-medium">Recent Payouts</h4>
                    <div className="max-h-64 overflow-auto rounded-lg border">
                      {(dashboardData?.recent_payouts || []).slice(0, 20).map((payout) => (
                        <div key={payout.id} className="grid grid-cols-4 gap-2 p-2 text-xs border-b">
                          <span className="font-mono">{payout.id?.slice(0, 10)}...</span>
                          <span>${Number(payout.amount || 0).toFixed(2)}</span>
                          <span className={payout.status === 'paid' ? 'text-green-600' : 'text-amber-600'}>{payout.status}</span>
                          <span>{payout.arrival_date?.slice(0, 10) || '-'}</span>
                        </div>
                      ))}
                      {(dashboardData?.recent_payouts || []).length === 0 && (
                        <div className="p-3 text-sm text-gray-500">No payouts yet.</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid lg:grid-cols-2 gap-4">
                  <div className="space-y-2" data-testid="stripe-recent-failed-payments-table">
                    <h4 className="font-medium">Failed / Expired Payments</h4>
                    <div className="max-h-52 overflow-auto rounded-lg border">
                      {(dashboardData?.recent_failed_payments || []).slice(0, 20).map((payment) => (
                        <div key={payment.session_id} className="grid grid-cols-3 gap-2 p-2 text-xs border-b">
                          <span className="font-mono">{payment.session_id?.slice(0, 10)}...</span>
                          <span>${Number(payment.amount || 0).toFixed(2)}</span>
                          <span className="text-red-600">{payment.status}</span>
                        </div>
                      ))}
                      {(dashboardData?.recent_failed_payments || []).length === 0 && (
                        <div className="p-3 text-sm text-gray-500">No failed payments recorded.</div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2" data-testid="stripe-recent-disputes-table">
                    <h4 className="font-medium">Recent Disputes</h4>
                    <div className="max-h-52 overflow-auto rounded-lg border">
                      {(dashboardData?.recent_disputes || []).slice(0, 20).map((dispute) => (
                        <div key={dispute.id} className="grid grid-cols-3 gap-2 p-2 text-xs border-b">
                          <span className="font-mono">{dispute.id?.slice(0, 10)}...</span>
                          <span>${Number(dispute.amount || 0).toFixed(2)}</span>
                          <span className="text-red-600">{dispute.status}</span>
                        </div>
                      ))}
                      {(dashboardData?.recent_disputes || []).length === 0 && (
                        <div className="p-3 text-sm text-gray-500">No disputes found.</div>
                      )}
                    </div>
                  </div>
                </div>

                <div data-testid="stripe-recent-events-table">
                  <h4 className="font-medium mb-2">Recent Stripe Events</h4>
                  <div className="max-h-56 overflow-auto rounded-lg border">
                    {(dashboardData?.recent_events || []).slice(0, 30).map((evt, idx) => (
                      <div key={`${evt.created_at}-${idx}`} className="grid grid-cols-4 gap-2 p-2 text-xs border-b">
                        <span>{evt.event_type}</span>
                        <span className={evt.status === 'paid' ? 'text-green-600' : 'text-amber-600'}>{evt.status}</span>
                        <span>{evt.reference_id || '-'}</span>
                        <span>{evt.created_at?.slice(0, 19)?.replace('T', ' ') || '-'}</span>
                      </div>
                    ))}
                    {(dashboardData?.recent_events || []).length === 0 && (
                      <div className="p-3 text-sm text-gray-500">No events captured yet.</div>
                    )}
                  </div>
                </div>

                {(dashboardData?.stripe_errors || []).length > 0 && (
                  <Alert className="border-amber-200 bg-amber-50" data-testid="stripe-dashboard-stripe-errors-alert">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-amber-800">
                      Stripe data warning: {(dashboardData.stripe_errors || []).join(' | ')}
                    </AlertDescription>
                  </Alert>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* How it works */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How Payments Work</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                1
              </div>
              <div>
                <h4 className="font-medium">Connect Your Stripe Account</h4>
                <p className="text-sm text-gray-500">
                  Link your existing Stripe account or create a new one. This takes about 5 minutes.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                2
              </div>
              <div>
                <h4 className="font-medium">Customers Pay Online</h4>
                <p className="text-sm text-gray-500">
                  Invoices include a "Pay Now" button. Webstore customers checkout with card.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                3
              </div>
              <div>
                <h4 className="font-medium">Money Goes to You</h4>
                <p className="text-sm text-gray-500">
                  Funds are deposited directly to your bank account (minus Stripe fees + {connectStatus?.platform_fee_percent || 3}% platform fee).
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
