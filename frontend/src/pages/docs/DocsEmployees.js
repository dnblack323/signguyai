import { Link } from 'react-router-dom';
import { UserCog, ArrowRight, Users, Key, Shield } from 'lucide-react';

export default function DocsEmployees() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <UserCog className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Employee Management</h1>
        <p className="text-lg text-gray-400">
          Add team members, assign roles, and give them access to the Employee Portal.
        </p>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Adding an Employee</h2>
        <ol className="space-y-3">
          {[
            'Navigate to Settings > Employees from the sidebar',
            'Click "Add Employee"',
            'Enter name, email, phone, and hourly rate',
            'Assign a role (Admin, Manager, or Staff)',
            'Set their PIN (default: 1234)'
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{i + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Employee Roles</h2>
        </div>
        <div className="space-y-4">
          {[
            { role: 'Admin', desc: 'Full access to all features, can manage other employees' },
            { role: 'Manager', desc: 'Can manage customers, jobs, and view reports' },
            { role: 'Staff', desc: 'Basic access to assigned tasks and time clock' },
          ].map((item) => (
            <div key={item.role} className="p-4 rounded-lg bg-gray-800/50">
              <strong className="text-white">{item.role}</strong>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Employee Portal</h2>
        <p className="text-gray-300 mb-4">
          Employees can access a dedicated portal at <code className="bg-gray-800 px-2 py-1 rounded">/employee-portal/login</code>
        </p>
        <p className="text-gray-300 mb-4">Portal features include:</p>
        <ul className="space-y-2 ml-4">
          {[
            'Clock in/out with break management',
            'View assigned tasks',
            'See pay information and history',
            'Update profile and PIN'
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <Users className="h-4 w-4 text-cyan-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/time-tracking" className="text-gray-400 hover:text-white">
          ← Time Tracking
        </Link>
        <Link to="/docs/faq" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          FAQ <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
