import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Loader2, LogIn, UserPlus, Building2 } from 'lucide-react';
import { setPortalToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PortalLogin() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ email: '', password: '', confirmPassword: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_URL}/api/portal/auth/login`, loginForm);
      
      setPortalToken(response.data.access_token);
      localStorage.setItem('portal_customer_id', response.data.customer_id);
      localStorage.setItem('portal_customer_name', response.data.customer_name);
      navigate('/customer-portal');
    } catch (err) {
      console.error('Login error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 401) {
        setError('Invalid email or password');
      } else if (err.response?.status === 403) {
        setError('Portal access is not enabled for this account');
      } else {
        setError('Unable to connect. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (registerForm.password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/portal/auth/register`, {
        email: registerForm.email,
        password: registerForm.password
      });
      
      setPortalToken(response.data.access_token);
      localStorage.setItem('portal_customer_id', response.data.customer_id);
      localStorage.setItem('portal_customer_name', response.data.customer_name);
      navigate('/customer-portal');
    } catch (err) {
      console.error('Registration error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-teal-500/20 mb-4">
            <Building2 className="h-8 w-8 text-teal-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">Customer Portal</h1>
          <p className="text-slate-400 mt-2">Access your orders, quotes, and more</p>
        </div>

        <Card className="border-slate-700 bg-slate-800/50 backdrop-blur">
          <CardHeader className="pb-4">
            <CardTitle className="text-white text-lg">Welcome Back</CardTitle>
            <CardDescription className="text-slate-400">
              Sign in to your customer account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2 bg-transparent border-b border-slate-600 rounded-none h-auto p-0">
                <TabsTrigger 
                  value="login" 
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-500 data-[state=active]:bg-transparent data-[state=active]:text-teal-400 text-slate-400 hover:text-slate-200 py-3"
                >
                  Sign In
                </TabsTrigger>
                <TabsTrigger 
                  value="register" 
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-500 data-[state=active]:bg-transparent data-[state=active]:text-teal-400 text-slate-400 hover:text-slate-200 py-3"
                >
                  Register
                </TabsTrigger>
              </TabsList>

              {error && (
                <Alert variant="destructive" className="mt-4 bg-red-500/10 border-red-500/50">
                  <AlertDescription className="text-red-400">{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="mt-4 bg-green-500/10 border-green-500/50">
                  <AlertDescription className="text-green-400">{success}</AlertDescription>
                </Alert>
              )}

              <TabsContent value="login" className="mt-4">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-slate-300">Email</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="your@email.com"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                      data-testid="portal-login-email"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-slate-300">Password or Temporary PIN</Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="Enter your password or invite PIN"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                      data-testid="portal-login-password"
                    />
                    <p className="text-xs text-slate-500">If you were invited by the shop, use the temporary PIN from the invitation email and change it after login.</p>
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-teal-500 hover:bg-teal-600 text-white"
                    disabled={loading}
                    data-testid="portal-login-submit"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <LogIn className="h-4 w-4 mr-2" />}
                    Sign In
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-4">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-email" className="text-slate-300">Email</Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="your@email.com"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                      data-testid="portal-register-email"
                    />
                    <p className="text-xs text-slate-500">Use the email address on file with the sign shop</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password" className="text-slate-300">Create Password</Label>
                    <Input
                      id="register-password"
                      type="password"
                      placeholder="Min 6 characters"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                      data-testid="portal-register-password"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-confirm" className="text-slate-300">Confirm Password</Label>
                    <Input
                      id="register-confirm"
                      type="password"
                      placeholder="Confirm your password"
                      value={registerForm.confirmPassword}
                      onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                      data-testid="portal-register-confirm"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full bg-teal-500 hover:bg-teal-600 text-white"
                    disabled={loading}
                    data-testid="portal-register-submit"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
                    Create Account
                  </Button>
                </form>
              </TabsContent>
            </Tabs>

            <div className="mt-6 text-center text-sm text-slate-500">
              <p>Need help? Contact your sign shop directly.</p>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-slate-500 text-sm mt-6">
          Powered by SignGuy AI
        </p>
      </div>
    </div>
  );
}
