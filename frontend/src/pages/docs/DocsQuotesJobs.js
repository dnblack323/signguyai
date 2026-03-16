import { Link } from 'react-router-dom';
import { Activity, ArrowRight, Briefcase, Clock, GitBranch, MessageSquare, Receipt, Users } from 'lucide-react';

const pipeline = ['Quote', 'Approved', 'In Progress', 'Completed', 'Invoiced', 'Archived'];

export default function DocsQuotesJobs() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-purple-400 text-sm font-medium mb-2">
          <Briefcase className="h-4 w-4" /> Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Quotes, Jobs & Production Workflow</h1>
        <p className="text-lg text-gray-400">
          SignGuy AI uses a unified jobs model. Quotes and jobs live in the same operational system, which means approval, production, portal activity, assignments, and invoicing all stay tied to one record.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Unified Job Pipeline</h2>
        <div className="flex flex-wrap items-center gap-3">
          {pipeline.map((stage, index) => (
            <div key={stage} className="flex items-center gap-3">
              <div className="px-3 py-2 rounded-lg bg-gray-800/70 text-gray-300 text-sm">{stage}</div>
              {index < pipeline.length - 1 && <ArrowRight className="h-4 w-4 text-gray-600" />}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">How Work Moves Through the System</h2>
        <div className="space-y-4">
          {[
            'Create a customer first so the work has a real account record attached to it.',
            'Create a quote if pricing still needs approval, or create a job directly if the work is already sold.',
            'Add line items manually or use the pricing calculator to produce company-based costing and selling price logic.',
            'Approve the quote/job to move it into production-ready status.',
            'Assign employees, attach proofs, send forms, and track history from the same job record.',
            'Create an invoice from the job when billing is ready.'
          ].map((item, index) => (
            <div key={index} className="flex items-start gap-3 text-gray-300">
              <div className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center flex-shrink-0">{index + 1}</div>
              <p>{item}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center gap-2 mb-3"><GitBranch className="h-5 w-5 text-purple-400" /><h3 className="font-semibold text-white">Timeline & History</h3></div>
          <p className="text-gray-300 text-sm mb-3">Each job includes a visible history/timeline panel so the team can quickly understand what happened, who did it, and when.</p>
          <ul className="space-y-2 text-sm text-gray-400">
            <li>• job creation and updates</li>
            <li>• proof upload and customer approval/revision history</li>
            <li>• production stage start/complete entries</li>
            <li>• document uploads</li>
            <li>• invoice/payment events when available</li>
          </ul>
        </div>
        <div className="p-5 rounded-xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center gap-2 mb-3"><Users className="h-5 w-5 text-purple-400" /><h3 className="font-semibold text-white">Assignments & Production</h3></div>
          <p className="text-gray-300 text-sm mb-3">Jobs support both whole-job assignment and stage-level assignment.</p>
          <ul className="space-y-2 text-sm text-gray-400">
            <li>• assign employees from Job Details</li>
            <li>• assign specific production stages in the timeline editor</li>
            <li>• employees can start, pause, and complete stages in their portal</li>
            <li>• workflows can be Simple, Detailed, or Custom</li>
          </ul>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {[
          { icon: Clock, title: 'Job Time Tracking', desc: 'Track labor time for costing, payroll support, and future analytics.' },
          { icon: MessageSquare, title: 'Customer Portal Context', desc: 'Job Details now exposes customer-facing proofs, forms, messages, documents, and invoice visibility.' },
          { icon: Receipt, title: 'Invoice Linkage', desc: 'Jobs can create invoices and show financial status directly in the record.' },
        ].map((item) => (
          <div key={item.title} className="p-4 rounded-lg bg-gray-800/30">
            <item.icon className="h-5 w-5 text-purple-400 mb-2" />
            <h3 className="font-medium text-white">{item.title}</h3>
            <p className="text-sm text-gray-400 mt-1">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4"><Activity className="h-5 w-5 text-purple-400" /><h2 className="text-lg font-semibold text-white">Best Practice</h2></div>
        <p className="text-gray-300">
          Treat Job Details as the operational center of the system. If something affects a specific project — employee assignment, proof approval, documents, forms, status changes, timeline, or invoice state — it should be reviewable there.
        </p>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customers" className="text-gray-400 hover:text-white">← Customers</Link>
        <Link to="/docs/invoicing" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Invoicing <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}