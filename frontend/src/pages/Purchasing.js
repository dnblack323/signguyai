import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, Ban, Building2, CheckCircle, Loader2, PackageCheck, Plus, Send, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
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
const fmt = x => String(x || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const money = x => `$${Number(x || 0).toFixed(2)}`;
const blankVendor = { name: '', website: '', account_number: '', default_shipping_notes: '', contact_name: '', email: '', phone: '', notes: '', is_active: true };

export default function Purchasing() {
  const { hasPermission } = useAuth();
  const canApprove = hasPermission(Permission.PURCHASING_APPROVE);
  const [shortages, setShortages] = useState([]);
  const [orders, setOrders] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [items, setItems] = useState([]);
  const [locations, setLocations] = useState([]);
  const [selected, setSelected] = useState([]);
  const [vendorId, setVendorId] = useState('');
  const [vendorForm, setVendorForm] = useState(blankVendor);
  const [dialog, setDialog] = useState('');
  const [receivePo, setReceivePo] = useState(null);
  const [editPo, setEditPo] = useState(null);
  const [receiveValues, setReceiveValues] = useState({});
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    try {
      const [shortRes, poRes, vendorRes, itemRes, locationRes] = await Promise.all([
        axios.get(`${API}/inventory/shortages`, { headers: hdr() }), axios.get(`${API}/purchase-orders`, { headers: hdr() }),
        axios.get(`${API}/vendors`, { headers: hdr() }), axios.get(`${API}/inventory/items`, { headers: hdr() }),
        axios.get(`${API}/inventory/locations`, { headers: hdr() }),
      ]);
      setShortages(shortRes.data); setOrders(poRes.data); setVendors(vendorRes.data); setItems(itemRes.data); setLocations(locationRes.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to load purchasing'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  const itemMap = useMemo(() => Object.fromEntries(items.map(x => [x.id, x])), [items]);
  const createVendor = async () => { try { const { data } = await axios.post(`${API}/vendors`, vendorForm, { headers: hdr() }); setVendorId(data.id); setDialog(''); setVendorForm(blankVendor); toast.success('Vendor created'); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create vendor'); } };
  const createPo = async () => { if (!vendorId || !selected.length) return toast.error('Select a vendor and shortages'); try { await axios.post(`${API}/purchase-orders/from-shortages`, { vendor_id: vendorId, shortage_ids: selected }, { headers: hdr() }); setSelected([]); toast.success('Draft PO created'); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create PO'); } };
  const action = async (po, verb) => { try { await axios.post(`${API}/purchase-orders/${po.id}/${verb}`, {}, { headers: hdr() }); toast.success(`Purchase order ${verb.replace('-', ' ')}`); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Action failed'); } };
  const openEdit = po => { setEditPo({ ...po, lines: po.lines.map(line => ({ ...line })) }); setDialog('edit'); };
  const savePo = async () => { try { await axios.put(`${API}/purchase-orders/${editPo.id}`, { notes: editPo.notes, expected_delivery_date: editPo.expected_delivery_date, lines: editPo.lines }, { headers: hdr() }); toast.success('Draft PO updated'); setDialog(''); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Failed to update PO'); } };
  const openReceive = po => { setReceivePo(po); setReceiveValues(Object.fromEntries(po.lines.map(line => [line.id, { received_quantity: 0, damaged_quantity: Number(line.damaged_quantity || 0), missing_quantity: Number(line.missing_quantity || 0), backordered_quantity: Number(line.backordered_quantity || 0), substituted_quantity: Number(line.substituted_quantity || 0), actual_unit_cost: line.actual_unit_cost ?? line.unit_cost, location_id: '' }]))); setDialog('receive'); };
  const receive = async () => { try { await axios.post(`${API}/purchase-orders/${receivePo.id}/receive`, { lines: receivePo.lines.map(line => ({ line_id: line.id, ...receiveValues[line.id], received_quantity: Number(receiveValues[line.id].received_quantity || 0), actual_unit_cost: Number(receiveValues[line.id].actual_unit_cost || 0) })) }, { headers: hdr() }); toast.success('Purchase order received'); setDialog(''); load(); } catch (e) { toast.error(e.response?.data?.detail || 'Receiving failed'); } };
  if (loading) return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin" /></div>;
  return <div className="space-y-5" data-testid="purchasing-page">
    <div className="flex justify-between gap-3 flex-wrap"><div><h1 className="text-2xl font-bold text-gray-900">Purchasing</h1><p className="text-sm text-gray-500">Shortages, manual purchase orders, vendors, and receiving</p></div><Button variant="outline" onClick={() => setDialog('vendor')}><Building2 className="w-4 h-4 mr-2" />Add Vendor</Button></div>
    <Tabs defaultValue="shortages"><TabsList><TabsTrigger value="shortages">Shortages ({shortages.length})</TabsTrigger><TabsTrigger value="orders">Purchase Orders ({orders.length})</TabsTrigger><TabsTrigger value="vendors">Vendors ({vendors.length})</TabsTrigger></TabsList>
      <TabsContent value="shortages" className="space-y-3"><Card><CardHeader><CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-600" />Open Shortages</CardTitle></CardHeader><CardContent className="space-y-3">
        <div className="flex gap-2"><Select value={vendorId} onValueChange={setVendorId}><SelectTrigger className="max-w-xs"><SelectValue placeholder="Select vendor for draft PO" /></SelectTrigger><SelectContent>{vendors.map(v => <SelectItem key={v.id} value={v.id}>{v.name}</SelectItem>)}</SelectContent></Select><Button onClick={createPo}>Create Draft PO</Button></div>
        {!shortages.length ? <p className="text-sm text-gray-500">No open shortages.</p> : shortages.map(s => <div key={s.id} className="flex items-center gap-3 border rounded-lg p-3"><Checkbox checked={selected.includes(s.id)} onCheckedChange={x => setSelected(v => x ? [...v, s.id] : v.filter(id => id !== s.id))} /><div className="flex-1"><p className="font-medium">{itemMap[s.inventory_item_id]?.name || s.inventory_item_id}</p><p className="text-xs text-gray-500">Job ticket {s.job_ticket_id?.slice(0, 8)} | Order {s.order_id?.slice(0, 8)}</p></div><Badge variant="outline">{s.quantity} {s.unit} short</Badge></div>)}
      </CardContent></Card></TabsContent>
      <TabsContent value="orders" className="space-y-3">{!orders.length ? <Card><CardContent className="p-6 text-sm text-gray-500">No purchase orders.</CardContent></Card> : orders.map(po => <Card key={po.id}><CardHeader className="pb-2"><div className="flex justify-between gap-3"><div><CardTitle className="text-base">{po.po_number} | {po.vendor_name}</CardTitle><p className="text-xs text-gray-500">{new Date(po.created_at).toLocaleString()}</p></div><Badge>{fmt(po.status)}</Badge></div></CardHeader><CardContent><div className="space-y-1 mb-3">{po.lines.map(line => <div key={line.id} className="flex justify-between text-sm border-b py-1"><span>{line.description || itemMap[line.inventory_item_id]?.name}</span><span>{line.ordered_quantity} {line.unit} | {money(line.unit_cost)} each | received {line.received_quantity || 0}</span></div>)}</div><div className="flex gap-2 flex-wrap">{po.status === 'draft' && <><Button size="sm" variant="outline" onClick={() => openEdit(po)}>Edit Costs</Button>{canApprove && <Button size="sm" onClick={() => action(po, 'approve')}><CheckCircle className="w-4 h-4 mr-2" />Approve</Button>}</>}{po.status === 'approved' && <Button size="sm" onClick={() => action(po, 'mark-sent')}><Send className="w-4 h-4 mr-2" />Mark Sent</Button>}{['approved', 'sent', 'partially_received'].includes(po.status) && <Button size="sm" variant="outline" onClick={() => openReceive(po)}><PackageCheck className="w-4 h-4 mr-2" />Receive</Button>}{['draft', 'approved', 'sent'].includes(po.status) && <Button size="sm" variant="outline" onClick={() => action(po, 'cancel')}><Ban className="w-4 h-4 mr-2" />Cancel</Button>}{['received', 'partially_received'].includes(po.status) && <Button size="sm" variant="outline" onClick={() => action(po, 'close')}><XCircle className="w-4 h-4 mr-2" />Close</Button>}</div></CardContent></Card>)}</TabsContent>
      <TabsContent value="vendors"><Card><CardContent className="p-0 overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left bg-gray-50"><th className="p-3">Vendor</th><th className="p-3">Account</th><th className="p-3">Contact</th><th className="p-3">Shipping Notes</th></tr></thead><tbody>{vendors.map(v => <tr key={v.id} className="border-t"><td className="p-3 font-medium">{v.name}<span className="block text-xs text-blue-600">{v.website}</span></td><td className="p-3">{v.account_number}</td><td className="p-3">{v.contact_name}<span className="block text-xs text-gray-500">{v.email} {v.phone}</span></td><td className="p-3">{v.default_shipping_notes}</td></tr>)}</tbody></table></CardContent></Card></TabsContent>
    </Tabs>
    <Dialog open={dialog === 'vendor'} onOpenChange={x => !x && setDialog('')}><DialogContent><DialogHeader><DialogTitle>Add Vendor</DialogTitle></DialogHeader><div className="space-y-3">{[['Name','name'],['Website','website'],['Account Number','account_number'],['Contact Name','contact_name'],['Email','email'],['Phone','phone']].map(([label,key]) => <div key={key}><Label>{label}</Label><Input value={vendorForm[key]} onChange={e => setVendorForm(v => ({ ...v, [key]: e.target.value }))} /></div>)}<div><Label>Default Shipping Notes</Label><Textarea value={vendorForm.default_shipping_notes} onChange={e => setVendorForm(v => ({ ...v, default_shipping_notes: e.target.value }))} /></div></div><DialogFooter><Button onClick={createVendor}><Plus className="w-4 h-4 mr-2" />Add Vendor</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'receive'} onOpenChange={x => !x && setDialog('')}><DialogContent className="max-w-3xl"><DialogHeader><DialogTitle>Receive {receivePo?.po_number}</DialogTitle></DialogHeader><div className="space-y-3 max-h-[60vh] overflow-auto">{receivePo?.lines.map(line => { const val = receiveValues[line.id] || {}; return <Card key={line.id}><CardContent className="p-3 grid grid-cols-2 md:grid-cols-4 gap-2"><div className="col-span-full font-medium">{line.description || itemMap[line.inventory_item_id]?.name}</div>{[['Received','received_quantity'],['Damaged','damaged_quantity'],['Missing','missing_quantity'],['Backordered','backordered_quantity'],['Substituted','substituted_quantity'],['Actual Unit Cost','actual_unit_cost']].map(([label,key]) => <div key={key}><Label className="text-xs">{label}</Label><Input type="number" value={val[key] ?? 0} onChange={e => setReceiveValues(all => ({ ...all, [line.id]: { ...all[line.id], [key]: e.target.value } }))} /></div>)}<div className="md:col-span-2"><Label className="text-xs">Location</Label><Select value={val.location_id || 'none'} onValueChange={x => setReceiveValues(all => ({ ...all, [line.id]: { ...all[line.id], location_id: x === 'none' ? '' : x } }))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">No location</SelectItem>{locations.map(x => <SelectItem key={x.id} value={x.id}>{x.name}</SelectItem>)}</SelectContent></Select></div></CardContent></Card>; })}</div><DialogFooter><Button onClick={receive}>Receive Items</Button></DialogFooter></DialogContent></Dialog>
    <Dialog open={dialog === 'edit'} onOpenChange={x => !x && setDialog('')}><DialogContent className="max-w-3xl"><DialogHeader><DialogTitle>Edit Draft {editPo?.po_number}</DialogTitle></DialogHeader><div className="space-y-3">{editPo?.lines.map((line, index) => <Card key={line.id}><CardContent className="p-3 grid grid-cols-3 gap-2"><div className="col-span-full font-medium">{line.description}</div><div><Label className="text-xs">Supplier SKU</Label><Input value={line.supplier_sku || ''} onChange={e => setEditPo(po => ({ ...po, lines: po.lines.map((x,i) => i === index ? { ...x, supplier_sku: e.target.value } : x) }))} /></div><div><Label className="text-xs">Quantity</Label><Input type="number" value={line.ordered_quantity} onChange={e => setEditPo(po => ({ ...po, lines: po.lines.map((x,i) => i === index ? { ...x, ordered_quantity: Number(e.target.value) } : x) }))} /></div><div><Label className="text-xs">Unit Cost</Label><Input type="number" value={line.unit_cost} onChange={e => setEditPo(po => ({ ...po, lines: po.lines.map((x,i) => i === index ? { ...x, unit_cost: Number(e.target.value) } : x) }))} /></div></CardContent></Card>)}</div><DialogFooter><Button onClick={savePo}>Save Draft</Button></DialogFooter></DialogContent></Dialog>
  </div>;
}
