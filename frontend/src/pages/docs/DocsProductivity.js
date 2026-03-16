import { Link } from 'react-router-dom';
import { ArrowRight, Columns } from 'lucide-react';

export default function DocsProductivity() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><Columns className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Productivity Tools</h1>
        <p className="text-lg text-gray-400">Productivity is currently centered around real operational tools rather than a large separate planning suite.</p>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Current Productivity Systems</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• job filtering and quick actions</li>
          <li>• assigned employees on jobs</li>
          <li>• employee task views</li>
          <li>• production workflow templates</li>
          <li>• job history / timeline views</li>
          <li>• schedule and task creation from jobs</li>
        </ul>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/financials" className="text-gray-400 hover:text-white">← Financial Tracking</Link>
        <Link to="/docs/faq" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">FAQ <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
