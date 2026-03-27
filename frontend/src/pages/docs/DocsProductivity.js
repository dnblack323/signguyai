import { Link } from 'react-router-dom';
import { ArrowRight, Calendar, CheckSquare, Columns3, Clock, ListTodo, Target, Columns } from 'lucide-react';

export default function DocsProductivity() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Columns className="h-4 w-4" /> Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Productivity Tools</h1>
        <p className="text-lg text-gray-400">
          Manage tasks, schedules, and team productivity with integrated planning tools.
        </p>
      </div>

      {/* Task List Section */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <ListTodo className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Task List</h2>
        </div>
        <p className="text-gray-300 mb-4">Your central hub for tracking all work items:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Create Tasks</strong> — Click "New Task" to add tasks with title, description, priority, and due date</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Link to Jobs</strong> — Connect tasks to specific job tickets for production tracking</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Priority Levels</strong> — Mark tasks as Low, Normal, High, or Urgent</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Quick Actions</strong> — Check off tasks as complete, edit details, or delete</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Filtering</strong> — View All, Incomplete, or Completed tasks</span>
          </li>
        </ul>
      </div>

      {/* Calendar Section */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Calendar className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Calendar View</h2>
        </div>
        <p className="text-gray-300 mb-4">See your tasks and deadlines in a visual calendar format:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Month View</strong> — See all tasks with due dates plotted on a monthly calendar</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Day Selection</strong> — Click any day to see tasks due that day</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Visual Indicators</strong> — Days with tasks show colored dots</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Today Highlight</strong> — Current date is highlighted for easy reference</span>
          </li>
        </ul>
      </div>

      {/* Kanban Section */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Columns3 className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Kanban Board</h2>
        </div>
        <p className="text-gray-300 mb-4">Visual project management with drag-and-drop columns:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Default Columns</strong> — To Do, In Progress, Review, and Done</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Drag & Drop</strong> — Move tasks between columns by dragging them</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Status Sync</strong> — Column position automatically syncs with task status</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckSquare className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Card Details</strong> — Each card shows title, priority badge, and due date</span>
          </li>
        </ul>
      </div>

      {/* Task Properties */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Task Properties</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-3">
          {[
            { name: 'Title', desc: 'Brief name of the task (required)' },
            { name: 'Description', desc: 'Detailed notes about the work' },
            { name: 'Due Date', desc: 'When the task should be completed' },
            { name: 'Priority', desc: 'Low, Normal, High, or Urgent' },
            { name: 'Linked Job', desc: 'Connect to a specific job ticket' },
            { name: 'Status', desc: 'Complete or Incomplete' },
          ].map(item => (
            <div key={item.name} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
              <p className="font-medium text-white">{item.name}</p>
              <p className="text-xs text-gray-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Best Practices */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-semibold text-white">Best Practices</h2>
        </div>
        <ul className="space-y-2 text-gray-300">
          <li>• Use the <strong className="text-white">Task List</strong> for daily to-dos and quick task management</li>
          <li>• Use the <strong className="text-white">Calendar</strong> for planning ahead and seeing deadlines</li>
          <li>• Use the <strong className="text-white">Kanban</strong> for visual workflow management on larger projects</li>
          <li>• Link tasks to job tickets to keep production work organized</li>
          <li>• Review incomplete tasks at start and end of each day</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/financials" className="text-gray-400 hover:text-white">← Financial Tracking</Link>
        <Link to="/docs/faq" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">FAQ <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
