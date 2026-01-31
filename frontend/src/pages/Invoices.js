import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
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
import { Plus, Edit2, CheckCircle, AlertTriangle, Eye } from 'lucide-react';
import { toast } from 'sonner';
import InvoicePreviewModal from '../components/InvoicePreviewModal';

const statusOptions = ['draft', 'sent', 'paid', 'overdue'];

export default function Invoices() {
  const { 
    invoices, customers, jobs, fetchInvoices, fetchCustomers, fetchJobs,
    createInvoice, updateInvoice 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: '',
    job_id: '',
    total: 0,
    status: 'draft',
    due_date: '',
    notes: ''
  });
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    await Promise.all([fetchInvoices(params), fetchCustomers(), fetchJobs()]);
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id) {
      toast.error('Please select a customer');
      return;
    }
    try {
      if (editingInvoice) {
        await updateInvoice(editingInvoice.id, {
          total: formData.total,
          status: formData.status,
          due_date: formData.due_date || null,
          notes: formData.notes
        });
        toast.success('Invoice updated');
      } else {
        await createInvoice(formData);
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
      total: 0,
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
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Invoices</h1>
          <p className="text-muted-foreground mt-1">{invoices.length} total invoices</p>
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
                    value={formData.job_id}
                    onValueChange={(val) => setFormData({ ...formData, job_id: val })}
                    disabled={!!editingInvoice}
                  >
                    <SelectTrigger data-testid="invoice-job-select">
                      <SelectValue placeholder="Select job (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
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
                    value={formData.total}
                    onChange={(e) => setFormData({ ...formData, total: parseFloat(e.target.value) || 0 })}
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Total</p>
            <p className="text-2xl font-bold">{formatCurrency(totals.all)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Paid</p>
            <p className="text-2xl font-bold text-green-400">{formatCurrency(totals.paid)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Pending</p>
            <p className="text-2xl font-bold text-yellow-400">{formatCurrency(totals.pending)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">Overdue</p>
            <p className="text-2xl font-bold text-red-400">{formatCurrency(totals.overdue)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-4">
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
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
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
                  <TableHead>Job</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((invoice, idx) => (
                  <TableRow 
                    key={invoice.id} 
                    className={idx % 2 === 0 ? 'bg-transparent' : 'bg-muted/30'}
                    data-testid={`invoice-row-${invoice.id}`}
                  >
                    <TableCell className="font-mono text-sm">
                      #{invoice.id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {getCustomerName(invoice.customer_id)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {getJobName(invoice.job_id)}
                    </TableCell>
                    <TableCell className="font-bold">{formatCurrency(invoice.total)}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(invoice.status)}>
                        {invoice.status === 'overdue' && <AlertTriangle className="h-3 w-3 mr-1" />}
                        {invoice.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
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
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleMarkPaid(invoice.id)}
                            data-testid={`mark-paid-${invoice.id}`}
                            className="text-green-400 border-green-400/50"
                          >
                            <CheckCircle className="h-4 w-4 mr-1" /> Mark Paid
                          </Button>
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
    </div>
  );
}
