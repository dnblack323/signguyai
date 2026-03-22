import { useState } from 'react';
import { ArrowLeft, Shield, Key, Ticket, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ProductionSetup() {
  const [setupKey, setSetupKey] = useState('');
  const [email, setEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [promoCode, setPromoCode] = useState('PAPPYBILL');
  const [promoType, setPromoType] = useState('free_trial');
  const [promoDays, setPromoDays] = useState(19);
  const [promoMaxUses, setPromoMaxUses] = useState(2);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleSetup = async () => {
    if (!setupKey.trim()) {
      setError('Setup key is required. Find JWT_SECRET_KEY in your backend .env file.');
      return;
    }
    
    setLoading(true);
    setError('');
    setResults(null);

    try {
      const body = { setup_key: setupKey };

      if (email && newPassword) {
        body.email = email;
        body.new_password = newPassword;
      }

      if (promoCode.trim()) {
        body.promo_codes = [{
          code: promoCode.trim().toUpperCase(),
          description: `Promo code: ${promoCode}`,
          discount_type: promoType,
          trial_days: promoType === 'free_trial' ? promoDays : 0,
          discount_value: promoType === 'percent' ? promoDays : 0,
          max_uses: promoMaxUses || null,
          expires_at: '2026-12-31',
          reset_usage: true,
        }];
      }

      const res = await fetch(`${API_URL}/api/auth/setup-admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Setup failed. Check your setup key.');
      } else {
        setResults(data.results);
      }
    } catch (err) {
      setError('Network error. Make sure the app is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060A13] text-slate-300" data-testid="production-setup-page">
      <div className="max-w-xl mx-auto px-4 py-16">
        <Link to="/login" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Login
        </Link>

        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-violet-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Production Setup</h1>
          <p className="text-slate-400">Reset your admin password and create promo codes</p>
        </div>

        <Card className="bg-[#111826] border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-violet-400" />
              Setup Key
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-slate-300">JWT Secret Key</Label>
              <Input
                type="password"
                value={setupKey}
                onChange={(e) => setSetupKey(e.target.value)}
                placeholder="Paste your JWT_SECRET_KEY from backend .env"
                className="bg-[#0B0F17] border-slate-600 text-white"
                data-testid="setup-key-input"
              />
              <p className="text-xs text-slate-500 mt-1">
                Find this in your deployed app's backend environment variables (JWT_SECRET_KEY)
              </p>
            </div>

            <div className="border-t border-slate-700 pt-4">
              <h3 className="text-white font-medium mb-3">Reset Admin Password</h3>
              <div className="space-y-3">
                <div>
                  <Label className="text-slate-300">Admin Email</Label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="thesigntistslab@gmail.com"
                    className="bg-[#0B0F17] border-slate-600 text-white"
                    data-testid="setup-email-input"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">New Password</Label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    className="bg-[#0B0F17] border-slate-600 text-white"
                    data-testid="setup-password-input"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-slate-700 pt-4">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Ticket className="w-4 h-4 text-violet-400" />
                Create Promo Code
              </h3>
              <div className="space-y-3">
                <div>
                  <Label className="text-slate-300">Code</Label>
                  <Input
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                    placeholder="PAPPYBILL"
                    className="bg-[#0B0F17] border-slate-600 text-white font-mono"
                    data-testid="setup-promo-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-slate-300">Type</Label>
                    <select
                      value={promoType}
                      onChange={(e) => setPromoType(e.target.value)}
                      className="w-full h-10 px-3 rounded-md bg-[#0B0F17] border border-slate-600 text-white text-sm"
                    >
                      <option value="free_trial">Free Days</option>
                      <option value="percent">Percent Off</option>
                    </select>
                  </div>
                  <div>
                    <Label className="text-slate-300">
                      {promoType === 'free_trial' ? 'Days Free' : '% Off'}
                    </Label>
                    <Input
                      type="number"
                      value={promoDays}
                      onChange={(e) => setPromoDays(parseInt(e.target.value) || 0)}
                      className="bg-[#0B0F17] border-slate-600 text-white"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-slate-300">Max Uses (leave empty for unlimited)</Label>
                  <Input
                    type="number"
                    value={promoMaxUses}
                    onChange={(e) => setPromoMaxUses(parseInt(e.target.value) || '')}
                    placeholder="Unlimited"
                    className="bg-[#0B0F17] border-slate-600 text-white"
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            {results && (
              <div className="space-y-2 bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                {results.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-green-400 text-sm">
                    <CheckCircle className="w-4 h-4 flex-shrink-0" />
                    {r}
                  </div>
                ))}
                <p className="text-green-300 text-sm font-medium mt-2">
                  Setup complete! You can now <Link to="/login" className="underline">log in</Link>.
                </p>
              </div>
            )}

            <Button
              onClick={handleSetup}
              disabled={loading || !setupKey.trim()}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white"
              data-testid="setup-submit-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Shield className="w-4 h-4 mr-2" />}
              Run Setup
            </Button>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-slate-600 mt-8">
          This page is protected by your server's JWT secret key. Only you can use it.
        </p>
      </div>
    </div>
  );
}
