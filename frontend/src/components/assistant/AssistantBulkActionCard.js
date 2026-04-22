import { useEffect, useState } from 'react';
import { Loader2, Mail, AlertTriangle, Check, X, DollarSign } from 'lucide-react';
import { toast } from 'sonner';
import { previewOverdueReminders, sendOverdueReminders } from '../../utils/assistantPrefsApi';

/**
 * Bulk action preview card — Phase 5: "send reminders to overdue customers".
 * Shows preview (count + sample invoices) then Confirm/Cancel.
 */
export default function AssistantBulkActionCard({ token, onDone, onCancel }) {
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [preview, setPreview] = useState(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    previewOverdueReminders(token)
      .then((d) => { if (!cancelled) setPreview(d); })
      .catch(() => { if (!cancelled) setPreview({ count: 0, sample: [], all_ids: [] }); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [token]);

  const handleSend = async () => {
    if (!preview?.all_ids?.length) return;
    setSending(true);
    try {
      const resp = await sendOverdueReminders(token, { invoice_ids: preview.all_ids });
      toast.success(resp?.message || `Queued ${resp?.sent || 0} reminders`);
      setDone(true);
      onDone?.(resp);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Could not queue reminders');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border bg-white px-3 py-2 flex items-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Checking overdue invoices…
      </div>
    );
  }

  if (done) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 flex items-center gap-2 text-sm text-green-800" data-testid="assistant-bulk-done">
        <Check className="h-4 w-4" /> Reminders queued.
      </div>
    );
  }

  const count = preview?.count || 0;
  if (count === 0) {
    return (
      <div className="rounded-lg border bg-white px-3 py-2 text-sm text-slate-600" data-testid="assistant-bulk-empty">
        No overdue invoices — nothing to remind.
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border border-violet-200 bg-white overflow-hidden"
      data-testid="assistant-bulk-overdue-card"
    >
      <div className="bg-violet-50 px-3 py-2 border-b border-violet-100 flex items-center gap-2">
        <Mail className="h-3.5 w-3.5 text-violet-700" />
        <span className="text-xs font-semibold text-violet-900">Bulk: Send overdue reminders</span>
      </div>

      <div className="px-3 py-2 text-xs space-y-1">
        <div className="flex items-center gap-2 font-semibold text-slate-900">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          {count} overdue invoice{count !== 1 ? 's' : ''} will receive a reminder
        </div>
        <div className="text-slate-500">Sample:</div>
        <div className="space-y-0.5">
          {(preview.sample || []).slice(0, 5).map((s) => (
            <div
              key={s.invoice_id}
              className="flex justify-between text-[11px] text-slate-700"
              data-testid={`assistant-bulk-row-${s.invoice_id}`}
            >
              <span className="truncate">
                {s.invoice_number || s.invoice_id} — {s.customer_name || 'Unknown'}
              </span>
              <span className="inline-flex items-center gap-0.5 text-slate-600 font-mono">
                <DollarSign className="h-3 w-3" />
                {s.balance_due?.toFixed?.(2) ?? s.balance_due}
              </span>
            </div>
          ))}
          {count > 5 && (
            <div className="text-[10px] text-slate-500 italic">…and {count - 5} more</div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1.5 px-3 py-2 border-t bg-slate-50">
        <button
          type="button"
          onClick={handleSend}
          disabled={sending}
          data-testid="assistant-bulk-confirm"
          className="inline-flex items-center gap-1 rounded-full bg-violet-600 text-white px-3 py-1 text-[11px] font-semibold hover:bg-violet-700 disabled:opacity-50"
        >
          {sending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
          Send {count} reminders
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={sending}
          data-testid="assistant-bulk-cancel"
          className="inline-flex items-center gap-1 rounded-full border border-slate-300 bg-white px-3 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          <X className="h-3 w-3" />
          Cancel
        </button>
      </div>
    </div>
  );
}
