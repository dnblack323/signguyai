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
  CheckCircle, XCircle, Link, Copy, Check, Calculator
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import PricingCalculatorModal from '../components/PricingCalculatorModal';

const statusOptions = ['draft', 'sent', 'approved', 'declined'];
const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function Quotes() {
  const { 
    quotes, customers, fetchQuotes, fetchCustomers, 
    createQuote, updateQuote, convertQuoteToJob 
  } = useApp();
  const { token } = useAuth();
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
  const [generatingLink, setGeneratingLink] = useState(false);
  const [portalLink, setPortalLink] = useState(null);
  const [linkCopied, setLinkCopied] = useState(false);
  
  // Pricing calculator modal state
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);

  // Handle calculated item from pricing calculator
  const handleCalculatedItem = (calculatedData) => {
    // Add the calculated item to line items
    const newItem = {
      description: calculatedData.description || `${calculatedData.category} - Qty ${calculatedData.quantity}`,
      quantity: calculatedData.quantity || 1,
      unit_price: calculatedData.unit_price || calculatedData.suggested_price || 0
    };
    
    // If the last item is empty, replace it; otherwise add a new one
    const lastItem = formData.line_items[formData.line_items.length - 1];
    if (lastItem && !lastItem.description && lastItem.quantity === 1 && lastItem.unit_price === 0) {
      const newItems = [...formData.line_items];
      newItems[newItems.length - 1] = newItem;
      setFormData({ ...formData, line_items: newItems });
    } else {
      setFormData({ ...formData, line_items: [...formData.line_items, newItem] });
    }
    
    setIsCalculatorOpen(false);
    toast.success('Item added from calculator!');
  };

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
    setPortalLink(null);
    setLinkCopied(false);
    setIsPreviewOpen(true);
  };

  const handleGenerateShareLink = async () => {
    if (!selectedQuote) return;
    
    setGeneratingLink(true);
    try {
      const customer = getCustomer(selectedQuote.customer_id);
      const response = await fetch(`${API_URL}/api/magic-links`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          resource_type: 'quote',
          resource_id: selectedQuote.id,
          customer_email: customer?.email || null,
          expires_in_days: 7
        })
      });

      if (response.ok) {
        const data = await response.json();
        const link = `${window.location.origin}/portal/${data.token}`;
        setPortalLink(link);
        toast.success('Share link created (expires in 7 days)');
      } else {
        toast.error('Failed to generate share link');
      }
    } catch (err) {
      toast.error('Failed to generate share link');
    } finally {
      setGeneratingLink(false);
    }
  };

  const handleCopyLink = async () => {
    if (portalLink) {
      await navigator.clipboard.writeText(portalLink);
      setLinkCopied(true);
      toast.success('Link copied to clipboard');
      setTimeout(() => setLinkCopied(false), 2000);
    }
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

              {/* Calculator Shortcut */}
              <div className="p-3 bg-teal-500/10 border border-teal-500/30 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    <p className="text-teal-400 font-medium">Need to calculate pricing?</p>
                    <p className="text-muted-foreground text-xs mt-0.5">Use the pricing calculator for accurate quotes</p>
                  </div>
                  <Button 
                    type="button"
                    variant="outline" 
                    size="sm"
                    className="border-teal-500/50 text-teal-500 hover:bg-teal-500/10"
                    onClick={() => setIsCalculatorOpen(true)}
                    data-testid="quote-open-calculator-btn"
                  >
                    <Calculator className="h-4 w-4 mr-1" /> Calculate
                  </Button>
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

      {/* Quote Preview Modal */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto print:max-w-full print:max-h-full print:overflow-visible" data-testid="quote-preview-modal">
          <DialogHeader className="print:hidden">
            <div className="flex items-center justify-between">
              <DialogTitle className="font-heading uppercase flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Quote Preview
              </DialogTitle>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleGenerateShareLink}
                  disabled={generatingLink}
                  data-testid="share-quote-btn"
                >
                  <Link className="h-4 w-4 mr-2" /> 
                  {generatingLink ? 'Creating...' : 'Share Link'}
                </Button>
                <Button variant="outline" size="sm" onClick={handleEmail} data-testid="email-quote-btn">
                  <Mail className="h-4 w-4 mr-2" /> Email
                </Button>
                <Button variant="outline" size="sm" onClick={handlePrint} data-testid="print-quote-btn">
                  <Printer className="h-4 w-4 mr-2" /> Print
                </Button>
              </div>
            </div>
            {/* Share Link Display */}
            {portalLink && (
              <div className="mt-3 p-3 bg-teal-500/10 border border-teal-500/30 rounded-lg">
                <p className="text-sm text-[var(--text-secondary)] mb-2">Customer portal link (expires in 7 days):</p>
                <div className="flex items-center gap-2">
                  <Input 
                    value={portalLink} 
                    readOnly 
                    className="text-xs bg-[var(--input-bg)] border-[var(--input-border)]"
                  />
                  <Button 
                    size="sm" 
                    onClick={handleCopyLink}
                    className="bg-teal-500 hover:bg-teal-600"
                  >
                    {linkCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            )}
          </DialogHeader>

          {selectedQuote && (() => {
            const customer = getCustomer(selectedQuote.customer_id);
            const statusIcon = selectedQuote.status === 'approved' ? (
              <CheckCircle className="h-5 w-5 text-green-400" />
            ) : selectedQuote.status === 'declined' ? (
              <XCircle className="h-5 w-5 text-red-400" />
            ) : null;

            return (
              <div className="quote-preview space-y-6 p-4 bg-background rounded-lg border print:border-none print:p-0">
                {/* Quote Header */}
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-2xl font-bold font-heading uppercase tracking-tight text-primary">
                      QUOTE
                    </h2>
                    <p className="text-muted-foreground font-mono text-sm mt-1">
                      #{selectedQuote.id.slice(0, 8).toUpperCase()}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2 justify-end mb-2">
                      {statusIcon}
                      <Badge className={getStatusColor(selectedQuote.status)} data-testid="quote-status-badge">
                        {selectedQuote.status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      <Calendar className="h-3 w-3 inline mr-1" />
                      Created: {formatDate(selectedQuote.created_at)}
                    </p>
                    {selectedQuote.job_id && (
                      <p className="text-sm text-green-400 mt-1">
                        Converted to Job
                      </p>
                    )}
                  </div>
                </div>

                <Separator />

                {/* Customer Info */}
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                      Prepared For
                    </h3>
                    {customer ? (
                      <div className="space-y-1">
                        <p className="font-bold text-lg">{customer.name}</p>
                        {customer.company && (
                          <p className="text-muted-foreground flex items-center gap-1">
                            <Building2 className="h-3 w-3" /> {customer.company}
                          </p>
                        )}
                        {customer.email && (
                          <p className="text-muted-foreground flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {customer.email}
                          </p>
                        )}
                        {customer.phone && (
                          <p className="text-muted-foreground flex items-center gap-1">
                            <Phone className="h-3 w-3" /> {customer.phone}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-muted-foreground">Customer not found</p>
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                      From
                    </h3>
                    <div className="space-y-1">
                      <p className="font-bold text-lg">SignGuy AI</p>
                      <p className="text-muted-foreground">Your Professional Sign Shop</p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Line Items Table */}
                <div>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
                    Quote Details
                  </h3>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="text-left p-3 text-sm font-semibold">Description</th>
                          <th className="text-center p-3 text-sm font-semibold w-20">Qty</th>
                          <th className="text-right p-3 text-sm font-semibold w-28">Unit Price</th>
                          <th className="text-right p-3 text-sm font-semibold w-28">Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedQuote.line_items && selectedQuote.line_items.length > 0 ? (
                          selectedQuote.line_items.map((item, idx) => (
                            <tr key={idx} className={idx % 2 === 1 ? 'bg-muted/20' : ''}>
                              <td className="p-3 text-sm">{item.description}</td>
                              <td className="p-3 text-sm text-center">{item.quantity}</td>
                              <td className="p-3 text-sm text-right">{formatCurrency(item.unit_price)}</td>
                              <td className="p-3 text-sm text-right font-medium">
                                {formatCurrency(item.quantity * item.unit_price)}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="4" className="p-3 text-sm text-center text-muted-foreground">
                              No line items
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Totals */}
                <div className="flex justify-end">
                  <div className="w-64 space-y-2">
                    <Separator />
                    <div className="flex justify-between font-bold text-lg">
                      <span>Total:</span>
                      <span className="text-primary">
                        {formatCurrency(selectedQuote.total)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Notes */}
                {selectedQuote.notes && (
                  <>
                    <Separator />
                    <div>
                      <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                        Notes
                      </h3>
                      <p className="text-sm p-3 bg-muted/30 rounded-lg whitespace-pre-wrap">
                        {selectedQuote.notes}
                      </p>
                    </div>
                  </>
                )}

                {/* Terms / Footer */}
                <Separator />
                <div className="text-sm text-muted-foreground space-y-2">
                  <p className="font-medium">Terms & Conditions:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>This quote is valid for 30 days from the date issued</li>
                    <li>50% deposit required upon approval to begin production</li>
                    <li>Balance due upon completion</li>
                    <li>Prices subject to change if specifications are modified</li>
                  </ul>
                </div>

                {/* Footer */}
                <div className="text-center text-xs text-muted-foreground print:mt-8">
                  <p>Thank you for your business!</p>
                  <p className="mt-1">SignGuy AI - Your Professional Sign Shop</p>
                </div>

                {/* Actions (hidden in print) */}
                <div className="flex justify-between print:hidden">
                  {!selectedQuote.job_id && selectedQuote.status !== 'approved' && (
                    <Button 
                      variant="outline" 
                      onClick={() => { setIsPreviewOpen(false); handleEdit(selectedQuote); }}
                    >
                      <Edit2 className="h-4 w-4 mr-2" /> Edit Quote
                    </Button>
                  )}
                  {!selectedQuote.job_id && selectedQuote.status === 'approved' && (
                    <Button 
                      onClick={() => { handleConvert(selectedQuote.id); setIsPreviewOpen(false); }}
                      className="bg-primary"
                    >
                      <ArrowRightCircle className="h-4 w-4 mr-2" /> Convert to Job
                    </Button>
                  )}
                  {selectedQuote.job_id && <div />}
                  <Button variant="outline" onClick={() => setIsPreviewOpen(false)}>
                    Close
                  </Button>
                </div>
              </div>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}
