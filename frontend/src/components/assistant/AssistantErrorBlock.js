import { AlertCircle, RefreshCcw } from 'lucide-react';

/**
 * Structured error block with retry action where appropriate.
 * Error types: 'permission' | 'parse' | 'missing_data' | 'system' | 'not_found'
 */
export default function AssistantErrorBlock({
  title = 'Something went wrong',
  message,
  errorType,
  onRetry,
  onAlternative,
}) {
  return (
    <div
      className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs flex flex-col gap-2"
      data-testid="assistant-error-block"
    >
      <div className="flex items-start gap-2">
        <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="font-semibold text-rose-900">{title}</div>
          {message && <div className="text-rose-800 mt-0.5">{message}</div>}
          {errorType && (
            <div className="mt-1 inline-block text-[10px] uppercase tracking-wide font-semibold text-rose-700 bg-rose-100 rounded px-1.5 py-0.5">
              {errorType.replace(/_/g, ' ')}
            </div>
          )}
        </div>
      </div>
      {(onRetry || onAlternative) && (
        <div className="flex gap-1.5">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              data-testid="assistant-error-retry"
              className="inline-flex items-center gap-1 rounded-full bg-rose-600 text-white px-3 py-1 text-[11px] font-semibold hover:bg-rose-700"
            >
              <RefreshCcw className="h-3 w-3" />
              Retry
            </button>
          )}
          {onAlternative && (
            <button
              type="button"
              onClick={onAlternative.action}
              className="inline-flex items-center rounded-full border border-rose-300 bg-white px-3 py-1 text-[11px] font-semibold text-rose-700 hover:bg-rose-50"
            >
              {onAlternative.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
