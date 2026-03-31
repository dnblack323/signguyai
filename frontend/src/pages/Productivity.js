import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { BarChart3, CalendarDays, KanbanSquare, ListTodo, Loader2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { ProductivityFiltersBar } from '../components/productivity/ProductivityFiltersBar';
import { ProductivityItemDialog } from '../components/productivity/ProductivityItemDialog';
import { ProductivityDashboardView } from '../components/productivity/ProductivityDashboardView';
import { ProductivityTaskListView } from '../components/productivity/ProductivityTaskListView';
import { ProductivityKanbanView } from '../components/productivity/ProductivityKanbanView';
import { ProductivityCalendarView } from '../components/productivity/ProductivityCalendarView';
import { parseItemDate, sortItemsByDate } from '../lib/productivity';

const buildCommonParams = (filters) => {
  const params = { include_completed: filters.includeCompleted };
  if (filters.search) params.search = filters.search;
  if (filters.assignedUserId) params.assigned_user_ids = filters.assignedUserId;
  if (filters.status) params.statuses = filters.status;
  if (filters.itemTypes.length) params.item_types = filters.itemTypes.join(',');
  return params;
};

const VIEW_OPTIONS = [
  { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
  { id: 'calendar', label: 'Calendar', icon: CalendarDays },
  { id: 'kanban', label: 'Kanban Board', icon: KanbanSquare },
  { id: 'tasks', label: 'Task List', icon: ListTodo },
];

export default function Productivity() {
  const { api, employees, fetchEmployees } = useApp();
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState(() => searchParams.get('view') || 'calendar');
  const [calendarView, setCalendarView] = useState(() => searchParams.get('calendar') || 'month');
  const [anchorDate, setAnchorDate] = useState(() => searchParams.get('date') || format(new Date(), 'yyyy-MM-dd'));
  const [filters, setFilters] = useState({
    search: '',
    assignedUserId: '',
    status: '',
    includeCompleted: false,
    itemTypes: ['task', 'job', 'production_task', 'schedule_shift', 'appointment'],
  });
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [calendarPayload, setCalendarPayload] = useState({ items: [], range: null, summary: null });
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);

  useEffect(() => {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.set('view', activeView);
      next.set('calendar', calendarView);
      next.set('date', anchorDate);
      return next;
    });
  }, [activeView, calendarView, anchorDate, setSearchParams]);

  const loadCore = async () => {
    setLoading(true);
    try {
      await fetchEmployees();
      const params = buildCommonParams(filters);
      const [itemsRes, summaryRes] = await Promise.all([
        api.get('/productivity/items', { params }),
        api.get('/productivity/summary', { params: { ...params, include_completed: true } }),
      ]);
      setItems(itemsRes.data.items || []);
      setSummary(summaryRes.data || null);
    } finally {
      setLoading(false);
    }
  };

  const loadCalendar = async () => {
    const params = { ...buildCommonParams(filters), anchor_date: anchorDate, view: calendarView };
    const response = await api.get('/productivity/calendar-range', { params });
    setCalendarPayload(response.data || { items: [], range: null, summary: null });
  };

  useEffect(() => { loadCore(); }, [filters.search, filters.assignedUserId, filters.status, filters.includeCompleted, filters.itemTypes.join(',')]);
  useEffect(() => { loadCalendar(); }, [anchorDate, calendarView, filters.search, filters.assignedUserId, filters.status, filters.includeCompleted, filters.itemTypes.join(',')]);

  const dayItems = useMemo(() => {
    if (!selectedDay) return [];
    return sortItemsByDate((calendarPayload.items || []).filter((item) => {
      const itemDate = parseItemDate(item);
      return itemDate && format(itemDate, 'yyyy-MM-dd') === format(selectedDay, 'yyyy-MM-dd');
    }));
  }, [calendarPayload.items, selectedDay]);

  if (loading && !summary) {
    return <div className="flex items-center justify-center py-24"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;
  }

  return (
    <div className="space-y-6" data-testid="productivity-page-unified">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-4xl font-bold text-white font-heading">Productivity</h1>
          <p className="text-slate-300 mt-1">Calendar, Kanban, Task List, and Dashboard now pull from one unified productivity layer.</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="productivity-view-nav">
        {VIEW_OPTIONS.map((view) => (
          <Button key={view.id} variant={activeView === view.id ? 'default' : 'outline'} onClick={() => setActiveView(view.id)} data-testid={`productivity-nav-${view.id}`}>
            <view.icon className="w-4 h-4 mr-2" /> {view.label}
          </Button>
        ))}
      </div>

      <ProductivityFiltersBar filters={filters} setFilters={setFilters} employees={employees || []} />

      {activeView === 'dashboard' && <ProductivityDashboardView items={items} summary={summary || {}} onOpenItem={setSelectedItem} />}
      {activeView === 'tasks' && <ProductivityTaskListView items={items} onOpenItem={setSelectedItem} />}
      {activeView === 'kanban' && <ProductivityKanbanView items={items.filter((item) => ['task', 'job', 'production_task'].includes(item.type))} onOpenItem={setSelectedItem} />}
      {activeView === 'calendar' && (
        <ProductivityCalendarView
          calendarView={calendarView}
          anchorDate={anchorDate}
          setAnchorDate={setAnchorDate}
          items={calendarPayload.items || []}
          onOpenItem={setSelectedItem}
          onOpenDay={(day, action) => {
            if (action === 'month' || action === 'week' || action === 'day') {
              setCalendarView(action);
              return;
            }
            if (day) setSelectedDay(day);
          }}
        />
      )}

      <ProductivityItemDialog item={selectedItem} open={!!selectedItem} onClose={() => setSelectedItem(null)} />

      <Dialog open={!!selectedDay} onOpenChange={() => setSelectedDay(null)}>
        <DialogContent className="sm:max-w-[620px]" data-testid="productivity-day-detail-dialog">
          <DialogHeader>
            <DialogTitle>{selectedDay ? format(selectedDay, 'EEEE, MMMM d, yyyy') : 'Day Detail'}</DialogTitle>
            <DialogDescription>All unified productivity items for this day.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {dayItems.length === 0 ? (
              <Card className="bg-white border-gray-200"><CardContent className="p-6 text-center text-gray-500">No items scheduled for this day.</CardContent></Card>
            ) : dayItems.map((item) => (
              <Card key={item.uid} className="bg-white border-gray-200">
                <CardContent className="p-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-gray-900">{item.title}</p>
                    <p className="text-sm text-gray-500 mt-1">{item.customer_name || item.source_label || item.type}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => { setSelectedItem(item); }} data-testid={`day-detail-open-${item.uid}`}>Open</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}