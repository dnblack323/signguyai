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
  ArrowLeft, BarChart3, Calculator, ChevronDown, ChevronUp, ClipboardCheck, DollarSign, Edit2, Factory,
  Layers3, Loader2, Package, Plus, Save, Settings2, Sparkles, Trash2, Wrench,
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

const HARDWARE_CATEGORIES = [
  { value: 'mounting', label: 'Mounting / Fasteners' },
  { value: 'frames', label: 'Frames & Stands' },
  { value: 'electrical', label: 'Electrical / Lighting' },
  { value: 'hardware', label: 'General Hardware' },
  { value: 'accessories', label: 'Accessories' },
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

const AI_FALLBACK_OPTIONS = [
  { value: 'allow', label: 'Allow AI fallback' },
  { value: 'warn', label: 'Allow with warning' },
  { value: 'block', label: 'Block fallback' },
];

const CUT_VINYL_USE_TYPES = [
  { value: 'indoor', label: 'Indoor' },
  { value: 'outdoor', label: 'Outdoor' },
  { value: 'wall', label: 'Wall' },
  { value: 'glass_window', label: 'Glass / Window' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'specialty', label: 'Specialty' },
];

const CUT_VINYL_WEEDING_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];

const CUT_VINYL_DESIGN_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];

const CUT_VINYL_INSTALL_LEVELS = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'difficult', label: 'Difficult' },
  { value: 'extreme', label: 'Extreme' },
];

const CUT_VINYL_SURFACE_TYPES = [
  { value: 'flat_smooth', label: 'Flat Smooth' },
  { value: 'glass_window', label: 'Glass / Window' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'textured_rough', label: 'Textured / Rough' },
  { value: 'curved_awkward', label: 'Curved / Awkward' },
];

const CUT_VINYL_UNIT_OPTIONS = [
  { value: 'inches', label: 'Inches' },
  { value: 'feet', label: 'Feet' },
];

const CATEGORY_DEFS = [
  { key: 'digital_print', label: 'Digital Print', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'cut_vinyl', label: 'Cut Vinyl', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'rigid_signs', label: 'Rigid Signs', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'banners', label: 'Banners', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'vehicle_wraps', label: 'Vehicle Graphics / Wraps', laborField: 'default_labor_hours_per_sqft', laborLabel: 'Labor Hours / Sq Ft' },
  { key: 'apparel', label: 'Apparel', laborField: 'default_labor_hours_per_unit', laborLabel: 'Labor Hours / Item' },
  { key: 'services', label: 'Services', laborField: 'default_labor_hours', laborLabel: 'Default Labor Hours' },
  { key: 'custom', label: 'Custom / Miscellaneous', laborField: 'default_labor_hours_per_unit', laborLabel: 'Labor Hours / Item' },
];

const LABOR_RATE_TYPES = [
  { key: 'design', label: 'Design' },
  { key: 'production', label: 'Production' },
  { key: 'finishing', label: 'Finishing' },
  { key: 'installation', label: 'Installation' },
  { key: 'removal', label: 'Removal' },
  { key: 'travel', label: 'Travel' },
  { key: 'admin_project_handling', label: 'Admin / Project Handling' },
  { key: 'consultation', label: 'Consultation' },
  { key: 'site_survey', label: 'Site Survey' },
  { key: 'other_labor', label: 'Other Labor' },
];

/* ────────── HELPERS ────────── */
const n = (v) => Number(v || 0);
const f2 = (v) => n(v).toFixed(2);
const parseCsvList = (value) => String(value || '')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean);
const listToCsv = (value) => (value || []).join(', ');
const blankMaterial = (cat = '') => ({
  id: `mat-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
  key: '', name: '', category: cat || 'vinyl', subtype: '', brand: '', vendor: '',
  thickness: '', width_inches: 0, length_inches: 0, roll_sheet_size: '',
  purchase_unit: '', purchase_cost: 0, cost_per_unit: 0, unit_type: 'sqft',
  cost_per_sqft: 0, cost_per_linear_foot: 0, sell_rate_per_sqft: 0,
  waste_factor: 0, waste_override: 0, compatible_categories: [], is_active: true, notes: '',
});
const blankHardware = (cat = '') => ({
  id: `hw-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
  name: '', category: cat || 'hardware', subcategory: '', unit_type: 'each',
  purchase_cost: 0, default_sell_price: 0, default_labor_addon_minutes: 0,
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
          <Row label="Removal Rate" field="removal_hourly_rate" suffix="/hr" hint="Removal labor" />
          <Row label="Travel Rate" field="travel_hourly_rate" suffix="/hr" hint="Travel labor" />
          <Row label="Admin Rate" field="admin_hourly_rate" suffix="/hr" hint="Admin / office labor" />
          <Row label="Project Handling" field="project_handling_hourly_rate" suffix="/hr" hint="Project management" />
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
          <Row label="Minimum Removal" field="minimum_removal_charge" />
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
          <Row label="Rush Flat Fee" field="rush_fee_flat" />
          <Row label="Default Setup Fee" field="setup_fee_default" />
          <Row label="File Cleanup Fee" field="file_cleanup_fee_default" />
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
              <Input
                type="number"
                value={val?.min_qty ?? ''}
                onChange={(e) => {
                  const qb = { ...settings.quantity_breaks, [key]: { ...val, min_qty: n(e.target.value) } };
                  up('quantity_breaks', qb);
                }}
                className="h-8 text-sm"
                disabled={!canEdit}
                data-testid={`quantity-break-${key}-min`}
              />
              <Input
                type="number"
                value={val?.discount_percent ?? ''}
                onChange={(e) => {
                  const qb = { ...settings.quantity_breaks, [key]: { ...val, discount_percent: n(e.target.value) } };
                  up('quantity_breaks', qb);
                }}
                className="h-8 text-sm"
                disabled={!canEdit}
                data-testid={`quantity-break-${key}-discount`}
              />
              <span />
            </div>
          ))}
        </CardContent>
      </Card>
      {/* Complexity & AI Fallbacks */}
      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">Complexity & AI Fallbacks</CardTitle><CardDescription>Default multipliers and fallback behavior for AI estimates</CardDescription></CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Row label="Complexity Base" field="complexity_multiplier_base" prefix="" suffix="x" />
          <Row label="Complexity Max" field="complexity_multiplier_max" prefix="" suffix="x" />
          <Row label="Install Complexity Base" field="install_complexity_multiplier_base" prefix="" suffix="x" />
          <Row label="Install Complexity Max" field="install_complexity_multiplier_max" prefix="" suffix="x" />
          <div className="space-y-1 col-span-2">
            <Label className="text-xs text-gray-500">AI Fallback Behavior</Label>
            <Select value={settings.ai_fallback_behavior || 'warn'} onValueChange={(v) => up('ai_fallback_behavior', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="shop-default-ai-fallback-behavior"><SelectValue /></SelectTrigger>
              <SelectContent>{AI_FALLBACK_OPTIONS.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-3 col-span-2">
            <Switch
              checked={settings.ai_fallback_warnings_enabled ?? true}
              onCheckedChange={(v) => up('ai_fallback_warnings_enabled', v)}
              disabled={!canEdit}
              data-testid="shop-default-ai-fallback-warnings"
            />
            <Label className="text-sm">Show warnings when fallback rules are used</Label>
          </div>
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
                      <div><Label className="text-[10px]">Key *</Label><Input className="h-7 text-xs" value={newItem.key} onChange={(e) => setNewItem({ ...newItem, key: e.target.value })} placeholder="e.g. oracal_651" data-testid="new-material-key" /></div>
                      <div><Label className="text-[10px]">Name *</Label><Input className="h-7 text-xs" value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} placeholder="Oracal 651" data-testid="new-material-name" /></div>
                      <div><Label className="text-[10px]">Brand</Label><Input className="h-7 text-xs" value={newItem.brand} onChange={(e) => setNewItem({ ...newItem, brand: e.target.value })} data-testid="new-material-brand" /></div>
                      <div><Label className="text-[10px]">Vendor</Label><Input className="h-7 text-xs" value={newItem.vendor || ''} onChange={(e) => setNewItem({ ...newItem, vendor: e.target.value })} data-testid="new-material-vendor" /></div>
                      <div><Label className="text-[10px]">Subtype</Label><Input className="h-7 text-xs" value={newItem.subtype} onChange={(e) => setNewItem({ ...newItem, subtype: e.target.value })} data-testid="new-material-subtype" /></div>
                      <div><Label className="text-[10px]">Cost / Unit</Label><Input type="number" className="h-7 text-xs" value={newItem.cost_per_unit} onChange={(e) => setNewItem({ ...newItem, cost_per_unit: n(e.target.value) })} data-testid="new-material-cost-per-unit" /></div>
                      <div><Label className="text-[10px]">Cost / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={newItem.cost_per_sqft || ''} onChange={(e) => setNewItem({ ...newItem, cost_per_sqft: n(e.target.value) })} data-testid="new-material-cost-per-sqft" /></div>
                      <div><Label className="text-[10px]">Cost / Linear Ft</Label><Input type="number" className="h-7 text-xs" value={newItem.cost_per_linear_foot || ''} onChange={(e) => setNewItem({ ...newItem, cost_per_linear_foot: n(e.target.value) })} data-testid="new-material-cost-per-linear-ft" /></div>
                      <div>
                        <Label className="text-[10px]">Unit Type</Label>
                        <Select value={newItem.unit_type} onValueChange={(v) => setNewItem({ ...newItem, unit_type: v })}>
                          <SelectTrigger className="h-7 text-xs" data-testid="new-material-unit-type"><SelectValue /></SelectTrigger>
                          <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                      <div><Label className="text-[10px]">Sell Rate / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={newItem.sell_rate_per_sqft} onChange={(e) => setNewItem({ ...newItem, sell_rate_per_sqft: n(e.target.value) })} data-testid="new-material-sell-rate" /></div>
                      <div><Label className="text-[10px]">Waste Factor %</Label><Input type="number" className="h-7 text-xs" value={newItem.waste_factor || ''} onChange={(e) => setNewItem({ ...newItem, waste_factor: n(e.target.value) })} data-testid="new-material-waste-factor" /></div>
                      <div><Label className="text-[10px]">Waste Override %</Label><Input type="number" className="h-7 text-xs" value={newItem.waste_override || ''} onChange={(e) => setNewItem({ ...newItem, waste_override: n(e.target.value) })} data-testid="new-material-waste-override" /></div>
                      <div className="col-span-2"><Label className="text-[10px]">Compatible Categories</Label><Input className="h-7 text-xs" value={listToCsv(newItem.compatible_categories)} onChange={(e) => setNewItem({ ...newItem, compatible_categories: parseCsvList(e.target.value) })} placeholder="cut_vinyl, banners" data-testid="new-material-compatible" /></div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" className="h-7 text-xs" onClick={addNewItem} data-testid="new-material-save"><Plus className="h-3 w-3 mr-1" /> Save</Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setNewItem(null)} data-testid="new-material-cancel">Cancel</Button>
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
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={onToggleEdit} data-testid={`material-edit-toggle-${mat.id}`}><Edit2 className="h-3 w-3" /></Button>
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-500" onClick={onRemove} data-testid={`material-delete-${mat.id}`}><Trash2 className="h-3 w-3" /></Button>
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="border rounded-lg p-3 my-1.5 space-y-2 bg-gray-50" data-testid={`material-edit-${mat.id}`}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div><Label className="text-[10px]">Key</Label><Input className="h-7 text-xs" value={mat.key} onChange={(e) => onChange('key', e.target.value)} data-testid={`material-${mat.id}-key`} /></div>
        <div><Label className="text-[10px]">Name</Label><Input className="h-7 text-xs" value={mat.name} onChange={(e) => onChange('name', e.target.value)} data-testid={`material-${mat.id}-name`} /></div>
        <div><Label className="text-[10px]">Brand</Label><Input className="h-7 text-xs" value={mat.brand || ''} onChange={(e) => onChange('brand', e.target.value)} data-testid={`material-${mat.id}-brand`} /></div>
        <div><Label className="text-[10px]">Vendor</Label><Input className="h-7 text-xs" value={mat.vendor || ''} onChange={(e) => onChange('vendor', e.target.value)} data-testid={`material-${mat.id}-vendor`} /></div>
        <div><Label className="text-[10px]">Subtype</Label><Input className="h-7 text-xs" value={mat.subtype || ''} onChange={(e) => onChange('subtype', e.target.value)} data-testid={`material-${mat.id}-subtype`} /></div>
        <div><Label className="text-[10px]">Thickness</Label><Input className="h-7 text-xs" value={mat.thickness || ''} onChange={(e) => onChange('thickness', e.target.value)} data-testid={`material-${mat.id}-thickness`} /></div>
        <div><Label className="text-[10px]">Width (in)</Label><Input type="number" className="h-7 text-xs" value={mat.width_inches || ''} onChange={(e) => onChange('width_inches', n(e.target.value))} data-testid={`material-${mat.id}-width`} /></div>
        <div><Label className="text-[10px]">Length (in)</Label><Input type="number" className="h-7 text-xs" value={mat.length_inches || ''} onChange={(e) => onChange('length_inches', n(e.target.value))} data-testid={`material-${mat.id}-length`} /></div>
        <div><Label className="text-[10px]">Roll / Sheet Size</Label><Input className="h-7 text-xs" value={mat.roll_sheet_size || ''} onChange={(e) => onChange('roll_sheet_size', e.target.value)} placeholder='e.g. 24"x50yd' data-testid={`material-${mat.id}-roll-size`} /></div>
        <div><Label className="text-[10px]">Purchase Unit</Label><Input className="h-7 text-xs" value={mat.purchase_unit || ''} onChange={(e) => onChange('purchase_unit', e.target.value)} placeholder="roll, sheet, each" data-testid={`material-${mat.id}-purchase-unit`} /></div>
        <div><Label className="text-[10px]">Purchase Cost</Label><Input type="number" className="h-7 text-xs" value={mat.purchase_cost || ''} onChange={(e) => onChange('purchase_cost', n(e.target.value))} data-testid={`material-${mat.id}-purchase-cost`} /></div>
        <div><Label className="text-[10px]">Cost / Unit</Label><Input type="number" className="h-7 text-xs" value={mat.cost_per_unit} onChange={(e) => onChange('cost_per_unit', n(e.target.value))} data-testid={`material-${mat.id}-cost-unit`} /></div>
        <div>
          <Label className="text-[10px]">Unit Type</Label>
          <Select value={mat.unit_type} onValueChange={(v) => onChange('unit_type', v)}>
            <SelectTrigger className="h-7 text-xs" data-testid={`material-${mat.id}-unit-type`}><SelectValue /></SelectTrigger>
            <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div><Label className="text-[10px]">Cost / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={mat.cost_per_sqft || ''} onChange={(e) => onChange('cost_per_sqft', n(e.target.value))} data-testid={`material-${mat.id}-cost-sqft`} /></div>
        <div><Label className="text-[10px]">Cost / Linear Ft</Label><Input type="number" className="h-7 text-xs" value={mat.cost_per_linear_foot || ''} onChange={(e) => onChange('cost_per_linear_foot', n(e.target.value))} data-testid={`material-${mat.id}-cost-linear`} /></div>
        <div><Label className="text-[10px]">Sell Rate / Sq Ft</Label><Input type="number" className="h-7 text-xs" value={mat.sell_rate_per_sqft || ''} onChange={(e) => onChange('sell_rate_per_sqft', n(e.target.value))} data-testid={`material-${mat.id}-sell-rate`} /></div>
        <div><Label className="text-[10px]">Waste Factor %</Label><Input type="number" className="h-7 text-xs" value={mat.waste_factor || ''} onChange={(e) => onChange('waste_factor', n(e.target.value))} data-testid={`material-${mat.id}-waste-factor`} /></div>
        <div><Label className="text-[10px]">Waste Override %</Label><Input type="number" className="h-7 text-xs" value={mat.waste_override || ''} onChange={(e) => onChange('waste_override', n(e.target.value))} data-testid={`material-${mat.id}-waste-override`} /></div>
        <div className="col-span-2"><Label className="text-[10px]">Compatible Categories</Label><Input className="h-7 text-xs" value={listToCsv(mat.compatible_categories)} onChange={(e) => onChange('compatible_categories', parseCsvList(e.target.value))} placeholder="cut_vinyl, banners" data-testid={`material-${mat.id}-compatible`} /></div>
        <div className="flex items-center gap-2 pt-4">
          <Switch checked={mat.is_active} onCheckedChange={(v) => onChange('is_active', v)} data-testid={`material-${mat.id}-active`} />
          <Label className="text-xs">{mat.is_active ? 'Active' : 'Inactive'}</Label>
        </div>
      </div>
      <div><Label className="text-[10px]">Notes</Label><Textarea className="text-xs min-h-[40px]" value={mat.notes || ''} onChange={(e) => onChange('notes', e.target.value)} data-testid={`material-${mat.id}-notes`} /></div>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={onToggleEdit} data-testid={`material-${mat.id}-done`}>Done</Button>
    </div>
  );
}

