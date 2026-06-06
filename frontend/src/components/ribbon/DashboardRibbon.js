/**
 * Dashboard command ribbon — matches WebstoresRibbon dimensions exactly.
 *
 * 12 visible actions in 3 groups:
 *   Create     — New Order | New Quote | New Customer | Pricing Calc
 *   Customer   — Send Proof | Request Approval | Send Document | New Invoice
 *   Production — Send Email | New Task | Schedule Install | Open Calendar
 *
 * Design mirrors WebstoresRibbon:
 *   h-14, bg-white, border-b border-gray-100, RibbonButton (min-w-[68px]),
 *   icon h-5 w-5, label text-[11px], group title text-[10px] uppercase.
 */
import { useNavigate } from 'react-router-dom';
import {
  Briefcase, FileText, UserPlus, Receipt,
  ClipboardCheck, Send, Eye,
  Calculator, CheckSquare, CalendarDays,
  Mail, Calendar,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const RibbonButton = ({ icon: Icon, label, onClick, disabled = false, testId }) => (
  <button
    type="button"
    onClick={disabled ? undefined : onClick}
    disabled={disabled}
    className={cn(
      'flex flex-col items-center justify-center gap-1 px-3 py-1.5 rounded-md min-w-[68px] transition-colors',
      disabled
        ? 'text-gray-400 cursor-not-allowed'
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
    )}
    data-testid={testId}
  >
    <Icon className={cn('h-5 w-5', disabled ? 'text-gray-300' : 'text-gray-500')} />
    <span className="text-[11px] leading-none font-medium">{label}</span>
  </button>
);

const RibbonGroup = ({ title, children, testId }) => (
  <div className="flex flex-col items-stretch px-2 first:pl-3 last:pr-3" data-testid={testId}>
    <div className="flex items-center gap-1 flex-1">
      {children}
    </div>
    <div className="text-[10px] uppercase tracking-wide text-gray-400 text-center mt-0.5">
      {title}
    </div>
  </div>
);

const GroupSeparator = () => (
  <div className="w-px self-stretch bg-gray-200 mx-1 my-1" aria-hidden="true" />
);

export const DashboardRibbon = () => {
  const navigate = useNavigate();

  return (
    <div
      className="h-14 flex items-stretch px-3 bg-white border-b border-gray-100 overflow-x-auto scrollbar-none"
      data-testid="dashboard-ribbon"
      role="toolbar"
      aria-label="Dashboard command ribbon"
    >
      {/* ── Create ─────────────────────────────── */}
      <RibbonGroup title="Create" testId="dashboard-ribbon-group-create">
        <RibbonButton
          icon={Briefcase}
          label="New Order"
          onClick={() => navigate('/orders/new')}
          testId="dashboard-ribbon-new-order"
        />
        <RibbonButton
          icon={FileText}
          label="New Quote"
          onClick={() => navigate('/orders/new?type=quote')}
          testId="dashboard-ribbon-new-quote"
        />
        <RibbonButton
          icon={UserPlus}
          label="New Customer"
          onClick={() => navigate('/customers?new=true')}
          testId="dashboard-ribbon-new-customer"
        />
        <RibbonButton
          icon={Calculator}
          label="Pricing Calc"
          onClick={() => navigate('/pricing-calculator')}
          testId="dashboard-ribbon-pricing-calc"
        />
      </RibbonGroup>

      <GroupSeparator />

      {/* ── Customer ───────────────────────────── */}
      <RibbonGroup title="Customer" testId="dashboard-ribbon-group-customer">
        <RibbonButton
          icon={Eye}
          label="Send Proof"
          onClick={() => navigate('/approvals')}
          testId="dashboard-ribbon-send-proof"
        />
        <RibbonButton
          icon={ClipboardCheck}
          label="Request Approval"
          onClick={() => navigate('/approvals')}
          testId="dashboard-ribbon-request-approval"
        />
        <RibbonButton
          icon={Send}
          label="Send Document"
          onClick={() => navigate('/documents')}
          testId="dashboard-ribbon-send-document"
        />
        <RibbonButton
          icon={Receipt}
          label="New Invoice"
          onClick={() => navigate('/invoices?new=true')}
          testId="dashboard-ribbon-new-invoice"
        />
      </RibbonGroup>

      <GroupSeparator />

      {/* ── Production ─────────────────────────── */}
      <RibbonGroup title="Production" testId="dashboard-ribbon-group-production">
        <RibbonButton
          icon={Mail}
          label="Send Email"
          onClick={() => navigate('/admin-portal')}
          testId="dashboard-ribbon-send-email"
        />
        <RibbonButton
          icon={CheckSquare}
          label="New Task"
          onClick={() => navigate('/productivity?view=tasks')}
          testId="dashboard-ribbon-new-task"
        />
        <RibbonButton
          icon={CalendarDays}
          label="Schedule Install"
          onClick={() => navigate('/productivity?view=calendar')}
          testId="dashboard-ribbon-schedule-install"
        />
        <RibbonButton
          icon={Calendar}
          label="Open Calendar"
          onClick={() => navigate('/productivity?view=calendar')}
          testId="dashboard-ribbon-open-calendar"
        />
      </RibbonGroup>
    </div>
  );
};

export default DashboardRibbon;
