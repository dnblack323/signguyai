import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import {
  ArrowLeft, Calculator, ChevronDown, ChevronUp, DollarSign, Edit2, Factory,
  Layers3, Loader2, Package, Plus, Save, ShieldCheck, Sparkles, Trash2,
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth, Permission } from '../context/AuthContext';
import { getAuthToken } from '../lib/authStorage';

const API = process.env.REACT_APP_BACKEND_URL;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

/* ────────── CONSTANTS ────────── */
const MATERIAL_CATEGORIES = [
  { value: 'print_material', label: 'Print / Banner' },
  { value: 'vinyl', label: 'Vinyl' },
  { value: 'substrate', label: 'Substrates / Boards' },
  { value: 'apparel', label: 'Apparel / Garments' },
  { value: 'decoration', label: 'Decoration Methods' },
  { value: 'lamination', label: 'Lamination' },
  { value: 'hardware', label: 'Hardware / Mounting' },
  { value: 'other', label: 'Other' },
];

const UNIT_TYPES = [
  { value: 'sqft', label: 'Per Sq Ft' },
  { value: 'each', label: 'Each' },
  { value: 'linear_ft', label: 'Per Linear Ft' },
  { value: 'per_color', label: 'Per Color' },
  { value: 'per_stitch', label: 'Per 1000 Stitches' },
  { value: 'per_sqin', label: 'Per Sq In' },
  { value: 'flat', label: 'Flat Rate' },
];

const ROUNDING_RULES = [
  { value: 'nearest_cent', label: 'Nearest Cent ($12.34)' },
  { value: 'nearest_dollar', label: 'Nearest Dollar ($12)' },
  { value: 'nearest_5', label: 'Nearest $5 ($10, $15)' },
  { value: 'nearest_10', label: 'Nearest $10 ($10, $20)' },
  { value: 'ceiling', label: 'Always Round Up' },
];

