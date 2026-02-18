import { Link } from 'react-router-dom';
import { Users, ArrowRight, Eye, CheckCircle, CreditCard, FileText, MessageSquare, Lock } from 'lucide-react';

export default function DocsCustomerPortal() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Users className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Customer Portal</h1>
        <p className="text-lg text-gray-400">
          Give your customers self-service access to view orders, approve artwork, make payments, and communicate with your shop - all without phone calls or emails.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Portal Capabilities</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: Eye, title: 'View Orders', color: 'text-blue-400' },
            { icon: CheckCircle, title: 'Approve Artwork', color: 'text-green-400' },
            { icon: CreditCard, title: 'Make Payments', color: 'text-purple-400' },
            { icon: MessageSquare, title: 'Send Messages', color: 'text-orange-400' },
          ].map((item) => (
            <div key={item.title} className="p-4 rounded-lg bg-gray-800/50 text-center">
              <item.icon className={`h-6 w-6 ${item.color} mx-auto mb-2`} />
              <span className="text-gray-300 text-sm">{item.title}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Enabling Portal Access for a Customer</h2>
        <ol className="space-y-4">
          {[
            { title: 'Open Customer Profile', desc: 'Go to Customers and click on the customer name' },
            { title: 'Enable Portal Access', desc: 'Toggle "Portal Access" to ON in the customer settings' },
            { title: 'Set Password', desc: 'Set an initial password or let the system generate one' },
            { title: 'Send Invitation', desc: 'Click "Send Portal Invite" to email login details to the customer' },
            { title: 'Customer Logs In', desc: 'Customer uses the portal link and their email/password to access' },
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{i + 1}</span>
              <div>
                <strong className="text-white">{step.title}</strong>
                <p className="text-gray-400">{step.desc}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">What Customers Can Do</h2>
        <div className="space-y-4">
          {[
            { icon: Eye, title: 'View Order Status', desc: 'See real-time status of all their orders (quoted, in production, complete, etc.)' },
            { icon: FileText, title: 'Download Proofs', desc: 'Access proof files and design mockups uploaded by your team' },
            { icon: CheckCircle, title: 'Approve Artwork', desc: 'Digitally approve proofs with a click - no more chasing signatures' },
            { icon: CreditCard, title: 'Pay Invoices', desc: 'Pay outstanding invoices online via credit card or ACH' },
            { icon: MessageSquare, title: 'Message Your Team', desc: 'Send messages tied to specific jobs - all communication in one place' },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-lg bg-gray-800/30">
              <item.icon className="h-5 w-5 text-cyan-400 mt-0.5" />
              <div>
                <strong className="text-white">{item.title}</strong>
                <p className="text-gray-400 text-sm">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
        <div className="flex items-start gap-3">
          <Lock className="h-5 w-5 text-cyan-400 mt-0.5" />
          <div>
            <h3 className="text-white font-semibold mb-2">Security Note</h3>
            <p className="text-gray-300">
              Each customer can only see their own orders and information. Portal access is tied to their email address and protected by a password. You can revoke access at any time from the customer profile.
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/webstores" className="text-gray-400 hover:text-white">
          ← Webstores
        </Link>
        <Link to="/docs/financials" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Financial Tracking <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
