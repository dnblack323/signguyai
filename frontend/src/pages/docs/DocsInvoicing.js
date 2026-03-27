import { Link } from 'react-router-dom';
import { ArrowRight, CreditCard, Mail, Receipt, Sparkles } from 'lucide-react';

export default function DocsInvoicing() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-amber-400 text-sm font-medium mb-2">
          <Receipt className="h-4 w-4" /> Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Invoicing & Payments</h1>
        <p className="text-lg text-gray-400">
          Invoices connect job billing, customer portal visibility, PDF delivery, AI-assisted email drafting, and Stripe-connected payment collection.
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        {[
          { status: 'Draft', desc: 'Built but not yet delivered' },
          { status: 'Sent', desc: 'Visible to customer and awaiting payment' },
          { status: 'Paid', desc: 'Payment received and reflected in records' },
          { status: 'Overdue', desc: 'Still unpaid after due date' },
        ].map((item) => (
          <div key={item.status} className="text-center p-4 rounded-lg bg-gray-900/50 border border-gray-800">
            <div className="text-white font-medium">{item.status}</div>
            <div className="text-xs text-gray-500 mt-1">{item.desc}</div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Standard Invoice Flow</h2>
        <ol className="space-y-3">
          {[
            'Create an invoice manually or generate one from a job.',
            'Review line items, due date, notes, and totals.',
            'Preview the invoice and optionally use AI Draft to generate the email copy.',
            'Send the invoice to the customer by email and/or expose it in the customer portal.',
            'If Stripe Connect is enabled, let the customer use Pay Now from the portal.',
            'Track paid amount, balance due, portal viewed timestamp, and status changes.'
          ].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-sm flex items-center justify-center">{index + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-gray-900/50 border border-gray-800">
          <Mail className="h-5 w-5 text-amber-400 mb-3" />
          <h3 className="font-semibold text-white">Email Delivery</h3>
          <p className="text-sm text-gray-400 mt-2">Send invoices directly and use AI Draft for professional email wording that matches the specific invoice context.</p>
        </div>
        <div className="p-5 rounded-xl bg-gray-900/50 border border-gray-800">
          <CreditCard className="h-5 w-5 text-amber-400 mb-3" />
          <h3 className="font-semibold text-white">Portal Payment Flow</h3>
          <p className="text-sm text-gray-400 mt-2">If Stripe is connected, customers can launch a payment session from the portal. If it is not connected, the system returns a clear message rather than a silent failure.</p>
        </div>
        <div className="p-5 rounded-xl bg-gray-900/50 border border-gray-800">
          <Sparkles className="h-5 w-5 text-amber-400 mb-3" />
          <h3 className="font-semibold text-white">PDF + Portal Visibility</h3>
          <p className="text-sm text-gray-400 mt-2">Customers can view invoices in the portal and download invoice PDFs where available.</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/quotes-jobs" className="text-gray-400 hover:text-white">← Orders Quotes & Jobs Job Tickets</Link>
        <Link to="/docs/pricing-calculator" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Pricing Calculator <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}