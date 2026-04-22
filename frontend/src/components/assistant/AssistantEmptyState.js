import { Sparkles, Clock, ArrowRight } from 'lucide-react';

/**
 * Empty / idle state for the Business Assistant.
 * Shows example prompts + recent commands (if localStorage has any).
 */
const DEFAULT_EXAMPLES = [
  { label: 'Show overdue invoices', icon: '📊' },
  { label: 'What jobs are due tomorrow?', icon: '📅' },
  { label: 'Revenue this week vs last week', icon: '📈' },
  { label: 'Who worked the most hours this week?', icon: '🕒' },
  { label: 'Open production schedule', icon: '🛠️' },
  { label: "What's waiting on artwork approval?", icon: '🎨' },
];

export default function AssistantEmptyState({
  pageContext,
  recentCommands = [],
  onExampleClick,
}) {
  return (
    <div className="space-y-3 p-2" data-testid="assistant-empty-state">
      <div className="flex items-start gap-2 px-1">
        <Sparkles className="h-4 w-4 text-violet-500 flex-shrink-0 mt-0.5" />
        <div>
          <div className="text-sm font-semibold text-slate-800">Ask me about your shop</div>
          <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
            Live data queries, navigation, record creation, and more.
            {pageContext?.record_label
              ? <> Currently on <span className="font-medium text-violet-700">{pageContext.record_label}</span>.</>
              : null}
          </p>
        </div>
      </div>

      {!!recentCommands.length && (
        <div>
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-slate-500 font-semibold px-1 mb-1">
            <Clock className="h-3 w-3" /> Recent
          </div>
          <div className="space-y-1">
            {recentCommands.slice(0, 3).map((cmd, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onExampleClick?.(cmd)}
                data-testid={`assistant-recent-cmd-${i}`}
                className="w-full text-left px-2 py-1.5 rounded-md text-xs text-slate-700 hover:bg-violet-50 hover:text-violet-800 border border-transparent hover:border-violet-200 transition flex items-center gap-1.5 group"
              >
                <ArrowRight className="h-3 w-3 text-slate-400 group-hover:text-violet-500" />
                {cmd}
              </button>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold px-1 mb-1">Try</div>
        <div className="space-y-1">
          {DEFAULT_EXAMPLES.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onExampleClick?.(ex.label)}
              data-testid={`assistant-example-${i}`}
              className="w-full text-left px-2 py-1.5 rounded-md text-xs text-slate-700 hover:bg-violet-50 hover:text-violet-800 border border-transparent hover:border-violet-200 transition flex items-center gap-2"
            >
              <span>{ex.icon}</span>
              {ex.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
