import { Link } from 'react-router-dom';
import { ArrowRight, Calculator, Sparkles, TrendingUp } from 'lucide-react';

export default function DocsPricingCalculator() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><Calculator className="h-4 w-4" /> Core Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Pricing System & Calculators</h1>
        <p className="text-lg text-gray-400">The pricing system now uses company-specific cost settings, category defaults, selling benchmarks, and stored cost snapshots rather than one-size-fits-all pricing.</p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">What Powers the Calculators</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Material costs from Pricing & Cost Settings</li>
          <li>• Labor rates from company settings</li>
          <li>• Overhead and markup rules</li>
          <li>• Category-specific defaults</li>
          <li>• Selling benchmarks stored separately from cost settings</li>
          <li>• Stored cost snapshots on quote/job items for reporting and review</li>
        </ul>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Supported Calculator Categories</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {['Promotional', 'Cut Vinyl', 'Services', 'Digital Print / Banners', 'Rigid Signs', 'Apparel', 'Vehicle Graphics', 'Custom / Misc'].map((cat) => (
            <div key={cat} className="p-3 rounded-lg bg-gray-800/50 text-center text-gray-300 text-sm">{cat}</div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Historical Pricing Setup</h2>
        <p className="text-gray-300 mb-4">Use Pricing Setup to upload PDF, CSV, or Excel invoice history. AI analyzes past selling behavior and suggests benchmarks, but those suggestions never overwrite cost settings automatically.</p>
        <ul className="space-y-2 text-gray-300">
          <li>• Map invoice fields if structure is inconsistent</li>
          <li>• Review confidence levels</li>
          <li>• Accept, edit, or ignore each suggestion</li>
          <li>• Save approved values into selling benchmarks only</li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-purple-500/10 border border-purple-500/20">
        <div className="flex items-center gap-3 mb-4"><Sparkles className="h-6 w-6 text-purple-400" /><h2 className="text-lg font-semibold text-white">AI Pricing Advisor</h2></div>
        <p className="text-gray-300 mb-3">The Pricing Advisor is a lightweight AI layer on top of the calculator. It does not replace your cost model — it comments on it.</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-center gap-2"><TrendingUp className="h-4 w-4 text-purple-400" /> Suggests better margins and markup positioning</li>
          <li className="flex items-center gap-2"><TrendingUp className="h-4 w-4 text-purple-400" /> Flags upsell and tier opportunities</li>
          <li className="flex items-center gap-2"><TrendingUp className="h-4 w-4 text-purple-400" /> Uses credits and follows the AI credit confirmation flow</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/invoicing" className="text-gray-400 hover:text-white">← Invoicing</Link>
        <Link to="/docs/ai-tools" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">AI Tools Suite <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
