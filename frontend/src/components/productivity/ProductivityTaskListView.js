import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { getItemBadgeClass, PRODUCTIVITY_TYPE_LABELS, sortItemsByDate } from '../../lib/productivity';

export const ProductivityTaskListView = ({ items, onOpenItem, onQuickUpdate, employees = [] }) => {
  const rows = sortItemsByDate(items);
  const canInlineAssign = (item) => ['task', 'production_task'].includes(item.type);
  const canInlinePriority = (item) => ['task', 'production_task'].includes(item.type);
  const canInlineEdit = (item) => ['task', 'job', 'production_task'].includes(item.type);

  return (
    <div className="space-y-3" data-testid="productivity-task-list-view">
      {rows.length === 0 ? (
        <Card className="bg-white border-gray-200"><CardContent className="p-8 text-center text-gray-500">No items match the current filters.</CardContent></Card>
      ) : rows.map((item) => (
        <Card key={item.uid} className="bg-white border-gray-200">
          <CardContent className="p-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            {(() => {
              const statusOptions = Array.from(new Set([item.status, 'to_do', 'open', 'pending', 'approved', 'in_progress', 'waiting', 'complete', 'completed', 'done'].filter(Boolean)));
              return (
                <>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-gray-900 truncate">{item.title}</p>
                <Badge className={getItemBadgeClass(item)}>{item.status.replace(/_/g, ' ')}</Badge>
                <Badge variant="outline">{PRODUCTIVITY_TYPE_LABELS[item.type] || item.type}</Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {item.customer_name || 'Internal'}
                {item.assigned_user_name ? ` · ${item.assigned_user_name}` : ''}
                {item.due_datetime ? ` · Due ${new Date(item.due_datetime).toLocaleDateString()}` : ''}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 justify-end">
              {canInlineEdit(item) && (
                <Select value={item.status} onValueChange={(value) => onQuickUpdate(item, { status: value })}>
                  <SelectTrigger className="w-[150px] h-9" data-testid={`task-list-status-${item.uid}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((status) => <SelectItem key={status} value={status}>{status.replace(/_/g, ' ')}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
              {canInlinePriority(item) && (
                <Select value={item.priority || 'normal'} onValueChange={(value) => onQuickUpdate(item, { priority: value })}>
                  <SelectTrigger className="w-[120px] h-9" data-testid={`task-list-priority-${item.uid}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {['normal', 'high', 'urgent', 'rush'].map((priority) => <SelectItem key={priority} value={priority}>{priority}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
              {canInlineEdit(item) && (
                <Input type="date" className="w-[150px] h-9" value={item.due_datetime ? item.due_datetime.slice(0, 10) : ''} onChange={(event) => onQuickUpdate(item, { due_datetime: event.target.value })} data-testid={`task-list-due-${item.uid}`} />
              )}
              {canInlineAssign(item) && (
                <Select value={item.assigned_user_id || 'unassigned'} onValueChange={(value) => onQuickUpdate(item, { assigned_user_id: value === 'unassigned' ? '' : value })}>
                  <SelectTrigger className="w-[170px] h-9" data-testid={`task-list-assignee-${item.uid}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="unassigned">Unassigned</SelectItem>
                    {employees.map((employee) => <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
              {canInlineEdit(item) && (
                <Button variant="outline" size="sm" onClick={() => onQuickUpdate(item, { is_completed: !item.is_completed, status: item.is_completed ? 'open' : (item.type === 'production_task' ? 'complete' : 'completed') })} data-testid={`task-list-complete-${item.uid}`}>
                  {item.is_completed ? 'Reopen' : 'Complete'}
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={() => onOpenItem(item)} data-testid={`task-list-open-${item.uid}`}>Open</Button>
            </div>
                </>
              );
            })()}
          </CardContent>
        </Card>
      ))}
    </div>
  );
};