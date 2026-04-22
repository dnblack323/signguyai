import { useEffect, useState } from 'react';
import { UserCheck, X } from 'lucide-react';
import { getLastOrderCustomer } from '../../utils/assistantPrefsApi';

/**
 * Tiny "Use Acme Corp again?" chip surfaced when the user recently created
 * an order via the assistant. Clicking it pre-fills a create-order command.
 */
export default function AssistantSmartDefault({ token, onPick }) {
  const [data, setData] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    getLastOrderCustomer(token)
      .then((d) => { if (!cancelled) setData(d); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [token]);

  if (dismissed || !data?.customer_name) return null;

  const onUse = () => {
    onPick?.(`Create order for ${data.customer_name}`);
  };

  return (
    <div
      className="flex items-center gap-1.5 rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-[11px] text-violet-800"
      data-testid="assistant-smart-default"
    >
      <UserCheck className="h-3 w-3 text-violet-600" />
      <button
        type="button"
        onClick={onUse}
        className="font-medium hover:underline"
        data-testid="assistant-smart-default-use"
      >
        Use {data.customer_name} again?
      </button>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="text-violet-400 hover:text-violet-700"
        data-testid="assistant-smart-default-dismiss"
        title="Dismiss"
      >
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}
