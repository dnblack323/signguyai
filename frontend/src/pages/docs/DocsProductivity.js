import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, CheckSquare, Columns3, Clock, ListTodo, Target, Columns, BarChart3, RefreshCw } from 'lucide-react';

export default function DocsProductivity() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Columns className="h-4 w-4" /> Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Productivity Tools</h1>
        <p className="text-lg text-gray-400">
          One unified productivity system for planning, scheduling, workflow tracking, and day-to-day execution.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
        <div className="flex items-center gap-2 mb-4">
          <RefreshCw className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">One Record, Multiple Views</h2>
        </div>
        <p className="text-gray-300 mb-4">
          Productivity now uses one shared data layer. The same work item can appear in the Task List, Calendar, Kanban Board, and Productivity Dashboard without being re-entered.
        </p>
        <ul className="space-y-2 text-gray-300">
          <li>• Shared item types include tasks, jobs/orders, production tasks, employee schedule items, and appointments.</li>
          <li>• Status or due date updates write back to the original source record.</li>
          <li>• Changes stay in sync across Task List, Calendar, Kanban, and Dashboard widgets.</li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Productivity Dashboard</h2>
        </div>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Command Center</strong> — See Due Today, Overdue, Waiting on Approval, and Scheduled This Week in one place.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Shared Summary</strong> — Dashboard widgets use the same unified productivity query layer as the other views.</span></li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <ListTodo className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Task List</h2>
        </div>
        <p className="text-gray-300 mb-4">Your central hub for tracking and editing open work:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Unified Work Items</strong> — View tasks, jobs/orders, production tasks, appointments, and schedule-driven items in one list.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Inline Updates</strong> — Change status, due date, assignee, priority, and completion state directly in the list where supported.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Source-Aware Editing</strong> — Edits write back to the real source record instead of a duplicate task copy.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Quick Actions</strong> — Complete/reopen work, open source details, or adjust planning fields quickly.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Shared Filters</strong> — Search and filter by type, status, assignee, and completion state.</span></li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Calendar View</h2>
        </div>
        <p className="text-gray-300 mb-4">Plan work visually from the same shared productivity records:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Large Month View</strong> — Month is the default and shows readable day cells with multiple visible items.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Week & Day Views</strong> — Switch between Month, Week, and Day without leaving Productivity.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Day Detail</strong> — Click a day to open all work scheduled or due on that date.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Shared Sync</strong> — Calendar details stay in sync with Kanban, Task List, and Dashboard summaries.</span></li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Columns3 className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Kanban Board</h2>
        </div>
        <p className="text-gray-300 mb-4">Visual workflow management with persisted status changes:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Workflow Columns</strong> — Jobs and tasks group by their shared board/status column.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Drag & Drop</strong> — Move cards between columns and write the change back to the correct source record.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Cross-View Sync</strong> — Column moves update the Task List, Calendar details, and Dashboard widgets automatically.</span></li>
          <li className="flex items-start gap-2"><CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" /><span><strong className="text-white">Card Details</strong> — Cards can show title, customer, due date, priority, and source-aware context.</span></li>
        </ul>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Shared Item Properties</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { name: 'Title', desc: 'Shared title used in all productivity views' },
            { name: 'Type', desc: 'Task, job/order, production task, appointment, or schedule item' },
            { name: 'Due / Start Date', desc: 'Drives calendar placement and due tracking' },
            { name: 'Priority', desc: 'Normal, High, Urgent, Rush where supported' },
            { name: 'Assigned User', desc: 'Used for planning, task views, and scheduling context' },
            { name: 'Status / Board Column', desc: 'Shared workflow status used by Kanban and summary widgets' },
          ].map(item => (
            <div key={item.name} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
              <p className="font-medium text-white">{item.name}</p>
              <p className="text-xs text-gray-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Best Practices</h2>
        </div>
        <ul className="space-y-2 text-gray-300">
          <li>• Use <strong className="text-white">Dashboard</strong> for quick triage and daily priorities</li>
          <li>• Use <strong className="text-white">Calendar</strong> for planning dates and capacity</li>
          <li>• Use <strong className="text-white">Task List</strong> for direct edits and cleanup work</li>
          <li>• Use <strong className="text-white">Kanban</strong> for workflow movement and status-driven planning</li>
          <li>• Remember: editing in one productivity view updates the same underlying record everywhere else</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/financials" className="text-gray-400 hover:text-white">← Financial Tracking</Link>
        <Link to="/docs/faq" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">FAQ <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}