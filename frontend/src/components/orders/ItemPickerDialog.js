import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';

const CATEGORY_ICONS = {
  apparel: '👕',
  banners: '🪧',
  digital_print: '🖨',
  rigid_signs: '🪧',
  cut_vinyl: '✂️',
  vehicle_wrap: '🚐',
  services: '🛠',
  promotional: '🎁',
  custom: '⋯',
};

export default function ItemPickerDialog({ open, onClose, items = [], mode = 'duplicate', onPick }) {
  const title = mode === 'variation' ? 'Select item to create variation from' : 'Select item to duplicate';
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent className="max-w-xl" data-testid="item-picker-dialog">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh]">
          <div className="space-y-2">
            {items.length === 0 && <p className="text-sm text-gray-500 py-6 text-center">No items yet — add one first.</p>}
            {items.map((item) => {
              const id = item.id || item.ticket_id;
              const cat = item.item_category || item.category || 'custom';
              return (
                <button
                  key={id}
                  onClick={() => onPick?.(id)}
                  className="w-full text-left border rounded-lg p-3 hover:bg-violet-50 hover:border-violet-300 transition-colors"
                  data-testid={`item-picker-row-${id}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{CATEGORY_ICONS[cat] || '⋯'}</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{item.item_name || item.name || 'Untitled'}</p>
                      <p className="text-xs text-gray-500">{cat.replace(/_/g, ' ')} · qty {item.quantity || 1}</p>
                    </div>
                    <Badge variant="outline">${Number(item.estimated_price || item.price || 0).toFixed(2)}</Badge>
                  </div>
                </button>
              );
            })}
          </div>
        </ScrollArea>
        <div className="flex justify-end mt-4">
          <Button variant="outline" onClick={onClose} data-testid="item-picker-cancel">Cancel</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
