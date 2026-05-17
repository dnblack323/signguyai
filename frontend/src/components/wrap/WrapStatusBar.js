// Phase 1: Horizontal pipeline chip bar. Visual only — clicking does nothing
// in phase 1; phase 2 will wire each chip to status transitions.
import { WRAP_PIPELINE } from './constants';

export default function WrapStatusBar({ currentStatus, testId }) {
  const idx = Math.max(0, WRAP_PIPELINE.findIndex((s) => s.toLowerCase() === String(currentStatus || '').toLowerCase()));
  return (
    <div className="overflow-x-auto" data-testid={testId || 'wrap-status-bar'}>
      <div className="flex items-center gap-1.5 py-1 min-w-max">
        {WRAP_PIPELINE.map((s, i) => {
          const isActive = i === idx;
          const isPast = i < idx;
          return (
            <div
              key={s}
              className={`px-2.5 py-1 rounded-full text-[11px] font-medium border whitespace-nowrap ${
                isActive
                  ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
                  : isPast
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-slate-50 text-slate-500 border-slate-200'
              }`}
              data-testid={`wrap-status-chip-${s.toLowerCase().replace(/\W+/g, '-')}`}
            >
              {s}
            </div>
          );
        })}
      </div>
    </div>
  );
}
