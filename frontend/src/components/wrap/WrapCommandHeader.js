// Phase 1: Sticky page header — shows merged order/item info + action buttons.
import { Link } from 'react-router-dom';
import { ArrowLeft, MessageSquare, UserSquare, FileText as FileTextIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const HEADER_ACTIONS = [];  // Phase 2: These will be wired to real actions

const money = (n) => (typeof n === 'number' ? `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');

export default function WrapCommandHeader({ orderId, header, saveStatus, saveError }) {
  const saveBadge = (() => {
    if (saveStatus === 'saving') return { text: 'Saving…', cls: 'bg-amber-50 text-amber-700 border-amber-200' };
    if (saveStatus === 'saved')  return { text: 'Saved',    cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    if (saveStatus === 'error')  return { text: `Error: ${saveError || 'save failed'}`, cls: 'bg-rose-50 text-rose-700 border-rose-200' };
    return null;
  })();

  return (
    <div className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200" data-testid="wrap-command-header">
      <div className="px-4 sm:px-6 py-3 space-y-2.5">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link to={`/orders/${orderId}`} className="inline-flex items-center gap-1 text-violet-700 hover:underline" data-testid="wrap-header-back">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to order
          </Link>
          <span>·</span>
          <span>Wrap Command Center</span>
        </div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-semibold text-slate-900 truncate">
                {header.order_number} · {header.customer_name}
              </h1>
              <Badge className="bg-violet-100 text-violet-800 border-violet-200">Wrap Workflow</Badge>
              <Badge variant="outline" className="bg-amber-50 text-amber-800 border-amber-200">{header.status}</Badge>
              {saveBadge && (
                <Badge variant="outline" className={saveBadge.cls} data-testid="wrap-save-status">
                  {saveBadge.text}
                </Badge>
              )}
            </div>
            <p className="text-sm text-slate-600 mt-0.5 truncate">
              {header.business_name && <span>{header.business_name} · </span>}
              {header.item_name}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              {header.vehicle} · {header.wrap_type}
            </p>
          </div>
          <div className="flex items-center gap-4 text-right">
            <div>
              <p className="text-[10px] uppercase tracking-wide text-slate-500">Quoted</p>
              <p className="text-sm font-semibold text-slate-900">{money(header.quoted_price)}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-slate-500">Deposit</p>
              <p className="text-sm font-semibold text-slate-700">{header.deposit_status || '—'}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-slate-500">Balance</p>
              <p className="text-sm font-semibold text-rose-700">{money(header.balance_due)}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-100" data-testid="wrap-header-respond-row">
          <span className="text-[11px] uppercase tracking-wide text-slate-500 mr-1">Respond:</span>
          <Link to={`/orders/${orderId}`} data-testid="wrap-respond-open-order">
            <Button size="sm" variant="outline" className="text-xs h-8">
              <FileTextIcon className="h-3.5 w-3.5 mr-1" /> Open Order
            </Button>
          </Link>
          <Link to="/admin-portal" data-testid="wrap-respond-open-conversation">
            <Button size="sm" variant="outline" className="text-xs h-8">
              <MessageSquare className="h-3.5 w-3.5 mr-1" /> Open Conversation
            </Button>
          </Link>
          <Link to="/customers" data-testid="wrap-respond-open-customer">
            <Button size="sm" variant="outline" className="text-xs h-8">
              <UserSquare className="h-3.5 w-3.5 mr-1" /> Open Customer
            </Button>
          </Link>
        </div>
        {/* Header action buttons removed for launch — these will be wired to real actions in Phase 2 */}
      </div>
    </div>
  );
}
