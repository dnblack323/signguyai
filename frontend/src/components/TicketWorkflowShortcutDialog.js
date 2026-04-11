import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { CalendarDays } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Checkbox } from './ui/checkbox';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const headers = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });
const DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

const getWeekStart = (dateValue) => {
  const base = new Date(`${dateValue}T12:00:00`);
  const day = base.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const monday = new Date(base);
  monday.setDate(base.getDate() + mondayOffset);
  return monday.toISOString().split('T')[0];
};

const defaultTaskDescription = (order, ticket) => [
  order?.order_number ? `Order: ${order.order_number}` : null,
  ticket?.ticket_number ? `Ticket: ${ticket.ticket_number}` : null,
  ticket?.item_name ? `Item: ${ticket.item_name}` : null,
].filter(Boolean).join('\n');

export const TicketWorkflowShortcutDialog = ({
  open,
  mode,
  ticket,
  order,
  employees,
  onClose,
  onCompleted,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const scheduleDateInputRef = useRef(null);
  const employeeOptions = useMemo(() => (employees || []).filter((employee) => employee.is_active !== false), [employees]);
  const defaultDate = order?.requested_due_date || new Date().toISOString().split('T')[0];

  const [assignForm, setAssignForm] = useState({ employee_id: '', apply_to_tasks: true });
  const [scheduleForm, setScheduleForm] = useState({ employee_id: '', date: defaultDate, start: '08:00', end: '17:00', notes: '', assign_ticket: true, assign_tasks: true });
  const [taskForm, setTaskForm] = useState({ title: '', description: '', employee_id: '', due_date: defaultDate });

  useEffect(() => {
    if (!open || !ticket) return;
    setAssignForm({ employee_id: ticket.assigned_user_id || '', apply_to_tasks: true });
    setScheduleForm({
      employee_id: ticket.assigned_user_id || '',
      date: order?.requested_due_date || new Date().toISOString().split('T')[0],
      start: '08:00',
      end: '17:00',
      notes: `${ticket.ticket_number} — ${ticket.item_name}`,
      assign_ticket: true,
      assign_tasks: true,
    });
    setTaskForm({
      title: `Follow up: ${ticket.ticket_number} — ${ticket.item_name}`,
      description: defaultTaskDescription(order, ticket),
      employee_id: ticket.assigned_user_id || '',
      due_date: order?.requested_due_date || new Date().toISOString().split('T')[0],
    });
  }, [open, ticket, order]);

  if (!ticket || !mode) return null;

  const syncTaskAssignments = async (employeeId) => {
    const response = await axios.get(`${API}/production-tasks?job_ticket_id=${ticket.id}&limit=200`, { headers: headers() });
    const tasks = response.data?.tasks || [];
    await Promise.all(tasks.map((task) => axios.put(`${API}/production-tasks/${task.id}`, { assigned_to: employeeId }, { headers: headers() })));
  };

  const handleAssign = async () => {
    if (!assignForm.employee_id) {
      toast.error('Choose an employee first');
      return;
    }
    setSubmitting(true);
    try {
      await axios.put(`${API}/job-tickets/${ticket.id}`, { assigned_user_id: assignForm.employee_id }, { headers: headers() });
      if (assignForm.apply_to_tasks) {
        await syncTaskAssignments(assignForm.employee_id);
      }
      toast.success('Ticket assignment saved');
      onCompleted?.();
      onClose?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSchedule = async () => {
    if (!scheduleForm.employee_id || !scheduleForm.date || !scheduleForm.start || !scheduleForm.end) {
      toast.error('Employee, date, start, and end times are required');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/payroll/schedule`, {
        employee_id: scheduleForm.employee_id,
        week_start: getWeekStart(scheduleForm.date),
        day: DAYS[new Date(`${scheduleForm.date}T12:00:00`).getDay()],
        start_time: scheduleForm.start,
        end_time: scheduleForm.end,
        notes: scheduleForm.notes,
      }, { headers: headers() });
      if (scheduleForm.assign_ticket) {
        await axios.put(`${API}/job-tickets/${ticket.id}`, { assigned_user_id: scheduleForm.employee_id }, { headers: headers() });
      }
      if (scheduleForm.assign_tasks) {
        await syncTaskAssignments(scheduleForm.employee_id);
      }
      toast.success('Ticket added to the schedule');
      onCompleted?.();
      onClose?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to schedule ticket');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTaskCreate = async () => {
    if (!taskForm.title.trim()) {
      toast.error('Task title is required');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/tasks`, {
        title: taskForm.title.trim(),
        description: taskForm.description.trim() || null,
        assigned_to: taskForm.employee_id || null,
        due_date: taskForm.due_date || null,
      }, { headers: headers() });
      toast.success('Task created from this ticket');
      onCompleted?.();
      onClose?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create task');
    } finally {
      setSubmitting(false);
    }
  };

  const config = {
    assign: {
      title: 'Assign ticket to employee',
      description: 'Update the ticket owner and optionally sync every production task.',
      action: handleAssign,
      actionLabel: 'Save assignment',
    },
    schedule: {
      title: 'Add ticket to schedule',
      description: 'Create an employee schedule slot and optionally assign the ticket too.',
      action: handleSchedule,
      actionLabel: 'Save schedule',
    },
    task: {
      title: 'Create productivity task',
      description: 'Add a follow-up task linked to this ticket context.',
      action: handleTaskCreate,
      actionLabel: 'Create task',
    },
  }[mode];

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose?.()}>
      <DialogContent className="sm:max-w-[460px]" data-testid={`ticket-shortcut-dialog-${mode}`}>
        <DialogHeader>
          <DialogTitle data-testid="ticket-shortcut-dialog-title">{config.title}</DialogTitle>
          <DialogDescription data-testid="ticket-shortcut-dialog-description">{config.description}</DialogDescription>
        </DialogHeader>

        {mode === 'assign' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ticket-assign-employee">Employee</Label>
              <Select value={assignForm.employee_id || 'unassigned'} onValueChange={(value) => setAssignForm((current) => ({ ...current, employee_id: value === 'unassigned' ? '' : value }))}>
                <SelectTrigger id="ticket-assign-employee" data-testid="ticket-assign-employee-select">
                  <SelectValue placeholder="Choose employee" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  {employeeOptions.map((employee) => (
                    <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <label className="flex items-center gap-3 rounded-lg border border-gray-200 p-3" data-testid="ticket-assign-apply-tasks-row">
              <Checkbox checked={assignForm.apply_to_tasks} onCheckedChange={(checked) => setAssignForm((current) => ({ ...current, apply_to_tasks: !!checked }))} data-testid="ticket-assign-apply-tasks-checkbox" />
              <span className="text-sm text-gray-700">Also assign all existing production tasks</span>
            </label>
          </div>
        )}

        {mode === 'schedule' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ticket-schedule-employee">Employee</Label>
              <Select value={scheduleForm.employee_id || 'unassigned'} onValueChange={(value) => setScheduleForm((current) => ({ ...current, employee_id: value === 'unassigned' ? '' : value }))}>
                <SelectTrigger id="ticket-schedule-employee" data-testid="ticket-schedule-employee-select">
                  <SelectValue placeholder="Choose employee" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Choose employee</SelectItem>
                  {employeeOptions.map((employee) => (
                    <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-2 col-span-3 sm:col-span-1">
                <Label htmlFor="ticket-schedule-date">Date</Label>
                <div className="flex items-center gap-2">
                  <Input
                    ref={scheduleDateInputRef}
                    id="ticket-schedule-date"
                    type="date"
                    value={scheduleForm.date}
                    onClick={(event) => event.currentTarget.showPicker?.()}
                    onFocus={(event) => event.currentTarget.showPicker?.()}
                    onChange={(event) => setScheduleForm((current) => ({ ...current, date: event.target.value }))}
                    data-testid="ticket-schedule-date-input"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      scheduleDateInputRef.current?.showPicker?.();
                      scheduleDateInputRef.current?.focus();
                    }}
                    data-testid="ticket-schedule-date-picker-button"
                  >
                    <CalendarDays className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-2 col-span-3 sm:col-span-1">
                <Label htmlFor="ticket-schedule-start">Start</Label>
                <Input id="ticket-schedule-start" type="time" value={scheduleForm.start} onChange={(event) => setScheduleForm((current) => ({ ...current, start: event.target.value }))} data-testid="ticket-schedule-start-input" />
              </div>
              <div className="space-y-2 col-span-3 sm:col-span-1">
                <Label htmlFor="ticket-schedule-end">End</Label>
                <Input id="ticket-schedule-end" type="time" value={scheduleForm.end} onChange={(event) => setScheduleForm((current) => ({ ...current, end: event.target.value }))} data-testid="ticket-schedule-end-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="ticket-schedule-notes">Notes</Label>
              <Input id="ticket-schedule-notes" value={scheduleForm.notes} onChange={(event) => setScheduleForm((current) => ({ ...current, notes: event.target.value }))} data-testid="ticket-schedule-notes-input" />
            </div>
            <label className="flex items-center gap-3 rounded-lg border border-gray-200 p-3" data-testid="ticket-schedule-assign-ticket-row">
              <Checkbox checked={scheduleForm.assign_ticket} onCheckedChange={(checked) => setScheduleForm((current) => ({ ...current, assign_ticket: !!checked }))} data-testid="ticket-schedule-assign-ticket-checkbox" />
              <span className="text-sm text-gray-700">Assign this ticket to the same employee</span>
            </label>
            <label className="flex items-center gap-3 rounded-lg border border-gray-200 p-3" data-testid="ticket-schedule-assign-tasks-row">
              <Checkbox checked={scheduleForm.assign_tasks} onCheckedChange={(checked) => setScheduleForm((current) => ({ ...current, assign_tasks: !!checked }))} data-testid="ticket-schedule-assign-tasks-checkbox" />
              <span className="text-sm text-gray-700">Assign all production tasks too</span>
            </label>
          </div>
        )}

        {mode === 'task' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ticket-task-title">Task title</Label>
              <Input id="ticket-task-title" value={taskForm.title} onChange={(event) => setTaskForm((current) => ({ ...current, title: event.target.value }))} data-testid="ticket-task-title-input" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ticket-task-description">Description</Label>
              <Input id="ticket-task-description" value={taskForm.description} onChange={(event) => setTaskForm((current) => ({ ...current, description: event.target.value }))} data-testid="ticket-task-description-input" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="ticket-task-employee">Assignee</Label>
                <Select value={taskForm.employee_id || 'unassigned'} onValueChange={(value) => setTaskForm((current) => ({ ...current, employee_id: value === 'unassigned' ? '' : value }))}>
                  <SelectTrigger id="ticket-task-employee" data-testid="ticket-task-employee-select">
                    <SelectValue placeholder="Optional" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unassigned">Unassigned</SelectItem>
                    {employeeOptions.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="ticket-task-due-date">Due date</Label>
                <Input id="ticket-task-due-date" type="date" value={taskForm.due_date} onChange={(event) => setTaskForm((current) => ({ ...current, due_date: event.target.value }))} data-testid="ticket-task-due-date-input" />
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} data-testid="ticket-shortcut-cancel-button">Cancel</Button>
          <Button type="button" onClick={config.action} disabled={submitting} data-testid="ticket-shortcut-submit-button">
            {submitting ? 'Saving...' : config.actionLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};