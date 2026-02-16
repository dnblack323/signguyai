import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { 
  Printer, X, Building2, Receipt, Calendar, 
  Phone, Mail, CheckCircle, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

export default function InvoicePreviewModal({ invoiceId, isOpen, onClose }) {
  const { customers, fetchCustomers, jobs, fetchJobs } = useApp();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen && invoiceId) {
      loadInvoice();
    }
  }, [isOpen, invoiceId]);

  const loadInvoice = async () => {
    setLoading(true);
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/invoices/${invoiceId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('Invoice not found');
      const data = await res.json();
      setInvoice(data);
      
      // Ensure we have customers and jobs loaded for display
      if (customers.length === 0) await fetchCustomers();
      if (jobs.length === 0) await fetchJobs();
    } catch (err) {
      toast.error('Failed to load invoice');
      onClose();
    }
    setLoading(false);
  };

  const handlePrint = () => {
    window.print();
  };

  const getCustomer = () => {
    if (!invoice) return null;
    return customers.find(c => c.id === invoice.customer_id);
  };

  const getJob = () => {
    if (!invoice || !invoice.job_id) return null;
    return jobs.find(j => j.id === invoice.job_id);
  };

  const customer = getCustomer();
  const job = getJob();

  const statusIcon = invoice?.status === 'paid' ? (
    <CheckCircle className="h-5 w-5 text-green-400" />
  ) : invoice?.status === 'overdue' ? (
    <AlertTriangle className="h-5 w-5 text-red-400" />
  ) : null;

  const handleEmail = () => {
    if (!invoice) return;
    const customer = getCustomer();
    if (customer?.email) {
      const subject = encodeURIComponent(`Invoice #${invoice.id.slice(0, 8).toUpperCase()} from SignGuy AI`);
      const body = encodeURIComponent(`Dear ${customer.name},\n\nPlease find attached your invoice #${invoice.id.slice(0, 8).toUpperCase()} for ${formatCurrency(invoice.total)}.\n\nThank you for your business!\n\nBest regards,\nSignGuy AI`);
      window.open(`mailto:${customer.email}?subject=${subject}&body=${body}`, '_blank');
    } else {
      toast.error('Customer email not found');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent 
        className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto print:max-w-full print:max-h-full print:overflow-visible"
        data-testid="invoice-preview-modal"
      >
        <DialogHeader className="print:hidden">
          <div className="flex items-center justify-between">
            <DialogTitle className="font-heading uppercase flex items-center gap-2">
              <Receipt className="h-5 w-5" />
              Invoice Preview
            </DialogTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleEmail} data-testid="email-invoice-btn">
                <Mail className="h-4 w-4 mr-2" /> Email
              </Button>
              <Button variant="outline" size="sm" onClick={handlePrint} data-testid="print-invoice-btn">
                <Printer className="h-4 w-4 mr-2" /> Print
              </Button>
            </div>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : invoice ? (
          <div className="invoice-preview space-y-6 p-4 bg-background rounded-lg border print:border-none print:p-0">
            {/* Invoice Header */}
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold font-heading uppercase tracking-tight text-primary">
                  INVOICE
                </h2>
                <p className="text-muted-foreground font-mono text-sm mt-1">
                  #{invoice.id.slice(0, 8).toUpperCase()}
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-2 justify-end mb-2">
                  {statusIcon}
                  <Badge className={getStatusColor(invoice.status)} data-testid="invoice-status-badge">
                    {invoice.status.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  <Calendar className="h-3 w-3 inline mr-1" />
                  Created: {formatDate(invoice.created_at)}
                </p>
                {invoice.due_date && (
                  <p className="text-sm text-muted-foreground">
                    Due: {formatDate(invoice.due_date)}
                  </p>
                )}
              </div>
            </div>

            <Separator />

            {/* Bill To Section */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Bill To
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
                  <p className="text-muted-foreground">Your Sign Shop</p>
                </div>
              </div>
            </div>

            {/* Job Reference */}
            {job && (
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="text-sm">
                  <span className="text-muted-foreground">Reference Job: </span>
                  <span className="font-medium">{job.name}</span>
                </p>
              </div>
            )}

            <Separator />

            {/* Line Items Table */}
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
                Line Items
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
                    {invoice.line_items && invoice.line_items.length > 0 ? (
                      invoice.line_items.map((item, idx) => (
                        <tr key={idx} className={idx % 2 === 1 ? 'bg-muted/20' : ''}>
                          <td className="p-3 text-sm">{item.description}</td>
                          <td className="p-3 text-sm text-center">{item.quantity}</td>
                          <td className="p-3 text-sm text-right">{formatCurrency(item.unit_price)}</td>
                          <td className="p-3 text-sm text-right font-medium">{formatCurrency(item.total)}</td>
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
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotal:</span>
                  <span>{formatCurrency(invoice.total)}</span>
                </div>
                {invoice.amount_paid > 0 && (
                  <div className="flex justify-between text-sm text-green-400">
                    <span>Paid:</span>
                    <span>-{formatCurrency(invoice.amount_paid)}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between font-bold text-lg">
                  <span>Balance Due:</span>
                  <span className={invoice.total - invoice.amount_paid > 0 ? 'text-primary' : 'text-green-400'}>
                    {formatCurrency(invoice.total - invoice.amount_paid)}
                  </span>
                </div>
              </div>
            </div>

            {/* Notes */}
            {invoice.notes && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                    Notes
                  </h3>
                  <p className="text-sm p-3 bg-muted/30 rounded-lg whitespace-pre-wrap">
                    {invoice.notes}
                  </p>
                </div>
              </>
            )}

            {/* Footer */}
            <Separator />
            <div className="text-center text-xs text-muted-foreground print:mt-8">
              <p>Thank you for your business!</p>
              <p className="mt-1">SignGuy AI - Your Professional Sign Shop</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            Invoice not found
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
