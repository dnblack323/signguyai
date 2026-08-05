import { useEffect, useReducer, useCallback, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Sparkles, Loader2, X, Mail, AlertCircle, CalendarCheck, ChevronRight, Bell } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const KIND_ICON = {
  stale_quote: Mail,
  overdue_invoice: AlertCircle,
  pending_appointment: CalendarCheck,
  reminder: Bell,
};
const KIND_STYLE = {
  stale_quote:         { bg: '#FEF3C7', border: '#FDE68A', iconColor: '#D97706' },
  overdue_invoice:     { bg: '#FEE2E2', border: '#FECACA', iconColor: '#DC2626' },
  pending_appointment: { bg: '#D1FAE5', border: '#A7F3D0', iconColor: '#059669' },
  reminder:            { bg: '#FEFCE8', border: '#FEF08A', iconColor: '#CA8A04' },
};

/**
 * Proactive Assistant Nudges — surfaced on the Dashboard.
 *
 * Props:
 *   sectionMode (bool) — when true, renders content inline without the outer
 *   card shell so it can be embedded as a section inside another card.
 */
export default function AssistantNudgesWidget({ sectionMode = false }) {
  const navigate = useNavigate();

  const [state, dispatch] = useReducer((s, action) => {
    switch (action.type) {
      case 'LOADED':     return { ...s, nudges: action.nudges, loading: false };
      case 'LOAD_ERR':   return { ...s, nudges: [], loading: false };
      case 'DISMISS':    return { ...s, dismissed: (() => { const n = new Set(s.dismissed); n.add(action.key); try { localStorage.setItem(`assistant_nudges_dismissed_${new Date().toISOString().slice(0,10)}`, JSON.stringify([...n])); } catch (e) { /* ignore */ } return n; })() };
      case 'FILTER':     return { ...s, nudges: s.nudges.filter(action.pred) };
      case 'DRAFT':      return { ...s, draft: action.payload };
      case 'DRAFT_UPD':  return { ...s, draft: { ...s.draft, ...action.patch } };
      case 'DRAFT_DONE': return { ...s, draft: null };
      default:           return s;
    }
  }, {
    nudges: [], loading: true,
    dismissed: (() => { try { return new Set(JSON.parse(localStorage.getItem(`assistant_nudges_dismissed_${new Date().toISOString().slice(0,10)}`) || '[]')); } catch { return new Set(); } })(),
    draft: null,
  });

  const { nudges, loading, dismissed, draft: draftState } = state;
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);

  const dismiss = useCallback((nudgeKey) => dispatch({ type: 'DISMISS', key: nudgeKey }), []);

  const load = useCallback(async () => {
    try {
      const r = await axios.get(`${API}/ai/assistant/nudges`, {
        headers: { Authorization: `Bearer ${getAuthToken()}` },
      });
      if (mounted.current) dispatch({ type: 'LOADED', nudges: r.data?.nudges || [] });
    } catch {
      if (mounted.current) dispatch({ type: 'LOAD_ERR' });
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAction = useCallback(async (n, idx) => {
    const key = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || n.ref?.reminder_id || idx}`;
    if (n.kind === 'pending_appointment' && n.ref?.appointment_id) {
      navigate(`/productivity/appointments/${n.ref.appointment_id}`);
      return;
    }
    if (n.kind === 'reminder' && n.ref?.reminder_id) {
      try {
        await axios.post(
          `${API}/ai/assistant/dismiss-reminder`,
          { reminder_id: n.ref.reminder_id },
          { headers: { Authorization: `Bearer ${getAuthToken()}` } },
        );
        toast.success('Reminder marked done');
        dismiss(key);
        if (mounted.current) dispatch({ type: 'FILTER', pred: (x) => x.ref?.reminder_id !== n.ref.reminder_id });
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Could not dismiss reminder');
      }
      return;
    }
    if (!n.customer?.id) { toast.error('Missing customer id — cannot draft email'); return; }
    try {
      const r = await axios.post(`${API}/ai/assistant/draft-email`, {
        customer_id: n.customer.id,
        kind: n.kind === 'overdue_invoice' ? 'payment_reminder' : 'follow_up',
        quote_id: n.ref?.quote_id,
        invoice_id: n.ref?.invoice_id,
        about: n.subtitle,
      }, { headers: { Authorization: `Bearer ${getAuthToken()}` } });
      if (mounted.current) dispatch({ type: 'DRAFT', payload: { nudge: n, nudgeKey: key, subject: r.data?.subject || '', body: r.data?.body || '', to: r.data?.to, sending: false }});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not draft email');
    }
  }, [dismiss, navigate]);

  const sendDraft = useCallback(async () => {
    if (!draftState) return;
    dispatch({ type: 'DRAFT_UPD', patch: { sending: true } });
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
      if (mounted.current) dispatch({ type: 'DRAFT_DONE' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Send failed');
      if (mounted.current) dispatch({ type: 'DRAFT_UPD', patch: { sending: false } });
    }
  }, [dismiss, draftState]);

  const visible = nudges.filter((n, i) => {
    const k = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || n.ref?.reminder_id || i}`;
    return !dismissed.has(k);
  });

  if (loading) return null;
  if (visible.length === 0) return null;

  // ── Section mode: no outer card shell ────────────────────────────────
  if (sectionMode) {
    return (
      <>
        <div className="space-y-1.5" data-testid="assistant-nudges-section">
          {visible.slice(0, 4).map((n, idx) => {
            const Icon = KIND_ICON[n.kind] || Sparkles;
            const s = KIND_STYLE[n.kind] || { bg: '#F3E8FF', border: '#D8B4FE', iconColor: '#7C3AED' };
            const key = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || n.ref?.reminder_id || idx}`;
            return (
              <div
                key={key}
                className="flex items-center justify-between gap-3 rounded-md px-3 py-2"
                style={{ backgroundColor: s.bg, border: `1px solid ${s.border}` }}
                data-testid={`nudge-${n.kind}-${idx}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Icon className="h-3.5 w-3.5 flex-shrink-0" style={{ color: s.iconColor }} />
                  <div className="min-w-0">
                    <div className="text-xs font-medium truncate" style={{ color: '#0F172A' }}>{n.title}</div>
                    <div className="text-[10px] truncate" style={{ color: '#475569' }}>{n.subtitle}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <Button
                    size="sm"
                    onClick={() => handleAction(n, idx)}
                    className="h-6 text-[10px] px-2"
                    variant="outline"
                    style={{ color: s.iconColor, borderColor: s.border }}
                    data-testid={`nudge-${n.kind}-${idx}-act`}
                  >
                    {n.confirm_label} <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                  <button
                    onClick={() => dismiss(key)}
                    className="p-1 rounded transition-colors hover:bg-black/10"
                    style={{ color: '#94A3B8' }}
                    aria-label="Dismiss"
                    data-testid={`nudge-${n.kind}-${idx}-dismiss`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
        {draftState && (
          <DraftEmailModal
            state={draftState}
            onChange={(patch) => dispatch({ type: 'DRAFT_UPD', patch })}
            onClose={() => dispatch({ type: 'DRAFT_DONE' })}
            onSend={sendDraft}
          />
        )}
      </>
    );
  }

  // ── Standalone card mode (default) ───────────────────────────────────
  return (
    <>
      <div
        className="rounded-xl p-4 sm:p-5"
        style={{ backgroundColor: '#F5F3FF', border: '1px solid #DDD6FE' }}
        data-testid="assistant-nudges-widget"
      >
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-md bg-purple-100">
            <Sparkles className="h-4 w-4 text-purple-600" />
          </div>
          <h3 className="text-sm font-semibold" style={{ color: '#1E1B4B' }}>Assistant suggestions</h3>
          <span className="text-xs" style={{ color: '#6D28D9' }}>{visible.length} for you today</span>
        </div>

        <div className="space-y-2">
          {visible.slice(0, 4).map((n, idx) => {
            const Icon = KIND_ICON[n.kind] || Sparkles;
            const s = KIND_STYLE[n.kind] || { bg: '#F3E8FF', border: '#D8B4FE', iconColor: '#7C3AED' };
            const key = `${n.kind}_${n.ref?.quote_id || n.ref?.invoice_id || n.ref?.appointment_id || n.ref?.reminder_id || idx}`;
            return (
              <div
                key={key}
                className="flex items-center justify-between gap-3 rounded-md px-3 py-2"
                style={{ backgroundColor: s.bg, border: `1px solid ${s.border}` }}
                data-testid={`nudge-${n.kind}-${idx}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Icon className="h-4 w-4 flex-shrink-0" style={{ color: s.iconColor }} />
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate" style={{ color: '#0F172A' }}>{n.title}</div>
                    <div className="text-xs opacity-80 truncate" style={{ color: '#475569' }}>{n.subtitle}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <Button
                    size="sm"
                    onClick={() => handleAction(n, idx)}
                    className="h-7 text-xs px-2"
                    variant="outline"
                    style={{ color: s.iconColor, borderColor: s.border }}
                    data-testid={`nudge-${n.kind}-${idx}-act`}
                  >
                    {n.confirm_label} <ChevronRight className="h-3 w-3 ml-1" />
                  </Button>
                  <button
                    onClick={() => dismiss(key)}
                    className="p-1 rounded transition-colors hover:bg-black/10"
                    style={{ color: '#94A3B8' }}
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
          onChange={(patch) => dispatch({ type: 'DRAFT_UPD', patch })}
          onClose={() => dispatch({ type: 'DRAFT_DONE' })}
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
