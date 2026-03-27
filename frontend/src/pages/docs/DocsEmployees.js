import { Link } from 'react-router-dom';
import { ArrowLeft, UserCog, Users, Calendar, Clock } from 'lucide-react';

export default function DocsEmployees() {
  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/docs" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Docs
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Employees & Team Management</h1>
      <p className="text-gray-500 mb-8">Manage employees, time tracking, scheduling, and payroll</p>

      <div className="space-y-8">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><UserCog className="w-5 h-5 text-violet-600" /> Employee Setup</h2>
          <ol className="list-decimal pl-6 space-y-2 text-gray-700">
            <li>Go to <strong>Team → Users</strong> to add employees</li>
            <li>Set name, email, and role (Owner, Admin, Staff)</li>
            <li>Set hourly rate for payroll calculations</li>
            <li>Generate or assign a PIN for kiosk clock-in</li>
            <li>Review portal permissions for what they can access</li>
          </ol>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Clock className="w-5 h-5 text-violet-600" /> Time Tracking</h2>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li><strong>Clock In/Out</strong> — employees punch in via portal or kiosk</li>
            <li><strong>Break tracking</strong> — start/end breaks during shift</li>
            <li><strong>Job timers</strong> — track time on specific jobs</li>
            <li><strong>Manual hours</strong> — admin can add/edit time entries</li>
            <li><strong>Timesheet editing</strong> — admin can correct any entry via the edit button</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Calendar className="w-5 h-5 text-violet-600" /> Employee Schedule</h2>
          <p className="text-gray-700 mb-3">Create weekly work schedules for your team:</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li>Go to <strong>Team → Payroll → Schedule tab</strong></li>
            <li>Weekly grid shows all employees (Mon-Sun)</li>
            <li>Click any cell to set start time, end time, and notes</li>
            <li>Assigned shifts show in purple with times displayed</li>
            <li>Clear a shift by clicking it and pressing "Clear"</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Users className="w-5 h-5 text-violet-600" /> Employee Portal</h2>
          <p className="text-gray-700 mb-3">Each employee gets their own portal with:</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li>Clock in / clock out / breaks</li>
            <li>Personal work summary and hours</li>
            <li>Assigned job tickets and production tasks</li>
            <li>Stage actions: start, pause, complete</li>
            <li>Task list and pay/profile areas</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Payroll</h2>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li><strong>Overview</strong> — total hours, regular/overtime, gross pay, net owed</li>
            <li><strong>Timesheets</strong> — consolidated view per employee with edit capability</li>
            <li><strong>Time Entries</strong> — add manual hours, edit existing entries</li>
            <li><strong>Transactions</strong> — record advances, payments, bonuses</li>
            <li><strong>Schedule</strong> — weekly shift planning</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
