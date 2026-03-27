import { Link } from 'react-router-dom';
import { Users, ArrowRight, UserPlus, Mail, Building2, Search, Edit2, Trash2 } from 'lucide-react';

export default function DocsCustomers() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-blue-400 text-sm font-medium mb-2">
          <Users className="h-4 w-4" />
          Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Customers</h1>
        <p className="text-lg text-gray-400">
          Learn how to manage your customer database, track their information, and give them access to the customer portal.
        </p>
      </div>

      {/* Screenshot */}
      <div className="rounded-xl overflow-hidden border border-gray-700">
        <img 
          src="/screenshots/feature_customers.jpeg" 
          alt="Customers Page Overview" 
          className="w-full"
        />
        <div className="bg-gray-800/80 px-4 py-2 text-xs text-gray-400">
          Customers list with search, status filters, and quick actions
        </div>
      </div>

      {/* Overview */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Overview</h2>
        <p className="text-gray-300 mb-4">
          The Customers module is your central hub for managing all client information. Every quote, job, and invoice 
          you create will be linked to a customer record.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="text-center p-4 rounded-lg bg-gray-800/50">
            <UserPlus className="h-6 w-6 text-blue-400 mx-auto mb-2" />
            <span className="text-sm text-gray-400">Add Customers</span>
          </div>
          <div className="text-center p-4 rounded-lg bg-gray-800/50">
            <Search className="h-6 w-6 text-blue-400 mx-auto mb-2" />
            <span className="text-sm text-gray-400">Search & Filter</span>
          </div>
          <div className="text-center p-4 rounded-lg bg-gray-800/50">
            <Edit2 className="h-6 w-6 text-blue-400 mx-auto mb-2" />
            <span className="text-sm text-gray-400">Edit Details</span>
          </div>
          <div className="text-center p-4 rounded-lg bg-gray-800/50">
            <Mail className="h-6 w-6 text-blue-400 mx-auto mb-2" />
            <span className="text-sm text-gray-400">Portal Access</span>
          </div>
        </div>
      </div>

      {/* Adding a Customer */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Adding a Customer</h2>
        <div className="space-y-4">
          <p className="text-gray-300">To add a new customer:</p>
          <ol className="space-y-3">
            {[
              'Navigate to Customers from the sidebar',
              'Click the "Add Customer" button in the top right',
              'Fill in the customer information:',
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-3 text-gray-300">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 text-sm flex items-center justify-center">
                  {i + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
          
          <div className="ml-9 p-4 rounded-lg bg-gray-800/50 space-y-2">
            <p className="text-gray-300"><strong className="text-white">Name</strong> (required) - Customer's full name</p>
            <p className="text-gray-300"><strong className="text-white">Email</strong> - For sending quotes/invoices and portal access</p>
            <p className="text-gray-300"><strong className="text-white">Phone</strong> - Contact phone number</p>
            <p className="text-gray-300"><strong className="text-white">Company</strong> - Business name if applicable</p>
            <p className="text-gray-300"><strong className="text-white">Address</strong> - Billing/shipping address</p>
            <p className="text-gray-300"><strong className="text-white">Notes</strong> - Internal notes about the customer</p>
          </div>
        </div>
      </div>

      {/* Customer Portal */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Customer Portal Access</h2>
        <p className="text-gray-300 mb-4">
          Customers with an email address can access the Customer Portal where they can:
        </p>
        <ul className="space-y-2 ml-4">
          {[
            'View and approve quotes',
            'Track job progress',
            'View and pay invoices',
            'Message your shop directly',
            'Download files and artwork'
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              {item}
            </li>
          ))}
        </ul>
        <div className="mt-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-200 text-sm">
          <strong className="text-blue-400">Note:</strong> Customers access the portal at <code className="bg-blue-500/20 px-1 rounded">/customer-portal/login</code> using their email.
        </div>
      </div>

      {/* Search and Filter */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Searching Customers</h2>
        <p className="text-gray-300 mb-4">
          Use the search bar at the top of the Customers page to quickly find customers by name, email, or company.
          You can also filter by status (Active/Inactive).
        </p>
      </div>

      {/* Next */}
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/getting-started" className="text-gray-400 hover:text-white">
          ← Getting Started
        </Link>
        <Link to="/docs/quotes-jobs" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Orders Orders & Job Tickets Job Tickets <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
