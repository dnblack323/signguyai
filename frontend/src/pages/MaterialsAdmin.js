import { useState, useEffect } from 'react';
import { Plus, Trash2, Save, Loader2, DollarSign, Package, ChevronDown, ChevronUp, Edit2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/json' });

const MATERIAL_CATEGORIES = [
  { value: 'print_material', label: 'Print / Banner Materials' },
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
  { value: 'per_stitch', label: 'Per Stitch (1000)' },
  { value: 'per_sqin', label: 'Per Sq In' },
  { value: 'flat', label: 'Flat Rate' },
];

export default function MaterialsAdmin() {
  const [defaults, setDefaults] = useState(null);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expandedCat, setExpandedCat] = useState(null);
  const [newItem, setNewItem] = useState(null);

  const loadData = async () => {
    try {
      const res = await axios.get(`${API}/pricing/defaults`, { headers: hdr() });
      setDefaults(res.data);
      setMaterials(res.data.materials || []);
    } catch { toast.error('Failed to load pricing settings'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const addMaterial = () => {
    setNewItem({
      key: '', name: '', category: expandedCat || 'print_material',
      cost_per_unit: 0, unit_type: 'sqft', description: '',
    });
  };

  const saveNewMaterial = async () => {
    if (!newItem.key || !newItem.name) { toast.error('ID and Name are required'); return; }
    const updated = [...materials, newItem];
    await saveAllMaterials(updated);
    setNewItem(null);
  };

  const removeMaterial = async (idx) => {
    const updated = materials.filter((_, i) => i !== idx);
    await saveAllMaterials(updated);
  };

  const updateMaterial = (idx, field, value) => {
    setMaterials(prev => prev.map((m, i) => i === idx ? { ...m, [field]: value } : m));
  };

  const saveAllMaterials = async (mats) => {
    setSaving(true);
    try {
      const updatedDefaults = { ...defaults, materials: mats || materials };
      await axios.put(`${API}/pricing/defaults`, updatedDefaults, { headers: hdr() });
      setMaterials(mats || materials);
      toast.success('Materials saved');
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save'); }
    finally { setSaving(false); }
  };

  const saveGlobalRates = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/pricing/defaults`, defaults, { headers: hdr() });
      toast.success('Pricing settings saved');
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save'); }
    finally { setSaving(false); }
  };

  const updateGlobal = (field, value) => {
    setDefaults(prev => ({ ...prev, [field]: value }));
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;

  // Group materials by category-like keys
  const grouped = {};
  materials.forEach((m, idx) => {
    const cat = m.category || 'other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push({ ...m, _idx: idx });
  });

  return (
    <div className="space-y-6" data-testid="materials-admin">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading flex items-center gap-3">
            <Package className="w-8 h-8 text-violet-400" /> Materials & Pricing
          </h1>
          <p className="text-slate-400 text-sm mt-1">Manage materials, costs, and labor rates used by the pricing calculator</p>
        </div>
        <Button onClick={() => saveAllMaterials()} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white gap-2">
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save All
        </Button>
      </div>

      {/* Global Rates */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg flex items-center gap-2"><DollarSign className="w-5 h-5 text-violet-600" /> Global Rates & Markup</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-gray-600 text-xs">Production Labor ($/hr)</Label>
              <Input type="number" step="0.01" value={defaults?.production_hourly_rate || ''} onChange={e => updateGlobal('production_hourly_rate', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Design Rate ($/hr)</Label>
              <Input type="number" step="0.01" value={defaults?.design_hourly_rate || ''} onChange={e => updateGlobal('design_hourly_rate', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Install Rate ($/hr)</Label>
              <Input type="number" step="0.01" value={defaults?.installer_hourly_rate || ''} onChange={e => updateGlobal('installer_hourly_rate', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Default Markup (x)</Label>
              <Input type="number" step="0.1" value={defaults?.default_markup_multiplier || ''} onChange={e => updateGlobal('default_markup_multiplier', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Overhead %</Label>
              <Input type="number" step="1" value={defaults?.overhead_percentage || ''} onChange={e => updateGlobal('overhead_percentage', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Target Profit Margin %</Label>
              <Input type="number" step="1" value={defaults?.target_profit_margin_percent || ''} onChange={e => updateGlobal('target_profit_margin_percent', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div>
              <Label className="text-gray-600 text-xs">Minimum Order ($)</Label>
              <Input type="number" step="1" value={defaults?.minimum_order || ''} onChange={e => updateGlobal('minimum_order', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 mt-1" />
            </div>
            <div className="flex items-end">
              <Button onClick={saveGlobalRates} disabled={saving} variant="outline" className="w-full gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Rates
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Materials List */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Materials ({materials.length})</h2>
        <Button variant="outline" size="sm" onClick={addMaterial} className="gap-2 bg-white"><Plus className="w-4 h-4" /> Add Material</Button>
      </div>

      {MATERIAL_CATEGORIES.map(cat => {
        const items = grouped[cat.value] || [];
        if (items.length === 0 && expandedCat !== cat.value) return null;
        const isExpanded = expandedCat === cat.value;

        return (
          <Card key={cat.value} className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid={`material-cat-${cat.value}`}>
            <button onClick={() => setExpandedCat(isExpanded ? null : cat.value)} className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-2">
                <h3 className="text-gray-900 font-medium">{cat.label}</h3>
                <Badge variant="outline" className="text-xs text-gray-500">{items.length}</Badge>
              </div>
              {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
            </button>
            {isExpanded && (
              <CardContent className="pt-0 space-y-2">
                {items.map(m => (
                  <div key={m._idx} className="grid grid-cols-12 gap-2 items-center bg-gray-50 rounded-lg p-2 border border-gray-200">
                    <div className="col-span-2">
                      <Input value={m.key} onChange={e => updateMaterial(m._idx, 'key', e.target.value)} placeholder="ID" className="bg-white border-gray-300 text-gray-900 h-8 text-xs" />
                    </div>
                    <div className="col-span-4">
                      <Input value={m.name} onChange={e => updateMaterial(m._idx, 'name', e.target.value)} placeholder="Material Name" className="bg-white border-gray-300 text-gray-900 h-8 text-sm" />
                    </div>
                    <div className="col-span-2">
                      <Input type="number" step="0.01" value={m.cost_per_unit} onChange={e => updateMaterial(m._idx, 'cost_per_unit', parseFloat(e.target.value) || 0)} className="bg-white border-gray-300 text-gray-900 h-8 text-sm" />
                    </div>
                    <div className="col-span-2">
                      <Select value={m.unit_type || 'sqft'} onValueChange={v => updateMaterial(m._idx, 'unit_type', v)}>
                        <SelectTrigger className="bg-white border-gray-300 text-gray-900 h-8 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>{UNIT_TYPES.map(u => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-2 flex justify-end">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-red-400 hover:text-red-600" onClick={() => removeMaterial(m._idx)}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
                {items.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No materials in this category</p>}
              </CardContent>
            )}
          </Card>
        );
      })}

      {/* Add New Material Dialog */}
      {newItem && (
        <Card className="bg-white rounded-xl border-2 border-violet-300 shadow-sm">
          <CardHeader><CardTitle className="text-gray-900 text-base">Add New Material</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div><Label className="text-gray-600 text-xs">Material ID *</Label><Input value={newItem.key} onChange={e => setNewItem(p => ({ ...p, key: e.target.value.toLowerCase().replace(/\s+/g, '_') }))} placeholder="e.g. banner_18oz" className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              <div><Label className="text-gray-600 text-xs">Name *</Label><Input value={newItem.name} onChange={e => setNewItem(p => ({ ...p, name: e.target.value }))} placeholder="e.g. 18oz Banner" className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              <div><Label className="text-gray-600 text-xs">Cost</Label><Input type="number" step="0.01" value={newItem.cost_per_unit} onChange={e => setNewItem(p => ({ ...p, cost_per_unit: parseFloat(e.target.value) || 0 }))} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              <div><Label className="text-gray-600 text-xs">Unit</Label>
                <Select value={newItem.unit_type} onValueChange={v => setNewItem(p => ({ ...p, unit_type: v }))}>
                  <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                  <SelectContent>{UNIT_TYPES.map(u => <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <div><Label className="text-gray-600 text-xs">Category</Label>
              <Select value={newItem.category} onValueChange={v => setNewItem(p => ({ ...p, category: v }))}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 w-64"><SelectValue /></SelectTrigger>
                <SelectContent>{MATERIAL_CATEGORIES.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button onClick={saveNewMaterial} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Add
              </Button>
              <Button variant="outline" onClick={() => setNewItem(null)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
