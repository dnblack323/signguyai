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
  Phone, Mail, CheckCircle, AlertTriangle, Sparkles, Send
} from 'lucide-react';
import { toast } from 'sonner';
import AIEmailComposer from './AIEmailComposer';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function InvoicePreviewModal({ invoiceId, isOpen, onClose }) {
  const { customers, fetchCustomers, jobs, fetchJobs, tenant } = useApp();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAIEmail, setShowAIEmail] = useState(false);
  const [sendingToPortal, setSendingToPortal] = useState(false);

  useEffect(() => {
    if (isOpen && invoiceId) {
      loadInvoice();
    }
  }, [isOpen, invoiceId]);

  const loadInvoice = async () => {
    setLoading(true);
    try {
      const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
      const token = getAuthToken();
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

  const handleSendToPortal = async () => {
    if (!invoice) return;
    setSendingToPortal(true);
    try {
      const token = getAuthToken();
      const res = await fetch(`${API}/invoices/${invoice.id}/send-to-portal`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to send to portal');
      }
      
      const data = await res.json();
      toast.success(`Invoice sent to ${data.customer_name}'s portal`);
      
      // Reload invoice to update portal status
      await loadInvoice();
    } catch (err) {
      toast.error(err.message || 'Failed to send invoice to portal');
    } finally {
      setSendingToPortal(false);
    }
  };

  const branding = tenant?.branding_settings || {};
  const accent = branding.invoice_accent_color || branding.primary_color || '#2563eb';
  const showInvoiceLogo = branding.invoice_show_logo !== false && tenant?.logo_url;
  const logoAlign = branding.invoice_logo_position === 'center' ? 'center' : branding.invoice_logo_position === 'right' ? 'flex-end' : 'flex-start';
  const showCompanyInfo = branding.invoice_show_company_info !== false;
  const companyName = tenant?.name || 'SignGuy AI';
  const companyAddressLine = [tenant?.city, tenant?.state, tenant?.zip_code].filter(Boolean).join(', ');

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
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setShowAIEmail(true)} 
                className="bg-purple-50 border-purple-200 text-purple-600 hover:bg-purple-100"
                data-testid="ai-email-invoice-btn"
              >
                <Sparkles className="h-4 w-4 mr-2" /> AI Draft
              </Button>
              <Button variant="outline" size="sm" onClick={handleEmail} data-testid="email-invoice-btn">
                <Mail className="h-4 w-4 mr-2" /> Email
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleSendToPortal}
                disabled={sendingToPortal || invoice?.portal_visible}
                className="bg-blue-50 border-blue-200 text-blue-600 hover:bg-blue-100 disabled:opacity-50"
                data-testid="send-to-portal-btn"
              >
                <Send className="h-4 w-4 mr-2" /> 
                {sendingToPortal ? 'Sending...' : invoice?.portal_visible ? 'In Portal' : 'Send to Portal'}
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
          <div className="invoice-preview space-y-6 p-6 bg-white rounded-lg border border-gray-200 shadow-sm print:border-none print:p-0 print:shadow-none">
            {/* Branded logo header */}
            {showInvoiceLogo && (
              <div className="flex" style={{ justifyContent: logoAlign }}>
                <img src={tenant.logo_url} alt={companyName} style={{ maxHeight: '56px', maxWidth: '220px' }} data-testid="invoice-brand-logo" />
              </div>
            )}
            {/* Invoice Header */}
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold font-heading uppercase tracking-tight" style={{ color: accent }}>
                  INVOICE
                </h2>
                <p className="text-gray-500 font-mono text-sm mt-1">
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
                <p className="text-sm text-gray-500">
                  <Calendar className="h-3 w-3 inline mr-1" />
                  Created: {formatDate(invoice.created_at)}
                </p>
                {invoice.due_date && (
                  <p className="text-sm text-gray-500">
                    Due: {formatDate(invoice.due_date)}
                  </p>
                )}
              </div>
            </div>

            <Separator className="bg-gray-200" />

            {/* Bill To Section */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                  Bill To
                </h3>
                {customer ? (
                  <div className="space-y-1">
                    <p className="font-bold text-lg text-gray-900">{customer.name}</p>
                    {customer.company && (
                      <p className="text-gray-600 flex items-center gap-1">
                        <Building2 className="h-3 w-3" /> {customer.company}
                      </p>
                    )}
                    {customer.email && (
                      <p className="text-gray-600 flex items-center gap-1">
                        <Mail className="h-3 w-3" /> {customer.email}
                      </p>
                    )}
                    {customer.phone && (
                      <p className="text-gray-600 flex items-center gap-1">
                        <Phone className="h-3 w-3" /> {customer.phone}
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500">Customer not found</p>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                  From
                </h3>
                <div className="space-y-1">
                  <p className="font-bold text-lg text-gray-900" data-testid="invoice-from-company">{companyName}</p>
                  {showCompanyInfo && tenant?.address && (
                    <p className="text-gray-600 text-sm">{tenant.address}</p>
                  )}
                  {showCompanyInfo && companyAddressLine && (
                    <p className="text-gray-600 text-sm">{companyAddressLine}</p>
                  )}
                  {showCompanyInfo && tenant?.phone && (
                    <p className="text-gray-600 text-sm">{tenant.phone}</p>
                  )}
                  {showCompanyInfo && tenant?.website && (
                    <p className="text-gray-600 text-sm">{tenant.website}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Order Reference */}
            {job && (
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-800">
                  <span className="text-gray-600">Reference Order: </span>
                  <span className="font-medium">{job.name}</span>
                </p>
              </div>
            )}

            <Separator className="bg-gray-200" />

            {/* Line Items Table */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wide">
                Line Items
              </h3>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3 text-sm font-semibold text-gray-700">Description</th>
                      <th className="text-center p-3 text-sm font-semibold text-gray-700 w-20">Qty</th>
                      <th className="text-right p-3 text-sm font-semibold text-gray-700 w-28">Unit Price</th>
                      <th className="text-right p-3 text-sm font-semibold text-gray-700 w-28">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoice.line_items && invoice.line_items.length > 0 ? (
                      invoice.line_items.map((item, idx) => (
                        <tr key={idx} className={idx % 2 === 1 ? 'bg-gray-50' : 'bg-white'}>
                          <td className="p-3 text-sm text-gray-900">{item.description}</td>
                          <td className="p-3 text-sm text-center text-gray-900">{item.quantity}</td>
                          <td className="p-3 text-sm text-right text-gray-900">{formatCurrency(item.unit_price)}</td>
                          <td className="p-3 text-sm text-right font-medium text-gray-900">{formatCurrency(item.total)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="4" className="p-3 text-sm text-center text-gray-500">
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
                  <span className="text-gray-600">Subtotal:</span>
                  <span className="text-gray-900">{formatCurrency(invoice.total)}</span>
                </div>
                {invoice.amount_paid > 0 && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Paid:</span>
                    <span>-{formatCurrency(invoice.amount_paid)}</span>
                  </div>
                )}
                <Separator className="bg-gray-200" />
                <div className="flex justify-between font-bold text-lg">
                  <span className="text-gray-900">Balance Due:</span>
                  <span style={{ color: invoice.total - invoice.amount_paid > 0 ? accent : '#16a34a' }}>
                    {formatCurrency(invoice.total - invoice.amount_paid)}
                  </span>
                </div>
              </div>
            </div>

            {/* Notes */}
            {invoice.notes && (
              <>
                <Separator className="bg-gray-200" />
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                    Notes
                  </h3>
                  <p className="text-sm p-3 bg-gray-100 rounded-lg whitespace-pre-wrap text-gray-800">
                    {invoice.notes}
                  </p>
                </div>
              </>
            )}

            {/* Payment terms */}
            {branding.invoice_payment_terms && (
              <div className="text-sm text-gray-600" data-testid="invoice-payment-terms">
                <span className="font-semibold text-gray-700">Payment Terms: </span>{branding.invoice_payment_terms}
              </div>
            )}

            {/* Footer */}
            <Separator />
            <div className="text-center text-xs text-muted-foreground print:mt-8" data-testid="invoice-footer">
              <p>{branding.invoice_footer_text || 'Thank you for your business!'}</p>
              <p className="mt-1">{companyName}</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            Invoice not found
          </div>
        )}
      </DialogContent>

      {/* AI Email Composer Modal */}
      <AIEmailComposer
        isOpen={showAIEmail}
        onClose={() => setShowAIEmail(false)}
        emailType={invoice?.status === 'overdue' ? 'invoice_overdue' : invoice?.status === 'sent' ? 'invoice_reminder' : 'invoice_send'}
        context={{
          customer_name: customer?.name,
          customer_email: customer?.email,
          invoice_number: invoice?.id?.slice(0, 8).toUpperCase(),
          job_name: job?.name,
          amount: invoice?.total,
          due_date: invoice?.due_date,
          company_name: companyName
        }}
      />
    </Dialog>
  );
}
