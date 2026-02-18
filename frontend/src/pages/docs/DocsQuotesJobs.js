import { Link } from 'react-router-dom';
import { Briefcase, ArrowRight, FileText, CheckCircle, Clock, ArrowRightCircle } from 'lucide-react';

export default function DocsQuotesJobs() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-purple-400 text-sm font-medium mb-2">
          <Briefcase className="h-4 w-4" />
          Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Quotes & Jobs</h1>
        <p className="text-lg text-gray-400">
          Learn how to create professional quotes, convert them to jobs, and track project progress through completion.
        </p>
      </div>

      {/* Workflow Overview */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">The Quote-to-Job Workflow</h2>
        <div className="flex items-center justify-between gap-2 overflow-x-auto py-4">
          {['Quote Created', 'Sent to Customer', 'Approved', 'Job Started', 'Completed'].map((stage, i) => (
            <div key={i} className="flex items-center">
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  i === 0 ? 'bg-purple-500/20 text-purple-400' : 'bg-gray-800 text-gray-500'
                }`}>
                  {i + 1}
                </div>
                <span className="text-xs text-gray-400 mt-2 whitespace-nowrap">{stage}</span>
              </div>
              {i < 4 && <ArrowRight className="h-4 w-4 text-gray-600 mx-2" />}
            </div>
          ))}
        </div>
      </div>

      {/* Creating Quotes */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Creating a Quote</h2>
        <ol className="space-y-4">
          <li className="flex items-start gap-3 text-gray-300">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center">1</span>
            <div>
              <strong className="text-white">Navigate to Quotes</strong>
              <p className="text-gray-400">Click "Quotes" in the sidebar, then "New Quote"</p>
            </div>
          </li>
          <li className="flex items-start gap-3 text-gray-300">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center">2</span>
            <div>
              <strong className="text-white">Select Customer</strong>
              <p className="text-gray-400">Choose an existing customer from the dropdown</p>
            </div>
          </li>
          <li className="flex items-start gap-3 text-gray-300">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center">3</span>
            <div>
              <strong className="text-white">Add Line Items</strong>
              <p className="text-gray-400">Enter description, quantity, and unit price for each item</p>
              <div className="mt-2 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-200 text-sm">
                <strong>Pro Tip:</strong> Use the Calculator icon to open the Pricing Calculator for accurate pricing!
              </div>
            </div>
          </li>
          <li className="flex items-start gap-3 text-gray-300">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center">4</span>
            <div>
              <strong className="text-white">Add Notes</strong>
              <p className="text-gray-400">Include any terms, conditions, or special instructions</p>
            </div>
          </li>
          <li className="flex items-start gap-3 text-gray-300">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center">5</span>
            <div>
              <strong className="text-white">Save or Send</strong>
              <p className="text-gray-400">Save as draft or send directly to the customer</p>
            </div>
          </li>
        </ol>
      </div>

      {/* Converting to Job */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Converting Quote to Job</h2>
        <p className="text-gray-300 mb-4">
          Once a customer approves a quote, you can convert it to an active job:
        </p>
        <ol className="space-y-3">
          {[
            'Open the quote by clicking the eye icon',
            'Click the "Convert to Job" button',
            'The job is created with all quote details',
            'Track progress through the job timeline'
          ].map((step, i) => (
            <li key={i} className="flex items-center gap-3 text-gray-300">
              <CheckCircle className="h-4 w-4 text-green-400" />
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Job Status Timeline */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Job Status Timeline</h2>
        <p className="text-gray-300 mb-4">
          Jobs progress through a series of statuses. Click on a job to see its timeline:
        </p>
        <div className="grid grid-cols-5 gap-2 p-4 rounded-lg bg-gray-800/50">
          {[
            { status: 'Quoted', color: 'bg-gray-500' },
            { status: 'Approved', color: 'bg-blue-500' },
            { status: 'In Production', color: 'bg-yellow-500' },
            { status: 'Installed', color: 'bg-purple-500' },
            { status: 'Complete', color: 'bg-green-500' },
          ].map((item, i) => (
            <div key={i} className="text-center">
              <div className={`w-8 h-8 rounded-full ${item.color} mx-auto mb-2`} />
              <span className="text-xs text-gray-400">{item.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Job Time Tracking */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Time Tracking on Jobs</h2>
        <p className="text-gray-300 mb-4">
          Track time spent on each job for accurate labor costing:
        </p>
        <ul className="space-y-2 ml-4">
          {[
            'Start/stop timer directly from the job page',
            'Select task type: Design, Production, Installation, Admin',
            'View time log with all entries and labor costs',
            'See total hours and costs in the summary panel'
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <Clock className="h-4 w-4 text-purple-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customers" className="text-gray-400 hover:text-white">
          ← Customers
        </Link>
        <Link to="/docs/invoicing" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Invoicing <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
