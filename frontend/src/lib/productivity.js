import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek } from 'date-fns';

export const PRODUCTIVITY_TYPE_LABELS = {
  task: 'Task',
  job: 'Order',
  production_task: 'Production Task',
  schedule_shift: 'Schedule',
  appointment: 'Appointment',
};

export const PRODUCTIVITY_COLOR_CLASSES = {
  red: 'bg-red-100 text-red-700 border-red-200',
  amber: 'bg-amber-100 text-amber-800 border-amber-200',
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  emerald: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  violet: 'bg-violet-100 text-violet-700 border-violet-200',
  teal: 'bg-teal-100 text-teal-700 border-teal-200',
  slate: 'bg-slate-100 text-slate-700 border-slate-200',
};

export const getItemBadgeClass = (item) => PRODUCTIVITY_COLOR_CLASSES[item.color] || PRODUCTIVITY_COLOR_CLASSES.slate;

export const parseItemDate = (item) => {
  const dateValue = item.start_datetime || item.due_datetime;
  return dateValue ? new Date(dateValue) : null;
};

export const formatCalendarTitle = (view, anchorDate) => {
  const date = new Date(anchorDate);
  if (view === 'day') return format(date, 'EEEE, MMMM d, yyyy');
  if (view === 'week') {
    const start = startOfWeek(date, { weekStartsOn: 1 });
    const end = endOfWeek(date, { weekStartsOn: 1 });
    return `${format(start, 'MMM d')} – ${format(end, 'MMM d, yyyy')}`;
  }
  return format(date, 'MMMM yyyy');
};

export const getCalendarRange = (view, anchorDate) => {
  const date = new Date(anchorDate);
  if (view === 'day') return { start: date, end: date };
  if (view === 'week') {
    return {
      start: startOfWeek(date, { weekStartsOn: 1 }),
      end: endOfWeek(date, { weekStartsOn: 1 }),
    };
  }
  return {
    start: startOfWeek(startOfMonth(date), { weekStartsOn: 1 }),
    end: endOfWeek(endOfMonth(date), { weekStartsOn: 1 }),
  };
};

export const sortItemsByDate = (items) => [...items].sort((left, right) => {
  const leftDate = parseItemDate(left)?.getTime() || 0;
  const rightDate = parseItemDate(right)?.getTime() || 0;
  return leftDate - rightDate;
});