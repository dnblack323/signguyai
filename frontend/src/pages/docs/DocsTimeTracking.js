import { Link } from 'react-router-dom';
import { Clock, ArrowRight, Play, Pause, Timer } from 'lucide-react';

export default function DocsTimeTracking() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Clock className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Time Tracking</h1>
        <p className="text-lg text-gray-400">
          Track time on jobs for accurate labor costing and payroll management.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Task Types</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { type: 'Design', color: 'bg-blue-500' },
            { type: 'Production', color: 'bg-green-500' },
            { type: 'Installation', color: 'bg-purple-500' },
            { type: 'Admin', color: 'bg-gray-500' },
          ].map((item) => (
            <div key={item.type} className="p-4 rounded-lg bg-gray-800/50 text-center">
              <div className={`w-3 h-3 rounded-full ${item.color} mx-auto mb-2`} />
              <span className="text-gray-300">{item.type}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Tracking Time on a Job</h2>
        <ol className="space-y-4">
          {[
            { title: 'Open Job Details', desc: 'Click on any job to open its detail page' },
            { title: 'Go to Time Tab', desc: 'Click the "Time" tab to see time tracking options' },
            { title: 'Start Timer', desc: 'Select a task type and click "Start Timer"' },
            { title: 'Work on the Job', desc: 'The timer runs in real-time (HH:MM:SS)' },
            { title: 'Stop Timer', desc: 'Click "Stop" when finished - time is automatically logged' },
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

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Time Summary</h2>
        <p className="text-gray-300 mb-4">
          Each job shows a summary panel with:
        </p>
        <ul className="space-y-2 ml-4">
          {[
            'Total hours worked',
            'Labor cost (based on employee rates)',
            'Number of time entries',
            'Breakdown by task type'
          ].map((item, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-300">
              <Timer className="h-4 w-4 text-cyan-400" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/ai-tools" className="text-gray-400 hover:text-white">
          ← AI Tools Suite
        </Link>
        <Link to="/docs/employees" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Employee Management <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
