// Used inside cards/tabs where backend data is not yet wired.
import { Sparkles } from 'lucide-react';

export default function WrapEmptyState({ title = 'Coming soon', message, action, testId }) {
  return (
    <div
      className="p-6 text-center border border-dashed border-slate-300 rounded-lg bg-slate-50/50"
      data-testid={testId}
    >
      <Sparkles className="h-5 w-5 mx-auto text-slate-400 mb-2" />
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {message && <p className="text-xs text-slate-500 mt-1">{message}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
