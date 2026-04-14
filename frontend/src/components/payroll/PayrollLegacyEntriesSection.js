import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { formatCurrency } from '../../lib/utils';

const HANDLING_OPTIONS = [
  { value: 'keep_legacy', label: 'Keep as manual legacy entry' },
  { value: 'worksheet_manual_row', label: 'Convert to worksheet manual row' },
  { value: 'merge_into_day', label: 'Merge into selected day' },
];

export const PayrollLegacyEntriesSection = ({
  entries,
  readOnlyLocked,
  unresolvedCount,
  totalHours,
  totalPay,
  weekDates,
  onEntryChange,
}) => {
  if (!entries.length) return null;

  return (
    <div className="space-y-4 rounded-[24px] border border-amber-200 bg-amber-50/70 p-4" data-testid="payroll-legacy-section">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">Legacy Manual Entries</p>
          <p className="mt-1 text-sm text-amber-900" data-testid="payroll-legacy-section-summary">{entries.length} legacy entr{entries.length === 1 ? 'y' : 'ies'} · {totalHours.toFixed(2)} hrs · {formatCurrency(totalPay)} currently included in payroll totals and exports.</p>
        </div>
        <Badge variant="outline" className={`border ${unresolvedCount > 0 ? 'border-amber-300 bg-white text-amber-800' : 'border-emerald-300 bg-white text-emerald-700'}`} data-testid="payroll-legacy-review-status-badge">
          {unresolvedCount > 0 ? `${unresolvedCount} needs review` : 'All reviewed or intentionally left as legacy'}
        </Badge>
      </div>

      {unresolvedCount > 0 ? (
        <div className="rounded-2xl border border-amber-300 bg-white/80 px-4 py-3 text-sm text-amber-900" data-testid="payroll-legacy-warning-banner">
          Payroll warning: current totals already include these off-grid entries. Review each one so they are either intentionally left as legacy or given a worksheet-compatible handling note.
        </div>
      ) : (
        <div className="rounded-2xl border border-emerald-200 bg-white/80 px-4 py-3 text-sm text-emerald-800" data-testid="payroll-legacy-resolved-banner">
          These legacy entries have already been intentionally handled. Totals and exports remain unchanged unless a future payroll rule explicitly changes that.
        </div>
      )}

      <div className="space-y-3">
        {entries.map((entry, index) => (
          <div key={entry.id} className="grid gap-3 rounded-[22px] border border-amber-200 bg-white p-4 xl:grid-cols-[110px_130px_90px_1.2fr_1.3fr_240px_150px_1fr]" data-testid={`payroll-legacy-entry-${index}`}>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Date</p>
              <p className="mt-2 text-sm font-medium text-slate-900" data-testid={`payroll-legacy-entry-date-${index}`}>{entry.date}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Source / Type</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700" data-testid={`payroll-legacy-entry-type-${index}`}>{entry.source_type}</Badge>
                {entry.handling_mode === 'worksheet_manual_row' && <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-700">Worksheet manual row</Badge>}
                {entry.handling_mode === 'merge_into_day' && <Badge variant="outline" className="border-violet-200 bg-violet-50 text-violet-700">Merged day</Badge>}
              </div>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Hours</p>
              <p className="mt-2 text-sm font-semibold text-slate-900" data-testid={`payroll-legacy-entry-hours-${index}`}>{entry.hours.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Notes / Reason</p>
              <p className="mt-2 text-sm text-slate-700" data-testid={`payroll-legacy-entry-notes-${index}`}>{entry.notes || 'No note saved.'}</p>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Current Effect On Totals</p>
              <p className="mt-2 text-sm text-slate-800" data-testid={`payroll-legacy-entry-effect-${index}`}>{entry.current_effect_label}</p>
            </div>
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Handling</p>
              <Select disabled={readOnlyLocked} value={entry.handling_mode} onValueChange={(value) => onEntryChange(index, 'handling_mode', value)}>
                <SelectTrigger className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid={`payroll-legacy-entry-handling-${index}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {HANDLING_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">Exclude from payroll totals is unavailable here so payroll math never changes silently during migration.</p>
            </div>
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Selected Day</p>
              <Select disabled={readOnlyLocked} value={entry.target_date} onValueChange={(value) => onEntryChange(index, 'target_date', value)}>
                <SelectTrigger className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid={`payroll-legacy-entry-target-date-${index}`}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {weekDates.map((weekDate) => (
                    <SelectItem key={weekDate.date} value={weekDate.date}>{weekDate.dayLabel} · {weekDate.date}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Admin Note</p>
              <Input disabled={readOnlyLocked} value={entry.admin_note} onChange={(event) => onEntryChange(index, 'admin_note', event.target.value)} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid={`payroll-legacy-entry-admin-note-${index}`} />
              <p className="text-xs text-slate-500" data-testid={`payroll-legacy-entry-status-${index}`}>{entry.resolution_saved ? 'Handled intentionally' : 'Needs review before payroll is fully cleared'}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};