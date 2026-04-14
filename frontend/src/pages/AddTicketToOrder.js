import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Plus, Loader2, Trash2, Calculator, BarChart3, Save } from 'lucide-react';
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
import { getAuthToken } from '../lib/authStorage';
import { OrderCommandBar } from '../components/orders/OrderCommandBar';

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

const getDerivedQuantity = (category, specs, quantity) => {
  if (category === 'apparel') {
    const sizeKeys = ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl'];
    const total = sizeKeys.reduce((sum, key) => sum + (parseInt(specs?.[key]) || 0), 0);
    if (total > 0) return total;
  }
  return quantity || 1;
};

export default function AddTicketToOrder() {
  const navigate = useNavigate();
  const { id: orderId } = useParams();
  const [saving, setSaving] = useState(false);
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [entryMode, setEntryMode] = useState('quick');

  const [ticket, setTicket] = useState({
    item_name: '', item_category: '', quantity: 1, priority: 'normal',
    production_flow_enabled: false, design_needed: false, proof_required: false,
    estimated_price: 0, special_instructions: '', specs: {},
  });

  // Load existing order info
  useEffect(() => {
    const loadOrder = async () => {
      try {
        const res = await axios.get(`${API}/orders/${orderId}`, { headers: hdrs() });
        setOrder(res.data);
      } catch (err) {
        toast.error('Failed to load order');
        navigate('/orders');
      } finally {
        setLoading(false);
      }
    };
    loadOrder();
  }, [orderId, navigate]);

  const updateTicket = (field, value) => setTicket(prev => ({ ...prev, [field]: value }));
  const estimatedTicketValue = Number(ticket.estimated_price || 0);

  const resetTicketForm = () => {
    setTicket({
      item_name: '', item_category: '', quantity: 1, priority: 'normal',
      production_flow_enabled: false, design_needed: false, proof_required: false,
      estimated_price: 0, special_instructions: '', specs: {},
    });
    setEntryMode('quick');
  };

  const handleSave = async (mode = 'return') => {
    if (!ticket.item_name.trim()) { 
      toast.error('Item name is required'); 
      return; 
    }
    setSaving(true);
    try {
      const created = await axios.post(`${API}/job-tickets`, {
        order_id: orderId,
        item_name: ticket.item_name,
        item_category: ticket.item_category || 'custom',
        quantity: ticket.quantity || 1,
        due_date: ticket.due_date || order?.requested_due_date || null,
        priority: ticket.priority || 'normal',
        production_flow_enabled: ticket.production_flow_enabled || false,
        design_needed: ticket.design_needed || false,
        proof_required: ticket.proof_required || false,
        estimated_price: ticket.estimated_price || 0,
        special_instructions: ticket.special_instructions || '',
        specs: ticket.specs || {},
      }, { headers: hdrs() });

      if (window.confirm('Send this item to production now?')) {
        await axios.put(`${API}/job-tickets/${created.data.id}`, { production_flow_enabled: true }, { headers: hdrs() });
        await axios.post(`${API}/orders/${orderId}/start-production`, {}, { headers: hdrs() });
      }

      if (mode === 'return') {
        toast.success('Order item added and order updated');
        navigate(`/orders/${orderId}`);
        return;
      }

      toast.success(mode === 'another' ? 'Ticket added — ready for the next one' : 'Ticket added to the order');
      resetTicketForm();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create ticket');
    } finally { 
      setSaving(false); 
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="add-ticket-form">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/orders/${orderId}`)}>
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-white font-heading">Add Order Item</h1>
          {order && (
            <p className="text-slate-400 text-sm">
              {order.order_number} — {order.customer_name}
              {order.company_name ? ` (${order.company_name})` : ''}
            </p>
          )}
        </div>
      </div>

      {/* Order Summary Card */}
      {order && (
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-500 text-xs uppercase">Customer</p>
                <p className="text-gray-900 font-medium">{order.customer_name}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs uppercase">Company</p>
                <p className="text-gray-900">{order.company_name || '-'}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs uppercase">Due Date</p>
                <p className="text-gray-900">{order.requested_due_date ? new Date(order.requested_due_date).toLocaleDateString() : '-'}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs uppercase">Existing Items</p>
                <p className="text-gray-900">{order.job_tickets?.length || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <OrderCommandBar
        onOpenPricingAnalysis={() => navigate('/pricing-setup')}
        onOpenPricingCalculator={() => navigate('/pricing-calculator')}
        onAddTicket={() => resetTicketForm()}
        onSave={() => handleSave('return')}
        testId="add-ticket-command-bar"
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px] xl:items-start">
      {/* Ticket Form */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid="ticket-form">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-gray-900 text-lg">New Order Item</CardTitle>
            <button 
              onClick={() => setEntryMode(entryMode === 'quick' ? 'detailed' : 'quick')} 
              className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${entryMode === 'detailed' ? 'bg-violet-50 text-violet-600 border-violet-300' : 'bg-gray-100 text-gray-500 border-gray-300'}`}
            >
              {entryMode === 'detailed' ? 'Detailed' : 'Quick'}
            </button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Common fields */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="col-span-2">
              <Label className="text-gray-700">Item Name *</Label>
              <Input 
                value={ticket.item_name} 
                onChange={e => updateTicket('item_name', e.target.value)} 
                placeholder="e.g. Race Banner 3x8" 
                className="bg-gray-50 border-gray-300 text-gray-900" 
                data-testid="ticket-item-name"
              />
            </div>
            <div>
              <Label className="text-gray-700">Category</Label>
              <Select value={ticket.item_category} onValueChange={v => updateTicket('item_category', v)}>
                <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900">
                  <SelectValue placeholder="Select Category..." />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.filter(c => c.value).map(c => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <Label className="text-gray-700">Qty</Label>
                <Input 
                  type="number" 
                  min={1} 
                  value={ticket.quantity} 
                  onChange={e => updateTicket('quantity', parseInt(e.target.value) || 1)} 
                  className="bg-gray-50 border-gray-300 text-gray-900" 
                />
              </div>
              <div>
                <Label className="text-gray-700">Priority</Label>
                <Select value={ticket.priority} onValueChange={v => updateTicket('priority', v)}>
                  <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="rush">Rush</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-gray-700">Price</Label>
                <Input 
                  type="number" 
                  min={0} 
                  step={0.01} 
                  value={ticket.estimated_price > 0 ? ticket.estimated_price : ''} 
                  onChange={e => updateTicket('estimated_price', parseFloat(e.target.value) || 0)} 
                  placeholder="0.00" 
                  className="bg-gray-50 border-gray-300 text-gray-900" 
                />
              </div>
            </div>
          </div>

          {/* QUICK MODE */}
          {entryMode !== 'detailed' && (
            <div className="space-y-3">
              <div>
                <Label className="text-gray-700">Description / Notes</Label>
                <Textarea 
                  value={ticket.special_instructions} 
                  onChange={e => updateTicket('special_instructions', e.target.value)} 
                  placeholder="Describe the item, materials, specs..." 
                  className="bg-gray-50 border-gray-300 text-gray-900" 
                  rows={3} 
                />
              </div>
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Switch checked={ticket.design_needed} onCheckedChange={v => updateTicket('design_needed', v)} />
                  <Label className="text-gray-700 text-sm">Design Needed</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={ticket.proof_required} onCheckedChange={v => updateTicket('proof_required', v)} />
                  <Label className="text-gray-700 text-sm">Proof Required</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={ticket.production_flow_enabled} onCheckedChange={v => updateTicket('production_flow_enabled', v)} />
                  <Label className="text-gray-700 text-sm">Workflow</Label>
                </div>
              </div>
              <button 
                onClick={() => setEntryMode('detailed')} 
                className="text-xs text-violet-600 hover:text-violet-700 underline"
              >
                Switch to Detailed Entry for full specs + calculator
              </button>
            </div>
          )}

          {/* DETAILED MODE */}
          {entryMode === 'detailed' && (
            <div className="space-y-3">
              {ticket.item_category ? (
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
                  <div className="space-y-3">
                    <DynamicCategoryFields
                      category={ticket.item_category}
                      specs={ticket.specs}
                      onChange={(newSpecs) => setTicket((current) => ({
                        ...current,
                        specs: newSpecs,
                        quantity: getDerivedQuantity(current.item_category, newSpecs, current.quantity),
                      }))}
                      mode="edit"
                    />
                    <div>
                      <Label className="text-gray-700">Special Instructions</Label>
                      <Textarea 
                        value={ticket.special_instructions} 
                        onChange={e => updateTicket('special_instructions', e.target.value)} 
                        className="bg-gray-50 border-gray-300 text-gray-900" 
                        rows={2} 
                      />
                    </div>
                  </div>
                  <div className="space-y-3 lg:sticky lg:top-24" data-testid="add-ticket-live-estimate-panel">
                    <LivePricingPreview 
                      category={ticket.item_category} 
                      specs={ticket.specs} 
                      quantity={ticket.quantity}
                      onPriceChange={(price) => setTicket((current) => ({
                        ...current,
                        estimated_price: price,
                        quantity: getDerivedQuantity(current.item_category, current.specs, current.quantity),
                      }))}
                    />
                    <div className="grid gap-2 sm:grid-cols-2">
                      <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-setup')} data-testid="add-ticket-pricing-analysis-link">
                        <BarChart3 className="mr-2 h-4 w-4" /> Pricing Analysis
                      </Button>
                      <Button type="button" variant="outline" className="justify-start" onClick={() => navigate('/pricing-calculator')} data-testid="add-ticket-pricing-calculator-link">
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
                <div className="flex items-center gap-2">
                  <Switch checked={ticket.production_flow_enabled} onCheckedChange={v => updateTicket('production_flow_enabled', v)} />
                  <Label className="text-gray-700 text-sm">Production Workflow</Label>
                </div>
              </div>
              <button 
                onClick={() => setEntryMode('quick')} 
                className="text-xs text-gray-500 hover:text-gray-700 underline"
              >
                Switch to Quick Entry
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      <aside className="space-y-4 xl:sticky xl:top-24" data-testid="add-ticket-summary-sidebar">
        <Card className="bg-white rounded-2xl border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-gray-900 text-lg">Live Estimate</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-violet-100 bg-violet-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">Current ticket</p>
              <p className="mt-2 text-3xl font-bold text-violet-700" data-testid="add-ticket-live-estimate-value">${estimatedTicketValue.toFixed(2)}</p>
              <p className="mt-2 text-sm text-gray-600">{ticket.item_name || 'Unnamed item'} · Qty {ticket.quantity || 1}</p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              <Button type="button" onClick={() => handleSave('stay')} disabled={saving} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="add-ticket-to-order-button">
                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />} Add to Order
              </Button>
              <Button type="button" variant="outline" onClick={() => handleSave('another')} disabled={saving} data-testid="add-another-ticket-button">
                <Plus className="mr-2 h-4 w-4" /> Add Another Ticket
              </Button>
              <Button type="button" variant="outline" onClick={() => handleSave('return')} disabled={saving} data-testid="save-order-from-add-ticket-button">
                <Save className="mr-2 h-4 w-4" /> Save Order
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate(`/orders/${orderId}`)} data-testid="cancel-add-ticket-button">
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </aside>
      </div>
    </div>
  );
}
