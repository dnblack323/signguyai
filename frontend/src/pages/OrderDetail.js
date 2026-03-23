import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Package, FileText, Play, Clock, CheckCircle, AlertTriangle, Trash2, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const token = () => localStorage.getItem('auth_token');
const headers = () => ({ Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' });

const STATUS_COLORS = {
  new_intake: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  awaiting_review: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  in_production: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  partially_complete: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  ready_for_pickup: 'bg-green-500/15 text-green-400 border-green-500/30',
  completed: 'bg-green-600/15 text-green-300 border-green-600/30',
  on_hold: 'bg-red-500/15 text-red-400 border-red-500/30',
  cancelled: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  approved: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
  new: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  queued: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
  in_qc: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  ready: 'bg-green-500/15 text-green-400 border-green-500/30',
  rework: 'bg-red-500/15 text-red-400 border-red-500/30',
};

const CATEGORY_LABELS = {
  rigid_signs: 'Rigid Signs', banners: 'Banners', cut_vinyl: 'Cut Vinyl',
  vehicle_wrap: 'Vehicle Wrap', apparel: 'Apparel', promo_misc: 'Promo / Misc', custom: 'Custom',
};

const PRIORITY_COLORS = { rush: 'bg-red-500 text-white', urgent: 'bg-orange-500 text-white', high: 'bg-amber-500/80 text-black', normal: 'bg-slate-600 text-slate-200' };
const formatStatus = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [tab, setTab] = useState('tickets');

  const load = async () => {
    try {
      const [orderRes, actRes] = await Promise.all([
        axios.get(`${API}/orders/${id}`, { headers: headers() }),
        axios.get(`${API}/orders/${id}/activity`, { headers: headers() }),
      ]);
      setOrder(orderRes.data);
      setActivities(actRes.data);
    } catch { toast.error('Failed to load order'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [id]);

  const startProduction = async () => {
    setActionLoading('production');
    try {
      const res = await axios.post(`${API}/orders/${id}/start-production`, {}, { headers: headers() });
      toast.success(`Production started: ${res.data.tasks_created} tasks created`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setActionLoading(''); }
  };

  const generateQuote = async () => {
    setActionLoading('quote');
    try {
      const res = await axios.post(`${API}/orders/${id}/generate-quote`, {}, { headers: headers() });
      toast.success(`Quote generated: $${res.data.total?.toFixed(2)}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setActionLoading(''); }
  };

  const deleteOrder = async () => {
    if (!window.confirm('Delete this order and all related records?')) return;
    try {
      await axios.delete(`${API}/orders/${id}`, { headers: headers() });
      toast.success('Order deleted');
      navigate('/orders');
    } catch { toast.error('Failed to delete'); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500" /></div>;
  if (!order) return <div className="text-center py-20 text-slate-400">Order not found</div>;

  const tickets = order.job_tickets || [];
  const totalEstimate = tickets.reduce((sum, t) => sum + (t.estimated_price || 0), 0);

  return (
    <div className="space-y-5" data-testid="order-detail-page">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/orders')}><ArrowLeft className="w-5 h-5 text-slate-400" /></Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white font-heading">{order.order_number}</h1>
              <Badge variant="outline" className={STATUS_COLORS[order.status]}>{formatStatus(order.status)}</Badge>
            </div>
            <p className="text-slate-400 text-sm">{order.customer_name}{order.company_name ? ` — ${order.company_name}` : ''}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={generateQuote} disabled={!!actionLoading || tickets.length === 0} data-testid="generate-quote-btn">
            {actionLoading === 'quote' ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <FileText className="w-4 h-4 mr-1" />} Generate Quote
          </Button>
          <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-white" onClick={startProduction} disabled={!!actionLoading || tickets.filter(t => t.production_flow_enabled).length === 0} data-testid="start-production-btn">
            {actionLoading === 'production' ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Play className="w-4 h-4 mr-1" />} Start Production
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Tickets', value: tickets.length },
          { label: 'Estimate', value: `$${totalEstimate.toFixed(2)}` },
          { label: 'Progress', value: `${Math.round(order.overall_progress || 0)}%` },
          { label: 'Due', value: order.requested_due_date ? new Date(order.requested_due_date).toLocaleDateString() : '-' },
          { label: 'Payment', value: formatStatus(order.payment_status) },
        ].map(c => (
          <Card key={c.label} className="bg-[#111826] border-slate-700">
            <CardContent className="p-3 text-center">
              <p className="text-xs text-slate-500 uppercase">{c.label}</p>
              <p className="text-lg font-bold text-white mt-1">{c.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Progress Bar */}
      <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${order.overall_progress || 0}%` }} />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-700">
        {['tickets', 'activity'].map(t => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${tab === t ? 'text-violet-400 border-violet-400' : 'text-slate-500 border-transparent hover:text-slate-300'}`}>
            {t === 'tickets' ? `Job Tickets (${tickets.length})` : `Activity (${activities.length})`}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'tickets' && (
        <div className="space-y-3">
          <Button variant="outline" size="sm" onClick={() => navigate(`/orders/${id}/add-ticket`)} className="gap-2" data-testid="add-ticket-btn">
            <Plus className="w-4 h-4" /> Add Job Ticket
          </Button>
          {tickets.length === 0 ? (
            <Card className="bg-[#111826] border-slate-700"><CardContent className="py-12 text-center text-slate-500">No job tickets yet. Add one to get started.</CardContent></Card>
          ) : (
            tickets.map(ticket => (
              <Card key={ticket.id} className="bg-[#111826] border-slate-700 hover:border-violet-500/30 transition-colors cursor-pointer" onClick={() => navigate(`/job-tickets/${ticket.id}`)} data-testid={`ticket-${ticket.ticket_number}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${ticket.production_flow_enabled ? 'bg-violet-500/15' : 'bg-slate-700'}`}>
                        <Package className={`w-5 h-5 ${ticket.production_flow_enabled ? 'text-violet-400' : 'text-slate-400'}`} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-sm text-slate-400">{ticket.ticket_number}</span>
                          <Badge variant="outline" className={STATUS_COLORS[ticket.status]}>{formatStatus(ticket.status)}</Badge>
                          {ticket.priority !== 'normal' && <Badge className={PRIORITY_COLORS[ticket.priority]}>{ticket.priority}</Badge>}
                          {ticket.production_flow_enabled && <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-xs">Workflow</Badge>}
                        </div>
                        <p className="text-white font-medium mt-0.5">{ticket.item_name}</p>
                        <p className="text-slate-500 text-xs">{CATEGORY_LABELS[ticket.item_category] || ticket.item_category} | Qty: {ticket.quantity} | {ticket.estimated_price ? `$${ticket.estimated_price.toFixed(2)}` : 'No price'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      {ticket.production_flow_enabled && (
                        <div className="text-right hidden sm:block">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                              <div className="h-full bg-violet-500 rounded-full" style={{ width: `${ticket.progress || 0}%` }} />
                            </div>
                            <span className="text-xs text-slate-400">{Math.round(ticket.progress || 0)}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {tab === 'activity' && (
        <div className="space-y-2">
          {activities.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No activity yet</p>
          ) : activities.map(a => (
            <div key={a.id} className="flex items-start gap-3 py-2 border-b border-slate-800 last:border-0">
              <div className="w-2 h-2 rounded-full bg-violet-500 mt-2 flex-shrink-0" />
              <div>
                <p className="text-sm text-white">{a.description}</p>
                <p className="text-xs text-slate-500 mt-0.5">{new Date(a.created_at).toLocaleString()}{a.user_name ? ` by ${a.user_name}` : ''}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="pt-4 border-t border-slate-800">
        <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={deleteOrder}>
          <Trash2 className="w-4 h-4 mr-2" /> Delete Order
        </Button>
      </div>
    </div>
  );
}
