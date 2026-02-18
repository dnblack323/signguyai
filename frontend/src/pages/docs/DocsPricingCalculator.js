import { Link } from 'react-router-dom';
import { Calculator, ArrowRight, Sparkles, DollarSign, TrendingUp } from 'lucide-react';

export default function DocsPricingCalculator() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Calculator className="h-4 w-4" />
          Core Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Pricing Calculator</h1>
        <p className="text-lg text-gray-400">
          Calculate accurate pricing with built-in profit margins, material costs, and AI-powered recommendations.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Supported Categories</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {['Banners', 'Vehicle Wraps', 'Wall Graphics', 'Window Graphics', 'Channel Letters', 'Yard Signs', 'Trade Shows', 'Apparel'].map((cat) => (
            <div key={cat} className="p-3 rounded-lg bg-gray-800/50 text-center">
              <span className="text-gray-300 text-sm">{cat}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Using the Calculator</h2>
        <ol className="space-y-4">
          {[
            { title: 'Select Category', desc: 'Choose the type of product you\'re pricing' },
            { title: 'Enter Dimensions', desc: 'Input width and height in inches or feet' },
            { title: 'Choose Material', desc: 'Select the material grade (economy, standard, premium)' },
            { title: 'Adjust Quantity', desc: 'Set how many units the customer needs' },
            { title: 'Set Complexity', desc: 'Use the slider to adjust for job difficulty (1x to 2x multiplier)' },
            { title: 'Review Pricing', desc: 'See material cost, labor, profit margin, and suggested price' },
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

      <div className="p-6 rounded-xl bg-purple-500/10 border border-purple-500/20">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="h-6 w-6 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">AI Pricing Advisor</h2>
        </div>
        <p className="text-gray-300 mb-4">
          Click the purple "AI Pricing Advisor" button to get intelligent pricing recommendations:
        </p>
        <ul className="space-y-2 ml-4">
          {[
            'Analysis of your current pricing vs. market rates',
            'Suggested quantity tier discounts',
            'Upsell opportunities',
            'Margin improvement tips'
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <TrendingUp className="h-4 w-4 text-purple-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/invoicing" className="text-gray-400 hover:text-white">
          ← Invoicing
        </Link>
        <Link to="/docs/ai-tools" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          AI Tools Suite <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
