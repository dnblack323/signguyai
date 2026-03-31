import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Clock, Play, Pause, Square, Coffee, DollarSign, 
  CheckCircle, ListTodo, LogOut, User, HardHat,
  ChevronRight, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Employee Portal Layout wrapper
const EmployeePortalLayout = ({ children, employeeName, portalConfig }) => {
  const navigate = useNavigate();
  const storedConfig = portalConfig || (() => {
    try {
      return JSON.parse(localStorage.getItem('employee_portal_config') || '{}');
    } catch {
      return {};
    }
  })();
  const canViewTimeClock = storedConfig?.can_view_time_clock !== false;
  const canViewPay = storedConfig?.can_view_pay_stubs !== false;
  const canViewTasks = storedConfig?.can_view_tasks !== false;
  const canEditProfile = storedConfig?.can_edit_profile !== false;

  const handleLogout = () => {
    localStorage.removeItem('employee_token');
    localStorage.removeItem('employee_id');
    localStorage.removeItem('employee_name');
    localStorage.removeItem('employee_tenant_id');
    localStorage.removeItem('employee_portal_config');
    navigate('/employee-portal/login');
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <header 
        className="sticky top-0 z-50 border-b"
        style={{ backgroundColor: 'var(--sidebar-bg)', borderColor: 'var(--border-dark)' }}
      >
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center overflow-hidden">
              <img 
                src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/zofnt5d0_sgai%20square.png" 
                alt="SignGuy AI" 
                className="h-10 w-auto"
              />
            </div>
            <div>
              <h1 className="font-bold font-heading" style={{ color: 'var(--text-on-dark)' }}>
                Employee Portal
              </h1>
              <p className="text-xs" style={{ color: 'var(--text-muted-on-dark)' }}>
                {employeeName}
              </p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleLogout}
            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
          >
            <LogOut className="h-4 w-4 mr-2" /> Sign Out
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav 
        className="fixed bottom-0 left-0 right-0 border-t"
        style={{ backgroundColor: 'var(--sidebar-bg)', borderColor: 'var(--border-dark)' }}
      >
        <div className="max-w-4xl mx-auto px-4 py-2 flex items-center justify-around">
          {canViewTimeClock && <Link to="/employee-portal" className="flex flex-col items-center py-2 px-4">
            <Clock className="h-5 w-5" style={{ color: 'var(--accent)' }} />
            <span className="text-xs mt-1" style={{ color: 'var(--text-on-dark)' }}>Clock</span>
          </Link>}
          {canViewPay && <Link to="/employee-portal/pay" className="flex flex-col items-center py-2 px-4">
            <DollarSign className="h-5 w-5" style={{ color: 'var(--text-muted-on-dark)' }} />
            <span className="text-xs mt-1" style={{ color: 'var(--text-muted-on-dark)' }}>My Pay</span>
          </Link>}
          {canViewTasks && <Link to="/employee-portal/tasks" className="flex flex-col items-center py-2 px-4">
            <ListTodo className="h-5 w-5" style={{ color: 'var(--text-muted-on-dark)' }} />
            <span className="text-xs mt-1" style={{ color: 'var(--text-muted-on-dark)' }}>Tasks</span>
          </Link>}
          {canEditProfile && <Link to="/employee-portal/profile" className="flex flex-col items-center py-2 px-4">
            <User className="h-5 w-5" style={{ color: 'var(--text-muted-on-dark)' }} />
            <span className="text-xs mt-1" style={{ color: 'var(--text-muted-on-dark)' }}>Profile</span>
          </Link>}
        </div>
      </nav>
    </div>
  );
};

// Format time helper
const formatTime = (isoString) => {
  if (!isoString) return '--:--';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
};

// Format hours helper
const formatHours = (hours) => {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return `${h}h ${m}m`;
};

