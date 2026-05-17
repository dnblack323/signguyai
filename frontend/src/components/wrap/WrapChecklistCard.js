// Phase 1: Visual-only checklist card. Items are passed in; toggling shows a phase-1 toast.
import { Check, Circle } from 'lucide-react';
import { toast } from 'sonner';
import WrapSectionCard from './WrapSectionCard';
import { TOAST_PHASE1 } from './constants';

export default function WrapChecklistCard({ title = 'Checklist', icon, items = [], testId }) {
  return (
    <WrapSectionCard title={title} icon={icon} testId={testId}>
      <ul className="space-y-1.5">
        {items.map((it, idx) => (
          <li
            key={idx}
            className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer hover:text-slate-900"
            onClick={() => toast.message(it.label, { description: TOAST_PHASE1 })}
            data-testid={`${testId || 'wrap-checklist'}-item-${idx}`}
          >
            {it.done ? (
              <Check className="h-3.5 w-3.5 text-emerald-600 flex-shrink-0" />
            ) : (
              <Circle className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
            )}
            <span className={it.done ? 'line-through text-slate-500' : ''}>{it.label}</span>
          </li>
        ))}
      </ul>
    </WrapSectionCard>
  );
}
