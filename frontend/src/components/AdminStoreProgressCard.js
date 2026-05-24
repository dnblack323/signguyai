/**
 * Phase 6 — Admin-side selected-store progress card.
 *
 * Reuses the Phase 5 `_build_store_progress_payload` server-side so admin
 * and owner see identical lifecycle + finance numbers. Adds three admin-
 * only stage-stamp buttons (Production Started / Ready for Pickup /
 * Completed) that PATCH /api/webstores/v2/{id}/admin-progress.
 *
 * Light visual styling so this sits inside the existing white-card store
 * detail dialog without redesigning the shell.
 */
import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import {
  CheckCircle2, Circle, Clock, AlertTriangle, Wallet,
  ChevronRight, Info, Loader2, PlayCircle, Truck, CheckCheck, Undo2,
} from 'lucide-react';
import { Button } from './ui/button';
import { getAuthToken } from '../lib/authStorage';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const fmtUsd = (v) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
    Number(v || 0),
  );

const STATUS_PILL = {
  done:   { cls: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  active: { cls: 'bg-blue-50 text-blue-700 border-blue-200', icon: Clock },
  todo:   { cls: 'bg-gray-100 text-gray-500 border-gray-200', icon: Circle },
};

export default function AdminStoreProgressCard({ storeId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stamping, setStamping] = useState(null);

  const load = useCallback(async () => {
    if (!storeId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(
        `${API}/webstores/v2/${storeId}/admin-progress`,
        { headers: { Authorization: `Bearer ${getAuthToken()}` } },
      );
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load progress');
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => { load(); }, [load]);

  const stamp = async (flagKey, label) => {
    setStamping(flagKey);
    try {
      const res = await axios.patch(
        `${API}/webstores/v2/${storeId}/admin-progress`,
        { [flagKey]: true },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } },
      );
      setData(res.data);
      toast.success(`${label} stamped`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update');
    } finally {
      setStamping(null);
    }
  };

  const clearStamp = async (flagKey, label) => {
    setStamping(flagKey);
    try {
      const res = await axios.patch(
        `${API}/webstores/v2/${storeId}/admin-progress`,
        { [flagKey]: false },
        { headers: { Authorization: `Bearer ${getAuthToken()}` } },
      );
      setData(res.data);
      toast.success(`${label} cleared`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update');
    } finally {
      setStamping(null);
    }
  };

  if (loading) {
    return (
      <div className="rounded-md border p-4 bg-white text-center text-gray-500" data-testid={`admin-progress-loading-${storeId}`}>
        <Loader2 className="h-4 w-4 mx-auto animate-spin text-blue-600" />
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800" data-testid={`admin-progress-error-${storeId}`}>
        <AlertTriangle className="inline h-4 w-4 mr-1.5" />
        {error || 'Progress unavailable.'}
      </div>
    );
  }

  const { current_stage, stages, next_blocker, required_actions, finance } = data;
  const pct = Math.round((current_stage.index / Math.max(current_stage.total, 1)) * 100);

  const stagesByKey = Object.fromEntries(stages.map((s) => [s.key, s]));
  const productionDone = stagesByKey.production_started?.status === 'done';
  const pickupDone = stagesByKey.ready_for_pickup?.status === 'done';
  const completedDone = stagesByKey.completed?.status === 'done';
  const todoActions = required_actions.filter((a) => a.status !== 'done');

  return (
    <div className="space-y-4" data-testid={`admin-progress-card-${storeId}`}>
      {/* ── Lifecycle progress (top) ───────────────────────────────── */}
      <div className="rounded-md border bg-white p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-900">Lifecycle progress</h3>
          <span className="text-xs text-gray-500" data-testid={`admin-progress-current-${storeId}`}>
            {current_stage.index} / {current_stage.total} · {pct}%
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 rounded overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="mt-2 text-sm font-medium text-blue-700 flex items-center gap-1">
          <ChevronRight className="h-4 w-4" /> {current_stage.label}
        </p>
        {next_blocker && (
          <p className="mt-0.5 ml-5 text-xs text-gray-600">{next_blocker}</p>
        )}

        {/* Compact stages strip */}
        <div className="mt-3 flex flex-wrap gap-1.5">
          {stages.map((s) => {
            const Pill = STATUS_PILL[s.status] || STATUS_PILL.todo;
            const Icon = Pill.icon;
            return (
              <span
                key={s.key}
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] ${Pill.cls}`}
                title={s.label}
                data-testid={`admin-progress-stage-${s.key}-${s.status}`}
              >
                <Icon className="h-2.5 w-2.5" />
                {s.label}
              </span>
            );
          })}
        </div>
      </div>

      {/* ── Needs attention / owner actions still pending ─────────── */}
      {todoActions.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3" data-testid={`admin-needs-attention-${storeId}`}>
          <p className="text-xs font-semibold text-amber-900 flex items-center gap-1.5 mb-2">
            <AlertTriangle className="h-3.5 w-3.5" /> Needs attention · {todoActions.length} owner action{todoActions.length !== 1 ? 's' : ''} pending
          </p>
          <ul className="space-y-1">
            {todoActions.slice(0, 4).map((a) => (
              <li key={a.key} className="text-xs text-amber-800 flex items-start gap-1.5" data-testid={`admin-needs-${a.key}`}>
                <Circle className="h-3 w-3 mt-0.5 text-amber-500 shrink-0" />
                <div>
                  <span className="font-medium">{a.label}.</span> {a.reason}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Admin stage-stamp controls ───────────────────────────── */}
      <div className="rounded-md border bg-white p-3" data-testid={`admin-stage-controls-${storeId}`}>
        <p className="text-xs font-semibold text-gray-700 mb-2">Stage controls</p>
        <div className="flex flex-wrap gap-2">
          {!productionDone ? (
            <Button
              size="sm" variant="outline"
              onClick={() => stamp('mark_production_started', 'Production started')}
              disabled={stamping === 'mark_production_started'}
              data-testid={`admin-stamp-production-${storeId}`}
            >
              {stamping === 'mark_production_started' ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <PlayCircle className="h-3 w-3 mr-1" />}
              Mark production started
            </Button>
          ) : (
            <Button
              size="sm" variant="ghost" className="text-emerald-700"
              onClick={() => clearStamp('mark_production_started', 'Production')}
              disabled={stamping === 'mark_production_started'}
              data-testid={`admin-unstamp-production-${storeId}`}
            >
              <CheckCircle2 className="h-3 w-3 mr-1" /> Production stamped
              <Undo2 className="h-3 w-3 ml-1.5 opacity-50" />
            </Button>
          )}
          {!pickupDone ? (
            <Button
              size="sm" variant="outline"
              onClick={() => stamp('mark_ready_for_pickup', 'Ready for pickup')}
              disabled={stamping === 'mark_ready_for_pickup'}
              data-testid={`admin-stamp-pickup-${storeId}`}
            >
              {stamping === 'mark_ready_for_pickup' ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Truck className="h-3 w-3 mr-1" />}
              Mark ready for pickup
            </Button>
          ) : (
            <Button
              size="sm" variant="ghost" className="text-emerald-700"
              onClick={() => clearStamp('mark_ready_for_pickup', 'Pickup')}
              disabled={stamping === 'mark_ready_for_pickup'}
              data-testid={`admin-unstamp-pickup-${storeId}`}
            >
              <CheckCircle2 className="h-3 w-3 mr-1" /> Pickup stamped
              <Undo2 className="h-3 w-3 ml-1.5 opacity-50" />
            </Button>
          )}
          {!completedDone ? (
            <Button
              size="sm" variant="outline"
              onClick={() => stamp('mark_completed', 'Completed')}
              disabled={stamping === 'mark_completed'}
              data-testid={`admin-stamp-completed-${storeId}`}
            >
              {stamping === 'mark_completed' ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <CheckCheck className="h-3 w-3 mr-1" />}
              Mark completed
            </Button>
          ) : (
            <Button
              size="sm" variant="ghost" className="text-emerald-700"
              onClick={() => clearStamp('mark_completed', 'Completed')}
              disabled={stamping === 'mark_completed'}
              data-testid={`admin-unstamp-completed-${storeId}`}
            >
              <CheckCircle2 className="h-3 w-3 mr-1" /> Marked completed
              <Undo2 className="h-3 w-3 ml-1.5 opacity-50" />
            </Button>
          )}
        </div>
        <p className="mt-2 text-[10px] text-gray-500">
          Stamps are additive timestamps only — the owner-visible lifecycle bar updates automatically.
        </p>
      </div>

      {/* ── Compact finance summary ──────────────────────────────── */}
      <div className="rounded-md border bg-white p-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
            <Wallet className="h-3.5 w-3.5 text-emerald-600" /> Money summary
          </h3>
          <span className="text-[10px] text-gray-400">{finance.total_orders} orders</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          <Tile label="Gross sales" value={fmtUsd(finance.gross_sales)} />
          <Tile label="Donations"   value={fmtUsd(finance.donations_collected)} muted />
          <Tile label="Owner owed"  value={fmtUsd(finance.payout_owed)} accent="amber" />
          <Tile label="Owner paid"  value={fmtUsd(finance.payout_paid)} accent="emerald" />
        </div>
        <p className="mt-2 text-[10px] text-gray-500 flex items-start gap-1">
          <Info className="h-3 w-3 mt-0.5" />
          {finance.formula}
        </p>
      </div>
    </div>
  );
}

function Tile({ label, value, accent, muted }) {
  const map = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    amber:   'border-amber-200 bg-amber-50 text-amber-700',
  };
  const cls = accent
    ? map[accent]
    : muted
      ? 'border-gray-200 bg-gray-50 text-gray-600'
      : 'border-gray-200 bg-white text-gray-900';
  return (
    <div className={`rounded p-2 border ${cls}`}>
      <p className="text-[10px] uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold">{value}</p>
    </div>
  );
}
