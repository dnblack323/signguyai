import { Link } from 'react-router-dom';
import { ArrowRight, DollarSign, TrendingUp } from 'lucide-react';

export default function DocsFinancials() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><DollarSign className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Financial Tracking & Profit Analytics</h1>
        <p className="text-lg text-gray-400">The platform now separates basic financial tracking from profit analytics. Use both together for a more accurate picture of business health.</p>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Two Financial Layers</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong className="text-white">Financials</strong> – sales, expenses, and category-level accounting records</li>
          <li>• <strong className="text-white">Profit & Margin Analytics</strong> – reporting based on stored cost snapshots and pricing benchmarks</li>
        </ul>
      </div>
      <div className="p-6 rounded-xl bg-green-500/10 border border-green-500/30">
        <div className="flex items-center gap-3 mb-3"><TrendingUp className="h-5 w-5 text-green-400" /><h2 className="text-lg font-semibold text-white">Profit & Margin Analytics</h2></div>
        <ul className="space-y-2 text-gray-300">
          <li>• revenue and profit summary metrics</li>
          <li>• profit by category</li>
          <li>• customer profitability</li>
          <li>• job profitability with underpriced-job detection</li>
          <li>• CSV / XLSX / PDF export</li>
        </ul>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/customer-portal" className="text-gray-400 hover:text-white">← Customer Portal</Link>
        <Link to="/docs/productivity" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Productivity Tools <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
