import { useEffect, useState, useCallback } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Loader2, ShieldCheck, CheckCircle2, AlertTriangle, ExternalLink, Banknote } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Public Webstore Owner onboarding landing page.
 * URL: /webstore-owner/onboard/:token
 *
 * Tokenized — no login required. Shows the webstore + the tenant who invited
 * them, then routes them through Stripe Express hosted onboarding. On return
 * from Stripe (?stripe_return=1) we poll the refresh endpoint until charges
 * are enabled.
 */
export default function WebstoreOwnerOnboard() {
  const { token } = useParams();
  const [searchParams] = useSearchParams();
  const [ctx, setCtx] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const isReturning = searchParams.get('stripe_return') === '1';

  const loadContext = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_URL}/api/owner-onboard/${token}`);
      setCtx(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'This invitation is invalid or has expired.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadContext(); }, [loadContext]);

  // If we just returned from Stripe hosted onboarding, poll for the new status.
  useEffect(() => {
    if (!isReturning || !token) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const { data } = await axios.get(`${API_URL}/api/owner-onboard/${token}/refresh`);
        if (!cancelled) {
          setCtx((prev) => prev ? { ...prev, ...data, charges_enabled: data.charges_enabled, payouts_enabled: data.payouts_enabled, details_submitted: data.details_submitted } : prev);
          if (!data.ready) {
            setTimeout(poll, 2500);
          }
        }
      } catch {
        // silent — user can retry
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [isReturning, token]);

  const startStripe = async () => {
    setStarting(true);
    try {
      const origin = window.location.origin;
      const baseReturn = `${origin}/webstore-owner/onboard/${token}`;
      const { data } = await axios.post(`${API_URL}/api/owner-onboard/${token}/start-stripe`, {
        return_url: `${baseReturn}?stripe_return=1`,
        refresh_url: baseReturn,
      });
      window.location.href = data.url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not start Stripe onboarding');
      setStarting(false);
    }
  };

  const openStripeDashboard = async () => {
    try {
      const { data } = await axios.post(`${API_URL}/api/owner-onboard/${token}/login-link`);
      window.open(data.url, '_blank', 'noopener');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not open Stripe dashboard');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-[#2F8BFB]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-[#111826] border-[#1E293B]">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Invitation expired</h2>
            <p className="text-slate-400">{error}</p>
            <p className="text-slate-500 text-sm mt-4">
              Ask the sign shop to send you a new invite link.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const charges = !!ctx?.charges_enabled;
  const payouts = !!ctx?.payouts_enabled;
  const started = !!ctx?.stripe_account_id;

  return (
    <div className="min-h-screen bg-[#0B0F17] py-10 px-4">
      <div className="max-w-xl mx-auto">
        <Card className="bg-[#111826] border-[#1E293B]" data-testid="owner-onboard-card">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#2F8BFB]/15 rounded-lg">
                <ShieldCheck className="h-6 w-6 text-[#2F8BFB]" />
              </div>
              <div>
                <CardTitle className="text-white">Connect Stripe to Get Paid</CardTitle>
                <CardDescription className="text-slate-400">
                  From <span className="text-slate-200 font-medium">{ctx?.tenant_company_name}</span>
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="bg-[#0B0F17] rounded-md p-4 border border-[#1E293B]">
              <p className="text-slate-400 text-sm">Your Webstore</p>
              <p className="text-white font-semibold">{ctx?.webstore_name}</p>
              <p className="text-slate-500 text-xs mt-2">Hi {ctx?.owner_name || 'there'} — invited as {ctx?.owner_email}</p>
            </div>

            {/* Status */}
            {charges ? (
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-md p-4 text-emerald-200">
                <div className="flex items-center gap-2 font-semibold mb-1">
                  <CheckCircle2 className="h-5 w-5" /> You're all set!
                </div>
                <p className="text-emerald-100/90 text-sm">
                  Your Stripe account is connected. From here on, every order on your store will deposit your
                  commission straight to your bank account automatically.
                </p>
                <div className="mt-3">
                  <Button onClick={openStripeDashboard} variant="outline" className="bg-emerald-500/5 border-emerald-500/30 text-emerald-100" data-testid="owner-stripe-dashboard-btn">
                    <ExternalLink className="h-4 w-4 mr-2" /> Open My Stripe Dashboard
                  </Button>
                </div>
              </div>
            ) : started ? (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-md p-4 text-amber-100">
                <div className="flex items-center gap-2 font-semibold mb-1">
                  <AlertTriangle className="h-5 w-5" /> Almost there
                </div>
                <p className="text-amber-100/90 text-sm">
                  Stripe still needs a bit more info before they can pay you out.
                  {isReturning && ' We\'re refreshing your status now…'}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button onClick={startStripe} disabled={starting} className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90" data-testid="owner-resume-stripe-btn">
                    {starting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ExternalLink className="h-4 w-4 mr-2" />}
                    Continue Stripe onboarding
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                  <StatusPill label="Identity submitted" ok={!!ctx?.details_submitted} />
                  <StatusPill label="Payouts enabled" ok={payouts} />
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-slate-300 text-sm">
                  Click below to securely connect your Stripe account.{' '}
                  <span className="text-slate-400">It takes about 5 minutes — you'll provide your bank info, ID, and tax details directly to Stripe.</span>
                </p>
                <div className="bg-[#0B0F17] border border-[#1E293B] rounded-md p-3 text-sm text-slate-300">
                  <p className="flex items-center gap-2 mb-1"><Banknote className="h-4 w-4 text-emerald-400" /> Direct deposits to your bank</p>
                  <p className="flex items-center gap-2 mb-1"><ShieldCheck className="h-4 w-4 text-emerald-400" /> Stripe handles all tax forms (1099-K)</p>
                  <p className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-400" /> No password to remember</p>
                </div>
                <Button onClick={startStripe} disabled={starting} className="w-full bg-[#2F8BFB] hover:bg-[#2F8BFB]/90" data-testid="owner-start-stripe-btn">
                  {starting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ShieldCheck className="h-4 w-4 mr-2" />}
                  Connect Stripe Now
                </Button>
              </div>
            )}

            <p className="text-xs text-slate-500 text-center pt-2">
              Powered by Stripe. SignGuy AI never sees your bank account or SSN.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatusPill({ label, ok }) {
  return (
    <div className={`flex items-center gap-1.5 rounded px-2 py-1 ${ok ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-700/40 text-slate-400'}`}>
      {ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
      <span>{label}</span>
    </div>
  );
}
