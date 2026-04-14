import { Input } from '../ui/input';
import { formatHoursCell } from '../../lib/payrollWorksheet';

const HEADER_CELLS = ['Date', 'Day', 'Start Time', 'Lunch Start', 'Lunch End', 'End Time', 'Regular Hours', 'Overtime Hours', 'Total Hours'];

export const PayrollWeekTable = ({ rows, onRowChange }) => (
  <div className="overflow-hidden rounded-[28px] border border-slate-300 bg-white shadow-[0_14px_40px_rgba(15,23,42,0.08)]" data-testid="payroll-week-table-shell">
    <div className="grid grid-cols-[140px_110px_1fr_1fr_1fr_1fr_120px_120px_120px] bg-[#bfe2df] text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-700">
      {HEADER_CELLS.map((label) => (
        <div key={label} className="border-r border-slate-300 px-3 py-3 last:border-r-0">{label}</div>
      ))}
    </div>
    <div className="divide-y divide-slate-200">
      {rows.map((row, index) => (
        <div key={row.date} className="grid grid-cols-[140px_110px_1fr_1fr_1fr_1fr_120px_120px_120px] bg-white" data-testid={`payroll-week-row-${index}`}>
          <Input type="date" value={row.date} onChange={(event) => onRowChange(index, 'date', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-row-date-${index}`} />
          <div className="flex items-center border-r border-slate-200 px-3 text-sm font-medium text-slate-800" data-testid={`payroll-row-day-${index}`}>{row.dayLabel}</div>
          <Input type="time" value={row.startTime} onChange={(event) => onRowChange(index, 'startTime', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-row-start-${index}`} />
          <Input type="time" value={row.lunchStart} onChange={(event) => onRowChange(index, 'lunchStart', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-row-lunch-start-${index}`} />
          <Input type="time" value={row.lunchEnd} onChange={(event) => onRowChange(index, 'lunchEnd', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-row-lunch-end-${index}`} />
          <Input type="time" value={row.endTime} onChange={(event) => onRowChange(index, 'endTime', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-row-end-${index}`} />
          <div className="flex items-center justify-end border-r border-slate-200 px-3 text-sm font-semibold text-slate-800" data-testid={`payroll-row-regular-hours-${index}`}>{formatHoursCell(row.regularHours)}</div>
          <div className="flex items-center justify-end border-r border-slate-200 px-3 text-sm font-semibold text-slate-800" data-testid={`payroll-row-overtime-hours-${index}`}>{formatHoursCell(row.overtimeHours)}</div>
          <div className="flex items-center justify-end px-3 text-sm font-semibold text-slate-900" data-testid={`payroll-row-total-hours-${index}`}>{formatHoursCell(row.totalHours)}</div>
        </div>
      ))}
    </div>
  </div>
);
