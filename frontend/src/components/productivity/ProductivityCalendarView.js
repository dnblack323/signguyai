import { addDays, addMonths, addWeeks, eachDayOfInterval, format, isSameDay, startOfDay, subDays, subMonths, subWeeks } from 'date-fns';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent } from '../ui/card';
import { formatCalendarTitle, getCalendarRange, getItemBadgeClass, parseItemDate, sortItemsByDate } from '../../lib/productivity';

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const groupItemsByDay = (items) => {
  const grouped = {};
  items.forEach((item) => {
    const itemDate = parseItemDate(item);
    if (!itemDate) return;
    const key = format(itemDate, 'yyyy-MM-dd');
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(item);
  });
  return grouped;
};

export const ProductivityCalendarView = ({ calendarView, anchorDate, setAnchorDate, items, onOpenItem, onOpenDay }) => {
  const baseDate = new Date(anchorDate);
  const grouped = groupItemsByDay(items);
  const { start, end } = getCalendarRange(calendarView, anchorDate);
  const days = eachDayOfInterval({ start, end });

  const moveRange = (direction) => {
    if (calendarView === 'day') setAnchorDate(format(addDays(baseDate, direction), 'yyyy-MM-dd'));
    else if (calendarView === 'week') setAnchorDate(format(addWeeks(baseDate, direction), 'yyyy-MM-dd'));
    else setAnchorDate(format(addMonths(baseDate, direction), 'yyyy-MM-dd'));
  };

  return (
    <div className="space-y-4" data-testid="productivity-calendar-view">
      <div className="rounded-2xl border border-gray-200 bg-white p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setAnchorDate(format(new Date(), 'yyyy-MM-dd'))} data-testid="calendar-today-button">Today</Button>
            <Button variant="outline" size="sm" onClick={() => moveRange(-1)} data-testid="calendar-prev-button">Previous</Button>
            <Button variant="outline" size="sm" onClick={() => moveRange(1)} data-testid="calendar-next-button">Next</Button>
          </div>
          <h2 className="text-xl font-semibold text-gray-900" data-testid="calendar-range-title">{formatCalendarTitle(calendarView, anchorDate)}</h2>
          <div className="flex items-center gap-2">
            {['month', 'week', 'day'].map((view) => (
              <Button key={view} variant={calendarView === view ? 'default' : 'outline'} size="sm" onClick={() => onOpenDay(undefined, view)} data-testid={`calendar-view-${view}`}>
                {view.charAt(0).toUpperCase() + view.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {calendarView === 'month' && (
        <div className="rounded-2xl border border-gray-200 bg-white overflow-hidden">
          <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
            {DAY_NAMES.map((day) => <div key={day} className="px-3 py-2 text-sm font-semibold text-gray-600">{day}</div>)}
          </div>
          <div className="grid grid-cols-7">
            {days.map((day) => {
              const key = format(day, 'yyyy-MM-dd');
              const dayItems = sortItemsByDate(grouped[key] || []);
              return (
                <button key={key} className="min-h-[150px] border-b border-r border-gray-200 p-2 align-top text-left hover:bg-violet-50/40 transition-colors" onClick={() => onOpenDay(day, 'modal')} data-testid={`calendar-day-${key}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-900">{format(day, 'd')}</span>
                    <span className="text-[10px] text-gray-400">{dayItems.length || ''}</span>
                  </div>
                  <div className="space-y-1">
                    {dayItems.slice(0, 3).map((item) => (
                      <div key={item.uid} className={`rounded-md border px-2 py-1 text-[11px] font-medium truncate ${getItemBadgeClass(item)}`} onClick={(event) => { event.stopPropagation(); onOpenItem(item); }} data-testid={`calendar-item-${item.uid}`}>
                        {item.title}
                      </div>
                    ))}
                    {dayItems.length > 3 && <div className="text-[11px] text-gray-500 font-medium">+{dayItems.length - 3} more</div>}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {calendarView !== 'month' && (
        <div className="grid gap-4 lg:grid-cols-7">
          {days.map((day) => {
            const key = format(day, 'yyyy-MM-dd');
            const dayItems = sortItemsByDate(grouped[key] || []);
            return (
              <Card key={key} className="bg-white border-gray-200">
                <CardContent className="p-4 space-y-3">
                  <button className="text-left" onClick={() => onOpenDay(day, 'modal')} data-testid={`calendar-column-${key}`}>
                    <p className="text-xs uppercase tracking-wide text-gray-500">{format(day, 'EEE')}</p>
                    <p className="text-lg font-semibold text-gray-900">{format(day, calendarView === 'day' ? 'MMMM d' : 'd')}</p>
                  </button>
                  {dayItems.length === 0 ? (
                    <p className="text-sm text-gray-400">No items</p>
                  ) : dayItems.map((item) => (
                    <button key={item.uid} className="w-full rounded-lg border border-gray-200 p-3 text-left hover:border-violet-300 transition-colors" onClick={() => onOpenItem(item)} data-testid={`calendar-detail-item-${item.uid}`}>
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                        <Badge className={getItemBadgeClass(item)}>{item.status.replace(/_/g, ' ')}</Badge>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">{item.start_datetime ? new Date(item.start_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : item.due_datetime ? `Due ${new Date(item.due_datetime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'All day'}</p>
                    </button>
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};