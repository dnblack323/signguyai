import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
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
import { 
  Plus, Search, Edit2, ArrowRightCircle, Trash2, Eye,
  Printer, Mail, Building2, Phone, Calendar, FileText,
  CheckCircle, XCircle
} from 'lucide-react';
import { toast } from 'sonner';

const statusOptions = ['draft', 'sent', 'approved', 'declined'];

export default function Quotes() {
  const { 
    quotes, customers, fetchQuotes, fetchCustomers, 
    createQuote, updateQuote, convertQuoteToJob 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingQuote, setEditingQuote] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: '',
    notes: '',
    status: 'draft',
    line_items: [{ description: '', quantity: 1, unit_price: 0 }]
  });

  // Quote preview modal state
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    await Promise.all([fetchQuotes(params), fetchCustomers()]);
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id) {
      toast.error('Please select a customer');
      return;
    }
    try {
      if (editingQuote) {
        await updateQuote(editingQuote.id, {
          line_items: formData.line_items,
          notes: formData.notes,
          status: formData.status
        });
        toast.success('Quote updated');
      } else {
        await createQuote(formData);
        toast.success('Quote created');
      }
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save quote');
    }
  };

  const handleConvert = async (quoteId) => {
    if (window.confirm('Convert this quote to a job?')) {
      try {
        await convertQuoteToJob(quoteId);
        toast.success('Quote converted to job');
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Failed to convert quote');
      }
    }
  };

  const handleEdit = (quote) => {
    if (quote.job_id) {
      toast.error('Cannot edit quote that has been converted to job');
      return;
    }
    setEditingQuote(quote);
    setFormData({
      customer_id: quote.customer_id,
      notes: quote.notes || '',
      status: quote.status,
      line_items: quote.line_items.length > 0 ? quote.line_items : [{ description: '', quantity: 1, unit_price: 0 }]
    });
    setIsDialogOpen(true);
  };

  const addLineItem = () => {
    setFormData({
      ...formData,
      line_items: [...formData.line_items, { description: '', quantity: 1, unit_price: 0 }]
    });
  };

  const updateLineItem = (index, field, value) => {
    const newItems = [...formData.line_items];
    newItems[index][field] = field === 'quantity' || field === 'unit_price' ? parseFloat(value) || 0 : value;
    setFormData({ ...formData, line_items: newItems });
  };

  const removeLineItem = (index) => {
    if (formData.line_items.length > 1) {
      const newItems = formData.line_items.filter((_, i) => i !== index);
      setFormData({ ...formData, line_items: newItems });
    }
  };

  const calculateTotal = () => {
    return formData.line_items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      notes: '',
      status: 'draft',
      line_items: [{ description: '', quantity: 1, unit_price: 0 }]
    });
    setEditingQuote(null);
    setIsDialogOpen(false);
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || 'Unknown';
  };

  const getCustomer = (customerId) => {
    return customers.find(c => c.id === customerId);
  };

  const handleViewQuote = (quote) => {
    setSelectedQuote(quote);
    setIsPreviewOpen(true);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleEmail = async () => {
    const customer = getCustomer(selectedQuote?.customer_id);
    if (!customer?.email) {
      toast.error('Customer has no email address');
      return;
    }
    // For now, show a toast with instructions
    // In production, this would integrate with an email service
    toast.success(`Quote ready to email to ${customer.email}. Email integration coming soon!`);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="quotes-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Quotes</h1>
          <p className="text-muted-foreground mt-1">{quotes.length} total quotes</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-quote-btn" onClick={() => resetForm()}>
              <Plus className="h-4 w-4 mr-2" /> New Quote
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">
                {editingQuote ? 'Edit Quote' : 'New Quote'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Customer *</Label>
                  <Select
                    value={formData.customer_id}
                    onValueChange={(val) => setFormData({ ...formData, customer_id: val })}
                    disabled={!!editingQuote}
                  >
                    <SelectTrigger data-testid="quote-customer-select">
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
                  <Label>Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(val) => setFormData({ ...formData, status: val })}
                  >
                    <SelectTrigger data-testid="quote-status-select">
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

              {/* Line Items */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Line Items</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addLineItem}>
                    <Plus className="h-3 w-3 mr-1" /> Add Item
                  </Button>
                </div>
                {formData.line_items.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end">
                    <div className="col-span-6">
                      <Input
                        placeholder="Description"
                        value={item.description}
                        onChange={(e) => updateLineItem(idx, 'description', e.target.value)}
                        data-testid={`line-item-desc-${idx}`}
                      />
                    </div>
                    <div className="col-span-2">
                      <Input
                        type="number"
                        placeholder="Qty"
                        value={item.quantity}
                        onChange={(e) => updateLineItem(idx, 'quantity', e.target.value)}
                        data-testid={`line-item-qty-${idx}`}
                      />
                    </div>
                    <div className="col-span-3">
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="Price"
                        value={item.unit_price}
                        onChange={(e) => updateLineItem(idx, 'unit_price', e.target.value)}
                        data-testid={`line-item-price-${idx}`}
                      />
                    </div>
                    <div className="col-span-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => removeLineItem(idx)}
                        disabled={formData.line_items.length === 1}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
                <div className="text-right font-bold text-lg">
                  Total: {formatCurrency(calculateTotal())}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  data-testid="quote-notes-input"
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="quote-submit-btn">
                  {editingQuote ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]" data-testid="quote-filter-status">
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

      {/* Quotes List */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : quotes.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No quotes found</p>
              <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                Create your first quote
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Quote #</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quotes.map((quote, idx) => (
                  <TableRow 
                    key={quote.id} 
                    className={`cursor-pointer transition-colors ${idx % 2 === 0 ? 'bg-transparent' : 'bg-muted/30'} hover:bg-muted/50`}
                    data-testid={`quote-row-${quote.id}`}
                    onClick={() => handleViewQuote(quote)}
                  >
                    <TableCell className="font-mono text-sm">
                      #{quote.id.slice(0, 8)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {getCustomerName(quote.customer_id)}
                    </TableCell>
                    <TableCell>{quote.line_items.length} items</TableCell>
                    <TableCell className="font-bold">{formatCurrency(quote.total)}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(quote.status)}>
                        {quote.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(quote.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleViewQuote(quote)}
                          data-testid={`view-quote-${quote.id}`}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {!quote.job_id && quote.status === 'approved' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleConvert(quote.id)}
                            data-testid={`convert-quote-${quote.id}`}
                            className="text-primary border-primary/50"
                          >
                            <ArrowRightCircle className="h-4 w-4 mr-1" /> To Job
                          </Button>
                        )}
                        {quote.job_id && (
                          <Badge variant="outline" className="text-green-400 border-green-400/50">
                            Converted
                          </Badge>
                        )}
                        {!quote.job_id && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(quote)}
                            data-testid={`edit-quote-${quote.id}`}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        )}
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
