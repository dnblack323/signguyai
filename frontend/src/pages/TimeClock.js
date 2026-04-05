import { useEffect, useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Switch } from '../components/ui/switch';
import { formatTime, cn } from '../lib/utils';
import { Play, Pause, Coffee, Square, Clock, Plus, User, Edit2, Trash2, KeyRound } from 'lucide-react';
import { toast } from 'sonner';

const actionButtons = [
  { action: 'start_work', label: 'Start Work', icon: Play, color: 'bg-green-600 hover:bg-green-700' },
  { action: 'break_start', label: 'Start Break', icon: Coffee, color: 'bg-yellow-600 hover:bg-yellow-700' },
  { action: 'break_end', label: 'End Break', icon: Coffee, color: 'bg-blue-600 hover:bg-blue-700' },
  { action: 'end_work', label: 'End Work', icon: Square, color: 'bg-red-600 hover:bg-red-700' },
];

export default function TimeClock() {
  const { isAdminOrOwner } = useAuth();
  const { 
    employees, fetchEmployees, createEmployee, updateEmployee, api,
    clockAction, getClockStatus, getTodayLogs, getShiftSummary 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [clockStatus, setClockStatus] = useState(null);
  const [todayLogs, setTodayLogs] = useState([]);
  const [shiftSummary, setShiftSummary] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', hourly_rate: '' });
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [employeeForm, setEmployeeForm] = useState({ name: '', email: '', phone: '', hourly_rate: '', role: 'staff', pin: '' });
  const [pinResetEmployee, setPinResetEmployee] = useState(null);
  const [newPin, setNewPin] = useState('');
  const [invitingEmployeeId, setInvitingEmployeeId] = useState('');
  const timeApiRef = useRef({ fetchEmployees, getClockStatus, getTodayLogs, getShiftSummary, clockAction });

  useEffect(() => {
    timeApiRef.current = { fetchEmployees, getClockStatus, getTodayLogs, getShiftSummary, clockAction };
  }, [fetchEmployees, getClockStatus, getTodayLogs, getShiftSummary, clockAction]);

  const loadEmployees = useCallback(async () => {
    setLoading(true);
    await timeApiRef.current.fetchEmployees();
    setLoading(false);
  }, []);

  const loadEmployeeData = useCallback(async (employeeId) => {
    if (!employeeId) return;
    try {
      const [status, logs, summary] = await Promise.all([
        timeApiRef.current.getClockStatus(employeeId),
        timeApiRef.current.getTodayLogs(employeeId),
        timeApiRef.current.getShiftSummary(employeeId)
      ]);
      setClockStatus(status);
      setTodayLogs(logs);
      setShiftSummary(summary);
    } catch (err) {
      console.error('Error loading employee data:', err);
    }
  }, []);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  useEffect(() => {
    if (selectedEmployee) {
      loadEmployeeData(selectedEmployee);
    }
  }, [selectedEmployee, loadEmployeeData]);

  const handleClockAction = async (action) => {
    if (!selectedEmployee) {
      toast.error('Please select an employee');
      return;
    }
    try {
      await timeApiRef.current.clockAction(selectedEmployee, action);
      toast.success(`${action.replace('_', ' ')} recorded`);
      await loadEmployeeData(selectedEmployee);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record action');
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    if (!newEmployee.name.trim()) {
      toast.error('Please enter employee name');
      return;
    }
    try {
      await createEmployee({ ...newEmployee, hourly_rate: parseFloat(newEmployee.hourly_rate || 0) || 0 });
      toast.success('Employee created');
      setNewEmployee({ name: '', hourly_rate: '' });
      setIsDialogOpen(false);
      await loadEmployees();
    } catch (err) {
      toast.error('Failed to create employee');
    }
  };

  const handleSaveEmployee = async (e) => {
    e.preventDefault();
    if (!editingEmployee) return;
    try {
      await updateEmployee(editingEmployee.id, {
        name: employeeForm.name,
        email: employeeForm.email || null,
        phone: employeeForm.phone || null,
        hourly_rate: parseFloat(employeeForm.hourly_rate || 0) || 0,
        role: employeeForm.role,
      });
      toast.success('Employee updated');
      setShowEditDialog(false);
      setEditingEmployee(null);
      await loadEmployees();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update employee');
    }
  };

  const openEditEmployee = (employee) => {
    setEditingEmployee(employee);
    setEmployeeForm({
      name: employee.name || '',
      email: employee.email || '',
      phone: employee.phone || '',
      hourly_rate: employee.hourly_rate ? String(employee.hourly_rate) : '',
      role: employee.role || 'staff',
      pin: employee.pin || '',
    });
    setShowEditDialog(true);
  };

  const handleToggleActive = async (employee) => {
    try {
      await updateEmployee(employee.id, { is_active: !employee.is_active });
      toast.success(`Employee ${employee.is_active ? 'deactivated' : 'reactivated'}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update employee');
    }
  };

  const handleDeleteEmployee = async (employee) => {
    if (!window.confirm(`Delete ${employee.name}? This removes employee-related records from admin tools.`)) return;
    try {
      await api.delete(`/employees/${employee.id}`);
      toast.success('Employee deleted');
      if (selectedEmployee === employee.id) {
        setSelectedEmployee('');
        setClockStatus(null);
        setTodayLogs([]);
        setShiftSummary(null);
      }
      await loadEmployees();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete employee');
    }
  };

  const handleResetPin = async (e) => {
    e.preventDefault();
    if (!pinResetEmployee || !newPin) return;
    try {
      await api.post(`/employees/${pinResetEmployee.id}/reset-pin`, { pin: newPin });
      toast.success('Employee PIN updated');
      setPinResetEmployee(null);
      setNewPin('');
      await loadEmployees();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update PIN');
    }
  };

  const handleInvitePortal = async (employee) => {
    if (!employee.email) {
      toast.error('Add an employee email before sending a portal invite');
      return;
    }
    setInvitingEmployeeId(employee.id);
    try {
      const res = await api.post(`/employees/${employee.id}/invite-portal`, { origin_url: window.location.origin });
      if (res.data.email_sent) {
        toast.success(`Portal invite sent to ${employee.email}. PIN: ${res.data.temporary_pin}`);
      } else {
        toast.success(`Invite prepared. Email service was unavailable, so use PIN ${res.data.temporary_pin} manually.`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to invite employee');
    } finally {
      setInvitingEmployeeId('');
    }
  };

  const getAvailableActions = () => {
    if (!clockStatus) return ['start_work'];
    const validSequences = {
      'not_started': ['start_work'],
      'working': ['break_start', 'end_work'],
      'on_break': ['break_end'],
      'finished': ['start_work']
    };
    return validSequences[clockStatus.status] || ['start_work'];
  };

  const availableActions = getAvailableActions();

  const getStatusBadge = () => {
    if (!clockStatus) return null;
    const statusColors = {
      'not_started': 'bg-gray-500/20 text-gray-400',
      'working': 'bg-green-500/20 text-green-400',
      'on_break': 'bg-yellow-500/20 text-yellow-400',
      'finished': 'bg-blue-500/20 text-blue-400'
    };
    const statusLabels = {
      'not_started': 'Not Started',
      'working': 'Working',
      'on_break': 'On Break',
      'finished': 'Finished'
    };
    return (
      <Badge className={statusColors[clockStatus.status]}>
        {statusLabels[clockStatus.status]}
      </Badge>
    );
  };

  const selectedEmployeeData = employees.find(e => e.id === selectedEmployee);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="timeclock-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight text-gray-900">Time Clock</h1>
          <p className="text-slate-300 mt-1">Track employee work hours</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" data-testid="add-employee-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Employee
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">New Employee</DialogTitle>
              <DialogDescription>Create a new employee for the time clock, payroll, and employee portal system.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddEmployee} className="space-y-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input
                  value={newEmployee.name}
                  onChange={(e) => setNewEmployee({ ...newEmployee, name: e.target.value })}
                  placeholder="Employee name"
                  data-testid="employee-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Hourly Rate</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={newEmployee.hourly_rate}
                  onChange={(e) => setNewEmployee({ ...newEmployee, hourly_rate: e.target.value })}
                  placeholder="0.00"
                  data-testid="employee-rate-input"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="employee-submit-btn">Create</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Employee Selector */}
      <Card className="bg-white border-gray-200">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-gray-500" />
              <Label className="text-base font-medium">Select Employee:</Label>
            </div>
            <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
              <SelectTrigger className="w-[280px]" data-testid="employee-select">
                <SelectValue placeholder="Choose an employee" />
              </SelectTrigger>
              <SelectContent>
                {employees.filter(e => e.is_active).map((emp) => (
                  <SelectItem key={emp.id} value={emp.id}>
                    {emp.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedEmployee && getStatusBadge()}
          </div>
        </CardContent>
      </Card>

      {selectedEmployee && (
        <>
          {/* Clock Actions */}
          <Card className="bg-white border-gray-200">
            <CardHeader>
              <CardTitle className="font-heading uppercase">Clock Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {actionButtons.map(({ action, label, icon: Icon, color }) => {
                  const isAvailable = availableActions.includes(action);
                  return (
                    <Button
                      key={action}
                      onClick={() => handleClockAction(action)}
                      disabled={!isAvailable}
                      className={cn(
                        "h-24 flex flex-col items-center justify-center gap-2 text-gray-900 transition-all",
                        isAvailable ? color : "bg-gray-50 text-gray-500 cursor-not-allowed",
                        isAvailable && "neon-glow"
                      )}
                      data-testid={`clock-${action}`}
                    >
                      <Icon className="h-8 w-8" />
                      <span className="font-bold uppercase tracking-wide">{label}</span>
                    </Button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Daily Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Shift Summary */}
            <Card className="bg-white border-gray-200">
              <CardHeader>
                <CardTitle className="font-heading uppercase flex items-center gap-2">
                  <Clock className="h-5 w-5 text-primary" />
                  Today's Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                {shiftSummary ? (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Work Time</p>
                      <p className="text-2xl font-bold text-green-400">
                        {Math.round(shiftSummary.work_minutes)} min
                      </p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Break Time</p>
                      <p className="text-2xl font-bold text-yellow-400">
                        {Math.round(shiftSummary.break_minutes)} min
                      </p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Net Hours</p>
                      <p className="text-2xl font-bold text-primary">
                        {shiftSummary.net_hours.toFixed(2)} hrs
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>

            {/* Today's Log */}
            <Card className="bg-white border-gray-200">
              <CardHeader>
                <CardTitle className="font-heading uppercase">Today's Activity</CardTitle>
              </CardHeader>
              <CardContent>
                {todayLogs.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No activity today</p>
                ) : (
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {todayLogs.map((log) => (
                      <div 
                        key={log.id} 
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        data-testid={`log-${log.id}`}
                      >
                        <span className="font-medium capitalize">
                          {log.action.replace('_', ' ')}
                        </span>
                        <span className="text-gray-500">
                          {formatTime(log.timestamp)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {!selectedEmployee && employees.length === 0 && !loading && (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <User className="h-12 w-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Employees</h3>
            <p className="text-gray-500 mb-4">Add an employee to start tracking time</p>
            <Button onClick={() => setIsDialogOpen(true)} data-testid="empty-add-employee">
              <Plus className="h-4 w-4 mr-2" /> Add First Employee
            </Button>
          </CardContent>
        </Card>
      )}

      {isAdminOrOwner() && employees.length > 0 && (
        <Card className="bg-white border-gray-200" data-testid="employee-directory-card">
          <CardHeader>
            <CardTitle className="font-heading uppercase">Employee Directory</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {employees.map((employee) => (
              <div key={employee.id} className="rounded-lg border border-gray-200 p-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between" data-testid={`employee-directory-row-${employee.id}`}>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-gray-900">{employee.name}</p>
                    <Badge variant="outline">{employee.role}</Badge>
                    {!employee.is_active && <Badge className="bg-red-100 text-red-700 border-red-200">Inactive</Badge>}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{employee.email || 'No email'}{employee.phone ? ` · ${employee.phone}` : ''}</p>
                  <p className="text-sm text-gray-500">Rate: {employee.hourly_rate ? `$${Number(employee.hourly_rate).toFixed(2)}/hr` : 'Not set'}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2 justify-end">
                  <Button variant="outline" size="sm" onClick={() => openEditEmployee(employee)} data-testid={`edit-employee-${employee.id}`}><Edit2 className="h-4 w-4 mr-1" /> Edit</Button>
                  <Button variant="outline" size="sm" onClick={() => handleInvitePortal(employee)} disabled={invitingEmployeeId === employee.id} data-testid={`invite-portal-${employee.id}`}><User className="h-4 w-4 mr-1" /> {invitingEmployeeId === employee.id ? 'Inviting...' : 'Invite Portal'}</Button>
                  <Button variant="outline" size="sm" onClick={() => { setPinResetEmployee(employee); setNewPin(''); }} data-testid={`reset-pin-${employee.id}`}><KeyRound className="h-4 w-4 mr-1" /> Reset PIN</Button>
                  <Button variant="outline" size="sm" onClick={() => handleToggleActive(employee)} data-testid={`toggle-employee-${employee.id}`}>{employee.is_active ? 'Deactivate' : 'Reactivate'}</Button>
                  <Button variant="outline" size="sm" className="text-red-600" onClick={() => handleDeleteEmployee(employee)} data-testid={`delete-employee-${employee.id}`}><Trash2 className="h-4 w-4 mr-1" /> Delete</Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[460px]">
          <DialogHeader><DialogTitle>Edit Employee</DialogTitle><DialogDescription>Update employee details, role, and hourly rate.</DialogDescription></DialogHeader>
          <form onSubmit={handleSaveEmployee} className="space-y-4">
            <div className="space-y-2"><Label>Name</Label><Input value={employeeForm.name} onChange={(e) => setEmployeeForm((prev) => ({ ...prev, name: e.target.value }))} data-testid="edit-employee-name-input" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Email</Label><Input value={employeeForm.email} onChange={(e) => setEmployeeForm((prev) => ({ ...prev, email: e.target.value }))} data-testid="edit-employee-email-input" /></div>
              <div className="space-y-2"><Label>Phone</Label><Input value={employeeForm.phone} onChange={(e) => setEmployeeForm((prev) => ({ ...prev, phone: e.target.value }))} data-testid="edit-employee-phone-input" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2"><Label>Hourly Rate</Label><Input type="number" step="0.01" value={employeeForm.hourly_rate} onChange={(e) => setEmployeeForm((prev) => ({ ...prev, hourly_rate: e.target.value }))} placeholder="0.00" data-testid="edit-employee-rate-input" /></div>
              <div className="space-y-2"><Label>Role</Label><Select value={employeeForm.role} onValueChange={(value) => setEmployeeForm((prev) => ({ ...prev, role: value }))}><SelectTrigger data-testid="edit-employee-role-select"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="staff">Staff</SelectItem><SelectItem value="admin">Admin</SelectItem></SelectContent></Select></div>
            </div>
            <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>Cancel</Button><Button type="submit" data-testid="edit-employee-submit-btn">Save</Button></div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={!!pinResetEmployee} onOpenChange={() => setPinResetEmployee(null)}>
        <DialogContent className="sm:max-w-[360px]">
          <DialogHeader><DialogTitle>Reset Employee PIN</DialogTitle><DialogDescription>Set a new 4-6 digit employee portal PIN.</DialogDescription></DialogHeader>
          <form onSubmit={handleResetPin} className="space-y-4">
            <div className="space-y-2"><Label>New PIN (4-6 digits)</Label><Input value={newPin} onChange={(e) => setNewPin(e.target.value)} maxLength={6} data-testid="employee-pin-reset-input" /></div>
            <div className="flex justify-end gap-2"><Button type="button" variant="outline" onClick={() => setPinResetEmployee(null)}>Cancel</Button><Button type="submit" data-testid="employee-pin-reset-submit">Save PIN</Button></div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
