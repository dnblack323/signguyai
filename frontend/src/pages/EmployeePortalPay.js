import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  DollarSign, TrendingUp, Clock, Calendar, 
  CreditCard, AlertCircle
} from 'lucide-react';
import { EmployeePortalLayout, formatHours } from './EmployeePortalDashboard';
import { getEmployeePortalToken, getEmployeePortalName, getEmployeePortalConfig } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount || 0);
};

export default function EmployeePortalPay() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [paySummary, setPaySummary] = useState(null);
  
  const employeeName = getEmployeePortalName() || 'Employee';
  const token = getEmployeePortalToken();
  const portalConfig = getEmployeePortalConfig();
  const canViewPay = portalConfig?.can_view_pay_stubs !== false;

  useEffect(() => {
    if (!token) {
      navigate('/employee-portal/login');
      return;
    }
    loadPaySummary();
  }, [token, navigate]);

  const loadPaySummary = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/employee-portal/pay/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPaySummary(res.data);
    } catch (err) {
      console.error('Failed to load pay summary:', err);
      if (err.response?.status === 401) {
        navigate('/employee-portal/login');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }}></div>
        </div>
      </EmployeePortalLayout>
    );
  }

  if (!canViewPay) {
    return (
      <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
        <div className="space-y-6 pb-24">
          <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
            <CardContent className="p-8 text-center">
              <AlertCircle className="h-10 w-10 mx-auto mb-3 text-amber-500" />
              <p className="font-medium" style={{ color: 'var(--text)' }}>Pay information is hidden</p>
              <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>Your admin has disabled pay-stub access for this portal account.</p>
            </CardContent>
          </Card>
        </div>
      </EmployeePortalLayout>
    );
  }

  const {
    current_period_earnings = 0,
    current_period_hours = 0,
    ytd_earnings = 0,
    ytd_hours = 0,
    last_payment_date,
    last_payment_amount,
    balance_owed = 0
  } = paySummary || {};

  return (
    <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
      <div className="space-y-6 pb-24">
        <h2 className="text-2xl font-bold font-heading" style={{ color: 'var(--text)' }}>
          My Pay
        </h2>

        {/* Current Period */}
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--text)' }}>
              <Calendar className="h-5 w-5 text-blue-500" />
              Current Pay Period
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold text-green-500">
                  {formatCurrency(current_period_earnings)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Earnings</p>
              </div>
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                  {formatHours(current_period_hours)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Hours Worked</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Balance Owed */}
        {balance_owed > 0 && (
          <Card 
            className="border-amber-500/50"
            style={{ backgroundColor: 'var(--warning-soft)' }}
          >
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-6 w-6 text-amber-500" />
                <div>
                  <p className="font-medium" style={{ color: 'var(--text)' }}>Balance Owed</p>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Pending payment</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-amber-500">
                {formatCurrency(balance_owed)}
              </p>
            </CardContent>
          </Card>
        )}

        {/* YTD Summary */}
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--text)' }}>
              <TrendingUp className="h-5 w-5 text-purple-500" />
              Year-to-Date
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold text-purple-500">
                  {formatCurrency(ytd_earnings)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Total Earnings</p>
              </div>
              <div 
                className="p-4 rounded-lg text-center"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                  {formatHours(ytd_hours)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Total Hours</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Last Payment */}
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--text)' }}>
              <CreditCard className="h-5 w-5 text-green-500" />
              Last Payment
            </CardTitle>
          </CardHeader>
          <CardContent>
            {last_payment_date ? (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium" style={{ color: 'var(--text)' }}>
                    {formatCurrency(last_payment_amount)}
                  </p>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    {new Date(last_payment_date).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                </div>
                <Badge className="bg-green-500/20 text-green-500 border-green-500/50">
                  Paid
                </Badge>
              </div>
            ) : (
              <p className="text-center py-4" style={{ color: 'var(--text-muted)' }}>
                No payment history
              </p>
            )}
          </CardContent>
        </Card>

        {/* Info Note */}
        <div 
          className="p-4 rounded-lg text-sm text-center"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text-muted)' }}
        >
          <p>
            Questions about your pay? Contact your manager.
          </p>
        </div>
      </div>
    </EmployeePortalLayout>
  );
}
