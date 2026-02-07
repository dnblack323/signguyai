import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Checkbox } from '../components/ui/checkbox';
import { Loader2, Eye, EyeOff, LogIn, UserPlus } from 'lucide-react';

export default function Login() {
  const { login, register, error, clearError } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

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
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] p-4">
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-teal-500/20 border border-teal-500/30 mb-4">
            <span className="text-2xl font-bold text-teal-400">SG</span>
          </div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Sign Guy AI</h1>
          <p className="text-[var(--text-secondary)] mt-2">Sign Shop Operating System</p>
        </div>

        <Card className="bg-[var(--card-bg)] border-[var(--card-border)]">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-[var(--text-primary)]">
              {isRegister ? 'Create an account' : 'Welcome back'}
            </CardTitle>
            <CardDescription className="text-center text-[var(--text-secondary)]">
              {isRegister
                ? 'Enter your details to get started'
                : 'Enter your credentials to access your account'}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {displayError && (
                <Alert variant="destructive" className="bg-red-500/10 border-red-500/50 text-red-400">
                  <AlertDescription>{displayError}</AlertDescription>
                </Alert>
              )}

              {isRegister && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fullName" className="text-[var(--text-primary)]">Full Name</Label>
                    <Input
                      id="fullName"
                      data-testid="register-fullname-input"
                      placeholder="John Smith"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="companyName" className="text-[var(--text-primary)]">Company Name <span className="text-[var(--text-secondary)]">(optional)</span></Label>
                    <Input
                      id="companyName"
                      data-testid="register-company-input"
                      placeholder="Your Sign Company"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                    />
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" className="text-[var(--text-primary)]">Email</Label>
                <Input
                  id="email"
                  data-testid="auth-email-input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-[var(--text-primary)]">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    data-testid="auth-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-[var(--text-primary)]">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    data-testid="register-confirm-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)] placeholder:text-[var(--text-secondary)]"
                  />
                </div>
              )}
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                data-testid={isRegister ? 'register-submit-btn' : 'login-submit-btn'}
                className="w-full bg-teal-500 hover:bg-teal-600 text-white"
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
                  className="text-sm text-teal-400 hover:text-teal-300 hover:underline"
                >
                  {isRegister
                    ? 'Already have an account? Sign in'
                    : "Don't have an account? Create one"}
                </button>
              </div>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs text-[var(--text-secondary)] mt-6">
          &copy; {new Date().getFullYear()} Sign Guy AI. All rights reserved.
        </p>
      </div>
    </div>
  );
}
