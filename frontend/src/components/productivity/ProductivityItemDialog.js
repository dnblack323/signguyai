import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { getItemBadgeClass, PRODUCTIVITY_TYPE_LABELS } from '../../lib/productivity';

export const ProductivityItemDialog = ({ item, open, onClose }) => {
  if (!item) return null;

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