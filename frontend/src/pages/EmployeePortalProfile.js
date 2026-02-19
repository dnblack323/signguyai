import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { 
  User, Mail, Phone, DollarSign, Briefcase, 
  Clock, Shield, Camera, Loader2
} from 'lucide-react';
import { EmployeePortalLayout } from './EmployeePortalDashboard';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount || 0);
};

export default function EmployeePortalProfile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [clockHistory, setClockHistory] = useState([]);
  
  const employeeName = localStorage.getItem('employee_name') || 'Employee';
  const token = localStorage.getItem('employee_token');

  useEffect(() => {
    if (!token) {
      navigate('/employee-portal/login');
      return;
    }
    loadData();
  }, [token, navigate]);

  const loadData = async () => {
    try {
      const [profileRes, historyRes] = await Promise.all([
        axios.get(`${API_URL}/api/employee-portal/profile`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/api/employee-portal/time-clock/history?days=7`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setProfile(profileRes.data);
      setClockHistory(historyRes.data);
    } catch (err) {
      console.error('Failed to load profile:', err);
      if (err.response?.status === 401) {
        navigate('/employee-portal/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDateShort = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getActionLabel = (action) => {
    const labels = {
      start_work: 'Clock In',
      break_start: 'Break Start',
      break_end: 'Break End',
      end_work: 'Clock Out'
    };
    return labels[action] || action;
  };

  const getActionColor = (action) => {
    const colors = {
      start_work: 'bg-green-500/20 text-green-500',
      break_start: 'bg-amber-500/20 text-amber-500',
      break_end: 'bg-blue-500/20 text-blue-500',
      end_work: 'bg-red-500/20 text-red-500'
    };
    return colors[action] || 'bg-gray-500/20 text-gray-500';
  };

  if (loading) {
    return (
      <EmployeePortalLayout employeeName={employeeName}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }}></div>
        </div>
      </EmployeePortalLayout>
    );
  }

  return (
    <EmployeePortalLayout employeeName={employeeName}>
      <div className="space-y-6 pb-24">
        <h2 className="text-2xl font-bold font-heading" style={{ color: 'var(--text)' }}>
          Profile
        </h2>

        {/* Profile Info */}
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 mb-6">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold"
                style={{ backgroundColor: 'var(--accent)', color: 'white' }}
              >
                {profile?.name?.charAt(0) || 'E'}
              </div>
              <div>
                <h3 className="text-xl font-bold" style={{ color: 'var(--text)' }}>
                  {profile?.name}
                </h3>
                <Badge 
                  className="mt-1"
                  style={{ backgroundColor: 'var(--accent-soft)', color: 'var(--accent)' }}
                >
                  {profile?.role || 'Staff'}
                </Badge>
              </div>
            </div>

            <div className="space-y-4">
              {profile?.email && (
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
                  <span style={{ color: 'var(--text)' }}>{profile.email}</span>
                </div>
              )}
              {profile?.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
                  <span style={{ color: 'var(--text)' }}>{profile.phone}</span>
                </div>
              )}
              <div className="flex items-center gap-3">
                <DollarSign className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
                <span style={{ color: 'var(--text)' }}>
                  {formatCurrency(profile?.hourly_rate)}/hour
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Time History */}
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2" style={{ color: 'var(--text)' }}>
              <Clock className="h-5 w-5 text-blue-500" />
              Recent Clock History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {clockHistory.length === 0 ? (
              <p className="text-center py-4" style={{ color: 'var(--text-muted)' }}>
                No recent clock history
              </p>
            ) : (
              <div className="space-y-2">
                {clockHistory.slice(0, 10).map((log) => (
                  <div 
                    key={log.id}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{ backgroundColor: 'var(--surface-2)' }}
                  >
                    <div className="flex items-center gap-3">
                      <Badge className={getActionColor(log.action)}>
                        {getActionLabel(log.action)}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                        {formatTime(log.timestamp)}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {formatDateShort(log.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* App Info */}
        <div 
          className="p-4 rounded-lg text-center text-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text-muted)' }}
        >
          <p>SignGuy AI Employee Portal v1.0</p>
          <p className="mt-1">Need help? Contact your manager.</p>
        </div>
      </div>
    </EmployeePortalLayout>
  );
}
