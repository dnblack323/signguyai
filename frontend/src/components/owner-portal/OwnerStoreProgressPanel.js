/**
 * Phase 5 — Owner-facing store progress + finance panel.
 *
 * Hits GET /api/owner-portal/stores/{id}/progress and renders three blocks:
 *   1. Lifecycle progress bar with current stage + next-blocker explainer
 *   2. Required-actions checklist with status / CTA / reason
 *   3. Financial transparency card with split math formula + payout history
 *
 * Privacy: backend strips any internal cost/margin/supplier data before
 * sending; this component never references those fields.
 */
import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  CheckCircle2, Circle, Clock, AlertTriangle, Wallet,
  ChevronRight, ShieldCheck, Info, ExternalLink, Loader2,
} from 'lucide-react';
import { Button } from '../ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const TOKEN_KEY = 'owner_portal_token';

const fmtUsd = (v) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
    Number(v || 0),
  );

const STATUS_PILL = {
  done: { cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30', icon: CheckCircle2 },
  active: { cls: 'bg-blue-500/15 text-blue-300 border-blue-500/30', icon: Clock },
  todo: { cls: 'bg-slate-700/40 text-slate-400 border-slate-600', icon: Circle },
};

export default function OwnerStoreProgressPanel({ storeId, onOpenStripe }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!storeId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const token = localStorage.getItem(TOKEN_KEY);
        const res = await axios.get(
          `${API_URL}/api/owner-portal/stores/${storeId}/progress`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
        if (!cancelled) setData(res.data);
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.detail || 'Failed to load progress');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [storeId]);

  if (loading) {
    return (
      <div className="rounded-md border border-[#1E293B] bg-[#0B0F17] p-6 text-center text-slate-400" data-testid={`owner-progress-loading-${storeId}`}>
        <Loader2 className="h-5 w-5 mx-auto animate-spin text-[#2F8BFB]" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-300" data-testid={`owner-progress-error-${storeId}`}>
        <AlertTriangle className="inline-block h-4 w-4 mr-1.5" />
        {error || 'Progress unavailable right now. Try again shortly.'}
      </div>
    );
  }

  const { current_stage, stages, next_blocker, required_actions, finance, payout_history, privacy_note } = data;
  const pct = Math.round(
    (current_stage.index / Math.max(current_stage.total, 1)) * 100,
  );

  return (
    <div className="space-y-5" data-testid={`owner-progress-panel-${storeId}`}>
      {/* ─── Lifecycle progress ─────────────────────────────────────── */}
      <div className="rounded-md border border-[#1E293B] bg-[#0B0F17] p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-white">Store progress</h3>
          <span className="text-xs text-slate-400" data-testid={`owner-progress-current-${storeId}`}>
            {current_stage.index} / {current_stage.total} · {pct}%
          </span>
        </div>
        <div className="w-full h-1.5 bg-slate-800 rounded overflow-hidden">
          <div
            className="h-full bg-[#2F8BFB] transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-3 text-sm font-medium text-blue-300 flex items-center gap-1.5">
          <ChevronRight className="h-4 w-4" /> {current_stage.label}
        </p>
        {next_blocker && (
          <p className="mt-1 text-xs text-slate-400 ml-5.5">
            {next_blocker}
          </p>
        )}
        <details className="mt-3">
          <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">
            Show full lifecycle
          </summary>
          <ul className="mt-2 space-y-1.5">
            {stages.map((s) => {
              const Pill = STATUS_PILL[s.status] || STATUS_PILL.todo;
              const Icon = Pill.icon;
              return (
                <li
                  key={s.key}
                  className="flex items-center gap-2 text-xs"
                  data-testid={`owner-progress-stage-${s.key}-${s.status}`}
                >
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border ${Pill.cls}`}>
                    <Icon className="h-3 w-3" />
                  </span>
                  <span className={s.status === 'done' ? 'text-slate-300' : s.status === 'active' ? 'text-blue-300' : 'text-slate-500'}>
                    {s.label}
                  </span>
                </li>
              );
            })}
          </ul>
        </details>
      </div>

      {/* ─── Required actions ──────────────────────────────────────── */}
      <div className="rounded-md border border-[#1E293B] bg-[#0B0F17] p-4">
        <h3 className="text-sm font-semibold text-white mb-3">What we need from you</h3>
        <ul className="space-y-2">
          {required_actions.map((a) => {
            const Pill = STATUS_PILL[a.status] || STATUS_PILL.todo;
            const Icon = Pill.icon;
            const isStripe = a.key === 'stripe_onboarding';
            return (
              <li
                key={a.key}
                className="flex items-start gap-2.5 text-sm"
                data-testid={`owner-action-${a.key}-${a.status}`}
              >
                <span className={`inline-flex items-center justify-center w-5 h-5 mt-0.5 rounded-full border ${Pill.cls}`}>
                  <Icon className="h-3 w-3" />
                </span>
                <div className="flex-1">
                  <p className={`font-medium ${a.status === 'done' ? 'text-slate-400 line-through' : 'text-white'}`}>
                    {a.label}
                  </p>
                  <p className="text-xs text-slate-400">{a.reason}</p>
                </div>
                {a.status !== 'done' && (
                  isStripe ? (
                    <Button
                      size="sm"
                      onClick={() => onOpenStripe && onOpenStripe(storeId)}
                      className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
                      data-testid={`owner-action-${a.key}-cta`}
                    >
                      <ExternalLink className="h-3 w-3 mr-1" /> Connect
                    </Button>
                  ) : a.cta_url ? (
                    <a
                      href={a.cta_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:text-blue-300 underline"
                      data-testid={`owner-action-${a.key}-cta`}
                    >
                      Open
                    </a>
                  ) : null
                )}
              </li>
            );
          })}
        </ul>
      </div>

      {/* ─── Financial transparency ────────────────────────────────── */}
      <div className="rounded-md border border-[#1E293B] bg-[#0B0F17] p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Wallet className="h-4 w-4 text-emerald-400" /> Financial summary
          </h3>
          <span className="text-[10px] text-slate-500 flex items-center gap-1">
            <ShieldCheck className="h-3 w-3" /> Owner view
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <FinanceTile label="Gross sales"           value={fmtUsd(finance.gross_sales)} testId={`owner-finance-gross-${storeId}`} />
          <FinanceTile label="Donations"             value={fmtUsd(finance.donations_collected)} muted />
          <FinanceTile label="Profit allocation"     value={fmtUsd(finance.profit_allocation)} muted />
          <FinanceTile label="Total raised"          value={fmtUsd(finance.fundraiser_total_raised)} muted />
          <FinanceTile label="Payout owed (to date)" value={fmtUsd(finance.payout_owed)} />
          <FinanceTile label="Payout paid"           value={fmtUsd(finance.payout_paid)} accent="emerald" />
          <FinanceTile label="Net pending payout"    value={fmtUsd(finance.net_pending_payout)} accent={finance.net_pending_payout > 0 ? 'amber' : 'slate'} testId={`owner-finance-net-${storeId}`} />
          <FinanceTile label="Total orders"          value={finance.total_orders} muted />
        </div>
        <p className="mt-3 text-xs text-slate-400 flex items-start gap-1.5">
          <Info className="h-3.5 w-3.5 mt-0.5 text-slate-500" />
          <span data-testid={`owner-finance-formula-${storeId}`}>{finance.formula}</span>
        </p>

        {/* Payout history */}
        <div className="mt-4">
          <h4 className="text-xs font-medium text-slate-300 mb-2">Payout history</h4>
          {(!payout_history || payout_history.length === 0) ? (
            <p className="text-xs text-slate-500" data-testid={`owner-payout-empty-${storeId}`}>
              No payouts yet. Once orders are paid and Stripe transfers are sent, they'll appear here.
            </p>
          ) : (
            <div className="border border-[#1E293B] rounded overflow-hidden">
              <table className="w-full text-xs" data-testid={`owner-payout-table-${storeId}`}>
                <thead className="bg-[#111826] text-slate-400">
                  <tr>
                    <th className="text-left px-2.5 py-1.5">Date</th>
                    <th className="text-left px-2.5 py-1.5">Order</th>
                    <th className="text-left px-2.5 py-1.5">Customer</th>
                    <th className="text-right px-2.5 py-1.5">Amount</th>
                    <th className="text-left px-2.5 py-1.5">Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {payout_history.map((p) => (
                    <tr key={p.id} className="border-t border-[#1E293B]">
                      <td className="px-2.5 py-1.5 text-slate-300">
                        {p.date ? new Date(p.date).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-2.5 py-1.5 text-slate-300">{p.order_number || p.id?.slice(0, 8)}</td>
                      <td className="px-2.5 py-1.5 text-slate-300">{p.customer_name || '—'}</td>
                      <td className="px-2.5 py-1.5 text-emerald-300 text-right font-medium">{fmtUsd(p.amount)}</td>
                      <td className="px-2.5 py-1.5 text-slate-500 font-mono text-[10px]">{(p.reference || '').slice(0, 14) || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Privacy banner */}
      <p className="text-[11px] text-slate-500 flex items-center gap-1.5">
        <ShieldCheck className="h-3 w-3" />
        {privacy_note}
      </p>
    </div>
  );
}

function FinanceTile({ label, value, accent, muted, testId }) {
  const colorByAccent = {
    emerald: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300',
    amber:   'border-amber-500/30 bg-amber-500/5 text-amber-300',
    slate:   'border-[#1E293B] bg-[#111826] text-white',
  };
  const cls = accent
    ? colorByAccent[accent]
    : muted
      ? 'border-[#1E293B] bg-[#111826] text-slate-300'
      : 'border-[#1E293B] bg-[#111826] text-white';
  return (
    <div className={`rounded p-2.5 border ${cls}`} data-testid={testId}>
      <p className="text-[10px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-0.5 text-sm font-semibold">{value}</p>
    </div>
  );
}
