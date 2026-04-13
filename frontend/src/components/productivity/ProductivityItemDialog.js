import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { getItemBadgeClass, PRODUCTIVITY_TYPE_LABELS } from '../../lib/productivity';

const WRITABLE_TYPES = new Set(['task', 'job', 'production_task', 'appointment', 'schedule_shift']);

const toDateTimeInputValue = (value) => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value.slice(0, 16);
  }
  const pad = (entry) => String(entry).padStart(2, '0');
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}T${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
};

export const ProductivityItemDialog = ({ item, open, onClose, employees = [], onUpdateItem }) => {
  if (!item) return null;

  const isWritable = WRITABLE_TYPES.has(item.type);
  const canAssign = ['task', 'production_task'].includes(item.type);
  const canEditPriority = ['task', 'production_task'].includes(item.type);
  const canEditStatus = ['task', 'job', 'production_task', 'appointment'].includes(item.type);
  const canEditDueDate = ['task', 'job', 'production_task'].includes(item.type);
  const canEditAppointmentStart = item.type === 'appointment';
  const canEditScheduleWindow = item.type === 'schedule_shift';
  const statusOptions = Array.from(new Set([item.status, 'to_do', 'open', 'pending', 'approved', 'scheduled', 'confirmed', 'in_progress', 'waiting', 'complete', 'completed', 'done', 'cancelled'].filter(Boolean)));

  const handleUpdate = (field, value) => {
    if (!onUpdateItem) return;
    const payload = { [field]: value };
    if (item.type === 'schedule_shift' && item.meta?.day_key) {
      payload.schedule_day_key = item.meta.day_key;
    }
    onUpdateItem(item, payload);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[520px]" data-testid="productivity-item-dialog">
        <DialogHeader>
          <DialogTitle>{item.title}</DialogTitle>
          <DialogDescription>{PRODUCTIVITY_TYPE_LABELS[item.type] || item.type} · {item.source_label || item.source_type}</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="flex flex-wrap gap-2">
            <Badge className={getItemBadgeClass(item)}>{item.status.replace(/_/g, ' ')}</Badge>
            {item.priority && <Badge variant="outline">Priority: {item.priority}</Badge>}
          </div>
          {item.customer_name && <p><span className="font-medium text-gray-900">Customer:</span> {item.customer_name}</p>}
          {item.assigned_user_name && <p><span className="font-medium text-gray-900">Assigned:</span> {item.assigned_user_name}</p>}
          {item.start_datetime && <p><span className="font-medium text-gray-900">Start:</span> {new Date(item.start_datetime).toLocaleString()}</p>}
          {item.due_datetime && <p><span className="font-medium text-gray-900">Due:</span> {new Date(item.due_datetime).toLocaleString()}</p>}
          {item.notes && <p><span className="font-medium text-gray-900">Notes:</span> {item.notes}</p>}
          {item.source_reference && <p><span className="font-medium text-gray-900">Reference:</span> {item.source_reference}</p>}
          {isWritable && (
            <div className="grid gap-4 rounded-xl border border-gray-200 p-4 md:grid-cols-2" data-testid="productivity-item-edit-panel">
              {canEditStatus && (
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select value={item.status} onValueChange={(value) => handleUpdate('status', value)}>
                    <SelectTrigger data-testid="productivity-item-status-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((status) => (
                        <SelectItem key={status} value={status}>{status.replace(/_/g, ' ')}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {canEditDueDate && (
                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Input type="date" value={item.due_datetime ? item.due_datetime.slice(0, 10) : ''} onChange={(event) => handleUpdate('due_datetime', event.target.value)} data-testid="productivity-item-due-input" />
                </div>
              )}
              {canEditAppointmentStart && (
                <div className="space-y-2">
                  <Label>Scheduled Start</Label>
                  <Input type="datetime-local" value={toDateTimeInputValue(item.start_datetime)} onChange={(event) => handleUpdate('start_datetime', event.target.value)} data-testid="productivity-item-appointment-start-input" />
                </div>
              )}
              {canEditScheduleWindow && (
                <>
                  <div className="space-y-2">
                    <Label>Shift Start</Label>
                    <Input type="datetime-local" value={toDateTimeInputValue(item.start_datetime)} onChange={(event) => handleUpdate('start_datetime', event.target.value)} data-testid="productivity-item-shift-start-input" />
                  </div>
                  <div className="space-y-2">
                    <Label>Shift End</Label>
                    <Input type="datetime-local" value={toDateTimeInputValue(item.due_datetime)} onChange={(event) => handleUpdate('due_datetime', event.target.value)} data-testid="productivity-item-shift-end-input" />
                  </div>
                </>
              )}
              {canEditPriority && (
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={item.priority || 'normal'} onValueChange={(value) => handleUpdate('priority', value)}>
                    <SelectTrigger data-testid="productivity-item-priority-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {['normal', 'high', 'urgent', 'rush'].map((priority) => (
                        <SelectItem key={priority} value={priority}>{priority}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {canAssign && (
                <div className="space-y-2">
                  <Label>Assigned User</Label>
                  <Select value={item.assigned_user_id || 'unassigned'} onValueChange={(value) => handleUpdate('assigned_user_id', value === 'unassigned' ? '' : value)}>
                    <SelectTrigger data-testid="productivity-item-assignee-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">Unassigned</SelectItem>
                      {employees.map((employee) => <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          )}
          <div className="pt-2">
            {item.source_route ? (
              <Button asChild size="sm" data-testid="productivity-open-source-button">
                <a href={item.source_route}>Open Source Record</a>
              </Button>
            ) : (
              <p className="text-xs text-gray-500">This item comes from an older source without a direct detail route yet.</p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};