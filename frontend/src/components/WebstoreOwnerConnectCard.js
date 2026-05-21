/**
 * Webstore-detail "Owner Stripe Connect" card.
 * Lets a tenant invite the store owner and tracks their Stripe onboarding status.
 * Light-mode compatible design with proper text contrast.
 */
import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { CreditCard, RefreshCw, Loader2, Mail, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { toast } from 'sonner';

export default function WebstoreOwnerConnectCard({ webstore }) {
  const { getWebstoreOwnerOnboardingStatus, sendWebstoreOwnerOnboardingEmail } = useApp();

  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [inviteEmail, setInviteEmail] = useState(webstore?.owner_email || '');

  const fetchStatus = useCallback(async () => {
    if (!webstore?.id) return;
    setLoadingStatus(true);
    try {
      const s = await getWebstoreOwnerOnboardingStatus(webstore.id);
      setStatus(s);
    } catch (err) {
      console.error('Failed to fetch Stripe onboarding status', err);
      setStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  }, [webstore?.id, getWebstoreOwnerOnboardingStatus]);

  const sendInvite = async () => {
    if (!inviteEmail.trim()) {
      toast.error('Enter an email address first');
      return;
    }
    setSendingEmail(true);
    try {
      const result = await sendWebstoreOwnerOnboardingEmail(webstore.id, inviteEmail.trim());
      if (result?.sent) {
        toast.success(`Onboarding email sent to ${inviteEmail}`);
      } else {
        toast.warning(result?.message || 'Email may not have been delivered — check your SendGrid logs');
      }
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      toast.error(typeof rawDetail === 'string' ? rawDetail
        : Array.isArray(rawDetail) ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
        : 'Failed to send invite email');
    } finally {
      setSendingEmail(false);
    }
  };

  // Status display helpers
  const connected = status?.stripe_onboarding_complete;
  const onboardingPending = status?.stripe_account_id && !connected;
  const notConnected = !status || (!status.stripe_account_id && !connected);

  const StatusBadge = () => {
    if (loadingStatus) return (
      <Badge variant="secondary" className="flex items-center gap-1 text-xs">
        <Loader2 className="h-3 w-3 animate-spin" /> Checking...
      </Badge>
    );
    if (connected) return (
      <Badge className="flex items-center gap-1 text-xs bg-emerald-100 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="h-3 w-3" /> Connected
      </Badge>
    );
    if (onboardingPending) return (
      <Badge className="flex items-center gap-1 text-xs bg-amber-100 text-amber-700 border border-amber-200">
        <Clock className="h-3 w-3" /> Onboarding Pending
      </Badge>
    );
    return (
      <Badge variant="outline" className="flex items-center gap-1 text-xs text-gray-500 border-gray-300">
        <AlertCircle className="h-3 w-3" /> Not Connected
      </Badge>
    );
  };

  return (
    <Card className="border border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base flex items-center gap-2 text-card-foreground">
            <CreditCard className="h-4 w-4 text-primary" />
            Owner Stripe Connection
          </CardTitle>
          <div className="flex items-center gap-2">
            <StatusBadge />
            <Button
              size="sm"
              variant="ghost"
              onClick={fetchStatus}
              disabled={loadingStatus}
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
              title="Refresh status"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingStatus ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          The store owner must connect a Stripe account to receive payouts. Send them an onboarding link via email.
        </p>

        {connected && status?.stripe_account_id && (
          <div className="flex items-start gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Stripe account connected</p>
              <p className="text-xs text-emerald-600 mt-0.5 font-mono">{status.stripe_account_id}</p>
            </div>
          </div>
        )}

        {onboardingPending && (
          <div className="flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
            <Clock className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Onboarding link sent — awaiting owner completion</p>
              <p className="text-xs text-amber-600 mt-0.5">Resend the email if the owner hasn't finished setup.</p>
            </div>
          </div>
        )}

        {notConnected && !loadingStatus && (
          <div className="flex items-start gap-2 rounded-md bg-blue-50 border border-blue-200 p-3 text-sm text-blue-700">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <p>Click "Check Status" to load the current Stripe onboarding state, or send the onboarding email below.</p>
          </div>
        )}

        {/* Invite / resend email */}
        <div className="space-y-2">
          <Label className="text-sm font-medium text-foreground">
            {connected ? 'Resend Onboarding Email' : 'Invite Store Owner'}
          </Label>
          <div className="flex gap-2">
            <Input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder={webstore?.owner_email || 'owner@example.com'}
              className="flex-1"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={sendInvite}
              disabled={sendingEmail}
              data-testid="send-stripe-invite-btn"
              className="shrink-0"
            >
              {sendingEmail
                ? <Loader2 className="h-4 w-4 animate-spin" />
                : <><Mail className="h-4 w-4 mr-1.5" /> Send</>}
            </Button>
          </div>
        </div>

        {!status && !loadingStatus && (
          <Button
            size="sm"
            variant="outline"
            onClick={fetchStatus}
            className="w-full"
            data-testid="check-stripe-status-btn"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Check Status
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
