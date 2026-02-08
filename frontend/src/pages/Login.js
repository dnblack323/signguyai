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
    <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#2E2E2E' }}>
      <div className="w-full max-w-md">
        {/* Logo / Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 overflow-hidden" style={{ backgroundColor: 'rgba(47, 139, 251, 0.2)' }}>
            <img 
              src="https://customer-assets.emergentagent.com/job_cc25406f-f7f9-4d81-8429-039b5b2a7159/artifacts/dmeif3yx_1766814558812.png" 
              alt="Sign Guy AI" 
              className="h-12 w-auto"
            />
          </div>
          <h1 className="text-3xl font-bold font-heading" style={{ color: '#F2F2F2' }}>Sign Guy AI</h1>
          <p style={{ color: '#BDBDBD' }} className="mt-2">Sign Shop Operating System</p>
        </div>

        <Card className="border shadow-xl" style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center font-heading" style={{ color: '#1A1A1A' }}>
              {isRegister ? 'Create an account' : 'Welcome back'}
            </CardTitle>
            <CardDescription className="text-center" style={{ color: '#5A5A5A' }}>
              {isRegister
                ? 'Enter your details to get started'
                : 'Enter your credentials to access your account'}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {displayError && (
                <Alert variant="destructive" className="border-red-300" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                  <AlertDescription className="text-red-600">{displayError}</AlertDescription>
                </Alert>
              )}

              {isRegister && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fullName" style={{ color: '#1A1A1A' }}>Full Name</Label>
                    <Input
                      id="fullName"
                      data-testid="register-fullname-input"
                      placeholder="John Smith"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="companyName" style={{ color: '#1A1A1A' }}>
                      Company Name <span style={{ color: '#5A5A5A' }}>(optional)</span>
                    </Label>
                    <Input
                      id="companyName"
                      data-testid="register-company-input"
                      placeholder="Your Sign Company"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                    />
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" style={{ color: '#1A1A1A' }}>Email</Label>
                <Input
                  id="email"
                  data-testid="auth-email-input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" style={{ color: '#1A1A1A' }}>Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    data-testid="auth-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pr-10"
                    style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 hover:opacity-70"
                    style={{ color: '#5A5A5A' }}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" style={{ color: '#1A1A1A' }}>Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    data-testid="register-confirm-password-input"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                  />
                </div>
              )}

              {/* Remember Me - Only show for login */}
              {!isRegister && (
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
                    style={{ color: '#5A5A5A' }}
                  >
                    Remember me for 30 days
                  </Label>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                data-testid={isRegister ? 'register-submit-btn' : 'login-submit-btn'}
                className="w-full text-white font-medium"
                style={{ backgroundColor: '#2F8BFB' }}
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
                  style={{ color: '#2F8BFB' }}
                >
                  {isRegister
                    ? 'Already have an account? Sign in'
                    : "Don't have an account? Create one"}
                </button>
              </div>
            </CardFooter>
          </form>
        </Card>

        <p className="text-center text-xs mt-6" style={{ color: '#BDBDBD' }}>
          &copy; {new Date().getFullYear()} Sign Guy AI. All rights reserved.
        </p>
      </div>
    </div>
  );
}
