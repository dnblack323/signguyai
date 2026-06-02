import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, KeyRound, ArrowLeft, CheckCircle2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('This reset link is missing its token. Please request a new link.');
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      if (response.ok) {
        setSuccess(true);
        setTimeout(() => navigate('/login'), 2500);
      } else {
        let msg = 'Could not reset your password. Please request a new link.';
        try {
          const data = await response.json();
          if (typeof data.detail === 'string') msg = data.detail;
          else if (Array.isArray(data.detail)) msg = data.detail.map((d) => d.msg).filter(Boolean).join(' ') || msg;
        } catch { /* ignore */ }
        setError(msg);
      }
    } catch {
      setError('Network error. Please try again.');
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <img
              src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/ht3r57hi_sgai%20slant.png"
              alt="SignGuy AI"
              className="h-32 w-auto"
            />
          </div>
          <p style={{ color: 'var(--text-muted-on-dark)' }} className="mt-2">Sign Shop Operating System</p>
        </div>

        <Card className="border shadow-xl" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }} data-testid="reset-password-page">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center font-heading" style={{ color: 'var(--text)' }}>
              Choose a New Password
            </CardTitle>
            <CardDescription className="text-center" style={{ color: 'var(--text-muted)' }}>
              Enter a new password for your account
            </CardDescription>
          </CardHeader>

          {success ? (
            <CardContent className="space-y-4">
              <Alert className="border-green-300 bg-green-50">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-700" data-testid="reset-confirm-success">
                  Your password has been reset. Redirecting you to login…
                </AlertDescription>
              </Alert>
              <Button
                onClick={() => navigate('/login')}
                data-testid="go-to-login-btn"
                className="w-full text-white font-medium bg-[#2F8BFB] hover:bg-[#1E7AF0]"
              >
                Go to Login
              </Button>
            </CardContent>
          ) : (
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4">
                {error && (
                  <Alert variant="destructive" className="border-red-300" style={{ backgroundColor: 'var(--danger-soft)' }}>
                    <AlertDescription className="text-red-600" data-testid="reset-confirm-error">{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="newPassword" style={{ color: 'var(--text)' }}>New Password</Label>
                  <Input
                    id="newPassword"
                    data-testid="reset-new-password-input"
                    type="password"
                    placeholder="Min 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" style={{ color: 'var(--text)' }}>Confirm New Password</Label>
                  <Input
                    id="confirmPassword"
                    data-testid="reset-confirm-password-input"
                    type="password"
                    placeholder="Repeat password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                  />
                </div>
              </CardContent>

              <CardFooter className="flex flex-col space-y-4">
                <Button
                  type="submit"
                  data-testid="reset-confirm-submit-btn"
                  className="w-full text-white font-medium bg-[#2F8BFB] hover:bg-[#1E7AF0]"
                  disabled={isLoading}
                >
                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <KeyRound className="mr-2 h-4 w-4" />}
                  {isLoading ? 'Saving...' : 'Reset Password'}
                </Button>

                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  data-testid="back-to-login-btn"
                  className="text-sm hover:underline flex items-center justify-center gap-1"
                  style={{ color: 'var(--accent)' }}
                >
                  <ArrowLeft className="h-3 w-3" /> Back to login
                </button>
              </CardFooter>
            </form>
          )}
        </Card>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted-on-dark)' }}>
          &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
        </p>
      </div>
    </div>
  );
}
