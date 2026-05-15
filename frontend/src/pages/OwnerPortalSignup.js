import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Loader2, ShieldCheck, AlertTriangle, KeyRound } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Public Owner Portal Signup page.
 * URL: /owner-portal-signup/:token
 *
 * Creates a SignGuy webstore_owner account, stores the JWT, then redirects to
 * the Stripe Express onboarding flow shared with the quick-connect path.
 */
export default function OwnerPortalSignup() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [ctx, setCtx] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadContext = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API_URL}/api/owner-onboard/${token}`);
      if (!data.portal_invite) {
        setError("This is a Quick Connect invite — open it from your email and you don't need a password.");
      } else {
        setCtx(data);
        setFullName(data.owner_name || '');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'This invitation is invalid or has expired.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadContext(); }, [loadContext]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await axios.post(`${API_URL}/api/owner-portal/signup`, {
        token,
        password,
        full_name: fullName,
      });
      localStorage.setItem('owner_portal_token', data.access_token);
      localStorage.setItem('owner_portal_webstore_id', data.webstore_id);
      toast.success('Account created — let\'s connect your Stripe next');
      // Send them through the same Stripe onboarding flow (shared token)
      navigate(`/webstore-owner/onboard/${token}?from=portal`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Signup failed');
    } finally {
      setSubmitting(false);
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
            <h2 className="text-xl font-bold text-white mb-2">Cannot continue</h2>
            <p className="text-slate-400">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] py-10 px-4">
      <div className="max-w-md mx-auto">
        <Card className="bg-[#111826] border-[#1E293B]" data-testid="owner-portal-signup-card">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#2F8BFB]/15 rounded-lg">
                <ShieldCheck className="h-6 w-6 text-[#2F8BFB]" />
              </div>
              <div>
                <CardTitle className="text-white">Create Your Owner Portal</CardTitle>
                <CardDescription className="text-slate-400">
                  For <span className="text-slate-200 font-medium">{ctx?.webstore_name}</span> with {ctx?.tenant_company_name}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label className="text-slate-200">Email</Label>
                <Input value={ctx?.owner_email || ''} disabled className="mt-1 bg-[#0B0F17] text-slate-400" />
              </div>
              <div>
                <Label className="text-slate-200">Your Name</Label>
                <Input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full name"
                  className="mt-1"
                  data-testid="owner-signup-name-input"
                />
              </div>
              <div>
                <Label className="text-slate-200 flex items-center gap-1.5"><KeyRound className="h-3.5 w-3.5" /> Choose a Password</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="mt-1"
                  required
                  minLength={8}
                  data-testid="owner-signup-password-input"
                />
                <p className="text-xs text-slate-500 mt-1">You'll use this to log into your owner portal anytime.</p>
              </div>
              <Button type="submit" disabled={submitting || !password} className="w-full bg-[#2F8BFB] hover:bg-[#2F8BFB]/90" data-testid="owner-signup-submit-btn">
                {submitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ShieldCheck className="h-4 w-4 mr-2" />}
                Create Account &amp; Continue
              </Button>
              <p className="text-xs text-slate-500 text-center">
                Next step: connect your Stripe account so you get paid directly.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
