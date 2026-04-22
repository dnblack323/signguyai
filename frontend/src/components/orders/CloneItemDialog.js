import { useState } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { toast } from 'sonner';
import { getAuthToken } from '../../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CARRY_OVER_DEFAULTS = {
  artwork: true,
  artwork_notes: true,
  production_notes: true,
  colors: true,
  shared_references: true,
  design_setup: true,
  rush_setting: true,
  due_date: true,
  install_location_notes: true,
  quantity: false,
  size_breakdown: false,
  names_numbers: false,
};

const CARRY_OVER_LABELS = {
  artwork: 'Linked artwork & assets',
  artwork_notes: 'Artwork notes',
  production_notes: 'Production notes',
  colors: 'Colors / brand notes',
  shared_references: 'Shared references',
  design_setup: 'Design / setup info',
  rush_setting: 'Rush setting',
  due_date: 'Due date',
  install_location_notes: 'Install / location notes',
  quantity: 'Quantity',
  size_breakdown: 'Size breakdown',
  names_numbers: 'Names & numbers',
};

const TARGET_CATEGORIES = [
  { value: 'banners', label: 'Banners' },
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'digital_print', label: 'Digital Print' },
  { value: 'cut_vinyl', label: 'Cut Vinyl' },
  { value: 'vehicle_wrap', label: 'Vehicle Wraps' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'services', label: 'Services' },
  { value: 'promo_misc', label: 'Promotional Items' },
  { value: 'custom', label: 'Custom' },
];

export default function CloneItemDialog({ open, onClose, orderId, sourceItemId, sourceItem, defaultMode = 'duplicate', onComplete }) {
  const [mode, setMode] = useState(defaultMode);
  const [targetCategory, setTargetCategory] = useState('');
  const [carryOver, setCarryOver] = useState(CARRY_OVER_DEFAULTS);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!orderId || !sourceItemId) {
      toast.error('Missing order or source item');
      return;
    }
    if (mode === 'copy_to_category' && !targetCategory) {
      toast.error('Please pick a target category');
      return;
    }
    try {
      setSubmitting(true);
      const token = getAuthToken();
      const { data } = await axios.post(
        `${API}/job-tickets/${sourceItemId}/clone`,
        { mode, target_category: mode === 'copy_to_category' ? targetCategory : null, carry_over: carryOver },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(mode === 'duplicate' ? 'Item duplicated' : mode === 'variation' ? 'Variation created' : 'Converted to new category');
      onComplete?.(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Clone failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent className="max-w-lg" data-testid="clone-item-dialog">
        <DialogHeader>
          <DialogTitle>
            {mode === 'duplicate' ? 'Duplicate Item' : mode === 'variation' ? 'Create Variation' : 'Copy to New Category'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Mode switcher */}
          <div className="flex gap-2">
            {['duplicate', 'variation', 'copy_to_category'].map((m) => (
              <Button key={m} size="sm" variant={mode === m ? 'default' : 'outline'} onClick={() => setMode(m)} data-testid={`clone-mode-${m}`}>
                {m === 'duplicate' ? 'Duplicate' : m === 'variation' ? 'Variation' : 'Copy to Category'}
              </Button>
            ))}
          </div>

          {sourceItem && (
            <div className="text-xs bg-slate-50 border rounded p-2">
              <span className="text-gray-500">Source:</span>{' '}
              <span className="font-medium">{sourceItem.item_name || sourceItem.name}</span>{' '}
              <span className="text-gray-500">({(sourceItem.item_category || sourceItem.category || 'custom').replace(/_/g, ' ')})</span>
            </div>
          )}

          {mode === 'copy_to_category' && (
            <div>
              <Label className="text-xs text-gray-500">Target Category</Label>
              <Select value={targetCategory} onValueChange={setTargetCategory}>
                <SelectTrigger data-testid="clone-target-category"><SelectValue placeholder="Select target category" /></SelectTrigger>
                <SelectContent>
                  {TARGET_CATEGORIES.map((c) => (<SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>))}
                </SelectContent>
              </Select>
              <p className="text-[11px] text-gray-500 mt-1">
                Incompatible fields from the source category will be dropped automatically.
              </p>
            </div>
          )}

          <div>
            <Label className="text-xs text-gray-600 font-semibold">Carry Over From Source</Label>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {Object.entries(CARRY_OVER_LABELS).map(([k, label]) => (
                <div key={k} className="flex items-center gap-2 text-xs">
                  <Switch
                    checked={!!carryOver[k]}
                    onCheckedChange={(v) => setCarryOver((prev) => ({ ...prev, [k]: v }))}
                    data-testid={`clone-carry-${k}`}
                  />
                  <span>{label}</span>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-gray-500 italic mt-2">
              Pricing, cost outputs, status, and incompatible category fields always reset.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose} disabled={submitting} data-testid="clone-cancel">Cancel</Button>
          <Button onClick={handleSubmit} disabled={submitting} data-testid="clone-submit" className="bg-violet-600 hover:bg-violet-700 text-white">
            {submitting ? 'Cloning…' : 'Create Item'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
