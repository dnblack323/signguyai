import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import { Loader2, ShieldCheck, ExternalLink, LogOut, CheckCircle2, AlertTriangle, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const TOKEN_KEY = 'owner_portal_token';

function authHeader() {
  const t = localStorage.getItem(TOKEN_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/**
 * Owner Portal Dashboard. Lists the owner's connected stores, commission
 * paid, and provides a button to open their Stripe Express dashboard.
 * URL: /owner-portal
 *
 * Includes a small built-in login UI so an owner who already created an
 * account via the portal-invite flow can come back later and log in.
 */
export default function OwnerPortal() {
  const navigate = useNavigate();
  const [authed, setAuthed] = useState(!!localStorage.getItem(TOKEN_KEY));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [transfers, setTransfers] = useState({});
  // Inline login state
  const [email, setEmail] = useState('');
  const [pwd, setPwd] = useState('');
  const [loggingIn, setLoggingIn] = useState(false);

  const fetchMe = useCallback(async () => {
    if (!authed) { setLoading(false); return; }
    setLoading(true);
    try {
      const { data } = await axios.get(`${API_URL}/api/owner-portal/me`, { headers: authHeader() });
      setData(data);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        localStorage.removeItem(TOKEN_KEY);
        setAuthed(false);
      } else {
        toast.error('Failed to load portal');
      }
    } finally {
      setLoading(false);
    }
  }, [authed]);

  useEffect(() => { fetchMe(); }, [fetchMe]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoggingIn(true);
    try {
      const { data } = await axios.post(`${API_URL}/api/auth/login`, { email, password: pwd });
      const token = data.access_token || data.token;
      if (!token) throw new Error('No token');
      localStorage.setItem(TOKEN_KEY, token);
      setAuthed(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoggingIn(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('owner_portal_webstore_id');
    setAuthed(false);
    setData(null);
  };

  const openStripeDashboard = async (storeId) => {
    try {
      const { data } = await axios.post(
        `${API_URL}/api/owner-portal/stores/${storeId}/stripe-login-link`,
        {},
        { headers: authHeader() },
      );
      window.open(data.url, '_blank', 'noopener');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not open Stripe dashboard');
    }
  };

  const loadTransfers = async (storeId) => {
    if (transfers[storeId]) return; // already cached
    try {
      const { data } = await axios.get(
        `${API_URL}/api/owner-portal/stores/${storeId}/transfers`,
        { headers: authHeader() },
      );
      setTransfers((prev) => ({ ...prev, [storeId]: data.transfers || [] }));
    } catch (err) {
      toast.error('Could not load payouts');
    }
  };

  if (!authed) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-[#111826] border-[#1E293B]" data-testid="owner-portal-login-card">
          <CardHeader>
            <CardTitle className="text-white">Webstore Owner Login</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-3">
              <div>
                <Label className="text-slate-200">Email</Label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required className="mt-1" data-testid="owner-login-email" />
              </div>
              <div>
                <Label className="text-slate-200">Password</Label>
                <Input value={pwd} onChange={(e) => setPwd(e.target.value)} type="password" required className="mt-1" data-testid="owner-login-password" />
              </div>
              <Button type="submit" disabled={loggingIn} className="w-full bg-[#2F8BFB] hover:bg-[#2F8BFB]/90" data-testid="owner-login-submit">
                {loggingIn ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null} Sign In
              </Button>
              <p className="text-xs text-slate-500 text-center pt-2">
                Don't have a portal yet? Ask the sign shop to send you a portal invite.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-[#2F8BFB]" />
      </div>
    );
  }

  const stores = data?.stores || [];

  return (
    <div className="min-h-screen bg-[#0B0F17] py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6" data-testid="owner-portal-dashboard">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Owner Portal</h1>
            <p className="text-slate-400 text-sm">Welcome, {data?.owner?.full_name || data?.owner?.email}</p>
          </div>
          <Button variant="outline" onClick={logout} className="text-slate-300 border-slate-600" data-testid="owner-portal-logout">
            <LogOut className="h-4 w-4 mr-2" /> Log out
          </Button>
        </div>

        {stores.length === 0 ? (
          <Card className="bg-[#111826] border-[#1E293B]">
            <CardContent className="p-8 text-center text-slate-400">
              No stores are linked to your account yet.
            </CardContent>
          </Card>
        ) : stores.map((s) => {
          const ready = !!(s.owner_stripe_account_id && s.owner_stripe_charges_enabled);
          return (
            <Card key={s.id} className="bg-[#111826] border-[#1E293B]">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div>
                    <CardTitle className="text-white text-lg">{s.name}</CardTitle>
                    <p className="text-slate-500 text-xs uppercase tracking-wide mt-0.5">{s.store_type} · {s.status}</p>
                  </div>
                  {ready ? (
                    <Badge className="bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Stripe connected
                    </Badge>
                  ) : (
                    <Badge className="bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      <AlertTriangle className="h-3.5 w-3.5 mr-1" /> Stripe pending
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <Stat label="Orders" value={s.total_orders || 0} />
                  <Stat label="Sales" value={`$${(s.total_sales || 0).toFixed(2)}`} />
                  <Stat label="Paid to You" value={`$${(s.payout_paid || 0).toFixed(2)}`} highlight />
                  <Stat label="Pending" value={`$${(s.payout_owed || 0).toFixed(2)}`} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => openStripeDashboard(s.id)}
                    disabled={!ready}
                    className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
                    data-testid={`owner-store-${s.id}-stripe-btn`}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" /> Open Stripe Dashboard
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => loadTransfers(s.id)}
                    className="text-slate-300 border-slate-600"
                  >
                    <Wallet className="h-4 w-4 mr-2" /> Show payout history
                  </Button>
                </div>

                {transfers[s.id] && (
                  <div className="mt-3 border border-[#1E293B] rounded-md overflow-hidden">
                    <Table>
                      <TableHeader className="bg-[#0B0F17]">
                        <TableRow>
                          <TableHead className="text-slate-400">Date</TableHead>
                          <TableHead className="text-slate-400">Order</TableHead>
                          <TableHead className="text-slate-400">Customer</TableHead>
                          <TableHead className="text-slate-400 text-right">Commission</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {transfers[s.id].length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={4} className="text-center text-slate-500 py-6">No payouts yet</TableCell>
                          </TableRow>
                        ) : transfers[s.id].map((t) => (
                          <TableRow key={t.id}>
                            <TableCell className="text-slate-300 text-xs">
                              {t.owner_transfer_at ? new Date(t.owner_transfer_at).toLocaleString() : '—'}
                            </TableCell>
                            <TableCell className="text-slate-300">{t.order_number || t.id?.slice(0, 8)}</TableCell>
                            <TableCell className="text-slate-300">{t.customer_name || '—'}</TableCell>
                            <TableCell className="text-emerald-300 text-right font-medium">
                              ${(t.owner_transfer_amount || 0).toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}

        <p className="text-xs text-slate-500 text-center">
          <ShieldCheck className="inline-block h-3.5 w-3.5 mr-1" />
          Your bank info and tax data are stored by Stripe, not SignGuy AI.
        </p>
      </div>
    </div>
  );
}

function Stat({ label, value, highlight }) {
  return (
    <div className={`rounded-md p-3 border ${highlight ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-[#0B0F17] border-[#1E293B]'}`}>
      <p className="text-slate-400 text-xs uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-lg font-semibold ${highlight ? 'text-emerald-300' : 'text-white'}`}>{value}</p>
    </div>
  );
}
