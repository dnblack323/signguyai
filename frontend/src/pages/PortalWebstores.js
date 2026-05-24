import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import {
  Loader2, Store, ExternalLink, Copy, CheckCircle, AlertCircle, Lock,
  Heart, Calendar, MapPin, Truck, Receipt, Activity, FileText, X, ListChecks,
} from 'lucide-react';
import { toast } from 'sonner';
import { getPortalToken, getPortalCustomerName } from '../lib/authStorage';
import { PortalLayout } from './PortalDashboard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (n) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(n || 0));

const formatDate = (d) => (d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—');

function StatusBadge({ status }) {
  const map = {
    active: 'bg-green-100 text-green-700',
    pending: 'bg-amber-100 text-amber-700',
    disabled: 'bg-slate-100 text-slate-600',
  };
  return (
    <Badge className={map[status] || 'bg-slate-100 text-slate-600'} variant="outline" data-testid={`store-status-${status}`}>
      {status || 'unknown'}
    </Badge>
  );
}

function StoreTypeBadge({ type }) {
  const map = {
    business: { label: 'Business', cls: 'bg-blue-100 text-blue-700' },
    fundraiser: { label: 'Fundraiser', cls: 'bg-pink-100 text-pink-700' },
    creator: { label: 'Creator', cls: 'bg-purple-100 text-purple-700' },
    event: { label: 'Event', cls: 'bg-teal-100 text-teal-700' },
  };
  const info = map[type] || { label: type || 'Store', cls: 'bg-slate-100 text-slate-700' };
  return <Badge className={info.cls} variant="outline">{info.label}</Badge>;
}

function ReadOnlyField({ label, value, hint, testId }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1">
      <div className="min-w-0">
        <p className="text-xs text-slate-500">{label}</p>
        <p className="font-medium text-slate-900 text-sm" data-testid={testId}>{value || '—'}</p>
      </div>
      {hint && (
        <Badge variant="outline" className="shrink-0 text-[10px] gap-1 bg-amber-50 text-amber-800 border-amber-200">
          <Lock className="h-3 w-3" />{hint}
        </Badge>
      )}
    </div>
  );
}

