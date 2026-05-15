import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { CheckCircle2, AlertTriangle, Link2, Mail, Loader2, ExternalLink, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { useApp } from '../context/AppContext';

/**
 * Webstore-detail "Owner Stripe Connect" card. Lets a tenant invite the
 * webstore owner to onboard with Stripe Express in two ways:
 *   - Quick Connect (magic link, no SignGuy account)
 *   - Owner Portal (creates a SignGuy login + Stripe Express)
 *
 * Once the owner finishes onboarding, the card shows live status and
 * unlocks the "Activate Store" gate on the webstore.
 */
export default function WebstoreOwnerConnectCard({ webstore, onChanged }) {
  const { api } = useApp();
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [inviteEmail, setInviteEmail] = useState(webstore?.owner_email || '');
  const [inviteName, setInviteName] = useState(webstore?.owner_name || '');
  const [sending, setSending] = useState(null); // 'quick' | 'portal' | null
  const [lastLink, setLastLink] = useState(null);

  const fetchStatus = useCallback(async () => {
    if (!webstore?.id) return;
    setLoadingStatus(true);
    try {
      const { data } = await api.get(`/webstore-owners/${webstore.id}/owner-status`);
      setStatus(data);
    } catch (err) {
      console.error('fetch owner-status failed', err);
    } finally {
      setLoadingStatus(false);
    }
  }, [api, webstore?.id]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const sendInvite = async (variant /* 'quick' | 'portal' */) => {
    if (!inviteEmail.trim()) {
      toast.error('Owner email is required');
      return;
    }
    setSending(variant);
    try {
      const path = variant === 'portal'
        ? `/webstore-owners/${webstore.id}/invite/portal`
        : `/webstore-owners/${webstore.id}/invite/quick`;
      const { data } = await api.post(path, {
        email: inviteEmail.trim(),
        name: inviteName.trim() || undefined,
        public_url: window.location.origin,
      });
      toast.success(data.message || 'Invite sent');
      setLastLink(data.invite_url);
      onChanged?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send invite');
    } finally {
      setSending(null);
    }
  };

  const copyLink = () => {
    if (!lastLink) return;
    navigator.clipboard.writeText(lastLink);
    toast.success('Link copied');
  };

  const ready = status?.ready_to_activate;
  const acctId = status?.owner_stripe_account_id;

  return (
    <Card className="bg-[#111826] border-[#1E293B]" data-testid="owner-connect-card">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-white flex items-center gap-2 text-base">
            <ShieldCheck className="h-4 w-4 text-[#2F8BFB]" />
            Owner Stripe Connection
          </CardTitle>
          {loadingStatus ? (
            <Badge variant="outline" className="text-slate-400 border-slate-600">Checking…</Badge>
          ) : ready ? (
            <Badge className="bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Connected
            </Badge>
          ) : acctId ? (
            <Badge className="bg-amber-500/15 text-amber-300 border border-amber-500/30">
              <AlertTriangle className="h-3.5 w-3.5 mr-1" /> Pending Stripe verification
            </Badge>
          ) : (
            <Badge variant="outline" className="text-slate-400 border-slate-600">Not connected</Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {ready ? (
          <div className="text-sm text-slate-300 space-y-2">
            <p>
              <strong className="text-white">{status?.owner_name || 'Owner'}</strong> is fully onboarded
              with Stripe. Their commission will be auto-deposited on every completed order — no manual payout
              needed.
            </p>
            <p className="text-slate-400 text-xs">
              Stripe account: <span className="font-mono text-slate-300">{acctId}</span>
            </p>
            <div className="pt-1">
              <Button
                size="sm"
                variant="outline"
                onClick={fetchStatus}
                className="text-slate-300 border-slate-600"
                data-testid="owner-refresh-status-btn"
              >
                Refresh status
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-md p-3 text-sm text-amber-100">
              <p className="font-medium text-amber-200 mb-1">Store cannot go Active yet.</p>
              <p className="text-amber-100/80">
                {acctId
                  ? 'Owner started onboarding but hasn\'t finished Stripe identity / bank verification.'
                  : 'Send the owner a Stripe connect link below. They\'ll get paid automatically once an order completes.'}
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <Label className="text-slate-200 text-xs">Owner Email</Label>
                <Input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="owner@example.com"
                  className="mt-1"
                  data-testid="owner-invite-email-input"
                />
              </div>
              <div>
                <Label className="text-slate-200 text-xs">Owner Name (optional)</Label>
                <Input
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  placeholder="Their full name"
                  className="mt-1"
                  data-testid="owner-invite-name-input"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-2">
              <Button
                onClick={() => sendInvite('quick')}
                disabled={sending !== null || !inviteEmail.trim()}
                className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
                data-testid="owner-invite-quick-btn"
              >
                {sending === 'quick' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Mail className="h-4 w-4 mr-2" />}
                Send Quick Connect Link
              </Button>
              <Button
                onClick={() => sendInvite('portal')}
                disabled={sending !== null || !inviteEmail.trim()}
                variant="outline"
                className="text-slate-200 border-slate-600 hover:bg-slate-800"
                data-testid="owner-invite-portal-btn"
              >
                {sending === 'portal' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ExternalLink className="h-4 w-4 mr-2" />}
                Create Owner Portal
              </Button>
            </div>

            <p className="text-xs text-slate-400">
              <strong className="text-slate-300">Quick:</strong> No login needed — owner clicks the link, connects Stripe, gets paid.{' '}
              <strong className="text-slate-300">Portal:</strong> Owner creates a SignGuy account they can log into to track commissions.
            </p>

            {lastLink && (
              <div className="border border-slate-700 rounded-md p-2 flex items-center gap-2 text-xs">
                <Link2 className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span className="text-slate-400 truncate flex-1" title={lastLink}>{lastLink}</span>
                <Button size="sm" variant="ghost" onClick={copyLink} className="h-7 text-slate-300">Copy</Button>
              </div>
            )}

            <div className="pt-1">
              <Button
                size="sm"
                variant="ghost"
                onClick={fetchStatus}
                className="text-slate-400 hover:text-white"
                data-testid="owner-refresh-status-btn"
              >
                Refresh status
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
