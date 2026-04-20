import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';

/**
 * Shared order-level context fields — populated ONCE per order and inherited by every Order Item.
 * Used by NewOrderForm and OrderDetail.
 */
export default function SharedContextPanel({ order = {}, onChange, readOnly = false }) {
  const update = (patch) => onChange?.({ ...order, ...patch });

  return (
    <div className="border rounded-lg p-3 bg-white space-y-3" data-testid="shared-context-panel">
      <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Shared Order Context</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <Label className="text-[10px] text-gray-500">Order / Project Title</Label>
          <Input
            value={order.order_title || ''}
            onChange={(e) => update({ order_title: e.target.value })}
            className="h-8 text-sm"
            placeholder="e.g. Fall 2026 event signage"
            disabled={readOnly}
            data-testid="shared-order-title"
          />
        </div>
        <div>
          <Label className="text-[10px] text-gray-500">Due Date</Label>
          <Input
            type="date"
            value={order.requested_due_date?.slice(0, 10) || ''}
            onChange={(e) => update({ requested_due_date: e.target.value })}
            className="h-8 text-sm"
            disabled={readOnly}
            data-testid="shared-due-date"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <Label className="text-[10px] text-gray-500">Production Notes (shared)</Label>
          <Textarea
            value={order.shared_production_notes || ''}
            onChange={(e) => update({ shared_production_notes: e.target.value })}
            className="text-sm min-h-[70px]"
            placeholder="Notes every item inherits (rush priorities, special handling…)"
            disabled={readOnly}
            data-testid="shared-prod-notes"
          />
        </div>
        <div>
          <Label className="text-[10px] text-gray-500">Color / Brand Notes (shared)</Label>
          <Textarea
            value={order.shared_color_brand_notes || ''}
            onChange={(e) => update({ shared_color_brand_notes: e.target.value })}
            className="text-sm min-h-[70px]"
            placeholder="Pantone refs, brand palette, font rules…"
            disabled={readOnly}
            data-testid="shared-color-notes"
          />
        </div>
        <div>
          <Label className="text-[10px] text-gray-500">Install / Location Notes (shared)</Label>
          <Textarea
            value={order.shared_install_notes || ''}
            onChange={(e) => update({ shared_install_notes: e.target.value })}
            className="text-sm min-h-[70px]"
            placeholder="Install address, access notes, hours…"
            disabled={readOnly}
            data-testid="shared-install-notes"
          />
        </div>
        <div>
          <Label className="text-[10px] text-gray-500">Design Notes (shared)</Label>
          <Textarea
            value={order.shared_design_notes || ''}
            onChange={(e) => update({ shared_design_notes: e.target.value })}
            className="text-sm min-h-[70px]"
            placeholder="Mood/style direction, references, revisions scope…"
            disabled={readOnly}
            data-testid="shared-design-notes"
          />
        </div>
      </div>

      <p className="text-[10px] text-gray-500 italic">
        These notes are stored once on the order and inherited by every new item. You can still override any note per item.
      </p>
    </div>
  );
}
