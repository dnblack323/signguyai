import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Checkbox } from '../components/ui/checkbox';
import { Loader2, Eye, EyeOff, LogIn, UserPlus, KeyRound, ArrowLeft } from 'lucide-react';
import { clearAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, register, error, clearError, isAuthenticated } = useAuth();
  
  // Check for ?register=true in URL
  const shouldRegister = searchParams.get('register') === 'true';
  const [isRegister, setIsRegister] = useState(shouldRegister);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);
  
  // Update isRegister when URL changes
  useEffect(() => {
    if (shouldRegister) {
      setIsRegister(true);
    }
  }, [shouldRegister]);

  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [resetError, setResetError] = useState('');

  useEffect(() => {
    clearAuthToken();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    clearError();

    // Validation
    if (!email || !password) {
      setLocalError('Email and password are required');
      return;
    }

    if (isRegister) {
      if (!fullName) {
        setLocalError('Full name is required');
        return;
      }
      if (password.length < 6) {
        setLocalError('Password must be at least 6 characters');
        return;
      }
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match');
        return;
      }
    }

    setIsLoading(true);

    if (isRegister) {
      const result = await register(email, password, fullName, companyName);
      if (!result.success) {
        setLocalError(result.error);
      }
    } else {
      const result = await login(email, password, rememberMe);
      if (!result.success) {
        setLocalError(result.error);
      }
    }

    setIsLoading(false);
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setLocalError('');
    clearError();
    setPassword('');
    setConfirmPassword('');
    setShowForgotPassword(false);
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setResetError('');
    setResetMessage('');

    if (!resetEmail) {
      setResetError('Email is required');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${API_URL}/api/auth/forgot-password`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: resetEmail, origin: window.location.origin }),
        }
      );
      if (response.ok) {
        const data = await response.json();
        setResetMessage(data.message || 'If an account exists for that email, a password reset link has been sent.');
        setResetEmail('');
      } else {
        let msg = 'Could not process your request. Please try again.';
        try {
          const data = await response.json();
          msg = typeof data.detail === 'string' ? data.detail : msg;
        } catch { /* ignore */ }
        setResetError(msg);
      }
    } catch {
      setResetError('Network error. Please try again.');
    }
    setIsLoading(false);
  };

  const displayError = localError || error;

  // Forgot Password view
  if (showForgotPassword) {
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

          <Card className="border shadow-xl" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl text-center font-heading" style={{ color: 'var(--text)' }}>
                Reset Password
              </CardTitle>
              <CardDescription className="text-center" style={{ color: 'var(--text-muted)' }}>
                Enter your account email and we'll send you a secure reset link
              </CardDescription>
            </CardHeader>

            <form onSubmit={handlePasswordReset}>
              <CardContent className="space-y-4">
                {resetError && (
                  <Alert variant="destructive" className="border-red-300" style={{ backgroundColor: 'var(--danger-soft)' }}>
                    <AlertDescription className="text-red-600">{resetError}</AlertDescription>
                  </Alert>
                )}
                {resetMessage && (
                  <Alert className="border-green-300 bg-green-50">
                    <AlertDescription className="text-green-700" data-testid="reset-success-message">{resetMessage}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="resetEmail" style={{ color: 'var(--text)' }}>Account Email</Label>
                  <Input
                    id="resetEmail"
                    data-testid="reset-email-input"
                    type="email"
                    placeholder="you@example.com"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                  />
                </div>
              </CardContent>

              <CardFooter className="flex flex-col space-y-4">
                <Button
                  type="submit"
                  data-testid="reset-password-submit-btn"
                  className="w-full text-white font-medium bg-[#2F8BFB] hover:bg-[#1E7AF0]"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <KeyRound className="mr-2 h-4 w-4" />
                  )}
                  {isLoading ? 'Sending...' : 'Send Reset Link'}
                </Button>

                <button
                  type="button"
                  onClick={() => { setShowForgotPassword(false); setResetError(''); setResetMessage(''); }}
                  data-testid="back-to-login-btn"
                  className="text-sm hover:underline flex items-center justify-center gap-1"
                  style={{ color: 'var(--accent)' }}
                >
                  <ArrowLeft className="h-3 w-3" /> Back to login
                </button>
              </CardFooter>
            </form>
          </Card>

          <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted-on-dark)' }}>
            &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--bg)' }}>
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
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

        <Card className="border shadow-xl" style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center font-heading" style={{ color: 'var(--text)' }}>
              {isRegister ? 'Create an account' : 'Welcome back'}
            </CardTitle>
            <CardDescription className="text-center" style={{ color: 'var(--text-muted)' }}>
              {isRegister
                ? 'Enter your details to get started'
                : 'Enter your credentials to access your account'}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {displayError && (
                <Alert variant="destructive" className="border-red-300" style={{ backgroundColor: 'var(--danger-soft)' }}>
                  <AlertDescription className="text-red-600">{displayError}</AlertDescription>
                </Alert>
              )}

              {isRegister && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fullName" style={{ color: 'var(--text)' }}>Full Name</Label>
                    <Input
                      id="fullName"
                      data-testid="register-fullname-input"
                      placeholder="John Smith"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="companyName" style={{ color: 'var(--text)' }}>
                      Company Name <span style={{ color: 'var(--text-muted)' }}>(optional)</span>
                    </Label>
                    <Input
                      id="companyName"
                      data-testid="register-company-input"
                      placeholder="Your Sign Company"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                    />
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" style={{ color: 'var(--text)' }}>Email</Label>
                <Input
                  id="email"
                  data-testid="auth-email-input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" style={{ color: 'var(--text)' }}>Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    data-testid="auth-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pr-10"
                    style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 hover:opacity-70"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" style={{ color: 'var(--text)' }}>Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    data-testid="register-confirm-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)', color: 'var(--text)' }}
                  />
                </div>
              )}

              {/* Remember Me - Only show for login */}
              {!isRegister && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="rememberMe"
                      data-testid="remember-me-checkbox"
                      checked={rememberMe}
                      onCheckedChange={setRememberMe}
                    />
                    <Label 
                      htmlFor="rememberMe" 
                      className="text-sm cursor-pointer"
                      style={{ color: 'var(--text-muted)' }}
                    >
                      Remember me for 30 days
                    </Label>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    data-testid="forgot-password-link"
                    className="text-sm hover:underline"
                    style={{ color: 'var(--accent)' }}
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                data-testid={isRegister ? 'register-submit-btn' : 'login-submit-btn'}
                className="w-full text-white font-medium bg-[#2F8BFB] hover:bg-[#1E7AF0]"
                disabled={isLoading}
              >
                {isLoading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : isRegister ? (
                  <UserPlus className="mr-2 h-4 w-4" />
                ) : (
                  <LogIn className="mr-2 h-4 w-4" />
                )}
                {isLoading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
              </Button>

              <div className="text-center">
                <button
                  type="button"
                  onClick={toggleMode}
                  data-testid="toggle-auth-mode-btn"
                  className="text-sm hover:underline"
                  style={{ color: 'var(--accent)' }}
                >
                  {isRegister
                    ? 'Already have an account? Sign in'
                    : "Don't have an account? Create one"}
                </button>
              </div>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted-on-dark)' }}>
          &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
        </p>
      </div>
    </div>
  );
}
