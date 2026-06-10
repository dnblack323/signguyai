import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowRightLeft, Boxes, ClipboardCheck, History, Loader2, MapPin, PackagePlus, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { getAuthToken } from '../lib/authStorage';
import { Permission, useAuth } from '../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });
const blankItem = { sku: '', name: '', category: 'other', tracking_method: 'quantity', base_unit: 'each', manufacturer: '', manufacturer_part_number: '', reorder_point: 0, preferred_stock_level: 0, pricing_material_key: '', notes: '', aliases: [], is_active: true };
const blankLocation = { name: '', code: '', location_type: 'bin', notes: '', is_active: true };
const blankLot = { item_id: '', location_id: '', lot_number: '', quantity_on_hand: 0, unit_cost: 0, width_inches: '', remaining_length_inches: '', sheet_width_inches: '', sheet_height_inches: '', thickness: '', pack_size: 1 };
const blankAdjustment = { item_id: '', lot_id: '', quantity_delta: 0, reason: '' };
const blankTransfer = { lot_id: '', destination_location_id: '', quantity: 0, reason: '' };
const blankAlias = { vendor_id: '', supplier_name: '', supplier_sku: '', supplier_product_name: '', manufacturer_sku: '', nickname: '', pack_quantity: 1, last_known_cost: 0, last_updated_at: null };