export default function EmployeePortalDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [clockStatus, setClockStatus] = useState(null);
  const [punching, setPunching] = useState(false);
  const [assignedJobs, setAssignedJobs] = useState([]);
  const [workSummary, setWorkSummary] = useState(null);
  const [portalConfig, setPortalConfig] = useState(null);
  
  const employeeName = localStorage.getItem('employee_name') || 'Employee';
  const token = localStorage.getItem('employee_token');

  useEffect(() => {
    if (!token) {
      navigate('/employee-portal/login');
      return;
    }
    loadClockStatus();
  }, [token, navigate]);

  const loadClockStatus = async () => {
    try {
      const [statusRes, jobsRes, summaryRes, configRes] = await Promise.all([
        axios.get(`${API_URL}/api/employee-portal/time-clock/status`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: null })),
        axios.get(`${API_URL}/api/employee-portal/jobs`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] })),
        axios.get(`${API_URL}/api/employee-portal/work-summary`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: null })),
        axios.get(`${API_URL}/api/employee-portal/config`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: {} }))
      ]);
      setClockStatus(statusRes.data);
      setAssignedJobs(jobsRes.data || []);
      setWorkSummary(summaryRes.data);
      setPortalConfig(configRes.data || {});
      localStorage.setItem('employee_portal_config', JSON.stringify(configRes.data || {}));
    } catch (err) {
      console.error('Failed to load clock status:', err);
      if (err.response?.status === 401) {
        navigate('/employee-portal/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePunch = async (action) => {
    setPunching(true);
    try {
      await axios.post(
        `${API_URL}/api/employee-portal/time-clock/punch?action=${action}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`${action.replace('_', ' ')} recorded!`);
      await loadClockStatus();
    } catch (err) {
      toast.error('Failed to record time');
    } finally {
      setPunching(false);
    }
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

  const { is_clocked_in, current_status, clocked_in_at, total_hours_today, break_time_today } = clockStatus || {};
  const canViewTimeClock = portalConfig?.can_view_time_clock !== false;
  const canViewPay = portalConfig?.can_view_pay_stubs !== false;
  const canViewTasks = portalConfig?.can_view_tasks !== false;
  const canSeeJobDetails = portalConfig?.can_see_job_details === true;

  return (
    <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
      <div className="space-y-6 pb-24">
        {/* Greeting */}
        <div className="text-center">
          <h2 className="text-2xl font-bold font-heading" style={{ color: 'var(--text)' }}>
            Hello, {employeeName.split(' ')[0]}!
          </h2>
          <p style={{ color: 'var(--text-muted)' }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>

        {/* Clock Status Card */}
        {canViewTimeClock && (
        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardContent className="pt-6">
            <div className="text-center mb-6">
              <div 
                className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-4 ${
                  is_clocked_in 
                    ? current_status === 'on_break' 
                      ? 'bg-amber-500/20' 
                      : 'bg-green-500/20' 
                    : 'bg-gray-500/20'
                }`}
              >
                {is_clocked_in ? (
                  current_status === 'on_break' ? (
                    <Coffee className="h-12 w-12 text-amber-500" />
                  ) : (
                    <Play className="h-12 w-12 text-green-500" />
                  )
                ) : (
                  <Clock className="h-12 w-12 text-gray-400" />
                )}
              </div>
              
              <Badge 
                className={`text-sm px-4 py-1 ${
                  is_clocked_in 
                    ? current_status === 'on_break'
                      ? 'bg-amber-500/20 text-amber-500 border-amber-500/50'
                      : 'bg-green-500/20 text-green-500 border-green-500/50'
                    : 'bg-gray-500/20 text-gray-400 border-gray-500/50'
                }`}
              >
                {is_clocked_in 
                  ? current_status === 'on_break' 
                    ? 'On Break' 
                    : 'Clocked In'
                  : 'Clocked Out'
                }
              </Badge>

              {is_clocked_in && clocked_in_at && (
                <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
                  Since {formatTime(clocked_in_at)}
                </p>
              )}
            </div>

            {/* Time Stats */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div 
                className="text-center p-4 rounded-lg"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                  {formatHours(total_hours_today || 0)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Hours Worked</p>
              </div>
              <div 
                className="text-center p-4 rounded-lg"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>
                  {formatHours(break_time_today || 0)}
                </p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Break Time</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-3">
              {!is_clocked_in ? (
                <Button 
                  className="col-span-2 h-14 text-lg bg-green-600 hover:bg-green-700 text-white"
                  onClick={() => handlePunch('start_work')}
                  disabled={punching}
                  data-testid="clock-in-btn"
                >
                  <Play className="h-5 w-5 mr-2" /> Clock In
                </Button>
              ) : (
                <>
                  {current_status === 'on_break' ? (
                    <Button 
                      className="col-span-2 h-14 text-lg bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => handlePunch('break_end')}
                      disabled={punching}
                      data-testid="end-break-btn"
                    >
                      <Play className="h-5 w-5 mr-2" /> End Break
                    </Button>
                  ) : (
                    <>
                      <Button 
                        className="h-14 bg-amber-600 hover:bg-amber-700 text-white"
                        onClick={() => handlePunch('break_start')}
                        disabled={punching}
                        data-testid="start-break-btn"
                      >
                        <Coffee className="h-5 w-5 mr-2" /> Break
                      </Button>
                      <Button 
                        className="h-14 bg-red-600 hover:bg-red-700 text-white"
                        onClick={() => handlePunch('end_work')}
                        disabled={punching}
                        data-testid="clock-out-btn"
                      >
                        <Square className="h-5 w-5 mr-2" /> Clock Out
                      </Button>
                    </>
                  )}
                </>
              )}
            </div>
          </CardContent>
        </Card>
        )}

        {/* Quick Links */}
        <div className="grid grid-cols-2 gap-4">
          {canViewPay && <Link to="/employee-portal/pay">
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-green-500" />
                  </div>
                  <span className="font-medium" style={{ color: 'var(--text)' }}>My Pay</span>
                </div>
                <ChevronRight className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
              </CardContent>
            </Card>
          </Link>}
          
          {canViewTasks && <Link to="/employee-portal/tasks">
            <Card 
              className="cursor-pointer hover:shadow-md transition-shadow"
              style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <ListTodo className="h-5 w-5 text-blue-500" />
                  </div>
                  <span className="font-medium" style={{ color: 'var(--text)' }}>My Tasks</span>
                </div>
                <ChevronRight className="h-5 w-5" style={{ color: 'var(--text-muted)' }} />
              </CardContent>
            </Card>
          </Link>}
        </div>

        {canViewTimeClock && <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }} data-testid="employee-work-summary-card">
          <CardHeader>
            <CardTitle style={{ color: 'var(--text)' }}>Personal Work Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }}>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Today’s Completed Stages</p>
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{workSummary?.completed_stages_today || 0}</p>
              </div>
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }}>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Assigned Jobs</p>
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{workSummary?.assigned_jobs_count || assignedJobs.length}</p>
              </div>
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }}>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Hours Today</p>
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{formatHours(workSummary?.today_hours_worked || 0)}</p>
              </div>
              <div className="p-4 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }}>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Hours This Week</p>
                <p className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{formatHours(workSummary?.week_hours_worked || 0)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        }

        {canSeeJobDetails && <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }} data-testid="employee-assigned-jobs-card">
          <CardHeader>
            <CardTitle style={{ color: 'var(--text)' }}>My Assigned Jobs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {assignedJobs.length === 0 ? (
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No jobs assigned right now.</p>
            ) : assignedJobs.map((job) => (
              <Link key={job.id} to={`/employee-portal/jobs/${job.id}`} data-testid={`employee-assigned-job-${job.id}`}>
                <div className="flex items-center justify-between rounded-lg p-4 hover:shadow-sm transition-shadow" style={{ backgroundColor: 'var(--surface-2)' }}>
                  <div>
                    <p className="font-medium" style={{ color: 'var(--text)' }}>{job.job_name}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {job.customer_name} · {job.current_production_stage || 'No active stage'}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge className={job.priority === 'urgent' ? 'bg-red-500/20 text-red-400 border-red-500/40' : 'bg-blue-500/20 text-blue-400 border-blue-500/40'}>
                      {job.priority}
                    </Badge>
                    <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>{job.due_date || 'No due date'}</p>
                  </div>
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
        }
      </div>
    </EmployeePortalLayout>
  );
}

// Export for use in other employee portal pages
export { EmployeePortalLayout, formatTime, formatHours };
