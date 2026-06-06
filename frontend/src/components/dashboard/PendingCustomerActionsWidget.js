// Phase 2F follow-up: Pending Customer Actions widget for the main Dashboard.
// Read-only. Shows every wrap ticket waiting on a customer action and links to
// the existing internal pages — no message templates, no AI dispatch.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Inbox, FileText as FileTextIcon, Wand2, MessageSquare, Loader2 } from 'lucide-react';
import { getAuthToken } from '../../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const ACTION_BADGE = {
  proof_pending:      'bg-violet-500/20 text-violet-300 border-violet-500/40',
  revision_requested: 'bg-amber-500/20  text-amber-300  border-amber-500/40',
  contract_pending:   'bg-indigo-500/20 text-indigo-300 border-indigo-500/40',
  quote_pending:      'bg-sky-500/20    text-sky-300    border-sky-500/40',
  inspection_pending: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
  aftercare_pending:  'bg-teal-500/20   text-teal-300   border-teal-500/40',
};

export default function PendingCustomerActionsWidget() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    axios
      .get(`${API}/wrap/pending-customer-actions`, { headers: hdr() })
      .then((res) => {
        if (!cancelled) setItems(res.data?.items || []);
      })
      .catch(() => { if (!cancelled) setItems([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  return (
    <div
      data-testid="pending-customer-actions-widget"
      className="rounded-xl"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}
    >
      <div className="px-5 py-3.5 flex items-center gap-2" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <Inbox className="h-4 w-4 text-violet-400 flex-shrink-0" />
        <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Pending Customer Actions</h2>
      </div>
      <div className="p-4">
        <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>Wrap tickets waiting on a customer reply or signature.</p>
        {loading ? (
          <div className="flex items-center justify-center py-6" style={{ color: 'var(--text-muted)' }} data-testid="pending-actions-loading">
            <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm italic" style={{ color: 'var(--text-muted)' }} data-testid="pending-actions-empty">
            All wrap tickets are caught up. Nothing waiting on a customer.
          </p>
        ) : (
          <div className="space-y-3" data-testid="pending-actions-list">
            {items.map((it) => (
              <div
                key={it.ticket_id}
                className="rounded-lg p-3 space-y-2"
                style={{ backgroundColor: 'var(--surface-2)', border: '1px solid var(--border-light)' }}
                data-testid={`pending-actions-row-${it.ticket_id}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>
                      {it.customer_name} · #{it.order_number || '—'}
                    </p>
                    <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>
                      {it.wrap_type} · {it.vehicle || 'Vehicle'}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {(it.actions || []).map((a) => (
                    <Badge
                      key={a.code}
                      className={`text-[10px] uppercase border ${ACTION_BADGE[a.code] || 'bg-slate-600/30 text-slate-300 border-slate-500/40'}`}
                      data-testid={`pending-actions-badge-${it.ticket_id}-${a.code}`}
                    >
                      {a.label}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <Link to={`/orders/${it.order_id}`} data-testid={`pending-actions-open-order-${it.ticket_id}`}>
                    <Button size="sm" variant="outline" className="text-xs h-7">
                      <FileTextIcon className="h-3 w-3 mr-1" /> Open Order
                    </Button>
                  </Link>
                  <Link
                    to={`/orders/${it.order_id}/items/${it.ticket_id}/wrap-command-center`}
                    data-testid={`pending-actions-open-wrap-${it.ticket_id}`}
                  >
                    <Button size="sm" variant="outline" className="text-xs h-7">
                      <Wand2 className="h-3 w-3 mr-1" /> Wrap CC
                    </Button>
                  </Link>
                  <Link to="/admin-portal" data-testid={`pending-actions-open-admin-${it.ticket_id}`}>
                    <Button size="sm" variant="outline" className="text-xs h-7">
                      <MessageSquare className="h-3 w-3 mr-1" /> Admin Portal
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
