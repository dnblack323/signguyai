import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Loader2, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';
import DynamicCategoryFields from '../components/DynamicCategoryFields';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const token = () => localStorage.getItem('auth_token');
const headers = () => ({ Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' });

const CATEGORIES = [
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'banners', label: 'Banners' },
  { value: 'cut_vinyl', label: 'Cut Vinyl / Lettering' },
  { value: 'vehicle_wrap', label: 'Vehicle Wrap' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'promo_misc', label: 'Promotional / Misc' },
  { value: 'custom', label: 'Custom' },
];

const SOURCES = [
  { value: 'phone', label: 'Phone' },
  { value: 'walk_in', label: 'Walk-in' },
  { value: 'email', label: 'Email' },
  { value: 'website', label: 'Website' },
  { value: 'repeat_order', label: 'Repeat Order' },
  { value: 'sales_rep', label: 'Sales Rep' },
];

export default function NewOrderForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [saving, setSaving] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [order, setOrder] = useState({
    customer_name: searchParams.get('customer_name') || '',
    contact_name: searchParams.get('customer_name') || '',
    phone: searchParams.get('phone') || '',
    email: searchParams.get('email') || '',
    company_name: searchParams.get('company') || '',
    customer_id: searchParams.get('customer_id') || '',
    order_source: 'phone', requested_due_date: '', event_date: '',
    pickup_delivery_method: 'pickup', pickup_delivery_notes: '',
    internal_notes: '', customer_notes: '',
  });
  const [tickets, setTickets] = useState([{
    item_name: '', item_category: 'custom', quantity: 1, priority: 'normal',
    production_flow_enabled: false, design_needed: false, proof_required: false,
    estimated_price: 0, special_instructions: '',
    specs: { width: '', height: '', material: '', substrate: '' },
  }]);

  useEffect(() => {
    axios.get(`${API}/customers?limit=100`, { headers: headers() })
      .then(r => setCustomers(r.data?.customers || r.data || []))
      .catch(() => {});
  }, []);

  const updateOrder = (field, value) => setOrder(prev => ({ ...prev, [field]: value }));
  const updateTicket = (i, field, value) => setTickets(prev => prev.map((t, idx) => idx === i ? { ...t, [field]: value } : t));
  const updateTicketSpec = (i, field, value) => setTickets(prev => prev.map((t, idx) => idx === i ? { ...t, specs: { ...t.specs, [field]: value } } : t));
  const addTicket = () => setTickets(prev => [...prev, { item_name: '', item_category: 'custom', quantity: 1, priority: 'normal', production_flow_enabled: false, design_needed: false, proof_required: false, estimated_price: 0, special_instructions: '', specs: { width: '', height: '', material: '', substrate: '' } }]);
  const removeTicket = (i) => setTickets(prev => prev.filter((_, idx) => idx !== i));

  const selectCustomer = (customerId) => {
    const c = customers.find(x => x.id === customerId);
    if (c) {
      setOrder(prev => ({
        ...prev,
        customer_id: c.id,
        customer_name: c.name || '',
        contact_name: c.name || '',
        phone: c.phone || '',
        email: c.email || '',
        company_name: c.company || '',
      }));
    }
  };

  const handleSave = async (generateQuote = false) => {
    if (!order.customer_name.trim()) { toast.error('Customer name is required'); return; }
    if (!tickets.some(t => t.item_name.trim())) { toast.error('At least one ticket needs a name'); return; }

    setSaving(true);
    try {
      const orderRes = await axios.post(`${API}/orders`, order, { headers: headers() });
      const orderId = orderRes.data.id;

      for (const t of tickets) {
        if (!t.item_name.trim()) continue;
        await axios.post(`${API}/job-tickets`, { ...t, order_id: orderId }, { headers: headers() });
      }

      if (generateQuote) {
        await axios.post(`${API}/orders/${orderId}/generate-quote`, {}, { headers: headers() });
        toast.success('Order created with quote!');
      } else {
        toast.success('Order saved as intake!');
      }

      navigate(`/orders/${orderId}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create order');
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6 max-w-4xl" data-testid="new-order-form">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate('/orders')}><ArrowLeft className="w-5 h-5 text-gray-500" /></Button>
        <h1 className="text-2xl font-bold text-white font-heading">New Order</h1>
      </div>

      {/* Customer Info */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg">Customer Information</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {customers.length > 0 && (
            <div>
              <Label className="text-gray-700">Select Existing Customer</Label>
              <Select onValueChange={selectCustomer}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue placeholder="Or type new customer below" /></SelectTrigger>
                <SelectContent>
                  {customers.map(c => <SelectItem key={c.id} value={c.id}>{c.name}{c.company ? ` (${c.company})` : ''}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-gray-700">Customer Name *</Label><Input value={order.customer_name} onChange={e => updateOrder('customer_name', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" data-testid="order-customer-name" /></div>
            <div><Label className="text-gray-700">Company</Label><Input value={order.company_name} onChange={e => updateOrder('company_name', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
            <div><Label className="text-gray-700">Phone</Label><Input value={order.phone} onChange={e => updateOrder('phone', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
            <div><Label className="text-gray-700">Email</Label><Input value={order.email} onChange={e => updateOrder('email', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><Label className="text-gray-700">Source</Label>
              <Select value={order.order_source} onValueChange={v => updateOrder('order_source', v)}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                <SelectContent>{SOURCES.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div><Label className="text-gray-700">Due Date</Label><Input type="date" value={order.requested_due_date} onChange={e => updateOrder('requested_due_date', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
            <div><Label className="text-gray-700">Pickup / Delivery</Label>
              <Select value={order.pickup_delivery_method} onValueChange={v => updateOrder('pickup_delivery_method', v)}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="pickup">Pickup</SelectItem>
                  <SelectItem value="delivery">Delivery</SelectItem>
                  <SelectItem value="install">Install</SelectItem>
                  <SelectItem value="ship">Ship</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label className="text-gray-700">Internal Notes</Label><Textarea value={order.internal_notes} onChange={e => updateOrder('internal_notes', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" rows={2} /></div>
        </CardContent>
      </Card>

      {/* Job Tickets */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Job Tickets ({tickets.length})</h2>
        <Button variant="outline" size="sm" onClick={addTicket} className="gap-2"><Plus className="w-4 h-4" /> Add Ticket</Button>
      </div>

      {tickets.map((ticket, i) => (
        <Card key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid={`ticket-form-${i}`}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-gray-900 text-base">Ticket {i + 1}</CardTitle>
              {tickets.length > 1 && <Button variant="ghost" size="icon" onClick={() => removeTicket(i)}><Trash2 className="w-4 h-4 text-red-400" /></Button>}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2"><Label className="text-gray-700">Item Name *</Label><Input value={ticket.item_name} onChange={e => updateTicket(i, 'item_name', e.target.value)} placeholder="e.g. Race Banner 3x8" className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              <div><Label className="text-gray-700">Category</Label>
                <Select value={ticket.item_category} onValueChange={v => updateTicket(i, 'item_category', v)}>
                  <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                  <SelectContent>{CATEGORIES.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div><Label className="text-gray-700">Qty</Label><Input type="number" min={1} value={ticket.quantity} onChange={e => updateTicket(i, 'quantity', parseInt(e.target.value) || 1)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
                <div><Label className="text-gray-700">Priority</Label>
                  <Select value={ticket.priority} onValueChange={v => updateTicket(i, 'priority', v)}>
                    <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                      <SelectItem value="rush">Rush</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label className="text-gray-700">Price Est.</Label><Input type="number" min={0} step={0.01} value={ticket.estimated_price} onChange={e => updateTicket(i, 'estimated_price', parseFloat(e.target.value) || 0)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              </div>
            </div>
            {/* Dynamic category-specific fields */}
            <DynamicCategoryFields
              category={ticket.item_category}
              specs={ticket.specs}
              onChange={(newSpecs) => updateTicket(i, 'specs', newSpecs)}
              mode="edit"
            />
            <div><Label className="text-gray-700">Special Instructions</Label><Textarea value={ticket.special_instructions} onChange={e => updateTicket(i, 'special_instructions', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" rows={2} /></div>
            <div className="flex items-center gap-6 pt-1">
              <div className="flex items-center gap-2"><Switch checked={ticket.production_flow_enabled} onCheckedChange={v => updateTicket(i, 'production_flow_enabled', v)} /><Label className="text-gray-700 text-sm">Enable Production Workflow</Label></div>
              <div className="flex items-center gap-2"><Switch checked={ticket.design_needed} onCheckedChange={v => updateTicket(i, 'design_needed', v)} /><Label className="text-gray-700 text-sm">Design Needed</Label></div>
              <div className="flex items-center gap-2"><Switch checked={ticket.proof_required} onCheckedChange={v => updateTicket(i, 'proof_required', v)} /><Label className="text-gray-700 text-sm">Proof Required</Label></div>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-2">
        <Button onClick={() => handleSave(false)} disabled={saving} className="bg-gray-200 hover:bg-slate-600 text-gray-900 flex-1" data-testid="save-intake-btn">
          {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null} Save as Intake Only
        </Button>
        <Button onClick={() => handleSave(true)} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white flex-1" data-testid="save-generate-quote-btn">
          {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null} Save + Generate Quote
        </Button>
      </div>
    </div>
  );
}
