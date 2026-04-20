import { useState } from 'react';
import { Button } from '../ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { Plus, FileText, Copy, Shuffle, Image, Zap } from 'lucide-react';
import ItemPickerDialog from './ItemPickerDialog';
import CloneItemDialog from './CloneItemDialog';
import SharedArtworkPickerDialog from './SharedArtworkPickerDialog';

/**
 * Unified "Add Order Item" menu — 5 paths:
 *  1. Quick Manual Item
 *  2. Detailed Item From Scratch
 *  3. Duplicate Existing Item
 *  4. Create Variation From Existing Item
 *  5. Add Item Using Shared Order Artwork
 *
 * Works for both NewOrderForm (pre-save orderId) and OrderDetail / AddTicketToOrder (post-save).
 */
export default function AddOrderItemMenu({
  orderId,
  existingItems = [],
  onQuickAdd,
  onDetailedAdd,
  onCloneComplete,
  onAddWithSharedArtwork,
  disabled = false,
  variant = 'primary',
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerMode, setPickerMode] = useState('duplicate');
  const [cloneSourceId, setCloneSourceId] = useState(null);
  const [cloneMode, setCloneMode] = useState('duplicate');
  const [artworkPickerOpen, setArtworkPickerOpen] = useState(false);

  const handlePick = (itemId) => {
    setCloneSourceId(itemId);
    setCloneMode(pickerMode);
    setPickerOpen(false);
  };

  const openPicker = (mode) => {
    setPickerMode(mode);
    setPickerOpen(true);
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            disabled={disabled}
            data-testid="add-order-item-menu-trigger"
            className={variant === 'primary' ? 'bg-violet-600 hover:bg-violet-700 text-white' : ''}
            variant={variant === 'primary' ? 'default' : 'outline'}
          >
            <Plus className="w-4 h-4 mr-2" /> Add Order Item
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-64">
          <DropdownMenuItem onClick={() => onQuickAdd?.()} data-testid="add-item-quick">
            <Zap className="w-4 h-4 mr-2 text-amber-500" />
            <div className="flex flex-col">
              <span className="font-medium">Quick Manual Item</span>
              <span className="text-[10px] text-gray-500">Name, quantity, price</span>
            </div>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onDetailedAdd?.()} data-testid="add-item-detailed">
            <FileText className="w-4 h-4 mr-2 text-violet-600" />
            <div className="flex flex-col">
              <span className="font-medium">Detailed Item From Scratch</span>
              <span className="text-[10px] text-gray-500">Pick a category, fill full spec</span>
            </div>
          </DropdownMenuItem>
          <DropdownMenuItem disabled={existingItems.length === 0} onClick={() => openPicker('duplicate')} data-testid="add-item-duplicate">
            <Copy className="w-4 h-4 mr-2 text-blue-600" />
            <div className="flex flex-col">
              <span className="font-medium">Duplicate Existing Item</span>
              <span className="text-[10px] text-gray-500">Clone exactly</span>
            </div>
          </DropdownMenuItem>
          <DropdownMenuItem disabled={existingItems.length === 0} onClick={() => openPicker('variation')} data-testid="add-item-variation">
            <Shuffle className="w-4 h-4 mr-2 text-emerald-600" />
            <div className="flex flex-col">
              <span className="font-medium">Create Variation From Existing</span>
              <span className="text-[10px] text-gray-500">Clone + open to change one spec</span>
            </div>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setArtworkPickerOpen(true)} data-testid="add-item-shared-artwork">
            <Image className="w-4 h-4 mr-2 text-pink-600" />
            <div className="flex flex-col">
              <span className="font-medium">Add Item Using Shared Artwork</span>
              <span className="text-[10px] text-gray-500">Pre-link order-level artwork</span>
            </div>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ItemPickerDialog
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        items={existingItems}
        mode={pickerMode}
        onPick={handlePick}
      />

      <CloneItemDialog
        open={!!cloneSourceId}
        onClose={() => setCloneSourceId(null)}
        orderId={orderId}
        sourceItemId={cloneSourceId}
        sourceItem={existingItems.find((i) => (i.id || i.ticket_id) === cloneSourceId) || null}
        defaultMode={cloneMode}
        onComplete={(newItem) => {
          setCloneSourceId(null);
          onCloneComplete?.(newItem);
        }}
      />

      <SharedArtworkPickerDialog
        open={artworkPickerOpen}
        orderId={orderId}
        onClose={() => setArtworkPickerOpen(false)}
        onPicked={(fileIds) => {
          setArtworkPickerOpen(false);
          onAddWithSharedArtwork?.(fileIds);
        }}
      />
    </>
  );
}
