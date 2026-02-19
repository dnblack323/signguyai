import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, LogIn, HardHat, Clock } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function EmployeePortalLogin() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [form, setForm] = useState({ email: '', pin: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_URL}/api/employee-portal/auth/login`, form);
      
      localStorage.setItem('employee_token', response.data.access_token);
      localStorage.setItem('employee_id', response.data.employee_id);
      localStorage.setItem('employee_name', response.data.employee_name);
      localStorage.setItem('employee_tenant_id', response.data.tenant_id);
      navigate('/employee-portal');
    } catch (err) {
      console.error('Login error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.status === 401) {
        setError('Invalid email or PIN');
      } else if (err.response?.status === 403) {
        setError('Your account is inactive. Please contact your manager.');
      } else {
        setError('Unable to connect. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{ backgroundColor: 'var(--bg-primary)' }}
    >
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <img 
              src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/zofnt5d0_sgai%20square.png" 
              alt="SignGuy AI" 
              className="h-20 w-auto"
            />
          </div>
          <h1 className="text-2xl font-bold font-heading" style={{ color: 'var(--text-on-dark)' }}>
            Employee Portal
          </h1>
          <p style={{ color: 'var(--text-muted-on-dark)' }}>
            SignGuy AI - Clock in & manage your work
          </p>
        </div>

        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2" style={{ color: 'var(--text)' }}>
              <LogIn className="h-5 w-5" /> Sign In
            </CardTitle>
            <CardDescription style={{ color: 'var(--text-muted)' }}>
              Enter your email and PIN to access the employee portal
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <Alert variant="destructive" className="bg-red-500/10 border-red-500/50 text-red-500">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email" style={{ color: 'var(--text)' }}>Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                  data-testid="employee-email-input"
                  style={{ 
                    backgroundColor: 'var(--input-bg)', 
                    borderColor: 'var(--border-light)',
                    color: 'var(--text)'
                  }}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="pin" style={{ color: 'var(--text)' }}>PIN</Label>
                <Input
                  id="pin"
                  type="password"
                  placeholder="Enter your 4-6 digit PIN"
                  value={form.pin}
                  onChange={(e) => setForm({ ...form, pin: e.target.value })}
                  required
                  maxLength={6}
                  data-testid="employee-pin-input"
                  style={{ 
                    backgroundColor: 'var(--input-bg)', 
                    borderColor: 'var(--border-light)',
                    color: 'var(--text)'
                  }}
                />
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  Default PIN: 1234 (or last 4 digits of your phone)
                </p>
              </div>

              <Button 
                type="submit" 
                className="w-full text-white"
                disabled={loading}
                data-testid="employee-login-btn"
                style={{ backgroundColor: 'var(--accent)' }}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <Clock className="mr-2 h-4 w-4" />
                    Clock In / Sign In
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                Not an employee?{' '}
                <a 
                  href="/" 
                  className="font-medium hover:underline"
                  style={{ color: 'var(--accent)' }}
                >
                  Admin Login
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted-on-dark)' }}>
          © 2026 SignGuy AI. All rights reserved.
        </p>
      </div>
    </div>
  );
}
