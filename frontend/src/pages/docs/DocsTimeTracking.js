import { Link } from 'react-router-dom';
import { ArrowRight, Clock, Timer } from 'lucide-react';

export default function DocsTimeTracking() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><Clock className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">Time Tracking</h1>
        <p className="text-lg text-gray-400">SignGuy AI tracks two different kinds of time: employee clock time for payroll and job time for labor/costing history.</p>
      </div>

      {/* Screenshot */}
      <div className="rounded-xl overflow-hidden border border-gray-700">
        <img 
          src="/screenshots/feature_time_clock.jpeg" 
          alt="Time Clock Interface" 
          className="w-full"
        />
        <div className="bg-gray-800/80 px-4 py-2 text-xs text-gray-400">
          Employee time clock and tracking interface
        </div>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Important Distinction</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• <strong className="text-white">Time Clock</strong> = attendance/payroll time</li>
          <li>• <strong className="text-white">Order Timer</strong> = labor time on a specific order</li>
          <li>• These should not be treated as the same dataset</li>
        </ul>
      </div>
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Order Timer Workflow</h2>
        <ol className="space-y-3">
          {['Open Order Details', 'Go to the Time tab', 'Choose a task type', 'Start timer', 'Stop timer when finished', 'Review hours and labor cost in the summary'].map((step, index) => (
            <li key={index} className="flex items-start gap-3 text-gray-300"><span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>{step}</li>
          ))}
        </ol>
      </div>
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <div className="flex items-center gap-2 mb-3"><Timer className="h-5 w-5 text-cyan-400" /><h2 className="text-lg font-semibold text-white">Why It Matters</h2></div>
        <p className="text-gray-300">Order time now feeds labor visibility, payroll review, production history, and future analytics. Even a simple workflow benefits from consistent timer use.</p>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/ai-tools" className="text-gray-400 hover:text-white">← AI Tools Suite</Link>
        <Link to="/docs/employees" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Employee Management <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
