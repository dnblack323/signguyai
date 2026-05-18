// Phase 1: Contextual AI helper card placed beside the section it supports.
// Phase 2F polish: cards default to `disabled` since real AI dispatch is
// deliberately deferred. Pass disabled={false} only when a card has a real
// rule-based action wired up.
import { Bot } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { toast } from 'sonner';
import { TOAST_AI_PHASE1 } from './constants';

export default function WrapAIHelperCard({
  title = 'AI Helper',
  description,
  actions = [],
  testId,
  disabled = true,
}) {
  const tone = disabled
    ? 'from-slate-50 to-white border-slate-200'
    : 'from-violet-50 to-white border-violet-200';
  const titleTone = disabled ? 'text-slate-500' : 'text-violet-900';
  const iconTone = disabled ? 'text-slate-400' : 'text-violet-600';
  // Derive a stable group slug from the title for automation testids.
  const slug = (testId || title || 'wrap-ai')
    .toString()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return (
    <Card
      className={`bg-gradient-to-b ${tone}`}
      data-testid={`wrap-ai-helper-card-${slug}`}
    >
      <CardHeader className="pb-2">
        <CardTitle className={`text-sm font-semibold flex items-center gap-2 ${titleTone}`}>
          <Bot className={`h-4 w-4 ${iconTone}`} /> {title}
          {disabled && (
            <span className="ml-auto text-[9px] uppercase tracking-wide bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
              Coming soon
            </span>
          )}
        </CardTitle>
        {description && (
          <CardDescription className={disabled ? 'text-xs text-slate-500' : 'text-xs text-violet-700'}>
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-1.5">
        {actions.map((a, idx) => (
          <Button
            key={idx}
            variant="outline"
            size="sm"
            disabled={disabled}
            className={`w-full justify-start text-xs ${disabled
              ? 'bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-white hover:bg-violet-50 border-violet-200 text-violet-900'}`}
            onClick={() => !disabled && toast.message(a.label, { description: TOAST_AI_PHASE1 })}
            data-testid={`${testId || 'wrap-ai'}-action-${idx}`}
          >
            <Bot className="h-3 w-3 mr-1.5" /> {a.label}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
