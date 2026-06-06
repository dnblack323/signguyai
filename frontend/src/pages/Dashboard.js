import { useEffect, useState, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { formatCurrency, formatDate } from '../lib/utils';
import {
  Users, FileText, Briefcase, Receipt, TrendingUp,
  AlertTriangle, Plus, ArrowRight, Clock, MessageSquare,
  CheckCircle, Calendar, UserCheck, Coffee, Sun, Sunset, Moon,
  ChevronRight, Eye, Sparkles, Download, Send, ExternalLink,
  BarChart2, DollarSign, TrendingDown, Package, Layers,
  RefreshCw, XCircle, Zap, Inbox
} from 'lucide-react';
import { Link } from 'react-router-dom';
import InvoicePreviewModal from '../components/InvoicePreviewModal';
import OnboardingChecklist from '../components/OnboardingChecklist';
import AssistantNudgesWidget from '../components/AssistantNudgesWidget';
import PendingCustomerActionsWidget from '../components/dashboard/PendingCustomerActionsWidget';
import { FoundersBadge } from '../components/founders';
import axios from 'axios';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// ─────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────
const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return { text: 'Good morning', icon: Sun, color: 'text-amber-500' };
  if (hour < 17) return { text: 'Good afternoon', icon: Sunset, color: 'text-orange-500' };
  return { text: 'Good evening', icon: Moon, color: 'text-indigo-400' };
};

// Returns freshness metadata: text to display + flags for stale/missing
const getFreshness = (isoStr) => {
  if (!isoStr) return { text: 'Last updated unavailable.', isStale: false, isMissing: true };
  try {
    const dt = new Date(isoStr);
    const ageMinutes = (Date.now() - dt.getTime()) / 60000;
    const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return {
      text: `Last updated at ${timeStr}`,
      isStale: ageMinutes > 10,
      isMissing: false,
    };
  } catch {
    return { text: 'Last updated unavailable.', isStale: false, isMissing: true };
  }
};

// Kept for backward-compat with plain text usages
const formatLastUpdated = (isoStr) => getFreshness(isoStr).text;

// Convert raw hours (from backend) into a human-readable age string
// < 24h → "18h"   |   1–9.9 days → "3.5d"   |   ≥ 10 days → "15d"
const formatAge = (hours) => {
  if (hours == null || hours === undefined) return null;
  if (hours < 24) return `${Math.round(hours)}h`;
  const days = hours / 24;
  return days < 10 ? `${days.toFixed(1)}d` : `${Math.round(days)}d`;
};

// ─── Sorting helpers ─────────────────────────────────────────────────────────

// At-risk priority: blocked first, then overdue, then due_24h_not_started
const AT_RISK_PRIORITY = { blocked: 0, overdue: 1, due_within_24h_not_started: 2 };
const sortAtRisk = (items) =>
  [...items].sort((a, b) => {
    const pa = AT_RISK_PRIORITY[a.reason] ?? 9;
    const pb = AT_RISK_PRIORITY[b.reason] ?? 9;
    if (pa !== pb) return pa - pb;
    // Within same priority: earliest due_at first
    return (a.due_at || '').localeCompare(b.due_at || '');
  });

// Customer attention lists: urgency_score desc, then timestamp desc
const sortByUrgency = (items, tsField = 'requested_at') =>
  [...items].sort((a, b) => {
    if (b.urgency_score !== a.urgency_score) return b.urgency_score - a.urgency_score;
    return (b[tsField] || '').localeCompare(a[tsField] || '');
  });

const getSeverityStyles = (severity) => {
  if (severity === 'red')   return { badge: 'bg-red-500/25 text-red-200 border border-red-500/50',   dot: '#EF4444' };
  if (severity === 'amber') return { badge: 'bg-amber-500/25 text-amber-200 border border-amber-500/50', dot: '#F59E0B' };
  return { badge: 'bg-slate-600/40 text-slate-300 border border-slate-500/40', dot: '#9CA3AF' };
};

// ─────────────────────────────────────────────
// StatCard — unchanged
// ─────────────────────────────────────────────
const StatCard = ({ title, value, icon: Icon, subtitle, href, accentColor = 'var(--accent)' }) => (
  <div
    className="rounded-xl p-4 sm:p-6 transition-all duration-200 hover:shadow-md group"
    style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}
  >
    <div className="flex items-start justify-between">
      <div className="space-y-1 sm:space-y-2 flex-1 min-w-0">
        <p className="text-xs sm:text-sm font-medium truncate" style={{ color: 'var(--text-muted)' }}>{title}</p>
        <p className="text-2xl sm:text-3xl font-bold font-heading tracking-tight" style={{ color: 'var(--text)' }}>{value}</p>
        {subtitle && <p className="text-xs hidden sm:block" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>}
      </div>
      <div className="p-2 sm:p-3 rounded-lg transition-transform group-hover:scale-110 flex-shrink-0 ml-2" style={{ backgroundColor: `${accentColor}15` }}>
        <Icon className="h-5 w-5 sm:h-6 sm:w-6" style={{ color: accentColor }} />
      </div>
    </div>
    {href && (
      <Link to={href}>
        <button className="mt-3 sm:mt-4 flex items-center text-xs sm:text-sm font-medium hover:opacity-80 transition-opacity" style={{ color: accentColor }}>
          View all <ArrowRight className="ml-1 h-3 w-3 sm:h-4 sm:w-4" />
        </button>
      </Link>
    )}
  </div>
);

const getStatusBadgeStyles = (status) => {
  const styles = {
    quoted: { backgroundColor: '#2F8BFB', color: '#FFFFFF' },
    in_production: { backgroundColor: '#F59E0B', color: '#000000' },
    printing: { backgroundColor: '#F59E0B', color: '#000000' },
    finishing: { backgroundColor: '#8B5CF6', color: '#FFFFFF' },
    complete: { backgroundColor: '#22C55E', color: '#FFFFFF' },
    delivered: { backgroundColor: '#22C55E', color: '#FFFFFF' },
    overdue: { backgroundColor: '#EF4444', color: '#FFFFFF' },
    paid: { backgroundColor: '#22C55E', color: '#FFFFFF' },
    sent: { backgroundColor: '#8B5CF6', color: '#FFFFFF' },
    draft: { backgroundColor: '#6B7280', color: '#FFFFFF' },
    working: { backgroundColor: '#22C55E', color: '#FFFFFF' },
    on_break: { backgroundColor: '#F59E0B', color: '#000000' },
    urgent: { backgroundColor: '#EF4444', color: '#FFFFFF' },
    rush: { backgroundColor: '#EF4444', color: '#FFFFFF' },
    pending: { backgroundColor: '#F59E0B', color: '#000000' },
    approved: { backgroundColor: '#2F8BFB', color: '#FFFFFF' },
    queued: { backgroundColor: '#6B7280', color: '#FFFFFF' },
  };
  return styles[status] || styles.draft;
};

// ─────────────────────────────────────────────
// Shared card shell
// ─────────────────────────────────────────────
const CardShell = ({ icon: Icon, iconColor = 'text-blue-500', title, badge, lastUpdatedAt, children, headerRight }) => {
  const freshness = lastUpdatedAt !== undefined ? getFreshness(lastUpdatedAt) : null;
  const showStale   = freshness?.isStale;
  const showMissing = freshness?.isMissing;

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Icon className={`h-4 w-4 flex-shrink-0 ${iconColor}`} />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</h2>
          {badge && <span className="flex-shrink-0">{badge}</span>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          {freshness && (showStale || showMissing) && (
            <span
              className="text-xs text-amber-400"
              title={showStale ? 'Data may be stale — loaded more than 10 minutes ago.' : undefined}
              data-testid={showStale ? 'stale-indicator' : showMissing ? 'missing-ts-indicator' : undefined}
            >
              {showStale ? '⚠ Stale' : 'No timestamp'}
            </span>
          )}
          {headerRight}
        </div>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
};

// Visible, actionable error block — never falls through to empty state
const ErrorState = ({ onRetry }) => (
  <div
    className="rounded-lg p-4"
    style={{ backgroundColor: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.25)' }}
    data-testid="section-error"
  >
    <div className="flex items-start gap-3">
      <XCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>Couldn&apos;t load this section.</p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>Please retry.</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2.5 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium transition-all hover:opacity-80"
            style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
            data-testid="section-error-retry"
          >
            <RefreshCw className="h-3 w-3" /> Retry
          </button>
        )}
      </div>
    </div>
  </div>
);

