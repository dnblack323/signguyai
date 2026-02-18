import { Link } from 'react-router-dom';
import { Columns, ArrowRight, Calendar, CheckSquare, ListTodo, Clock, Target, Repeat } from 'lucide-react';

export default function DocsProductivity() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Columns className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Productivity Tools</h1>
        <p className="text-lg text-gray-400">
          Stay organized with Kanban boards, to-do lists, and calendar views. Manage your shop's workflow visually and never miss a deadline.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Productivity Suite</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Columns, title: 'Kanban Board', desc: 'Drag-and-drop job management', color: 'bg-blue-500' },
            { icon: CheckSquare, title: 'To-Do Lists', desc: 'Personal and team task tracking', color: 'bg-green-500' },
            { icon: Calendar, title: 'Calendar View', desc: 'See all deadlines at a glance', color: 'bg-purple-500' },
          ].map((item) => (
            <div key={item.title} className="p-4 rounded-lg bg-gray-800/50">
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-8 h-8 rounded-lg ${item.color} flex items-center justify-center`}>
                  <item.icon className="h-4 w-4 text-white" />
                </div>
                <span className="text-white font-medium">{item.title}</span>
              </div>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Kanban Board</h2>
        <p className="text-gray-300 mb-4">
          The Kanban board gives you a visual overview of all your jobs organized by status. Drag cards between columns to update job status instantly.
        </p>
        <div className="grid grid-cols-5 gap-2 p-4 bg-gray-800/30 rounded-lg mb-4">
          {['Quoted', 'Approved', 'In Production', 'Ready', 'Complete'].map((status) => (
            <div key={status} className="text-center">
              <div className="text-xs text-gray-400 mb-2">{status}</div>
              <div className="h-24 bg-gray-700/50 rounded border border-gray-600/50 flex items-center justify-center">
                <span className="text-gray-500 text-xs">Drop jobs here</span>
              </div>
            </div>
          ))}
        </div>
        <ul className="space-y-2 ml-4">
          {[
            'Drag jobs between columns to change status',
            'Click on a job card to view details',
            'Color-coded by priority (red = high, yellow = medium, green = low)',
            'Shows customer name, job title, and due date',
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">To-Do Lists</h2>
        <p className="text-gray-300 mb-4">
          Create personal or team to-do lists to track tasks that aren't tied to specific jobs.
        </p>
        <div className="space-y-4">
          {[
            { icon: ListTodo, title: 'Personal Tasks', desc: 'Private to-do items only you can see' },
            { icon: Target, title: 'Team Tasks', desc: 'Shared tasks visible to your whole team' },
            { icon: Repeat, title: 'Recurring Tasks', desc: 'Set tasks to repeat daily, weekly, or monthly' },
            { icon: Clock, title: 'Due Dates', desc: 'Add deadlines and get reminders' },
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

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Calendar View</h2>
        <p className="text-gray-300 mb-4">
          See all your deadlines, scheduled jobs, and tasks in a calendar format.
        </p>
        <ul className="space-y-2 ml-4">
          {[
            'Month, week, and day views available',
            'Jobs appear on their due dates',
            'Click any date to see all items due',
            'Drag items to reschedule',
            'Color-coded by type (jobs, tasks, events)',
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <Calendar className="h-4 w-4 text-cyan-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
        <h3 className="text-white font-semibold mb-2">Accessing Productivity Tools</h3>
        <p className="text-gray-300">
          Navigate to <strong>"Productivity"</strong> in the sidebar to access the Kanban board, to-do lists, and calendar. You can switch between views using the tabs at the top of the page.
        </p>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/financials" className="text-gray-400 hover:text-white">
          ← Financial Tracking
        </Link>
        <Link to="/docs/faq" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          FAQ <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
