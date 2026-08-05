import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
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
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { Plus, Edit2, CheckCircle, AlertTriangle, Eye, CreditCard, Send, Search, Copy, ExternalLink, Mail, Loader2, Check } from 'lucide-react';
import { toast } from 'sonner';
import InvoicePreviewModal from '../components/InvoicePreviewModal';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const statusOptions = ['draft', 'sent', 'paid', 'overdue'];

export default function Invoices() {
  const { hasPermission } = useAuth();
  const canViewInvoices = hasPermission(Permission.INVOICES_VIEW);
  const canEditInvoices = hasPermission(Permission.INVOICES_CREATE);
  
  const { 
    invoices, customers, jobs, fetchInvoices, fetchCustomers, fetchJobs,
    createInvoice, updateInvoice 
  } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [verifyingSessionId, setVerifyingSessionId] = useState('');
  const [formData, setFormData] = useState({
    customer_id: '',
    job_id: '',
    total: '',
    status: 'draft',
    due_date: '',
    notes: ''
  });
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);

  // Payment link modal state
  const [payLinkModalOpen, setPayLinkModalOpen] = useState(false);
  const [payLinkInvoice, setPayLinkInvoice] = useState(null);
  const [payLinkData, setPayLinkData] = useState(null); // { url, customer_email, ... }
  const [payLinkEmail, setPayLinkEmail] = useState('');
  const [payLinkLoading, setPayLinkLoading] = useState(false);
  const [payLinkSending, setPayLinkSending] = useState(false);
  const [copied, setCopied] = useState(false);
  
  useEffect(() => {
    if (canViewInvoices) {
      loadData();
    }
  }, [statusFilter, canViewInvoices]);

  useEffect(() => {
    if (!canViewInvoices) return;

    const params = new URLSearchParams(window.location.search);
    const paymentStatus = params.get('payment');
    const sessionId = params.get('session_id');
    if (!paymentStatus) return;

    const clearUrlParams = () => {
      window.history.replaceState({}, document.title, window.location.pathname);
    };

    if (paymentStatus === 'cancelled') {
      toast.warning('Payment was cancelled');
      clearUrlParams();
      return;
    }

    if (paymentStatus !== 'success' || !sessionId) {
      clearUrlParams();
      return;
    }

    let cancelled = false;
    const verifySession = async () => {
      setVerifyingSessionId(sessionId);
      try {
        const token = getAuthToken();
        let paid = false;

        for (let attempt = 0; attempt < 6; attempt += 1) {
          if (cancelled) return;
          try {
            const response = await axios.get(`${API_URL}/api/stripe-connect/payment-status/${sessionId}`, {
              headers: token ? { Authorization: `Bearer ${token}` } : undefined,
            });

            if (response.data?.payment_status === 'paid') {
              paid = true;
              break;
            }
          } catch (error) {
            if (attempt === 5) {
              console.error('Invoice payment verification failed:', error);
            }
          }

          await new Promise((resolve) => setTimeout(resolve, 1500));
        }

        await loadData();
        if (!cancelled) {
          if (paid) {
            toast.success('Payment confirmed and invoice status refreshed');
          } else {
            toast.warning('Payment is still processing. It will appear once Stripe confirms it.');
          }
        }
      } finally {
        if (!cancelled) {
          setVerifyingSessionId('');
          clearUrlParams();
        }
      }
    };

    verifySession();
    return () => {
      cancelled = true;
    };
  }, [canViewInvoices]);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter !== 'all') params.status = statusFilter;

      const token = getAuthToken();
      try {
        await axios.post(`${API_URL}/api/stripe-connect/reconcile-invoices`, {}, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
      } catch (reconcileErr) {
        console.warn('Stripe invoice reconciliation skipped:', reconcileErr?.response?.data || reconcileErr?.message);
      }

      await Promise.all([fetchInvoices(params), fetchCustomers(), fetchJobs()]);
    } finally {
      setLoading(false);
    }
  };

  // Permission denied view
  if (!canViewInvoices) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4" style={{ color: '#d97706' }} />
        <h2 className="text-xl font-semibold mb-2 text-gray-900">Access Denied</h2>
        <p className="text-gray-500">You don't have permission to view invoices.</p>
      </div>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id) {
      toast.error('Please select a customer');
      return;
    }
    const totalAmount = parseFloat(formData.total) || 0;
    if (totalAmount <= 0) {
      toast.error('Total amount must be greater than 0');
      return;
    }
    try {
      if (editingInvoice) {
        await updateInvoice(editingInvoice.id, {
          total: totalAmount,
          status: formData.status,
          due_date: formData.due_date || null,
          notes: formData.notes
        });
        toast.success('Invoice updated');
      } else {
        await createInvoice({ ...formData, total: totalAmount });
        toast.success('Invoice created');
      }
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save invoice');
    }
  };

  const handleMarkPaid = async (invoiceId) => {
    try {
      await updateInvoice(invoiceId, { status: 'paid' });
      toast.success('Invoice marked as paid');
    } catch (err) {
      toast.error('Failed to update invoice');
    }
  };

  const handleEdit = (invoice) => {
    setEditingInvoice(invoice);
    setFormData({
      customer_id: invoice.customer_id,
      job_id: invoice.job_id || '',
      total: invoice.total,
      status: invoice.status,
      due_date: invoice.due_date || '',
      notes: invoice.notes || ''
    });
    setIsDialogOpen(true);
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      job_id: '',
      total: '',
      status: 'draft',
      due_date: '',
      notes: ''
    });
    setEditingInvoice(null);
    setIsDialogOpen(false);
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || 'Unknown';
  };

  const getJobName = (jobId) => {
    if (!jobId) return '-';
    const job = jobs.find(j => j.id === jobId);
    return job?.name || 'Unknown';
  };

  const handleOpenPayLinkModal = async (invoice) => {
    // Look up customer email from customers list
    const customer = customers.find(c => c.id === invoice.customer_id);
    setPayLinkInvoice(invoice);
    setPayLinkEmail(customer?.email || '');
    setPayLinkData(null);
    setCopied(false);
    setPayLinkModalOpen(true);

    // Auto-generate the link when the modal opens
    await generatePaymentLink(invoice, customer?.email || '');
  };

  const generatePaymentLink = async (invoice, email) => {
    setPayLinkLoading(true);
    try {
      const token = getAuthToken();
      const response = await axios.post(
        `${API_URL}/api/stripe-connect/invoice/${invoice.id}/send-payment-link`,
        { customer_email: email || null },
        { params: { origin_url: window.location.origin }, headers: { Authorization: `Bearer ${token}` } }
      );
      setPayLinkData(response.data);
      setPayLinkEmail(response.data.customer_email || email || '');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate payment link';
      if (msg.includes('not connected')) {
        toast.error('Connect your Stripe account in Payment Settings first');
      } else {
        toast.error(msg);
      }
      setPayLinkModalOpen(false);
    } finally {
      setPayLinkLoading(false);
    }
  };

  const handleCopyLink = () => {
    if (!payLinkData?.url) return;
    navigator.clipboard.writeText(payLinkData.url);
    setCopied(true);
    toast.success('Payment link copied!');
    setTimeout(() => setCopied(false), 2500);
  };

  const handleSendEmail = async () => {
    if (!payLinkInvoice || !payLinkEmail) return;
    setPayLinkSending(true);
    try {
      const token = getAuthToken();
      const response = await axios.post(
        `${API_URL}/api/stripe-connect/invoice/${payLinkInvoice.id}/send-payment-link`,
        { customer_email: payLinkEmail },
        { params: { origin_url: window.location.origin }, headers: { Authorization: `Bearer ${token}` } }
      );
      setPayLinkData(response.data);
      if (response.data.email_sent) {
        toast.success(`Payment link sent to ${payLinkEmail}`);
      } else {
        toast.warning('Email service not configured — link generated but not sent. Copy and share manually.');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send payment link');
    } finally {
      setPayLinkSending(false);
    }
  };

  // Calculate totals
  const totals = invoices.reduce((acc, inv) => {
    acc.all += inv.total;
    if (inv.status === 'paid') acc.paid += inv.total;
    if (inv.status === 'overdue') acc.overdue += inv.total;
    if (inv.status === 'sent') acc.pending += inv.total;
    return acc;
  }, { all: 0, paid: 0, overdue: 0, pending: 0 });

  return (
    <div className="space-y-6 animate-fade-in" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight text-gray-900">Invoices</h1>
          <p className="text-gray-700 mt-1">{invoices.length} total invoices</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-invoice-btn" onClick={() => resetForm()}>
              <Plus className="h-4 w-4 mr-2" /> New Invoice
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">
                {editingInvoice ? 'Edit Invoice' : 'New Invoice'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Customer *</Label>
                  <Select
                    value={formData.customer_id}
                    onValueChange={(val) => setFormData({ ...formData, customer_id: val })}
                    disabled={!!editingInvoice}
                  >
                    <SelectTrigger data-testid="invoice-customer-select">
                      <SelectValue placeholder="Select customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {customers.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Linked Job</Label>
                  <Select
                    value={formData.job_id || 'none'}
                    onValueChange={(val) => setFormData({ ...formData, job_id: val === 'none' ? '' : val })}
                    disabled={!!editingInvoice}
                  >
                    <SelectTrigger data-testid="invoice-job-select">
                      <SelectValue placeholder="Select job (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {jobs.filter(j => j.customer_id === formData.customer_id).map((j) => (
                        <SelectItem key={j.id} value={j.id}>
                          {j.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Total Amount *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={formData.total}
                    onChange={(e) => setFormData({ ...formData, total: e.target.value })}
                    data-testid="invoice-total-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(val) => setFormData({ ...formData, status: val })}
                  >
                    <SelectTrigger data-testid="invoice-status-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s.charAt(0).toUpperCase() + s.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  data-testid="invoice-due-date-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  data-testid="invoice-notes-input"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="invoice-submit-btn">
                  {editingInvoice ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Summary Cards */}
      {verifyingSessionId && (
        <Card className="bg-blue-50 border-blue-200" data-testid="invoice-payment-verification-banner">
          <CardContent className="py-3 text-sm text-blue-800">
            Verifying Stripe payment status for session <span className="font-mono">{verifyingSessionId.slice(0, 18)}...</span>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Total</p>
            <p className="text-2xl font-bold">{formatCurrency(totals.all)}</p>
          </CardContent>
        </Card>
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Paid</p>
            <p className="text-2xl font-bold text-green-400">{formatCurrency(totals.paid)}</p>
          </CardContent>
        </Card>
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Pending</p>
            <p className="text-2xl font-bold text-yellow-400">{formatCurrency(totals.pending)}</p>
          </CardContent>
        </Card>
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Overdue</p>
            <p className="text-2xl font-bold text-red-400">{formatCurrency(totals.overdue)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="p-4 flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search invoices..."
              className="pl-9"
              data-testid="invoices-search-input"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]" data-testid="invoice-filter-status">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {statusOptions.map((s) => (
                <SelectItem key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Invoice List */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No invoices found</p>
              <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                Create your first invoice
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Invoice #</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Order</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.filter(invoice => {
                  if (!searchQuery.trim()) return true;
                  const q = searchQuery.toLowerCase();
                  const customerName = (customers.find(c => c.id === invoice.customer_id)?.name || '').toLowerCase();
                  const jobName = (jobs.find(j => j.id === invoice.job_id)?.name || '').toLowerCase();
                  return (
                    customerName.includes(q) ||
                    jobName.includes(q) ||
                    (invoice.id || '').toLowerCase().includes(q) ||
                    (invoice.status || '').toLowerCase().includes(q) ||
                    (invoice.notes || '').toLowerCase().includes(q)
                  );
                }).map((invoice, idx) => (
                  <TableRow 
                    key={invoice.id} 
                    className={idx % 2 === 0 ? 'bg-transparent' : 'bg-gray-50'}
                    data-testid={`invoice-row-${invoice.id}`}
                  >
                    <TableCell className="font-mono text-sm">
                      #{invoice.id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {getCustomerName(invoice.customer_id)}
                    </TableCell>
                    <TableCell className="text-gray-500">
                      {getJobName(invoice.job_id)}
                    </TableCell>
                    <TableCell className="font-bold">{formatCurrency(invoice.total)}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(invoice.status)}>
                        {invoice.status === 'overdue' && <AlertTriangle className="h-3 w-3 mr-1" />}
                        {invoice.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-500 text-sm">
                      {formatDate(invoice.due_date)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setPreviewInvoiceId(invoice.id);
                            setIsInvoiceModalOpen(true);
                          }}
                          data-testid={`view-invoice-${invoice.id}`}
                        >
                          <Eye className="h-4 w-4 mr-1" /> View
                        </Button>
                        {invoice.status !== 'paid' && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenPayLinkModal(invoice)}
                              data-testid={`pay-invoice-${invoice.id}`}
                              className="text-primary border-primary/50"
                            >
                              <Send className="h-4 w-4 mr-1" /> Send Pay Link
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleMarkPaid(invoice.id)}
                              data-testid={`mark-paid-${invoice.id}`}
                              className="text-green-400 border-green-400/50"
                            >
                              <CheckCircle className="h-4 w-4 mr-1" /> Mark Paid
                            </Button>
                          </>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(invoice)}
                          data-testid={`edit-invoice-${invoice.id}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Invoice Preview Modal */}
      <InvoicePreviewModal
        invoiceId={previewInvoiceId}
        isOpen={isInvoiceModalOpen}
        onClose={() => {
          setIsInvoiceModalOpen(false);
          setPreviewInvoiceId(null);
        }}
      />

      {/* Send Payment Link Modal */}
      <Dialog open={payLinkModalOpen} onOpenChange={setPayLinkModalOpen}>
        <DialogContent className="max-w-md" data-testid="payment-link-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              Send Payment Link
            </DialogTitle>
          </DialogHeader>

          {payLinkLoading ? (
            <div className="flex flex-col items-center py-10 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm text-gray-500">Generating secure payment link…</p>
            </div>
          ) : payLinkData ? (
            <div className="space-y-5">
              {/* Amount chip */}
              <div className="rounded-lg bg-primary/10 border border-primary/20 px-4 py-3 text-center">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Amount Due</p>
                <p className="text-2xl font-bold text-primary" data-testid="pay-link-amount">
                  {formatCurrency(payLinkData.amount)}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">Invoice #{payLinkData.invoice_number}</p>
              </div>

              {/* Copy link row */}
              <div>
                <Label className="text-xs text-gray-500 mb-1.5 block">Payment Link</Label>
                <div className="flex gap-2">
                  <Input
                    readOnly
                    value={payLinkData.url}
                    className="text-xs font-mono bg-gray-50"
                    data-testid="pay-link-url-input"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyLink}
                    data-testid="pay-link-copy-btn"
                    className={copied ? 'text-green-600 border-green-400' : ''}
                  >
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.open(payLinkData.url, '_blank')}
                    data-testid="pay-link-open-btn"
                    title="Open in new tab"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Email row */}
              <div>
                <Label className="text-xs text-gray-500 mb-1.5 block">Send to Customer Email</Label>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="customer@example.com"
                    value={payLinkEmail}
                    onChange={e => setPayLinkEmail(e.target.value)}
                    data-testid="pay-link-email-input"
                  />
                  <Button
                    size="sm"
                    onClick={handleSendEmail}
                    disabled={payLinkSending || !payLinkEmail}
                    data-testid="pay-link-send-btn"
                    className="shrink-0"
                  >
                    {payLinkSending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <><Mail className="h-4 w-4 mr-1" /> Send</>
                    )}
                  </Button>
                </div>
                {payLinkData.email_sent && (
                  <p className="text-xs text-green-600 mt-1.5 flex items-center gap-1" data-testid="pay-link-email-sent">
                    <Check className="h-3 w-3" /> Email sent to {payLinkData.customer_email}
                  </p>
                )}
              </div>

              <p className="text-xs text-gray-400 border-t pt-3">
                Your customer does not need an account to pay — the link goes directly to a secure Stripe checkout page.
              </p>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
