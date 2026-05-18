// Phase 2F follow-up: Pending Customer Actions widget for the main Dashboard.
// Read-only. Shows every wrap ticket waiting on a customer action and links to
// the existing internal pages — no message templates, no AI dispatch.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Inbox, FileText as FileTextIcon, Wand2, MessageSquare, Loader2 } from 'lucide-react';
import { getAuthToken } from '../../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const ACTION_BADGE = {
  proof_pending: 'bg-violet-100 text-violet-800 border-violet-200',
  revision_requested: 'bg-amber-100 text-amber-800 border-amber-200',
  contract_pending: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  quote_pending: 'bg-sky-100 text-sky-800 border-sky-200',
  inspection_pending: 'bg-purple-100 text-purple-800 border-purple-200',
  aftercare_pending: 'bg-teal-100 text-teal-800 border-teal-200',
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
    <Card data-testid="pending-customer-actions-widget" className="border-violet-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Inbox className="h-4 w-4 text-violet-600" />
          Pending Customer Actions
        </CardTitle>
        <CardDescription>
          Wrap tickets waiting on a customer reply or signature.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-6 text-slate-500" data-testid="pending-actions-loading">
            <Loader2 className="h-4 w-4 animate-spin mr-2" /> Loading…
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500 italic" data-testid="pending-actions-empty">
            All wrap tickets are caught up. Nothing waiting on a customer.
          </p>
        ) : (
          <div className="space-y-3" data-testid="pending-actions-list">
            {items.map((it) => (
              <div
                key={it.ticket_id}
                className="rounded-lg border border-slate-200 p-3 space-y-2"
                data-testid={`pending-actions-row-${it.ticket_id}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-900 truncate">
                      {it.customer_name} · #{it.order_number || '—'}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {it.wrap_type} · {it.vehicle || 'Vehicle'}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {(it.actions || []).map((a) => (
                    <Badge
                      key={a.code}
                      className={`text-[10px] uppercase border ${ACTION_BADGE[a.code] || 'bg-slate-100 text-slate-800 border-slate-200'}`}
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
      </CardContent>
    </Card>
  );
}