const n = (value) => Number(value || 0);
const money = (value) => `$${n(value).toFixed(2)}`;
const fmt = (value) => String(value || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

function Metric({ label, value, icon: Icon, tone = 'text-blue-600' }) {
  return <Card><CardContent className="p-4 flex items-center gap-3"><Icon className={`w-5 h-5 ${tone}`} /><div><p className="text-xs text-gray-500">{label}</p><p className="text-xl font-bold text-gray-900">{value}</p></div></CardContent></Card>;
}

export default function Inventory() {
  const { hasPermission } = useAuth();
  const canAdjust = hasPermission(Permission.INVENTORY_ADJUST);
  const canManagePurchasing = hasPermission(Permission.PURCHASING_MANAGE);
  const [summary, setSummary] = useState({ items: [] });
  const [locations, setLocations] = useState([]);
  const [lots, setLots] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [counts, setCounts] = useState([]);
  const [costSuggestions, setCostSuggestions] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState('');
  const [itemForm, setItemForm] = useState(blankItem);
  const [editingItemId, setEditingItemId] = useState('');
  const [locationForm, setLocationForm] = useState(blankLocation);
  const [lotForm, setLotForm] = useState(blankLot);
  const [adjustForm, setAdjustForm] = useState(blankAdjustment);
  const [transferForm, setTransferForm] = useState(blankTransfer);
  const [countValues, setCountValues] = useState({});
  const [countReasons, setCountReasons] = useState({});

  const load = useCallback(async () => {
    try {
      const [summaryRes, locationsRes, lotsRes, transactionsRes, countsRes, suggestionsRes, vendorsRes] = await Promise.all([
        axios.get(`${API}/inventory/summary`, { headers: hdr() }),
        axios.get(`${API}/inventory/locations`, { headers: hdr() }),
        axios.get(`${API}/inventory/lots`, { headers: hdr() }),
        axios.get(`${API}/inventory/transactions`, { headers: hdr() }),
        axios.get(`${API}/inventory/cycle-counts`, { headers: hdr() }),
        axios.get(`${API}/inventory/cost-suggestions`, { headers: hdr() }),
        canManagePurchasing ? axios.get(`${API}/vendors`, { headers: hdr() }) : Promise.resolve({ data: [] }),
      ]);
      setSummary(summaryRes.data); setLocations(locationsRes.data); setLots(lotsRes.data);
      setTransactions(transactionsRes.data); setCounts(countsRes.data);
      setCostSuggestions(suggestionsRes.data);
      setVendors(vendorsRes.data);
    } catch (error) { toast.error(error.response?.data?.detail || 'Failed to load inventory'); }
    finally { setLoading(false); }
  }, [canManagePurchasing]);
  useEffect(() => { load(); }, [load]);

  const itemMap = useMemo(() => Object.fromEntries((summary.items || []).map(item => [item.id, item])), [summary.items]);
  const locationMap = useMemo(() => Object.fromEntries(locations.map(location => [location.id, location])), [locations]);
  const lowStock = (summary.items || []).filter(item => n(item.reorder_point) > 0 && n(item.available) <= n(item.reorder_point));

  const saveItem = async () => {
    try {
      const payload = { ...itemForm, reorder_point: n(itemForm.reorder_point), preferred_stock_level: n(itemForm.preferred_stock_level) };
      if (editingItemId) await axios.put(`${API}/inventory/items/${editingItemId}`, payload, { headers: hdr() });
      else await axios.post(`${API}/inventory/items`, payload, { headers: hdr() });
      toast.success(editingItemId ? 'Inventory item updated' : 'Inventory item created'); setDialog(''); setItemForm(blankItem); setEditingItemId(''); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create item'); }
  };
  const saveLocation = async () => {
    try {
      await axios.post(`${API}/inventory/locations`, locationForm, { headers: hdr() });
      toast.success('Location created'); setDialog(''); setLocationForm(blankLocation); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create location'); }
  };
  const saveLot = async () => {
    try {
      const payload = { ...lotForm, quantity_on_hand: n(lotForm.quantity_on_hand), unit_cost: n(lotForm.unit_cost), pack_size: n(lotForm.pack_size), location_id: lotForm.location_id || null };
      ['width_inches', 'remaining_length_inches', 'sheet_width_inches', 'sheet_height_inches'].forEach(key => { payload[key] = lotForm[key] === '' ? null : n(lotForm[key]); });
      await axios.post(`${API}/inventory/lots`, payload, { headers: hdr() });
      toast.success('Stock received'); setDialog(''); setLotForm(blankLot); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to receive stock'); }
  };
  const saveAdjustment = async () => {
    try {
      await axios.post(`${API}/inventory/adjustments`, { ...adjustForm, quantity_delta: n(adjustForm.quantity_delta), lot_id: adjustForm.lot_id || null }, { headers: hdr() });
      toast.success('Adjustment recorded'); setDialog(''); setAdjustForm(blankAdjustment); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to adjust inventory'); }
  };
  const saveTransfer = async () => {
    try {
      await axios.post(`${API}/inventory/transfers`, { ...transferForm, quantity: n(transferForm.quantity) }, { headers: hdr() });
      toast.success('Stock transferred'); setDialog(''); setTransferForm(blankTransfer); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to transfer stock'); }
  };
  const importPricingMaterials = async () => {
    try {
      const { data } = await axios.post(`${API}/inventory/import-pricing-materials`, {}, { headers: hdr() });
      toast.success(`Imported ${data.created} pricing materials; skipped ${data.skipped}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to import Pricing Foundation materials'); }
  };
  const completeCount = async () => {
    const lines = lots.filter(lot => countValues[lot.id] !== undefined).map(lot => ({ item_id: lot.item_id, lot_id: lot.id, location_id: lot.location_id || null, actual_quantity: n(countValues[lot.id]), reason: countReasons[lot.id] || null }));
    if (!lines.length) return toast.error('Enter at least one actual quantity');
    try {
      await axios.post(`${API}/inventory/cycle-counts`, { name: `Cycle count ${new Date().toLocaleDateString()}`, lines }, { headers: hdr() });
      toast.success('Cycle count completed'); setCountValues({}); setCountReasons({}); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to complete count'); }
  };
  const updateAlias = (index, key, value) => setItemForm(form => ({
    ...form, aliases: form.aliases.map((alias, aliasIndex) => aliasIndex === index ? { ...alias, [key]: value } : alias),
  }));
  const addAlias = () => setItemForm(form => ({ ...form, aliases: [...(form.aliases || []), { ...blankAlias }] }));
  const removeAlias = index => setItemForm(form => ({ ...form, aliases: form.aliases.filter((_, aliasIndex) => aliasIndex !== index) }));

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  return <div className="space-y-5" data-testid="inventory-page">
    <div className="flex items-center justify-between gap-3 flex-wrap">
      <div><h1 className="text-2xl font-bold text-gray-900">Inventory</h1><p className="text-sm text-gray-500">Physical stock, reservations, counts, and activity</p></div>
      <div className="flex gap-2 flex-wrap">
        <Button variant="outline" onClick={load}><RefreshCw className="w-4 h-4 mr-2" />Refresh</Button>
        {canAdjust && <><Button variant="outline" onClick={importPricingMaterials}>Import Pricing Materials</Button>
        <Button variant="outline" onClick={() => setDialog('location')}><MapPin className="w-4 h-4 mr-2" />Add Location</Button>
        <Button variant="outline" onClick={() => setDialog('lot')}><PackagePlus className="w-4 h-4 mr-2" />Receive Stock</Button>
        <Button onClick={() => { setEditingItemId(''); setItemForm(blankItem); setDialog('item'); }}><Plus className="w-4 h-4 mr-2" />New Item</Button></>}
      </div>
    </div>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <Metric label="Active items" value={summary.item_count || 0} icon={Boxes} />
      <Metric label="Low stock" value={summary.low_stock_count || 0} icon={AlertTriangle} tone="text-amber-600" />
      <Metric label="Open shortages" value={summary.shortage_count || 0} icon={AlertTriangle} tone="text-red-600" />
      <Metric label="Inventory value" value={money(summary.inventory_value)} icon={PackagePlus} tone="text-emerald-600" />
    </div>
    <Tabs defaultValue="stock">
      <TabsList><TabsTrigger value="overview">Overview</TabsTrigger><TabsTrigger value="stock">Stock</TabsTrigger><TabsTrigger value="counts">Counts</TabsTrigger><TabsTrigger value="activity">Activity</TabsTrigger></TabsList>
      <TabsContent value="overview" className="space-y-3">
        <Card><CardHeader><CardTitle className="text-base">Low Stock Alerts</CardTitle></CardHeader><CardContent>
          {!lowStock.length ? <p className="text-sm text-gray-500">No low-stock items.</p> : <div className="space-y-2">{lowStock.map(item => <div key={item.id} className="flex justify-between border rounded-lg p-3"><div><p className="font-medium">{item.name}</p><p className="text-xs text-gray-500">{item.sku}</p></div><Badge variant="outline">{item.available} available / reorder at {item.reorder_point}</Badge></div>)}</div>}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">Pricing Foundation Cost Suggestions</CardTitle></CardHeader><CardContent>
          {!costSuggestions.length ? <p className="text-sm text-gray-500">No received-cost changes awaiting review.</p> : <div className="space-y-2">{costSuggestions.map(s => <div key={s.id} className="flex justify-between items-center border rounded-lg p-3"><div><p className="font-medium">{itemMap[s.inventory_item_id]?.name || s.pricing_material_key}</p><p className="text-xs text-gray-500">{money(s.current_cost)} current → {money(s.suggested_cost)} received cost</p></div><Link to="/pricing-foundation"><Button size="sm" variant="outline">Review Pricing</Button></Link></div>)}</div>}
        </CardContent></Card>
      </TabsContent>
      <TabsContent value="stock" className="space-y-4">
        <Card><CardContent className="p-0 overflow-x-auto"><table className="w-full text-sm"><thead className="bg-gray-50 text-left"><tr>{['Item', 'Tracking', 'On Hand', 'Reserved', 'Available', 'Incoming', 'Short', 'Action'].map(x => <th key={x} className="p-3">{x}</th>)}</tr></thead><tbody>
          {(summary.items || []).map(item => <tr key={item.id} className="border-t"><td className="p-3"><p className="font-medium">{item.name}</p><p className="text-xs text-gray-500">{item.sku} · {item.base_unit}</p></td><td className="p-3">{fmt(item.tracking_method)}</td><td className="p-3">{item.on_hand}</td><td className="p-3">{item.reserved}</td><td className="p-3 font-medium">{item.available}</td><td className="p-3">{item.incoming}</td><td className="p-3">{item.short || 0}</td><td className="p-3 flex gap-1">{canAdjust && <><Button size="sm" variant="outline" onClick={() => { setEditingItemId(item.id); setItemForm({ ...blankItem, ...item }); setDialog('item'); }}>Edit</Button><Button size="sm" variant="outline" onClick={() => { setAdjustForm({ ...blankAdjustment, item_id: item.id }); setDialog('adjust'); }}>Adjust</Button></>}</td></tr>)}
        </tbody></table></CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">Physical Lots and Locations</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto"><table className="w-full text-sm"><thead className="bg-gray-50 text-left"><tr>{['Item / Lot', 'Location', 'On Hand', 'Reserved', 'Available', 'Dimensions', 'Action'].map(x => <th key={x} className="p-3">{x}</th>)}</tr></thead><tbody>{lots.map(lot => <tr key={lot.id} className="border-t"><td className="p-3"><p className="font-medium">{itemMap[lot.item_id]?.name || lot.item_id}</p><p className="text-xs text-gray-500">{lot.lot_number || lot.id.slice(0, 8)}</p></td><td className="p-3">{locationMap[lot.location_id]?.name || 'Unlocated'}</td><td className="p-3">{lot.quantity_on_hand}</td><td className="p-3">{lot.reserved_quantity || 0}</td><td className="p-3">{lot.available_quantity}</td><td className="p-3">{lot.width_inches ? `${lot.width_inches}" x ${lot.remaining_length_inches}"` : lot.sheet_width_inches ? `${lot.sheet_width_inches}" x ${lot.sheet_height_inches}"` : '-'}</td><td className="p-3">{canAdjust && <Button size="sm" variant="outline" onClick={() => { setTransferForm({ ...blankTransfer, lot_id: lot.id, quantity: lot.available_quantity }); setDialog('transfer'); }}><ArrowRightLeft className="w-4 h-4 mr-2" />Transfer</Button>}</td></tr>)}</tbody></table></CardContent></Card>
      </TabsContent>
      <TabsContent value="counts" className="space-y-4">
        <Card><CardHeader><CardTitle className="text-base flex items-center gap-2"><ClipboardCheck className="w-4 h-4" />New Cycle Count</CardTitle></CardHeader><CardContent className="space-y-3">
          <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left border-b"><th className="p-2">Item / Lot</th><th className="p-2">Expected</th><th className="p-2">Actual</th><th className="p-2">Reason if different</th></tr></thead><tbody>{lots.map(lot => <tr key={lot.id} className="border-b"><td className="p-2">{itemMap[lot.item_id]?.name || lot.item_id}<span className="block text-xs text-gray-500">{lot.lot_number || lot.id.slice(0, 8)} · {locationMap[lot.location_id]?.name || 'No location'}</span></td><td className="p-2">{lot.quantity_on_hand}</td><td className="p-2"><Input className="w-28" type="number" value={countValues[lot.id] ?? ''} onChange={e => setCountValues(v => ({ ...v, [lot.id]: e.target.value }))} /></td><td className="p-2"><Input value={countReasons[lot.id] || ''} onChange={e => setCountReasons(v => ({ ...v, [lot.id]: e.target.value }))} /></td></tr>)}</tbody></table></div>
          {canAdjust && <Button onClick={completeCount}>Complete Count</Button>}
        </CardContent></Card>
        <Card><CardHeader><CardTitle className="text-base">Completed Counts</CardTitle></CardHeader><CardContent>{!counts.length ? <p className="text-sm text-gray-500">No completed cycle counts.</p> : counts.map(count => <div key={count.id} className="border-b py-2 flex justify-between"><span>{count.name}</span><span className="text-xs text-gray-500">{count.lines?.length || 0} lines · {new Date(count.completed_at).toLocaleString()}</span></div>)}</CardContent></Card>
      </TabsContent>
      <TabsContent value="activity"><Card><CardHeader><CardTitle className="text-base flex items-center gap-2"><History className="w-4 h-4" />Transaction Ledger</CardTitle></CardHeader><CardContent className="p-0 overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left bg-gray-50"><th className="p-3">Date</th><th className="p-3">Item</th><th className="p-3">Type</th><th className="p-3">Quantity</th><th className="p-3">Reason</th><th className="p-3">Actor</th></tr></thead><tbody>{transactions.map(tx => <tr key={tx.id} className="border-t"><td className="p-3">{new Date(tx.created_at).toLocaleString()}</td><td className="p-3">{itemMap[tx.item_id]?.name || tx.item_id}</td><td className="p-3">{fmt(tx.transaction_type)}</td><td className="p-3">{tx.quantity} {tx.unit}</td><td className="p-3">{tx.reason}</td><td className="p-3">{tx.actor_name}</td></tr>)}</tbody></table></CardContent></Card></TabsContent>
    </Tabs>

    <Dialog open={dialog === 'item'} onOpenChange={open => !open && setDialog('')}><DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto"><DialogHeader><DialogTitle>{editingItemId ? 'Edit Inventory Item' : 'New Inventory Item'}</DialogTitle></DialogHeader><div className="grid grid-cols-2 gap-3">
      <Field label="Internal SKU"><Input value={itemForm.sku} onChange={e => setItemForm(v => ({ ...v, sku: e.target.value }))} /></Field><Field label="Name"><Input value={itemForm.name} onChange={e => setItemForm(v => ({ ...v, name: e.target.value }))} /></Field>
      <Field label="Category"><Input value={itemForm.category} onChange={e => setItemForm(v => ({ ...v, category: e.target.value }))} /></Field><Field label="Tracking"><Select value={itemForm.tracking_method} onValueChange={x => setItemForm(v => ({ ...v, tracking_method: x }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['quantity', 'roll', 'sheet', 'remnant', 'pack'].map(x => <SelectItem key={x} value={x}>{fmt(x)}</SelectItem>)}</SelectContent></Select></Field>
      <Field label="Base Unit"><Select value={itemForm.base_unit} onValueChange={x => setItemForm(v => ({ ...v, base_unit: x }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['each', 'sqft', 'linear_ft', 'linear_inches', 'pack'].map(x => <SelectItem key={x} value={x}>{fmt(x)}</SelectItem>)}</SelectContent></Select></Field><Field label="Pricing Material Key"><Input value={itemForm.pricing_material_key} onChange={e => setItemForm(v => ({ ...v, pricing_material_key: e.target.value }))} /></Field>
      <Field label="Reorder Point"><Input type="number" value={itemForm.reorder_point} onChange={e => setItemForm(v => ({ ...v, reorder_point: e.target.value }))} /></Field><Field label="Preferred Stock"><Input type="number" value={itemForm.preferred_stock_level} onChange={e => setItemForm(v => ({ ...v, preferred_stock_level: e.target.value }))} /></Field>
      <div className="col-span-2 space-y-2"><div className="flex justify-between items-center"><Label>Supplier Aliases</Label><Button type="button" size="sm" variant="outline" onClick={addAlias}><Plus className="w-4 h-4 mr-2" />Add Alias</Button></div>{!(itemForm.aliases || []).length ? <p className="text-xs text-gray-500">No supplier aliases.</p> : itemForm.aliases.map((alias, index) => <Card key={alias.id || index}><CardContent className="p-3 grid grid-cols-2 gap-2"><Field label="Vendor">{vendors.length ? <Select value={alias.vendor_id || 'none'} onValueChange={value => updateAlias(index, 'vendor_id', value === 'none' ? null : value)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">No linked vendor</SelectItem>{vendors.map(vendor => <SelectItem key={vendor.id} value={vendor.id}>{vendor.name}</SelectItem>)}</SelectContent></Select> : <Input value={alias.supplier_name || ''} onChange={event => updateAlias(index, 'supplier_name', event.target.value)} placeholder="Supplier name" />}</Field><Field label="Supplier Name"><Input value={alias.supplier_name || ''} onChange={event => updateAlias(index, 'supplier_name', event.target.value)} /></Field><Field label="Supplier SKU"><Input value={alias.supplier_sku || ''} onChange={event => updateAlias(index, 'supplier_sku', event.target.value)} /></Field><Field label="Supplier Product Name"><Input value={alias.supplier_product_name || ''} onChange={event => updateAlias(index, 'supplier_product_name', event.target.value)} /></Field><Field label="Manufacturer SKU"><Input value={alias.manufacturer_sku || ''} onChange={event => updateAlias(index, 'manufacturer_sku', event.target.value)} /></Field><Field label="Nickname"><Input value={alias.nickname || ''} onChange={event => updateAlias(index, 'nickname', event.target.value)} /></Field><Field label="Pack Quantity"><Input type="number" value={alias.pack_quantity || 1} onChange={event => updateAlias(index, 'pack_quantity', Number(event.target.value || 1))} /></Field><Field label="Last Known Cost"><Input type="number" value={alias.last_known_cost || 0} onChange={event => { updateAlias(index, 'last_known_cost', Number(event.target.value || 0)); updateAlias(index, 'last_updated_at', new Date().toISOString()); }} /></Field><div className="col-span-2 flex justify-end"><Button type="button" size="sm" variant="outline" onClick={() => removeAlias(index)}><Trash2 className="w-4 h-4 mr-2" />Remove Alias</Button></div></CardContent></Card>)}</div>
      <Field label="Notes" className="col-span-2"><Textarea value={itemForm.notes} onChange={e => setItemForm(v => ({ ...v, notes: e.target.value }))} /></Field>
    </div><DialogFooter><Button onClick={saveItem}>{editingItemId ? 'Save Item' : 'Create Item'}</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'location'} onOpenChange={open => !open && setDialog('')}><DialogContent><DialogHeader><DialogTitle>Add Location or Bin</DialogTitle></DialogHeader><div className="space-y-3"><Field label="Name"><Input value={locationForm.name} onChange={e => setLocationForm(v => ({ ...v, name: e.target.value }))} /></Field><Field label="Code"><Input value={locationForm.code} onChange={e => setLocationForm(v => ({ ...v, code: e.target.value }))} /></Field><Field label="Type"><Select value={locationForm.location_type} onValueChange={x => setLocationForm(v => ({ ...v, location_type: x }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{['receiving', 'warehouse', 'rack', 'shelf', 'bin', 'production'].map(x => <SelectItem key={x} value={x}>{fmt(x)}</SelectItem>)}</SelectContent></Select></Field></div><DialogFooter><Button onClick={saveLocation}>Add Location</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'lot'} onOpenChange={open => !open && setDialog('')}><DialogContent className="max-w-2xl"><DialogHeader><DialogTitle>Receive Stock</DialogTitle></DialogHeader><div className="grid grid-cols-2 gap-3"><Field label="Item"><Select value={lotForm.item_id} onValueChange={x => setLotForm(v => ({ ...v, item_id: x }))}><SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger><SelectContent>{(summary.items || []).map(x => <SelectItem key={x.id} value={x.id}>{x.name}</SelectItem>)}</SelectContent></Select></Field><Field label="Location"><Select value={lotForm.location_id || 'none'} onValueChange={x => setLotForm(v => ({ ...v, location_id: x === 'none' ? '' : x }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">No location</SelectItem>{locations.map(x => <SelectItem key={x.id} value={x.id}>{x.name}</SelectItem>)}</SelectContent></Select></Field><Field label="Quantity"><Input type="number" value={lotForm.quantity_on_hand} onChange={e => setLotForm(v => ({ ...v, quantity_on_hand: e.target.value }))} /></Field><Field label="Unit Cost"><Input type="number" value={lotForm.unit_cost} onChange={e => setLotForm(v => ({ ...v, unit_cost: e.target.value }))} /></Field><Field label="Lot Number"><Input value={lotForm.lot_number} onChange={e => setLotForm(v => ({ ...v, lot_number: e.target.value }))} /></Field><Field label="Roll Width (in)"><Input type="number" value={lotForm.width_inches} onChange={e => setLotForm(v => ({ ...v, width_inches: e.target.value }))} /></Field><Field label="Remaining Length (in)"><Input type="number" value={lotForm.remaining_length_inches} onChange={e => setLotForm(v => ({ ...v, remaining_length_inches: e.target.value }))} /></Field><Field label="Sheet Width (in)"><Input type="number" value={lotForm.sheet_width_inches} onChange={e => setLotForm(v => ({ ...v, sheet_width_inches: e.target.value }))} /></Field><Field label="Sheet Height (in)"><Input type="number" value={lotForm.sheet_height_inches} onChange={e => setLotForm(v => ({ ...v, sheet_height_inches: e.target.value }))} /></Field><Field label="Thickness"><Input value={lotForm.thickness} onChange={e => setLotForm(v => ({ ...v, thickness: e.target.value }))} /></Field><Field label="Pack Size"><Input type="number" value={lotForm.pack_size} onChange={e => setLotForm(v => ({ ...v, pack_size: e.target.value }))} /></Field></div><DialogFooter><Button onClick={saveLot}>Receive</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'transfer'} onOpenChange={open => !open && setDialog('')}><DialogContent><DialogHeader><DialogTitle>Transfer Stock</DialogTitle></DialogHeader><div className="space-y-3"><Field label="Destination Location"><Select value={transferForm.destination_location_id} onValueChange={x => setTransferForm(v => ({ ...v, destination_location_id: x }))}><SelectTrigger><SelectValue placeholder="Select destination" /></SelectTrigger><SelectContent>{locations.filter(x => x.id !== lots.find(lot => lot.id === transferForm.lot_id)?.location_id).map(x => <SelectItem key={x.id} value={x.id}>{x.name}</SelectItem>)}</SelectContent></Select></Field><Field label="Quantity"><Input type="number" value={transferForm.quantity} onChange={e => setTransferForm(v => ({ ...v, quantity: e.target.value }))} /></Field><Field label="Required Reason"><Textarea value={transferForm.reason} onChange={e => setTransferForm(v => ({ ...v, reason: e.target.value }))} /></Field></div><DialogFooter><Button onClick={saveTransfer}>Transfer</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'adjust'} onOpenChange={open => !open && setDialog('')}><DialogContent><DialogHeader><DialogTitle>Manual Adjustment</DialogTitle></DialogHeader><div className="space-y-3"><Field label="Lot"><Select value={adjustForm.lot_id || 'none'} onValueChange={x => setAdjustForm(v => ({ ...v, lot_id: x === 'none' ? '' : x }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">Create unlocated lot</SelectItem>{lots.filter(x => x.item_id === adjustForm.item_id).map(x => <SelectItem key={x.id} value={x.id}>{x.lot_number || x.id.slice(0, 8)} · {x.quantity_on_hand}</SelectItem>)}</SelectContent></Select></Field><Field label="Quantity Change"><Input type="number" value={adjustForm.quantity_delta} onChange={e => setAdjustForm(v => ({ ...v, quantity_delta: e.target.value }))} /></Field><Field label="Required Reason"><Textarea value={adjustForm.reason} onChange={e => setAdjustForm(v => ({ ...v, reason: e.target.value }))} /></Field></div><DialogFooter><Button onClick={saveAdjustment}>Record Adjustment</Button></DialogFooter></DialogContent></Dialog>
  </div>;
}

function Field({ label, children, className = '' }) { return <div className={`space-y-1 ${className}`}><Label>{label}</Label>{children}</div>; }
