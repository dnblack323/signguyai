import { Link } from 'react-router-dom';
import { DollarSign, ArrowRight, TrendingUp, Receipt, FileSpreadsheet, PieChart, Calendar, Calculator } from 'lucide-react';

export default function DocsFinancials() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <DollarSign className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Financial Tracking & Expenses</h1>
        <p className="text-lg text-gray-400">
          Track your shop's revenue, expenses, and profitability. Generate reports for tax time and make data-driven business decisions.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Financial Dashboard</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { metric: 'Revenue', desc: 'Total invoiced', color: 'text-green-400' },
            { metric: 'Expenses', desc: 'Tracked costs', color: 'text-red-400' },
            { metric: 'Profit', desc: 'Revenue - Expenses', color: 'text-cyan-400' },
            { metric: 'Margin', desc: 'Profit percentage', color: 'text-purple-400' },
          ].map((item) => (
            <div key={item.metric} className="p-4 rounded-lg bg-gray-800/50 text-center">
              <span className={`text-lg font-bold ${item.color}`}>{item.metric}</span>
              <p className="text-gray-500 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Tracking Expenses</h2>
        <p className="text-gray-300 mb-4">
          Keep track of all your business expenses for accurate profit calculations and tax preparation.
        </p>
        <ol className="space-y-4">
          {[
            { title: 'Go to Financials', desc: 'Click "Financials" in the sidebar navigation' },
            { title: 'Click Add Expense', desc: 'Click the "Add Expense" button' },
            { title: 'Enter Details', desc: 'Add vendor name, amount, date, and category' },
            { title: 'Attach Receipt', desc: 'Upload a photo or PDF of the receipt (optional but recommended for taxes)' },
            { title: 'Save', desc: 'Click Save to record the expense' },
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
        <h2 className="text-xl font-semibold text-white mb-4">Expense Categories</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            'Materials & Supplies',
            'Equipment',
            'Vehicle Expenses',
            'Rent & Utilities',
            'Software & Subscriptions',
            'Marketing & Advertising',
            'Labor & Contractors',
            'Office Supplies',
            'Insurance',
            'Taxes & Fees',
            'Repairs & Maintenance',
            'Other',
          ].map((category) => (
            <div key={category} className="p-3 rounded-lg bg-gray-800/30 text-gray-300 text-sm">
              {category}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Reports for Taxes</h2>
        <div className="space-y-4">
          {[
            { icon: FileSpreadsheet, title: 'Expense Report', desc: 'Export all expenses by date range and category - perfect for your accountant' },
            { icon: TrendingUp, title: 'Profit & Loss', desc: 'See revenue vs expenses over any time period' },
            { icon: PieChart, title: 'Category Breakdown', desc: 'Visual breakdown of where your money is going' },
            { icon: Calendar, title: 'Monthly/Quarterly/Annual', desc: 'Generate reports for any time period' },
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

      <div className="p-6 rounded-xl bg-green-500/10 border border-green-500/30">
        <div className="flex items-start gap-3">
          <Calculator className="h-5 w-5 text-green-400 mt-0.5" />
          <div>
            <h3 className="text-white font-semibold mb-2">Tax Time Tip</h3>
            <p className="text-gray-300">
              At the end of the year, use the "Export to CSV" feature to download all your expense data. This can be imported directly into accounting software like QuickBooks, or sent to your accountant. Remember to attach receipts throughout the year!
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customer-portal" className="text-gray-400 hover:text-white">
          ← Customer Portal
        </Link>
        <Link to="/docs/productivity" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Productivity Tools <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
