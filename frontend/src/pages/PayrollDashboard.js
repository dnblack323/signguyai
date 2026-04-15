import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Calendar, Clock, ClipboardList, DollarSign, FileSpreadsheet, Loader2,
  TrendingUp, Users, ArrowRight, AlertTriangle,
} from 'lucide-react';
import { useAuth, Permission } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { getAuthToken } from '../lib/authStorage';
import { formatCurrency } from '../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PayrollDashboard() {
  const { hasPermission, isAdminOrOwner } = useAuth();
  const canView = hasPermission(Permission.PAYROLL_VIEW) || isAdminOrOwner();
  const { employees, fetchEmployees } = useApp();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    const token = getAuthToken();
    if (!token) return;
    setLoading(true);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const weekStart = new Date();
      weekStart.setDate(weekStart.getDate() - weekStart.getDay() + 1);
      const ws = weekStart.toISOString().slice(0, 10);
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekEnd.getDate() + 6);
      const we = weekEnd.toISOString().slice(0, 10);

      const headers = { Authorization: `Bearer ${token}` };
      const [empRes, shiftRes, txnRes] = await Promise.all([
        fetch(`${API}/api/employees`, { headers }).then((r) => r.json()),
        fetch(`${API}/api/payroll/timeclock-shifts?start_date=${ws}&end_date=${we}`, { headers }).then((r) => r.json()).catch(() => []),
        fetch(`${API}/api/payroll/transactions?start_date=${ws}&end_date=${we}`, { headers }).then((r) => r.json()).catch(() => []),
      ]);

      const activeEmps = (empRes || []).filter((e) => e.is_active);
      const clockedIn = (shiftRes || []).filter((s) => s.status === 'working' || s.status === 'on_break');
      const weekShifts = (shiftRes || []).filter((s) => s.status === 'finished');
      const totalWeekHours = weekShifts.reduce((sum, s) => sum + (s.net_hours || s.total_hours || 0), 0);
      const weekEarnings = (txnRes || []).filter((t) => t.type === 'earnings').reduce((sum, t) => sum + (t.amount || 0), 0);
      const weekAdvances = (txnRes || []).filter((t) => t.type === 'advance').reduce((sum, t) => sum + (t.amount || 0), 0);
      const weekPayments = (txnRes || []).filter((t) => t.type === 'payment').reduce((sum, t) => sum + (t.amount || 0), 0);

      setStats({
        totalEmployees: activeEmps.length,
        clockedIn: clockedIn.length,
        weekHours: totalWeekHours.toFixed(1),
        weekShiftCount: weekShifts.length,
        weekEarnings,
        weekAdvances,
        weekPayments,
        weekStart: ws,
        weekEnd: we,
        today,
      });
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canView) { fetchStats(); fetchEmployees(); }
  }, [canView, fetchStats, fetchEmployees]);

  if (!canView) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-xl font-semibold text-gray-900">Access Denied</h2>
        <p className="mt-2 text-gray-500">You do not have permission to view payroll.</p>
      </div>
    );
  }

  if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-violet-500" /></div>;

  return (
    <div className="max-w-6xl mx-auto pb-12" data-testid="payroll-dashboard-page">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900" data-testid="payroll-dashboard-title">Payroll</h1>
        <p className="text-sm text-gray-500">Overview, shortcuts, and this week's summary</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Link to="/timesheets" data-testid="shortcut-timesheets">
          <Card className="hover:border-violet-300 transition-colors cursor-pointer h-full">
            <CardContent className="flex flex-col items-center justify-center p-5 text-center gap-2">
              <FileSpreadsheet className="h-7 w-7 text-violet-600" />
              <p className="text-sm font-semibold text-gray-900">Timesheets</p>
              <p className="text-[11px] text-gray-500">Payroll worksheet & hours</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/employee-schedule" data-testid="shortcut-schedule">
          <Card className="hover:border-violet-300 transition-colors cursor-pointer h-full">
            <CardContent className="flex flex-col items-center justify-center p-5 text-center gap-2">
              <Calendar className="h-7 w-7 text-teal-600" />
              <p className="text-sm font-semibold text-gray-900">Employee Schedule</p>
              <p className="text-[11px] text-gray-500">Work schedules & shifts</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/timeclock" data-testid="shortcut-timeclock">
          <Card className="hover:border-violet-300 transition-colors cursor-pointer h-full">
            <CardContent className="flex flex-col items-center justify-center p-5 text-center gap-2">
              <Clock className="h-7 w-7 text-amber-600" />
              <p className="text-sm font-semibold text-gray-900">Time Clock</p>
              <p className="text-[11px] text-gray-500">Clock in/out & breaks</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/users" data-testid="shortcut-users">
          <Card className="hover:border-violet-300 transition-colors cursor-pointer h-full">
            <CardContent className="flex flex-col items-center justify-center p-5 text-center gap-2">
              <Users className="h-7 w-7 text-blue-600" />
              <p className="text-sm font-semibold text-gray-900">Employees</p>
              <p className="text-[11px] text-gray-500">Manage team members</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* This Week Stats */}
      {stats && (
        <>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-3">This Week ({stats.weekStart} — {stats.weekEnd})</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <Card data-testid="stat-employees">
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Active Employees</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.totalEmployees}</p>
                {stats.clockedIn > 0 && <Badge className="mt-1 bg-green-100 text-green-700 text-[10px]">{stats.clockedIn} clocked in now</Badge>}
              </CardContent>
            </Card>
            <Card data-testid="stat-hours">
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Hours This Week</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.weekHours}</p>
                <p className="text-[11px] text-gray-400">{stats.weekShiftCount} shifts completed</p>
              </CardContent>
            </Card>
            <Card data-testid="stat-earnings">
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Adjustments (Earnings)</p>
                <p className="text-2xl font-bold text-green-700 mt-1">{formatCurrency(stats.weekEarnings)}</p>
              </CardContent>
            </Card>
            <Card data-testid="stat-deductions">
              <CardContent className="p-4">
                <p className="text-xs text-gray-500">Advances & Payments</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrency(stats.weekAdvances + stats.weekPayments)}</p>
              </CardContent>
            </Card>
          </div>

          {/* Employee Quick List */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base text-gray-900">Employees</CardTitle>
                  <CardDescription>Quick access to individual timesheets</CardDescription>
                </div>
                <Link to="/timesheets">
                  <Button variant="outline" size="sm" className="gap-1">Open Timesheets <ArrowRight className="h-3.5 w-3.5" /></Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-gray-100">
                {employees.filter((e) => e.is_active).map((emp) => (
                  <Link key={emp.id} to={`/timesheets?employee=${emp.id}`} className="flex items-center justify-between py-2.5 hover:bg-gray-50 rounded px-2 -mx-2 transition-colors" data-testid={`emp-row-${emp.id}`}>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{emp.name}</p>
                      <p className="text-xs text-gray-400">{emp.title || emp.role}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">{formatCurrency(emp.hourly_rate || 0)}/hr</p>
                    </div>
                  </Link>
                ))}
                {employees.filter((e) => e.is_active).length === 0 && (
                  <p className="text-sm text-gray-400 py-4 text-center">No active employees</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