/* ────────── HARDWARE & ACCESSORIES TAB ────────── */
function HardwareAccessoriesTab({ items, setItems, canEdit }) {
  const [expandedCat, setExpandedCat] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [newItem, setNewItem] = useState(null);

  const categoryList = [...HARDWARE_CATEGORIES];
  (items || []).forEach((item) => {
    if (item?.category && !categoryList.find((c) => c.value === item.category)) {
      categoryList.push({ value: item.category, label: item.category });
    }
  });

  const grouped = {};
  categoryList.forEach((c) => { grouped[c.value] = []; });
  (items || []).forEach((item) => {
    const cat = item.category || 'other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  });

  const updateItem = (id, field, value) => {
    setItems((prev) => prev.map((item) => item.id === id ? { ...item, [field]: value } : item));
  };
  const removeItem = (id) => setItems((prev) => prev.filter((item) => item.id !== id));
  const addNewItem = () => {
    if (!newItem?.name) { toast.error('Name is required'); return; }
    setItems((prev) => [...prev, { ...newItem, id: newItem.id || `hw-${Date.now()}` }]);
    setNewItem(null);
    toast.success('Hardware item added');
  };

  return (
    <div className="space-y-4" data-testid="hardware-library-tab">
      {categoryList.map((cat) => {
        const catKey = cat.value;
        const itemsInCat = grouped[catKey] || [];
        const isOpen = expandedCat === catKey;
        if (!itemsInCat.length && !newItem) return null;
        return (
          <Card key={catKey}>
            <CardHeader className="pb-2 cursor-pointer" onClick={() => setExpandedCat(isOpen ? null : catKey)}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-gray-500" />
                  <CardTitle className="text-sm text-gray-900">{cat.label}</CardTitle>
                  <Badge variant="secondary" className="text-xs">{itemsInCat.length}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  {canEdit && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 text-xs"
                      onClick={(e) => { e.stopPropagation(); setNewItem(blankHardware(catKey)); setExpandedCat(catKey); }}
                      data-testid={`add-hardware-${catKey}`}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add
                    </Button>
                  )}
                  {isOpen ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                </div>
              </div>
            </CardHeader>
            {isOpen && (
              <CardContent className="pt-0">
                {itemsInCat.length === 0 && !newItem && <p className="text-xs text-gray-400 py-2">No hardware in this category.</p>}
                {itemsInCat.map((item) => (
                  <HardwareRow
                    key={item.id}
                    item={item}
                    editing={editingId === item.id}
                    canEdit={canEdit}
                    onToggleEdit={() => setEditingId(editingId === item.id ? null : item.id)}
                    onChange={(field, value) => updateItem(item.id, field, value)}
                    onRemove={() => removeItem(item.id)}
                  />
                ))}
                {newItem && newItem.category === catKey && (
                  <div className="border border-dashed border-amber-300 rounded-lg p-3 mt-2 space-y-3 bg-amber-50/40">
                    <p className="text-xs font-medium text-amber-700">New Hardware / Accessory</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <div><Label className="text-[10px]">Name *</Label><Input className="h-7 text-xs" value={newItem.name} onChange={(e) => setNewItem({ ...newItem, name: e.target.value })} data-testid="new-hardware-name" /></div>
                      <div><Label className="text-[10px]">Category</Label><Input className="h-7 text-xs" value={newItem.category} onChange={(e) => setNewItem({ ...newItem, category: e.target.value })} data-testid="new-hardware-category" /></div>
                      <div><Label className="text-[10px]">Subcategory</Label><Input className="h-7 text-xs" value={newItem.subcategory} onChange={(e) => setNewItem({ ...newItem, subcategory: e.target.value })} data-testid="new-hardware-subcategory" /></div>
                      <div>
                        <Label className="text-[10px]">Unit Type</Label>
                        <Select value={newItem.unit_type} onValueChange={(v) => setNewItem({ ...newItem, unit_type: v })}>
                          <SelectTrigger className="h-7 text-xs" data-testid="new-hardware-unit-type"><SelectValue /></SelectTrigger>
                          <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
                        </Select>
                      </div>
                      <div><Label className="text-[10px]">Purchase Cost</Label><Input type="number" className="h-7 text-xs" value={newItem.purchase_cost || ''} onChange={(e) => setNewItem({ ...newItem, purchase_cost: n(e.target.value) })} data-testid="new-hardware-purchase-cost" /></div>
                      <div><Label className="text-[10px]">Default Sell Price</Label><Input type="number" className="h-7 text-xs" value={newItem.default_sell_price || ''} onChange={(e) => setNewItem({ ...newItem, default_sell_price: n(e.target.value) })} data-testid="new-hardware-sell-price" /></div>
                      <div><Label className="text-[10px]">Labor Add-on (min)</Label><Input type="number" className="h-7 text-xs" value={newItem.default_labor_addon_minutes || ''} onChange={(e) => setNewItem({ ...newItem, default_labor_addon_minutes: n(e.target.value) })} data-testid="new-hardware-labor-addon" /></div>
                      <div className="col-span-2"><Label className="text-[10px]">Compatible Categories</Label><Input className="h-7 text-xs" value={listToCsv(newItem.compatible_categories)} onChange={(e) => setNewItem({ ...newItem, compatible_categories: parseCsvList(e.target.value) })} placeholder="banners, rigid_signs" data-testid="new-hardware-compatible" /></div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" className="h-7 text-xs" onClick={addNewItem} data-testid="new-hardware-save"><Plus className="h-3 w-3 mr-1" /> Save</Button>
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => setNewItem(null)} data-testid="new-hardware-cancel">Cancel</Button>
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

function HardwareRow({ item, editing, canEdit, onToggleEdit, onChange, onRemove }) {
  if (!editing) {
    return (
      <div className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0 group" data-testid={`hardware-row-${item.id}`}>
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={`w-2 h-2 rounded-full ${item.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{item.name}</p>
            <p className="text-[10px] text-gray-400 truncate">{item.category}{item.subcategory ? ` — ${item.subcategory}` : ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-600">
          <span>${f2(item.purchase_cost)} / {item.unit_type}</span>
          {n(item.default_sell_price) > 0 && <span className="text-emerald-600">Sell: ${f2(item.default_sell_price)}</span>}
          {canEdit && (
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={onToggleEdit} data-testid={`hardware-edit-toggle-${item.id}`}><Edit2 className="h-3 w-3" /></Button>
              <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-500" onClick={onRemove} data-testid={`hardware-delete-${item.id}`}><Trash2 className="h-3 w-3" /></Button>
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className="border rounded-lg p-3 my-1.5 space-y-2 bg-gray-50" data-testid={`hardware-edit-${item.id}`}>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div><Label className="text-[10px]">Name</Label><Input className="h-7 text-xs" value={item.name} onChange={(e) => onChange('name', e.target.value)} data-testid={`hardware-${item.id}-name`} /></div>
        <div><Label className="text-[10px]">Category</Label><Input className="h-7 text-xs" value={item.category || ''} onChange={(e) => onChange('category', e.target.value)} data-testid={`hardware-${item.id}-category`} /></div>
        <div><Label className="text-[10px]">Subcategory</Label><Input className="h-7 text-xs" value={item.subcategory || ''} onChange={(e) => onChange('subcategory', e.target.value)} data-testid={`hardware-${item.id}-subcategory`} /></div>
        <div>
          <Label className="text-[10px]">Unit Type</Label>
          <Select value={item.unit_type} onValueChange={(v) => onChange('unit_type', v)}>
            <SelectTrigger className="h-7 text-xs" data-testid={`hardware-${item.id}-unit-type`}><SelectValue /></SelectTrigger>
            <SelectContent>{UNIT_TYPES.map((u) => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div><Label className="text-[10px]">Purchase Cost</Label><Input type="number" className="h-7 text-xs" value={item.purchase_cost || ''} onChange={(e) => onChange('purchase_cost', n(e.target.value))} data-testid={`hardware-${item.id}-purchase-cost`} /></div>
        <div><Label className="text-[10px]">Default Sell Price</Label><Input type="number" className="h-7 text-xs" value={item.default_sell_price || ''} onChange={(e) => onChange('default_sell_price', n(e.target.value))} data-testid={`hardware-${item.id}-sell-price`} /></div>
        <div><Label className="text-[10px]">Labor Add-on (min)</Label><Input type="number" className="h-7 text-xs" value={item.default_labor_addon_minutes || ''} onChange={(e) => onChange('default_labor_addon_minutes', n(e.target.value))} data-testid={`hardware-${item.id}-labor-addon`} /></div>
        <div className="col-span-2"><Label className="text-[10px]">Compatible Categories</Label><Input className="h-7 text-xs" value={listToCsv(item.compatible_categories)} onChange={(e) => onChange('compatible_categories', parseCsvList(e.target.value))} data-testid={`hardware-${item.id}-compatible`} /></div>
        <div className="flex items-center gap-2 pt-4">
          <Switch checked={item.is_active} onCheckedChange={(v) => onChange('is_active', v)} data-testid={`hardware-${item.id}-active`} />
          <Label className="text-xs">{item.is_active ? 'Active' : 'Inactive'}</Label>
        </div>
      </div>
      <div><Label className="text-[10px]">Notes</Label><Textarea className="text-xs min-h-[40px]" value={item.notes || ''} onChange={(e) => onChange('notes', e.target.value)} data-testid={`hardware-${item.id}-notes`} /></div>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={onToggleEdit} data-testid={`hardware-${item.id}-done`}>Done</Button>
    </div>
  );
}

/* ────────── CATEGORY PRICING RULES TAB ────────── */
function CategoryRulesTab({ settings, onChange, canEdit, materials }) {
  const [openCat, setOpenCat] = useState('digital_print');
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
  const F = ({ label, value, onChg, prefix = '$', suffix = '', testId }) => (
    <div className="space-y-0.5">
      <Label className="text-[10px] text-gray-500">{label}</Label>
      <div className="relative">
        {prefix && <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 text-[10px]">{prefix}</span>}
        <Input
          type="number"
          value={value ?? ''}
          onChange={(e) => onChg(n(e.target.value))}
          disabled={!canEdit}
          className={`h-7 text-xs ${prefix ? 'pl-5' : ''} ${suffix ? 'pr-7' : ''}`}
          data-testid={testId}
        />
        {suffix && <span className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 text-[10px]">{suffix}</span>}
      </div>
    </div>
  );

  const dpMediaOptions = (materials || []).filter((m) => (
    m.category === 'print_media'
  ));
  const dpLaminateOptions = (materials || []).filter((m) => (
    m.category === 'laminate'
  ));
  const cvVinylOptions = (materials || []).filter((m) => m.category === 'cut_vinyl');
  const rigidSubstrateOptions = (materials || []).filter((m) => m.category === 'substrate');
  const rigidFinishOptions = (materials || []).filter((m) => m.category === 'rigid_finish' || m.category === 'finish');
  const rigidGraphicOptions = (materials || []).filter((m) => m.category === 'rigid_graphic');
  const rigidVinylOptions = (materials || []).filter((m) => m.category === 'cut_vinyl');

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
        const dpTiers = cat.quantity_discounts || [
          { min_qty: 1, max_qty: 4, discount_percent: 0 },
          { min_qty: 5, max_qty: 24, discount_percent: 5 },
          { min_qty: 25, max_qty: 99, discount_percent: 10 },
          { min_qty: 100, max_qty: null, discount_percent: 15 },
        ];
        const updateDpTier = (idx, field, value) => {
          const next = dpTiers.map((tier, i) => (i === idx ? { ...tier, [field]: value } : tier));
          setCatField(def.key, 'quantity_discounts', next);
        };
        const cvTiers = cat.quantity_discounts || [
          { min_qty: 1, max_qty: 5, discount_percent: 0 },
          { min_qty: 6, max_qty: 24, discount_percent: 5 },
          { min_qty: 25, max_qty: 99, discount_percent: 10 },
          { min_qty: 100, max_qty: null, discount_percent: 15 },
        ];
        const updateCvTier = (idx, field, value) => {
          const next = cvTiers.map((tier, i) => (i === idx ? { ...tier, [field]: value } : tier));
          setCatField(def.key, 'quantity_discounts', next);
        };
        const rsTiers = cat.quantity_discounts || [
          { min_qty: 1, max_qty: 4, discount_percent: 0 },
          { min_qty: 5, max_qty: 24, discount_percent: 5 },
          { min_qty: 25, max_qty: 99, discount_percent: 10 },
          { min_qty: 100, max_qty: null, discount_percent: 15 },
        ];
        const updateRsTier = (idx, field, value) => {
          const next = rsTiers.map((tier, i) => (i === idx ? { ...tier, [field]: value } : tier));
          setCatField(def.key, 'quantity_discounts', next);
        };
        return (
          <Card key={def.key}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base text-gray-900">{def.label}</CardTitle>
              <CardDescription>Production cost defaults, labor assumptions, and selling rate rules</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <F label={def.laborLabel} value={cat[def.laborField]} onChg={(v) => setCatField(def.key, def.laborField, v)} prefix="" suffix="hrs" testId={`category-${def.key}-labor`} />
                <F label="Markup Multiplier" value={cat.default_markup_multiplier} onChg={(v) => setCatField(def.key, 'default_markup_multiplier', v)} prefix="" suffix="x" testId={`category-${def.key}-markup`} />
                <F label="Target Margin %" value={cat.target_profit_margin_percent} onChg={(v) => setCatField(def.key, 'target_profit_margin_percent', v)} prefix="" suffix="%" testId={`category-${def.key}-margin`} />
                <F label="Minimum Charge" value={cat.minimum_charge} onChg={(v) => setCatField(def.key, 'minimum_charge', v)} testId={`category-${def.key}-min-charge`} />
                <F
                  label="Sell Rate Default"
                  value={(cat.sell_rate_defaults || {}).base_rate}
                  onChg={(v) => setCatField(def.key, 'sell_rate_defaults', { ...(cat.sell_rate_defaults || {}), base_rate: v })}
                  testId={`category-${def.key}-sell-rate-default`}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <Label className="text-[10px] text-gray-500">Default Material Keys</Label>
                  <Input
                    className="h-7 text-xs"
                    value={listToCsv(cat.default_material_keys)}
                    onChange={(e) => setCatField(def.key, 'default_material_keys', parseCsvList(e.target.value))}
                    placeholder="vinyl, banner_material"
                    data-testid={`category-${def.key}-materials`}
                    disabled={!canEdit}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Default Hardware Keys</Label>
                  <Input
                    className="h-7 text-xs"
                    value={listToCsv(cat.default_hardware_keys)}
                    onChange={(e) => setCatField(def.key, 'default_hardware_keys', parseCsvList(e.target.value))}
                    placeholder="grommets, stakes"
                    data-testid={`category-${def.key}-hardware`}
                    disabled={!canEdit}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Default Labor Types</Label>
                  <Input
                    className="h-7 text-xs"
                    value={listToCsv(cat.default_labor_types)}
                    onChange={(e) => setCatField(def.key, 'default_labor_types', parseCsvList(e.target.value))}
                    placeholder="production, installation"
                    data-testid={`category-${def.key}-labor-types`}
                    disabled={!canEdit}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">AI Prefill Overrides</Label>
                  <Textarea
                    className="text-xs min-h-[40px]"
                    value={typeof cat.ai_prefill_overrides === 'string' ? cat.ai_prefill_overrides : JSON.stringify(cat.ai_prefill_overrides || {}, null, 2)}
                    onChange={(e) => setCatField(def.key, 'ai_prefill_overrides', e.target.value)}
                    placeholder="Optional notes or JSON"
                    data-testid={`category-${def.key}-ai-prefill`}
                    disabled={!canEdit}
                  />
                </div>
              </div>
              {def.key === 'digital_print' && (
                <div className="space-y-4 border rounded-lg p-3 bg-slate-50" data-testid="digital-print-category-defaults">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Print Media</Label>
                      <Select value={cat.default_print_media_key || ''} onValueChange={(v) => setCatField(def.key, 'default_print_media_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-media">
                          <SelectValue placeholder="Select media" />
                        </SelectTrigger>
                        <SelectContent>
                          {dpMediaOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Laminate Type</Label>
                      <Select value={cat.default_laminate_key || ''} onValueChange={(v) => setCatField(def.key, 'default_laminate_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-laminate">
                          <SelectValue placeholder="Select laminate" />
                        </SelectTrigger>
                        <SelectContent>
                          {dpLaminateOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Print Quality</Label>
                      <Select value={cat.default_print_quality_mode || 'standard'} onValueChange={(v) => setCatField(def.key, 'default_print_quality_mode', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-quality">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="draft">Draft</SelectItem>
                          <SelectItem value="standard">Standard</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="photo">Photo</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Use Type</Label>
                      <Select value={cat.default_use_type || 'indoor'} onValueChange={(v) => setCatField(def.key, 'default_use_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-use-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="indoor">Indoor</SelectItem>
                          <SelectItem value="outdoor">Outdoor</SelectItem>
                          <SelectItem value="display">Display</SelectItem>
                          <SelectItem value="floor">Floor</SelectItem>
                          <SelectItem value="window">Window</SelectItem>
                          <SelectItem value="wall">Wall</SelectItem>
                          <SelectItem value="backlit">Backlit</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Unit of Measure</Label>
                      <Select value={cat.default_unit_of_measure || 'inches'} onValueChange={(v) => setCatField(def.key, 'default_unit_of_measure', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-unit">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="inches">Inches</SelectItem>
                          <SelectItem value="feet">Feet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Contour Cut</Label>
                      <Select value={cat.default_contour_cut_type || 'none'} onValueChange={(v) => setCatField(def.key, 'default_contour_cut_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-contour">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          <SelectItem value="simple">Simple Contour</SelectItem>
                          <SelectItem value="complex">Complex Contour</SelectItem>
                          <SelectItem value="kiss">Kiss Cut / Sheet Cut</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Trim Finish</Label>
                      <Select value={cat.default_trim_finish_type || 'standard'} onValueChange={(v) => setCatField(def.key, 'default_trim_finish_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-trim">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="standard">Standard Trim</SelectItem>
                          <SelectItem value="premium">Premium Trim</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Design Complexity</Label>
                      <Select value={cat.default_design_complexity || 'simple'} onValueChange={(v) => setCatField(def.key, 'default_design_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-design-complexity">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="simple">Simple</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="complex">Complex</SelectItem>
                          <SelectItem value="extreme">Extreme</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Install Complexity</Label>
                      <Select value={cat.default_install_complexity || 'easy'} onValueChange={(v) => setCatField(def.key, 'default_install_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="digital-print-default-install-complexity">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="easy">Easy</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="difficult">Difficult</SelectItem>
                          <SelectItem value="extreme">Extreme</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Min Billable Area" value={cat.default_minimum_billable_area} onChg={(v) => setCatField(def.key, 'default_minimum_billable_area', v)} prefix="" suffix="sqft" testId="digital-print-min-billable" />
                    <F label="Min Sell Price" value={cat.default_minimum_sell_price} onChg={(v) => setCatField(def.key, 'default_minimum_sell_price', v)} testId="digital-print-min-sell" />
                    <F label="File Prep Fee" value={cat.default_file_prep_fee} onChg={(v) => setCatField(def.key, 'default_file_prep_fee', v)} testId="digital-print-file-prep" />
                    <F label="Design Time (hrs)" value={cat.default_design_time_hours} onChg={(v) => setCatField(def.key, 'default_design_time_hours', v)} prefix="" suffix="hrs" testId="digital-print-design-time" />
                    <F label="Ink Coverage %" value={cat.default_ink_coverage_percent} onChg={(v) => setCatField(def.key, 'default_ink_coverage_percent', v)} prefix="" suffix="%" testId="digital-print-ink-coverage" />
                    <F label="Ink Cost / Sq Ft" value={cat.base_ink_cost_per_sqft} onChg={(v) => setCatField(def.key, 'base_ink_cost_per_sqft', v)} testId="digital-print-ink-cost" />
                    <F label="Prod Labor / Sq Ft" value={cat.production_labor_hours_per_sqft} onChg={(v) => setCatField(def.key, 'production_labor_hours_per_sqft', v)} prefix="" suffix="hrs" testId="digital-print-prod-labor" />
                    <F label="Min Prod Labor / Item" value={cat.min_production_labor_hours_per_item} onChg={(v) => setCatField(def.key, 'min_production_labor_hours_per_item', v)} prefix="" suffix="hrs" testId="digital-print-min-prod-labor" />
                    <F label="Mounting Labor / Sq Ft" value={cat.mounting_labor_hours_per_sqft} onChg={(v) => setCatField(def.key, 'mounting_labor_hours_per_sqft', v)} prefix="" suffix="hrs" testId="digital-print-mounting-labor" />
                    <F label="Separation Labor / Piece" value={cat.piece_separation_hours_per_piece} onChg={(v) => setCatField(def.key, 'piece_separation_hours_per_piece', v)} prefix="" suffix="hrs" testId="digital-print-separation-labor" />
                    <F label="Install Hours / Sq Ft" value={cat.install_hours_per_sqft} onChg={(v) => setCatField(def.key, 'install_hours_per_sqft', v)} prefix="" suffix="hrs" testId="digital-print-install-hours" />
                    <F label="Trim Premium Add-on" value={cat.trim_premium_addon} onChg={(v) => setCatField(def.key, 'trim_premium_addon', v)} testId="digital-print-trim-addon" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_laminate_required ?? false} onCheckedChange={(v) => setCatField(def.key, 'default_laminate_required', v)} disabled={!canEdit} data-testid="digital-print-default-laminate-required" />
                      <Label className="text-xs">Default Laminate Required</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_install_included ?? false} onCheckedChange={(v) => setCatField(def.key, 'default_install_included', v)} disabled={!canEdit} data-testid="digital-print-default-install-included" />
                      <Label className="text-xs">Default Install Included</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.sell_method === 'max_of_rate_or_minimum'} onCheckedChange={(v) => setCatField(def.key, 'sell_method', v ? 'max_of_rate_or_minimum' : 'rate_only')} disabled={!canEdit} data-testid="digital-print-sell-method" />
                      <Label className="text-xs">Use max of rate/min</Label>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Quality Mult: Draft" value={cat.quality_multipliers?.draft} onChg={(v) => setCatField(def.key, 'quality_multipliers', { ...(cat.quality_multipliers || {}), draft: v })} prefix="" suffix="x" testId="digital-print-quality-draft" />
                    <F label="Quality Mult: Standard" value={cat.quality_multipliers?.standard} onChg={(v) => setCatField(def.key, 'quality_multipliers', { ...(cat.quality_multipliers || {}), standard: v })} prefix="" suffix="x" testId="digital-print-quality-standard" />
                    <F label="Quality Mult: High" value={cat.quality_multipliers?.high} onChg={(v) => setCatField(def.key, 'quality_multipliers', { ...(cat.quality_multipliers || {}), high: v })} prefix="" suffix="x" testId="digital-print-quality-high" />
                    <F label="Quality Mult: Photo" value={cat.quality_multipliers?.photo} onChg={(v) => setCatField(def.key, 'quality_multipliers', { ...(cat.quality_multipliers || {}), photo: v })} prefix="" suffix="x" testId="digital-print-quality-photo" />
                    <F label="Contour Mult: None" value={cat.contour_cut_multipliers?.none} onChg={(v) => setCatField(def.key, 'contour_cut_multipliers', { ...(cat.contour_cut_multipliers || {}), none: v })} prefix="" suffix="x" testId="digital-print-contour-none" />
                    <F label="Contour Mult: Simple" value={cat.contour_cut_multipliers?.simple} onChg={(v) => setCatField(def.key, 'contour_cut_multipliers', { ...(cat.contour_cut_multipliers || {}), simple: v })} prefix="" suffix="x" testId="digital-print-contour-simple" />
                    <F label="Contour Mult: Complex" value={cat.contour_cut_multipliers?.complex} onChg={(v) => setCatField(def.key, 'contour_cut_multipliers', { ...(cat.contour_cut_multipliers || {}), complex: v })} prefix="" suffix="x" testId="digital-print-contour-complex" />
                    <F label="Contour Mult: Kiss" value={cat.contour_cut_multipliers?.kiss} onChg={(v) => setCatField(def.key, 'contour_cut_multipliers', { ...(cat.contour_cut_multipliers || {}), kiss: v })} prefix="" suffix="x" testId="digital-print-contour-kiss" />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs text-gray-500">Quantity Discount Tiers</Label>
                    <div className="grid grid-cols-4 gap-2 text-[11px] text-gray-500">
                      <span>Min Qty</span>
                      <span>Max Qty</span>
                      <span>Discount %</span>
                      <span></span>
                    </div>
                    {dpTiers.map((tier, idx) => (
                      <div key={`dp-tier-${idx}`} className="grid grid-cols-4 gap-2">
                        <Input type="number" className="h-7 text-xs" value={tier.min_qty ?? ''} onChange={(e) => updateDpTier(idx, 'min_qty', n(e.target.value))} data-testid={`digital-print-tier-${idx}-min`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.max_qty ?? ''} onChange={(e) => updateDpTier(idx, 'max_qty', e.target.value === '' ? null : n(e.target.value))} data-testid={`digital-print-tier-${idx}-max`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.discount_percent ?? ''} onChange={(e) => updateDpTier(idx, 'discount_percent', n(e.target.value))} data-testid={`digital-print-tier-${idx}-discount`} disabled={!canEdit} />
                        <div className="text-xs text-gray-400 flex items-center">%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {def.key === 'cut_vinyl' && (
                <div className="space-y-4 border rounded-lg p-3 bg-slate-50" data-testid="cut-vinyl-category-defaults">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Vinyl Type</Label>
                      <Select value={cat.default_vinyl_type_key || ''} onValueChange={(v) => setCatField(def.key, 'default_vinyl_type_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-vinyl">
                          <SelectValue placeholder="Select vinyl" />
                        </SelectTrigger>
                        <SelectContent>
                          {cvVinylOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Use Type</Label>
                      <Select value={cat.default_use_type || 'indoor'} onValueChange={(v) => setCatField(def.key, 'default_use_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-use-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_USE_TYPES.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Unit of Measure</Label>
                      <Select value={cat.default_unit_of_measure || 'inches'} onValueChange={(v) => setCatField(def.key, 'default_unit_of_measure', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-unit">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_UNIT_OPTIONS.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Weeding</Label>
                      <Select value={cat.default_weeding_complexity || 'simple'} onValueChange={(v) => setCatField(def.key, 'default_weeding_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-weeding">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_WEEDING_LEVELS.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Design Complexity</Label>
                      <Select value={cat.default_design_complexity || 'simple'} onValueChange={(v) => setCatField(def.key, 'default_design_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-design">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_DESIGN_LEVELS.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Install Complexity</Label>
                      <Select value={cat.default_install_complexity || 'easy'} onValueChange={(v) => setCatField(def.key, 'default_install_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-install">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_INSTALL_LEVELS.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Surface Type</Label>
                      <Select value={cat.default_surface_type || 'flat_smooth'} onValueChange={(v) => setCatField(def.key, 'default_surface_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="cut-vinyl-default-surface">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_SURFACE_TYPES.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default # Colors</Label>
                      <Input type="number" className="h-8 text-xs" value={cat.default_number_of_colors ?? ''} onChange={(e) => setCatField(def.key, 'default_number_of_colors', n(e.target.value))} data-testid="cut-vinyl-default-colors" disabled={!canEdit} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Min Billable Area" value={cat.default_minimum_billable_area} onChg={(v) => setCatField(def.key, 'default_minimum_billable_area', v)} prefix="" suffix="sqft" testId="cut-vinyl-min-billable" />
                    <F label="Min Sell Price" value={cat.default_minimum_sell_price} onChg={(v) => setCatField(def.key, 'default_minimum_sell_price', v)} testId="cut-vinyl-min-sell" />
                    <F label="Cleanup Fee" value={cat.default_cleanup_fee} onChg={(v) => setCatField(def.key, 'default_cleanup_fee', v)} testId="cut-vinyl-cleanup-fee" />
                    <F label="Design Time (hrs)" value={cat.default_design_time_hours} onChg={(v) => setCatField(def.key, 'default_design_time_hours', v)} prefix="" suffix="hrs" testId="cut-vinyl-design-time" />
                    <F label="Waste %" value={cat.waste_percentage} onChg={(v) => setCatField(def.key, 'waste_percentage', v)} prefix="" suffix="%" testId="cut-vinyl-waste" />
                    <F label="Prod Labor / Sq Ft" value={cat.production_labor_hours_per_sqft} onChg={(v) => setCatField(def.key, 'production_labor_hours_per_sqft', v)} prefix="" suffix="hrs" testId="cut-vinyl-prod-labor" />
                    <F label="Min Prod Labor / Item" value={cat.min_production_labor_hours_per_item} onChg={(v) => setCatField(def.key, 'min_production_labor_hours_per_item', v)} prefix="" suffix="hrs" testId="cut-vinyl-min-prod-labor" />
                    <F label="Install Hours / Sq Ft" value={cat.install_hours_per_sqft} onChg={(v) => setCatField(def.key, 'install_hours_per_sqft', v)} prefix="" suffix="hrs" testId="cut-vinyl-install-hours" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_masking_required ?? true} onCheckedChange={(v) => setCatField(def.key, 'default_masking_required', v)} disabled={!canEdit} data-testid="cut-vinyl-default-masking" />
                      <Label className="text-xs">Masking Required</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_install_included ?? false} onCheckedChange={(v) => setCatField(def.key, 'default_install_included', v)} disabled={!canEdit} data-testid="cut-vinyl-default-install-included" />
                      <Label className="text-xs">Default Install Included</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.sell_method === 'max_of_rate_or_minimum'} onCheckedChange={(v) => setCatField(def.key, 'sell_method', v ? 'max_of_rate_or_minimum' : 'rate_only')} disabled={!canEdit} data-testid="cut-vinyl-sell-method" />
                      <Label className="text-xs">Use max of rate/min</Label>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Color Mult: 1" value={cat.color_multipliers?.["1"]} onChg={(v) => setCatField(def.key, 'color_multipliers', { ...(cat.color_multipliers || {}), "1": v })} prefix="" suffix="x" testId="cut-vinyl-color-1" />
                    <F label="Color Mult: 2" value={cat.color_multipliers?.["2"]} onChg={(v) => setCatField(def.key, 'color_multipliers', { ...(cat.color_multipliers || {}), "2": v })} prefix="" suffix="x" testId="cut-vinyl-color-2" />
                    <F label="Color Mult: 3" value={cat.color_multipliers?.["3"]} onChg={(v) => setCatField(def.key, 'color_multipliers', { ...(cat.color_multipliers || {}), "3": v })} prefix="" suffix="x" testId="cut-vinyl-color-3" />
                    <F label="Color Mult: 4+" value={cat.color_multipliers?.["4_plus"]} onChg={(v) => setCatField(def.key, 'color_multipliers', { ...(cat.color_multipliers || {}), "4_plus": v })} prefix="" suffix="x" testId="cut-vinyl-color-4" />
                    <F label="Weeding: Simple" value={cat.weeding_multipliers?.simple} onChg={(v) => setCatField(def.key, 'weeding_multipliers', { ...(cat.weeding_multipliers || {}), simple: v })} prefix="" suffix="x" testId="cut-vinyl-weeding-simple" />
                    <F label="Weeding: Medium" value={cat.weeding_multipliers?.medium} onChg={(v) => setCatField(def.key, 'weeding_multipliers', { ...(cat.weeding_multipliers || {}), medium: v })} prefix="" suffix="x" testId="cut-vinyl-weeding-medium" />
                    <F label="Weeding: Complex" value={cat.weeding_multipliers?.complex} onChg={(v) => setCatField(def.key, 'weeding_multipliers', { ...(cat.weeding_multipliers || {}), complex: v })} prefix="" suffix="x" testId="cut-vinyl-weeding-complex" />
                    <F label="Weeding: Extreme" value={cat.weeding_multipliers?.extreme} onChg={(v) => setCatField(def.key, 'weeding_multipliers', { ...(cat.weeding_multipliers || {}), extreme: v })} prefix="" suffix="x" testId="cut-vinyl-weeding-extreme" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Install: Easy" value={cat.install_complexity_multipliers?.easy} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), easy: v })} prefix="" suffix="x" testId="cut-vinyl-install-easy" />
                    <F label="Install: Medium" value={cat.install_complexity_multipliers?.medium} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), medium: v })} prefix="" suffix="x" testId="cut-vinyl-install-medium" />
                    <F label="Install: Difficult" value={cat.install_complexity_multipliers?.difficult} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), difficult: v })} prefix="" suffix="x" testId="cut-vinyl-install-difficult" />
                    <F label="Install: Extreme" value={cat.install_complexity_multipliers?.extreme} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), extreme: v })} prefix="" suffix="x" testId="cut-vinyl-install-extreme" />
                    <F label="Surface: Flat" value={cat.surface_multipliers?.flat_smooth} onChg={(v) => setCatField(def.key, 'surface_multipliers', { ...(cat.surface_multipliers || {}), flat_smooth: v })} prefix="" suffix="x" testId="cut-vinyl-surface-flat" />
                    <F label="Surface: Glass" value={cat.surface_multipliers?.glass_window} onChg={(v) => setCatField(def.key, 'surface_multipliers', { ...(cat.surface_multipliers || {}), glass_window: v })} prefix="" suffix="x" testId="cut-vinyl-surface-glass" />
                    <F label="Surface: Vehicle" value={cat.surface_multipliers?.vehicle} onChg={(v) => setCatField(def.key, 'surface_multipliers', { ...(cat.surface_multipliers || {}), vehicle: v })} prefix="" suffix="x" testId="cut-vinyl-surface-vehicle" />
                    <F label="Surface: Textured" value={cat.surface_multipliers?.textured_rough} onChg={(v) => setCatField(def.key, 'surface_multipliers', { ...(cat.surface_multipliers || {}), textured_rough: v })} prefix="" suffix="x" testId="cut-vinyl-surface-textured" />
                    <F label="Surface: Curved" value={cat.surface_multipliers?.curved_awkward} onChg={(v) => setCatField(def.key, 'surface_multipliers', { ...(cat.surface_multipliers || {}), curved_awkward: v })} prefix="" suffix="x" testId="cut-vinyl-surface-curved" />
                    <F label="Use Type: Indoor" value={cat.use_type_multipliers?.indoor} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), indoor: v })} prefix="" suffix="x" testId="cut-vinyl-use-indoor" />
                    <F label="Use Type: Outdoor" value={cat.use_type_multipliers?.outdoor} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), outdoor: v })} prefix="" suffix="x" testId="cut-vinyl-use-outdoor" />
                    <F label="Use Type: Wall" value={cat.use_type_multipliers?.wall} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), wall: v })} prefix="" suffix="x" testId="cut-vinyl-use-wall" />
                    <F label="Use Type: Glass" value={cat.use_type_multipliers?.glass_window} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), glass_window: v })} prefix="" suffix="x" testId="cut-vinyl-use-glass" />
                    <F label="Use Type: Vehicle" value={cat.use_type_multipliers?.vehicle} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), vehicle: v })} prefix="" suffix="x" testId="cut-vinyl-use-vehicle" />
                    <F label="Use Type: Specialty" value={cat.use_type_multipliers?.specialty} onChg={(v) => setCatField(def.key, 'use_type_multipliers', { ...(cat.use_type_multipliers || {}), specialty: v })} prefix="" suffix="x" testId="cut-vinyl-use-specialty" />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs text-gray-500">Quantity Discount Tiers</Label>
                    <div className="grid grid-cols-4 gap-2 text-[11px] text-gray-500">
                      <span>Min Qty</span>
                      <span>Max Qty</span>
                      <span>Discount %</span>
                      <span></span>
                    </div>
                    {cvTiers.map((tier, idx) => (
                      <div key={`cv-tier-${idx}`} className="grid grid-cols-4 gap-2">
                        <Input type="number" className="h-7 text-xs" value={tier.min_qty ?? ''} onChange={(e) => updateCvTier(idx, 'min_qty', n(e.target.value))} data-testid={`cut-vinyl-tier-${idx}-min`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.max_qty ?? ''} onChange={(e) => updateCvTier(idx, 'max_qty', e.target.value === '' ? null : n(e.target.value))} data-testid={`cut-vinyl-tier-${idx}-max`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.discount_percent ?? ''} onChange={(e) => updateCvTier(idx, 'discount_percent', n(e.target.value))} data-testid={`cut-vinyl-tier-${idx}-discount`} disabled={!canEdit} />
                        <div className="text-xs text-gray-400 flex items-center">%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {def.key === 'rigid_signs' && (
                <div className="space-y-4 border rounded-lg p-3 bg-slate-50" data-testid="rigid-signs-category-defaults">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Substrate</Label>
                      <Select value={cat.default_substrate_key || ''} onValueChange={(v) => setCatField(def.key, 'default_substrate_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-substrate">
                          <SelectValue placeholder="Select substrate" />
                        </SelectTrigger>
                        <SelectContent>
                          {rigidSubstrateOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Graphic Method</Label>
                      <Select value={cat.default_graphic_method || 'direct_print'} onValueChange={(v) => setCatField(def.key, 'default_graphic_method', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-graphic-method">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="direct_print">Direct Print</SelectItem>
                          <SelectItem value="mounted_print">Mounted Print</SelectItem>
                          <SelectItem value="cut_vinyl_applied">Cut Vinyl Applied</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Finish Type</Label>
                      <Select value={cat.default_finish_key || ''} onValueChange={(v) => setCatField(def.key, 'default_finish_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-finish">
                          <SelectValue placeholder="Select finish" />
                        </SelectTrigger>
                        <SelectContent>
                          {rigidFinishOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Unit of Measure</Label>
                      <Select value={cat.default_unit_of_measure || 'inches'} onValueChange={(v) => setCatField(def.key, 'default_unit_of_measure', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-unit">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CUT_VINYL_UNIT_OPTIONS.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Sidedness</Label>
                      <Select value={cat.default_sidedness || 'single'} onValueChange={(v) => setCatField(def.key, 'default_sidedness', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-sidedness">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="single">Single</SelectItem>
                          <SelectItem value="double">Double</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Double-Sided Art</Label>
                      <Select value={cat.default_double_sided_art || 'same'} onValueChange={(v) => setCatField(def.key, 'default_double_sided_art', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-double-art">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="same">Same Art</SelectItem>
                          <SelectItem value="different">Different Art</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Shape Type</Label>
                      <Select value={cat.default_shape_type || 'rectangle'} onValueChange={(v) => setCatField(def.key, 'default_shape_type', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-shape">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="rectangle">Rectangle</SelectItem>
                          <SelectItem value="rounded_corners">Rounded Corners</SelectItem>
                          <SelectItem value="simple_contour">Simple Contour</SelectItem>
                          <SelectItem value="complex_contour">Complex Contour</SelectItem>
                          <SelectItem value="specialty_routed">Specialty Routed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Finish Quality</Label>
                      <Select value={cat.default_finish_quality || 'standard'} onValueChange={(v) => setCatField(def.key, 'default_finish_quality', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-finish-quality">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="standard">Standard</SelectItem>
                          <SelectItem value="premium">Premium</SelectItem>
                          <SelectItem value="presentation">Presentation</SelectItem>
                          <SelectItem value="architectural">Architectural</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Default Install Complexity</Label>
                      <Select value={cat.default_install_complexity || 'easy'} onValueChange={(v) => setCatField(def.key, 'default_install_complexity', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-default-install-complexity">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="easy">Easy</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="difficult">Difficult</SelectItem>
                          <SelectItem value="high_risk">High-Risk</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Min Billable Area" value={cat.default_minimum_billable_area} onChg={(v) => setCatField(def.key, 'default_minimum_billable_area', v)} prefix="" suffix="sqft" testId="rigid-signs-min-billable" />
                    <F label="Min Sell Price" value={cat.default_minimum_sell_price} onChg={(v) => setCatField(def.key, 'default_minimum_sell_price', v)} testId="rigid-signs-min-sell" />
                    <F label="Design Time (hrs)" value={cat.default_design_time_hours} onChg={(v) => setCatField(def.key, 'default_design_time_hours', v)} prefix="" suffix="hrs" testId="rigid-signs-design-time" />
                    <F label="Waste %" value={cat.waste_percentage} onChg={(v) => setCatField(def.key, 'waste_percentage', v)} prefix="" suffix="%" testId="rigid-signs-waste" />
                    <F label="Prod Labor / Sq Ft" value={cat.production_labor_hours_per_sqft} onChg={(v) => setCatField(def.key, 'production_labor_hours_per_sqft', v)} prefix="" suffix="hrs" testId="rigid-signs-prod-labor" />
                    <F label="Min Prod Labor / Item" value={cat.min_production_labor_hours_per_item} onChg={(v) => setCatField(def.key, 'min_production_labor_hours_per_item', v)} prefix="" suffix="hrs" testId="rigid-signs-min-prod-labor" />
                    <F label="Mounting Labor / Sq Ft" value={cat.default_mounting_labor_hours_per_sqft} onChg={(v) => setCatField(def.key, 'default_mounting_labor_hours_per_sqft', v)} prefix="" suffix="hrs" testId="rigid-signs-mounting-labor" />
                    <F label="Install Hours / Sq Ft" value={cat.install_hours_per_sqft} onChg={(v) => setCatField(def.key, 'install_hours_per_sqft', v)} prefix="" suffix="hrs" testId="rigid-signs-install-hours" />
                    <F label="Hardware Handling Labor" value={cat.hardware_handling_labor_cost} onChg={(v) => setCatField(def.key, 'hardware_handling_labor_cost', v)} testId="rigid-signs-hardware-labor" />
                    <F label="Drill / Prep Fee" value={cat.drill_prep_fee} onChg={(v) => setCatField(def.key, 'drill_prep_fee', v)} testId="rigid-signs-drill-fee" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_finish_required ?? false} onCheckedChange={(v) => setCatField(def.key, 'default_finish_required', v)} disabled={!canEdit} data-testid="rigid-signs-default-finish-required" />
                      <Label className="text-xs">Default Finish Required</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.default_install_included ?? false} onCheckedChange={(v) => setCatField(def.key, 'default_install_included', v)} disabled={!canEdit} data-testid="rigid-signs-default-install-included" />
                      <Label className="text-xs">Default Install Included</Label>
                    </div>
                    <div className="flex items-center gap-2 pt-4">
                      <Switch checked={cat.sell_method === 'max_of_rate_or_minimum'} onCheckedChange={(v) => setCatField(def.key, 'sell_method', v ? 'max_of_rate_or_minimum' : 'rate_only')} disabled={!canEdit} data-testid="rigid-signs-sell-method" />
                      <Label className="text-xs">Use max of rate/min</Label>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <F label="Thickness: Thin" value={cat.thickness_multipliers?.thin_basic} onChg={(v) => setCatField(def.key, 'thickness_multipliers', { ...(cat.thickness_multipliers || {}), thin_basic: v })} prefix="" suffix="x" testId="rigid-signs-thickness-thin" />
                    <F label="Thickness: Medium" value={cat.thickness_multipliers?.medium} onChg={(v) => setCatField(def.key, 'thickness_multipliers', { ...(cat.thickness_multipliers || {}), medium: v })} prefix="" suffix="x" testId="rigid-signs-thickness-medium" />
                    <F label="Thickness: Heavy" value={cat.thickness_multipliers?.thick_heavy} onChg={(v) => setCatField(def.key, 'thickness_multipliers', { ...(cat.thickness_multipliers || {}), thick_heavy: v })} prefix="" suffix="x" testId="rigid-signs-thickness-heavy" />
                    <F label="Sidedness: Single" value={cat.sidedness_multipliers?.single} onChg={(v) => setCatField(def.key, 'sidedness_multipliers', { ...(cat.sidedness_multipliers || {}), single: v })} prefix="" suffix="x" testId="rigid-signs-sided-single" />
                    <F label="Sidedness: Double Same" value={cat.sidedness_multipliers?.double_same} onChg={(v) => setCatField(def.key, 'sidedness_multipliers', { ...(cat.sidedness_multipliers || {}), double_same: v })} prefix="" suffix="x" testId="rigid-signs-sided-same" />
                    <F label="Sidedness: Double Diff" value={cat.sidedness_multipliers?.double_diff} onChg={(v) => setCatField(def.key, 'sidedness_multipliers', { ...(cat.sidedness_multipliers || {}), double_diff: v })} prefix="" suffix="x" testId="rigid-signs-sided-diff" />
                    <F label="Shape: Rectangle" value={cat.shape_multipliers?.rectangle} onChg={(v) => setCatField(def.key, 'shape_multipliers', { ...(cat.shape_multipliers || {}), rectangle: v })} prefix="" suffix="x" testId="rigid-signs-shape-rectangle" />
                    <F label="Shape: Rounded" value={cat.shape_multipliers?.rounded_corners} onChg={(v) => setCatField(def.key, 'shape_multipliers', { ...(cat.shape_multipliers || {}), rounded_corners: v })} prefix="" suffix="x" testId="rigid-signs-shape-rounded" />
                    <F label="Shape: Simple Contour" value={cat.shape_multipliers?.simple_contour} onChg={(v) => setCatField(def.key, 'shape_multipliers', { ...(cat.shape_multipliers || {}), simple_contour: v })} prefix="" suffix="x" testId="rigid-signs-shape-simple" />
                    <F label="Shape: Complex Contour" value={cat.shape_multipliers?.complex_contour} onChg={(v) => setCatField(def.key, 'shape_multipliers', { ...(cat.shape_multipliers || {}), complex_contour: v })} prefix="" suffix="x" testId="rigid-signs-shape-complex" />
                    <F label="Shape: Specialty" value={cat.shape_multipliers?.specialty_routed} onChg={(v) => setCatField(def.key, 'shape_multipliers', { ...(cat.shape_multipliers || {}), specialty_routed: v })} prefix="" suffix="x" testId="rigid-signs-shape-specialty" />
                    <F label="Finish: Standard" value={cat.finish_quality_multipliers?.standard} onChg={(v) => setCatField(def.key, 'finish_quality_multipliers', { ...(cat.finish_quality_multipliers || {}), standard: v })} prefix="" suffix="x" testId="rigid-signs-finish-standard" />
                    <F label="Finish: Premium" value={cat.finish_quality_multipliers?.premium} onChg={(v) => setCatField(def.key, 'finish_quality_multipliers', { ...(cat.finish_quality_multipliers || {}), premium: v })} prefix="" suffix="x" testId="rigid-signs-finish-premium" />
                    <F label="Finish: Presentation" value={cat.finish_quality_multipliers?.presentation} onChg={(v) => setCatField(def.key, 'finish_quality_multipliers', { ...(cat.finish_quality_multipliers || {}), presentation: v })} prefix="" suffix="x" testId="rigid-signs-finish-presentation" />
                    <F label="Finish: Architectural" value={cat.finish_quality_multipliers?.architectural} onChg={(v) => setCatField(def.key, 'finish_quality_multipliers', { ...(cat.finish_quality_multipliers || {}), architectural: v })} prefix="" suffix="x" testId="rigid-signs-finish-architectural" />
                    <F label="Install: Easy" value={cat.install_complexity_multipliers?.easy} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), easy: v })} prefix="" suffix="x" testId="rigid-signs-install-easy" />
                    <F label="Install: Medium" value={cat.install_complexity_multipliers?.medium} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), medium: v })} prefix="" suffix="x" testId="rigid-signs-install-medium" />
                    <F label="Install: Difficult" value={cat.install_complexity_multipliers?.difficult} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), difficult: v })} prefix="" suffix="x" testId="rigid-signs-install-difficult" />
                    <F label="Install: High-Risk" value={cat.install_complexity_multipliers?.high_risk} onChg={(v) => setCatField(def.key, 'install_complexity_multipliers', { ...(cat.install_complexity_multipliers || {}), high_risk: v })} prefix="" suffix="x" testId="rigid-signs-install-high-risk" />
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <Label className="text-[10px] text-gray-500">Direct Print Consumable</Label>
                      <Select value={cat.direct_print_consumable_key || ''} onValueChange={(v) => setCatField(def.key, 'direct_print_consumable_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-direct-print-key">
                          <SelectValue placeholder="Select material" />
                        </SelectTrigger>
                        <SelectContent>
                          {rigidGraphicOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Mounted Print Graphic</Label>
                      <Select value={cat.mounted_print_graphic_key || ''} onValueChange={(v) => setCatField(def.key, 'mounted_print_graphic_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-mounted-print-key">
                          <SelectValue placeholder="Select material" />
                        </SelectTrigger>
                        <SelectContent>
                          {rigidGraphicOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-[10px] text-gray-500">Cut Vinyl Material</Label>
                      <Select value={cat.cut_vinyl_material_key || ''} onValueChange={(v) => setCatField(def.key, 'cut_vinyl_material_key', v)} disabled={!canEdit}>
                        <SelectTrigger className="h-8 text-xs" data-testid="rigid-signs-cut-vinyl-key">
                          <SelectValue placeholder="Select vinyl" />
                        </SelectTrigger>
                        <SelectContent>
                          {rigidVinylOptions.map((m) => (
                            <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs text-gray-500">Quantity Discount Tiers</Label>
                    <div className="grid grid-cols-4 gap-2 text-[11px] text-gray-500">
                      <span>Min Qty</span>
                      <span>Max Qty</span>
                      <span>Discount %</span>
                      <span></span>
                    </div>
                    {rsTiers.map((tier, idx) => (
                      <div key={`rs-tier-${idx}`} className="grid grid-cols-4 gap-2">
                        <Input type="number" className="h-7 text-xs" value={tier.min_qty ?? ''} onChange={(e) => updateRsTier(idx, 'min_qty', n(e.target.value))} data-testid={`rigid-signs-tier-${idx}-min`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.max_qty ?? ''} onChange={(e) => updateRsTier(idx, 'max_qty', e.target.value === '' ? null : n(e.target.value))} data-testid={`rigid-signs-tier-${idx}-max`} disabled={!canEdit} />
                        <Input type="number" className="h-7 text-xs" value={tier.discount_percent ?? ''} onChange={(e) => updateRsTier(idx, 'discount_percent', n(e.target.value))} data-testid={`rigid-signs-tier-${idx}-discount`} disabled={!canEdit} />
                        <div className="text-xs text-gray-400 flex items-center">%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="border-t pt-3">
                <p className="text-xs font-medium text-gray-700 mb-2">Selling Benchmarks</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {bench.average_sell_price_per_sqft !== undefined && (
                    <F label="Avg Sell / Sq Ft" value={bench.average_sell_price_per_sqft} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_sqft', v)} testId={`category-${def.key}-avg-sqft`} />
                  )}
                  {bench.average_sell_price_per_unit !== undefined && (
                    <F label="Avg Sell / Unit" value={bench.average_sell_price_per_unit} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_unit', v)} testId={`category-${def.key}-avg-unit`} />
                  )}
                  {bench.average_sell_price_per_hour !== undefined && (
                    <F label="Avg Sell / Hour" value={bench.average_sell_price_per_hour} onChg={(v) => setBenchField(def.key, 'average_sell_price_per_hour', v)} testId={`category-${def.key}-avg-hour`} />
                  )}
                  <F label="Avg Order Total" value={bench.average_order_total} onChg={(v) => setBenchField(def.key, 'average_order_total', v)} testId={`category-${def.key}-avg-order`} />
                  <F label="Min Charge" value={bench.minimum_charge} onChg={(v) => setBenchField(def.key, 'minimum_charge', v)} testId={`category-${def.key}-avg-min`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/* ────────── LABOR  SERVICE RATES TAB ────────── */
function LaborRatesTab({ settings, onChange, canEdit }) {
  const rates = settings.labor_rates || {};
  const updateRate = (rateKey, field, value) => {
    const nextRates = {
      ...rates,
      [rateKey]: { ...(rates[rateKey] || {}), [field]: value },
    };
    onChange({ ...settings, labor_rates: nextRates });
  };

  return (
    <div className="space-y-4" data-testid="labor-rates-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-gray-900">Labor & Service Rates</CardTitle>
          <CardDescription>Hourly rates, minimums, and default time assumptions for billing</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {LABOR_RATE_TYPES.map((rate) => {
            const rule = rates[rate.key] || {};
            return (
              <div key={rate.key} className="border rounded-lg p-3 bg-gray-50" data-testid={`labor-rate-${rate.key}`}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-900">{rate.label}</p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                  <div>
                    <Label className="text-[10px] text-gray-500">Hourly Rate</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.hourly_rate ?? ''}
                      onChange={(e) => updateRate(rate.key, 'hourly_rate', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-hourly-rate`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Minimum Charge</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.minimum_charge ?? ''}
                      onChange={(e) => updateRate(rate.key, 'minimum_charge', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-minimum-charge`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Billing Increment (min)</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.billing_increment_minutes ?? ''}
                      onChange={(e) => updateRate(rate.key, 'billing_increment_minutes', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-increment`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Default Time (min)</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.default_time_minutes ?? ''}
                      onChange={(e) => updateRate(rate.key, 'default_time_minutes', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-default-time`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Helper Add-on</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.helper_addon_rate ?? ''}
                      onChange={(e) => updateRate(rate.key, 'helper_addon_rate', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-helper-addon`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">After Hours</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.after_hours_multiplier ?? ''}
                      onChange={(e) => updateRate(rate.key, 'after_hours_multiplier', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-after-hours`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Weekend</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.weekend_multiplier ?? ''}
                      onChange={(e) => updateRate(rate.key, 'weekend_multiplier', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-weekend`}
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-gray-500">Emergency</Label>
                    <Input
                      type="number"
                      className="h-7 text-xs"
                      value={rule.emergency_multiplier ?? ''}
                      onChange={(e) => updateRate(rate.key, 'emergency_multiplier', n(e.target.value))}
                      disabled={!canEdit}
                      data-testid={`labor-${rate.key}-emergency`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}

/* ────────── AI ESTIMATION RULES TAB ────────── */
function AiEstimationRulesTab({ settings, onChange, canEdit }) {
  const rules = settings.ai_estimation_rules || {};
  const updateRule = (field, value) => {
    onChange({ ...settings, ai_estimation_rules: { ...rules, [field]: value } });
  };

  return (
    <div className="space-y-4" data-testid="ai-estimation-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-gray-900">AI Estimation Rules</CardTitle>
          <CardDescription>Controls for AI-prefill behavior and source labeling</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { key: 'fill_missing_only', label: 'AI fills missing fields only' },
            { key: 'never_override_user_values', label: 'AI never overwrites user-entered values' },
            { key: 'allow_prefill_category_defaults', label: 'AI can prefill category defaults' },
            { key: 'suggest_material_type', label: 'AI can suggest material/type selections' },
            { key: 'suggest_complexity', label: 'AI can suggest complexity levels' },
            { key: 'suggest_install', label: 'AI can suggest install requirements' },
            { key: 'suggest_design', label: 'AI can suggest design work' },
            { key: 'value_source_labels_enabled', label: 'Label values as default / AI / user' },
          ].map((rule) => (
            <div key={rule.key} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
              <Label className="text-sm text-gray-700">{rule.label}</Label>
              <Switch
                checked={rules[rule.key] ?? true}
                onCheckedChange={(value) => updateRule(rule.key, value)}
                disabled={!canEdit}
                data-testid={`ai-rule-${rule.key}`}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

/* ────────── BENCHMARK RULES TAB ────────── */
function BenchmarkRulesTab({ settings, onChange, canEdit }) {
  const rules = settings.benchmark_rules || {};
  const benchmarks = settings.selling_price_benchmarks || {};

  const updateRule = (field, value) => {
    onChange({ ...settings, benchmark_rules: { ...rules, [field]: value } });
  };
  const updateBench = (catKey, field, value) => {
    onChange({
      ...settings,
      selling_price_benchmarks: {
        ...benchmarks,
        [catKey]: { ...(benchmarks[catKey] || {}), [field]: value },
      },
    });
  };

  return (
    <div className="space-y-4" data-testid="benchmark-rules-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-gray-900">Benchmark / Historical Pricing Rules</CardTitle>
          <CardDescription>Guidance ranges and historical influence settings</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="flex items-center gap-3 col-span-2">
            <Switch
              checked={rules.enabled ?? true}
              onCheckedChange={(value) => updateRule('enabled', value)}
              disabled={!canEdit}
              data-testid="benchmark-enabled"
            />
            <Label className="text-sm">Benchmark guidance enabled</Label>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Historical Influence (0-1)</Label>
            <Input
              type="number"
              step="0.05"
              className="h-8 text-sm"
              value={rules.historical_influence ?? ''}
              onChange={(e) => updateRule('historical_influence', n(e.target.value))}
              disabled={!canEdit}
              data-testid="benchmark-historical-influence"
            />
          </div>
          <div>
            <Label className="text-xs text-gray-500">Outlier Handling</Label>
            <Select value={rules.outlier_handling || 'exclude_high_low'} onValueChange={(v) => updateRule('outlier_handling', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="benchmark-outlier-handling"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="exclude_high_low">Exclude High/Low</SelectItem>
                <SelectItem value="cap_outliers">Cap to Bounds</SelectItem>
                <SelectItem value="include_all">Include All</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Confidence Handling</Label>
            <Select value={rules.confidence_handling || 'warn_low_confidence'} onValueChange={(v) => updateRule('confidence_handling', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="benchmark-confidence-handling"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="warn_low_confidence">Warn on Low Confidence</SelectItem>
                <SelectItem value="flag_for_review">Flag for Review</SelectItem>
                <SelectItem value="no_action">No Action</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {CATEGORY_DEFS.map((def) => {
          const bench = benchmarks[def.key] || {};
          return (
            <Card key={def.key}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-gray-900">{def.label}</CardTitle>
                <CardDescription>Low / Typical / Premium guidance</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div>
                  <Label className="text-[10px] text-gray-500">Low</Label>
                  <Input
                    type="number"
                    className="h-7 text-xs"
                    value={bench.low_price ?? ''}
                    onChange={(e) => updateBench(def.key, 'low_price', n(e.target.value))}
                    disabled={!canEdit}
                    data-testid={`benchmark-${def.key}-low`}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Typical</Label>
                  <Input
                    type="number"
                    className="h-7 text-xs"
                    value={bench.typical_price ?? ''}
                    onChange={(e) => updateBench(def.key, 'typical_price', n(e.target.value))}
                    disabled={!canEdit}
                    data-testid={`benchmark-${def.key}-typical`}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Premium</Label>
                  <Input
                    type="number"
                    className="h-7 text-xs"
                    value={bench.premium_price ?? ''}
                    onChange={(e) => updateBench(def.key, 'premium_price', n(e.target.value))}
                    disabled={!canEdit}
                    data-testid={`benchmark-${def.key}-premium`}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Avg Order Total</Label>
                  <Input
                    type="number"
                    className="h-7 text-xs"
                    value={bench.average_order_total ?? ''}
                    onChange={(e) => updateBench(def.key, 'average_order_total', n(e.target.value))}
                    disabled={!canEdit}
                    data-testid={`benchmark-${def.key}-avg-order`}
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500">Min Charge</Label>
                  <Input
                    type="number"
                    className="h-7 text-xs"
                    value={bench.minimum_charge ?? ''}
                    onChange={(e) => updateBench(def.key, 'minimum_charge', n(e.target.value))}
                    disabled={!canEdit}
                    data-testid={`benchmark-${def.key}-min-charge`}
                  />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

/* ────────── GLOBAL CALCULATION RULES TAB ────────── */
function GlobalCalculationRulesTab({ settings, onChange, canEdit }) {
  const rules = settings.global_calc_rules || {};
  const updateRule = (field, value) => {
    onChange({ ...settings, global_calc_rules: { ...rules, [field]: value } });
  };

  return (
    <div className="space-y-4" data-testid="global-calculation-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-gray-900">Global Calculation Rules</CardTitle>
          <CardDescription>Shared pricing logic rules and override behavior</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <Label className="text-xs text-gray-500">Pricing Method Hierarchy</Label>
            <Select value={rules.pricing_method_hierarchy || 'max_of_margin_or_markup'} onValueChange={(v) => updateRule('pricing_method_hierarchy', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="global-pricing-hierarchy"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="max_of_margin_or_markup" data-testid="global-pricing-hierarchy-max">Max of Margin or Markup</SelectItem>
                <SelectItem value="markup_first" data-testid="global-pricing-hierarchy-markup">Markup First</SelectItem>
                <SelectItem value="margin_first" data-testid="global-pricing-hierarchy-margin">Margin First</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Overhead Application</Label>
            <Select value={rules.overhead_application || 'material_and_labor'} onValueChange={(v) => updateRule('overhead_application', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="global-overhead-application"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="material_and_labor" data-testid="global-overhead-material-labor">Material + Labor</SelectItem>
                <SelectItem value="labor_only" data-testid="global-overhead-labor">Labor Only</SelectItem>
                <SelectItem value="material_only" data-testid="global-overhead-material">Material Only</SelectItem>
                <SelectItem value="none" data-testid="global-overhead-none">No Overhead</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Waste Application</Label>
            <Select value={rules.waste_application || 'material_only'} onValueChange={(v) => updateRule('waste_application', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="global-waste-application"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="material_only" data-testid="global-waste-material">Material Only</SelectItem>
                <SelectItem value="all_materials" data-testid="global-waste-all">All Material Components</SelectItem>
                <SelectItem value="none" data-testid="global-waste-none">No Waste</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Rush Application</Label>
            <Select value={rules.rush_application || 'multiply_total'} onValueChange={(v) => updateRule('rush_application', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="global-rush-application"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="multiply_total" data-testid="global-rush-multiply">Multiply Total</SelectItem>
                <SelectItem value="add_flat" data-testid="global-rush-flat">Add Flat Fee</SelectItem>
                <SelectItem value="none" data-testid="global-rush-none">No Rush Adjustment</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Minimum Billable Area (sq ft)</Label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={rules.minimum_billable_area ?? ''}
              onChange={(e) => updateRule('minimum_billable_area', n(e.target.value))}
              disabled={!canEdit}
              data-testid="global-min-billable-area"
            />
          </div>
          <div>
            <Label className="text-xs text-gray-500">Minimum Price Floor</Label>
            <Input
              type="number"
              className="h-8 text-sm"
              value={rules.minimum_price_floor ?? ''}
              onChange={(e) => updateRule('minimum_price_floor', n(e.target.value))}
              disabled={!canEdit}
              data-testid="global-min-price-floor"
            />
          </div>
          <div>
            <Label className="text-xs text-gray-500">Fallback Warning Behavior</Label>
            <Select value={rules.fallback_warning_behavior || 'warn'} onValueChange={(v) => updateRule('fallback_warning_behavior', v)} disabled={!canEdit}>
              <SelectTrigger className="h-8 text-sm" data-testid="global-fallback-warning"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="warn" data-testid="global-fallback-warn">Warn</SelectItem>
                <SelectItem value="block" data-testid="global-fallback-block">Block</SelectItem>
                <SelectItem value="silent" data-testid="global-fallback-silent">Silent</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-2">
            <Label className="text-xs text-gray-500">Category Override Rules</Label>
            <Textarea
              className="text-xs min-h-[60px]"
              value={rules.category_override_rules || ''}
              onChange={(e) => updateRule('category_override_rules', e.target.value)}
              disabled={!canEdit}
              placeholder="Optional notes or JSON override rules"
              data-testid="global-category-overrides"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* ────────── REVIEW / TESTING PANEL ────────── */
function ReviewTestingPanel({ materials, settings }) {
  const [testInputs, setTestInputs] = useState({
    category: 'digital_print',
    material_key: '',
    width_inches: 24,
    length_inches: 24,
    quantity: 1,
    labor_hours: '',
    rush_order: false,
    install_required: false,
    manual_price: '',
    complexity: 1,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const materialOptions = materials || [];
  const selectedMaterial = materialOptions.find((mat) => mat.key === testInputs.material_key);

  const buildPayload = () => {
    const base = {
      complexity: Number(testInputs.complexity || 1),
      rush_order: testInputs.rush_order,
      install_required: testInputs.install_required,
    };
    if (testInputs.width_inches || testInputs.length_inches) {
      base.width_inches = Number(testInputs.width_inches) || null;
      base.length_inches = Number(testInputs.length_inches) || null;
    }
    if (testInputs.category === 'services' && testInputs.labor_hours) {
      base.estimated_hours = Number(testInputs.labor_hours) || null;
    }
    if (testInputs.category === 'custom' && selectedMaterial?.cost_per_unit) {
      base.unit_cost = Number(selectedMaterial.cost_per_unit);
    }
    return base;
  };

  const runTest = async () => {
    setLoading(true);
    try {
      const apiCategoryMap = {
        digital_print: 'digital_print',
        banners: 'banners',
        cut_vinyl: 'cut_vinyl',
        rigid_signs: 'rigid_signs',
        vehicle_wraps: 'vehicle_wrap',
        apparel: 'apparel',
        services: 'services',
        custom: 'custom',
      };
      const payload = {
        category: apiCategoryMap[testInputs.category] || 'custom',
        pricing_data: buildPayload(),
        quantity: Number(testInputs.quantity || 1),
      };
      const res = await fetch(`${API}/api/pricing/calculate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Failed to run test');
      setResult(data);
      toast.success('Pricing test complete');
    } catch (error) {
      toast.error(error.message || 'Failed to run test');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const manualPrice = Number(testInputs.manual_price || 0) || 0;
  const totalCost = Number(result?.total_cost || 0);
  const profit = manualPrice ? manualPrice - totalCost : 0;
  const margin = manualPrice ? ((profit / manualPrice) * 100) : 0;

  return (
    <div className="space-y-4" data-testid="review-tab">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-gray-900">Review / Testing Panel</CardTitle>
          <CardDescription>Run quick pricing tests against current foundation settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <Label className="text-xs text-gray-500">Test Category</Label>
              <Select value={testInputs.category} onValueChange={(value) => setTestInputs({ ...testInputs, category: value })}>
                <SelectTrigger className="h-8 text-sm" data-testid="review-category"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CATEGORY_DEFS.map((def) => (
                    <SelectItem key={def.key} value={def.key}>{def.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs text-gray-500">Material (for custom tests)</Label>
              <Select value={testInputs.material_key} onValueChange={(value) => setTestInputs({ ...testInputs, material_key: value })}>
                <SelectTrigger className="h-8 text-sm" data-testid="review-material"><SelectValue placeholder="Select material" /></SelectTrigger>
                <SelectContent>
                  {materialOptions.map((mat) => (
                    <SelectItem key={mat.key || mat.id} value={mat.key}>{mat.name || mat.key}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs text-gray-500">Width (in)</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.width_inches} onChange={(e) => setTestInputs({ ...testInputs, width_inches: e.target.value })} data-testid="review-width" />
            </div>
            <div>
              <Label className="text-xs text-gray-500">Height (in)</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.length_inches} onChange={(e) => setTestInputs({ ...testInputs, length_inches: e.target.value })} data-testid="review-height" />
            </div>
            <div>
              <Label className="text-xs text-gray-500">Quantity</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.quantity} onChange={(e) => setTestInputs({ ...testInputs, quantity: e.target.value })} data-testid="review-quantity" />
            </div>
            <div>
              <Label className="text-xs text-gray-500">Labor Hours</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.labor_hours} onChange={(e) => setTestInputs({ ...testInputs, labor_hours: e.target.value })} data-testid="review-labor" />
            </div>
            <div>
              <Label className="text-xs text-gray-500">Complexity</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.complexity} onChange={(e) => setTestInputs({ ...testInputs, complexity: e.target.value })} data-testid="review-complexity" />
            </div>
            <div className="flex items-center gap-2 pt-5">
              <Switch checked={testInputs.rush_order} onCheckedChange={(value) => setTestInputs({ ...testInputs, rush_order: value })} data-testid="review-rush" />
              <Label className="text-xs text-gray-600">Rush</Label>
            </div>
            <div className="flex items-center gap-2 pt-5">
              <Switch checked={testInputs.install_required} onCheckedChange={(value) => setTestInputs({ ...testInputs, install_required: value })} data-testid="review-install" />
              <Label className="text-xs text-gray-600">Install</Label>
            </div>
            <div>
              <Label className="text-xs text-gray-500">Manual Quote Price</Label>
              <Input type="number" className="h-8 text-sm" value={testInputs.manual_price} onChange={(e) => setTestInputs({ ...testInputs, manual_price: e.target.value })} data-testid="review-manual-price" />
            </div>
          </div>

          <Button onClick={runTest} disabled={loading} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="review-run-test">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ClipboardCheck className="h-4 w-4 mr-2" />} Run Test
          </Button>

          {result && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" data-testid="review-results">
              <div className="space-y-2">
                <p className="text-xs text-gray-500">Estimated Costs</p>
                <div className="flex justify-between text-sm"><span>Material</span><span data-testid="review-material-cost">${(result.material_cost || 0).toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span>Labor</span><span data-testid="review-labor-cost">${(result.labor_cost || 0).toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span>Overhead</span><span data-testid="review-overhead">${(result.overhead_cost || 0).toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span>Total Production</span><span data-testid="review-production-cost">${(result.production_cost || 0).toFixed(2)}</span></div>
                <div className="flex justify-between text-sm font-medium"><span>Suggested Sell</span><span data-testid="review-suggested">${(result.selling_price || 0).toFixed(2)}</span></div>
              </div>
              <div className="space-y-2">
                <p className="text-xs text-gray-500">Manual Quote Comparison</p>
                <div className="flex justify-between text-sm"><span>Manual Price</span><span data-testid="review-manual">${manualPrice.toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span>Profit</span><span data-testid="review-profit">${profit.toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span>Margin</span><span data-testid="review-margin">{margin.toFixed(1)}%</span></div>
                <div className="mt-3 text-xs text-gray-500 space-y-1">
                  <p data-testid="review-source-material">Material Source: {testInputs.material_key ? 'User Selected' : 'Default'}</p>
                  <p data-testid="review-source-labor">Labor Source: {testInputs.labor_hours ? 'User Entered' : 'Default'}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
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
  const [hardwareAccessories, setHardwareAccessories] = useState([]);
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
      setHardwareAccessories(data.hardware_accessories || []);
      setSnapshotJson(JSON.stringify({ ...data, materials: data.materials || [], hardware_accessories: data.hardware_accessories || [] }));
    } catch { toast.error('Failed to load pricing data'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Detect changes
  useEffect(() => {
    if (!settings) return;
    const current = JSON.stringify({ ...settings, materials, hardware_accessories: hardwareAccessories });
    setHasChanges(current !== snapshotJson);
  }, [settings, materials, hardwareAccessories, snapshotJson]);

  const handleSettingsChange = (updated) => setSettings(updated);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = { ...settings, materials, hardware_accessories: hardwareAccessories };
      const res = await fetch(`${API}/api/pricing/defaults`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      const saved = await res.json();
      setSettings(saved);
      setMaterials(saved.materials || []);
      setHardwareAccessories(saved.hardware_accessories || []);
      setSnapshotJson(JSON.stringify({ ...saved, materials: saved.materials || [], hardware_accessories: saved.hardware_accessories || [] }));
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
        <TabsList className="bg-gray-100 p-1 flex flex-wrap">
          <TabsTrigger value="defaults" className="gap-1 text-sm" data-testid="tab-defaults"><DollarSign className="h-3.5 w-3.5" /> Shop Defaults</TabsTrigger>
          <TabsTrigger value="materials" className="gap-1 text-sm" data-testid="tab-materials"><Package className="h-3.5 w-3.5" /> Materials</TabsTrigger>
          <TabsTrigger value="hardware" className="gap-1 text-sm" data-testid="tab-hardware"><Wrench className="h-3.5 w-3.5" /> Hardware</TabsTrigger>
          <TabsTrigger value="labor" className="gap-1 text-sm" data-testid="tab-labor"><Factory className="h-3.5 w-3.5" /> Labor</TabsTrigger>
          <TabsTrigger value="categories" className="gap-1 text-sm" data-testid="tab-categories"><Layers3 className="h-3.5 w-3.5" /> Category Rules</TabsTrigger>
          <TabsTrigger value="ai" className="gap-1 text-sm" data-testid="tab-ai"><Sparkles className="h-3.5 w-3.5" /> AI Rules</TabsTrigger>
          <TabsTrigger value="benchmarks" className="gap-1 text-sm" data-testid="tab-benchmarks"><BarChart3 className="h-3.5 w-3.5" /> Benchmarks</TabsTrigger>
          <TabsTrigger value="global" className="gap-1 text-sm" data-testid="tab-global"><Settings2 className="h-3.5 w-3.5" /> Global Rules</TabsTrigger>
          <TabsTrigger value="review" className="gap-1 text-sm" data-testid="tab-review"><ClipboardCheck className="h-3.5 w-3.5" /> Review</TabsTrigger>
        </TabsList>

        <TabsContent value="defaults">
          <ShopDefaultsTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="materials">
          <MaterialsLibraryTab materials={materials} setMaterials={setMaterials} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="hardware">
          <HardwareAccessoriesTab items={hardwareAccessories} setItems={setHardwareAccessories} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="labor">
          <LaborRatesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="categories">
          <CategoryRulesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} materials={materials} />
        </TabsContent>

        <TabsContent value="ai">
          <AiEstimationRulesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="benchmarks">
          <BenchmarkRulesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="global">
          <GlobalCalculationRulesTab settings={settings} onChange={handleSettingsChange} canEdit={canEdit} />
        </TabsContent>

        <TabsContent value="review">
          <ReviewTestingPanel materials={materials} settings={settings} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
