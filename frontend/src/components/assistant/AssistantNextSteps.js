import { ArrowRight, Sparkles } from 'lucide-react';

/**
 * Renders 1–3 next-step suggestions returned by /next-step-suggestions.
 * Each suggestion is either a "navigate" target or a "rerun_command".
 */
export default function AssistantNextSteps({ suggestions = [], onAction }) {
  if (!suggestions?.length) return null;
  return (
    <div
      className="rounded-lg border border-violet-100 bg-violet-50/60 px-2.5 py-2 space-y-1"
      data-testid="assistant-next-steps"
    >
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide font-semibold text-violet-700">
        <Sparkles className="h-3 w-3" /> Next step
      </div>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onAction?.(s)}
            data-testid={`assistant-next-step-${s.id}`}
            className="inline-flex items-center gap-1 rounded-full bg-white border border-violet-200 text-violet-700 px-2 py-0.5 text-[11px] font-medium hover:bg-violet-100 hover:border-violet-300 transition"
          >
            {s.label}
            <ArrowRight className="h-3 w-3" />
          </button>
        ))}
      </div>
    </div>
  );
}
