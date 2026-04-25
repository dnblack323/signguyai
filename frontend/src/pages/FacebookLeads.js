import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  MessageSquare, Zap, AlertTriangle, CheckCircle, Clock, Search,
  Facebook, Loader2, RefreshCw, ExternalLink, ChevronDown, X,
  FileText, ShoppingCart, Eye, ThumbsDown, Filter
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const authHeader = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const URGENCY_COLORS = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  low: 'bg-gray-100 text-gray-600 border-gray-200',
};

const STATUS_FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'new', label: 'New' },
  { value: 'pending', label: 'Pending AI' },
  { value: 'lead_created', label: 'Lead Created' },
  { value: 'order_created', label: 'Order Created' },
  { value: 'reviewed', label: 'Reviewed' },
  { value: 'spam', label: 'Spam' },
];

const CLASSIFICATION_BADGE = {
  new_quote_request: { label: 'Quote Request', color: 'bg-blue-100 text-blue-700' },
  new_order_request: { label: 'Order Request', color: 'bg-green-100 text-green-700' },
  vehicle_wrap_request: { label: 'Vehicle Wrap', color: 'bg-purple-100 text-purple-700' },
  price_question: { label: 'Price Question', color: 'bg-cyan-100 text-cyan-700' },
  general_question: { label: 'General Q', color: 'bg-gray-100 text-gray-600' },
  spam_or_unrelated: { label: 'Spam', color: 'bg-red-100 text-red-500' },
  unknown: { label: 'Unclassified', color: 'bg-gray-100 text-gray-400' },
};

