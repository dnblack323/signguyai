import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Plus, Loader2, Trash2, Search, UserPlus, Upload, FileUp, Pen, Truck, Calculator, BarChart3, Save } from 'lucide-react';
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
import LivePricingPreview from '../components/LivePricingPreview';
import DrawingModal from './DrawingModal';
import { OrderCommandBar } from '../components/orders/OrderCommandBar';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const token = () => getAuthToken();
const hdrs = () => ({ Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' });

const CATEGORIES = [
  { value: '', label: 'Select Category...' },
  { value: 'banners', label: 'Banners' },
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'cut_vinyl', label: 'Cut Vinyl / Lettering' },
  { value: 'digital_print', label: 'Digital Print' },
  { value: 'vehicle_wrap', label: 'Vehicle Wrap' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'services', label: 'Services' },
  { value: 'promo_misc', label: 'Promotional / Misc' },
  { value: 'custom', label: 'Custom' },
];

const SOURCES = [
  { value: 'phone', label: 'Phone' }, { value: 'walk_in', label: 'Walk-in' },
  { value: 'email', label: 'Email' }, { value: 'website', label: 'Website' },
  { value: 'repeat_order', label: 'Repeat Order' }, { value: 'sales_rep', label: 'Sales Rep' },
];

const getDerivedQuantity = (category, specs, quantity) => {
  if (category === 'apparel') {
    const sizeKeys = ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl'];
    const total = sizeKeys.reduce((sum, key) => sum + (parseInt(specs?.[key]) || 0), 0);
    if (total > 0) return total;
  }
  return quantity || 1;
};

const createLocalTicket = (mode = 'quick') => ({
  local_id: `ticket_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  item_name: '', item_category: '', quantity: 1, priority: 'normal',
  production_flow_enabled: false, design_needed: false, proof_required: false,
  estimated_price: 0, special_instructions: '', entry_mode: mode, specs: {},
});
const createOrderSketch = (imageData, label, type) => ({
  local_id: `sketch_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  image_data: imageData,
  label,
  type,
});

const createOrderFile = (file) => ({
  local_id: `file_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  file,
});

export default function NewOrderForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const today = new Date().toISOString().split('T')[0];
  const [saving, setSaving] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [customerSearch, setCustomerSearch] = useState(searchParams.get('customer_name') || '');
  const [showCustomerResults, setShowCustomerResults] = useState(false);

  const [order, setOrder] = useState({
    customer_name: searchParams.get('customer_name') || '',
    contact_name: searchParams.get('customer_name') || '',
    phone: searchParams.get('phone') || '',
    email: searchParams.get('email') || '',
    company_name: searchParams.get('company') || '',
    customer_id: searchParams.get('customer_id') || '',
    order_source: 'phone', date_created: today, requested_due_date: '',
    pickup_delivery_method: 'pickup', pickup_delivery_notes: '',
    internal_notes: '', customer_notes: '',
  });

  // Start with NO tickets — user adds them
  const [tickets, setTickets] = useState([]);
  const [orderFiles, setOrderFiles] = useState([]);
  const [showSketchModal, setShowSketchModal] = useState(false);
  const [orderSketches, setOrderSketches] = useState([]);

  useEffect(() => {
    axios.get(`${API}/customers?limit=200`, { headers: hdrs() })
      .then(r => setCustomers(r.data?.customers || r.data || []))
      .catch(() => {});
  }, []);

  const filteredCustomers = useMemo(() => {
    if (!customerSearch.trim()) return [];
    const q = customerSearch.toLowerCase();
    return customers.filter(c =>
      (c.name || '').toLowerCase().includes(q) ||
      (c.company || '').toLowerCase().includes(q) ||
      (c.email || '').toLowerCase().includes(q) ||
      (c.phone || '').includes(q)
    ).slice(0, 8);
  }, [customerSearch, customers]);
  const totalEstimate = useMemo(() => tickets.reduce((sum, ticket) => sum + Number(ticket.estimated_price || 0), 0), [tickets]);
  const detailedTicketCount = useMemo(() => tickets.filter((ticket) => ticket.entry_mode === 'detailed').length, [tickets]);

  const updateOrder = (field, value) => setOrder(prev => ({ ...prev, [field]: value }));
  const updateTicket = (ticketId, field, value) => setTickets(prev => prev.map((ticket) => ticket.local_id === ticketId ? { ...ticket, [field]: value } : ticket));

  const addTicket = (mode = 'quick') => setTickets(prev => [...prev, createLocalTicket(mode)]);
  const removeTicket = (ticketId) => setTickets(prev => prev.filter((ticket) => ticket.local_id !== ticketId));
  const toggleEntryMode = (ticketId) => setTickets(prev => prev.map((ticket) => ticket.local_id === ticketId ? { ...ticket, entry_mode: ticket.entry_mode === 'quick' ? 'detailed' : 'quick' } : ticket));

  const selectCustomer = (c) => {
    setOrder(prev => ({
      ...prev, customer_id: c.id, customer_name: c.name || '',
      contact_name: c.name || '', phone: c.phone || '',
      email: c.email || '', company_name: c.company || '',
    }));
    setCustomerSearch(c.name || c.company || '');
    setShowCustomerResults(false);
  };

  const handleSave = async (saveAsDraft = false) => {
    if (!order.customer_name.trim()) { toast.error('Customer name is required'); return; }
    setSaving(true);
    try {
      const orderPayload = { ...order };
      if (saveAsDraft) orderPayload.status = 'draft';

      const orderRes = await axios.post(`${API}/orders`, orderPayload, { headers: hdrs() });
      const orderId = orderRes.data.id;

      const createdTicketIds = [];
      for (const t of tickets) {
        if (!t.item_name.trim()) continue;
        try {
          const ticketRes = await axios.post(`${API}/job-tickets`, {
            order_id: orderId,
            item_name: t.item_name,
            item_category: t.item_category || 'custom',
            quantity: t.quantity || 1,
            due_date: t.due_date || order.requested_due_date || null,
            priority: t.priority || 'normal',
            production_flow_enabled: t.production_flow_enabled || false,
            design_needed: t.design_needed || false,
            proof_required: t.proof_required || false,
            estimated_price: t.estimated_price || 0,
            special_instructions: t.special_instructions || '',
            specs: t.specs || {},
          }, { headers: hdrs() });
          createdTicketIds.push(ticketRes.data.id);
        } catch (ticketErr) {
          console.error('Ticket creation error:', ticketErr);
          toast.error(`Failed to create ticket: ${t.item_name}`);
        }
      }

      if (createdTicketIds.length > 0 && window.confirm('Do you want to send these items to production now?')) {
        for (const ticketId of createdTicketIds) {
          await axios.put(`${API}/job-tickets/${ticketId}`, { production_flow_enabled: true }, { headers: hdrs() });
        }
        await axios.post(`${API}/orders/${orderId}/start-production`, {}, { headers: hdrs() });
      }

      // Upload files
      for (const f of orderFiles) {
        const formData = new FormData();
        formData.append('file', f.file);
        formData.append('label', f.file.name);
        await axios.post(`${API}/orders/${orderId}/upload`, formData, {
          headers: { Authorization: `Bearer ${token()}` },
        });
      }

      // Upload sketches as drawings
      for (const sketch of orderSketches) {
        try {
          await axios.post(`${API}/order-drawings/`, {
            order_id: orderId,
            type: sketch.type || 'sketch',
            label: sketch.label || 'Order Sketch',
            image_data: sketch.image_data,
          }, { headers: hdrs() });
        } catch { console.error('Sketch upload failed'); }
      }

      toast.success(saveAsDraft ? 'Order saved as draft!' : 'Order saved!');
      navigate(`/orders/${orderId}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create order');
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-6" data-testid="new-order-form">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate('/orders')}><ArrowLeft className="w-5 h-5 text-gray-400" /></Button>
        <h1 className="text-2xl font-bold text-white font-heading">New Order</h1>
      </div>

      <OrderCommandBar
        onOpenPricingAnalysis={() => navigate('/pricing-setup')}
        onOpenPricingCalculator={() => navigate('/pricing-calculator')}
        onOpenSketch={() => setShowSketchModal(true)}
        onAddTicket={() => addTicket('detailed')}
        onSave={() => handleSave(false)}
        testId="new-order-command-bar"
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
      <div className="space-y-6">

      {/* Customer Info */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg">Customer</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {/* Type-ahead customer search */}
          <div className="relative">
            <Label className="text-gray-700">Search Customer</Label>
            <div className="relative mt-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={customerSearch}
                onChange={e => { setCustomerSearch(e.target.value); setShowCustomerResults(true); updateOrder('customer_name', e.target.value); }}
                onFocus={() => setShowCustomerResults(true)}
                placeholder="Start typing customer name, company, email, or phone..."
                className="pl-10 bg-gray-50 border-gray-300 text-gray-900"
                data-testid="customer-search"
              />
            </div>
            {showCustomerResults && customerSearch.trim() && (
              <div className="absolute z-20 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {filteredCustomers.length > 0 ? filteredCustomers.map(c => (
                  <button key={c.id} onClick={() => selectCustomer(c)} className="w-full text-left px-4 py-2.5 hover:bg-violet-50 flex items-center justify-between border-b border-gray-100 last:border-0" data-testid={`customer-result-${c.id}`}>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{c.name}</p>
                      <p className="text-xs text-gray-500">{c.company}{c.email ? ` | ${c.email}` : ''}</p>
                    </div>
                  </button>
                )) : (
                  <div className="px-4 py-3 text-center">
                    <p className="text-sm text-gray-500">No customers found</p>
                    <button onClick={() => { updateOrder('customer_name', customerSearch); setShowCustomerResults(false); }} className="text-xs text-violet-600 hover:underline mt-1 flex items-center gap-1 mx-auto">
                      <UserPlus className="w-3 h-3" /> Use as new customer
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div><Label className="text-gray-700">Customer Name *</Label><Input value={order.customer_name} onChange={e => updateOrder('customer_name', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" data-testid="order-customer-name" /></div>
            <div><Label className="text-gray-700">Company</Label><Input value={order.company_name} onChange={e => updateOrder('company_name', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
            <div><Label className="text-gray-700">Phone</Label><Input value={order.phone} onChange={e => updateOrder('phone', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
            <div><Label className="text-gray-700">Email</Label><Input value={order.email} onChange={e => updateOrder('email', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
          </div>
        </CardContent>
      </Card>

      {/* Order Information */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg">Order Information</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div><Label className="text-gray-700">Source</Label>
              <Select value={order.order_source} onValueChange={v => updateOrder('order_source', v)}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                <SelectContent>{SOURCES.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div><Label className="text-gray-700">Today's Date</Label><Input type="date" value={order.date_created} onChange={e => updateOrder('date_created', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" data-testid="order-date-created" /></div>
            <div><Label className="text-gray-700">Due Date</Label><Input type="date" value={order.requested_due_date} onChange={e => updateOrder('requested_due_date', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" data-testid="order-due-date" /></div>
          </div>
          <div><Label className="text-gray-700">Internal Notes</Label><Textarea value={order.internal_notes} onChange={e => updateOrder('internal_notes', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" rows={2} placeholder="Internal notes about this order..." /></div>
        </CardContent>
      </Card>

      {/* Order Items Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Order Items ({tickets.length})</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => addTicket('quick')} className="gap-2 bg-white" data-testid="add-quick-ticket"><Plus className="w-4 h-4" /> Quick Entry</Button>
          <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-white gap-2" onClick={() => addTicket('detailed')} data-testid="add-detailed-ticket"><Plus className="w-4 h-4" /> Detailed Entry</Button>
        </div>
      </div>

      {/* Empty state */}
      {tickets.length === 0 && (
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">No order items yet. Add your first item to get started.</p>
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => addTicket('quick')} className="gap-2"><Plus className="w-4 h-4" /> Quick Entry</Button>
              <Button className="bg-violet-600 hover:bg-violet-700 text-white gap-2" onClick={() => addTicket('detailed')}><Plus className="w-4 h-4" /> Detailed Entry</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ticket Forms */}
      {tickets.map((ticket, i) => (
        <Card key={ticket.local_id} className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid={`ticket-form-${i}`}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CardTitle className="text-gray-900 text-base">Item {i + 1}</CardTitle>
                <button onClick={() => toggleEntryMode(ticket.local_id)} className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${ticket.entry_mode === 'detailed' ? 'bg-violet-50 text-violet-600 border-violet-300' : 'bg-gray-100 text-gray-500 border-gray-300'}`}>
                  {ticket.entry_mode === 'detailed' ? 'Detailed' : 'Quick'}
                </button>
              </div>
              <Button variant="ghost" size="icon" onClick={() => removeTicket(ticket.local_id)}><Trash2 className="w-4 h-4 text-red-400" /></Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Common fields */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="col-span-2"><Label className="text-gray-700">Item Name *</Label><Input value={ticket.item_name} onChange={e => updateTicket(ticket.local_id, 'item_name', e.target.value)} placeholder="e.g. Race Banner 3x8" className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              <div><Label className="text-gray-700">Category</Label>
                <Select value={ticket.item_category} onValueChange={v => updateTicket(ticket.local_id, 'item_category', v)}>
                  <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue placeholder="Select Category..." /></SelectTrigger>
                  <SelectContent>{CATEGORIES.filter(c => c.value).map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div><Label className="text-gray-700">Qty</Label><Input type="number" min={1} value={ticket.quantity} onChange={e => updateTicket(ticket.local_id, 'quantity', parseInt(e.target.value) || 1)} className="bg-gray-50 border-gray-300 text-gray-900" /></div>
                <div><Label className="text-gray-700">Priority</Label>
                  <Select value={ticket.priority} onValueChange={v => updateTicket(ticket.local_id, 'priority', v)}>
                    <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                      <SelectItem value="rush">Rush</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div><Label className="text-gray-700">Price</Label><Input type="number" min={0} step={0.01} value={ticket.estimated_price > 0 ? ticket.estimated_price : ''} onChange={e => updateTicket(ticket.local_id, 'estimated_price', parseFloat(e.target.value) || 0)} placeholder="0.00" className="bg-gray-50 border-gray-300 text-gray-900" /></div>
              </div>
            </div>

            {/* QUICK MODE */}
            {ticket.entry_mode !== 'detailed' && (
              <div className="space-y-3">
                <div><Label className="text-gray-700">Description / Notes</Label><Textarea value={ticket.special_instructions} onChange={e => updateTicket(ticket.local_id, 'special_instructions', e.target.value)} placeholder="Describe the item, materials, specs..." className="bg-gray-50 border-gray-300 text-gray-900" rows={3} /></div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2"><Switch checked={ticket.design_needed} onCheckedChange={v => updateTicket(ticket.local_id, 'design_needed', v)} /><Label className="text-gray-700 text-sm">Design Needed</Label></div>
                  <div className="flex items-center gap-2"><Switch checked={ticket.proof_required} onCheckedChange={v => updateTicket(ticket.local_id, 'proof_required', v)} /><Label className="text-gray-700 text-sm">Proof Required</Label></div>
                  <div className="flex items-center gap-2"><Switch checked={ticket.production_flow_enabled} onCheckedChange={v => updateTicket(ticket.local_id, 'production_flow_enabled', v)} /><Label className="text-gray-700 text-sm">Workflow</Label></div>
                </div>
                <button onClick={() => toggleEntryMode(ticket.local_id)} className="text-xs text-violet-600 hover:text-violet-700 underline">Switch to Detailed Entry for full specs + calculator</button>
              </div>
            )}

            {/* DETAILED MODE — only show dynamic fields if category is selected */}
            {ticket.entry_mode === 'detailed' && (
              <div className="space-y-3">
                {ticket.item_category ? (
                  <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
                    <div className="space-y-3">
                      <DynamicCategoryFields
                        category={ticket.item_category}
                        specs={ticket.specs}
                        onChange={(newSpecs) => setTickets(prev => prev.map((currentTicket) => currentTicket.local_id === ticket.local_id ? {
                          ...currentTicket,
                          specs: newSpecs,
                          quantity: getDerivedQuantity(currentTicket.item_category, newSpecs, currentTicket.quantity),
                        } : currentTicket))}
                        mode="edit"
                      />
                      <div><Label className="text-gray-700">Special Instructions</Label><Textarea value={ticket.special_instructions} onChange={e => updateTicket(ticket.local_id, 'special_instructions', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" rows={2} /></div>
                    </div>
                    <div className="space-y-3 lg:sticky lg:top-24" data-testid={`ticket-live-estimate-panel-${ticket.local_id}`}>
                      <LivePricingPreview
                        category={ticket.item_category}
                        specs={ticket.specs}
                        quantity={ticket.quantity}
                        onPriceChange={(price) => setTickets(prev => prev.map((currentTicket) => currentTicket.local_id === ticket.local_id ? {
                          ...currentTicket,
                          estimated_price: price,
                          quantity: getDerivedQuantity(currentTicket.item_category, currentTicket.specs, currentTicket.quantity),
                        } : currentTicket))}
                      />
                      <div className="grid gap-2 sm:grid-cols-2">
                        <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-setup')} data-testid={`ticket-pricing-analysis-link-${ticket.local_id}`}>
                          <BarChart3 className="mr-2 h-4 w-4" /> Pricing Analysis
                        </Button>
                        <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-calculator')} data-testid={`ticket-pricing-calculator-link-${ticket.local_id}`}>
                          <Calculator className="mr-2 h-4 w-4" /> Calculator
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-6 text-center text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                    Select a category above to see category-specific fields
                  </div>
                )}
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2"><Switch checked={ticket.production_flow_enabled} onCheckedChange={v => updateTicket(ticket.local_id, 'production_flow_enabled', v)} /><Label className="text-gray-700 text-sm">Production Workflow</Label></div>
                </div>
                <button onClick={() => toggleEntryMode(ticket.local_id)} className="text-xs text-gray-500 hover:text-gray-700 underline">Switch to Quick Entry</button>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* Add more tickets + Save */}
      {tickets.length > 0 && (
        <div className="flex gap-2 justify-center">
          <Button variant="outline" size="sm" onClick={() => addTicket('quick')} className="gap-2 bg-white"><Plus className="w-4 h-4" /> Quick Entry</Button>
          <Button variant="outline" size="sm" className="bg-violet-50 text-violet-700 border-violet-300 gap-2" onClick={() => addTicket('detailed')}><Plus className="w-4 h-4" /> Detailed Entry</Button>
        </div>
      )}

      {/* Sketches / Drawing Pad */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-gray-900 text-lg flex items-center gap-2"><Pen className="w-5 h-5 text-violet-500" /> Sketches & Notes</CardTitle>
            <Button size="sm" variant="outline" className="gap-1 text-violet-600 border-violet-300 hover:bg-violet-50" onClick={() => setShowSketchModal(true)} data-testid="add-sketch-btn">
              <Pen className="w-4 h-4" /> Add Sketch
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {orderSketches.length === 0 ? (
            <div className="text-center py-6 text-gray-400 bg-gray-50 rounded-lg border border-dashed border-gray-300">
              <Pen className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No sketches yet. Use the drawing pad to capture quick notes or layouts.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {orderSketches.map((s) => (
                <div key={s.local_id} className="border border-gray-200 rounded-lg overflow-hidden group relative">
                  <div className="aspect-[4/3] bg-gray-50">
                    <img src={s.image_data} alt={s.label} className="w-full h-full object-contain" />
                  </div>
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-xs text-gray-700 truncate">{s.label || 'Sketch'}</span>
                    <button onClick={() => setOrderSketches(prev => prev.filter((sketch) => sketch.local_id !== s.local_id))} className="text-red-400 hover:text-red-600"><Trash2 className="w-3 h-3" /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pickup / Delivery */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg flex items-center gap-2"><Truck className="w-5 h-5 text-blue-500" /> Pickup / Delivery</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div><Label className="text-gray-700">Method</Label>
              <Select value={order.pickup_delivery_method} onValueChange={v => updateOrder('pickup_delivery_method', v)}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900" data-testid="pickup-delivery-method"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="pickup">Pickup</SelectItem>
                  <SelectItem value="delivery">Delivery</SelectItem>
                  <SelectItem value="install">Install</SelectItem>
                  <SelectItem value="ship">Ship</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div><Label className="text-gray-700">Delivery / Pickup Notes</Label><Textarea value={order.pickup_delivery_notes} onChange={e => updateOrder('pickup_delivery_notes', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900" rows={2} placeholder="Address, delivery instructions, or pickup details..." /></div>
        </CardContent>
      </Card>

      {/* Attachments */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader><CardTitle className="text-gray-900 text-lg flex items-center gap-2"><Upload className="w-5 h-5 text-emerald-500" /> Attachments / Artwork</CardTitle></CardHeader>
        <CardContent>
          <input
            type="file"
            multiple
            onChange={(e) => {
              const newFiles = Array.from(e.target.files || []).map(createOrderFile);
              setOrderFiles(prev => [...prev, ...newFiles]);
              e.target.value = '';
            }}
            className="hidden"
            id="order-file-input"
            data-testid="order-file-input"
          />
          <label htmlFor="order-file-input" className="block border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-violet-400 transition-colors cursor-pointer bg-gray-50">
            <Upload className="w-6 h-6 mx-auto text-gray-400 mb-1" />
            <p className="text-sm text-gray-500">Click to upload artwork, drawings, photos, or notes</p>
          </label>
          {orderFiles.length > 0 && (
            <div className="mt-2 space-y-1">
              {orderFiles.map((f) => (
                <div key={f.local_id} className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded px-3 py-1.5 text-sm">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileUp className="w-4 h-4 text-violet-500 flex-shrink-0" />
                    <span className="text-gray-700 truncate">{f.file.name}</span>
                    <span className="text-gray-400 text-xs flex-shrink-0">({(f.file.size / 1024).toFixed(0)} KB)</span>
                  </div>
                  <button onClick={() => setOrderFiles(prev => prev.filter((file) => file.local_id !== f.local_id))} className="text-red-400 hover:text-red-600 ml-2"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Save Buttons */}
      <div className="grid gap-3 pt-2 md:grid-cols-3" data-testid="new-order-bottom-actions">
        <Button variant="outline" onClick={() => addTicket('detailed')} disabled={saving} className="py-6 text-base bg-white text-gray-700 hover:bg-gray-50" data-testid="bottom-add-another-ticket-btn">
          <Plus className="w-4 h-4 mr-2" /> Add Another Item
        </Button>
        <Button variant="outline" onClick={() => handleSave(true)} disabled={saving} className="flex-1 py-6 text-lg bg-white text-gray-700 hover:bg-gray-50" data-testid="save-draft-btn">
          Save as Draft
        </Button>
        <Button onClick={() => handleSave(false)} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white flex-1 py-6 text-lg" data-testid="save-order-btn">
          {saving ? <Loader2 className="w-5 h-5 animate-spin mr-2" /> : <Save className="w-5 h-5 mr-2" />} Save Order
        </Button>
      </div>

      </div>

      <aside className="space-y-4 xl:sticky xl:top-24" data-testid="new-order-summary-sidebar">
        <Card className="bg-white rounded-2xl border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-gray-900 text-lg">Live Estimate</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">Order total</p>
              <p className="mt-2 text-3xl font-bold text-violet-700" data-testid="new-order-live-estimate-value">${totalEstimate.toFixed(2)}</p>
              <p className="mt-2 text-sm text-gray-600">{tickets.length} item{tickets.length !== 1 ? 's' : ''} · {detailedTicketCount} detailed</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-slate-50 p-4 text-sm text-gray-700">
              <p className="font-semibold text-gray-900">Quick links</p>
              <div className="mt-3 grid gap-2">
                <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-setup')} data-testid="new-order-pricing-analysis-link">
                  <BarChart3 className="mr-2 h-4 w-4" /> Pricing Analysis
                </Button>
                <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-calculator')} data-testid="new-order-pricing-calculator-link">
                  <Calculator className="mr-2 h-4 w-4" /> Pricing Calculator
                </Button>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              <Button type="button" onClick={() => addTicket('detailed')} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="new-order-add-ticket-sidebar-button">
                <Plus className="mr-2 h-4 w-4" /> Add Another Item
              </Button>
              <Button type="button" variant="outline" onClick={() => handleSave(true)} disabled={saving} data-testid="new-order-save-draft-sidebar-button">
                Save Draft
              </Button>
              <Button type="button" variant="outline" onClick={() => handleSave(false)} disabled={saving} data-testid="new-order-save-order-sidebar-button">
                <Save className="mr-2 h-4 w-4" /> Save Order
              </Button>
            </div>
          </CardContent>
        </Card>
      </aside>
      </div>

      {/* Sketch Drawing Modal */}
      {showSketchModal && (
        <DrawingModal
          orderId={null}
          onClose={() => setShowSketchModal(false)}
          onSaved={(imageData, label, type) => {
            // For new order, we capture the sketch locally until order is saved
          }}
          onLocalSave={(imageData, label, type) => {
            setOrderSketches(prev => [...prev, createOrderSketch(imageData, label, type)]);
            setShowSketchModal(false);
          }}
        />
      )}
    </div>
  );
}
