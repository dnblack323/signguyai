import { useEffect, useState } from 'react';
import { formatCurrency } from '../../lib/utils';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Pencil, Check, X } from 'lucide-react';

const Row = ({ label, value, testId, emphasis = false }) => (
  <div className="flex items-baseline justify-between py-2 border-b border-slate-200 last:border-b-0">
    <span className={`text-sm ${emphasis ? 'font-semibold text-slate-900' : 'text-slate-600'}`}>{label}</span>
    <span className={`tabular-nums ${emphasis ? 'text-base font-semibold text-slate-900' : 'text-sm font-medium text-slate-800'}`} data-testid={testId}>{value}</span>
  </div>
);

export const PayrollWorksheetSummary = ({
  adjustmentsTotal,
  carryoverBalance,
  legacyManualHours = 0,
  legacyManualPay = 0,
  summary,
  canEditCarryover = false,
  onSaveCarryover,
}) => {
  const totalHours = summary.totalHours + legacyManualHours;
  const regularHours = summary.regularHours + legacyManualHours;
  const regularPay = summary.regularPay + legacyManualPay;
  const grossPay = regularPay + summary.overtimePay;
  const finalTotal = grossPay + adjustmentsTotal + carryoverBalance;

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(carryoverBalance ?? 0));
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!editing) setDraft(String(carryoverBalance ?? 0));
  }, [carryoverBalance, editing]);

  const handleSave = async () => {
    if (!onSaveCarryover) return;
    const numericValue = Number(draft);
    if (Number.isNaN(numericValue)) return;
    setSaving(true);
    try {
      await onSaveCarryover(numericValue);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl rounded-[22px] border border-slate-300 bg-white p-5 shadow-sm" data-testid="payroll-worksheet-summary">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Pay Period Summary</h3>

      {/* Hours section */}
      <div className="divide-y divide-slate-200">
        {legacyManualHours > 0 && (
          <Row label="Legacy Manual Included" value={`${legacyManualHours.toFixed(2)} hrs · ${formatCurrency(legacyManualPay)}`} testId="payroll-summary-legacy-manual" />
        )}
        <Row label="Total Time" value={`${totalHours.toFixed(2)} hrs`} testId="payroll-summary-total-time" emphasis />
        <Row label="Regular Hours" value={`${regularHours.toFixed(2)} hrs`} testId="payroll-summary-regular-hours" />
        <Row label="Overtime Hours" value={`${summary.overtimeHours.toFixed(2)} hrs`} testId="payroll-summary-overtime-hours" />
      </div>

      {/* Pay calc section */}
      <div className="mt-3 divide-y divide-slate-200">
        <Row label="Regular Pay" value={formatCurrency(regularPay)} testId="payroll-summary-regular-pay" />
        <Row label="Overtime Pay" value={formatCurrency(summary.overtimePay)} testId="payroll-summary-overtime-pay" />
        <Row label="Gross Pay (before adjustments)" value={formatCurrency(grossPay)} testId="payroll-summary-gross-pay" emphasis />
      </div>

      {/* Adjustments + editable carryover */}
      <div className="mt-3 divide-y divide-slate-200">
        <Row label="Total Adjustments" value={formatCurrency(adjustmentsTotal)} testId="payroll-summary-total-adjustments" />

        {/* Carryover row — clearly editable when permitted */}
        <div className="flex items-baseline justify-between py-2">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Carryover Balance</span>
            {canEditCarryover && !editing && (
              <Button
                size="sm"
                variant="outline"
                className="h-7 px-2 text-[11px] font-medium border-slate-300 text-slate-700 hover:bg-slate-50 gap-1"
                onClick={() => setEditing(true)}
                data-testid="edit-carryover-balance-btn"
              >
                <Pencil className="w-3 h-3" /> Edit
              </Button>
            )}
          </div>
          {editing ? (
            <div className="flex items-center gap-1.5">
              <Input
                type="number"
                step="0.01"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                className="h-9 w-28 text-right tabular-nums"
                data-testid="carryover-balance-input"
                autoFocus
              />
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saving}
                className="h-9 bg-slate-900 hover:bg-slate-800 text-white px-2"
                data-testid="save-carryover-balance-btn"
                title="Save"
              >
                <Check className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => { setDraft(String(carryoverBalance ?? 0)); setEditing(false); }}
                disabled={saving}
                className="h-9 px-2"
                data-testid="cancel-carryover-balance-btn"
                title="Cancel"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <span className="tabular-nums text-sm font-medium text-slate-800" data-testid="payroll-summary-carryover-balance">{formatCurrency(carryoverBalance)}</span>
          )}
        </div>
      </div>

      {/* Final Total — standout block */}
      <div className="mt-5 rounded-2xl bg-slate-900 px-5 py-5 text-white">
        <div className="flex items-baseline justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-400">Final Total for Pay Period</span>
        </div>
        <div className="mt-2 text-4xl font-bold tabular-nums" data-testid="payroll-summary-final-total">{formatCurrency(finalTotal)}</div>
        <p className="mt-2 text-[11px] text-slate-400">Gross Pay + Adjustments + Carryover</p>
      </div>
    </div>
  );
};
