import { formatCurrency } from '../../lib/utils';

const SummaryRow = ({ label, value, testId, strong = false }) => (
  <div className="grid grid-cols-[1fr_180px] border-b border-slate-200 last:border-b-0">
    <div className="px-4 py-3 text-sm uppercase tracking-[0.18em] text-slate-500">{label}</div>
    <div className={`px-4 py-3 text-right text-sm ${strong ? 'font-semibold text-slate-900' : 'font-medium text-slate-700'}`} data-testid={testId}>{value}</div>
  </div>
);

export const PayrollWorksheetSummary = ({ adjustmentsTotal, carryoverBalance, legacyManualHours = 0, legacyManualPay = 0, summary }) => {
  const totalHours = summary.totalHours + legacyManualHours;
  const regularHours = summary.regularHours + legacyManualHours;
  const regularPay = summary.regularPay + legacyManualPay;
  const grossPay = regularPay + summary.overtimePay;
  const finalTotal = grossPay + adjustmentsTotal + carryoverBalance;

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_280px]" data-testid="payroll-worksheet-summary">
      <div className="rounded-[26px] border border-slate-300 bg-white">
        {legacyManualHours > 0 && (
          <SummaryRow label="Legacy Manual Included" value={`${legacyManualHours.toFixed(2)} hrs · ${formatCurrency(legacyManualPay)}`} testId="payroll-summary-legacy-manual" />
        )}
        <SummaryRow label="Total Time" value={`${totalHours.toFixed(2)} hrs`} testId="payroll-summary-total-time" strong />
        <SummaryRow label="Total Regular Hours" value={`${regularHours.toFixed(2)} hrs`} testId="payroll-summary-regular-hours" />
        <SummaryRow label="Total Overtime Hours" value={`${summary.overtimeHours.toFixed(2)} hrs`} testId="payroll-summary-overtime-hours" />
        <SummaryRow label="Regular Pay" value={formatCurrency(regularPay)} testId="payroll-summary-regular-pay" />
        <SummaryRow label="Overtime Pay" value={formatCurrency(summary.overtimePay)} testId="payroll-summary-overtime-pay" />
        <SummaryRow label="Gross Pay Before Adjustments" value={formatCurrency(grossPay)} testId="payroll-summary-gross-pay" strong />
      </div>

      <div className="space-y-4 self-end rounded-[26px] border border-slate-300 bg-[#fffdf6] p-5">
        <div className="grid gap-2">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Carryover Balance</p>
          <div className="border border-slate-300 bg-white px-4 py-3 text-right text-lg font-semibold text-slate-900" data-testid="payroll-summary-carryover-balance">{formatCurrency(carryoverBalance)}</div>
        </div>
        <div className="grid gap-2">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Total Adjustments</p>
          <div className="border border-slate-300 bg-white px-4 py-3 text-right text-lg font-semibold text-slate-900" data-testid="payroll-summary-total-adjustments">{formatCurrency(adjustmentsTotal)}</div>
        </div>
        <div className="grid gap-2">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Final Total For Pay Period</p>
          <div className="border border-slate-900 bg-slate-900 px-4 py-4 text-right text-xl font-semibold text-white" data-testid="payroll-summary-final-total">{formatCurrency(finalTotal)}</div>
        </div>
      </div>
    </div>
  );
};