// Generic titled card used by every tab of the Wrap Command Center.
// Keeps tab content visually consistent without each tab importing Card primitives directly.
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';

export default function WrapSectionCard({ title, description, icon: Icon, children, action, testId }) {
  return (
    <Card className="bg-white border border-slate-200" data-testid={testId}>
      <CardHeader className="flex flex-row items-start justify-between gap-2 pb-3">
        <div>
          <CardTitle className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            {Icon && <Icon className="h-4 w-4 text-violet-600" />} {title}
          </CardTitle>
          {description && <CardDescription className="text-xs">{description}</CardDescription>}
        </div>
        {action}
      </CardHeader>
      <CardContent className="text-sm text-slate-700">{children}</CardContent>
    </Card>
  );
}
