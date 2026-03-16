import { Link } from 'react-router-dom';
import { ArrowRight, Store } from 'lucide-react';

export default function DocsWebstores() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><Store className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Webstores</h1>
        <p className="text-lg text-gray-400">Webstores let you sell products online, route orders into jobs, and use Stripe Connect for checkout when enabled.</p>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">What a Webstore Includes</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• store branding and public URL</li>
          <li>• selected products from the master product catalog</li>
          <li>• optional price overrides</li>
          <li>• customer checkout</li>
          <li>• order records that can create jobs automatically</li>
        </ul>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Best Practice</h2>
        <p className="text-gray-300">Use the Products module to maintain reusable product data, then use Webstores to decide which products a specific store should expose and at what price.</p>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/employees" className="text-gray-400 hover:text-white">← Employees</Link>
        <Link to="/docs/customer-portal" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Customer Portal <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