const CATEGORY_DEFS = [
  { key: 'cut_vinyl', label: 'Cut Vinyl', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'banners', label: 'Banners (Digital Print)', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'rigid_signs', label: 'Rigid Signs', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'vehicle_wraps', label: 'Vehicle Graphics / Wraps', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'apparel', label: 'Apparel', laborField: 'default_labor_hours_per_unit', laborLabel: 'Labor Hours / Item' },
  { key: 'services', label: 'Services', laborField: 'default_labor_hours', laborLabel: 'Default Labor Hours' },
  { key: 'custom', label: 'Custom / Miscellaneous', laborField: 'default_labor_hours_per_unit', laborLabel: 'Labor Hours / Item' },
  { key: 'digital_print', label: 'Digital Print (General)', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
];

/* ────────── HELPERS ────────── */
const n = (v) => Number(v || 0);
const f2 = (v) => n(v).toFixed(2);
const blankMaterial = (cat = '') => ({
  id: `mat-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
  key: '', name: '', category: cat || 'vinyl', subtype: '', brand: '',
  thickness: '', width_inches: 0, length_inches: 0, roll_sheet_size: '',
  purchase_unit: '', purchase_cost: 0, cost_per_unit: 0, unit_type: 'sqft',
  cost_per_sqft: 0, sell_rate_per_sqft: 0, waste_factor: 0,
  compatible_categories: [], is_active: true, notes: '',
});

/* ────────── GENERAL SHOP DEFAULTS TAB ────────── */
function ShopDefaultsTab({ settings, onChange, canEdit }) {
  const up = (field, value) => onChange({ ...settings, [field]: value });
  const Row = ({ label, field, prefix = '$', suffix = '', type = 'number', hint }) => (
    <div className="space-y-1">
      <Label className="text-xs text-gray-500">{label}</Label>
      <div className="relative">
        {prefix && <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">{prefix}</span>}
        <Input
          type={type}
          value={settings[field] ?? ''}
          onChange={(e) => up(field, type === 'number' ? n(e.target.value) : e.target.value)}
          disabled={!canEdit}
          className={`h-8 text-sm ${prefix ? 'pl-6' : ''} ${suffix ? 'pr-8' : ''}`}
          data-testid={`shop-default-${field}`}
        />
        {suffix && <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">{suffix}</span>}
      </div>
      {hint && <p className="text-[10px] text-gray-400">{hint}</p>}
    </div>
  );
  return (
    <div className="space-y-6" data-testid="shop-defaults-tab">
      {/* Labor Rates */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Labor Rates</CardTitle><CardDescription>Hourly rates used in cost and pricing calculations</CardDescription></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Production Rate" field="production_hourly_rate" suffix="/hr" hint="Shop floor production" />
          <Row label="Design Rate" field="design_hourly_rate" suffix="/hr" hint="Graphic design work" />
          <Row label="Install Rate" field="install_hourly_rate" suffix="/hr" hint="Field installation" />
          <Row label="Admin Rate" field="admin_hourly_rate" suffix="/hr" hint="Admin / office labor" />
        </CardContent>
      </Card>
      {/* Overhead / Waste / Markup */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Overhead, Waste & Markup</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Overhead %" field="overhead_percentage" prefix="" suffix="%" />
          <Row label="Shop Overhead / Hr" field="shop_overhead_per_hour" suffix="/hr" />
          <Row label="Waste %" field="waste_percentage" prefix="" suffix="%" hint="Added to material cost" />
          <Row label="Default Markup Multiplier" field="default_markup_multiplier" prefix="" suffix="x" />
          <Row label="Target Profit Margin" field="target_profit_margin_percent" prefix="" suffix="%" />
          <Row label="Material Markup %" field="material_markup_percent" prefix="" suffix="%" />
          <div className="flex items-center gap-3 col-span-2">
            <Switch
              checked={settings.apply_overhead_to_jobs ?? true}
              onCheckedChange={(v) => up('apply_overhead_to_jobs', v)}
              disabled={!canEdit}
              data-testid="shop-default-apply_overhead"
            />
            <Label className="text-sm">Apply overhead to order calculations</Label>
          </div>
        </CardContent>
      </Card>
      {/* Minimum Charges */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Minimum Charges</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Minimum Order" field="minimum_order" />
          <Row label="Minimum Design" field="minimum_design_charge" />
          <Row label="Minimum Install" field="minimum_install_charge" />
          <Row label="Min Vinyl" field="minimum_vinyl_charge" />
          <Row label="Min Print" field="minimum_print_charge" />
          <Row label="Min Sign" field="minimum_sign_charge" />
          <Row label="Min Service" field="minimum_service_charge" />
          <Row label="Min Wrap" field="minimum_wrap_charge" />
        </CardContent>
      </Card>
      {/* Rush / Setup / Rounding / Deposit */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Rush, Setup, Rounding & Deposit</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Rush Fee %" field="rush_fee_percentage" prefix="" suffix="%" hint="Added to total when rush" />
          <Row label="Default Setup Fee" field="setup_fee_default" />
          <Row label="Setup Fee — Vinyl" field="setup_fee_vinyl" />
          <Row label="Setup Fee — Print" field="setup_fee_print" />
          <Row label="Setup Fee — Screen" field="setup_fee_apparel_screen" />
          <Row label="Setup Fee — DTF" field="setup_fee_apparel_dtf" />
          <Row label="Deposit %" field="deposit_percentage" prefix="" suffix="%" hint="Displayed on quotes" />
          <div className="space-y-1">
            <Label className="text-xs text-gray-500">Rounding Rule</Label>
            <Select value={settings.rounding_rule || 'nearest_dollar'} onValueChange={(v) => up('rounding_rule', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="shop-default-rounding_rule"><SelectValue /></SelectTrigger>
              <SelectContent>{ROUNDING_RULES.map((r) => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Time Estimates and Travel */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Time Estimates & Travel</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Weeding Time / Sq Ft" field="weeding_time_per_sqft" prefix="" suffix="min" />
          <Row label="Application Time / Sq Ft" field="application_time_per_sqft" prefix="" suffix="min" />
          <Row label="Print Time / Sq Ft" field="print_time_per_sqft" prefix="" suffix="min" />
          <Row label="Laminate Time / Sq Ft" field="laminate_time_per_sqft" prefix="" suffix="min" />
          <Row label="Mileage Rate" field="mileage_rate" suffix="/mi" />
          <Row label="Min Travel Charge" field="minimum_travel_charge" />
          <Row label="Grommet Price (ea)" field="banner_grommet_price_each" />
          <Row label="Hemming Tape / Linear In" field="banner_hemming_tape_price_per_linear_inch" />
        </CardContent>
      </Card>
      {/* Quantity Breaks */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Quantity Breaks</CardTitle><CardDescription>Volume discount tiers applied automatically</CardDescription></CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-3 text-xs text-gray-500 mb-2 px-1">
            <span>Tier</span><span>Min Qty</span><span>Discount %</span><span />
          </div>
          {Object.entries(settings.quantity_breaks || {}).map(([key, val]) => (
            <div key={key} className="grid grid-cols-4 gap-3 mb-2 items-center">
              <span className="text-sm text-gray-700">{key.replace('_', ' ')}</span>
              <Input type="number" value={val?.min_qty ?? ''} onChange={(e) => {
                const qb = { ...settings.quantity_breaks, [key]: { ...val, min_qty: n(e.target.value) } };
                up('quantity_breaks', qb);
              }} className="h-8 text-sm" disabled={!canEdit} />
              <Input type="number" value={val?.discount_percent ?? ''} onChange={(e) => {
                const qb = { ...settings.quantity_breaks, [key]: { ...val, discount_percent: n(e.target.value) } };
                up('quantity_breaks', qb);
              }} className="h-8 text-sm" disabled={!canEdit} />
              <span />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

/* ────────── MATERIALS LIBRARY TAB ────────── */
function MaterialsLibraryTab({ materials, setMaterials, canEdit }) {
  const [expandedCat, setExpandedCat] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [newItem, setNewItem] = useState(null);

  const grouped = {};
  MATERIAL_CATEGORIES.forEach((c) => { grouped[c.value] = []; });
  (materials || []).forEach((m) => {
    const cat = m.category || 'other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(m);
  });

  const updateMaterial = (id, field, value) => {
    setMaterials((prev) => prev.map((m) => m.id === id ? { ...m, [field]: value } : m));
  };
  const removeMaterial = (id) => setMaterials((prev) => prev.filter((m) => m.id !== id));
  const addNewItem = () => {
    if (!newItem?.name || !newItem?.key) { toast.error('Name and key are required'); return; }
    setMaterials((prev) => [...prev, { ...newItem, id: newItem.id || `mat-${Date.now()}` }]);
    setNewItem(null);
    toast.success('Material added');
  };

  return (
    <div className="space-y-4" data-testid="materials-library-tab">
      {MATERIAL_CATEGORIES.map((cat) => {
        const items = grouped[cat.value] || [];
        const isOpen = expandedCat === cat.value;
        return (
          <Card key={cat.value}>
            <CardHeader className="pb-2 cursor-pointer" onClick={() => setExpandedCat(isOpen ? null : cat.value)}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Package className="h-4 w-4 text-gray-500" />
                  <CardTitle className="text-sm text-gray-900">{cat.label}</CardTitle>
                  <Badge variant="secondary" className="text-xs">{items.length}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  {canEdit && (
                    <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={(e) => { e.stopPropagation(); setNewItem(blankMaterial(cat.value)); setExpandedCat(cat.value); }} data-testid={`add-material-${cat.value}`}>
                      <Plus className="h-3 w-3 mr-1" /> Add
                    </Button>
                  )}
                  {isOpen ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                </div>
              </div>
            </CardHeader>
            {isOpen && (
              <CardContent className="pt-0">
                {items.length === 0 && !newItem && <p className="text-xs text-gray-400 py-2">No materials in this category.</p>}
                {items.map((mat) => (
                  <MaterialRow key={mat.id} mat={mat} editing={editingId === mat.id} canEdit={canEdit}
                    onToggleEdit={() => setEditingId(editingId === mat.id ? null : mat.id)}
                    onChange={(f, v) => updateMaterial(mat.id, f, v)}
                    onRemove={() => removeMaterial(mat.id)}
                  />
                ))}
                {/* New item form */}
                {newItem && newItem.category === cat.value && (
                  <div className="border border-dashed border-violet-300 rounded-lg p-3 mt-2 space-y-3 bg-violet-50/30">
                    <p className="text-xs font-medium text-violet-700">New Material</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <div><Label className="text-[10px]">Key *</Label><Input className="h-7 text-xs" value={newItem.key} onChange={(e) => setNewItem({ ...newItem, key: e.target.value })} placeholder="e.g. oracal_651" /></div>
                      <div><Label className="text-[10px]">Name *</Label><Input className="h-7 text-xs" value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} placeholder="Oracal 651" /></div>
                      <div><Label className="text-[10px]">Brand</Label><Input className="h-7 text-xs" value={newItem.brand} onChange={(e) => setNewItem({ ...newItem, brand: e.target.value })} /></div>
                      <div><Label className="text-[10px]">Subtype</Label><Input className="h-7 text-xs" value={newItem.subtype} onChange={(e) => setNewItem({ ...newItem, subtype: e.target.value })} /></div>
                      <div><Label className="text-[10px]">Cost / Unit</Label><Input type="number" className="h-7 text-xs" value={newItem.cost_per_unit} onChange={(e) => setNewItem({ ...newItem, cost_per_unit: n(e.target.value) })} /></div>
                      <div>
                        <Label className="text-[10px]">Unit Type</Label>
                        <Select value={newItem.unit_type} onValueChange={(v) => setNewItem({ ...newItem, unit_type: v })}>
                          <SelectTrigger className="h-7 text-xs"><SelectValue /></SelectTrigger>
                          <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                      <div><Label className="text-[10px]">Sell Rate / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={newItem.sell_rate_per_sqft} onChange={(e) => setNewItem({ ...newItem, sell_rate_per_sqft: n(e.target.value) })} /></div>
                      <div><Label className="text-[10px]">Waste Factor %</Label><Input type="number" className="h-7 text-xs" value={newItem.waste_factor} onChange={(e) => setNewItem({ ...newItem, waste_factor: n(e.target.value) })} /></div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" className="h-7 text-xs" onClick={addNewItem}><Plus className="h-3 w-3 mr-1" /> Save</Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setNewItem(null)}>Cancel</Button>
                    </div>
                  </div>
                )}
              </CardContent>
            )}
          </Card>
        );
      })}
    </div>
  );
}

function MaterialRow({ mat, editing, canEdit, onToggleEdit, onChange, onRemove }) {
  if (!editing) {
    return (
      <div className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0 group" data-testid={`material-row-${mat.id}`}>
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={`w-2 h-2 rounded-full ${mat.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{mat.name || mat.key}</p>
            <p className="text-[10px] text-gray-400 truncate">{mat.key}{mat.brand ? ` — ${mat.brand}` : ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-600">
          <span>${f2(mat.cost_per_unit)} / {mat.unit_type}</span>
          {n(mat.sell_rate_per_sqft) > 0 && <span className="text-green-600">Sell: ${f2(mat.sell_rate_per_sqft)}/sqft</span>}
          {canEdit && (
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={onToggleEdit}><Edit2 className="h-3 w-3" /></Button>
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-500" onClick={onRemove}><Trash2 className="h-3 w-3" /></Button>
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="border rounded-lg p-3 my-1.5 space-y-2 bg-gray-50" data-testid={`material-edit-${mat.id}`}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div><Label className="text-[10px]">Key</Label><Input className="h-7 text-xs" value={mat.key} onChange={(e) => onChange('key', e.target.value)} /></div>
        <div><Label className="text-[10px]">Name</Label><Input className="h-7 text-xs" value={mat.name} onChange={(e) => onChange('name', e.target.value)} /></div>
        <div><Label className="text-[10px]">Brand</Label><Input className="h-7 text-xs" value={mat.brand || ''} onChange={(e) => onChange('brand', e.target.value)} /></div>
        <div><Label className="text-[10px]">Subtype</Label><Input className="h-7 text-xs" value={mat.subtype || ''} onChange={(e) => onChange('subtype', e.target.value)} /></div>
        <div><Label className="text-[10px]">Thickness</Label><Input className="h-7 text-xs" value={mat.thickness || ''} onChange={(e) => onChange('thickness', e.target.value)} /></div>
        <div><Label className="text-[10px]">Width (in)</Label><Input type="number" className="h-7 text-xs" value={mat.width_inches || ''} onChange={(e) => onChange('width_inches', n(e.target.value))} /></div>
        <div><Label className="text-[10px]">Length (in)</Label><Input type="number" className="h-7 text-xs" value={mat.length_inches || ''} onChange={(e) => onChange('length_inches', n(e.target.value))} /></div>
        <div><Label className="text-[10px]">Roll / Sheet Size</Label><Input className="h-7 text-xs" value={mat.roll_sheet_size || ''} onChange={(e) => onChange('roll_sheet_size', e.target.value)} placeholder='e.g. 24"x50yd' /></div>
        <div><Label className="text-[10px]">Purchase Unit</Label><Input className="h-7 text-xs" value={mat.purchase_unit || ''} onChange={(e) => onChange('purchase_unit', e.target.value)} placeholder="roll, sheet, each" /></div>
        <div><Label className="text-[10px]">Purchase Cost</Label><Input type="number" className="h-7 text-xs" value={mat.purchase_cost || ''} onChange={(e) => onChange('purchase_cost', n(e.target.value))} /></div>
        <div><Label className="text-[10px]">Cost / Unit</Label><Input type="number" className="h-7 text-xs" value={mat.cost_per_unit} onChange={(e) => onChange('cost_per_unit', n(e.target.value))} /></div>
        <div>
          <Label className="text-[10px]">Unit Type</Label>
          <Select value={mat.unit_type} onValueChange={(v) => onChange('unit_type', v)}>
            <SelectTrigger className="h-7 text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div><Label className="text-[10px]">Cost / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={mat.cost_per_sqft || ''} onChange={(e) => onChange('cost_per_sqft', n(e.target.value))} /></div>
        <div><Label className="text-[10px]">Sell Rate / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={mat.sell_rate_per_sqft || ''} onChange={(e) => onChange('sell_rate_per_sqft', n(e.target.value))} /></div>
        <div><Label className="text-[10px]">Waste Factor %</Label><Input type="number" className="h-7 text-xs" value={mat.waste_factor || ''} onChange={(e) => onChange('waste_factor', n(e.target.value))} /></div>
        <div className="flex items-center gap-2 pt-4">
          <Switch checked={mat.is_active} onCheckedChange={(v) => onChange('is_active', v)} />
          <Label className="text-xs">{mat.is_active ? 'Active' : 'Inactive'}</Label>
        </div>
      </div>
      <div><Label className="text-[10px]">Notes</Label><Textarea className="text-xs min-h-[40px]" value={mat.notes || ''} onChange={(e) => onChange('notes', e.target.value)} /></div>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={onToggleEdit}>Done</Button>
    </div>
  );
}

/* ────────── CATEGORY PRICING RULES TAB ────────── */
function CategoryRulesTab({ settings, onChange, canEdit }) {
  const [openCat, setOpenCat] = useState('cut_vinyl');
  const cats = settings.category_defaults || {};
  const benchmarks = settings.selling_price_benchmarks || {};

  const setCatField = (catKey, field, value) => {
    onChange({
      ...settings,
      category_defaults: {
        ...cats,
        [catKey]: { ...(cats[catKey] || {}), [field]: value },
      },
    });
  };
  const setBenchField = (catKey, field, value) => {
    onChange({
      ...settings,
      selling_price_benchmarks: {
        ...benchmarks,
        [catKey]: { ...(benchmarks[catKey] || {}), [field]: value },
      },
    });
  };
  const F = ({ label, value, onChg, prefix = '$', suffix = '' }) => (
    <div className="space-y-0.5">
      <Label className="text-[10px] text-gray-500">{label}</Label>
      <div className="relative">
        {prefix && <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 text-[10px]">{prefix}</span>}
        <Input type="number" value={value ?? ''} onChange={(e) => onChg(n(e.target.value))} disabled={!canEdit}
          className={`h-7 text-xs ${prefix ? 'pl-5' : ''} ${suffix ? 'pr-7' : ''}`} />
        {suffix && <span className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 text-[10px]">{suffix}</span>}
      </div>
    </div>
  );

  return (
    <div className="space-y-3" data-testid="category-rules-tab">
      <div className="flex flex-wrap gap-1.5">
        {CATEGORY_DEFS.map((c) => (
          <Button key={c.key} size="sm" variant={openCat === c.key ? 'default' : 'outline'}
            className={`h-7 text-xs ${openCat === c.key ? 'bg-violet-600 text-white' : ''}`}
            onClick={() => setOpenCat(c.key)} data-testid={`category-tab-${c.key}`}>
            {c.label}
          </Button>
        ))}
      </div>
      {CATEGORY_DEFS.filter((c) => c.key === openCat).map((def) => {
        const cat = cats[def.key] || {};
        const bench = benchmarks[def.key] || {};
        return (
          <Card key={def.key}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-gray-900">{def.label}</CardTitle>
              <CardDescription>Production cost defaults, labor assumptions, and selling rate rules</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <F label={def.laborLabel} value={cat[def.laborField]} onChg={(v) => setCatField(def.key, def.laborField, v)} prefix="" suffix="hrs" />
                <F label="Markup Multiplier" value={cat.default_markup_multiplier} onChg={(v) => setCatField(def.key, 'default_markup_multiplier', v)} prefix="" suffix="x" />
                <F label="Target Margin %" value={cat.target_profit_margin_percent} onChg={(v) => setCatField(def.key, 'target_profit_margin_percent', v)} prefix="" suffix="%" />
                <F label="Minimum Charge" value={cat.minimum_charge} onChg={(v) => setCatField(def.key, 'minimum_charge', v)} />
              </div>
              {cat.default_material_keys?.length > 0 && (
                <div>
                  <Label className="text-[10px] text-gray-500">Default Materials</Label>
                  <div className="flex flex-wrap gap-1 mt-1">{cat.default_material_keys.map((k) => <Badge key={k} variant="secondary" className="text-[10px]">{k}</Badge>)}</div>
                </div>
              )}
              <div className="border-t pt-3">
                <p className="text-xs font-medium text-gray-700 mb-2">Selling Benchmarks</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {bench.average_sell_price_per_sqft !== undefined && <F label="Avg Sell / Sq Ft" value={bench.average_sell_price_per_sqft} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_sqft', v)} />}
                  {bench.average_sell_price_per_unit !== undefined && <F label="Avg Sell / Unit" value={bench.average_sell_price_per_unit} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_unit', v)} />}
                  {bench.average_sell_price_per_hour !== undefined && <F label="Avg Sell / Hour" value={bench.average_sell_price_per_hour} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_hour', v)} />}
                  <F label="Avg Order Total" value={bench.average_order_total} onChg={(v) => setBenchField(def.key, 'average_order_total', v)} />
                  <F label="Min Charge" value={bench.minimum_charge} onChg={(v) => setBenchField(def.key, 'minimum_charge', v)} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/* ────────── MAIN PAGE ────────── */
export default function PricingFoundation() {
  const { hasPermission, isOwner, isAdminOrOwner } = useAuth();
  const canView = hasPermission(Permission.SETTINGS_VIEW) || isAdminOrOwner();
  const canEdit = hasPermission(Permission.SETTINGS_EDIT) || isOwner();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [settings, setSettings] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [snapshotJson, setSnapshotJson] = useState('');

  const fetchAll = useCallback(async () => {
    const token = getAuthToken();
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/pricing/defaults`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSettings(data);
      setMaterials(data.materials || []);
      setSnapshotJson(JSON.stringify(data));
    } catch { toast.error('Failed to load pricing data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Detect changes
  useEffect(() => {
    if (!settings) return;
    const current = JSON.stringify({ ...settings, materials });
    setHasChanges(current !== snapshotJson);
  }, [settings, materials, snapshotJson]);

  const handleSettingsChange = (updated) => setSettings(updated);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...settings, materials };
      const res = await fetch(`${API}/api/pricing/defaults`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      const saved = await res.json();
      setSettings(saved);
      setMaterials(saved.materials || []);
      setSnapshotJson(JSON.stringify(saved));
      setHasChanges(false);
      toast.success('Pricing Foundation saved');
    } catch { toast.error('Failed to save'); }
    finally { setSaving(false); }
  };

  if (!canView) return <div className="p-8 text-center text-gray-500">You do not have permission to view pricing settings.</div>;
  if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;

  return (
    <div className="max-w-6xl mx-auto pb-12" data-testid="pricing-foundation-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link to="/pricing-calculator">
            <Button variant="ghost" size="sm"><ArrowLeft className="h-4 w-4 mr-1" /> Calculator</Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900" data-testid="pricing-foundation-title">Pricing Foundation</h1>
            <p className="text-sm text-gray-500">Single source of truth for all production costs, materials, and selling defaults</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && <Badge variant="outline" className="text-amber-600 border-amber-300" data-testid="unsaved-badge">Unsaved Changes</Badge>}
          <Link to="/settings/pricing-setup">
            <Button variant="outline" size="sm" className="gap-1" data-testid="import-invoices-link"><Sparkles className="h-3.5 w-3.5" /> Import Invoices</Button>
          </Link>
          {canEdit && (
            <Button onClick={handleSave} disabled={saving || !hasChanges} className="bg-violet-600 hover:bg-violet-700 text-white gap-1" data-testid="pricing-save-btn">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save All
            </Button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="defaults" className="space-y-4">
        <TabsList className="bg-gray-100 p-1">
          <TabsTrigger value="defaults" className="gap-1 text-sm" data-testid="tab-defaults"><DollarSign className="h-3.5 w-3.5" /> Shop Defaults</TabsTrigger>
          <TabsTrigger value="materials" className="gap-1 text-sm" data-testid="tab-materials"><Package className="h-3.5 w-3.5" /> Materials Library</TabsTrigger>
          <TabsTrigger value="categories" className="gap-1 text-sm" data-testid="tab-categories"><Layers3 className="h-3.5 w-3.5" /> Category Rules</TabsTrigger>
        </TabsList>

        <TabsContent value="defaults">
          <ShopDefaultsTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="materials">
          <MaterialsLibraryTab materials={materials} setMaterials={setMaterials} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="categories">
          <CategoryRulesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
