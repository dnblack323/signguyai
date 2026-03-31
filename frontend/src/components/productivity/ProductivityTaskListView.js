import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { getItemBadgeClass, PRODUCTIVITY_TYPE_LABELS, sortItemsByDate } from '../../lib/productivity';

export const ProductivityTaskListView = ({ items, onOpenItem }) => {
  const rows = sortItemsByDate(items);
  return (
    <div className="space-y-3" data-testid="productivity-task-list-view">
      {rows.length === 0 ? (
        <Card className="bg-white border-gray-200"><CardContent className="p-8 text-center text-gray-500">No items match the current filters.</CardContent></Card>
      ) : rows.map((item) => (
        <Card key={item.uid} className="bg-white border-gray-200">
          <CardContent className="p-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
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
            <Button variant="outline" size="sm" onClick={() => onOpenItem(item)} data-testid={`task-list-open-${item.uid}`}>Open</Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};