import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Plus, Package, FileText, Play, Clock, CheckCircle, AlertTriangle,
  Trash2, Loader2, Receipt, Wrench, MessageSquare, DollarSign, Pause, ChevronRight,
  Copy, Calculator, Edit3, MoreHorizontal, Upload, FileUp, Paperclip, Send, Mail, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/json' });

const STATUS_COLORS = {
  new_intake: 'bg-blue-500/15 text-blue-400 border-blue-500/30', awaiting_review: 'bg-yellow-500/15 text-yellow-400',
  in_production: 'bg-violet-500/15 text-violet-400', partially_complete: 'bg-cyan-500/15 text-cyan-400',
  ready_for_pickup: 'bg-green-500/15 text-green-400', completed: 'bg-green-600/15 text-green-600',
  on_hold: 'bg-red-500/15 text-red-400', cancelled: 'bg-slate-500/15 text-gray-500',
  approved: 'bg-teal-500/15 text-teal-400', new: 'bg-blue-500/15 text-blue-400',
  queued: 'bg-indigo-500/15 text-indigo-400', in_qc: 'bg-amber-500/15 text-amber-400',
  ready: 'bg-green-500/15 text-green-400', rework: 'bg-red-500/15 text-red-400',
  awaiting_quote: 'bg-orange-500/15 text-orange-400', quote_sent: 'bg-purple-500/15 text-purple-400',
  draft: 'bg-slate-500/15 text-gray-500', sent: 'bg-blue-500/15 text-blue-400', paid: 'bg-green-500/15 text-green-400',
  not_started: 'bg-gray-200 text-gray-700', in_progress: 'bg-violet-500/15 text-violet-400',
  paused: 'bg-orange-500/15 text-orange-400', complete: 'bg-green-500/15 text-green-400',
};
const CATEGORY_LABELS = { rigid_signs: 'Rigid Signs', banners: 'Banners', cut_vinyl: 'Cut Vinyl', vehicle_wrap: 'Vehicle Wrap', apparel: 'Apparel', promo_misc: 'Promo / Misc', custom: 'Custom' };
const PRIORITY_COLORS = { rush: 'bg-red-500 text-gray-900', urgent: 'bg-orange-500 text-gray-900', high: 'bg-amber-500/80 text-black', normal: 'bg-slate-600 text-slate-200' };
const DEPT_LABELS = { design: 'Design', print: 'Print', cut_trim: 'Cut / Trim', lamination: 'Lamination', weed_mask: 'Weed / Mask', sewing_finishing: 'Sewing', assembly: 'Assembly', apparel: 'Apparel', wrap_prep: 'Wrap Prep', install: 'Install', qc_review: 'QC', packaging: 'Packaging', delivery: 'Delivery' };
const fmt = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function OrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [activities, setActivities] = useState([]);
  const [financials, setFinancials] = useState({ quotes: [], invoices: [] });
  const [prodSummary, setProdSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [tab, setTab] = useState('tickets');
  const [taskLoading, setTaskLoading] = useState('');
  const [orderFiles, setOrderFiles] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);

  const load = async () => {
    try {
      const [orderRes, actRes, finRes, prodRes, filesRes] = await Promise.all([
        axios.get(`${API}/orders/${id}`, { headers: hdr() }),
        axios.get(`${API}/orders/${id}/activity`, { headers: hdr() }),
        axios.get(`${API}/orders/${id}/financials`, { headers: hdr() }).catch(() => ({ data: { quotes: [], invoices: [] } })),
        axios.get(`${API}/orders/${id}/production-summary`, { headers: hdr() }).catch(() => ({ data: null })),
        axios.get(`${API}/orders/${id}/files`, { headers: hdr() }).catch(() => ({ data: [] })),
      ]);
      setOrder(orderRes.data);
      setActivities(actRes.data);
      setFinancials(finRes.data);
      setProdSummary(prodRes.data);
      setOrderFiles(filesRes.data || []);
    } catch { toast.error('Failed to load order'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [id]);

  const startProduction = async () => {
    setActionLoading('production');
    try {
      const res = await axios.post(`${API}/orders/${id}/start-production`, {}, { headers: hdr() });
      toast.success(`Production started: ${res.data.tasks_created} tasks created`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setActionLoading(''); }
  };

  const generateDoc = async (type) => {
    setActionLoading(type);
    try {
      const res = await axios.post(`${API}/orders/${id}/generate-${type}`, {}, { headers: hdr() });
      toast.success(`${fmt(type)} generated: $${res.data.total?.toFixed(2)}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setActionLoading(''); }
  };

  const updateTask = async (taskId, status) => {
    setTaskLoading(taskId);
    try {
      await axios.put(`${API}/production-tasks/${taskId}`, { status }, { headers: hdr() });
      toast.success(`Task ${fmt(status)}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setTaskLoading(''); }
  };

  const deleteOrder = async () => {
    if (!window.confirm('Delete this order and all related records?')) return;
    try {
      await axios.delete(`${API}/orders/${id}`, { headers: hdr() });
      toast.success('Order deleted');
      navigate('/orders');
    } catch { toast.error('Failed to delete'); }
  };

  const sendEmail = async (docType) => {
    setActionLoading('email');
    try {
      // Find the latest quote or invoice for this order
      const docs = docType === 'quote' ? financials.quotes : financials.invoices;
      if (!docs?.length) {
        toast.error(`No ${docType} found. Generate one first.`);
        setActionLoading('');
        return;
      }
      const doc = docs[0];
      await axios.post(`${API}/documents/send-email`, {
        document_type: docType,
        document_id: doc.id,
        customer_email: order.email,
        customer_name: order.customer_name,
        subject: `${docType === 'quote' ? 'Quote' : 'Invoice'} from ${order.company_name || 'SignGuy AI'} - ${order.order_number}`,
      }, { headers: hdr() });
      toast.success(`${docType === 'quote' ? 'Quote' : 'Invoice'} sent to ${order.email}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to send email');
    } finally { setActionLoading(''); }
  };

  const updateOrderStatus = async (newStatus) => {
    try {
      await axios.put(`${API}/orders/${id}`, { status: newStatus }, { headers: hdr() });
      toast.success(`Status updated to ${fmt(newStatus)}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const duplicateTicket = async (ticketId) => {
    try {
      const res = await axios.post(`${API}/job-tickets/${ticketId}/duplicate`, {}, { headers: hdr() });
      toast.success(`Duplicated → ${res.data.ticket_number}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to duplicate'); }
  };

  const deleteTicket = async (ticketId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this job ticket and its tasks?')) return;
    try {
      await axios.delete(`${API}/job-tickets/${ticketId}`, { headers: hdr() });
      toast.success('Ticket deleted');
      load();
    } catch { toast.error('Failed to delete'); }
  };

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploadingFile(true);
    try {
      for (const f of files) {
        const formData = new FormData();
        formData.append('file', f);
        formData.append('label', f.name);
        await axios.post(`${API}/orders/${id}/upload`, formData, {
          headers: { Authorization: `Bearer ${localStorage.getItem('auth_token')}` },
        });
      }
      toast.success(`${files.length} file(s) uploaded`);
      load();
    } catch { toast.error('Upload failed'); }
    finally { setUploadingFile(false); e.target.value = ''; }
  };

  const deleteFile = async (fileId) => {
    try {
      await axios.delete(`${API}/orders/${id}/files/${fileId}`, { headers: hdr() });
      toast.success('File deleted');
      setOrderFiles(prev => prev.filter(f => f.id !== fileId));
    } catch { toast.error('Failed to delete file'); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;
  if (!order) return <div className="text-center py-20 text-gray-500">Order not found</div>;

  const tickets = order.job_tickets || [];
  // Order total: use active price from pricing snapshot, fallback to estimated_price
  const orderTotal = order.order_total || tickets.reduce((sum, t) => {
    const snapshot = t.pricing_snapshot;
    if (snapshot?.active_price) return sum + snapshot.active_price;
    return sum + (t.estimated_price || 0);
  }, 0);
  const workflowTickets = tickets.filter(t => t.production_flow_enabled);
  const allTasks = prodSummary?.tasks || [];

  return (
    <div className="space-y-6" data-testid="order-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate('/orders')}><ArrowLeft className="w-5 h-5 text-gray-500" /></Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white font-heading">{order.order_number}</h1>
              <Badge variant="outline" className={STATUS_COLORS[order.status]}>{fmt(order.status)}</Badge>
            </div>
            <p className="text-slate-400 text-sm">{order.customer_name}{order.company_name ? ` — ${order.company_name}` : ''}</p>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <FileText className="w-4 h-4" /> Generate
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => generateDoc('quote')} disabled={!!actionLoading || tickets.length === 0}>
                <FileText className="w-4 h-4 mr-2" /> Generate Quote
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generateDoc('invoice')} disabled={!!actionLoading || tickets.length === 0}>
                <Receipt className="w-4 h-4 mr-2" /> Generate Invoice
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => generateDoc('work_order')} disabled={!!actionLoading || tickets.length === 0}>
                <Wrench className="w-4 h-4 mr-2" /> Generate Work Order
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <Send className="w-4 h-4" /> Send
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => sendEmail('quote')} disabled={!!actionLoading || !order.email}>
                <Mail className="w-4 h-4 mr-2" /> Email Quote
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => sendEmail('invoice')} disabled={!!actionLoading || !order.email}>
                <Mail className="w-4 h-4 mr-2" /> Email Invoice
              </DropdownMenuItem>
              {order.customer_id && (
                <DropdownMenuItem onClick={() => navigate(`/admin-portal?customer_id=${order.customer_id}`)}>
                  <ExternalLink className="w-4 h-4 mr-2" /> View in Portal
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <Edit3 className="w-4 h-4" /> Status
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {['approved', 'in_production', 'on_hold', 'ready_for_pickup', 'completed', 'cancelled'].map(s => (
                <DropdownMenuItem key={s} onClick={() => updateOrderStatus(s)} disabled={order.status === s}>
                  {fmt(s)}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-white" onClick={startProduction} disabled={!!actionLoading || workflowTickets.length === 0} data-testid="start-production-btn">
            {actionLoading === 'production' ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Play className="w-4 h-4 mr-1" />} Start Production
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { label: 'Tickets', value: tickets.length },
          { label: 'Estimate', value: `$${orderTotal.toFixed(2)}` },
          { label: 'Progress', value: `${Math.round(order.overall_progress || 0)}%` },
          { label: 'Due', value: order.requested_due_date ? new Date(order.requested_due_date).toLocaleDateString() : '-' },
          { label: 'Payment', value: fmt(order.payment_status) },
          { label: 'Source', value: fmt(order.order_source) },
        ].map(c => (
          <Card key={c.label} className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardContent className="p-3 text-center">
              <p className="text-xs text-gray-500 uppercase">{c.label}</p>
              <p className="text-lg font-bold text-gray-900 mt-1">{c.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Progress Bar */}
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${order.overall_progress || 0}%` }} />
      </div>

      {/* Tabs + Content Card */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex gap-1 border-b border-gray-200 overflow-x-auto px-4 pt-3">
          {[
            { id: 'tickets', label: `Job Tickets (${tickets.length})` },
            { id: 'production', label: `Production (${allTasks.length})` },
            { id: 'financial', label: `Financial (${(financials.quotes?.length || 0) + (financials.invoices?.length || 0)})` },
            { id: 'files', label: `Files (${orderFiles.length})` },
            { id: 'notes', label: 'Notes' },
            { id: 'activity', label: `Activity (${activities.length})` },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${tab === t.id ? 'text-violet-600 border-violet-600' : 'text-gray-500 border-transparent hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="p-4 lg:p-6">

      {/* === TICKETS TAB === */}
      {tab === 'tickets' && (
        <div className="space-y-3">
          <Button variant="outline" size="sm" onClick={() => navigate(`/orders/${id}/add-ticket`)} className="gap-2" data-testid="add-ticket-btn">
            <Plus className="w-4 h-4" /> Add Job Ticket
          </Button>
          {tickets.length === 0 ? (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="py-12 text-center text-gray-500">No job tickets yet.</CardContent></Card>
          ) : tickets.map(ticket => {
            const snapshot = ticket.pricing_snapshot;
            const pricingMode = snapshot?.pricing_mode || (ticket.estimated_price ? 'estimate' : 'none');
            const activePrice = snapshot?.active_price || ticket.estimated_price || 0;
            const specs = ticket.specs || {};
            const specSummary = [specs.width, specs.height, specs.material].filter(Boolean).join(' × ');
            return (
              <Card key={ticket.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:border-violet-500/30 transition-colors cursor-pointer" onClick={() => navigate(`/job-tickets/${ticket.id}`)} data-testid={`ticket-${ticket.ticket_number}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${ticket.production_flow_enabled ? 'bg-violet-500/15' : 'bg-gray-200'}`}>
                        <Package className={`w-5 h-5 ${ticket.production_flow_enabled ? 'text-violet-400' : 'text-gray-500'}`} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
                          <Badge variant="outline" className={STATUS_COLORS[ticket.status]}>{fmt(ticket.status)}</Badge>
                          {ticket.priority !== 'normal' && <Badge className={PRIORITY_COLORS[ticket.priority]}>{ticket.priority}</Badge>}
                          {ticket.production_flow_enabled && <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-xs">Workflow</Badge>}
                          {/* Pricing mode badge */}
                          {pricingMode === 'calculator' && <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30 text-xs"><Calculator className="w-3 h-3 mr-1" />Calc</Badge>}
                          {pricingMode === 'manual' && <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30 text-xs"><Edit3 className="w-3 h-3 mr-1" />Manual</Badge>}
                          {ticket.design_needed && <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30 text-xs">Design</Badge>}
                          {ticket.proof_required && <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-xs">Proof</Badge>}
                        </div>
                        <p className="text-gray-900 font-medium mt-0.5">{ticket.item_name}</p>
                        <p className="text-gray-500 text-xs">
                          {CATEGORY_LABELS[ticket.item_category] || ticket.item_category} | Qty: {ticket.quantity}
                          {specSummary ? ` | ${specSummary}` : ''}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      {/* Price */}
                      <div className="text-right hidden sm:block">
                        <p className="text-lg font-bold text-gray-900">${activePrice.toFixed(2)}</p>
                        <p className="text-xs text-gray-500">{pricingMode !== 'none' ? pricingMode : 'no price'}</p>
                      </div>
                      {/* Progress */}
                      {ticket.production_flow_enabled && (
                        <div className="text-right hidden md:block">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div className="h-full bg-violet-500 rounded-full" style={{ width: `${ticket.progress || 0}%` }} />
                            </div>
                            <span className="text-xs text-gray-500">{Math.round(ticket.progress || 0)}%</span>
                          </div>
                        </div>
                      )}
                      {/* Actions */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-gray-500">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); navigate(`/job-tickets/${ticket.id}`); }}>
                            <Package className="w-4 h-4 mr-2" /> Open Ticket
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); duplicateTicket(ticket.id); }}>
                            <Copy className="w-4 h-4 mr-2" /> Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-400" onClick={(e) => deleteTicket(ticket.id, e)}>
                            <Trash2 className="w-4 h-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* === PRODUCTION TAB === */}
      {tab === 'production' && (
        <div className="space-y-4">
          {prodSummary?.summary && (
            <div className="grid grid-cols-3 gap-3">
              <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="p-3 text-center"><p className="text-xs text-gray-500">Total Tasks</p><p className="text-xl font-bold text-gray-900">{prodSummary.summary.total_tasks}</p></CardContent></Card>
              <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="p-3 text-center"><p className="text-xs text-gray-500">Completed</p><p className="text-xl font-bold text-green-400">{prodSummary.summary.completed}</p></CardContent></Card>
              <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="p-3 text-center"><p className="text-xs text-gray-500">Flagged</p><p className="text-xl font-bold text-red-400">{prodSummary.summary.on_hold}</p></CardContent></Card>
            </div>
          )}
          {allTasks.length === 0 ? (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="py-12 text-center text-gray-500">No production tasks. Start production to generate tasks.</CardContent></Card>
          ) : (
            Object.entries(prodSummary?.by_department || {}).map(([dept, tasks]) => (
              <div key={dept}>
                <h3 className="text-sm font-bold text-gray-700 uppercase mb-2">{DEPT_LABELS[dept] || fmt(dept)} ({tasks.length})</h3>
                <div className="space-y-1">
                  {tasks.map(task => {
                    const ticket = (prodSummary?.tickets || []).find(t => t.id === task.job_ticket_id);
                    return (
                      <Card key={task.id} className={`bg-white border-gray-200 ${task.status === 'in_progress' ? 'border-l-4 border-l-violet-500' : task.status === 'complete' ? 'border-l-4 border-l-green-500' : ''}`}>
                        <CardContent className="p-3 flex items-center justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-900 text-sm font-medium">{task.task_name}</span>
                              <Badge variant="outline" className={`text-xs ${STATUS_COLORS[task.status]}`}>{fmt(task.status)}</Badge>
                            </div>
                            <p className="text-xs text-gray-500">{ticket?.ticket_number} — {ticket?.item_name}</p>
                          </div>
                          <div className="flex gap-1">
                            {task.status !== 'complete' && task.status !== 'in_progress' && (
                              <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-violet-400" onClick={() => updateTask(task.id, 'in_progress')} disabled={taskLoading === task.id}>
                                {taskLoading === task.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                              </Button>
                            )}
                            {task.status === 'in_progress' && (
                              <>
                                <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-green-400" onClick={() => updateTask(task.id, 'complete')} disabled={taskLoading === task.id}><CheckCircle className="w-3 h-3" /></Button>
                                <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-orange-400" onClick={() => updateTask(task.id, 'paused')} disabled={taskLoading === task.id}><Pause className="w-3 h-3" /></Button>
                              </>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* === FINANCIAL TAB === */}
      {tab === 'financial' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => generateDoc('quote')} disabled={!!actionLoading || tickets.length === 0}>
              {actionLoading === 'quote' ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <FileText className="w-4 h-4 mr-1" />} Generate Quote
            </Button>
            <Button variant="outline" size="sm" onClick={() => generateDoc('invoice')} disabled={!!actionLoading || tickets.length === 0}>
              {actionLoading === 'invoice' ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Receipt className="w-4 h-4 mr-1" />} Generate Invoice
            </Button>
          </div>
          {financials.quotes?.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-700 uppercase mb-2">Quotes ({financials.quotes.length})</h3>
              {financials.quotes.map(q => (
                <Card key={q.id} className="bg-white border-gray-200 mb-2">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2"><FileText className="w-4 h-4 text-purple-400" /><span className="text-gray-900 font-medium">Quote</span><Badge variant="outline" className={STATUS_COLORS[q.status]}>{fmt(q.status)}</Badge></div>
                        <p className="text-xs text-gray-500 mt-1">{new Date(q.created_at).toLocaleDateString()} | {q.line_items?.length || 0} items</p>
                      </div>
                      <p className="text-xl font-bold text-gray-900">${(q.total || 0).toFixed(2)}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          {financials.invoices?.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-700 uppercase mb-2">Invoices ({financials.invoices.length})</h3>
              {financials.invoices.map(inv => (
                <Card key={inv.id} className="bg-white border-gray-200 mb-2">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2"><Receipt className="w-4 h-4 text-green-400" /><span className="text-gray-900 font-medium">Invoice</span><Badge variant="outline" className={STATUS_COLORS[inv.status]}>{fmt(inv.status)}</Badge></div>
                        <p className="text-xs text-gray-500 mt-1">{new Date(inv.created_at).toLocaleDateString()} | {inv.line_items?.length || 0} items{inv.due_date ? ` | Due: ${new Date(inv.due_date).toLocaleDateString()}` : ''}</p>
                      </div>
                      <p className="text-xl font-bold text-gray-900">${(inv.total || 0).toFixed(2)}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          {(financials.quotes?.length || 0) === 0 && (financials.invoices?.length || 0) === 0 && (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="py-12 text-center text-gray-500">No financial documents yet. Generate a quote or invoice from the job tickets.</CardContent></Card>
          )}
        </div>
      )}


      {/* === FILES TAB === */}
      {tab === 'files' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">{orderFiles.length} file{orderFiles.length !== 1 ? 's' : ''} attached</p>
            <div>
              <input type="file" multiple onChange={handleFileUpload} className="hidden" id="order-detail-file-input" />
              <label htmlFor="order-detail-file-input">
                <Button asChild variant="outline" size="sm" className="gap-2 cursor-pointer" disabled={uploadingFile}>
                  <span>{uploadingFile ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Upload Files</span>
                </Button>
              </label>
            </div>
          </div>
          {orderFiles.length === 0 ? (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <CardContent className="py-12 text-center">
                <Paperclip className="w-8 h-8 mx-auto text-gray-300 mb-3" />
                <p className="text-gray-500">No files attached to this order</p>
                <p className="text-gray-400 text-sm mt-1">Upload artwork, drawings, photos, or any reference files</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {orderFiles.map(f => (
                <Card key={f.id} className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <CardContent className="p-3 flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-10 h-10 rounded-lg bg-violet-50 flex items-center justify-center flex-shrink-0">
                        <FileUp className="w-5 h-5 text-violet-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{f.label || f.filename}</p>
                        <p className="text-xs text-gray-500">{f.filename} | {(f.file_size / 1024).toFixed(0)} KB | {new Date(f.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-600" onClick={() => deleteFile(f.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* === NOTES TAB === */}
      {tab === 'notes' && (
        <div className="space-y-4">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2"><MessageSquare className="w-4 h-4 text-gray-500" /><p className="text-sm font-medium text-gray-700">Internal Notes</p></div>
              <p className="text-gray-900 text-sm">{order.internal_notes || <span className="text-gray-400 italic">No internal notes</span>}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2"><MessageSquare className="w-4 h-4 text-gray-500" /><p className="text-sm font-medium text-gray-700">Customer Notes</p></div>
              <p className="text-gray-900 text-sm">{order.customer_notes || <span className="text-gray-400 italic">No customer notes</span>}</p>
            </CardContent>
          </Card>
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2"><Package className="w-4 h-4 text-gray-500" /><p className="text-sm font-medium text-gray-700">Pickup / Delivery</p></div>
              <p className="text-gray-900 text-sm">{fmt(order.pickup_delivery_method)}{order.pickup_delivery_notes ? ` — ${order.pickup_delivery_notes}` : ''}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* === ACTIVITY TAB === */}
      {tab === 'activity' && (
        <div className="space-y-2">
          {activities.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No activity yet</p>
          ) : activities.map(a => (
            <div key={a.id} className="flex items-start gap-3 py-2 border-b border-gray-200 last:border-0">
              <div className="w-2 h-2 rounded-full bg-violet-500 mt-2 flex-shrink-0" />
              <div>
                <p className="text-sm text-gray-900">{a.description}</p>
                <p className="text-xs text-gray-500 mt-0.5">{new Date(a.created_at).toLocaleString()}{a.user_name ? ` by ${a.user_name}` : ''}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="pt-4 border-t border-gray-200">
        <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600 hover:bg-red-50" onClick={deleteOrder}>
          <Trash2 className="w-4 h-4 mr-2" /> Delete Order
        </Button>
      </div>
        </div>
      </Card>
    </div>
  );
}
