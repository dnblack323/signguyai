const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const pad = (value) => String(value).padStart(2, '0');

export const getWeekStart = (reference = new Date()) => {
  const date = new Date(reference);
  const day = date.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + mondayOffset);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

export const getWeekDates = (weekStart) => {
  const start = new Date(`${weekStart}T00:00:00`);
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    return {
      date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`,
      dayLabel: DAY_NAMES[index],
    };
  });
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
  const breakMinutes = calculateBreakMinutes(row.lunchStart, row.lunchEnd);
  return Math.max(end - start - breakMinutes, 0);
};

export const buildWorksheetRows = (weekStart, shifts = []) => {
  const shiftMap = new Map();
  shifts.forEach((shift) => {
    if (!shiftMap.has(shift.date)) {
      shiftMap.set(shift.date, shift);
    }
  });

  return getWeekDates(weekStart).map(({ date, dayLabel }) => {
    const shift = shiftMap.get(date);
    return {
      id: shift?.id || null,
      date,
      dayLabel,
      startTime: shift?.clock_in?.slice(11, 16) || '',
      lunchStart: shift?.lunch_start?.slice(11, 16) || '',
      lunchEnd: shift?.lunch_end?.slice(11, 16) || '',
      endTime: shift?.clock_out?.slice(11, 16) || '',
      notes: shift?.notes || '',
      source: shift?.source || 'worksheet',
    };
  });
};

export const summarizeWorksheet = (rows, hourlyRate, overtimeRate) => {
  const normalizedHourly = Number(hourlyRate || 0);
  const normalizedOvertime = Number(overtimeRate || 0);
  let cumulativeMinutes = 0;
  let totalMinutes = 0;
  let regularMinutes = 0;
  let overtimeMinutes = 0;

  const detailedRows = rows.map((row) => {
    const minutes = calculateRowMinutes(row);
    const regularAllowance = Math.max((40 * 60) - cumulativeMinutes, 0);
    const rowRegularMinutes = Math.min(minutes, regularAllowance);
    const rowOvertimeMinutes = Math.max(minutes - rowRegularMinutes, 0);
    cumulativeMinutes += minutes;
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

export const hasShiftContent = (row) => [row.startTime, row.lunchStart, row.lunchEnd, row.endTime, row.notes].some(Boolean);

export const hasAdjustmentContent = (row) => [row.date, row.notes, row.amount].some((value) => String(value || '').trim() !== '');

export const toIsoDateTime = (date, time) => (date && time ? `${date}T${time}:00` : null);

export const formatHoursCell = (value) => (Number(value || 0).toFixed(2));
