import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, Package, Wrench, FileImage, MessageSquare, Clock, CheckCircle, AlertTriangle,
  Play, Pause, RotateCcw, Eye, Upload, Loader2, ChevronDown, ChevronRight, Edit3,
  UserPlus, CalendarPlus, ListTodo, Pen, Image as ImageIcon, Camera
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import axios from 'axios';
import LivePricingPanel from '../components/LivePricingPanel';
import DynamicCategoryFields from '../components/DynamicCategoryFields';
import { TicketWorkflowShortcutDialog } from '../components/TicketWorkflowShortcutDialog';
import DrawingModal from './DrawingModal';
import DrawingPreviewModal from './DrawingPreviewModal';
import { getAuthToken } from '../lib/authStorage';
import { useSetPageContext } from '../context/PageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

const STATUS_COLORS = {
  new: 'bg-blue-500/15 text-blue-400 border-blue-500/30', awaiting_info: 'bg-yellow-500/15 text-yellow-400', awaiting_proof: 'bg-orange-500/15 text-orange-400',
  awaiting_approval: 'bg-amber-500/15 text-amber-400', approved: 'bg-teal-500/15 text-teal-400', queued: 'bg-indigo-500/15 text-indigo-400',
  in_production: 'bg-violet-500/15 text-violet-400', in_qc: 'bg-cyan-500/15 text-cyan-400', on_hold: 'bg-red-500/15 text-red-400',
  ready: 'bg-green-500/15 text-green-400', completed: 'bg-green-600/15 text-green-600', rework: 'bg-red-500/15 text-red-400', cancelled: 'bg-slate-500/15 text-gray-500',
};
const TASK_COLORS = {
  not_started: 'bg-gray-200 text-gray-700', waiting: 'bg-yellow-500/15 text-yellow-400', ready: 'bg-blue-500/15 text-blue-400',
  in_progress: 'bg-violet-500/15 text-violet-400', paused: 'bg-orange-500/15 text-orange-400', on_hold: 'bg-red-500/15 text-red-400',
  needs_review: 'bg-amber-500/15 text-amber-400', complete: 'bg-green-500/15 text-green-400', rework: 'bg-red-500/15 text-red-400',
};
const PRIORITY_COLORS = { rush: 'bg-red-500 text-gray-900', urgent: 'bg-orange-500 text-gray-900', high: 'bg-amber-500/80 text-black', normal: 'bg-slate-600 text-slate-200' };
const CATEGORY_LABELS = { rigid_signs: 'Rigid Signs', banners: 'Banners', cut_vinyl: 'Cut Vinyl', digital_print: 'Digital Print', vehicle_wrap: 'Vehicle Wrap', apparel: 'Apparel', services: 'Services', promo_misc: 'Promo / Misc', custom: 'Custom' };
const fmt = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function JobTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [ticket, setTicket] = useState(null);

  useSetPageContext({
    page: 'job_ticket_detail',
    recordType: 'job_ticket',
    recordId: ticketId,
    recordLabel: ticket?.ticket_number || ticket?.item_name || ticketId,
  });
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(() => searchParams.get('tab') || 'specs');
  const [taskLoading, setTaskLoading] = useState('');
  const [employees, setEmployees] = useState([]);
  const [orderSummary, setOrderSummary] = useState(null);
  const [shortcutMode, setShortcutMode] = useState('');
  const [ticketDrawings, setTicketDrawings] = useState([]);
  const [orderFiles, setOrderFiles] = useState([]);
  const [showDrawingModal, setShowDrawingModal] = useState(false);
  const [markupImage, setMarkupImage] = useState(null);
  const [previewDrawing, setPreviewDrawing] = useState(null);
  const [drawingsEnabled, setDrawingsEnabled] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);
  const [quickPhotoUploading, setQuickPhotoUploading] = useState(false);
  const quickPhotoCameraRef = useRef(null);
  const quickPhotoGalleryRef = useRef(null);

  const handleQuickPhoto = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !ticket?.order_id) return;
    e.target.value = '';
    setQuickPhotoUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('label', `Photo — ${file.name}`);
      const res = await axios.post(`${API}/orders/${ticket.order_id}/upload`, formData, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      const uploadedFile = res.data;
      toast.success('Photo uploaded — opening markup');
      await load();
      const contentRes = await axios.get(`${API}/orders/${ticket.order_id}/files/${uploadedFile.id}/content`, {
        headers: hdr(),
        responseType: 'blob',
      });
      const contentUrl = URL.createObjectURL(contentRes.data);
      setMarkupImage({
        id: uploadedFile.id,
        label: uploadedFile.label || uploadedFile.filename || file.name,
        contentUrl,
      });
      setShowDrawingModal(true);
    } catch {
      toast.error('Photo upload failed');
    } finally {
      setQuickPhotoUploading(false);
    }
  };

  const load = async () => {
    try {
      const [ticketRes, employeesRes] = await Promise.all([
        axios.get(`${API}/job-tickets/${ticketId}`, { headers: hdr() }),
        axios.get(`${API}/employees`, { headers: hdr() }).catch(() => ({ data: [] })),
      ]);
      setTicket(ticketRes.data);
      setEmployees(employeesRes.data || []);
      if (ticketRes.data?.order_id) {
        const [orderRes, drawingsRes, filesRes] = await Promise.all([
          axios.get(`${API}/orders/${ticketRes.data.order_id}`, { headers: hdr() }).catch(() => ({ data: null })),
          axios.get(`${API}/order-drawings`, { headers: hdr(), params: { job_ticket_id: ticketId } }).catch(() => ({ data: [] })),
          axios.get(`${API}/orders/${ticketRes.data.order_id}/files`, { headers: hdr() }).catch(() => ({ data: [] })),
        ]);
        setOrderSummary(orderRes.data);
        setTicketDrawings(drawingsRes.data || []);
        setOrderFiles((filesRes.data || []).filter((file) => file.content_type?.startsWith('image/')));
        setDrawingsEnabled((drawingsRes.data || []).length > 0);
      }
    } catch { toast.error('Failed to load ticket'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [ticketId]);

  const [editing, setEditing] = useState(false);
  const [editSpecs, setEditSpecs] = useState({});
  const [editFields, setEditFields] = useState({});
  const [saveLoading, setSaveLoading] = useState(false);

  const startEdit = () => {
    setEditSpecs({ ...(ticket?.specs || {}) });
    setEditFields({
      special_instructions: ticket?.special_instructions || '',
      production_notes: ticket?.production_notes || '',
      install_notes: ticket?.install_notes || '',
      packaging_notes: ticket?.packaging_notes || '',
    });
    setEditing(true);
  };

  const saveEdit = async () => {
    setSaveLoading(true);
    try {
      await axios.put(`${API}/job-tickets/${ticketId}`, { specs: editSpecs, ...editFields }, { headers: hdr() });
      toast.success('Order item updated');
      setEditing(false);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save'); }
    finally { setSaveLoading(false); }
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

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;
  if (!ticket) return <div className="text-center py-20 text-gray-500">Ticket not found</div>;

  const tasks = ticket.production_tasks || [];
  const specs = ticket.specs || {};
  const completedTasks = tasks.filter(t => t.status === 'complete').length;
  const getEmployeeName = (employeeId) => employees.find((employee) => employee.id === employeeId)?.name || employeeId;
  const latestDraftDrawing = ticketDrawings.find((drawing) => drawing.status === 'draft') || null;

  const buildImageMarkupPayload = async (file) => {
    const response = await axios.get(`${API}/orders/${ticket.order_id}/files/${file.id}/content`, { headers: hdr(), responseType: 'blob' });
    const objectUrl = URL.createObjectURL(response.data);
    return {
      id: file.id,
      label: file.label || file.filename,
      contentUrl: objectUrl,
    };
  };

  return (
    <div className="space-y-6" data-testid="job-ticket-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/orders/${ticket.order_id}`)}><ArrowLeft className="w-5 h-5 text-gray-500" /></Button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm text-gray-500">{ticket.ticket_number}</span>
              <Badge variant="outline" className={STATUS_COLORS[ticket.status]}>{fmt(ticket.status)}</Badge>
              {ticket.priority !== 'normal' && <Badge className={PRIORITY_COLORS[ticket.priority]}>{ticket.priority}</Badge>}
              {ticket.production_flow_enabled && <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-xs">Workflow</Badge>}
            </div>
            <h1 className="text-2xl font-bold text-white mt-1">{ticket.item_name}</h1>
            <p className="text-slate-400 text-sm">{CATEGORY_LABELS[ticket.item_category] || ticket.item_category} | Qty: {ticket.quantity} {ticket.unit_type}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="job-ticket-shortcut-actions">
        {/* Quick Photo — hidden inputs */}
        <input ref={quickPhotoCameraRef} type="file" accept="image/*" capture="environment" onChange={handleQuickPhoto} className="hidden" data-testid="item-quick-photo-camera" />
        <input ref={quickPhotoGalleryRef} type="file" accept="image/*" onChange={handleQuickPhoto} className="hidden" data-testid="item-quick-photo-gallery" />
        <Button variant="outline" size="sm" onClick={() => quickPhotoCameraRef.current?.click()} disabled={quickPhotoUploading} data-testid="item-quick-photo-btn">
          {quickPhotoUploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Camera className="w-4 h-4 mr-2" />} Quick Photo
        </Button>
        <Button variant="outline" size="sm" onClick={() => quickPhotoGalleryRef.current?.click()} disabled={quickPhotoUploading} data-testid="item-choose-photo-btn">
          <ImageIcon className="w-4 h-4 mr-2" /> Choose Photo
        </Button>
        <Button variant="outline" size="sm" onClick={() => setShortcutMode('assign')} data-testid="job-ticket-assign-shortcut-button">
          <UserPlus className="w-4 h-4 mr-2" /> Assign Employee
        </Button>
        <Button variant="outline" size="sm" onClick={() => setShortcutMode('schedule')} data-testid="job-ticket-schedule-shortcut-button">
          <CalendarPlus className="w-4 h-4 mr-2" /> Add to Schedule
        </Button>
        <Button variant="outline" size="sm" onClick={() => setShortcutMode('task')} data-testid="job-ticket-task-shortcut-button">
          <ListTodo className="w-4 h-4 mr-2" /> Create Task
        </Button>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {[
          { label: 'Price', value: ticket.estimated_price ? `$${ticket.estimated_price.toFixed(2)}` : '-' },
          { label: 'Progress', value: `${Math.round(ticket.progress || 0)}%` },
          { label: 'Tasks', value: tasks.length > 0 ? `${completedTasks}/${tasks.length}` : 'None' },
          { label: 'Due', value: ticket.due_date ? new Date(ticket.due_date).toLocaleDateString() : '-' },
          { label: 'Proof', value: fmt(ticket.proof_approval_status || 'none') },
          { label: 'Assigned', value: ticket.assigned_user_id ? getEmployeeName(ticket.assigned_user_id) : 'Unassigned' },
        ].map(c => (
          <Card key={c.label} className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardContent className="p-3 text-center">
              <p className="text-xs text-gray-500 uppercase">{c.label}</p>
              <p className="text-lg font-bold text-gray-900 mt-1">{c.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Progress bar */}
      {tasks.length > 0 && (
        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full transition-all duration-500" style={{ width: `${ticket.progress || 0}%` }} />
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm px-4 pt-3">
        <div className="flex gap-1 overflow-x-auto">
          {[
            { id: 'specs', label: 'Specs' },
            { id: 'production', label: `Production (${tasks.length})` },
            { id: 'drawings', label: `Drawings (${ticketDrawings.length})` },
            { id: 'artwork', label: 'Artwork / Files' },
            { id: 'notes', label: 'Notes' },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${tab === t.id ? 'text-violet-600 border-violet-600' : 'text-gray-500 border-transparent hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* SPECS TAB - with Live Pricing Panel */}
      {tab === 'specs' && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-5">
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-gray-900 text-lg flex items-center gap-2"><Package className="w-5 h-5 text-violet-400" /> Item Specifications</CardTitle>
                {!editing ? (
                  <Button variant="outline" size="sm" onClick={startEdit} className="gap-1 text-gray-700"><Edit3 className="w-3.5 h-3.5" /> Edit</Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setEditing(false)}>Cancel</Button>
                    <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-white" onClick={saveEdit} disabled={saveLoading}>
                      {saveLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null} Save
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {editing ? (
                <DynamicCategoryFields category={ticket.item_category} specs={editSpecs} onChange={setEditSpecs} mode="edit" />
              ) : (
                <DynamicCategoryFields category={ticket.item_category} specs={specs} onChange={() => {}} mode="view" />
              )}
              {/* Boolean flags */}
              <div className="flex flex-wrap gap-3 mt-4">
                {specs.grommets && <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">Grommets</Badge>}
                {specs.hemming && <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">Hemming</Badge>}
                {specs.install_required && <Badge variant="outline" className="bg-orange-500/10 text-orange-400 border-orange-500/30">Install Required</Badge>}
                {ticket.design_needed && <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/30">Design Needed</Badge>}
                {ticket.proof_required && <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30">Proof Required</Badge>}
                {ticket.customer_artwork && <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">Customer Artwork</Badge>}
              </div>
            </CardContent>
          </Card>

          {/* Live Pricing Panel - right side */}
          <LivePricingPanel ticketId={ticketId} ticketData={ticket} onPriceSaved={() => load()} />
        </div>
      )}

      {/* PRODUCTION TAB */}
      {tab === 'production' && (
        <div className="space-y-2">
          {tasks.length === 0 ? (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm"><CardContent className="py-12 text-center text-gray-500">No production tasks. Enable workflow on this ticket to generate tasks.</CardContent></Card>
          ) : tasks.map((task, i) => {
            const isComplete = task.status === 'complete';
            const isActive = task.status === 'in_progress';
            return (
              <Card key={task.id} className={`bg-white border-gray-200 ${isActive ? 'border-l-4 border-l-violet-500' : isComplete ? 'border-l-4 border-l-green-500' : ''}`} data-testid={`task-${task.stage_sequence}`}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${isComplete ? 'bg-green-100 text-green-600' : isActive ? 'bg-violet-100 text-violet-600' : 'bg-gray-200 text-gray-500'}`}>
                        {isComplete ? <CheckCircle className="w-4 h-4" /> : task.stage_sequence}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-gray-900 font-medium">{task.task_name}</span>
                          <Badge variant="outline" className={TASK_COLORS[task.status] || TASK_COLORS.not_started}>{fmt(task.status)}</Badge>
                          {task.qc_required && <Badge variant="outline" className="text-xs bg-cyan-500/10 text-cyan-400 border-cyan-500/30">QC</Badge>}
                          {task.rework_flag && <Badge className="bg-red-500 text-gray-900 text-xs">Rework</Badge>}
                        </div>
                            <p className="text-xs text-gray-500 mt-0.5">{fmt(task.department)}{task.assigned_to ? ` | ${getEmployeeName(task.assigned_to)}` : ''}</p>
                      </div>
                    </div>
                    <div className="flex gap-1 flex-shrink-0">
                      {!isComplete && task.status !== 'in_progress' && (
                        <Button size="sm" variant="ghost" className="text-violet-400 hover:bg-violet-500/10" onClick={() => updateTask(task.id, 'in_progress')} disabled={taskLoading === task.id}>
                          {taskLoading === task.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        </Button>
                      )}
                      {task.status === 'in_progress' && (
                        <>
                          <Button size="sm" variant="ghost" className="text-green-400 hover:bg-green-500/10" onClick={() => updateTask(task.id, 'complete')} disabled={taskLoading === task.id}>
                            <CheckCircle className="w-4 h-4" />
                          </Button>
                          <Button size="sm" variant="ghost" className="text-orange-400 hover:bg-orange-500/10" onClick={() => updateTask(task.id, 'paused')} disabled={taskLoading === task.id}>
                            <Pause className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      {(task.status === 'paused' || task.status === 'on_hold') && (
                        <Button size="sm" variant="ghost" className="text-violet-400 hover:bg-violet-500/10" onClick={() => updateTask(task.id, 'in_progress')} disabled={taskLoading === task.id}>
                          <Play className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  {task.notes && <p className="text-sm text-gray-500 mt-2 ml-11">{task.notes}</p>}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {tab === 'drawings' && (
        <div className="space-y-4" data-testid="job-ticket-drawings-tab">
          <div className="flex items-center justify-between gap-3 rounded-xl border border-gray-200 bg-white p-4">
            <div>
              <p className="font-medium text-gray-900">Item Drawings</p>
              <p className="text-sm text-gray-500">Sketches, measurement notes, install notes, and image markups attached only to this item.</p>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-sm text-gray-600">Add Sketch/Notes</Label>
              <Button variant={drawingsEnabled ? 'default' : 'outline'} size="sm" onClick={() => setDrawingsEnabled((current) => !current)} data-testid="job-ticket-drawings-toggle-button">
                {drawingsEnabled ? 'Enabled' : 'Enable'}
              </Button>
            </div>
          </div>

          {(drawingsEnabled || ticketDrawings.length > 0) && (
            <Card className="bg-white border-gray-200">
              <CardContent className="p-4 space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-white" onClick={() => { setMarkupImage(null); setShowDrawingModal(true); }} data-testid="job-ticket-create-drawing-button">
                    <Pen className="w-4 h-4 mr-2" /> {latestDraftDrawing ? 'Resume Draft' : 'Create Drawing'}
                  </Button>
                </div>

                {orderFiles.length > 0 && (
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-gray-700">Markup Uploaded Images</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      {orderFiles.map((file) => (
                        <div key={file.id} className="rounded-xl border border-gray-200 p-3 flex items-center justify-between gap-3" data-testid={`job-ticket-markup-file-${file.id}`}>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">{file.label || file.filename}</p>
                            <p className="text-xs text-gray-500 truncate">{file.filename}</p>
                          </div>
                          <Button variant="outline" size="sm" onClick={() => {
                            buildImageMarkupPayload(file).then((payload) => {
                              setMarkupImage(payload);
                              setShowDrawingModal(true);
                            });
                          }} data-testid={`job-ticket-markup-button-${file.id}`}>
                            Markup
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => buildImageMarkupPayload(file).then(setPreviewFile)} data-testid={`job-ticket-preview-file-${file.id}`}>
                            <ImageIcon className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {ticketDrawings.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-6 text-center text-sm text-gray-500">No item drawings attached yet.</div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                    {ticketDrawings.map((drawing) => (
                      <button key={drawing.id} className="rounded-xl border border-gray-200 overflow-hidden text-left hover:border-violet-300 transition-colors" onClick={() => setPreviewDrawing(drawing)} data-testid={`job-ticket-drawing-${drawing.id}`}>
                        <div className="aspect-[4/3] bg-gray-50 flex items-center justify-center">
                          <img src={`${process.env.REACT_APP_BACKEND_URL}${drawing.image_url}`} alt={drawing.label} className="w-full h-full object-contain" />
                        </div>
                        <div className="p-3">
                          <p className="text-sm font-medium text-gray-900 truncate">{drawing.label}</p>
                          <p className="text-xs text-gray-500 mt-1">{drawing.type?.replace(/_/g, ' ')}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ARTWORK TAB */}
      {tab === 'artwork' && (
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardHeader><CardTitle className="text-gray-900 text-lg flex items-center gap-2"><FileImage className="w-5 h-5 text-violet-400" /> Artwork & Files</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { label: 'Artwork Status', value: fmt(ticket.artwork_status), color: ticket.artwork_status === 'complete' ? 'text-green-400' : 'text-yellow-400' },
                { label: 'Proof Status', value: fmt(ticket.proof_approval_status), color: ticket.proof_approval_status === 'approved' ? 'text-green-400' : 'text-amber-400' },
                { label: 'Revisions', value: ticket.revision_count || 0, color: 'text-gray-900' },
              ].map(f => (
                <div key={f.label} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 uppercase">{f.label}</p>
                  <p className={`text-lg font-bold mt-1 ${f.color}`}>{f.value}</p>
                </div>
              ))}
            </div>
            {[
              { label: 'Artwork Files', files: ticket.artwork_files },
              { label: 'Reference Images', files: ticket.reference_images },
              { label: 'Mockups', files: ticket.mockups },
              { label: 'Proof Files', files: ticket.proof_files },
              { label: 'Production Output', files: ticket.production_output_files },
            ].map(section => (
              <div key={section.label}>
                <p className="text-sm font-medium text-gray-700 mb-2">{section.label}</p>
                {section.files?.length > 0 ? (
                  <div className="flex flex-wrap gap-2">{section.files.map((f, i) => <Badge key={i} variant="outline" className="text-gray-700">{f}</Badge>)}</div>
                ) : (
                  <p className="text-sm text-gray-400">No files uploaded</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* NOTES TAB */}
      {tab === 'notes' && (
        <div className="space-y-4">
          {[
            { label: 'Special Instructions', value: ticket.special_instructions, icon: MessageSquare },
            { label: 'Production Notes', value: ticket.production_notes, icon: Wrench },
            { label: 'Install Notes', value: ticket.install_notes, icon: Wrench },
            { label: 'Packaging Notes', value: ticket.packaging_notes, icon: Package },
            { label: 'Rework Notes', value: ticket.rework_notes, icon: RotateCcw },
          ].map(n => (
            <Card key={n.label} className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <n.icon className="w-4 h-4 text-gray-500" />
                  <p className="text-sm font-medium text-gray-700">{n.label}</p>
                </div>
                <p className="text-gray-900 text-sm">{n.value || <span className="text-gray-400 italic">No notes</span>}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <TicketWorkflowShortcutDialog
        open={!!shortcutMode}
        mode={shortcutMode}
        ticket={ticket}
        order={orderSummary}
        employees={employees}
        onClose={() => setShortcutMode('')}
        onCompleted={load}
      />
      {showDrawingModal && (
        <DrawingModal
          orderId={ticket.order_id}
          parentType={markupImage ? 'uploaded_image' : 'job_ticket'}
          parentId={markupImage ? markupImage.id : ticket.id}
          jobTicketId={ticket.id}
          uploadedImage={markupImage}
          existingDrawing={!markupImage ? latestDraftDrawing : null}
          defaultType={markupImage ? 'markup' : 'sketch'}
          onClose={() => {
            setShowDrawingModal(false);
            setMarkupImage(null);
          }}
          onSaved={load}
        />
      )}
      {previewDrawing && (
        <DrawingPreviewModal drawing={previewDrawing} onClose={() => setPreviewDrawing(null)} onDeleted={load} isAdmin />
      )}
      <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
        <DialogContent className="sm:max-w-[760px]">
          <DialogHeader><DialogTitle>{previewFile?.label || 'Artwork Preview'}</DialogTitle></DialogHeader>
          {previewFile?.contentUrl && <img src={previewFile.contentUrl} alt={previewFile.label} className="w-full max-h-[70vh] object-contain rounded-lg" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
