import { Link } from 'react-router-dom';
import { ArrowRight, Shield, UserCog, Users } from 'lucide-react';

export default function DocsEmployees() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><UserCog className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Employees & Employee Portal</h1>
        <p className="text-lg text-gray-400">Employees can clock in, see assigned jobs, act on production stages, and use their own portal. Admins control what they can and cannot see.</p>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Core Employee Setup</h2>
        <ol className="space-y-3">
          {['Add employee record', 'Set email and role', 'Set hourly rate', 'Generate or assign PIN', 'Review portal permissions', 'Assign jobs or stages as needed'].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300"><span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>{step}</li>
          ))}
        </ol>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4"><Users className="h-5 w-5 text-cyan-400" /><h2 className="text-lg font-semibold text-white">Employee Portal</h2></div>
        <ul className="space-y-2 text-gray-300">
          <li>• clock in / clock out / breaks</li>
          <li>• personal work summary</li>
          <li>• assigned jobs</li>
          <li>• stage start / pause / complete actions</li>
          <li>• tasks and pay/profile areas</li>
        </ul>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4"><Shield className="h-5 w-5 text-cyan-400" /><h2 className="text-lg font-semibold text-white">Permission Model</h2></div>
        <p className="text-gray-300 mb-3">Employees should only see what their role needs. Sensitive toggles exist for:</p>
        <ul className="space-y-2 text-gray-300">
          <li>• job details</li>
          <li>• customer information</li>
          <li>• pricing visibility</li>
        </ul>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/time-tracking" className="text-gray-400 hover:text-white">← Time Tracking</Link>
        <Link to="/docs/webstores" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Webstores <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
