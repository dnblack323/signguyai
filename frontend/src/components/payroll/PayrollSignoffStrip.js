import { Input } from '../ui/input';
import { Label } from '../ui/label';

const inputClassName = 'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500';

export const PayrollSignoffStrip = ({ readOnlyLocked, signoff, onChange }) => (
  <div className="rounded-[24px] border border-slate-300 bg-[#f9fbfb] p-4" data-testid="payroll-signoff-strip">
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Payroll review sign-off</p>
        <p className="mt-1 text-sm text-slate-600">Compact review fields that stay inside the worksheet instead of opening a second workflow.</p>
      </div>
    </div>
    <div className="grid gap-4 xl:grid-cols-[1fr_180px_1fr_180px_1.3fr]">
      <div className="space-y-2">
        <Label htmlFor="payroll-signoff-reviewed-by">Reviewed By</Label>
        <Input id="payroll-signoff-reviewed-by" disabled={readOnlyLocked} value={signoff.reviewed_by} onChange={(event) => onChange('reviewed_by', event.target.value)} className={inputClassName} data-testid="payroll-signoff-reviewed-by-input" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="payroll-signoff-review-date">Review Date</Label>
        <Input id="payroll-signoff-review-date" type="date" disabled={readOnlyLocked} value={signoff.review_date} onChange={(event) => onChange('review_date', event.target.value)} className={inputClassName} data-testid="payroll-signoff-review-date-input" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="payroll-signoff-approved-by">Approved By</Label>
        <Input id="payroll-signoff-approved-by" disabled={readOnlyLocked} value={signoff.approved_by} onChange={(event) => onChange('approved_by', event.target.value)} className={inputClassName} data-testid="payroll-signoff-approved-by-input" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="payroll-signoff-approval-date">Approval Date</Label>
        <Input id="payroll-signoff-approval-date" type="date" disabled={readOnlyLocked} value={signoff.approval_date} onChange={(event) => onChange('approval_date', event.target.value)} className={inputClassName} data-testid="payroll-signoff-approval-date-input" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="payroll-signoff-notes">Payroll Notes</Label>
        <Input id="payroll-signoff-notes" disabled={readOnlyLocked} value={signoff.payroll_notes} onChange={(event) => onChange('payroll_notes', event.target.value)} className={inputClassName} data-testid="payroll-signoff-notes-input" />
      </div>
    </div>
  </div>
);