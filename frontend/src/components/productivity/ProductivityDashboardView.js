import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { sortItemsByDate } from '../../lib/productivity';

const Widget = ({ title, value, items, onOpenItem }) => (
  <Card className="bg-white border-gray-200">
    <CardHeader className="pb-3">
      <CardTitle className="flex items-center justify-between text-base text-gray-900">
        <span>{title}</span>
        <Badge variant="outline">{value}</Badge>
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-2">
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Nothing here.</p>
      ) : sortItemsByDate(items).slice(0, 4).map((item) => (
        <button key={item.uid} className="w-full rounded-lg border border-gray-200 p-3 text-left hover:border-violet-300 transition-colors" onClick={() => onOpenItem(item)} data-testid={`dashboard-item-${item.uid}`}>
          <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
          <p className="text-xs text-gray-500 mt-1">{item.customer_name || item.source_label || item.type}</p>
        </button>
      ))}
    </CardContent>
  </Card>
);

export const ProductivityDashboardView = ({ items, summary, onOpenItem }) => {
  const today = new Date().toISOString().slice(0, 10);
  const dueTodayItems = items.filter((item) => item.due_datetime?.slice(0, 10) === today && !item.is_completed);
  const overdueItems = items.filter((item) => item.due_datetime?.slice(0, 10) < today && !item.is_completed);
  const waitingItems = items.filter((item) => ['pending', 'awaiting_approval', 'awaiting_quote', 'awaiting_review'].includes(item.status));
  const scheduledItems = items.filter((item) => item.start_datetime && !item.is_completed);

  return (
    <div className="space-y-6" data-testid="productivity-dashboard-view">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ['Due Today', summary.due_today],
          ['Overdue', summary.overdue],
          ['Waiting on Approval', summary.waiting_on_approval],
          ['Scheduled This Week', summary.scheduled_this_week],
        ].map(([label, value]) => (
          <Card key={label} className="bg-white border-gray-200">
            <CardContent className="p-5">
              <p className="text-xs uppercase tracking-wide text-gray-500">{label}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-4">
        <Widget title="Due Today" value={dueTodayItems.length} items={dueTodayItems} onOpenItem={onOpenItem} />
        <Widget title="Overdue" value={overdueItems.length} items={overdueItems} onOpenItem={onOpenItem} />
        <Widget title="Waiting on Approval" value={waitingItems.length} items={waitingItems} onOpenItem={onOpenItem} />
        <Widget title="Upcoming Schedule" value={scheduledItems.length} items={scheduledItems} onOpenItem={onOpenItem} />
      </div>
    </div>
  );
};