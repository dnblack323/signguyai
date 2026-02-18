import { Link } from 'react-router-dom';
import { Receipt, ArrowRight, Mail, Sparkles, DollarSign } from 'lucide-react';

export default function DocsInvoicing() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-amber-400 text-sm font-medium mb-2">
          <Receipt className="h-4 w-4" />
          Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Invoicing</h1>
        <p className="text-lg text-gray-400">
          Generate professional invoices, track payments, and manage your accounts receivable.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Invoice Statuses</h2>
        <div className="grid grid-cols-4 gap-4">
          {[
            { status: 'Draft', color: 'bg-gray-500', desc: 'Not yet sent' },
            { status: 'Sent', color: 'bg-blue-500', desc: 'Awaiting payment' },
            { status: 'Paid', color: 'bg-green-500', desc: 'Payment received' },
            { status: 'Overdue', color: 'bg-red-500', desc: 'Past due date' },
          ].map((item) => (
            <div key={item.status} className="text-center p-4 rounded-lg bg-gray-800/50">
              <div className={`w-3 h-3 rounded-full ${item.color} mx-auto mb-2`} />
              <div className="text-white font-medium">{item.status}</div>
              <div className="text-xs text-gray-500">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Creating an Invoice</h2>
        <ol className="space-y-3">
          {[
            'Navigate to Invoices from the sidebar',
            'Click "New Invoice" button',
            'Select a customer from the dropdown',
            'Optionally link to a job (auto-fills total)',
            'Set due date and add any notes',
            'Save as draft or mark as sent'
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-sm flex items-center justify-center">{i + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Sending Invoices</h2>
        <p className="text-gray-300 mb-4">
          Click the eye icon on any invoice to preview it, then use the action buttons:
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-gray-800/50">
            <div className="flex items-center gap-2 mb-2">
              <Mail className="h-5 w-5 text-amber-400" />
              <span className="text-white font-medium">Email</span>
            </div>
            <p className="text-sm text-gray-400">Send directly to customer's email</p>
          </div>
          <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-5 w-5 text-purple-400" />
              <span className="text-white font-medium">AI Draft</span>
            </div>
            <p className="text-sm text-gray-400">Generate professional email text with AI</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/quotes-jobs" className="text-gray-400 hover:text-white">
          ← Quotes & Jobs
        </Link>
        <Link to="/docs/pricing-calculator" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Pricing Calculator <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
