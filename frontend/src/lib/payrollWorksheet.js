const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const DAY_ORDER = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

const pad = (value) => String(value).padStart(2, '0');

// Detect whether an ISO string carries a timezone designator.
const hasTzSuffix = (iso) => /[Zz]$|[+-]\d{2}:?\d{2}$/.test(iso);

// Convert an ISO datetime from the backend into the user's local HH:MM.
// IMPORTANT: the backend stores two different shapes in `clock_in`/`clock_out`:
//   (a) Real-time punches: UTC with +00:00 suffix (e.g. "2026-04-21T02:00:00+00:00")
//   (b) Manual worksheet entries: naive local "YYYY-MM-DDTHH:MM:00" (no tz)
// Shape (a) needs UTC → local conversion. Shape (b) is ALREADY local — slice as-is.
// Falls back to empty string on parse failure.
const isoToLocalHHMM = (iso) => {
  if (!iso) return '';
  if (!hasTzSuffix(iso)) {
    // Naive ISO: the stored value already represents local clock time.
    // Returning chars 11-15 preserves historical worksheet behavior.
    return iso.slice(11, 16);
  }
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

// Convert local date + HH:MM → naive ISO ("YYYY-MM-DDTHH:MM:00").
// We deliberately keep the naive shape here (no timezone suffix) so that
// new worksheet entries match the historical storage format and round-trip
// via `isoToLocalHHMM` without drift. Real-time punches continue to write
// UTC timestamps via the backend _now_iso() helper.
const localDateTimeToIsoUtc = (date, time) => {
  if (!date || !time) return null;
  return `${date}T${time}:00`;
};

const normalizeDate = (value) => {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
};

const toDateString = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;

export const getTodayDate = () => toDateString(new Date());

export const getPayWeekStartIndex = (dayName = 'monday') => DAY_ORDER.indexOf((dayName || 'monday').toLowerCase());

export const getPayWeekStartForDate = (value, dayName = 'monday') => {
  const date = typeof value === 'string' ? normalizeDate(value) : new Date(value);
  if (!date || Number.isNaN(date.getTime())) return getTodayDate();
  const desired = getPayWeekStartIndex(dayName);
  const delta = (date.getDay() - desired + 7) % 7;
  const result = new Date(date);
  result.setDate(date.getDate() - delta);
  return toDateString(result);
};

export const getCurrentCycleRange = ({ cycle = 'weekly', payWeekStartDay = 'monday', referenceDate = getTodayDate() } = {}) => {
  const cycleStart = getPayWeekStartForDate(referenceDate, payWeekStartDay);
  const start = normalizeDate(cycleStart);
  const days = cycle === 'biweekly' ? 13 : 6;
  const end = new Date(start);
  end.setDate(start.getDate() + days);
  return { startDate: cycleStart, endDate: toDateString(end) };
};

export const getPresetDateRange = (preset, payrollSettings = {}) => {
  if (preset === 'weekly') return getCurrentCycleRange({ cycle: 'weekly', payWeekStartDay: payrollSettings.payWeekStartDay });
  if (preset === 'biweekly') return getCurrentCycleRange({ cycle: 'biweekly', payWeekStartDay: payrollSettings.payWeekStartDay });
  return getCurrentCycleRange({ cycle: payrollSettings.defaultCycle || 'weekly', payWeekStartDay: payrollSettings.payWeekStartDay });
};

export const getDateRangeDates = (startDate, endDate) => {
  const start = normalizeDate(startDate);
  const end = normalizeDate(endDate);
  if (!start || !end || end < start) return [];
  const days = [];
  const cursor = new Date(start);
  while (cursor <= end) {
    days.push({
      date: toDateString(cursor),
      dayLabel: DAY_NAMES[cursor.getDay()],
    });
    cursor.setDate(cursor.getDate() + 1);
  }
  return days;
};

export const timeToMinutes = (value) => {
  if (!value) return null;
  const [hours, minutes] = value.split(':').map(Number);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  return (hours * 60) + minutes;
};

export const calculateBreakMinutes = (lunchStart, lunchEnd) => {
  const start = timeToMinutes(lunchStart);
  const end = timeToMinutes(lunchEnd);
  if (start === null || end === null) return 0;
  return Math.max(end - start, 0);
};

export const calculateRowMinutes = (row) => {
  const start = timeToMinutes(row.startTime);
  const end = timeToMinutes(row.endTime);
  if (start === null || end === null || end <= start) return 0;
  return Math.max(end - start - calculateBreakMinutes(row.lunchStart, row.lunchEnd), 0);
};

export const buildWorksheetRows = (startDate, endDate, shifts = []) => {
  const shiftMap = new Map();
  shifts.forEach((shift) => {
    if (!shiftMap.has(shift.date)) {
      shiftMap.set(shift.date, shift);
    }
  });

  return getDateRangeDates(startDate, endDate).map(({ date, dayLabel }) => {
    const shift = shiftMap.get(date);
    return {
      id: shift?.id || null,
      date,
      dayLabel,
      startTime: isoToLocalHHMM(shift?.clock_in),
      lunchStart: isoToLocalHHMM(shift?.lunch_start),
      lunchEnd: isoToLocalHHMM(shift?.lunch_end),
      endTime: isoToLocalHHMM(shift?.clock_out),
      notes: shift?.notes || '',
      source: shift?.source || 'worksheet',
      shiftStatus: shift?.status || null,
    };
  });
};

export const summarizeWorksheet = (rows, hourlyRate, overtimeRate, payWeekStartDay = 'monday') => {
  const normalizedHourly = Number(hourlyRate || 0);
  const normalizedOvertime = Number(overtimeRate || 0);
  const weeklyMinutes = new Map();
  let totalMinutes = 0;
  let regularMinutes = 0;
  let overtimeMinutes = 0;

  const detailedRows = rows.map((row) => {
    const minutes = calculateRowMinutes(row);
    const payWeekKey = getPayWeekStartForDate(row.date, payWeekStartDay);
    const priorWeekMinutes = weeklyMinutes.get(payWeekKey) || 0;
    const regularAllowance = Math.max((40 * 60) - priorWeekMinutes, 0);
    const rowRegularMinutes = Math.min(minutes, regularAllowance);
    const rowOvertimeMinutes = Math.max(minutes - rowRegularMinutes, 0);
    weeklyMinutes.set(payWeekKey, priorWeekMinutes + minutes);
    totalMinutes += minutes;
    regularMinutes += rowRegularMinutes;
    overtimeMinutes += rowOvertimeMinutes;
    return {
      ...row,
      totalHours: Number((minutes / 60).toFixed(2)),
      regularHours: Number((rowRegularMinutes / 60).toFixed(2)),
      overtimeHours: Number((rowOvertimeMinutes / 60).toFixed(2)),
    };
  });

  const regularPay = Number(((regularMinutes / 60) * normalizedHourly).toFixed(2));
  const overtimePay = Number(((overtimeMinutes / 60) * normalizedOvertime).toFixed(2));

  return {
    rows: detailedRows,
    totalMinutes,
    totalHours: Number((totalMinutes / 60).toFixed(2)),
    regularHours: Number((regularMinutes / 60).toFixed(2)),
    overtimeHours: Number((overtimeMinutes / 60).toFixed(2)),
    regularPay,
    overtimePay,
    grossPay: Number((regularPay + overtimePay).toFixed(2)),
  };
};

export const buildAdjustmentRows = (transactions = [], minRows = 10) => {
  const normalized = transactions
    .slice()
    .sort((left, right) => (left.date || '').localeCompare(right.date || ''))
    .map((transaction) => ({
      id: transaction.id,
      date: transaction.date || '',
      notes: transaction.description || '',
      amount: transaction.type === 'earnings' ? String(transaction.amount || '') : String(-(transaction.amount || 0)),
      type: transaction.type,
    }));

  while (normalized.length < minRows) {
    normalized.push({ id: null, date: '', notes: '', amount: '', type: 'advance' });
  }

  return normalized;
};

export const getSignedAdjustmentTotal = (rows) => rows.reduce((sum, row) => sum + (Number(row.amount || 0) || 0), 0);

export const inferTransactionType = (amountValue, fallbackType = 'advance') => {
  const amount = Number(amountValue || 0);
  if (amount > 0) return 'earnings';
  if (amount < 0) return fallbackType === 'payment' ? 'payment' : 'advance';
  return fallbackType;
};

export const hasShiftContent = (row) => [row.startTime, row.lunchStart, row.lunchEnd, row.endTime].some(Boolean);

export const hasAdjustmentContent = (row) => [row.date, row.notes, row.amount].some((value) => String(value || '').trim() !== '');

export const toIsoDateTime = (date, time) => localDateTimeToIsoUtc(date, time);

export const formatHoursCell = (value) => (Number(value || 0).toFixed(2));
