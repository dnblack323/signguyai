import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, CreditCard, Eye, FileText, Lock, MessageSquare, Users } from 'lucide-react';

export default function DocsCustomerPortal() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><Users className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Customer Portal</h1>
        <p className="text-lg text-gray-400">The Customer Portal is a communication, approval, forms, document, and invoice system — not just a file share page.</p>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        {[
          { icon: Eye, title: 'Jobs', desc: 'Customer-facing job tracking and simplified status timeline' },
          { icon: CheckCircle, title: 'Proofs', desc: 'Approvals, revisions, and version history' },
          { icon: MessageSquare, title: 'Messages', desc: 'Job-specific and account-level communication' },
          { icon: CreditCard, title: 'Invoices', desc: 'View, download, and pay when Stripe is enabled' },
        ].map((item) => (
          <div key={item.title} className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 text-center">
            <item.icon className="h-6 w-6 text-cyan-400 mx-auto mb-2" />
            <h3 className="font-medium text-white">{item.title}</h3>
            <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Portal Invite Flow</h2>
        <ol className="space-y-3">
          {[
            'Create the customer record first.',
            'Open the customer detail modal and go to the Customer Portal section.',
            'Click Invite to Portal.',
            'The system enables portal access and generates a temporary 6-digit PIN.',
            'The customer logs in with email + temporary PIN and changes credentials afterward.'
          ].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300"><span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>{step}</li>
          ))}
        </ol>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-start gap-3"><Lock className="h-5 w-5 text-cyan-400 mt-0.5" /><div><h3 className="text-white font-semibold mb-2">Security Rule</h3><p className="text-gray-300">Customers should only see their own records. Internal notes, internal production stages, pricing breakdowns, and internal-only documents must remain hidden.</p></div></div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">What the Portal Now Supports</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• dashboard widgets for approvals, forms, documents, and invoices</li>
          <li>• customer-facing job detail with proofs, forms, documents, invoices, and message context</li>
          <li>• proof version history</li>
          <li>• forms/questionnaires with submission saved back into the document library</li>
          <li>• invoice PDF download and payment session launch where Stripe is configured</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/webstores" className="text-gray-400 hover:text-white">← Webstores</Link>
        <Link to="/docs/financials" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Financial Tracking <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
