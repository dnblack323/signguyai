import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Sparkles, Loader2, X, Mail, AlertCircle, CalendarCheck, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const KIND_ICON = {
  stale_quote: Mail,
  overdue_invoice: AlertCircle,
  pending_appointment: CalendarCheck,
};
const KIND_COLOR = {
  stale_quote: 'text-amber-600 bg-amber-50 border-amber-200',
  overdue_invoice: 'text-rose-600 bg-rose-50 border-rose-200',
  pending_appointment: 'text-emerald-600 bg-emerald-50 border-emerald-200',
};

/**
 * Proactive Assistant Nudges — surfaced on the Dashboard.
 *
 * Pulls /api/ai/assistant/nudges (cached/dismissed in localStorage for the
 * current day so a user who dismisses doesn't see the same items spam-loop)
 * and renders a one-click action pill per item.
 *
 * For stale-quote / overdue-invoice nudges, "Draft" calls /assistant/draft-email
 * and opens a small inline review-and-send modal. For appointment nudges, we
 * route to the appointment detail page.
 */
export default function AssistantNudgesWidget() {
  const navigate = useNavigate();
  const [nudges, setNudges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(() => {
    try {
      const k = `assistant_nudges_dismissed_${new Date().toISOString().slice(0, 10)}`;
      return new Set(JSON.parse(localStorage.getItem(k) || '[]'));
    } catch { return new Set(); }
  });
  const [draftState, setDraftState] = useState(null); // { nudge, subject, body, sending }

  const persistDismissed = useCallback((s) => {
    const k = `assistant_nudges_dismissed_${new Date().toISOString().slice(0, 10)}`;
    localStorage.setItem(k, JSON.stringify(Array.from(s)));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/ai/assistant/nudges`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      setNudges(r.data?.nudges || []);
    } catch {
      setNudges([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const dismiss = (nudgeKey) => {
    const next = new Set(dismissed); next.add(nudgeKey);
    setDismissed(next);
    persistDismissed(next);
  };

  const handleAction = async (n, idx) => {
    const key = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || idx}`;
    if (n.kind === 'pending_appointment' && n.ref?.appointment_id) {
      navigate(`/appointments/${n.ref.appointment_id}`);
      return;
    }
    // Draft email path (stale_quote or overdue_invoice)
    if (!n.customer?.id) {
      toast.error('Missing customer id — cannot draft email');
      return;
    }
    try {
      const r = await axios.post(`${API}/ai/assistant/draft-email`, {
        customer_id: n.customer.id,
        kind: n.kind === 'overdue_invoice' ? 'payment_reminder' : 'follow_up',
        quote_id: n.ref?.quote_id,
        invoice_id: n.ref?.invoice_id,
        about: n.subtitle,
      }, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
      setDraftState({
        nudge: n,
        nudgeKey: key,
        subject: r.data?.subject || '',
        body: r.data?.body || '',
        to: r.data?.to,
        sending: false,
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not draft email');
    }
  };

  const sendDraft = async () => {
    if (!draftState) return;
    setDraftState((p) => ({ ...p, sending: true }));
    try {
      await axios.post(`${API}/ai/assistant/send-email`, {
        customer_id: draftState.nudge.customer.id,
        subject: draftState.subject,
        body: draftState.body,
        quote_id: draftState.nudge.ref?.quote_id,
        invoice_id: draftState.nudge.ref?.invoice_id,
      }, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
      toast.success(`Email sent to ${draftState.to}`);
      dismiss(draftState.nudgeKey);
      setDraftState(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Send failed');
      setDraftState((p) => ({ ...p, sending: false }));
    }
  };

  const visible = nudges.filter((n, i) => {
    const k = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || i}`;
    return !dismissed.has(k);
  });

  if (loading) return null;
  if (visible.length === 0) return null;

  return (
    <>
      <div
        className="rounded-xl border bg-gradient-to-br from-purple-50 via-white to-white p-4 sm:p-5"
        style={{ borderColor: 'var(--border-light)' }}
        data-testid="assistant-nudges-widget"
      >
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-md bg-purple-100">
            <Sparkles className="h-4 w-4 text-purple-600" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Assistant suggestions</h3>
          <span className="text-xs text-slate-500">{visible.length} for you today</span>
        </div>

        <div className="space-y-2">
          {visible.slice(0, 4).map((n, idx) => {
            const Icon = KIND_ICON[n.kind] || Sparkles;
            const color = KIND_COLOR[n.kind] || 'text-purple-600 bg-purple-50 border-purple-200';
            const key = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || idx}`;
            return (
              <div
                key={key}
                className={`flex items-center justify-between gap-3 border rounded-md px-3 py-2 ${color}`}
                data-testid={`nudge-${n.kind}-${idx}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{n.title}</div>
                    <div className="text-xs opacity-80 truncate">{n.subtitle}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <Button
                    size="sm"
                    onClick={() => handleAction(n, idx)}
                    className="bg-white border border-current hover:bg-current hover:text-white h-7 text-xs px-2"
                    variant="outline"
                    data-testid={`nudge-${n.kind}-${idx}-act`}
                  >
                    {n.confirm_label} <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                  <button
                    onClick={() => dismiss(key)}
                    className="p-1 rounded hover:bg-white/60 transition-colors"
                    aria-label="Dismiss"
                    data-testid={`nudge-${n.kind}-${idx}-dismiss`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {draftState && (
        <DraftEmailModal
          state={draftState}
          onChange={(patch) => setDraftState((p) => ({ ...p, ...patch }))}
          onClose={() => setDraftState(null)}
          onSend={sendDraft}
        />
      )}
    </>
  );
}

function DraftEmailModal({ state, onChange, onClose, onSend }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      data-testid="assistant-draft-email-modal"
    >
      <div className="bg-white rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-purple-600" />
            <h3 className="font-semibold text-slate-900">Review email draft</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-slate-100">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5 space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-600 uppercase">To</label>
            <div className="text-sm text-slate-900 mt-0.5">{state.to}</div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 uppercase">Subject</label>
            <input
              className="mt-1 w-full border rounded-md px-3 py-2 text-sm"
              value={state.subject}
              onChange={(e) => onChange({ subject: e.target.value })}
              data-testid="draft-email-subject"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-600 uppercase">Body</label>
            <textarea
              className="mt-1 w-full border rounded-md px-3 py-2 text-sm leading-relaxed h-44 resize-none"
              value={state.body}
              onChange={(e) => onChange({ body: e.target.value })}
              data-testid="draft-email-body"
            />
            <p className="text-xs text-slate-400 mt-1">
              Drafted by your AI assistant — review before sending.
            </p>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t bg-slate-50">
          <Button variant="outline" onClick={onClose} disabled={state.sending}>Cancel</Button>
          <Button
            onClick={onSend}
            disabled={state.sending || !state.subject.trim() || !state.body.trim()}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="draft-email-send"
          >
            {state.sending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Mail className="h-4 w-4 mr-2" />}
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