function StripeBlock({ store, onRefresh, onStartOnboarding, onDashboard, busyAction }) {
  const onboarded = !!store.owner_stripe_charges_enabled;
  const started = !!store.owner_stripe_account_id;

  if (onboarded) {
    return (
      <div className="rounded-md border border-green-200 bg-green-50 p-3 space-y-2" data-testid="portal-store-stripe-ready">
        <div className="flex items-center gap-2 text-green-800">
          <CheckCircle className="h-4 w-4" />
          <p className="font-medium text-sm">Stripe connected — payouts active</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" variant="outline" onClick={onDashboard} disabled={!!busyAction} data-testid="portal-store-stripe-dashboard">
            <ExternalLink className="h-3.5 w-3.5 mr-1.5" /> Stripe Dashboard
          </Button>
          <Button size="sm" variant="ghost" onClick={onRefresh} disabled={!!busyAction} data-testid="portal-store-stripe-refresh">
            Refresh status
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-2" data-testid="portal-store-stripe-pending">
      <div className="flex items-center gap-2 text-amber-900">
        <AlertCircle className="h-4 w-4" />
        <p className="font-medium text-sm">
          {started ? 'Stripe onboarding incomplete' : 'Connect Stripe to receive payouts'}
        </p>
      </div>
      <p className="text-xs text-amber-800">
        Customers can browse this store, but checkout is inactive until your Stripe account is fully onboarded.
      </p>
      <div className="flex gap-2 flex-wrap">
        <Button size="sm" onClick={onStartOnboarding} disabled={!!busyAction} data-testid="portal-store-stripe-onboard">
          {started ? 'Continue Stripe Onboarding' : 'Complete Stripe Onboarding'}
        </Button>
        {started && (
          <Button size="sm" variant="ghost" onClick={onRefresh} disabled={!!busyAction} data-testid="portal-store-stripe-refresh">
            I just finished — refresh status
          </Button>
        )}
      </div>
    </div>
  );
}

function FundraiserSummary({ store }) {
  if (!store.fundraiser_enabled) return null;
  const goal = Number(store.fundraiser_goal_amount || 0);
  const raised = Number(store.total_raised || 0);
  const showBar = store.show_progress_bar && goal > 0;
  const pct = goal > 0 ? Math.min(100, (raised / goal) * 100) : 0;

  return (
    <div className="rounded-md border bg-pink-50/50 border-pink-100 p-3 space-y-2" data-testid="portal-store-fundraiser-summary">
      <div className="flex items-center gap-2 text-pink-900">
        <Heart className="h-4 w-4" />
        <p className="font-medium text-sm">
          {store.fundraiser_name || 'Fundraiser'}
        </p>
      </div>
      {store.fundraiser_description && (
        <p className="text-xs text-slate-600">{store.fundraiser_description}</p>
      )}
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <p className="text-slate-500">Donations</p>
          <p className="font-semibold text-slate-900" data-testid="portal-store-total-donations">{formatCurrency(store.total_donations)}</p>
        </div>
        <div>
          <p className="text-slate-500">Profit allocated</p>
          <p className="font-semibold text-slate-900" data-testid="portal-store-total-profit-allocated">{formatCurrency(store.total_profit_allocated)}</p>
        </div>
        <div>
          <p className="text-slate-500">Total raised</p>
          <p className="font-semibold text-slate-900" data-testid="portal-store-total-raised">{formatCurrency(store.total_raised)}</p>
        </div>
      </div>
      {showBar && (
        <div data-testid="portal-store-fundraiser-progress">
          <div className="flex justify-between text-xs mb-1 text-slate-600">
            <span>Progress</span>
            <span className="font-medium">{formatCurrency(raised)} / {formatCurrency(goal)}</span>
          </div>
          <div className="w-full bg-pink-100 rounded-full h-2 overflow-hidden">
            <div className="h-2 bg-pink-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}
    </div>
  );
}

function EventDetails({ store }) {
  if (store.store_type !== 'event') return null;
  return (
    <div className="rounded-md border bg-slate-50 p-3 space-y-1" data-testid="portal-store-event-details">
      <div className="flex items-center gap-2 text-slate-800 mb-1">
        <Calendar className="h-4 w-4" />
        <p className="font-medium text-sm">Event Details</p>
      </div>
      <ReadOnlyField label="Event Name" value={store.event_name} testId="portal-store-event-name" />
      <ReadOnlyField label="Event Type" value={store.event_type} />
      <ReadOnlyField
        label="Event Dates"
        value={`${formatDate(store.event_start_date)} → ${formatDate(store.event_end_date)}`}
        testId="portal-store-event-dates"
      />
      <ReadOnlyField label="Order Deadline" value={formatDate(store.order_deadline)} testId="portal-store-order-deadline" />
      <ReadOnlyField label="Pickup / Delivery Date" value={formatDate(store.pickup_delivery_date)} />
      {store.event_location && (
        <div className="flex items-start gap-2 text-xs text-slate-600">
          <MapPin className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{store.event_location}</span>
        </div>
      )}
      {store.pickup_delivery_instructions && (
        <div className="flex items-start gap-2 text-xs text-slate-600">
          <Truck className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{store.pickup_delivery_instructions}</span>
        </div>
      )}
    </div>
  );
}

function FinancialSummary({ store }) {
  const locked = store.locked_settings || {};
  const shAmount = locked.shipping_handling_enabled
    ? Number(locked.shipping_handling_fee || 0)
    : Number(locked.shipping_fee || 0) + Number(locked.handling_fee || 0);

  return (
    <div className="rounded-md border bg-white p-3 space-y-1" data-testid="portal-store-financial-summary">
      <div className="flex items-center gap-2 text-slate-800 mb-1">
        <Receipt className="h-4 w-4" />
        <p className="font-medium text-sm">Financial Summary</p>
        <Badge variant="outline" className="ml-auto text-[10px] gap-1 bg-amber-50 text-amber-800 border-amber-200">
          <Lock className="h-3 w-3" />Read-only
        </Badge>
      </div>
      <ReadOnlyField label="Total Orders" value={store.total_orders} testId="portal-store-total-orders" />
      <ReadOnlyField label="Gross Sales" value={formatCurrency(store.total_sales)} testId="portal-store-total-sales" />
      <ReadOnlyField label="Payout Owed" value={formatCurrency(store.payout_owed)} testId="portal-store-payout-owed" />
      <ReadOnlyField label="Payout Paid" value={formatCurrency(store.payout_paid)} />
      <Separator className="my-2" />
      {shAmount > 0 ? (
        <ReadOnlyField
          label={locked.shipping_handling_label || 'Shipping & Handling'}
          value={formatCurrency(shAmount)}
          hint="Set by store provider"
          testId="portal-store-shipping-handling"
        />
      ) : (
        <p className="text-xs text-slate-500">Shipping &amp; handling not configured.</p>
      )}
    </div>
  );
}

function QuestionnaireBlock({ store }) {
  const q = store.questionnaire;
  if (!q) return null;
  if (!q.linked) {
    return (
      <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600" data-testid="portal-store-questionnaire-block">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4" /> No questionnaire sent yet.
        </div>
      </div>
    );
  }
  const status = q.questionnaire?.status || 'sent';
  const submitted = q.latest_response?.submitted_at;
  const applied = q.latest_response?.applied_to_webstore;

  return (
    <div className="rounded-md border border-slate-200 bg-white p-3 text-sm space-y-1" data-testid="portal-store-questionnaire-block">
      <div className="flex items-center gap-2 text-slate-800">
        <FileText className="h-4 w-4" />
        <p className="font-medium">Setup Questionnaire</p>
        <Badge variant="outline" className="ml-auto">{submitted ? (applied ? 'Applied' : 'Submitted') : status}</Badge>
      </div>
      <p className="text-xs text-slate-500">
        Last sent: {formatDate(q.questionnaire?.last_sent_at)} · Responses: {q.questionnaire?.response_count || 0}
      </p>
    </div>
  );
}

function RecentOrdersBlock({ orders }) {
  if (!orders || orders.length === 0) return null;
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3" data-testid="portal-store-recent-orders">
      <div className="flex items-center gap-2 text-slate-800 mb-2">
        <Activity className="h-4 w-4" />
        <p className="font-medium text-sm">Recent Orders</p>
      </div>
      <div className="space-y-1.5">
        {orders.slice(0, 5).map((o) => (
          <div key={o.id} className="flex items-center justify-between text-xs">
            <div className="min-w-0">
              <p className="font-medium text-slate-800 truncate">{o.customer_name || 'Customer'}</p>
              <p className="text-slate-500">{formatDate(o.created_at)} · {o.status}</p>
            </div>
            <p className="font-semibold text-slate-900 shrink-0">
              {formatCurrency(o.grand_total || o.subtotal || 0)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function OwnerChecklist({ store }) {
  // Derive checklist purely from data already on the sanitized store doc.
  const questionnaire = store.questionnaire || {};
  const qSubmitted = !!questionnaire.latest_response?.submitted_at;
  const stripeReady = !!store.owner_stripe_charges_enabled;
  const storeLive = store.status === 'active';
  const firstOrder = Array.isArray(store.recent_orders) && store.recent_orders.length > 0;
  const fundraiserEnabled = !!store.fundraiser_enabled;
  const isEvent = store.store_type === 'event';

  const items = [
    { key: 'assigned', label: 'Store assigned to you', done: true },
    ...(isEvent
      ? [{ key: 'questionnaire', label: 'Setup questionnaire completed', done: qSubmitted,
           hint: qSubmitted ? null : 'Watch your email for the setup questionnaire from the sign shop.' }]
      : []),
    { key: 'stripe', label: 'Stripe onboarding complete', done: stripeReady,
      hint: stripeReady ? null : 'Click "Complete Stripe Onboarding" above to start receiving payouts.' },
    { key: 'live', label: 'Store live (accepting orders)', done: storeLive,
      hint: storeLive ? null : 'The sign shop activates the store once Stripe + products are ready.' },
    { key: 'first_order', label: 'First order received', done: firstOrder, optional: true,
      hint: firstOrder ? null : 'Share your public store link to launch — copy the link above.' },
    ...(isEvent
      ? [{ key: 'fundraiser', label: 'Fundraiser enabled', done: fundraiserEnabled, optional: true,
           hint: fundraiserEnabled ? null : 'Optional — your sign shop can enable a fundraiser for this event.' }]
      : []),
  ];

  const required = items.filter((i) => !i.optional);
  const doneCount = required.filter((i) => i.done).length;
  const pct = required.length === 0 ? 0 : Math.round((doneCount / required.length) * 100);

  return (
    <div className="rounded-md border bg-white p-3 space-y-2" data-testid="portal-store-owner-checklist">
      <div className="flex items-center gap-2 text-slate-800">
        <ListChecks className="h-4 w-4" />
        <p className="font-medium text-sm">Onboarding Checklist</p>
        <span className="ml-auto text-xs font-semibold text-slate-600" data-testid="portal-store-checklist-progress">
          {doneCount} / {required.length} ({pct}%)
        </span>
      </div>
      <ul className="space-y-1.5">
        {items.map((i) => (
          <li
            key={i.key}
            className="flex items-start gap-2 text-xs"
            data-testid={`portal-store-checklist-${i.key}-${i.done ? 'done' : 'todo'}`}
          >
            {i.done ? (
              <CheckCircle className="h-3.5 w-3.5 mt-0.5 text-green-600 shrink-0" />
            ) : (
              <div className="h-3.5 w-3.5 mt-0.5 rounded-full border border-slate-300 shrink-0" />
            )}
            <div className="min-w-0">
              <p className={i.done ? 'line-through text-slate-400' : 'text-slate-700 font-medium'}>
                {i.label} {i.optional && !i.done && <span className="text-slate-400">(optional)</span>}
              </p>
              {!i.done && i.hint && <p className="text-slate-500">{i.hint}</p>}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}


function AssignmentNotificationBanner({ onDismissed }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const token = getPortalToken();
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/api/portal/notifications?notification_type=webstore_assigned&unread_only=true`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const data = res.ok ? await res.json() : [];
      setNotifications(Array.isArray(data) ? data : []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const dismiss = async (id) => {
    const token = getPortalToken();
    try {
      const res = await fetch(`${API_URL}/api/portal/notifications/${id}/dismiss`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to dismiss');
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      if (onDismissed) onDismissed();
    } catch (err) {
      toast.error('Could not dismiss notification');
    }
  };

  if (loading || notifications.length === 0) return null;

  return (
    <div className="mb-6 space-y-2" data-testid="portal-webstore-assignment-banner">
      {notifications.map((n) => (
        <Alert key={n.id} className="border-teal-200 bg-teal-50" data-testid={`portal-assignment-notif-${n.id}`}>
          <CheckCircle className="h-4 w-4 text-teal-700" />
          <AlertTitle className="flex items-center gap-2 text-teal-900">
            {n.title}
            <Button
              size="sm"
              variant="ghost"
              className="ml-auto h-7 px-2 text-teal-700 hover:bg-teal-100"
              onClick={() => dismiss(n.id)}
              data-testid={`portal-assignment-notif-dismiss-${n.id}`}
              aria-label="Dismiss notification"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </AlertTitle>
          <AlertDescription className="text-teal-900 text-sm">{n.message}</AlertDescription>
        </Alert>
      ))}
    </div>
  );
}


function StoreCard({ store, onChanged }) {
  const [busy, setBusy] = useState(null);
  const [detail, setDetail] = useState(store);
  const publicUrl = `${window.location.origin}${detail.public_path || `/store/${detail.id}`}`;

  const refresh = useCallback(async () => {
    const token = getPortalToken();
    try {
      const res = await fetch(`${API_URL}/api/portal/webstores/${detail.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const d = await res.json();
        setDetail(d);
        if (onChanged) onChanged(d);
      } else {
        // Don't blank the card — keep the list-level data we already have.
        console.warn(`Webstore detail refresh failed: ${res.status}`);
      }
    } catch (err) {
      console.warn('Webstore detail refresh failed', err);
    }
  }, [detail.id, onChanged]);

  // First mount: pull full detail (list endpoint returns the same shape minus
  // recent_orders + questionnaire — fetch detail to enrich the card).
  useEffect(() => { refresh(); /* eslint-disable-line react-hooks/exhaustive-deps */ }, []);

  const copyLink = () => {
    navigator.clipboard.writeText(publicUrl).then(
      () => toast.success('Store link copied'),
      () => toast.error('Could not copy link'),
    );
  };

  const startStripe = async () => {
    setBusy('onboarding');
    try {
      const token = getPortalToken();
      const res = await fetch(`${API_URL}/api/portal/webstores/${detail.id}/stripe-onboarding`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          return_url: `${window.location.origin}/customer-portal/webstores?stripe=return`,
          refresh_url: `${window.location.origin}/customer-portal/webstores?stripe=refresh`,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Failed to start onboarding');
      window.location.href = data.url;
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(null);
    }
  };

  const refreshStripe = async () => {
    setBusy('refresh');
    try {
      const token = getPortalToken();
      const res = await fetch(`${API_URL}/api/portal/webstores/${detail.id}/stripe-refresh`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Failed to refresh');
      await refresh();
      if (data.ready) toast.success('Stripe is fully connected!');
      else toast.info('Stripe onboarding still incomplete.');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(null);
    }
  };

  const openDashboard = async () => {
    setBusy('dashboard');
    try {
      const token = getPortalToken();
      const res = await fetch(`${API_URL}/api/portal/webstores/${detail.id}/stripe-login-link`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || 'Failed to open Stripe dashboard');
      window.open(data.url, '_blank', 'noopener');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="overflow-hidden" data-testid={`portal-webstore-card-${detail.id}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-base flex items-center gap-2 flex-wrap">
              <span data-testid="portal-store-name" className="truncate">{detail.name}</span>
              <StoreTypeBadge type={detail.store_type} />
              <StatusBadge status={detail.status} />
            </CardTitle>
            {detail.description && (
              <CardDescription className="mt-1 line-clamp-2">{detail.description}</CardDescription>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Public link + QR */}
        <div className="rounded-md border bg-slate-50 p-3 flex items-start gap-3" data-testid="portal-store-public-link">
          <div className="shrink-0 p-2 bg-white rounded">
            <QRCodeSVG value={publicUrl} size={72} data-testid="portal-store-qr" />
          </div>
          <div className="min-w-0 flex-1 space-y-1">
            <p className="text-xs text-slate-500">Public store link</p>
            <p className="text-sm font-medium text-slate-800 break-all">{publicUrl}</p>
            <div className="flex gap-2 flex-wrap pt-1">
              <Button size="sm" variant="outline" onClick={copyLink} data-testid="portal-store-copy-link">
                <Copy className="h-3.5 w-3.5 mr-1.5" /> Copy
              </Button>
              <Button size="sm" variant="outline" asChild>
                <a href={publicUrl} target="_blank" rel="noopener noreferrer" data-testid="portal-store-open-link">
                  <ExternalLink className="h-3.5 w-3.5 mr-1.5" /> Open store
                </a>
              </Button>
            </div>
          </div>
        </div>

        <StripeBlock
          store={detail}
          onStartOnboarding={startStripe}
          onRefresh={refreshStripe}
          onDashboard={openDashboard}
          busyAction={busy}
        />

        <OwnerChecklist store={detail} />

        <EventDetails store={detail} />
        <FundraiserSummary store={detail} />
        <QuestionnaireBlock store={detail} />
        <FinancialSummary store={detail} />
        <RecentOrdersBlock orders={detail.recent_orders} />

        <Alert className="bg-slate-50 border-slate-200">
          <Lock className="h-4 w-4" />
          <AlertTitle className="text-sm">Set by store provider</AlertTitle>
          <AlertDescription className="text-xs text-slate-600">
            Pricing, fees, profit allocation, and shipping/handling are configured by the sign shop. Reach out to your provider if anything needs to change.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}

export default function PortalWebstores() {
  const navigate = useNavigate();
  const customerName = getPortalCustomerName() || 'Customer';
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/portal/webstores`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        navigate('/customer-portal/login');
        return;
      }
      if (!res.ok) {
        // Surface the real error instead of silently rendering the empty state.
        let detail = '';
        try {
          const errData = await res.json();
          detail = typeof errData?.detail === 'string' ? errData.detail : '';
        } catch (_) { /* response wasn't JSON */ }
        throw new Error(detail || `Webstore service returned ${res.status}`);
      }
      const data = await res.json();
      setStores(Array.isArray(data) ? data : []);
    } catch (err) {
      setStores([]);
      setError(err.message || 'Failed to load webstores');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => { load(); }, [load]);

  // Returning from Stripe AccountLink: refresh on mount so flags catch up.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('stripe')) {
      // Strip the param so the URL is clean after first refresh.
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  return (
    <PortalLayout activeNav="webstores" customerName={customerName}>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Store className="h-6 w-6 text-teal-600" /> Your Webstores
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage the storefronts you've been assigned as the owner. Pricing and fees are set by your sign shop.
        </p>
      </div>

      <AssignmentNotificationBanner />

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      )}

      {!loading && error && (
        <Alert variant="destructive" data-testid="portal-webstores-error">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Couldn't load your webstores</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && !error && stores.length === 0 && (
        <Card data-testid="portal-webstores-empty">
          <CardContent className="py-12 text-center">
            <Store className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-600">You aren't assigned to any webstores yet.</p>
            <p className="text-xs text-slate-400 mt-1">Your sign shop will add you as an owner when a store is ready.</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && stores.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="portal-webstores-grid">
          {stores.map((s) => (
            <StoreCard key={s.id} store={s} />
          ))}
        </div>
      )}
    </PortalLayout>
  );
}
