import { Link } from 'react-router-dom';
import { Users, ArrowRight, UserPlus, Mail, Building2, Search, Edit2, Trash2, Palette, Sparkles } from 'lucide-react';

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

      {/* CSV Import / Export */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Mail className="h-5 w-5 text-cyan-400" />
          Bulk Import & Export
        </h2>
        <p className="text-gray-300 mb-4">
          Already have a customer list somewhere else? Bring it in (or take it out) with the CSV buttons at the top of the Customers page.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
            <h3 className="font-medium text-white mb-2">Import CSV</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Click <strong className="text-white">Import CSV</strong> on the Customers page header.</li>
              <li>• Required column: <code className="text-cyan-300">name</code>. Optional columns: <code className="text-cyan-300">email, phone, company, address, notes</code>.</li>
              <li>• If any row fails validation, the whole import is rolled back and an error message tells you which row was bad — no half-imported data.</li>
              <li>• Use this to onboard a new tenant from another CRM in one shot.</li>
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
            <h3 className="font-medium text-white mb-2">Export CSV</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Click <strong className="text-white">Export CSV</strong> on the Customers page header.</li>
              <li>• Downloads every customer record (name, email, phone, company, address, status, notes, created date).</li>
              <li>• Use this for end-of-month reporting, backup, or migrating away.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Welcome Email */}
      <div className="p-4 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-100 text-sm flex items-start gap-2">
        <Mail className="h-4 w-4 text-cyan-400 mt-0.5 flex-shrink-0" />
        <span>
          <strong className="text-white">Welcome email:</strong> when you add a customer with an email address, the system can automatically send a "welcome" email from your shop. Toggle it under Settings → Notifications → <em>Send welcome email on customer create</em> (default ON).
        </span>
      </div>

      {/* Customer Branding Profile */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Palette className="h-5 w-5 text-pink-400" />
          Customer Branding Profile
          <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">New</span>
        </h2>
        <p className="text-gray-300 mb-4">
          Every customer record now has a <strong className="text-white">Branding</strong> tab that stores their brand information in one place. The AI Branding Tools can pre-fill from this profile and save outputs (taglines, logos, brand kits) directly back to it.
        </p>

        <div className="rounded-xl bg-gray-900/60 border border-gray-800 p-5 space-y-4">
          <div>
            <h3 className="font-medium text-white mb-2">What you can store</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Business name, industry, target audience, brand personality</li>
              <li>• Brand voice notes, USP, things to avoid, key competitors</li>
              <li>• Brand colors (hex), font suggestions, brand-kit text</li>
              <li>• Saved taglines (with one selected as the active tagline)</li>
              <li>• Saved logo concepts (up to 3)</li>
            </ul>
          </div>

          <div>
            <h3 className="font-medium text-white mb-2">How to use it</h3>
            <ol className="space-y-2 text-sm text-gray-300">
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">1</span>
                <span>Open a customer from the Customers list. Click the <strong className="text-white">Branding</strong> tab (5th tab).</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">2</span>
                <span>Click <strong className="text-white">Edit</strong>, fill in what you know about their brand, and Save.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">3</span>
                <span>Use the three CTAs at the top of the tab — <em>Brainstorm Ideas</em>, <em>Create Brand Kit</em>, <em>Logo Concepts</em>. They open the matching AI tool with this customer pre-attached and the form pre-filled from the profile.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">4</span>
                <span>Run the AI tool. The result panel has <strong className="text-white">"Save to Customer Branding"</strong> buttons that push the output (tagline / logo / brand kit) straight back to the profile.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">5</span>
                <span>Re-open the customer's Branding tab to see the saved items, with delete buttons next to each.</span>
              </li>
            </ol>
          </div>

          <div className="text-sm bg-pink-500/5 border border-pink-500/20 rounded-lg p-3 flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-0.5 flex-shrink-0" />
            <span className="text-pink-100">
              <strong className="text-white">Why it matters:</strong> Outputs from the AI Branding tools no longer "die" in your AI history. Everything stays organized on the customer record so the next time you work with that customer, you don't start from scratch.
            </span>
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
          Orders & Order Items <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
