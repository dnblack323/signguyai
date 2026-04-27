import { Link } from 'react-router-dom';
import { ArrowRight, DollarSign, TrendingUp, PieChart, FileText, Calendar, CreditCard, AlertCircle } from 'lucide-react';

export default function DocsFinancials() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><DollarSign className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Financial Tracking & Profit Analytics</h1>
        <p className="text-lg text-gray-400">The platform separates basic financial tracking from profit analytics. Use both together for a more accurate picture of business health.</p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><PieChart className="h-5 w-5 text-cyan-400" /> Two Financial Layers</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <h3 className="font-semibold text-white mb-2">Financials Dashboard</h3>
            <ul className="text-sm text-gray-400 space-y-1">
              <li>• Revenue tracking (monthly/yearly)</li>
              <li>• Expense entry with receipts</li>
              <li>• Invoice aging buckets (0-30, 31-60, 61-90, 90+ days)</li>
              <li>• Category-level accounting</li>
              <li>• Quick expense photo capture</li>
            </ul>
          </div>
          <div className="bg-cyan-900/30 rounded-lg p-4 border border-cyan-700/50">
            <h3 className="font-semibold text-cyan-300 mb-2">Profit & Margin Analytics</h3>
            <ul className="text-sm text-cyan-200/70 space-y-1">
              <li>• Job-level cost vs sell comparison</li>
              <li>• Category profitability breakdown</li>
              <li>• Customer profitability ranking</li>
              <li>• Underpriced job detection</li>
              <li>• Export to CSV/XLSX/PDF</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><FileText className="h-5 w-5 text-cyan-400" /> Invoice Management</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong className="text-white">Generate from Orders</strong> — One-click invoice generation from any order</li>
          <li>• <strong className="text-white">PDF Download</strong> — Professional invoices with your logo, payment terms, and totals</li>
          <li>• <strong className="text-white">Email Invoices</strong> — Send directly to customers with pay link</li>
          <li>• <strong className="text-white">Online Payments</strong> — Stripe Connect integration for card payments</li>
          <li>• <strong className="text-white">Partial Payments</strong> — Track deposits and payment plans</li>
          <li>• <strong className="text-white">Tax Handling</strong> — Automatic tax calculation for non-exempt customers</li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-green-500/10 border border-green-500/30">
        <div className="flex items-center gap-3 mb-3"><TrendingUp className="h-5 w-5 text-green-400" /><h2 className="text-lg font-semibold text-white">Profit Analytics Reports</h2></div>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong className="text-white">Revenue Summary</strong> — Total revenue and profit metrics</li>
          <li>• <strong className="text-white">Profit by Category</strong> — See which product lines are most profitable</li>
          <li>• <strong className="text-white">Customer Profitability</strong> — Rank customers by total profit contribution</li>
          <li>• <strong className="text-white">Job Profitability</strong> — Identify underpriced jobs with cost vs sell analysis</li>
          <li>• <strong className="text-white">Top/Bottom 10</strong> — Quick view of best and worst performing orders</li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/30">
        <div className="flex items-center gap-3 mb-3"><CreditCard className="h-5 w-5 text-amber-400" /><h2 className="text-lg font-semibold text-white">Stripe Connect Integration</h2></div>
        <ul className="space-y-2 text-gray-300">
          <li>• Connect your Stripe account in Settings → Payment Settings</li>
          <li>• Customer payments go directly to your Stripe balance</li>
          <li>• Automatic invoice status updates via webhooks</li>
          <li>• View payout history and upcoming payouts</li>
          <li>• Supports refunds from Stripe dashboard</li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Calendar className="h-5 w-5 text-cyan-400" /> Invoice Aging</h2>
        <p className="text-gray-300 mb-3">Track outstanding invoices by age:</p>
        <div className="grid grid-cols-4 gap-2 text-center">
          <div className="bg-green-500/20 rounded p-2"><span className="text-green-400 font-semibold">0-30 days</span><br/><span className="text-xs text-gray-400">Current</span></div>
          <div className="bg-yellow-500/20 rounded p-2"><span className="text-yellow-400 font-semibold">31-60 days</span><br/><span className="text-xs text-gray-400">Overdue</span></div>
          <div className="bg-orange-500/20 rounded p-2"><span className="text-orange-400 font-semibold">61-90 days</span><br/><span className="text-xs text-gray-400">Past Due</span></div>
          <div className="bg-red-500/20 rounded p-2"><span className="text-red-400 font-semibold">90+ days</span><br/><span className="text-xs text-gray-400">Collections</span></div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customer-portal" className="text-gray-400 hover:text-white">← Customer Portal</Link>
        <Link to="/docs/productivity" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Productivity Tools <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
