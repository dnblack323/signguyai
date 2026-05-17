// Phase 1: Sticky page header — shows merged order/item info + action buttons.
import { Link } from 'react-router-dom';
import { ArrowLeft, Send, FileSignature, ClipboardList, Wand2, CalendarClock, Heart, Package, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { toast } from 'sonner';
import { TOAST_PHASE1 } from './constants';

const HEADER_ACTIONS = [
  { id: 'send_quote',       label: 'Send Quote',          icon: Send },
  { id: 'send_contract',    label: 'Send Contract',       icon: FileSignature },
  { id: 'send_quest',       label: 'Send Questionnaire',  icon: ClipboardList },
  { id: 'create_mockup',    label: 'Create AI Mockup',    icon: Wand2 },
  { id: 'schedule_install', label: 'Schedule Install',    icon: CalendarClock },
  { id: 'send_aftercare',   label: 'Send Aftercare',      icon: Heart },
  { id: 'final_packet',     label: 'Generate Final Packet', icon: Package },
  { id: 'mark_complete',    label: 'Mark Complete',       icon: CheckCircle2 },
];

const money = (n) => (typeof n === 'number' ? `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—');

export default function WrapCommandHeader({ orderId, header }) {
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
        <div className="flex flex-wrap gap-1.5" data-testid="wrap-header-actions">
          {HEADER_ACTIONS.map((a) => (
            <Button
              key={a.id}
              size="sm"
              variant="outline"
              className="text-xs h-8"
              onClick={() => toast.message(a.label, { description: TOAST_PHASE1 })}
              data-testid={`wrap-header-action-${a.id}`}
            >
              <a.icon className="h-3.5 w-3.5 mr-1" /> {a.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
