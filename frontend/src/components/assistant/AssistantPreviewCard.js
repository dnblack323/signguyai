import { Check, Pencil, X, Clock } from 'lucide-react';

/**
 * Structured preview card shown before a write action executes.
 * Replaces the "Should I create this? [Yes] [No]" plain-text bubble.
 */
export default function AssistantPreviewCard({
  title = 'Action Preview',
  fields = [],
  onConfirm,
  onCancel,
  onEdit,
  loading = false,
  state = 'preview', // 'preview' | 'confirming' | 'done' | 'failed'
  warnings = [],
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
}) {
  const isBusy = loading || state === 'confirming';
  return (
    <div className="rounded-lg border border-violet-200 bg-white overflow-hidden" data-testid="assistant-preview-card">
      <div className="bg-violet-50 px-3 py-2 border-b border-violet-100 flex items-center gap-2">
        <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-violet-500 text-white">
          {state === 'confirming' ? <Clock className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
        </span>
        <span className="text-xs font-semibold text-violet-900">{title}</span>
      </div>

      {warnings.length > 0 && (
        <div className="px-3 py-2 bg-amber-50 border-b border-amber-100 space-y-1">
          {warnings.map((w, i) => (
            <div key={i} className="text-[11px] text-amber-900">⚠ {w}</div>
          ))}
        </div>
      )}

      <div className="px-3 py-2.5 space-y-1.5">
        {fields.map((f, i) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <span className="text-slate-500 w-28 flex-shrink-0">{f.label}</span>
            <span className="flex-1">
              {f.previous != null && f.previous !== f.value ? (
                <span>
                  <span className="line-through text-slate-400 mr-1">{f.previous}</span>
                  <span className="font-semibold text-slate-900">{formatFieldValue(f.value)}</span>
                </span>
              ) : (
                <span className="font-semibold text-slate-900">{formatFieldValue(f.value)}</span>
              )}
            </span>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-1.5 px-3 py-2 border-t border-slate-100 bg-slate-50">
        <button
          type="button"
          disabled={isBusy}
          onClick={onConfirm}
          data-testid="assistant-preview-confirm"
          className="inline-flex items-center gap-1 rounded-full bg-violet-600 text-white px-3 py-1 text-[11px] font-semibold hover:bg-violet-700 disabled:opacity-50"
        >
          <Check className="h-3 w-3" />
          {confirmLabel}
        </button>
        {onEdit && (
          <button
            type="button"
            disabled={isBusy}
            onClick={onEdit}
            data-testid="assistant-preview-edit"
            className="inline-flex items-center gap-1 rounded-full border border-slate-300 bg-white px-3 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            <Pencil className="h-3 w-3" />
            Edit
          </button>
        )}
        <button
          type="button"
          disabled={isBusy}
          onClick={onCancel}
          data-testid="assistant-preview-cancel"
          className="inline-flex items-center gap-1 rounded-full border border-slate-300 bg-white px-3 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          <X className="h-3 w-3" />
          {cancelLabel}
        </button>
      </div>
    </div>
  );
}

function formatFieldValue(v) {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  return String(v);
}
