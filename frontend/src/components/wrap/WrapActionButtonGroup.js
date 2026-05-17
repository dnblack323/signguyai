// Phase 1: A row of action buttons; each shows a phase-1 toast on click.
import { Button } from '../ui/button';
import { toast } from 'sonner';
import { TOAST_PHASE1 } from './constants';

export default function WrapActionButtonGroup({ actions = [], testId }) {
  return (
    <div className="flex flex-wrap gap-2" data-testid={testId || 'wrap-action-group'}>
      {actions.map((a, idx) => (
        <Button
          key={idx}
          size="sm"
          variant={a.variant || 'outline'}
          className="text-xs"
          onClick={() => toast.message(a.label, { description: a.message || TOAST_PHASE1 })}
          data-testid={`${testId || 'wrap-action'}-btn-${idx}`}
        >
          {a.icon && <a.icon className="h-3.5 w-3.5 mr-1" />}
          {a.label}
        </Button>
      ))}
    </div>
  );
}
