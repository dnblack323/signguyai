import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Calendar, ChevronLeft, ChevronRight, Loader2, Save } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth, Permission } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { getAuthToken } from '../lib/authStorage';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });
const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const DAY_SHORT = { monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu', friday: 'Fri', saturday: 'Sat', sunday: 'Sun' };

function getWeekStart(refDate) {
  const d = new Date(refDate);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  return d.toISOString().slice(0, 10);
}

function getWeekDates(weekStart) {
  const start = new Date(weekStart + 'T12:00:00');
  return DAYS.map((_, i) => {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    return d.toISOString().slice(0, 10);
  });
}

function blankDay(dayOfWeek) {
  return { day_of_week: dayOfWeek, start_time: '', end_time: '', is_off: false, notes: '' };
}

export default function EmployeeSchedule() {
  const { hasPermission, isAdminOrOwner } = useAuth();
  const canView = hasPermission(Permission.PAYROLL_VIEW) || isAdminOrOwner();
  const canEdit = isAdminOrOwner();
  const { employees, fetchEmployees } = useApp();

  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [weekStart, setWeekStart] = useState(getWeekStart(new Date()));
  const [schedule, setSchedule] = useState(DAYS.map(blankDay));
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => { if (canView) fetchEmployees(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [canView]);
  useEffect(() => { if (employees.length && !selectedEmployeeId) setSelectedEmployeeId(employees[0]?.id || ''); }, [employees, selectedEmployeeId]);

  const weekDates = getWeekDates(weekStart);

  const loadSchedule = useCallback(async () => {
    if (!selectedEmployeeId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/api/payroll/schedule`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
        params: { employee_id: selectedEmployeeId, week_start: weekStart },
      });
      const saved = res.data?.schedules || [];
      const merged = DAYS.map((day) => {
        const existing = saved.find((s) => s.day_of_week === day);
        return existing ? { ...blankDay(day), ...existing } : blankDay(day);
      });
      setSchedule(merged);
      setHasChanges(false);
    } catch {
      setSchedule(DAYS.map(blankDay));
    } finally {
      setLoading(false);
    }
  }, [selectedEmployeeId, weekStart]);

  useEffect(() => { loadSchedule(); }, [loadSchedule]);

  const updateDay = (index, field, value) => {
    setSchedule((prev) => prev.map((d, i) => i === index ? { ...d, [field]: value } : d));
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      for (let i = 0; i < DAYS.length; i++) {
        const day = schedule[i];
        await axios.post(`${API}/api/payroll/schedule`, {
          employee_id: selectedEmployeeId,
          week_start: weekStart,
          day: day.day_of_week,
          start_time: day.start_time || '',
          end_time: day.end_time || '',
          notes: day.notes || '',
        }, { headers: hdr() });
      }
      toast.success('Schedule saved');
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save schedule:', error);
      toast.error('Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  const shiftWeek = (dir) => {
    const d = new Date(weekStart + 'T12:00:00');
    d.setDate(d.getDate() + (dir * 7));
    setWeekStart(d.toISOString().slice(0, 10));
  };

  const selectedEmployee = employees.find((e) => e.id === selectedEmployeeId);

  if (!canView) {
    return <div className="flex h-64 items-center justify-center text-gray-500">You do not have permission to view schedules.</div>;
  }

  return (
    <div className="max-w-5xl mx-auto pb-12" data-testid="employee-schedule-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900" data-testid="employee-schedule-title">Employee Schedule</h1>
          <p className="text-sm text-gray-500">Set weekly work schedules for each employee</p>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && <Badge variant="outline" className="text-amber-600 border-amber-300">Unsaved</Badge>}
          {canEdit && (
            <Button onClick={handleSave} disabled={saving || !hasChanges || !selectedEmployeeId} className="bg-violet-600 hover:bg-violet-700 text-white gap-1" data-testid="schedule-save-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save Schedule
            </Button>
          )}
        </div>
      </div>

      {/* Employee + Week Selector */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Employee</Label>
          <Select value={selectedEmployeeId} onValueChange={setSelectedEmployeeId}>
            <SelectTrigger data-testid="schedule-employee-select"><SelectValue placeholder="Select employee" /></SelectTrigger>
            <SelectContent>
              {employees.filter((e) => e.is_active).map((e) => (
                <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Week</Label>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" className="h-9 w-9" onClick={() => shiftWeek(-1)} data-testid="schedule-prev-week">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex-1 text-center">
              <p className="text-sm font-medium text-gray-900">
                {new Date(weekStart + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} — {new Date(weekDates[6] + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </p>
            </div>
            <Button variant="outline" size="icon" className="h-9 w-9" onClick={() => shiftWeek(1)} data-testid="schedule-next-week">
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Schedule Grid */}
      {loading ? (
        <div className="flex h-40 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-violet-500" /></div>
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-gray-900 flex items-center gap-2">
              <Calendar className="h-4 w-4" /> {selectedEmployee?.name || 'Employee'} — Weekly Schedule
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500 w-20">Day</th>
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500 w-24">Date</th>
                    <th className="text-center py-2 px-2 text-xs font-semibold uppercase text-gray-500 w-16">Off</th>
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500">Start</th>
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500">End</th>
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500">Hours</th>
                    <th className="text-left py-2 px-2 text-xs font-semibold uppercase text-gray-500">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.map((day, idx) => {
                    const isWeekend = idx >= 5;
                    const hrs = day.start_time && day.end_time && !day.is_off
                      ? Math.max(0, ((parseInt(day.end_time.split(':')[0]) * 60 + parseInt(day.end_time.split(':')[1])) - (parseInt(day.start_time.split(':')[0]) * 60 + parseInt(day.start_time.split(':')[1]))) / 60).toFixed(1)
                      : '—';
                    return (
                      <tr key={day.day_of_week} className={`border-b border-gray-100 ${isWeekend ? 'bg-gray-50/50' : ''} ${day.is_off ? 'opacity-50' : ''}`} data-testid={`schedule-row-${day.day_of_week}`}>
                        <td className="py-2 px-2 font-medium text-gray-900">{DAY_SHORT[day.day_of_week]}</td>
                        <td className="py-2 px-2 text-gray-500 text-xs">{weekDates[idx]}</td>
                        <td className="py-2 px-2 text-center">
                          <Switch
                            checked={day.is_off}
                            onCheckedChange={(v) => updateDay(idx, 'is_off', v)}
                            disabled={!canEdit}
                            data-testid={`schedule-off-${day.day_of_week}`}
                          />
                        </td>
                        <td className="py-2 px-2">
                          <Input
                            type="time"
                            value={day.start_time}
                            onChange={(e) => updateDay(idx, 'start_time', e.target.value)}
                            disabled={!canEdit || day.is_off}
                            className="h-8 text-xs w-28"
                            data-testid={`schedule-start-${day.day_of_week}`}
                          />
                        </td>
                        <td className="py-2 px-2">
                          <Input
                            type="time"
                            value={day.end_time}
                            onChange={(e) => updateDay(idx, 'end_time', e.target.value)}
                            disabled={!canEdit || day.is_off}
                            className="h-8 text-xs w-28"
                            data-testid={`schedule-end-${day.day_of_week}`}
                          />
                        </td>
                        <td className="py-2 px-2 text-gray-600 font-medium">{day.is_off ? 'OFF' : hrs}</td>
                        <td className="py-2 px-2">
                          <Input
                            value={day.notes}
                            onChange={(e) => updateDay(idx, 'notes', e.target.value)}
                            disabled={!canEdit}
                            placeholder="Notes..."
                            className="h-8 text-xs"
                            data-testid={`schedule-notes-${day.day_of_week}`}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-300">
                    <td colSpan={5} className="py-2 px-2 text-right font-semibold text-gray-700 text-xs uppercase">Total Scheduled Hours</td>
                    <td className="py-2 px-2 font-bold text-gray-900">
                      {schedule.reduce((sum, day) => {
                        if (day.is_off || !day.start_time || !day.end_time) return sum;
                        const [sh, sm] = day.start_time.split(':').map(Number);
                        const [eh, em] = day.end_time.split(':').map(Number);
                        return sum + Math.max(0, ((eh * 60 + em) - (sh * 60 + sm)) / 60);
                      }, 0).toFixed(1)}
                    </td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
