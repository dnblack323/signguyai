// Phase 1: Contextual AI helper card placed beside the section it supports.
// Future phases will replace the placeholder onClick with a real AI dispatch.
import { Bot } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { toast } from 'sonner';
import { TOAST_AI_PHASE1 } from './constants';

export default function WrapAIHelperCard({ title = 'AI Helper', description, actions = [], testId }) {
  return (
    <Card
      className="bg-gradient-to-b from-violet-50 to-white border border-violet-200"
      data-testid={testId || 'wrap-ai-helper'}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-violet-900 flex items-center gap-2">
          <Bot className="h-4 w-4 text-violet-600" /> {title}
        </CardTitle>
        {description && <CardDescription className="text-xs text-violet-700">{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-1.5">
        {actions.map((a, idx) => (
          <Button
            key={idx}
            variant="outline"
            size="sm"
            className="w-full justify-start text-xs bg-white hover:bg-violet-50 border-violet-200 text-violet-900"
            onClick={() => toast.message(a.label, { description: TOAST_AI_PHASE1 })}
            data-testid={`${testId || 'wrap-ai'}-action-${idx}`}
          >
            <Bot className="h-3 w-3 mr-1.5" /> {a.label}
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
