import { formatCurrency } from '../../lib/utils';
import { Input } from '../ui/input';

export const PayrollAdjustmentsPanel = ({ rows, onChange, total }) => (
  <aside className="border-r border-slate-200 bg-[#fbfbf7]" data-testid="payroll-adjustments-panel">
    <div className="border-b border-slate-200 px-5 py-5">
      <p className="font-mono text-[2rem] uppercase tracking-tight text-slate-900">Adjustments</p>
      <p className="mt-2 text-xs uppercase tracking-[0.22em] text-slate-500">Positive adds pay · negative deducts</p>
    </div>
    <div className="grid grid-cols-[112px_1fr_110px] border-b border-slate-300 bg-[#f1f4ec] text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-600">
      <div className="border-r border-slate-300 px-3 py-3">Date</div>
      <div className="border-r border-slate-300 px-3 py-3">Notes</div>
      <div className="px-3 py-3 text-right">Amount</div>
    </div>
    <div className="divide-y divide-slate-200">
      {rows.map((row, index) => (
        <div key={row.id || `adjustment-row-${index}`} className="grid grid-cols-[112px_1fr_110px]" data-testid={`payroll-adjustment-row-${index}`}>
          <Input type="date" value={row.date} onChange={(event) => onChange(index, 'date', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-adjustment-date-${index}`} />
          <Input value={row.notes} onChange={(event) => onChange(index, 'notes', event.target.value)} className="h-12 rounded-none border-0 border-r border-slate-200 bg-transparent px-3 text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-adjustment-notes-${index}`} />
          <Input type="number" step="0.01" value={row.amount} onChange={(event) => onChange(index, 'amount', event.target.value)} className="h-12 rounded-none border-0 bg-transparent px-3 text-right text-sm shadow-none focus-visible:ring-0" data-testid={`payroll-adjustment-amount-${index}`} />
        </div>
      ))}
    </div>
    <div className="flex items-center justify-between border-t border-slate-300 bg-white px-5 py-4">
      <p className="font-mono text-[1.7rem] uppercase tracking-tight text-slate-900">Total Adjustments</p>
      <div className="min-w-[112px] border border-slate-300 bg-[#fffdf6] px-3 py-3 text-right text-lg font-semibold text-slate-900" data-testid="payroll-adjustments-total">{formatCurrency(total)}</div>
    </div>
  </aside>
);