const LoadingSpinner = () => (
  <div className="flex justify-center py-5">
    <div className="animate-spin rounded-full h-5 w-5 border-b-2" style={{ borderColor: 'var(--accent)' }} />
  </div>
);

// ─────────────────────────────────────────────
// Row 1 — Severity Strip (summary-v2)
// ─────────────────────────────────────────────
const STRIP_METRICS = [
  { key: 'due_today',         label: 'Due Today',       icon: Clock,         href: '/orders'                       },
  { key: 'overdue',           label: 'Overdue',          icon: AlertTriangle, href: '/orders'                       },
  { key: 'awaiting_approval', label: 'Needs Approval',   icon: Eye,           href: '/approvals'                    },
  { key: 'in_production',     label: 'In Production',    icon: Package,       href: '/orders'                       },
  { key: 'unpaid_invoices',   label: 'Unpaid Invoices',  icon: Receipt,       href: '/invoices'                     },
];

const SeverityStripWidget = ({ data, loading, error, onRetry }) => {
  if (loading) return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
      {STRIP_METRICS.map(m => (
        <div key={m.key} className="h-28 rounded-xl animate-pulse" style={{ backgroundColor: 'var(--surface)' }} />
      ))}
    </div>
  );

  if (error) return (
    <div className="rounded-xl p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <ErrorState onRetry={onRetry} />
    </div>
  );

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3" data-testid="severity-strip">
      {STRIP_METRICS.map(({ key, label, icon: Icon, href }) => {
        const metric = data?.metrics?.[key] || { count: 0, severity: 'neutral' };
        const isOverdue   = key === 'overdue'   && metric.count > 0;
        const isRedUrgent = metric.severity === 'red'   && metric.count > 0;
        const isAmber     = metric.severity === 'amber' && metric.count > 0;

        let cardBg, cardBorder, countColor, iconColor;
        if (isOverdue) {
          cardBg     = 'rgba(239,68,68,0.14)';
          cardBorder = 'rgba(239,68,68,0.55)';
          countColor = '#FCA5A5';
          iconColor  = '#EF4444';
        } else if (isRedUrgent) {
          cardBg     = 'rgba(239,68,68,0.08)';
          cardBorder = 'rgba(239,68,68,0.35)';
          countColor = '#FCA5A5';
          iconColor  = '#EF4444';
        } else if (isAmber) {
          cardBg     = 'rgba(245,158,11,0.10)';
          cardBorder = 'rgba(245,158,11,0.40)';
          countColor = '#FCD34D';
          iconColor  = '#F59E0B';
        } else {
          cardBg     = 'var(--surface)';
          cardBorder = 'var(--border-light)';
          countColor = 'var(--text)';
          iconColor  = 'var(--text-muted)';
        }

        return (
          <Link key={key} to={href} data-testid={`severity-${key}`}>
            <div
              className="rounded-xl px-4 py-4 flex flex-col gap-2 transition-all hover:shadow-md hover:translate-y-[-1px]"
              style={{ backgroundColor: cardBg, border: `1px solid ${cardBorder}` }}
            >
              <Icon className="h-4 w-4 flex-shrink-0" style={{ color: iconColor }} />
              <span className="text-3xl font-bold font-heading leading-none" style={{ color: countColor }}>
                {metric.count}
              </span>
              <p className="text-xs font-medium leading-tight" style={{ color: 'var(--text)' }}>{label}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
};

// ─────────────────────────────────────────────
// Row 2 — Today Command Center widgets
// ─────────────────────────────────────────────

// Due Order Items Today
const ScheduleWidget = ({ items = [], lastUpdatedAt, loading, error, onRetry }) => {
  const badge = items.length > 0 && (
    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-medium border border-purple-500/40">{items.length}</span>
  );
  return (
    <CardShell
      icon={Calendar}
      iconColor="text-purple-500"
      title="Due Today"
      badge={badge}
      lastUpdatedAt={lastUpdatedAt}
      headerRight={
        <Link to="/orders">
          <span className="text-xs text-blue-400 hover:underline">View all orders</span>
        </Link>
      }
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : items.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No order items due today.</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {items.slice(0, 5).map(item => (
            <Link key={item.order_item_id} to={item.order_id ? `/orders/${item.order_id}` : '/orders'} data-testid={`schedule-item-${item.order_item_id}`}>
              <div
                className="flex items-center justify-between p-2.5 rounded-lg transition-all duration-150 hover:shadow-sm cursor-pointer"
                style={{
                  backgroundColor: item.priority === 'urgent' || item.priority === 'rush' ? 'var(--danger-soft)' : 'var(--surface-2)',
                  border: item.priority === 'urgent' || item.priority === 'rush' ? '1px solid var(--danger)' : '1px solid transparent',
                }}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{item.item_name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.customer_name}</p>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                  {(item.priority === 'urgent' || item.priority === 'rush') && <AlertTriangle className="h-3.5 w-3.5 text-red-400" />}
                  <span className="px-1.5 py-0.5 rounded-full text-xs font-medium" style={getStatusBadgeStyles(item.stage)}>
                    {item.stage}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </CardShell>
  );
};

// Appointments / Installs Today
const AppointmentsWidget = ({ items = [], lastUpdatedAt, loading, error, onRetry }) => {
  return (
    <CardShell
      icon={Calendar}
      iconColor="text-blue-400"
      title="Appointments Today"
      lastUpdatedAt={lastUpdatedAt}
      headerRight={
        <Link to="/productivity?view=calendar">
          <span className="text-xs text-blue-400 hover:underline">Calendar</span>
        </Link>
      }
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : items.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No appointments scheduled today.</p>
          <Link to="/productivity?view=calendar">
            <Button size="sm" variant="outline" className="mt-2 text-xs">
              <Calendar className="h-3 w-3 mr-1" /> Open Calendar
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-1.5">
          {items.slice(0, 4).map(appt => (
            <div
              key={appt.appointment_id}
              className="flex items-center justify-between p-2.5 rounded-lg"
              style={{ backgroundColor: 'var(--surface-2)' }}
              data-testid={`appt-${appt.appointment_id}`}
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{appt.title}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {appt.customer_name}
                  {appt.start_at && ` · ${new Date(appt.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                </p>
              </div>
              <span className="px-1.5 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ml-2" style={getStatusBadgeStyles(appt.status)}>
                {appt.type?.replace('_', ' ') || 'appt'}
              </span>
            </div>
          ))}
        </div>
      )}
    </CardShell>
  );
};

// Team Status Today — unchanged data structure, updated empty state
const TeamStatusWidget = ({ teamStatus, lastUpdatedAt, loading, error, onRetry }) => {
  const scheduled = (teamStatus?.employees || []).filter(e => e.is_scheduled);
  const unscheduledClockedIn = (teamStatus?.employees || []).filter(e => !e.is_scheduled && e.clock_status !== 'not_clocked_in');

  const getStatusIcon = (status) => {
    if (status === 'working') return <UserCheck className="h-4 w-4 text-emerald-500" />;
    if (status === 'on_break') return <Coffee className="h-4 w-4 text-amber-500" />;
    if (status === 'finished') return <Clock className="h-4 w-4 text-blue-400" />;
    return <Clock className="h-4 w-4 text-gray-400" />;
  };
  const getStatusLabel = (s) => ({ working: 'Clocked In', on_break: 'On Break', finished: 'Finished' }[s] || 'Not In');
  const getStatusBadge = (s) => ({
    working: { backgroundColor: '#22C55E', color: '#FFFFFF' },
    on_break: { backgroundColor: '#F59E0B', color: '#000000' },
    finished: { backgroundColor: '#6B7280', color: '#FFFFFF' },
  }[s] || { backgroundColor: '#EF444433', color: '#EF4444' });

  const badge = (
    <div className="flex items-center gap-1.5 ml-1">
      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium border border-emerald-500/40" data-testid="team-clocked-in-count">
        {teamStatus?.clocked_in_count || 0} in
      </span>
      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium border border-blue-500/40" data-testid="team-scheduled-count">
        {teamStatus?.scheduled_count || 0} sched
      </span>
    </div>
  );

  return (
    <CardShell
      icon={Users}
      iconColor="text-emerald-500"
      title="Team Status"
      badge={badge}
      lastUpdatedAt={lastUpdatedAt}
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : (
        <>
          {scheduled.length > 0 && (
            <div className="mb-2">
              <p className="text-xs font-medium uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>Scheduled Today</p>
              <div className="space-y-1.5">
                {scheduled.map(emp => (
                  <div key={emp.employee_id} className="flex items-center justify-between p-2.5 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }} data-testid={`team-status-${emp.employee_id}`}>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: emp.clock_status === 'working' ? 'rgba(34,197,94,0.15)' : emp.clock_status === 'on_break' ? 'rgba(245,158,11,0.15)' : 'rgba(107,114,128,0.1)' }}>
                        {getStatusIcon(emp.clock_status)}
                      </div>
                      <div>
                        <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>{emp.employee_name}</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {emp.shift_start && emp.shift_end ? `${emp.shift_start}–${emp.shift_end}` : 'Scheduled'}
                          {emp.clocked_in_at && ` · in ${new Date(emp.clocked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                        </p>
                      </div>
                    </div>
                    <span className="px-1.5 py-0.5 rounded-full text-xs font-medium" style={getStatusBadge(emp.clock_status)}>{getStatusLabel(emp.clock_status)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {unscheduledClockedIn.length > 0 && (
            <div className="mb-2">
              <p className="text-xs font-medium uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>Clocked In (Unscheduled)</p>
              <div className="space-y-1.5">
                {unscheduledClockedIn.map(emp => (
                  <div key={emp.employee_id} className="flex items-center justify-between p-2.5 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }} data-testid={`team-status-unscheduled-${emp.employee_id}`}>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(34,197,94,0.15)' }}>
                        {getStatusIcon(emp.clock_status)}
                      </div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>{emp.employee_name}</p>
                    </div>
                    <span className="px-1.5 py-0.5 rounded-full text-xs font-medium" style={getStatusBadge(emp.clock_status)}>{getStatusLabel(emp.clock_status)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {scheduled.length === 0 && unscheduledClockedIn.length === 0 && (
            <div className="text-center py-3">
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No team schedule for today. Set schedule.</p>
              <Link to="/payroll?tab=schedule">
                <Button size="sm" variant="outline" className="mt-2 text-xs">
                  <Calendar className="h-3 w-3 mr-1" /> Set Schedule
                </Button>
              </Link>
            </div>
          )}
          {(scheduled.length > 0 || unscheduledClockedIn.length > 0) && (
            <div className="flex items-center justify-between pt-2 mt-1" style={{ borderTop: '1px solid var(--border-light)' }}>
              <Link to="/payroll?tab=schedule">
                <span className="text-xs text-blue-400 hover:underline flex items-center gap-1"><Calendar className="h-3 w-3" /> Schedule</span>
              </Link>
              <Link to="/timeclock">
                <span className="text-xs text-blue-400 hover:underline flex items-center gap-1"><Clock className="h-3 w-3" /> Time Clock</span>
              </Link>
            </div>
          )}
        </>
      )}
    </CardShell>
  );
};

// ─────────────────────────────────────────────
// Row 3 — Production Pipeline
// ─────────────────────────────────────────────
const STAGE_COLORS = {
  queued:    { bg: 'bg-slate-600/40',   text: 'text-slate-200',   border: 'border-slate-500/50',   label: 'Queued'    },
  printing:  { bg: 'bg-amber-500/30',   text: 'text-amber-200',   border: 'border-amber-500/50',   label: 'Printing'  },
  finishing: { bg: 'bg-purple-500/30',  text: 'text-purple-200',  border: 'border-purple-500/50',  label: 'Finishing' },
  install:   { bg: 'bg-blue-500/30',    text: 'text-blue-200',    border: 'border-blue-500/50',    label: 'Install'   },
  complete:  { bg: 'bg-emerald-500/30', text: 'text-emerald-200', border: 'border-emerald-500/50', label: 'Completed' },
};

const ProductionSnapshotWidget = ({ data, loading, error, onRetry }) => {
  const stages      = data?.order_items_by_stage || {};
  const atRisk      = sortAtRisk(data?.at_risk || []);
  const bottlenecks = data?.bottlenecks || [];

  // Build oldest-age lookup from bottlenecks: stage → hours
  const ageByStage = {};
  bottlenecks.forEach(b => { if (b.stage) ageByStage[b.stage] = b.oldest_item_age_hours; });

  const freshness = data?.last_updated_at !== undefined ? getFreshness(data?.last_updated_at) : null;

  const _reasonLabel = (r) => ({
    overdue:                    'Overdue',
    due_within_24h_not_started: 'Due Soon',
    blocked:                    'Blocked',
  }[r] || r);

  const _reasonBadge = (r) => ({
    overdue:                    { bg: 'rgba(239,68,68,0.20)',   color: '#FCA5A5', border: 'rgba(239,68,68,0.40)'    },
    due_within_24h_not_started: { bg: 'rgba(245,158,11,0.20)', color: '#FCD34D', border: 'rgba(245,158,11,0.40)'  },
    blocked:                    { bg: 'rgba(107,114,128,0.25)', color: '#D1D5DB', border: 'rgba(107,114,128,0.40)' },
  }[r] || { bg: 'rgba(107,114,128,0.25)', color: '#D1D5DB', border: 'rgba(107,114,128,0.40)' });

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-blue-400" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Production Pipeline</h2>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {freshness && (freshness.isStale || freshness.isMissing) && (
            <span
              className="text-xs text-amber-400"
              data-testid={freshness.isStale ? 'stale-indicator' : freshness.isMissing ? 'missing-ts-indicator' : undefined}
            >
              {freshness.isStale ? '⚠ Stale' : 'No timestamp'}
            </span>
          )}
          <Link to="/production-board" data-testid="production-board-link">
            <span className="text-xs text-blue-400 hover:underline">Production Board</span>
          </Link>
        </div>
      </div>
      {loading ? <div className="p-4"><LoadingSpinner /></div> : error ? <div className="p-4"><ErrorState onRetry={onRetry} /></div> : (
        <div className="p-4 space-y-5">
          {/* Stage strip */}
          <div className="grid grid-cols-5 gap-2" data-testid="production-stages">
            {Object.entries(STAGE_COLORS).map(([key, style]) => {
              const ageStr = ageByStage[key] != null ? formatAge(ageByStage[key]) : null;
              return (
                <div key={key} className={`flex flex-col items-center gap-1 p-3 rounded-lg border ${style.bg} ${style.border}`}>
                  <span className={`text-2xl font-bold font-heading ${style.text}`}>{stages[key] ?? 0}</span>
                  <span className={`text-xs font-semibold ${style.text}`}>{style.label}</span>
                  {ageStr && (
                    <span className={`text-[10px] opacity-75 ${style.text}`}>{ageStr} oldest</span>
                  )}
                </div>
              );
            })}
          </div>
          {/* At risk + Bottlenecks */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* At Risk */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider mb-2.5" style={{ color: 'var(--text-muted)' }}>At Risk</p>
              {atRisk.length === 0 ? (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No items at risk right now.</p>
              ) : (
                <div className="space-y-1.5">
                  {atRisk.slice(0, 5).map(item => {
                    const bdg       = _reasonBadge(item.reason);
                    const isOverdue = item.reason === 'overdue';
                    return (
                      <Link key={item.order_item_id} to={item.order_id ? `/orders/${item.order_id}` : '/orders'} data-testid={`at-risk-${item.order_item_id}`}>
                        <div
                          className="flex items-center justify-between px-3 py-2 rounded-lg hover:opacity-90 transition-opacity"
                          style={{
                            backgroundColor: isOverdue ? 'rgba(239,68,68,0.10)' : 'var(--surface-2)',
                            borderLeft:      isOverdue ? '3px solid rgba(239,68,68,0.65)' : '3px solid transparent',
                          }}
                        >
                          <div className="flex-1 min-w-0 mr-2">
                            <p className="text-xs font-medium truncate" style={{ color: 'var(--text)' }}>
                              {item.item_name || item.order_number || 'Unnamed item'}
                            </p>
                            {item.order_number && item.item_name && (
                              <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{item.order_number}</p>
                            )}
                          </div>
                          <span
                            className="flex-shrink-0 px-2 py-0.5 rounded-md text-[10px] font-semibold border"
                            style={{ backgroundColor: bdg.bg, color: bdg.color, borderColor: bdg.border }}
                          >
                            {_reasonLabel(item.reason)}
                          </span>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
            {/* Bottlenecks */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider mb-2.5" style={{ color: 'var(--text-muted)' }}>Bottlenecks</p>
              {bottlenecks.length === 0 ? (
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No bottlenecks right now.</p>
              ) : (
                <div className="space-y-1.5">
                  {bottlenecks.slice(0, 4).map(b => {
                    const ageStr    = formatAge(b.oldest_item_age_hours);
                    const stageLabel = STAGE_COLORS[b.stage]?.label || b.stage;
                    return (
                      <div key={b.stage} className="flex items-center justify-between px-3 py-2.5 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }}>
                        <div className="min-w-0">
                          <p className="text-xs font-semibold" style={{ color: 'var(--text)' }}>{stageLabel}</p>
                          {ageStr && <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{ageStr} oldest</p>}
                        </div>
                        <div className="text-right flex-shrink-0 ml-2">
                          <span className="text-lg font-bold" style={{ color: 'var(--text)' }}>{b.backlog_count}</span>
                          <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>items</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// Row 4 — Customer Attention widgets
// ─────────────────────────────────────────────

// Unread Messages — clickable rows
const MessagesWidget = ({ data, loading, error, onRetry }) => {
  // Frontend-sort: urgency_score desc, then last_message_at desc
  const messages = sortByUrgency(data?.unread_conversations || [], 'last_message_at');
  const totalUnread = messages.reduce((sum, m) => sum + (m.unread_count || 0), 0);

  const badge = messages.length > 0 && (
    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium border border-blue-500/40">{totalUnread} unread</span>
  );

  return (
    <CardShell
      icon={MessageSquare}
      iconColor="text-blue-500"
      title="Messages"
      badge={messages.length === 0 ? <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">Inbox zero</span> : badge}
      lastUpdatedAt={data?.last_updated_at}
      headerRight={
        <Link to="/admin-portal?tab=messages">
          <span className="text-xs text-blue-400 hover:underline">All messages</span>
        </Link>
      }
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : messages.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No unread customer messages.</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {messages.slice(0, 3).map(msg => (
            <Link key={msg.conversation_id} to="/admin-portal?tab=messages" data-testid={`message-row-${msg.conversation_id}`}>
              <div className="flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all duration-150 hover:shadow-sm" style={{ backgroundColor: 'var(--surface-2)' }}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{msg.customer_name}</p>
                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
                      {msg.unread_count}
                    </span>
                  </div>
                  <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{msg.last_message_preview}</p>
                </div>
                <ChevronRight className="h-3.5 w-3.5 ml-2 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </CardShell>
  );
};

// Pending Approvals & Signatures — links to /approvals
const PendingApprovalsWidget = ({ data, loading, error, onRetry }) => {
  // Frontend-sort: urgency_score desc, then requested_at desc
  const approvals = sortByUrgency(data?.approvals_signatures_pending || [], 'requested_at');
  const badge = approvals.length > 0
    ? <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/25 text-amber-200 font-medium border border-amber-500/40">{approvals.length} pending</span>
    : <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">All clear</span>;

  return (
    <CardShell
      icon={approvals.length > 0 ? Eye : CheckCircle}
      iconColor={approvals.length > 0 ? 'text-amber-500' : 'text-emerald-500'}
      title="Pending Approvals"
      badge={badge}
      lastUpdatedAt={data?.last_updated_at}
      headerRight={
        <Link to="/approvals">
          <span className="text-xs text-blue-400 hover:underline">All approvals</span>
        </Link>
      }
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : approvals.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No approvals pending. Send a new proof.</p>
          <Link to="/approvals">
            <Button size="sm" variant="outline" className="mt-2 text-xs">
              <Send className="h-3 w-3 mr-1" /> Send Proof
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-1.5">
          {approvals.slice(0, 4).map(item => (
            <Link key={item.record_id} to="/approvals" data-testid={`approval-${item.record_id}`}>
              <div className="flex items-center justify-between p-2.5 rounded-lg transition-all duration-150 hover:shadow-sm cursor-pointer" style={{ backgroundColor: 'var(--surface-2)', border: '1px solid transparent' }}>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{item.order_number || item.customer_name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {item.customer_name} · {item.type} · {item.age_hours < 1 ? '<1h' : `${Math.round(item.age_hours)}h`} ago
                  </p>
                </div>
                <ChevronRight className="h-3.5 w-3.5 ml-2 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </CardShell>
  );
};

// Quote Follow-Ups
const QuoteFollowupsWidget = ({ data, loading, error, onRetry }) => {
  // Frontend-sort: urgency_score desc, then last_sent_at desc
  const quotes = sortByUrgency(data?.quote_followups || [], 'last_sent_at');
  const badge = quotes.length > 0 && (
    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-medium border border-purple-500/40">{quotes.length}</span>
  );

  return (
    <CardShell
      icon={Send}
      iconColor="text-purple-500"
      title="Quote Follow-Ups"
      badge={badge}
      lastUpdatedAt={data?.last_updated_at}
      headerRight={
        <Link to="/orders?filter=quote_sent">
          <span className="text-xs text-blue-400 hover:underline">All quotes</span>
        </Link>
      }
    >
      {loading ? <LoadingSpinner /> : error ? <ErrorState onRetry={onRetry} /> : quotes.length === 0 ? (
        <div className="text-center py-3">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No pending quote follow-ups.</p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {quotes.slice(0, 4).map(q => (
            <div key={q.quote_id} className="flex items-center justify-between p-2.5 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }} data-testid={`quote-followup-${q.quote_id}`}>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{q.customer_name}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  {formatCurrency(q.quote_total)} · {Math.round(q.age_days)}d old
                </p>
              </div>
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/25 text-amber-200 font-medium border border-amber-500/40 flex-shrink-0 ml-2">
                {Math.round(q.age_days)}d
              </span>
            </div>
          ))}
        </div>
      )}
    </CardShell>
  );
};

// ─────────────────────────────────────────────
// ACTION REQUIRED — shared sub-components
// ─────────────────────────────────────────────
const SectionLabel = ({ icon: Icon, iconColor, label, badge, right }) => (
  <div className="flex items-center justify-between mb-2">
    <div className="flex items-center gap-2">
      <Icon className={`h-3.5 w-3.5 ${iconColor}`} />
      <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{label}</span>
      {badge}
    </div>
    {right}
  </div>
);

const ActionEmptyRow = ({ text }) => (
  <div className="flex items-center gap-2 py-1 pl-1">
    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0" />
    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{text}</p>
  </div>
);

const SectionDivider = () => <div style={{ borderTop: '1px solid var(--border-light)' }} />;

// ─────────────────────────────────────────────
// ACTION REQUIRED — consolidated vertical-list card
// Sections: Customer Approvals · Messages · Quote Follow-Ups ·
//           Invoices & Payments · Customer Actions
// ─────────────────────────────────────────────

const ActionRequiredCard = ({ data, loading, error, onRetry, summaryData }) => {
  const messages    = sortByUrgency(data?.unread_conversations || [], 'last_message_at');
  const approvals   = sortByUrgency(data?.approvals_signatures_pending || [], 'requested_at');
  const quotes      = sortByUrgency(data?.quote_followups || [], 'last_sent_at');
  const totalUnread = messages.reduce((sum, m) => sum + (m.unread_count || 0), 0);
  const overdueCount = summaryData?.metrics?.overdue?.count || 0;
  const unpaidCount  = summaryData?.metrics?.unpaid_invoices?.count || 0;
  const totalActions = approvals.length + totalUnread + quotes.length + overdueCount;

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      {/* Card header */}
      <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-400" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Action Required</h2>
          {!loading && !error && totalActions > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-medium border border-amber-500/40" data-testid="action-required-total">
              {totalActions}
            </span>
          )}
        </div>
        {loading && <div className="h-3 w-3 rounded-full border-2 border-t-transparent border-blue-400 animate-spin" />}
      </div>

      {loading ? (
        <div className="p-4"><LoadingSpinner /></div>
      ) : error ? (
        <div className="p-4"><ErrorState onRetry={onRetry} /></div>
      ) : (
        <>
          {/* ── 1. Customer Approvals ── */}
          <div className="p-4">
            <SectionLabel
              icon={Eye} iconColor="text-amber-400" label="Customer Approvals"
              badge={approvals.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/25 text-amber-200 border border-amber-500/40 font-semibold">{approvals.length}</span>
              )}
              right={<Link to="/approvals"><span className="text-[10px] text-blue-400 hover:underline">All approvals →</span></Link>}
            />
            {approvals.length === 0 ? (
              <ActionEmptyRow text="No approvals pending." />
            ) : (
              <div className="space-y-1">
                {approvals.slice(0, 4).map(item => (
                  <Link key={item.record_id} to="/approvals" data-testid={`approval-${item.record_id}`}>
                    <div className="flex items-center justify-between px-2.5 py-2 rounded-lg hover:opacity-90 transition-opacity" style={{ backgroundColor: 'var(--surface-2)' }}>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-xs" style={{ color: 'var(--text)' }}>{item.order_number || item.customer_name}</p>
                        <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
                          {item.customer_name} · {item.type} · {item.age_hours < 1 ? '<1h' : `${Math.round(item.age_hours)}h`} ago
                        </p>
                      </div>
                      <ChevronRight className="h-3 w-3 ml-2 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <SectionDivider />

          {/* ── 2. Messages ── */}
          <div className="p-4">
            <SectionLabel
              icon={MessageSquare} iconColor="text-blue-400" label="Messages"
              badge={totalUnread > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40 font-semibold">{totalUnread} unread</span>
              )}
              right={<Link to="/admin-portal?tab=messages"><span className="text-[10px] text-blue-400 hover:underline">All messages →</span></Link>}
            />
            {messages.length === 0 ? (
              <ActionEmptyRow text="Inbox zero — no unread messages." />
            ) : (
              <div className="space-y-1">
                {messages.slice(0, 3).map(msg => (
                  <Link key={msg.conversation_id} to="/admin-portal?tab=messages" data-testid={`message-row-${msg.conversation_id}`}>
                    <div className="flex items-center justify-between px-2.5 py-2 rounded-lg hover:opacity-90 transition-opacity" style={{ backgroundColor: 'var(--surface-2)' }}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-xs truncate" style={{ color: 'var(--text)' }}>{msg.customer_name}</p>
                          <span className="flex-shrink-0 w-4 h-4 rounded-full bg-blue-500 text-white text-[10px] flex items-center justify-center">{msg.unread_count}</span>
                        </div>
                        <p className="text-[10px] truncate" style={{ color: 'var(--text-muted)' }}>{msg.last_message_preview}</p>
                      </div>
                      <ChevronRight className="h-3 w-3 ml-2 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          <SectionDivider />

          {/* ── 3. Quote Follow-Ups ── */}
          <div className="p-4">
            <SectionLabel
              icon={Send} iconColor="text-purple-400" label="Quote Follow-Ups"
              badge={quotes.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-semibold">{quotes.length}</span>
              )}
              right={<Link to="/orders?filter=quote_sent"><span className="text-[10px] text-blue-400 hover:underline">All quotes →</span></Link>}
            />
            {quotes.length === 0 ? (
              <ActionEmptyRow text="No pending quote follow-ups." />
            ) : (
              <div className="space-y-1">
                {quotes.slice(0, 3).map(q => (
                  <div key={q.quote_id} className="flex items-center justify-between px-2.5 py-2 rounded-lg" style={{ backgroundColor: 'var(--surface-2)' }} data-testid={`quote-followup-${q.quote_id}`}>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-xs truncate" style={{ color: 'var(--text)' }}>{q.customer_name}</p>
                      <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{formatCurrency(q.quote_total)} · {Math.round(q.age_days)}d old</p>
                    </div>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/25 text-amber-200 border border-amber-500/40 flex-shrink-0 ml-2">{Math.round(q.age_days)}d</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <SectionDivider />

          {/* ── 4. Invoices & Payments ── */}
          <div className="p-4">
            <SectionLabel
              icon={Receipt} iconColor="text-amber-400" label="Invoices & Payments"
              badge={unpaidCount > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-semibold">{unpaidCount} unpaid</span>
              )}
              right={<Link to="/invoices"><span className="text-[10px] text-blue-400 hover:underline">All invoices →</span></Link>}
            />
            {overdueCount > 0 ? (
              <Link to="/invoices?status=overdue">
                <div className="flex items-center justify-between px-2.5 py-2 rounded-lg hover:opacity-90 transition-opacity"
                  style={{ backgroundColor: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)' }}>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-3.5 w-3.5 text-red-400 flex-shrink-0" />
                    <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                      {overdueCount} overdue invoice{overdueCount !== 1 ? 's' : ''} — needs attention
                    </span>
                  </div>
                  <ChevronRight className="h-3 w-3 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                </div>
              </Link>
            ) : (
              <ActionEmptyRow text={unpaidCount > 0 ? `${unpaidCount} unpaid — none overdue yet.` : 'No outstanding invoices.'} />
            )}
          </div>

          <SectionDivider />

          {/* ── 5. Customer Actions ── */}
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Inbox className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>Customer Actions</span>
            </div>
            <PendingCustomerActionsWidget />
          </div>
        </>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// Row 5 — Financial Attention
// ─────────────────────────────────────────────
const FinancialSectionCard = ({ title, icon: Icon, iconColor, data: section, emptyText, href }) => (
  <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
    <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
      <div className="flex items-center gap-1.5">
        <Icon className={`h-4 w-4 ${iconColor}`} />
        <span className="text-sm font-semibold font-heading" style={{ color: 'var(--text)' }}>{title}</span>
      </div>
      {section?.count > 0 && (
        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${iconColor.includes('red') ? 'bg-red-500/10 text-red-400' : iconColor.includes('amber') ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'}`}>
          {section.count}
        </span>
      )}
    </div>
    <div className="p-3">
      {!section || section.count === 0 ? (
        <p className="text-xs text-center py-2" style={{ color: 'var(--text-muted)' }}>{emptyText}</p>
      ) : (
        <>
          <p className="text-lg font-bold font-heading mb-2" style={{ color: 'var(--text)' }}>{formatCurrency(section.total_amount)}</p>
          <div className="space-y-1">
            {(section.top_records || []).map((rec, i) => (
              <Link key={rec.invoice_id || i} to={href || '/invoices'}>
                <div className="flex items-center justify-between text-xs py-1 hover:opacity-80" style={{ borderTop: i > 0 ? '1px solid var(--border-light)' : 'none' }}>
                  <span className="truncate flex-1" style={{ color: 'var(--text-muted)' }}>{rec.customer_name}</span>
                  <span className="font-medium ml-2 flex-shrink-0" style={{ color: 'var(--text)' }}>{formatCurrency(rec.amount)}</span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  </div>
);

const FinancialAttentionRow = ({ data, loading, error, onRetry }) => {
  const freshness = data?.last_updated_at !== undefined ? getFreshness(data?.last_updated_at) : null;

  if (loading) return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {[1,2,3,4].map(i => <div key={i} className="h-32 rounded-xl animate-pulse" style={{ backgroundColor: 'var(--surface)' }} />)}
    </div>
  );
  if (error) return <div className="rounded-xl p-4" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}><ErrorState onRetry={onRetry} /></div>;

  return (
    <div data-testid="financial-attention-row">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-emerald-400" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Financial Attention</h2>
        </div>
        <div className="flex items-center gap-2">
          {freshness && (freshness.isStale || freshness.isMissing) && (
            <span
              className="text-xs text-amber-400"
              data-testid={freshness.isStale ? 'stale-indicator' : freshness.isMissing ? 'missing-ts-indicator' : undefined}
            >
              {freshness.isStale ? '⚠ Stale' : 'No timestamp'}
            </span>
          )}
          <Link to="/invoices"><span className="text-xs text-blue-400 hover:underline">All invoices</span></Link>
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <FinancialSectionCard title="Unpaid" icon={Receipt} iconColor="text-amber-400" data={data?.unpaid} emptyText="No unpaid invoices." href="/invoices?status=sent" />
        <FinancialSectionCard title="Overdue" icon={AlertTriangle} iconColor="text-red-400" data={data?.overdue} emptyText="No overdue invoices." href="/invoices?status=overdue" />
        <FinancialSectionCard title="Due This Week" icon={Clock} iconColor="text-blue-400" data={data?.due_this_week} emptyText="Nothing due this week." href="/invoices" />
        <FinancialSectionCard title="Recent Payments" icon={TrendingUp} iconColor="text-emerald-400" data={data?.recent_payments} emptyText="No recent payments." href="/invoices?status=paid" />
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// BILLING SNAPSHOT — replaces Financial Attention row
// ─────────────────────────────────────────────
const BILLING_ROWS = [
  { key: 'unpaid',          icon: Receipt,       label: 'Unpaid',         href: '/invoices?status=sent',    colorSet: { icon: 'text-amber-400',   badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/35'   } },
  { key: 'overdue',         icon: AlertTriangle, label: 'Overdue',        href: '/invoices?status=overdue', colorSet: { icon: 'text-red-400',     badge: 'bg-red-500/20 text-red-300 border border-red-500/35'         } },
  { key: 'due_this_week',   icon: Clock,         label: 'Due This Week',  href: '/invoices',                colorSet: { icon: 'text-blue-400',    badge: 'bg-blue-500/20 text-blue-300 border border-blue-500/35'      } },
  { key: 'recent_payments', icon: TrendingUp,    label: 'Paid This Week', href: '/invoices?status=paid',    colorSet: { icon: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/35' } },
];

const BillingSnapshotCard = ({ data, loading, error, onRetry }) => {
  // Pick top items from overdue first, then unpaid
  const topItems = (
    (data?.overdue?.top_records?.length > 0 ? data.overdue.top_records : data?.unpaid?.top_records) || []
  ).slice(0, 2);
  const topLabel = data?.overdue?.top_records?.length > 0 ? 'Most Overdue' : 'Largest Unpaid';

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-emerald-400" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Billing Snapshot</h2>
        </div>
        <Link to="/invoices"><span className="text-xs text-blue-400 hover:underline">All invoices</span></Link>
      </div>
      {loading ? (
        <div className="p-4"><LoadingSpinner /></div>
      ) : error ? (
        <div className="p-4"><ErrorState onRetry={onRetry} /></div>
      ) : (
        <div className="p-3" data-testid="financial-attention-row">
          {BILLING_ROWS.map(({ key, icon: Icon, label, href, colorSet }) => {
            const section = data?.[key];
            const hasData = section?.count > 0;
            return (
              <Link key={key} to={href}>
                <div
                  className="flex items-center justify-between px-2 py-2.5 rounded-lg hover:opacity-90 transition-opacity"
                  style={{ backgroundColor: 'transparent' }}
                  data-testid={`billing-row-${key}`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`h-3.5 w-3.5 flex-shrink-0 ${colorSet.icon}`} />
                    <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {hasData ? (
                      <>
                        <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>
                          {formatCurrency(section.total_amount)}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${colorSet.badge}`}>
                          {section.count}
                        </span>
                      </>
                    ) : (
                      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Clear</span>
                    )}
                    <ChevronRight className="h-3 w-3 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                  </div>
                </div>
              </Link>
            );
          })}
          {/* Top 2 items */}
          {topItems.length > 0 && (
            <div className="mt-1 pt-3 mx-2" style={{ borderTop: '1px solid var(--border-light)' }}>
              <p className="text-[10px] font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>{topLabel}</p>
              <div className="space-y-0.5">
                {topItems.map((rec, i) => (
                  <Link key={rec.invoice_id || i} to="/invoices">
                    <div className="flex items-center justify-between py-1.5 hover:opacity-80">
                      <span className="text-xs truncate flex-1" style={{ color: 'var(--text-muted)' }}>{rec.customer_name}</span>
                      <span className="text-xs font-semibold ml-2 flex-shrink-0" style={{ color: 'var(--text)' }}>{formatCurrency(rec.amount)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// Row 6 — Quick Actions (6 primary + More toggle)
// ─────────────────────────────────────────────
const QuickActionBtn = ({ to, onClick, icon: Icon, iconColor, label, testId, disabled }) => {
  const inner = (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full flex items-center justify-start gap-2 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 hover:shadow-sm disabled:opacity-50"
      style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
      data-testid={testId}
    >
      <Icon className="h-3.5 w-3.5 flex-shrink-0" style={{ color: iconColor || 'var(--accent)' }} />
      <span className="leading-snug text-left">{label}</span>
    </button>
  );
  return to ? <Link to={to}>{inner}</Link> : inner;
};

const QuickActions = ({ onSendDigest, sendingDigest }) => {
  const [showMore, setShowMore] = useState(false);

  const PRIMARY = [
    { to: '/orders/new',                    icon: Plus,      iconColor: 'var(--accent)', label: 'New Order',        testId: 'quick-new-order'        },
    { to: '/orders/new?type=quote',         icon: FileText,  iconColor: '#8B5CF6',       label: 'New Quote',        testId: 'quick-new-quote'        },
    { to: '/customers',                     icon: Plus,      iconColor: 'var(--accent)', label: 'New Customer',     testId: 'quick-add-customer'     },
    { to: '/invoices',                      icon: Receipt,   iconColor: '#10B981',       label: 'New Invoice',      testId: 'quick-create-invoice'   },
    { to: '/production-board',              icon: Briefcase, iconColor: '#2F8BFB',       label: 'Production Board', testId: 'quick-production-board' },
    { to: '/productivity?view=calendar',    icon: Calendar,  iconColor: '#8B5CF6',       label: 'Open Calendar',    testId: 'quick-open-calendar'    },
  ];

  const MORE = [
    { to: '/approvals',   icon: Send,     iconColor: '#F59E0B',       label: 'Send Approval', testId: 'quick-send-approval' },
    { to: '/invoices',    icon: Send,     iconColor: '#10B981',       label: 'Send Invoice',  testId: 'quick-send-invoice'  },
    { to: '/timeclock',   icon: Clock,    iconColor: 'var(--accent)', label: 'Time Clock',    testId: 'quick-clock-in'      },
    { to: '/ai-assistant',icon: Sparkles, iconColor: '#8B5CF6',       label: 'AI Assistant',  testId: 'quick-ai-assistant'  },
  ];

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-5 py-3.5" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Quick Actions</h2>
      </div>
      <div className="p-3 space-y-2">
        <div className="grid grid-cols-2 gap-2">
          {PRIMARY.map(a => <QuickActionBtn key={a.testId} {...a} />)}
        </div>
        {showMore && (
          <div className="grid grid-cols-2 gap-2 pt-1" style={{ borderTop: '1px solid var(--border-light)' }}>
            {MORE.map(a => <QuickActionBtn key={a.testId} {...a} />)}
          </div>
        )}
        <button
          onClick={() => setShowMore(v => !v)}
          className="w-full text-xs py-1.5 rounded-lg transition-all hover:opacity-80 flex items-center justify-center gap-1 font-medium"
          style={{ color: 'var(--text-muted)', backgroundColor: 'var(--surface-2)', border: '1px solid var(--border-light)' }}
          data-testid="quick-actions-more-toggle"
        >
          {showMore ? '▲ Show less' : '▼ More actions'}
        </button>
      </div>
    </div>
  );
};

// RecentAIDocumentsWidget — unchanged
const RecentAIDocumentsWidget = ({ documents }) => {
  const handleDownload = async (doc) => {
    try {
      const token = getAuthToken();
      const res = await axios.get(`${API}/documents/${doc.id}/download`, { headers: { Authorization: `Bearer ${token}` } });
      const { file_data, file_type, original_filename } = res.data;
      const bytes = atob(file_data);
      const arr = new Uint8Array(bytes.length).map((_, i) => bytes.charCodeAt(i));
      const url = URL.createObjectURL(new Blob([arr], { type: file_type }));
      const a = Object.assign(document.createElement('a'), { href: url, download: original_filename });
      document.body.appendChild(a); a.click(); URL.revokeObjectURL(url); document.body.removeChild(a);
      toast.success('Document downloaded');
    } catch { toast.error('Failed to download'); }
  };

  const handleView = async (doc) => {
    try {
      const token = getAuthToken();
      const res = await axios.get(`${API}/documents/${doc.id}/download`, { headers: { Authorization: `Bearer ${token}` } });
      const { file_data, file_type } = res.data;
      const bytes = atob(file_data);
      const arr = new Uint8Array(bytes.length).map((_, i) => bytes.charCodeAt(i));
      window.open(URL.createObjectURL(new Blob([arr], { type: file_type })), '_blank');
    } catch { toast.error('Failed to open document'); }
  };

  const getToolName = (tags) => {
    const toolTag = tags?.find(t => t !== 'ai-generated');
    return ({ document_composer: 'Composer', business_copywriter: 'Copywriter', blog_creator: 'Blog', email_template: 'Email', job_post_creator: 'Order Post', social_media_creator: 'Social' }[toolTag]) || 'AI Tool';
  };

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-purple-500" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Recent AI Documents</h2>
        </div>
        <Link to="/ai-tools"><span className="text-xs text-purple-400 hover:underline flex items-center gap-1">Create new <ArrowRight className="h-3 w-3" /></span></Link>
      </div>
      <div className="p-4">
        {!documents?.length ? (
          <div className="text-center py-4">
            <Sparkles className="h-7 w-7 mx-auto mb-2 text-purple-500/30" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No AI documents yet</p>
            <Link to="/ai-tools"><Button size="sm" variant="outline" className="mt-2 text-xs text-purple-500 border-purple-500/30"><Plus className="h-3 w-3 mr-1" /> Create</Button></Link>
          </div>
        ) : (
          <div className="space-y-1.5">
            {documents.map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-2.5 rounded-lg" style={{ backgroundColor: 'var(--surface-2)', border: '1px solid transparent' }}>
                <div className="flex-1 min-w-0 mr-2">
                  <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{doc.name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{getToolName(doc.tags)} · {formatDate(doc.created_at)}</p>
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => handleView(doc)} className="p-1.5 rounded-md hover:bg-purple-500/10 transition-colors" title="View"><Eye className="h-3.5 w-3.5 text-purple-500" /></button>
                  <button onClick={() => handleDownload(doc)} className="p-1.5 rounded-md hover:bg-purple-500/10 transition-colors" title="Download"><Download className="h-3.5 w-3.5 text-purple-500" /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// Main Dashboard component
// ─────────────────────────────────────────────
export default function Dashboard() {
  const { user } = useAuth();
  const { fetchDashboardStats, dashboardStats } = useApp();

  // V1 data
  const [summaryV2,          setSummaryV2]          = useState(null);
  const [commandCenter,      setCommandCenter]      = useState(null);
  const [productionSnapshot, setProductionSnapshot] = useState(null);
  const [customerAttention,  setCustomerAttention]  = useState(null);
  const [financialAttention, setFinancialAttention] = useState(null);
  const [recentAIDocs,       setRecentAIDocs]       = useState([]);

  // Per-section loading/error states
  const [loadingSummary,    setLoadingSummary]    = useState(true);
  const [loadingCommand,    setLoadingCommand]    = useState(true);
  const [loadingProduction, setLoadingProduction] = useState(true);
  const [loadingCustomer,   setLoadingCustomer]   = useState(true);
  const [loadingFinancial,  setLoadingFinancial]  = useState(true);

  const [errorSummary,    setErrorSummary]    = useState(false);
  const [errorCommand,    setErrorCommand]    = useState(false);
  const [errorProduction, setErrorProduction] = useState(false);
  const [errorCustomer,   setErrorCustomer]   = useState(false);
  const [errorFinancial,  setErrorFinancial]  = useState(false);

  const [loading,        setLoading]        = useState(true);
  const [globalUpdatedAt, setGlobalUpdatedAt] = useState(null);
  const [sendingDigest,  setSendingDigest]  = useState(false);
  const [previewInvoiceId,   setPreviewInvoiceId]   = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);

  const greeting     = getGreeting();
  const GreetingIcon = greeting.icon;

  const getHeaders = () => ({ Authorization: `Bearer ${getAuthToken()}` });

  // Individual section fetchers (used for initial load + retry)
  const fetchSummary = useCallback(async () => {
    setLoadingSummary(true); setErrorSummary(false);
    try {
      const res = await axios.get(`${API}/dashboard/summary-v2`, { headers: getHeaders() });
      setSummaryV2(res.data);
    } catch (err) { console.warn('[Dashboard] summary-v2 failed', err); setErrorSummary(true); }
    setLoadingSummary(false);
  }, []);

  const fetchCommandCenter = useCallback(async () => {
    setLoadingCommand(true); setErrorCommand(false);
    try {
      const res = await axios.get(`${API}/dashboard/today-command-center`, { headers: getHeaders() });
      setCommandCenter(res.data);
    } catch (err) { console.warn('[Dashboard] today-command-center failed', err); setErrorCommand(true); }
    setLoadingCommand(false);
  }, []);

  const fetchProductionSnapshot = useCallback(async () => {
    setLoadingProduction(true); setErrorProduction(false);
    try {
      const res = await axios.get(`${API}/dashboard/production-snapshot`, { headers: getHeaders() });
      setProductionSnapshot(res.data);
    } catch (err) { console.warn('[Dashboard] production-snapshot failed', err); setErrorProduction(true); }
    setLoadingProduction(false);
  }, []);

  const fetchCustomerAttention = useCallback(async () => {
    setLoadingCustomer(true); setErrorCustomer(false);
    try {
      const res = await axios.get(`${API}/dashboard/customer-attention`, { headers: getHeaders() });
      setCustomerAttention(res.data);
    } catch (err) { console.warn('[Dashboard] customer-attention failed', err); setErrorCustomer(true); }
    setLoadingCustomer(false);
  }, []);

  const fetchFinancialAttention = useCallback(async () => {
    setLoadingFinancial(true); setErrorFinancial(false);
    try {
      const res = await axios.get(`${API}/dashboard/financial-attention`, { headers: getHeaders() });
      setFinancialAttention(res.data);
    } catch (err) { console.warn('[Dashboard] financial-attention failed', err); setErrorFinancial(true); }
    setLoadingFinancial(false);
  }, []);

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      await Promise.all([
        fetchDashboardStats(),
        fetchSummary(),
        fetchCommandCenter(),
        fetchProductionSnapshot(),
        fetchCustomerAttention(),
        fetchFinancialAttention(),
        axios.get(`${API}/dashboard/recent-ai-documents`, { headers: getHeaders() })
          .then(res => setRecentAIDocs(res.data))
          .catch(err => console.warn('[Dashboard] recent-ai-documents failed', err)),
      ]);
      setLoading(false);
      setGlobalUpdatedAt(new Date());
    };
    loadAll();
  }, []);

  const handleSendDigest = async () => {
    setSendingDigest(true);
    try {
      const res = await axios.post(`${API}/digest/send`, {}, { headers: getHeaders() });
      toast.success(res.data.message || 'Daily digest sent!');
    } catch {
      toast.error('Failed to send digest. Check Settings > Daily Digest to add recipients.');
    }
    setSendingDigest(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }} />
      </div>
    );
  }

  const dueItems   = commandCenter?.due_order_items_today        || [];
  const appts      = commandCenter?.appointments_installs_today  || [];
  const teamStatus = commandCenter?.team_status_today            || null;
  const cmdLastUpdated = commandCenter?.last_updated_at;

  return (
    <div className="space-y-5 sm:space-y-6 animate-fade-in" data-testid="dashboard">
      {/* ── Header ─────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 sm:gap-3 mb-1">
            <GreetingIcon className={`h-6 w-6 sm:h-7 sm:w-7 ${greeting.color}`} />
            <h1 className="text-2xl sm:text-3xl font-bold font-heading tracking-tight text-white">
              {greeting.text}, {user?.full_name?.split(' ')[0] || 'there'}!
            </h1>
            <FoundersBadge size="small" />
          </div>
          <p className="ml-8 sm:ml-10 text-sm sm:text-base" style={{ color: 'var(--text-muted)' }}>
            Here&apos;s what&apos;s happening at {user?.company_name || 'your shop'} today
          </p>
        </div>
        <div className="text-left sm:text-right ml-8 sm:ml-0 flex-shrink-0">
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {globalUpdatedAt
              ? `Updated ${globalUpdatedAt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`
              : loading ? 'Loading…' : 'Ready'}
          </p>
        </div>
      </div>

      {/* ── Priority Action Strip (urgent ops first) ── */}
      <SeverityStripWidget data={summaryV2} loading={loadingSummary} error={errorSummary} onRetry={fetchSummary} />

      {/* ── Business Overview + Quick Actions (side by side) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest mb-2.5" style={{ color: 'var(--text-muted)', borderLeft: '2px solid var(--accent)', paddingLeft: '8px' }}>
            Business Overview
          </p>
          <div className="grid grid-cols-2 gap-3">
            <StatCard title="Total Customers"  value={dashboardStats?.total_customers || 0}              icon={Users}      href="/customers"  accentColor="#2F8BFB" />
            <StatCard title="Active Orders"    value={dashboardStats?.active_orders ?? dashboardStats?.active_jobs ?? 0} icon={Briefcase} href="/orders" accentColor="#10B981" />
            <StatCard title="Pending Invoices" value={dashboardStats?.pending_invoices || 0}              icon={Receipt}    href="/invoices"   accentColor="#F59E0B" />
            <StatCard title="Today's Revenue"  value={formatCurrency(dashboardStats?.today_revenue || 0)} icon={TrendingUp} href="/financials" accentColor="#8B5CF6" />
          </div>
        </div>
        <QuickActions onSendDigest={handleSendDigest} sendingDigest={sendingDigest} />
      </div>

      {/* ── Today Command Center ─────────── */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Clock className="h-4 w-4 text-blue-400" />
          <h2 className="font-heading text-sm font-semibold" style={{ color: 'var(--text)' }}>Today&apos;s Command Center</h2>
          {commandCenter && (() => {
            const f = getFreshness(cmdLastUpdated);
            return (f.isStale || f.isMissing) ? (
              <span className="text-xs text-amber-400" data-testid={f.isStale ? 'stale-indicator' : undefined}>
                {f.isStale ? '⚠ Stale' : 'No timestamp'}
              </span>
            ) : null;
          })()}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
          <ScheduleWidget   items={dueItems} lastUpdatedAt={cmdLastUpdated} loading={loadingCommand} error={errorCommand} onRetry={fetchCommandCenter} />
          <AppointmentsWidget items={appts} lastUpdatedAt={cmdLastUpdated} loading={loadingCommand} error={errorCommand} onRetry={fetchCommandCenter} />
          <TeamStatusWidget teamStatus={teamStatus} lastUpdatedAt={cmdLastUpdated} loading={loadingCommand} error={errorCommand} onRetry={fetchCommandCenter} />
        </div>
      </div>

      {/* ── Production Pipeline ──────────── */}
      <ProductionSnapshotWidget data={productionSnapshot} loading={loadingProduction} error={errorProduction} onRetry={fetchProductionSnapshot} />

      {/* ── Action Required (consolidated) ─────────── */}
      <ActionRequiredCard
        data={customerAttention}
        loading={loadingCustomer}
        error={errorCustomer}
        onRetry={fetchCustomerAttention}
        summaryData={summaryV2}
      />

      {/* ── Billing Snapshot ─────────────────────── */}
      <BillingSnapshotCard data={financialAttention} loading={loadingFinancial} error={errorFinancial} onRetry={fetchFinancialAttention} />

      {/* ── Recent AI Documents ──────────────────── */}
      <RecentAIDocumentsWidget documents={recentAIDocs} />

      {/* ── Onboarding + AI Nudges ───────────────── */}
      <OnboardingChecklist />
      <AssistantNudgesWidget />

      {/* ── Invoice Preview Modal ────────────────── */}
      <InvoicePreviewModal
        invoiceId={previewInvoiceId}
        isOpen={isInvoiceModalOpen}
        onClose={() => { setIsInvoiceModalOpen(false); setPreviewInvoiceId(null); }}
      />
    </div>
  );
}
