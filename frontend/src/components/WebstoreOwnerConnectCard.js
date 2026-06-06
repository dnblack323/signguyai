/**
 * Webstore-detail "Owner Stripe Connect" card.
 *
 * Lets a tenant:
 *   1. Check the current Stripe onboarding status of the store owner.
 *   2. Send (or resend) a quick-connect invite email.
 *
 * Backend endpoints consumed:
 *   GET  /api/webstore-owners/{id}/owner-status  → owner Stripe status
 *   POST /api/webstore-owners/{id}/invite/quick  → send one-time onboarding link
 *
 * Response shapes are matched to the backend models (OwnerInviteResponse +
 * the owner-status dict) — NOT the old stub field names that were broken.
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
  const { getWebstoreOwnerStatus, sendWebstoreOwnerInvite } = useApp();

  const [status, setStatus]             = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [sendingEmail, setSendingEmail]   = useState(false);
  const [inviteEmail, setInviteEmail]     = useState(webstore?.owner_email || '');

  // ── Status helpers (mapped to actual backend fields) ──────────────────────

  /**
   * Backend owner-status response:
   *   owner_stripe_account_id, charges_enabled, payouts_enabled,
   *   details_submitted, portal_enabled, ready_to_activate
   */
  const isConnected      = Boolean(status?.charges_enabled);
  const isPending        = Boolean(status?.owner_stripe_account_id && !status?.charges_enabled);
  const isNotConnected   = !status || !status.owner_stripe_account_id;

  // ── Check Status ──────────────────────────────────────────────────────────

  const fetchStatus = useCallback(async () => {
    if (!webstore?.id) return;
    setLoadingStatus(true);
    try {
      const s = await getWebstoreOwnerStatus(webstore.id);
      setStatus(s);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      console.error('Failed to fetch owner Stripe status', err);
      toast.error(typeof detail === 'string' ? detail : 'Could not load owner Stripe status');
      setStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  }, [webstore?.id, getWebstoreOwnerStatus]);

  // ── Send / Resend Invite ──────────────────────────────────────────────────

  const sendInvite = async () => {
    if (!inviteEmail.trim()) {
      toast.error('Enter an email address first');
      return;
    }
    setSendingEmail(true);
    try {
      /**
       * Backend OwnerInviteResponse: { success, invite_url, expires_at, message }
       * success=false means the invite was created but the email failed (SendGrid).
       */
      const result = await sendWebstoreOwnerInvite(
        webstore.id,
        inviteEmail.trim(),
        window.location.origin,
      );

      if (result?.success) {
        toast.success(`Onboarding invite sent to ${inviteEmail}`);
        // Refresh status so badge updates if the invite already resolved
        fetchStatus();
      } else {
        // Email delivery failed — invite_url is still usable
        const fallbackUrl = result?.invite_url;
        toast.error(
          result?.message || 'Email could not be delivered. Check your SendGrid configuration.'
        );
        if (fallbackUrl) {
          // Show a copyable warning so staff can share manually
          toast.warning(
            `Invite link (share manually): ${fallbackUrl}`,
            { duration: 12000 }
          );
        }
      }
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      // Backend throws 502 when SendGrid fails — surface a clear, user-friendly message.
      const status = err?.response?.status;
      const userMsg =
        status === 502
          ? 'Email delivery failed. Check your SendGrid API key in settings.'
          : typeof rawDetail === 'string'
            ? rawDetail
            : Array.isArray(rawDetail)
              ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
              : 'Failed to send invite — check backend logs';
      toast.error(userMsg);
    } finally {
      setSendingEmail(false);
    }
  };

  // ── Status badge ──────────────────────────────────────────────────────────

  const StatusBadge = () => {
    if (loadingStatus) return (
      <Badge variant="secondary" className="flex items-center gap-1 text-xs">
        <Loader2 className="h-3 w-3 animate-spin" /> Checking…
      </Badge>
    );
    if (isConnected) return (
      <Badge className="flex items-center gap-1 text-xs bg-emerald-100 text-emerald-700 border border-emerald-200" data-testid="owner-stripe-badge-connected">
        <CheckCircle2 className="h-3 w-3" /> Connected
      </Badge>
    );
    if (isPending) return (
      <Badge className="flex items-center gap-1 text-xs bg-amber-100 text-amber-700 border border-amber-200" data-testid="owner-stripe-badge-pending">
        <Clock className="h-3 w-3" /> Onboarding Pending
      </Badge>
    );
    return (
      <Badge variant="outline" className="flex items-center gap-1 text-xs text-gray-500 border-gray-300" data-testid="owner-stripe-badge-not-connected">
        <AlertCircle className="h-3 w-3" /> Not Connected
      </Badge>
    );
  };

  // ── Render ────────────────────────────────────────────────────────────────

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
              data-testid="refresh-owner-stripe-status-btn"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingStatus ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          The store owner must connect a Stripe account to receive payouts.
          Send them an onboarding link via email.
        </p>

        {/* Connected state */}
        {isConnected && status?.owner_stripe_account_id && (
          <div className="flex items-start gap-2 rounded-md bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">
            <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Stripe account connected</p>
              <p className="text-xs text-emerald-600 mt-0.5 font-mono">{status.owner_stripe_account_id}</p>
              {status.payouts_enabled && (
                <p className="text-xs text-emerald-600 mt-0.5">Payouts enabled</p>
              )}
            </div>
          </div>
        )}

        {/* Pending state */}
        {isPending && (
          <div className="flex items-start gap-2 rounded-md bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
            <Clock className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Onboarding link sent — awaiting owner completion</p>
              <p className="text-xs text-amber-600 mt-0.5 font-mono">{status.owner_stripe_account_id}</p>
              <p className="text-xs text-amber-600 mt-0.5">Resend the email if the owner hasn't finished setup.</p>
            </div>
          </div>
        )}

        {/* Not connected — prompt to check or send */}
        {isNotConnected && !loadingStatus && (
          <div className="flex items-start gap-2 rounded-md bg-blue-50 border border-blue-200 p-3 text-sm text-blue-700">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <p>Click "Check Status" to load the current Stripe onboarding state, or send the onboarding email below.</p>
          </div>
        )}

        {/* Invite / resend email input */}
        <div className="space-y-2">
          <Label className="text-sm font-medium text-foreground">
            {isConnected ? 'Resend Onboarding Email' : 'Invite Store Owner'}
          </Label>
          <div className="flex gap-2">
            <Input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder={webstore?.owner_email || 'owner@example.com'}
              className="flex-1"
              data-testid="owner-invite-email-input"
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

        {/* "Check Status" shown when status has never been loaded */}
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
