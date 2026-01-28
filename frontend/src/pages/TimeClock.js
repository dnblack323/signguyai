import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { formatTime, cn } from '../lib/utils';
import { Play, Pause, Coffee, Square, Clock, Plus, User } from 'lucide-react';
import { toast } from 'sonner';

const actionButtons = [
  { action: 'start_work', label: 'Start Work', icon: Play, color: 'bg-green-600 hover:bg-green-700' },
  { action: 'break_start', label: 'Start Break', icon: Coffee, color: 'bg-yellow-600 hover:bg-yellow-700' },
  { action: 'break_end', label: 'End Break', icon: Coffee, color: 'bg-blue-600 hover:bg-blue-700' },
  { action: 'end_work', label: 'End Work', icon: Square, color: 'bg-red-600 hover:bg-red-700' },
];

export default function TimeClock() {
  const { 
    employees, fetchEmployees, createEmployee,
    clockAction, getClockStatus, getTodayLogs, getShiftSummary 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [clockStatus, setClockStatus] = useState(null);
  const [todayLogs, setTodayLogs] = useState([]);
  const [shiftSummary, setShiftSummary] = useState(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newEmployee, setNewEmployee] = useState({ name: '', hourly_rate: 0 });

  useEffect(() => {
    loadEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      loadEmployeeData();
    }
  }, [selectedEmployee]);

  const loadEmployees = async () => {
    setLoading(true);
    await fetchEmployees();
    setLoading(false);
  };

  const loadEmployeeData = async () => {
    if (!selectedEmployee) return;
    try {
      const [status, logs, summary] = await Promise.all([
        getClockStatus(selectedEmployee),
        getTodayLogs(selectedEmployee),
        getShiftSummary(selectedEmployee)
      ]);
      setClockStatus(status);
      setTodayLogs(logs);
      setShiftSummary(summary);
    } catch (err) {
      console.error('Error loading employee data:', err);
    }
  };

  const handleClockAction = async (action) => {
    if (!selectedEmployee) {
      toast.error('Please select an employee');
      return;
    }
    try {
      await clockAction(selectedEmployee, action);
      toast.success(`${action.replace('_', ' ')} recorded`);
      await loadEmployeeData();
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
      await createEmployee(newEmployee);
      toast.success('Employee created');
      setNewEmployee({ name: '', hourly_rate: 0 });
      setIsDialogOpen(false);
      await loadEmployees();
    } catch (err) {
      toast.error('Failed to create employee');
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
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Time Clock</h1>
          <p className="text-muted-foreground mt-1">Track employee work hours</p>
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
                  onChange={(e) => setNewEmployee({ ...newEmployee, hourly_rate: parseFloat(e.target.value) || 0 })}
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
      <Card className="bg-card border-border/50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-muted-foreground" />
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
          <Card className="bg-card border-border/50">
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
                        "h-24 flex flex-col items-center justify-center gap-2 text-white transition-all",
                        isAvailable ? color : "bg-muted text-muted-foreground cursor-not-allowed",
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
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase flex items-center gap-2">
                  <Clock className="h-5 w-5 text-primary" />
                  Today's Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                {shiftSummary ? (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-muted/30 rounded-lg">
                      <p className="text-sm text-muted-foreground">Work Time</p>
                      <p className="text-2xl font-bold text-green-400">
                        {Math.round(shiftSummary.work_minutes)} min
                      </p>
                    </div>
                    <div className="text-center p-4 bg-muted/30 rounded-lg">
                      <p className="text-sm text-muted-foreground">Break Time</p>
                      <p className="text-2xl font-bold text-yellow-400">
                        {Math.round(shiftSummary.break_minutes)} min
                      </p>
                    </div>
                    <div className="text-center p-4 bg-muted/30 rounded-lg">
                      <p className="text-sm text-muted-foreground">Net Hours</p>
                      <p className="text-2xl font-bold text-primary">
                        {shiftSummary.net_hours.toFixed(2)} hrs
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>

            {/* Today's Log */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase">Today's Activity</CardTitle>
              </CardHeader>
              <CardContent>
                {todayLogs.length === 0 ? (
                  <p className="text-muted-foreground text-center py-4">No activity today</p>
                ) : (
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {todayLogs.map((log) => (
                      <div 
                        key={log.id} 
                        className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                        data-testid={`log-${log.id}`}
                      >
                        <span className="font-medium capitalize">
                          {log.action.replace('_', ' ')}
                        </span>
                        <span className="text-muted-foreground">
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
        <Card className="bg-card border-border/50">
          <CardContent className="p-12 text-center">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Employees</h3>
            <p className="text-muted-foreground mb-4">Add an employee to start tracking time</p>
            <Button onClick={() => setIsDialogOpen(true)} data-testid="empty-add-employee">
              <Plus className="h-4 w-4 mr-2" /> Add First Employee
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
