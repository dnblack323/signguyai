import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, Loader2, Package, Plus, WandSparkles } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Checkbox } from '../ui/checkbox';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { getAuthToken } from '../../lib/authStorage';
import { Permission, useAuth } from '../../context/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });
const fmt = value => String(value || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function JobMaterialsPanel({ ticketId, onChanged }) {
  const { hasPermission } = useAuth();
  const canAdjust = hasPermission(Permission.INVENTORY_ADJUST);
  const canPull = hasPermission(Permission.INVENTORY_PULL);
  const [requirements, setRequirements] = useState([]);
  const [items, setItems] = useState([]);
  const [lots, setLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState('');
  const [editingRequirementId, setEditingRequirementId] = useState('');
  const [form, setForm] = useState({ inventory_item_id: '', required_quantity: 1, unit: 'each', expected_waste_percent: 0, required_width_inches: '', required_length_inches: '', notes: '', source: 'manual' });
  const [pull, setPull] = useState({ requirement_id: '', lot_id: '', pulled_quantity: 0, consumed_quantity: 0, waste_quantity: 0, returned_quantity: 0, waste_reason: '', create_remnant: false, remnant_width_inches: '', remnant_length_inches: '', notes: '' });
  const load = useCallback(async () => {
    try {
      const [reqRes, itemRes, lotRes] = await Promise.all([
        axios.get(`${API}/job-tickets/${ticketId}/material-requirements`, { headers: hdr() }),
        axios.get(`${API}/inventory/items`, { headers: hdr() }),
        axios.get(`${API}/inventory/lots`, { headers: hdr() }),
      ]);
      setRequirements(reqRes.data); setItems(itemRes.data); setLots(lotRes.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to load job materials'); }
    finally { setLoading(false); }
  }, [ticketId]);
  useEffect(() => { load(); }, [load]);
  const itemMap = useMemo(() => Object.fromEntries(items.map(item => [item.id, item])), [items]);
  const save = async () => { try { const payload = { ...form, required_quantity: Number(form.required_quantity), expected_waste_percent: Number(form.expected_waste_percent), required_width_inches: form.required_width_inches === '' ? null : Number(form.required_width_inches), required_length_inches: form.required_length_inches === '' ? null : Number(form.required_length_inches) }; if (editingRequirementId) await axios.put(`${API}/material-requirements/${editingRequirementId}`, payload, { headers: hdr() }); else await axios.post(`${API}/job-tickets/${ticketId}/material-requirements`, payload, { headers: hdr() }); toast.success(editingRequirementId ? 'Material requirement updated' : 'Material requirement added'); setDialog(''); setEditingRequirementId(''); load(); onChanged?.(); } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save requirement'); } };
  const generate = async () => { try { await axios.post(`${API}/job-tickets/${ticketId}/material-requirements/generate`, {}, { headers: hdr() }); toast.success('Material requirement generated'); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Could not generate requirement'); } };
  const reserve = async id => { try { await axios.post(`${API}/material-requirements/${id}/reserve`, {}, { headers: hdr() }); toast.success('Materials reserved'); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Reservation failed'); } };
  const editRequirement = req => { setEditingRequirementId(req.id); setForm({ inventory_item_id: req.inventory_item_id, required_quantity: req.required_quantity, unit: req.unit, expected_waste_percent: req.expected_waste_percent || 0, required_width_inches: req.required_width_inches || '', required_length_inches: req.required_length_inches || '', notes: req.notes || '', source: req.source || 'manual' }); setDialog('add'); };
  const openPull = req => { setPull({ requirement_id: req.id, lot_id: '', pulled_quantity: Math.max(Number(req.reserved_quantity || 0), Number(req.required_quantity || 0)), consumed_quantity: Number(req.required_quantity || 0), waste_quantity: 0, returned_quantity: 0, waste_reason: '', create_remnant: false, remnant_width_inches: '', remnant_length_inches: '', notes: '' }); setDialog('pull'); };
  const submitPull = async () => { try { await axios.post(`${API}/job-tickets/${ticketId}/pull-materials`, Object.fromEntries(Object.entries(pull).map(([k,v]) => ['pulled_quantity','consumed_quantity','waste_quantity','returned_quantity','remnant_width_inches','remnant_length_inches'].includes(k) ? [k, v === '' ? null : Number(v || 0)] : [k,v])), { headers: hdr() }); toast.success('Material pull recorded'); setDialog(''); load(); onChanged?.(); } catch (e) { toast.error(e.response?.data?.detail || 'Material pull failed'); } };
  const selectedRequirement = requirements.find(req => req.id === pull.requirement_id);
  const lotFits = lot => {
    if (!selectedRequirement?.required_width_inches || !selectedRequirement?.required_length_inches) return true;
    const width = Number(lot.width_inches || lot.sheet_width_inches || 0);
    const length = Number(lot.remaining_length_inches ?? lot.length_inches ?? lot.sheet_height_inches ?? 0);
    const rw = Number(selectedRequirement.required_width_inches); const rl = Number(selectedRequirement.required_length_inches);
    return (width >= rw && length >= rl) || (width >= rl && length >= rw);
  };
  if (loading) return <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin" /></div>;
  return <div className="space-y-4">
    {canAdjust && <div className="flex gap-2"><Button size="sm" onClick={() => { setEditingRequirementId(''); setForm({ inventory_item_id: '', required_quantity: 1, unit: 'each', expected_waste_percent: 0, required_width_inches: '', required_length_inches: '', notes: '', source: 'manual' }); setDialog('add'); }}><Plus className="w-4 h-4 mr-2" />Add Requirement</Button><Button size="sm" variant="outline" onClick={generate}><WandSparkles className="w-4 h-4 mr-2" />Generate from Specs</Button></div>}
      {!requirements.length ? <Card><CardContent className="p-6 text-sm text-gray-500">No material requirements yet.</CardContent></Card> : requirements.map(req => <Card key={req.id}><CardHeader className="pb-2"><div className="flex justify-between gap-3"><CardTitle className="text-base flex items-center gap-2"><Package className="w-4 h-4" />{itemMap[req.inventory_item_id]?.name || req.inventory_item_id}</CardTitle><Badge variant={req.status === 'short' ? 'destructive' : 'outline'}>{fmt(req.status)}</Badge></div></CardHeader><CardContent><div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm"><div><span className="text-gray-500">Required</span><p className="font-medium">{req.required_quantity} {req.unit}</p></div><div><span className="text-gray-500">Reserved</span><p className="font-medium">{req.reserved_quantity || 0}</p></div><div><span className="text-gray-500">Consumed</span><p className="font-medium">{req.consumed_quantity || 0}</p></div><div><span className="text-gray-500">Short</span><p className="font-medium text-red-600">{req.short_quantity || 0}</p></div><div><span className="text-gray-500">Dimensions</span><p className="font-medium">{req.required_width_inches && req.required_length_inches ? `${req.required_width_inches}" × ${req.required_length_inches}"` : 'None'}</p></div></div>{req.status === 'short' && <p className="mt-3 text-xs text-amber-700 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />Shortage appears in Purchasing.</p>}<div className="flex gap-2 mt-3">{canAdjust && <><Button size="sm" variant="outline" onClick={() => editRequirement(req)}>Edit</Button><Button size="sm" variant="outline" onClick={() => reserve(req.id)}>Reserve Available</Button></>}{canPull && <Button size="sm" onClick={() => openPull(req)}>Pull Materials</Button>}</div></CardContent></Card>)}
    <Dialog open={dialog === 'add'} onOpenChange={x => !x && setDialog('')}><DialogContent><DialogHeader><DialogTitle>{editingRequirementId ? 'Edit Material Requirement' : 'Add Material Requirement'}</DialogTitle></DialogHeader><div className="space-y-3"><Field label="Inventory Item"><Select value={form.inventory_item_id} onValueChange={x => { const item = itemMap[x]; setForm(v => ({ ...v, inventory_item_id: x, unit: item?.base_unit || 'each' })); }}><SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger><SelectContent>{items.map(x => <SelectItem key={x.id} value={x.id}>{x.name} · {x.available} available</SelectItem>)}</SelectContent></Select></Field><div className="grid grid-cols-2 gap-3"><Field label="Required Quantity"><Input type="number" value={form.required_quantity} onChange={e => setForm(v => ({ ...v, required_quantity: e.target.value }))} /></Field><Field label="Unit"><Input value={form.unit} onChange={e => setForm(v => ({ ...v, unit: e.target.value }))} /></Field><Field label="Required Width (in)"><Input type="number" value={form.required_width_inches} onChange={e => setForm(v => ({ ...v, required_width_inches: e.target.value }))} /></Field><Field label="Required Length (in)"><Input type="number" value={form.required_length_inches} onChange={e => setForm(v => ({ ...v, required_length_inches: e.target.value }))} /></Field></div><Field label="Notes"><Textarea value={form.notes} onChange={e => setForm(v => ({ ...v, notes: e.target.value }))} /></Field></div><DialogFooter><Button onClick={save}>{editingRequirementId ? 'Save Requirement' : 'Add Requirement'}</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'pull'} onOpenChange={x => !x && setDialog('')}><DialogContent><DialogHeader><DialogTitle>Pull Materials</DialogTitle></DialogHeader><div className="space-y-3"><Field label="Source Lot / Roll / Sheet / Remnant"><Select value={pull.lot_id} onValueChange={x => setPull(v => ({ ...v, lot_id: x }))}><SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger><SelectContent>{lots.filter(x => x.item_id === selectedRequirement?.inventory_item_id).map(x => <SelectItem key={x.id} value={x.id}>{lotFits(x) ? 'Fits' : 'Does not fit'} · {x.lot_number || x.id.slice(0,8)} · {x.available_quantity} available{x.width_inches ? ` · ${x.width_inches}" × ${x.remaining_length_inches}"` : ''}</SelectItem>)}</SelectContent></Select></Field><div className="grid grid-cols-2 gap-3">{[['Pulled','pulled_quantity'],['Consumed','consumed_quantity'],['Waste','waste_quantity'],['Returned','returned_quantity']].map(([label,key]) => <Field key={key} label={label}><Input type="number" value={pull[key]} onChange={e => setPull(v => ({ ...v, [key]: e.target.value }))} /></Field>)}</div><Field label="Waste Reason"><Input value={pull.waste_reason} onChange={e => setPull(v => ({ ...v, waste_reason: e.target.value }))} /></Field><div className="flex items-center gap-2"><Checkbox checked={pull.create_remnant} onCheckedChange={x => setPull(v => ({ ...v, create_remnant: Boolean(x) }))} /><Label>Create reusable remnant from returned material</Label></div>{pull.create_remnant && <div className="grid grid-cols-2 gap-3"><Field label="Remnant Width (in)"><Input type="number" value={pull.remnant_width_inches} onChange={e => setPull(v => ({ ...v, remnant_width_inches: e.target.value }))} /></Field><Field label="Remnant Length (in)"><Input type="number" value={pull.remnant_length_inches} onChange={e => setPull(v => ({ ...v, remnant_length_inches: e.target.value }))} /></Field></div>}<Field label="Notes"><Textarea value={pull.notes} onChange={e => setPull(v => ({ ...v, notes: e.target.value }))} /></Field></div><DialogFooter><Button onClick={submitPull}>Confirm Material Pull</Button></DialogFooter></DialogContent></Dialog>
  </div>;
}
function Field({ label, children }) { return <div className="space-y-1"><Label>{label}</Label>{children}</div>; }
