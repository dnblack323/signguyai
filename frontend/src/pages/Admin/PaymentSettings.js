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

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PaymentSettings() {
  const [loading, setLoading] = useState(true);
  const [connectStatus, setConnectStatus] = useState(null);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    fetchConnectStatus();
    
    // Check for return from Stripe onboarding
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('stripe_return') === 'true') {
      toast.success('Stripe account setup updated');
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const fetchConnectStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API_URL}/api/stripe-connect/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConnectStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch Stripe status:', err);
      toast.error('Failed to load payment settings');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectStripe = async () => {
    setConnecting(true);
    try {
      const token = localStorage.getItem('auth_token');
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
      const token = localStorage.getItem('auth_token');
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
      toast.error('Failed to continue setup');
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Are you sure you want to disconnect your Stripe account? You will not be able to accept payments until you reconnect.')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('auth_token');
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
        <p className="text-muted-foreground">
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

      {/* Connection Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${connectStatus?.connected ? 'bg-green-500/10' : 'bg-muted'}`}>
                <CreditCard className={`h-5 w-5 ${connectStatus?.connected ? 'text-green-500' : 'text-muted-foreground'}`} />
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
                <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
                  {connectStatus.charges_enabled ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm">
                    Payments {connectStatus.charges_enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
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

              {/* Actions */}
              <div className="flex gap-3 pt-2">
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
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-muted/30">
                  <CreditCard className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Accept Cards</h4>
                  <p className="text-xs text-muted-foreground">Credit & debit cards</p>
                </div>
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-muted/30">
                  <Shield className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Secure Payments</h4>
                  <p className="text-xs text-muted-foreground">PCI compliant</p>
                </div>
                <div className="flex flex-col items-center text-center p-4 rounded-lg bg-muted/30">
                  <TrendingUp className="h-8 w-8 text-primary mb-2" />
                  <h4 className="font-medium">Fast Payouts</h4>
                  <p className="text-xs text-muted-foreground">Direct to your bank</p>
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
                <p className="text-sm text-muted-foreground">
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
                <p className="text-sm text-muted-foreground">
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
                <p className="text-sm text-muted-foreground">
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
