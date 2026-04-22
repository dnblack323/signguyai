import { Sparkles, Clock, ArrowRight, ListOrdered, Mail } from 'lucide-react';
import AssistantSavedCommands from './AssistantSavedCommands';
import AssistantSmartDefault from './AssistantSmartDefault';

/**
 * Empty / idle state for the Business Assistant.
 * Shows example prompts + recent commands + saved pinned commands + smart default.
 */
const DEFAULT_EXAMPLES = [
  { label: 'Show overdue invoices', icon: '📊' },
  { label: 'What jobs are due tomorrow?', icon: '📅' },
  { label: 'Revenue this week vs last week', icon: '📈' },
  { label: 'Who worked the most hours this week?', icon: '🕒' },
];

export default function AssistantEmptyState({
  token,
  pageContext,
  recentCommands = [],
  savedRefreshKey,
  onExampleClick,
  onOpenRoutines,
  onTriggerBulkReminders,
}) {
  return (
    <div className="space-y-3 p-2" data-testid="assistant-empty-state">
      <div className="flex items-start gap-2 px-1">
        <Sparkles className="h-4 w-4 text-violet-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="text-sm font-semibold text-slate-800">Ask me about your shop</div>
          <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
            Live data queries, navigation, record creation, and more.
            {pageContext?.record_label
              ? <> Currently on <span className="font-medium text-violet-700">{pageContext.record_label}</span>.</>
              : null}
          </p>
        </div>
      </div>

      {/* Smart default: recent customer chip */}
      {token && (
        <div className="flex flex-wrap gap-1.5 px-1">
          <AssistantSmartDefault token={token} onPick={onExampleClick} />
        </div>
      )}

      {/* Quick automation launchers */}
      <div className="flex flex-wrap gap-1.5 px-1">
        {onOpenRoutines && (
          <button
            type="button"
            onClick={onOpenRoutines}
            data-testid="assistant-open-routines"
            className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-300 px-2 py-0.5 text-[11px] text-slate-700 hover:border-violet-300 hover:text-violet-700 transition"
          >
            <ListOrdered className="h-3 w-3" /> Routines
          </button>
        )}
        {onTriggerBulkReminders && (
          <button
            type="button"
            onClick={onTriggerBulkReminders}
            data-testid="assistant-bulk-reminders-chip"
            className="inline-flex items-center gap-1 rounded-full bg-white border border-slate-300 px-2 py-0.5 text-[11px] text-slate-700 hover:border-violet-300 hover:text-violet-700 transition"
          >
            <Mail className="h-3 w-3" /> Remind overdue
          </button>
        )}
      </div>

      {/* Pinned/saved commands */}
      {token && (
        <AssistantSavedCommands
          token={token}
          refreshKey={savedRefreshKey}
          onRunCommand={onExampleClick}
        />
      )}

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
