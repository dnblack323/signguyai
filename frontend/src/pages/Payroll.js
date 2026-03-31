import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import { formatCurrency, formatDate } from '../lib/utils';
import {
  DollarSign, Plus, TrendingUp, TrendingDown, Minus, AlertTriangle,
  Clock, Users, CalendarDays, Edit2, Trash2, Briefcase, Timer, Loader2
} from 'lucide-react';
import { toast } from 'sonner';

const TASK_TYPES = [
  { value: 'general', label: 'General' },
  { value: 'design', label: 'Design' },
  { value: 'production', label: 'Production' },
  { value: 'installation', label: 'Installation' },
  { value: 'admin', label: 'Admin' },
];

const TRANSACTION_TYPES = ['earnings', 'advance', 'payment'];

function StatCard({ label, value, icon: Icon, color = 'text-blue-600', bgColor = 'bg-blue-500/10' }) {
  return (
    <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
            <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
          </div>
          <div className={`w-10 h-10 rounded-lg ${bgColor} flex items-center justify-center`}>
            <Icon className={`h-5 w-5 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Payroll() {
  const { hasPermission } = useAuth();
  const canViewPayroll = hasPermission(Permission.PAYROLL_VIEW);
  const canEditPayroll = hasPermission(Permission.PAYROLL_EDIT);
  
  const { employees, fetchEmployees, api } = useApp();
  
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(() => searchParams.get('tab') || 'overview');
  
  // Overview state
  const [payPeriod, setPayPeriod] = useState(null);
  const [periodType, setPeriodType] = useState('weekly');
  
  // Timesheet state
  const [timesheet, setTimesheet] = useState(null);
  const [timesheetRange, setTimesheetRange] = useState({
    start: getWeekStart(),
    end: getWeekEnd()
  });
  const [selectedEmployee, setSelectedEmployee] = useState('all');
  
  // Manual hours state
  const [manualHours, setManualHours] = useState([]);
  const [timeclockShifts, setTimeclockShifts] = useState([]);
  const [showAddHours, setShowAddHours] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [editingShift, setEditingShift] = useState(null);
  const [showEditShift, setShowEditShift] = useState(false);
  const [hoursForm, setHoursForm] = useState({
    employee_id: '', date: new Date().toISOString().split('T')[0],
    hours: '', description: '', job_id: '', task_type: 'general'
  });
  const [shiftForm, setShiftForm] = useState({ date: new Date().toISOString().split('T')[0], clock_in_time: '08:00', clock_out_time: '17:00', break_minutes: '0', notes: '' });
  
  // Transactions state
  const [transactions, setTransactions] = useState([]);
  const [txnEmployee, setTxnEmployee] = useState('');
  const [showAddTxn, setShowAddTxn] = useState(false);
  const [txnForm, setTxnForm] = useState({
    employee_id: '', type: 'earnings', amount: '',
    description: '', date: new Date().toISOString().split('T')[0]
  });
  
  // Jobs for dropdown
  const [jobs, setJobs] = useState([]);

  function getWeekStart() {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff)).toISOString().split('T')[0];
  }
  
  function getWeekEnd() {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? 0 : 7);
    return new Date(d.setDate(diff)).toISOString().split('T')[0];
  }

  const loadPayPeriod = useCallback(async () => {
    try {
      const res = await api.get('/payroll/pay-period', { params: { period_type: periodType } });
      setPayPeriod(res.data);
    } catch (err) { console.error('Error loading pay period:', err); }
  }, [api, periodType]);

  const loadTimesheet = useCallback(async () => {
    try {
      const params = { start_date: timesheetRange.start, end_date: timesheetRange.end };
      if (selectedEmployee !== 'all') params.employee_id = selectedEmployee;
      const res = await api.get('/payroll/timesheet', { params });
      setTimesheet(res.data);
    } catch (err) { console.error('Error loading timesheet:', err); }
  }, [api, timesheetRange, selectedEmployee]);

  const loadManualHours = useCallback(async () => {
    try {
      const res = await api.get('/payroll/hours', { params: { start_date: timesheetRange.start, end_date: timesheetRange.end } });
      setManualHours(res.data);
    } catch (err) { console.error('Error loading hours:', err); }
  }, [api, timesheetRange]);

  const loadTimeclockShifts = useCallback(async () => {
    try {
      const res = await api.get('/payroll/timeclock-shifts', { params: { start_date: timesheetRange.start, end_date: timesheetRange.end } });
      setTimeclockShifts(res.data);
    } catch (err) { console.error('Error loading timeclock shifts:', err); }
  }, [api, timesheetRange]);

  const loadTransactions = useCallback(async () => {
    try {
      const params = {};
      if (txnEmployee && txnEmployee !== 'all') params.employee_id = txnEmployee;
      const res = await api.get('/payroll/transactions', { params });
      setTransactions(res.data);
    } catch (err) { console.error('Error loading transactions:', err); }
  }, [api, txnEmployee]);

  const loadJobs = useCallback(async () => {
    try {
      const res = await api.get('/jobs');
      setJobs(Array.isArray(res.data) ? res.data : res.data.jobs || []);
    } catch { /* ignore */ }
  }, [api]);

  useEffect(() => {
    if (!canViewPayroll) return;
    setLoading(true);
    Promise.all([fetchEmployees(), loadJobs()]).finally(() => setLoading(false));
  }, [canViewPayroll, fetchEmployees, loadJobs]);

  useEffect(() => { if (canViewPayroll) loadPayPeriod(); }, [canViewPayroll, loadPayPeriod]);
  useEffect(() => { if (canViewPayroll) loadTimesheet(); }, [canViewPayroll, loadTimesheet]);
  useEffect(() => { if (canViewPayroll) loadManualHours(); }, [canViewPayroll, loadManualHours]);
  useEffect(() => { if (canViewPayroll) loadTimeclockShifts(); }, [canViewPayroll, loadTimeclockShifts]);
  useEffect(() => { if (canViewPayroll) loadTransactions(); }, [canViewPayroll, loadTransactions]);

  if (!canViewPayroll) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4 text-amber-500" />
        <h2 className="text-xl font-semibold mb-2 text-white">Access Denied</h2>
        <p className="text-gray-500">You don't have permission to view payroll.</p>
      </div>
    );
  }

  // Manual hours handlers
  const handleAddHours = async (e) => {
    e.preventDefault();
    if (!hoursForm.employee_id || !hoursForm.hours) {
      toast.error('Employee and hours are required');
      return;
    }
    try {
      const payload = { ...hoursForm, hours: parseFloat(hoursForm.hours) };
      if (!payload.job_id) delete payload.job_id;
      
      if (editingEntry) {
        await api.put(`/payroll/hours/${editingEntry.id}`, {
          hours: payload.hours, description: payload.description,
          task_type: payload.task_type, date: payload.date
        });
        toast.success('Hours updated');
      } else {
        await api.post('/payroll/hours', payload);
        toast.success('Hours added');
      }
      setShowAddHours(false);
      setEditingEntry(null);
      setHoursForm({ employee_id: '', date: new Date().toISOString().split('T')[0], hours: '', description: '', job_id: '', task_type: 'general' });
      loadManualHours();
      loadTimeclockShifts();
      loadTimesheet();
      loadPayPeriod();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save hours');
    }
  };

  const handleDeleteHours = async (id) => {
    if (!window.confirm('Delete this hours entry?')) return;
    try {
      await api.delete(`/payroll/hours/${id}`);
      toast.success('Hours entry deleted');
      loadManualHours();
      loadTimeclockShifts();
      loadTimesheet();
      loadPayPeriod();
    } catch { toast.error('Failed to delete'); }
  };

  const handleEditHours = (entry) => {
    setEditingEntry(entry);
    setHoursForm({
      employee_id: entry.employee_id,
      date: entry.date, hours: String(entry.hours),
      description: entry.description || '', job_id: entry.job_id || '',
      task_type: entry.task_type || 'general'
    });
    setShowAddHours(true);
  };

  const handleEditShift = (entry) => {
    setEditingShift(entry);
    setShiftForm({
      date: entry.date,
      clock_in_time: entry.clock_in ? entry.clock_in.slice(11, 16) : '08:00',
      clock_out_time: entry.clock_out ? entry.clock_out.slice(11, 16) : '17:00',
      break_minutes: String(entry.break_minutes || 0),
      notes: entry.description || '',
    });
    setShowEditShift(true);
  };

  const handleSaveShift = async (e) => {
    e.preventDefault();
    if (!editingShift) return;
    try {
      await api.put(`/payroll/timeclock-shifts/${editingShift.id}`, {
        clock_in: `${shiftForm.date}T${shiftForm.clock_in_time}:00`,
        clock_out: `${shiftForm.date}T${shiftForm.clock_out_time}:00`,
        break_minutes: parseFloat(shiftForm.break_minutes || 0),
        notes: shiftForm.notes,
      });
      toast.success('Time clock shift updated');
      setShowEditShift(false);
      setEditingShift(null);
      loadTimeclockShifts();
      loadTimesheet();
      loadPayPeriod();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update shift');
    }
  };

  // Transaction handlers
  const handleAddTransaction = async (e) => {
    e.preventDefault();
    if (!txnForm.employee_id || !txnForm.amount) {
      toast.error('Employee and amount are required');
      return;
    }
    try {
      await api.post('/payroll/transactions', { ...txnForm, amount: parseFloat(txnForm.amount) });
      toast.success('Transaction recorded');
      setShowAddTxn(false);
      setTxnForm({ employee_id: '', type: 'earnings', amount: '', description: '', date: new Date().toISOString().split('T')[0] });
      loadTransactions();
      loadPayPeriod();
    } catch { toast.error('Failed to record transaction'); }
  };

  const getTypeIcon = (type) => {
    if (type === 'earnings') return <TrendingUp className="h-3.5 w-3.5 text-green-600" />;
    if (type === 'advance') return <Minus className="h-3.5 w-3.5 text-amber-600" />;
    return <TrendingDown className="h-3.5 w-3.5 text-blue-600" />;
  };

  const totals = payPeriod?.totals || {};
  const combinedEntries = [
    ...timeclockShifts.map((entry) => ({
      ...entry,
      source: 'time_clock',
      employee_name: employees.find((emp) => emp.id === entry.employee_id)?.name || entry.employee_id,
      hours: entry.net_hours,
      gross_pay: (employees.find((emp) => emp.id === entry.employee_id)?.hourly_rate || 0) * (entry.net_hours || 0),
      task_type: 'time_clock',
      description: entry.notes || '',
    })),
    ...manualHours.map((entry) => ({ ...entry, source: 'manual', employee_name: employees.find((emp) => emp.id === entry.employee_id)?.name || entry.employee_id })),
  ].sort((a, b) => `${b.date}${b.clock_in || ''}`.localeCompare(`${a.date}${a.clock_in || ''}`));

  return (
    <div className="space-y-6 animate-fade-in" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Admin Payroll</h1>
          <p className="text-gray-500 mt-1">
            {payPeriod ? `Pay Period: ${payPeriod.period_start} to ${payPeriod.period_end}` : 'Manage employee hours, pay & transactions'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={periodType} onValueChange={setPeriodType}>
            <SelectTrigger className="w-[140px]" data-testid="period-type-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="weekly">Weekly</SelectItem>
              <SelectItem value="biweekly">Bi-Weekly</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Total Hours" value={totals.total_hours || 0} icon={Clock} color="text-blue-600" bgColor="bg-blue-500/10" />
        <StatCard label="Regular Hours" value={totals.regular_hours || 0} icon={Timer} color="text-green-600" bgColor="bg-green-500/10" />
        <StatCard label="Overtime Hours" value={totals.overtime_hours || 0} icon={AlertTriangle} color="text-amber-600" bgColor="bg-amber-500/10" />
        <StatCard label="Gross Pay" value={formatCurrency(totals.gross_pay || 0)} icon={DollarSign} color="text-emerald-600" bgColor="bg-emerald-500/10" />
        <StatCard label="Net Owed" value={formatCurrency(totals.net_owed || 0)} icon={TrendingUp} color="text-purple-600" bgColor="bg-purple-500/10" />
      </div>

      {/* Tabbed Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-800/50 border border-gray-200">
          <TabsTrigger value="overview" data-testid="tab-overview">
            <Users className="h-4 w-4 mr-1.5" /> Overview
          </TabsTrigger>
          <TabsTrigger value="timesheet" data-testid="tab-timesheet">
            <CalendarDays className="h-4 w-4 mr-1.5" /> Time Sheets
          </TabsTrigger>
          <TabsTrigger value="hours" data-testid="tab-hours">
            <Clock className="h-4 w-4 mr-1.5" /> Time Entries
          </TabsTrigger>
          <TabsTrigger value="transactions" data-testid="tab-transactions">
            <DollarSign className="h-4 w-4 mr-1.5" /> Transactions
          </TabsTrigger>
          <TabsTrigger value="schedule" data-testid="tab-schedule">
            <CalendarDays className="h-4 w-4 mr-1.5" /> Schedule
          </TabsTrigger>
        </TabsList>

        {/* OVERVIEW TAB */}
        <TabsContent value="overview">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Pay Period Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {!payPeriod?.employees?.length ? (
                <p className="text-gray-500 text-center py-8">No employees found. Add employees first.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead className="text-right">Rate</TableHead>
                      <TableHead className="text-right">Hours</TableHead>
                      <TableHead className="text-right">OT</TableHead>
                      <TableHead className="text-right">Gross Pay</TableHead>
                      <TableHead className="text-right">Advances</TableHead>
                      <TableHead className="text-right">Paid</TableHead>
                      <TableHead className="text-right">Net Owed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payPeriod.employees.map((emp) => (
                      <TableRow key={emp.employee_id} data-testid={`overview-row-${emp.employee_id}`}>
                        <TableCell className="font-medium">{emp.employee_name}</TableCell>
                        <TableCell className="text-right text-gray-500">{formatCurrency(emp.hourly_rate)}/hr</TableCell>
                        <TableCell className="text-right">{emp.total_hours}</TableCell>
                        <TableCell className="text-right">
                          {emp.overtime_hours > 0 ? (
                            <Badge variant="outline" className="text-amber-600 border-amber-400/30">{emp.overtime_hours} hrs</Badge>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="text-right text-green-600 font-medium">{formatCurrency(emp.gross_pay)}</TableCell>
                        <TableCell className="text-right text-amber-600">{formatCurrency(emp.advances)}</TableCell>
                        <TableCell className="text-right text-blue-600">{formatCurrency(emp.payments_made)}</TableCell>
                        <TableCell className={`text-right font-bold ${emp.net_owed >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {formatCurrency(emp.net_owed)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TIMESHEET TAB */}
        <TabsContent value="timesheet">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <CardTitle className="text-lg">Consolidated Time Sheet</CardTitle>
                <div className="flex items-center gap-2 flex-wrap">
                  <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                    <SelectTrigger className="w-[180px]" data-testid="timesheet-employee-filter">
                      <SelectValue placeholder="All Employees" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Employees</SelectItem>
                      {employees.map((emp) => (
                        <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input type="date" value={timesheetRange.start}
                    onChange={(e) => setTimesheetRange(prev => ({ ...prev, start: e.target.value }))}
                    className="w-[145px]" data-testid="timesheet-start-date" />
                  <span className="text-gray-500 text-sm">to</span>
                  <Input type="date" value={timesheetRange.end}
                    onChange={(e) => setTimesheetRange(prev => ({ ...prev, end: e.target.value }))}
                    className="w-[145px]" data-testid="timesheet-end-date" />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {!timesheet?.employees?.length ? (
                <p className="text-gray-500 text-center py-8">No time entries found for this period.</p>
              ) : (
                <div className="space-y-6">
                  {timesheet.employees.map((emp) => (
                    <div key={emp.employee_id} className="border border-gray-200 rounded-lg overflow-hidden" data-testid={`timesheet-${emp.employee_id}`}>
                      <div className="p-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{emp.employee_name}</h3>
                          <p className="text-sm text-gray-500">{formatCurrency(emp.hourly_rate)}/hr</p>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="text-center">
                            <p className="text-gray-500">Regular</p>
                            <p className="font-bold text-green-600">{emp.regular_hours} hrs</p>
                          </div>
                          {emp.overtime_hours > 0 && (
                            <div className="text-center">
                              <p className="text-gray-500">Overtime</p>
                              <p className="font-bold text-amber-600">{emp.overtime_hours} hrs</p>
                            </div>
                          )}
                          <div className="text-center">
                            <p className="text-gray-500">Total Pay</p>
                            <p className="font-bold text-emerald-600">{formatCurrency(emp.total_pay)}</p>
                          </div>
                        </div>
                      </div>
                      {emp.entries.length > 0 && (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Date</TableHead>
                              <TableHead>Source</TableHead>
                              <TableHead>Job</TableHead>
                              <TableHead>Task</TableHead>
                              <TableHead className="text-right">Hours</TableHead>
                              <TableHead className="text-right">Pay</TableHead>
                              <TableHead className="text-right w-16">Edit</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {emp.entries.map((entry, idx) => (
                              <TableRow key={entry.id || idx}>
                                <TableCell className="text-sm">{entry.date}</TableCell>
                                <TableCell>
                                  <Badge variant="outline" className={entry.source === 'job_timer' ? 'text-blue-600 border-blue-400/30' : 'text-purple-600 border-purple-400/30'}>
                                    {entry.source === 'job_timer' ? 'Timer' : 'Manual'}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-sm text-gray-500">{entry.job_name || '-'}</TableCell>
                                <TableCell className="text-sm capitalize">{entry.task_type}</TableCell>
                                <TableCell className="text-right font-medium">{entry.hours}</TableCell>
                                <TableCell className="text-right text-green-600">{formatCurrency(entry.pay)}</TableCell>
                                <TableCell className="text-right">
                                  {canEditPayroll && (
                                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => entry.source === 'time_clock' ? handleEditShift(entry) : handleEditHours(entry)} data-testid={`edit-timesheet-${entry.id}`}>
                                      <Edit2 className="h-3.5 w-3.5 text-gray-400 hover:text-violet-600" />
                                    </Button>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* MANUAL HOURS TAB */}
        <TabsContent value="hours">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Time Entries</CardTitle>
                <Button onClick={() => { setEditingEntry(null); setHoursForm({ employee_id: '', date: new Date().toISOString().split('T')[0], hours: '', description: '', job_id: '', task_type: 'general' }); setShowAddHours(true); }} data-testid="add-hours-btn">
                  <Plus className="h-4 w-4 mr-1.5" /> Add Hours
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {combinedEntries.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No time entries found. Add manual hours or use the employee time clock.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Employee</TableHead>
                      <TableHead>Task</TableHead>
                      <TableHead>Job</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Hours</TableHead>
                      <TableHead className="text-right">Pay</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {combinedEntries.map((entry) => {
                      return (
                        <TableRow key={entry.id} data-testid={`hours-row-${entry.id}`}>
                          <TableCell className="text-sm">{entry.date}</TableCell>
                          <TableCell className="font-medium">{entry.employee_name}</TableCell>
                          <TableCell className="capitalize text-sm">{entry.task_type}</TableCell>
                          <TableCell className="text-sm text-gray-500">{entry.job_name || '-'}</TableCell>
                          <TableCell className="text-sm text-gray-500">{entry.source === 'time_clock' ? `${entry.clock_in?.slice(11, 16) || '--:--'} - ${entry.clock_out?.slice(11, 16) || '--:--'} · Break ${entry.break_minutes || 0}m` : entry.description || '-'}</TableCell>
                          <TableCell className="text-right font-medium">{entry.hours}</TableCell>
                          <TableCell className="text-right text-green-600">{formatCurrency(entry.gross_pay)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button variant="ghost" size="sm" onClick={() => entry.source === 'time_clock' ? handleEditShift(entry) : handleEditHours(entry)} data-testid={`edit-hours-${entry.id}`}>
                                <Edit2 className="h-3.5 w-3.5" />
                              </Button>
                              {entry.source !== 'time_clock' && <Button variant="ghost" size="sm" onClick={() => handleDeleteHours(entry.id)} data-testid={`delete-hours-${entry.id}`}>
                                <Trash2 className="h-3.5 w-3.5 text-red-600" />
                              </Button>}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TRANSACTIONS TAB */}
        <TabsContent value="transactions">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <CardTitle className="text-lg">Payroll Transactions</CardTitle>
                <div className="flex items-center gap-2">
                  <Select value={txnEmployee} onValueChange={setTxnEmployee}>
                    <SelectTrigger className="w-[180px]" data-testid="txn-employee-filter">
                      <SelectValue placeholder="All Employees" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Employees</SelectItem>
                      {employees.map((emp) => (
                        <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button onClick={() => { setTxnForm({ employee_id: '', type: 'earnings', amount: '', description: '', date: new Date().toISOString().split('T')[0] }); setShowAddTxn(true); }} data-testid="add-transaction-btn">
                    <Plus className="h-4 w-4 mr-1.5" /> Add Transaction
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {transactions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No transactions found.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Employee</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((txn) => {
                      const emp = employees.find(e => e.id === txn.employee_id);
                      const typeColor = txn.type === 'earnings' ? 'text-green-600' : txn.type === 'advance' ? 'text-amber-600' : 'text-blue-600';
                      return (
                        <TableRow key={txn.id} data-testid={`txn-row-${txn.id}`}>
                          <TableCell className="text-sm">{formatDate(txn.date)}</TableCell>
                          <TableCell className="font-medium">{emp?.name || txn.employee_id}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1.5">
                              {getTypeIcon(txn.type)}
                              <span className="capitalize text-sm">{txn.type}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-gray-500">{txn.description || '-'}</TableCell>
                          <TableCell className={`text-right font-bold ${typeColor}`}>{formatCurrency(txn.amount)}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Balance Info Card */}
          <Card className="bg-white border-gray-200 mt-4">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-blue-600" /> Balance Formula
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex items-center gap-3">
                <Badge className="bg-green-500/20 text-green-600">Earnings</Badge>
                <span className="text-gray-500">Hours x Rate = Money owed to employee</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-amber-500/20 text-amber-600">Advances</Badge>
                <span className="text-gray-500">Money borrowed by employee (reduces balance)</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-blue-500/20 text-blue-600">Payments</Badge>
                <span className="text-gray-500">Wages paid to employee (reduces balance)</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SCHEDULE TAB */}
        <TabsContent value="schedule">
          <ScheduleTab employees={employees} api={api} canEdit={canEditPayroll} />
        </TabsContent>
      </Tabs>

      {/* Add/Edit Hours Dialog */}
      <Dialog open={showAddHours} onOpenChange={setShowAddHours}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader>
            <DialogTitle>{editingEntry ? 'Edit Hours' : 'Add Manual Hours'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddHours} className="space-y-4">
            <div className="space-y-2">
              <Label>Employee *</Label>
              <Select value={hoursForm.employee_id} onValueChange={(val) => setHoursForm({ ...hoursForm, employee_id: val })} disabled={!!editingEntry}>
                <SelectTrigger data-testid="hours-employee-select"><SelectValue placeholder="Select employee" /></SelectTrigger>
                <SelectContent>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>{emp.name} ({formatCurrency(emp.hourly_rate)}/hr)</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Date *</Label>
                <Input type="date" value={hoursForm.date}
                  onChange={(e) => setHoursForm({ ...hoursForm, date: e.target.value })}
                  data-testid="hours-date-input" />
              </div>
              <div className="space-y-2">
                <Label>Hours *</Label>
                <Input type="number" step="0.25" min="0" placeholder="0.00"
                  value={hoursForm.hours}
                  onChange={(e) => setHoursForm({ ...hoursForm, hours: e.target.value })}
                  data-testid="hours-amount-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Task Type</Label>
              <Select value={hoursForm.task_type} onValueChange={(val) => setHoursForm({ ...hoursForm, task_type: val })}>
                <SelectTrigger data-testid="hours-task-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TASK_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Job (optional)</Label>
              <Select value={hoursForm.job_id || 'none'} onValueChange={(val) => setHoursForm({ ...hoursForm, job_id: val === 'none' ? '' : val })}>
                <SelectTrigger data-testid="hours-job-select"><SelectValue placeholder="No job" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No job</SelectItem>
                  {jobs.slice(0, 50).map((j) => (
                    <SelectItem key={j.id} value={j.id}>{j.name || j.title || j.id}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input value={hoursForm.description} placeholder="Optional notes"
                onChange={(e) => setHoursForm({ ...hoursForm, description: e.target.value })}
                data-testid="hours-description-input" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowAddHours(false)}>Cancel</Button>
              <Button type="submit" data-testid="hours-submit-btn">{editingEntry ? 'Update' : 'Add Hours'}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Transaction Dialog */}
      <Dialog open={showAddTxn} onOpenChange={setShowAddTxn}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>New Transaction</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddTransaction} className="space-y-4">
            <div className="space-y-2">
              <Label>Employee *</Label>
              <Select value={txnForm.employee_id} onValueChange={(val) => setTxnForm({ ...txnForm, employee_id: val })}>
                <SelectTrigger data-testid="txn-employee-select"><SelectValue placeholder="Select employee" /></SelectTrigger>
                <SelectContent>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Type *</Label>
                <Select value={txnForm.type} onValueChange={(val) => setTxnForm({ ...txnForm, type: val })}>
                  <SelectTrigger data-testid="txn-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {TRANSACTION_TYPES.map((t) => (
                      <SelectItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Amount *</Label>
                <Input type="number" step="0.01" min="0" placeholder="0.00"
                  value={txnForm.amount}
                  onChange={(e) => setTxnForm({ ...txnForm, amount: e.target.value })}
                  data-testid="txn-amount-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Date</Label>
              <Input type="date" value={txnForm.date}
                onChange={(e) => setTxnForm({ ...txnForm, date: e.target.value })}
                data-testid="txn-date-input" />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Input value={txnForm.description} placeholder="Optional notes"
                onChange={(e) => setTxnForm({ ...txnForm, description: e.target.value })}
                data-testid="txn-description-input" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowAddTxn(false)}>Cancel</Button>
              <Button type="submit" data-testid="txn-submit-btn">Record</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={showEditShift} onOpenChange={setShowEditShift}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>Edit Time Clock Shift</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSaveShift} className="space-y-4">
            <div className="space-y-2">
              <Label>Date</Label>
              <Input type="date" value={shiftForm.date} onChange={(e) => setShiftForm((prev) => ({ ...prev, date: e.target.value }))} data-testid="shift-date-input" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Clock In</Label>
                <Input type="time" value={shiftForm.clock_in_time} onChange={(e) => setShiftForm((prev) => ({ ...prev, clock_in_time: e.target.value }))} data-testid="shift-clock-in-input" />
              </div>
              <div className="space-y-2">
                <Label>Clock Out</Label>
                <Input type="time" value={shiftForm.clock_out_time} onChange={(e) => setShiftForm((prev) => ({ ...prev, clock_out_time: e.target.value }))} data-testid="shift-clock-out-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Break Minutes</Label>
              <Input type="number" min="0" step="1" value={shiftForm.break_minutes} onChange={(e) => setShiftForm((prev) => ({ ...prev, break_minutes: e.target.value }))} data-testid="shift-break-input" />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input value={shiftForm.notes} onChange={(e) => setShiftForm((prev) => ({ ...prev, notes: e.target.value }))} data-testid="shift-notes-input" />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setShowEditShift(false)}>Cancel</Button>
              <Button type="submit" data-testid="shift-submit-btn">Save Shift</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}


function ScheduleTab({ employees, api, canEdit }) {
  const [schedules, setSchedules] = useState({});
  const [editCell, setEditCell] = useState(null);
  const [shiftForm, setShiftForm] = useState({ start: '08:00', end: '17:00', notes: '' });
  const [saving, setSaving] = useState(false);

  const today = new Date();
  const mondayOffset = today.getDay() === 0 ? -6 : 1 - today.getDay();
  const monday = new Date(today);
  monday.setDate(today.getDate() + mondayOffset);
  const weekStart = monday.toISOString().split('T')[0];

  const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
  const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  useEffect(() => {
    api.get(`/payroll/schedule?week_start=${weekStart}`)
      .then(res => {
        const map = {};
        (res.data?.schedules || []).forEach(s => { map[s.employee_id] = s.shifts || {}; });
        setSchedules(map);
      })
      .catch(() => {});
  }, [weekStart]);

  const getShift = (empId, day) => (schedules[empId] || {})[day];

  const openEdit = (empId, day) => {
    if (!canEdit) return;
    const existing = getShift(empId, day);
    setShiftForm({ start: existing?.start || '08:00', end: existing?.end || '17:00', notes: existing?.notes || '' });
    setEditCell({ empId, day });
  };

  const saveShift = async () => {
    if (!editCell) return;
    setSaving(true);
    try {
      await api.post('/payroll/schedule', {
        employee_id: editCell.empId,
        week_start: weekStart,
        day: editCell.day,
        start_time: shiftForm.start,
        end_time: shiftForm.end,
        notes: shiftForm.notes,
      });
      setSchedules(prev => ({
        ...prev,
        [editCell.empId]: {
          ...(prev[editCell.empId] || {}),
          [editCell.day]: { start: shiftForm.start, end: shiftForm.end, notes: shiftForm.notes },
        }
      }));
      setEditCell(null);
    } catch { toast.error('Failed to save'); }
    finally { setSaving(false); }
  };

  const clearShift = async () => {
    if (!editCell) return;
    setSaving(true);
    try {
      await api.post('/payroll/schedule', {
        employee_id: editCell.empId,
        week_start: weekStart,
        day: editCell.day,
        start_time: '',
        end_time: '',
        notes: '',
      });
      setSchedules(prev => {
        const empShifts = { ...(prev[editCell.empId] || {}) };
        delete empShifts[editCell.day];
        return { ...prev, [editCell.empId]: empShifts };
      });
      setEditCell(null);
    } catch { toast.error('Failed to clear'); }
    finally { setSaving(false); }
  };

  return (
    <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">Employee Schedule — Week of {weekStart}</CardTitle>
      </CardHeader>
      <CardContent>
        {employees.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No employees. Add employees in User Management.</p>
        ) : (
          <div className="space-y-2 overflow-x-auto">
            <div className="grid grid-cols-8 gap-1 text-center text-xs font-semibold text-gray-500 uppercase min-w-[700px]">
              <div className="text-left">Employee</div>
              {DAY_LABELS.map(d => <div key={d}>{d}</div>)}
            </div>
            {employees.map(emp => (
              <div key={emp.id} className="grid grid-cols-8 gap-1 items-stretch min-w-[700px]">
                <div className="text-sm font-medium text-gray-900 truncate pr-2 flex items-center">{emp.name}</div>
                {DAYS.map(day => {
                  const shift = getShift(emp.id, day);
                  const hasShift = shift?.start && shift?.end;
                  return (
                    <button key={day} onClick={() => openEdit(emp.id, day)} className={`rounded border p-1.5 text-center min-h-[44px] transition-colors ${hasShift ? 'bg-violet-50 border-violet-300 hover:bg-violet-100' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'} ${canEdit ? 'cursor-pointer' : 'cursor-default'}`} data-testid={`schedule-${emp.id}-${day}`}>
                      {hasShift ? (
                        <div>
                          <p className="text-xs font-medium text-violet-700">{shift.start}-{shift.end}</p>
                          {shift.notes && <p className="text-[10px] text-gray-500 truncate">{shift.notes}</p>}
                        </div>
                      ) : <span className="text-xs text-gray-300">—</span>}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        )}

        {/* Edit shift dialog */}
        <Dialog open={!!editCell} onOpenChange={() => setEditCell(null)}>
          <DialogContent className="sm:max-w-[350px]">
            <DialogHeader>
              <DialogTitle>Set Shift{editCell ? ` — ${editCell.day.charAt(0).toUpperCase() + editCell.day.slice(1)}` : ''}</DialogTitle>
              <DialogDescription>{editCell ? (employees.find(e => e.id === editCell.empId)?.name || '') : ''}</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><Label>Start Time</Label><Input type="time" value={shiftForm.start} onChange={e => setShiftForm(p => ({ ...p, start: e.target.value }))} /></div>
                <div><Label>End Time</Label><Input type="time" value={shiftForm.end} onChange={e => setShiftForm(p => ({ ...p, end: e.target.value }))} /></div>
              </div>
              <div><Label>Notes</Label><Input value={shiftForm.notes} onChange={e => setShiftForm(p => ({ ...p, notes: e.target.value }))} placeholder="Optional" /></div>
              <div className="flex gap-2">
                <Button onClick={saveShift} disabled={saving} className="flex-1 bg-violet-600 hover:bg-violet-700 text-white">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null} Save
                </Button>
                <Button variant="outline" onClick={clearShift} disabled={saving} className="text-red-500">Clear</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