export default function FacebookLeads() {
  const [messages, setMessages] = useState([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMessages = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 50, skip: 0 };
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
      const [msgRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/facebook/messages`, { params, headers: authHeader() }),
        axios.get(`${API_URL}/api/facebook/messages/summary/stats`, { headers: authHeader() }),
      ]);
      setMessages(msgRes.data.messages || []);
      setTotal(msgRes.data.total || 0);
      setStats(statsRes.data);
    } catch (err) {
      if (err.response?.status !== 404) toast.error('Failed to load Facebook messages');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { fetchMessages(); }, [fetchMessages]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchMessages();
    setRefreshing(false);
  };

  const openDetail = (msg) => {
    setSelectedMessage(msg);
    setDetailOpen(true);
  };

  const filteredMessages = messages.filter(m =>
    !searchText || (m.message_text || '').toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Facebook className="h-7 w-7 text-blue-600" />
            Facebook Leads
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Incoming Messenger messages from your connected Business Pages
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing} data-testid="refresh-messages-btn">
          <RefreshCw className={`h-4 w-4 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-4 gap-3" data-testid="fb-stats">
          <StatCard label="Total" value={stats.total} icon={MessageSquare} color="blue" />
          <StatCard label="New" value={stats.new} icon={Zap} color="green" />
          <StatCard label="Needs Review" value={stats.needs_review} icon={Clock} color="amber" />
          <StatCard label="High Urgency" value={stats.high_urgency} icon={AlertTriangle} color="red" />
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search messages…"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            className="pl-9 h-9"
            data-testid="fb-search-input"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 h-9" data-testid="status-filter-select">
            <Filter className="h-3.5 w-3.5 mr-1 text-gray-400" />
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            {STATUS_FILTERS.map(f => (
              <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-sm text-gray-400">{total} total</span>
      </div>

      {/* Message list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-7 w-7 animate-spin text-blue-600" />
        </div>
      ) : filteredMessages.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Facebook className="h-10 w-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No Facebook messages yet</p>
            <p className="text-gray-400 text-sm mt-1">
              Connect a Facebook Business Page and messages will appear here.
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.href = '/settings/meta-integration'}
              data-testid="go-to-settings-btn"
            >
              Go to Integration Settings
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2" data-testid="fb-messages-list">
          {filteredMessages.map(msg => (
            <MessageRow
              key={msg.id}
              message={msg}
              onOpen={() => openDetail(msg)}
              onRefresh={fetchMessages}
            />
          ))}
        </div>
      )}

      {/* Message Detail Modal */}
      {selectedMessage && (
        <MessageDetailModal
          message={selectedMessage}
          open={detailOpen}
          onClose={() => { setDetailOpen(false); setSelectedMessage(null); }}
          onRefresh={fetchMessages}
        />
      )}
    </div>
  );
}

// ── Stat Card ──────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon: Icon, color }) {
  const colors = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    amber: 'bg-amber-50 border-amber-200 text-amber-700',
    red: 'bg-red-50 border-red-200 text-red-700',
  };
  return (
    <Card className={`border ${colors[color]}`}>
      <CardContent className="pt-3 pb-3 flex items-center gap-3">
        <Icon className="h-5 w-5 shrink-0" />
        <div>
          <p className="text-xl font-bold leading-none">{value ?? 0}</p>
          <p className="text-xs mt-0.5 opacity-70">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Message Row ────────────────────────────────────────────────────────────────
function MessageRow({ message: msg, onOpen, onRefresh }) {
  const [actioning, setActioning] = useState(false);
  const [processing, setProcessing] = useState(false);
  const clf = CLASSIFICATION_BADGE[msg.classification] || CLASSIFICATION_BADGE.unknown;

  const handleProcess = async (e) => {
    e.stopPropagation();
    setProcessing(true);
    try {
      await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/process`, {}, { headers: authHeader() });
      toast.success('AI processing complete');
      await onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const handleMarkSpam = async (e) => {
    e.stopPropagation();
    setActioning(true);
    try {
      await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/mark-spam`, {}, { headers: authHeader() });
      toast.success('Marked as spam');
      await onRefresh();
    } finally {
      setActioning(false);
    }
  };

  const statusBadge = {
    new: 'bg-blue-100 text-blue-700',
    pending: 'bg-gray-100 text-gray-500',
    lead_created: 'bg-green-100 text-green-700',
    order_created: 'bg-purple-100 text-purple-700',
    reviewed: 'bg-gray-100 text-gray-500',
    spam: 'bg-red-100 text-red-400 line-through',
    draft_created: 'bg-green-100 text-green-600',
  };

  return (
    <div
      className="flex items-start gap-4 p-4 rounded-xl border bg-white hover:bg-blue-50/30 hover:border-blue-200 cursor-pointer transition-all"
      onClick={onOpen}
      data-testid={`message-row-${msg.id}`}
    >
      {/* Avatar placeholder */}
      <div className="h-9 w-9 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
        <Facebook className="h-5 w-5 text-blue-600" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <span className="font-medium text-sm text-gray-800">Sender {msg.sender_id?.slice(-6)}</span>
          <Badge className={`text-xs border ${clf.color}`}>{clf.label}</Badge>
          {msg.urgency && msg.urgency !== 'low' && (
            <Badge className={`text-xs border ${URGENCY_COLORS[msg.urgency]}`}>
              {msg.urgency} urgency
            </Badge>
          )}
          {msg.confidence_score != null && (
            <span className="text-xs text-gray-400">
              {(msg.confidence_score * 100).toFixed(0)}% confidence
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 truncate">
          {msg.message_text || <em className="text-gray-400">Attachment only</em>}
        </p>
        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
          <span className="text-xs text-gray-400">
            {new Date(msg.received_at || msg.created_at).toLocaleString()}
          </span>
          {msg.missing_information?.length > 0 && (
            <span className="text-xs text-amber-600">
              {msg.missing_information.length} missing fields
            </span>
          )}
          <span className={`text-xs px-1.5 py-0.5 rounded-full ${statusBadge[msg.review_status] || 'bg-gray-100 text-gray-400'}`}>
            {msg.review_status?.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 shrink-0" onClick={e => e.stopPropagation()}>
        {msg.processing_status === 'pending' && (
          <Button size="sm" variant="outline" onClick={handleProcess} disabled={processing} className="h-7 text-xs">
            {processing ? <Loader2 className="h-3 w-3 animate-spin" /> : <><Zap className="h-3 w-3 mr-1" />AI</>}
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={handleMarkSpam} disabled={actioning} className="h-7 text-xs text-gray-400">
          <ThumbsDown className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── Message Detail Modal ───────────────────────────────────────────────────────
function MessageDetailModal({ message: initialMsg, open, onClose, onRefresh }) {
  const [msg, setMsg] = useState(initialMsg);
  const [creatingLead, setCreatingLead] = useState(false);
  const [creatingOrder, setCreatingOrder] = useState(false);
  const [markingReviewed, setMarkingReviewed] = useState(false);
  const [processingAI, setProcessingAI] = useState(false);
  const [suggestingReply, setSuggestingReply] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => { setMsg(initialMsg); }, [initialMsg]);

  const refreshMsg = async () => {
    const res = await axios.get(`${API_URL}/api/facebook/messages/${msg.id}`, { headers: authHeader() });
    setMsg(res.data);
    onRefresh();
  };

  const handleProcessAI = async () => {
    setProcessingAI(true);
    try {
      const res = await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/process`, {}, { headers: authHeader() });
      setMsg(m => ({ ...m, ...res.data, processing_status: 'processed' }));
      toast.success('AI classification complete');
      onRefresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'AI processing failed');
    } finally {
      setProcessingAI(false);
    }
  };

  const handleCreateLead = async () => {
    setCreatingLead(true);
    try {
      const res = await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/create-lead`, {}, { headers: authHeader() });
      toast.success('Draft lead created');
      await refreshMsg();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create lead');
    } finally {
      setCreatingLead(false);
    }
  };

  const handleCreateOrder = async () => {
    setCreatingOrder(true);
    try {
      await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/create-draft-order`, {}, { headers: authHeader() });
      toast.success('Draft order created');
      await refreshMsg();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create draft order');
    } finally {
      setCreatingOrder(false);
    }
  };

  const handleMarkReviewed = async () => {
    setMarkingReviewed(true);
    try {
      await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/mark-reviewed`, {}, { headers: authHeader() });
      toast.success('Marked as reviewed');
      await refreshMsg();
    } finally {
      setMarkingReviewed(false);
    }
  };

  const handleSuggestReply = async () => {
    setSuggestingReply(true);
    try {
      const res = await axios.post(`${API_URL}/api/facebook/messages/${msg.id}/suggest-reply`, {}, { headers: authHeader() });
      setMsg(m => ({ ...m, suggested_reply: res.data.suggested_reply }));
      toast.success('Reply suggestion updated');
    } finally {
      setSuggestingReply(false);
    }
  };

  const handleCopyReply = () => {
    if (!msg.suggested_reply) return;
    navigator.clipboard.writeText(msg.suggested_reply);
    setCopied(true);
    toast.success('Reply copied to clipboard');
    setTimeout(() => setCopied(false), 2500);
  };

  const clf = CLASSIFICATION_BADGE[msg.classification] || CLASSIFICATION_BADGE.unknown;
  const ext = msg.extracted_fields || {};

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="message-detail-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <Facebook className="h-5 w-5 text-blue-600" />
            Facebook Message Detail
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Message */}
          <div>
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="text-xs text-gray-400">Sender: {msg.sender_id}</span>
              <span className="text-xs text-gray-400">·</span>
              <span className="text-xs text-gray-400">{new Date(msg.received_at || msg.created_at).toLocaleString()}</span>
              {msg.classification && <Badge className={`text-xs ${clf.color}`}>{clf.label}</Badge>}
              {msg.urgency && msg.urgency !== 'low' && (
                <Badge className={`text-xs ${URGENCY_COLORS[msg.urgency]}`}>{msg.urgency} urgency</Badge>
              )}
              {msg.confidence_score != null && (
                <span className="text-xs text-gray-400">{(msg.confidence_score * 100).toFixed(0)}% confidence</span>
              )}
            </div>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
              <p className="text-sm text-gray-700 whitespace-pre-wrap" data-testid="message-text">
                {msg.message_text || <em className="text-gray-400">No text — attachment only</em>}
              </p>
              {msg.attachments?.length > 0 && (
                <div className="mt-2 flex gap-2 flex-wrap">
                  {msg.attachments.map((a, i) => (
                    <a key={i} href={a.url} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-blue-600 underline flex items-center gap-1">
                      <ExternalLink className="h-3 w-3" /> {a.type || 'attachment'}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* AI Extraction */}
          {msg.extracted_fields && Object.keys(ext).some(k => ext[k] && k !== 'confidence_score' && k !== 'missing_information') && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">AI Extracted Details</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {[
                  ['Product', ext.product_type],
                  ['Quantity', ext.quantity],
                  ['Size', ext.size],
                  ['Material', ext.material],
                  ['Deadline', ext.requested_deadline],
                  ['Budget', ext.budget_mentioned],
                  ['Phone', ext.phone_number],
                  ['Email', ext.email_address],
                  ['Vehicle', [ext.vehicle_year, ext.vehicle_make, ext.vehicle_model].filter(Boolean).join(' ')],
                  ['Wrap Type', ext.wrap_type],
                  ['Delivery', ext.delivery_preference],
                ].filter(([, v]) => v).map(([k, v]) => (
                  <div key={k} className="flex gap-2">
                    <span className="text-gray-400 text-xs w-16 shrink-0">{k}:</span>
                    <span className="text-gray-700 text-xs font-medium">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing info */}
          {msg.missing_information?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-amber-700 mb-1.5 flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" /> Missing Information
              </p>
              <ul className="text-xs text-amber-700 space-y-0.5 list-disc list-inside">
                {msg.missing_information.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          )}

          {/* Suggested reply */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Suggested Reply</p>
              <Button size="sm" variant="ghost" onClick={handleSuggestReply} disabled={suggestingReply} className="h-6 text-xs text-blue-600">
                {suggestingReply ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <RefreshCw className="h-3 w-3 mr-1" />}
                Regenerate
              </Button>
            </div>
            {msg.suggested_reply ? (
              <div className="bg-gray-50 border rounded-lg p-3 relative">
                <p className="text-sm text-gray-700 pr-16" data-testid="suggested-reply">{msg.suggested_reply}</p>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCopyReply}
                  className="absolute top-2 right-2 h-7 text-xs"
                  data-testid="copy-reply-btn"
                >
                  {copied ? <CheckCircle className="h-3.5 w-3.5 text-green-600" /> : 'Copy'}
                </Button>
              </div>
            ) : (
              <p className="text-xs text-gray-400 italic">No suggestion yet — click Regenerate.</p>
            )}
          </div>

          {/* Linked records */}
          {(msg.linked_lead_id || msg.linked_order_id) && (
            <div className="flex items-center gap-3 text-xs text-gray-500 bg-green-50 border border-green-200 rounded-lg p-2.5">
              <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
              {msg.linked_lead_id && <span>Lead created (ID: {msg.linked_lead_id.slice(-8)})</span>}
              {msg.linked_order_id && <span>Draft order created (ID: {msg.linked_order_id.slice(-8)})</span>}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 flex-wrap pt-2 border-t">
            {msg.processing_status !== 'processed' && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleProcessAI}
                disabled={processingAI}
                data-testid="process-ai-btn"
              >
                {processingAI ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Zap className="h-4 w-4 mr-1.5" />}
                Run AI
              </Button>
            )}

            {!msg.linked_lead_id && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleCreateLead}
                disabled={creatingLead}
                data-testid="create-lead-btn"
                className="text-blue-700 border-blue-300"
              >
                {creatingLead ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <FileText className="h-4 w-4 mr-1.5" />}
                Create Lead
              </Button>
            )}

            {!msg.linked_order_id && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleCreateOrder}
                disabled={creatingOrder}
                data-testid="create-draft-order-btn"
                className="text-purple-700 border-purple-300"
              >
                {creatingOrder ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <ShoppingCart className="h-4 w-4 mr-1.5" />}
                Create Draft Order
              </Button>
            )}

            {msg.review_status !== 'reviewed' && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleMarkReviewed}
                disabled={markingReviewed}
                data-testid="mark-reviewed-btn"
                className="text-gray-600"
              >
                {markingReviewed ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : <Eye className="h-4 w-4 mr-1.5" />}
                Mark Reviewed
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
