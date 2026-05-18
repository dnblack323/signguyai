// Phase 2C: Horizontal pipeline chip bar.
// Reads pipeline_state from wrap_data (Phase 2C backend) to light up chips
// that correspond to completed/active wrap workflow stages. Falls back to
// the simple currentStatus index when pipeline_state is not yet present.
import { WRAP_PIPELINE } from './constants';

// Map each pipeline label to the boolean key on wrap_data.pipeline_state
// that determines whether the chip should render as "complete".
const PIPELINE_KEY_MAP = {
  Lead: null, // always shown but never "complete"
  Estimate: 'estimate_complete',
  Measurements: 'measurements_complete',
  'Quote Sent': 'quote_sent',
  'Contract Sent': 'contract_sent',
  'Contract Signed': 'contract_signed',
  'Deposit Paid': 'deposit_paid',
  Design: null,
  'Proof Sent': 'proof_sent',
  Approved: 'proof_approved',
  Production: 'production_complete',
  Inspection: 'inspection_complete',
  Install: 'install_complete',
  Aftercare: 'aftercare_complete',
  Complete: 'workflow_complete',
};

export default function WrapStatusBar({ currentStatus, pipelineState, testId }) {
  const ps = pipelineState || {};
  // Determine "current" index: the first pipeline entry whose state is not yet done.
  let activeIdx = -1;
  if (pipelineState) {
    for (let i = 0; i < WRAP_PIPELINE.length; i++) {
      const key = PIPELINE_KEY_MAP[WRAP_PIPELINE[i]];
      if (key && !ps[key]) { activeIdx = i; break; }
    }
  } else {
    activeIdx = Math.max(
      0,
      WRAP_PIPELINE.findIndex((s) => s.toLowerCase() === String(currentStatus || '').toLowerCase()),
    );
  }

  return (
    <div className="overflow-x-auto" data-testid={testId || 'wrap-status-bar'}>
      <div className="flex items-center gap-1.5 py-1 min-w-max">
        {WRAP_PIPELINE.map((s, i) => {
          const key = PIPELINE_KEY_MAP[s];
          const isComplete = !!(pipelineState && key && ps[key]);
          const isActive = i === activeIdx && !isComplete;
          let cls = 'bg-slate-50 text-slate-500 border-slate-200';
          if (isActive) cls = 'bg-violet-600 text-white border-violet-600 shadow-sm';
          else if (isComplete) cls = 'bg-emerald-50 text-emerald-700 border-emerald-200';
          return (
            <div
              key={s}
              className={`px-2.5 py-1 rounded-full text-[11px] font-medium border whitespace-nowrap ${cls}`}
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
