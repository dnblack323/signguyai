// Phase 2E: Aftercare tab — real persistence + followup checklist.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { LifeBuoy, Send, Save, CalendarClock } from 'lucide-react';

const STATUSES = [
  'not_sent', 'generated', 'sent', 'viewed', 'acknowledged', 'followup_active', 'complete',
];

const FOLLOWUP_DEFS = [
  ['followup_24h', '24-hour follow-up'],
  ['followup_7d', '7-day follow-up'],
  ['followup_30d', '30-day follow-up'],
];

const STATUS_CLS = {
  not_sent: 'bg-slate-100 text-slate-700',
  generated: 'bg-blue-100 text-blue-800',
  sent: 'bg-amber-100 text-amber-800',
  viewed: 'bg-violet-100 text-violet-800',
  acknowledged: 'bg-emerald-100 text-emerald-800',
  followup_active: 'bg-emerald-50 text-emerald-700',
  complete: 'bg-emerald-200 text-emerald-900',
};

export default function AftercareTab({
  wrapData,
  onSaveAftercare,
  onToggleField,
  saveStatus,
}) {
  const aftercare = wrapData?.aftercare || {};
  const [form, setForm] = useState({ aftercare_status: 'not_sent', aftercare_template: '', sent_by: '', aftercare_notes: '' });
  const [dirty, setDirty] = useState(false);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({
      aftercare_status: aftercare.aftercare_status || 'not_sent',
      aftercare_template: aftercare.aftercare_template || '',
      sent_by: aftercare.sent_by || '',
      aftercare_notes: aftercare.aftercare_notes || '',
    });
    setDirty(false);
  }, [wrapData]);  // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const ok = await onSaveAftercare?.(form);
    if (ok) setDirty(false);
  };

  const statusCls = STATUS_CLS[aftercare.aftercare_status || 'not_sent'] || STATUS_CLS.not_sent;

  return (
    <div className="space-y-3" data-testid="aftercare-tab">
      <WrapSectionCard
          title="Aftercare Status"
          icon={LifeBuoy}
          testId="aftercare-status"
          action={
            <div className="flex items-center gap-2 flex-wrap">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="aftercare-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="aftercare-save-btn"><Save className="h-3.5 w-3.5 mr-1" /> Save Aftercare</Button>
            </div>
          }
        >
          <div className="flex items-center gap-2 flex-wrap mb-3">
            <span className="text-xs text-slate-500">Status:</span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusCls}`} data-testid="aftercare-status-chip">{(aftercare.aftercare_status || 'not_sent').replace(/_/g, ' ')}</span>
            {aftercare.aftercare_sent_at && <span className="text-[11px] text-amber-700" data-testid="aftercare-sent-at">Sent: {new Date(aftercare.aftercare_sent_at).toLocaleString()}</span>}
            {aftercare.customer_viewed_at && <span className="text-[11px] text-violet-700">Viewed: {new Date(aftercare.customer_viewed_at).toLocaleString()}</span>}
            {aftercare.customer_acknowledged_at && <span className="text-[11px] text-emerald-700">Acknowledged: {new Date(aftercare.customer_acknowledged_at).toLocaleString()}</span>}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Label className="text-xs">Status</Label>
              <select className="w-full border rounded h-9 px-2 text-sm" value={form.aftercare_status} onChange={(e) => set('aftercare_status', e.target.value)} data-testid="aftercare-select-status">
                {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div><Label className="text-xs">Template</Label><Input value={form.aftercare_template} onChange={(e) => set('aftercare_template', e.target.value)} placeholder="Standard wrap care v3" data-testid="aftercare-input-template" /></div>
            <div><Label className="text-xs">Sent By</Label><Input value={form.sent_by} onChange={(e) => set('sent_by', e.target.value)} data-testid="aftercare-input-sent_by" /></div>
            <div className="md:col-span-3"><Label className="text-xs">Aftercare Notes</Label><Textarea rows={2} value={form.aftercare_notes} onChange={(e) => set('aftercare_notes', e.target.value)} data-testid="aftercare-input-notes" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Aftercare Actions" icon={Send} testId="aftercare-actions">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={!!aftercare.aftercare_sent} onChange={(e) => onToggleField?.('aftercare_sent', e.target.checked)} disabled={busy} data-testid="aftercare-toggle-sent" />
              <span className={aftercare.aftercare_sent ? 'line-through text-slate-500' : 'text-slate-700'}>Aftercare sent to customer</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={!!aftercare.customer_viewed} onChange={(e) => onToggleField?.('customer_viewed', e.target.checked)} disabled={busy} data-testid="aftercare-toggle-viewed" />
              <span className={aftercare.customer_viewed ? 'line-through text-slate-500' : 'text-slate-700'}>Customer viewed aftercare</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={!!aftercare.customer_acknowledged} onChange={(e) => onToggleField?.('customer_acknowledged', e.target.checked)} disabled={busy} data-testid="aftercare-toggle-acknowledged" />
              <span className={aftercare.customer_acknowledged ? 'line-through text-slate-500' : 'text-slate-700'}>Customer acknowledged</span>
            </label>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">"Aftercare sent" mirrors into <span className="font-medium">approvals.aftercare_sent</span>.</p>
        </WrapSectionCard>

        <WrapSectionCard title="Follow-up Checklist" icon={CalendarClock} testId="aftercare-followup">
          <ul className="grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="aftercare-followup-list">
            {FOLLOWUP_DEFS.map(([key, label]) => {
              const done = !!aftercare[key];
              const ts = aftercare[`${key}_at`];
              return (
                <li key={key} className="flex flex-col gap-1 p-2 border rounded-md bg-white">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={done}
                      onChange={(e) => onToggleField?.(key, e.target.checked)}
                      disabled={busy}
                      data-testid={`aftercare-toggle-${key}`}
                    />
                    <span className={done ? 'line-through text-slate-500' : 'text-slate-700'}>{label}</span>
                  </label>
                  {ts && <span className="text-[10px] text-emerald-700" data-testid={`aftercare-ts-${key}`}>{new Date(ts).toLocaleString()}</span>}
                </li>
              );
            })}
          </ul>
        </WrapSectionCard>

        <WrapSectionCard title="Aftercare PDF (placeholder)" icon={LifeBuoy} testId="aftercare-pdf">
          <p className="text-xs text-slate-500">Aftercare PDF generation will be connected in a later phase.</p>
        </WrapSectionCard>
    </div>
  );
}
