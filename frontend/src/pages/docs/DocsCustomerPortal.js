import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle, CreditCard, Eye, FileText, Lock, MessageSquare, Users, Mail, Shield, Settings, Image } from 'lucide-react';

export default function DocsCustomerPortal() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Users className="h-4 w-4" /> Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Customer Portal</h1>
        <p className="text-lg text-gray-400">
          The Customer Portal is a full communication, approval, forms, document, and invoice system — giving your customers 24/7 self-service access to their projects.
        </p>
      </div>

      {/* Feature Grid */}
      <div className="grid md:grid-cols-4 gap-4">
        {[
          { icon: Eye, title: 'Orders', desc: 'Customer-facing order tracking and simplified status timeline' },
          { icon: CheckCircle, title: 'Proofs', desc: 'Approvals, revisions, and version history' },
          { icon: MessageSquare, title: 'Messages', desc: 'Order-specific and account-level communication' },
          { icon: CreditCard, title: 'Invoices', desc: 'View, download, and pay when Stripe is enabled' },
        ].map((item) => (
          <div key={item.title} className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 text-center">
            <item.icon className="h-6 w-6 text-cyan-400 mx-auto mb-2" />
            <h3 className="font-medium text-white">{item.title}</h3>
            <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* Portal Invite Flow */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Mail className="h-5 w-5 text-cyan-400" /> Portal Invite Flow
        </h2>
        <ol className="space-y-3">
          {[
            'Create the customer record first (Customers → + Add Customer)',
            'Open the customer detail modal and find the Customer Portal section',
            'Click "Invite to Portal" button',
            'System enables portal access and generates a temporary 6-digit PIN',
            'Customer receives login instructions via email',
            'Customer logs in with email + temporary PIN and sets their own password'
          ].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* What Customers See */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Eye className="h-5 w-5 text-cyan-400" /> What Customers See
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-white mb-2">Dashboard</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Pending approvals counter</li>
              <li>• Outstanding forms/questionnaires</li>
              <li>• Recent documents shared</li>
              <li>• Unpaid invoices summary</li>
              <li>• Quick action buttons</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-white mb-2">Order Details</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Simplified status timeline</li>
              <li>• Proof images with approve/reject</li>
              <li>• Revision request notes</li>
              <li>• Associated documents</li>
              <li>• Message thread for that order</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Proofs & Approvals */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Image className="h-5 w-5 text-cyan-400" /> Proofs & Approvals
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Upload Proofs</strong> — Send design proofs directly from order item detail</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Version History</strong> — All proof versions are saved and viewable</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Approve / Request Changes</strong> — Customer can approve or add revision notes</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Notifications</strong> — Alerts sent when new proofs are uploaded</span>
          </li>
        </ul>
      </div>

      {/* Forms & Questionnaires */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-cyan-400" /> Forms & Questionnaires
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Create questionnaire templates in Document Library</li>
          <li>• Assign questionnaires to specific customers or jobs</li>
          <li>• Customers fill out forms through the portal</li>
          <li>• Responses saved back to the document library</li>
          <li>• Use for: vehicle wrap measurements, event details, design briefs</li>
        </ul>
      </div>

      {/* Quotes & Approvals */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-cyan-400" /> Quotes & Invoices
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">View Quotes</strong> — Customers see all pending quotes with line items and totals</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Approve / Reject Quotes</strong> — One-click approval triggers signature capture flow</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Download PDFs</strong> — Quote and invoice PDFs available for download</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Online Payments</strong> — Pay invoices via Stripe when connected</span>
          </li>
        </ul>
      </div>

      {/* Appointments */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-violet-500/20 to-purple-500/20 border border-violet-500/30">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Users className="h-5 w-5 text-violet-400" /> Appointment Requests
        </h2>
        <p className="text-gray-300 mb-3">Customers can request appointments directly through the portal:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-violet-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Request New Appointment</strong> — Customer selects type (consultation, install, site survey), date, time, and location</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-violet-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Pending Confirmation</strong> — Shows amber badge until shop confirms or rejects</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-violet-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Admin Notification</strong> — Shop owner receives email when new request submitted</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-violet-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">View Scheduled Appointments</strong> — List of all confirmed appointments with details</span>
          </li>
        </ul>
      </div>

      {/* Security */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/30">
        <div className="flex items-start gap-3">
          <Lock className="h-5 w-5 text-red-400 mt-0.5" />
          <div>
            <h3 className="text-white font-semibold mb-2">Security & Isolation</h3>
            <p className="text-gray-300 mb-3">Customers only see their own records. The following are ALWAYS hidden from customers:</p>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Internal notes and comments</li>
              <li>• Detailed production stages</li>
              <li>• Pricing cost breakdowns</li>
              <li>• Internal-only documents</li>
              <li>• Other customer information</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Portal Settings */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5 text-cyan-400" /> Portal Configuration
        </h2>
        <p className="text-gray-300 mb-3">Configure portal behavior in Settings → Customer Portal:</p>
        <ul className="space-y-1 text-gray-300">
          <li>• Enable/disable portal features globally</li>
          <li>• Control what customers can see and do</li>
          <li>• Set up approval workflow preferences</li>
          <li>• Configure invoice payment settings</li>
          <li>• Customize portal branding with your logo</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/webstores" className="text-gray-400 hover:text-white">← Webstores</Link>
        <Link to="/docs/financials" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Financial Tracking <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
