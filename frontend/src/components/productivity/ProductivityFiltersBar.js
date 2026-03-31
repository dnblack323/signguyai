import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';

const ITEM_TYPE_OPTIONS = [
  { value: 'task', label: 'Tasks' },
  { value: 'job', label: 'Jobs' },
  { value: 'production_task', label: 'Production' },
  { value: 'schedule_shift', label: 'Schedule' },
  { value: 'appointment', label: 'Appointments' },
];

export const ProductivityFiltersBar = ({ filters, setFilters, employees }) => {
  const toggleType = (type) => {
    const next = filters.itemTypes.includes(type)
      ? filters.itemTypes.filter((current) => current !== type)
      : [...filters.itemTypes, type];
    setFilters((current) => ({ ...current, itemTypes: next }));
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-4" data-testid="productivity-filters-bar">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <Input
          value={filters.search}
          onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
          placeholder="Search productivity items..."
          className="max-w-lg"
          data-testid="productivity-search-input"
        />
        <div className="flex flex-wrap gap-3">
          <Select value={filters.assignedUserId || 'all'} onValueChange={(value) => setFilters((current) => ({ ...current, assignedUserId: value === 'all' ? '' : value }))}>
            <SelectTrigger className="w-[190px]" data-testid="productivity-assignee-filter">
              <SelectValue placeholder="Assigned employee" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Employees</SelectItem>
              {employees.map((employee) => (
                <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filters.status || 'all'} onValueChange={(value) => setFilters((current) => ({ ...current, status: value === 'all' ? '' : value }))}>
            <SelectTrigger className="w-[170px]" data-testid="productivity-status-filter">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {['to_do', 'open', 'approved', 'pending', 'scheduled', 'in_progress', 'waiting', 'complete', 'completed', 'done'].map((status) => (
                <SelectItem key={status} value={status}>{status.replace(/_/g, ' ')}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2">
            <Label className="text-sm text-gray-600">Completed</Label>
            <Switch checked={filters.includeCompleted} onCheckedChange={(checked) => setFilters((current) => ({ ...current, includeCompleted: checked }))} data-testid="productivity-completed-toggle" />
          </div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {ITEM_TYPE_OPTIONS.map((option) => (
          <Button
            key={option.value}
            type="button"
            size="sm"
            variant={filters.itemTypes.includes(option.value) ? 'default' : 'outline'}
            onClick={() => toggleType(option.value)}
            data-testid={`productivity-type-filter-${option.value}`}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
};