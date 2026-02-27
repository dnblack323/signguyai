import { useNavigate } from 'react-router-dom';
import { 
  Plus, Save, Copy, FileText, Send, List, Calendar, LayoutGrid, UserCheck,
  Briefcase, Clock, CalendarDays, Printer, FileDown,
  CheckCircle, ArrowRightCircle, FileCheck,
  Receipt, DollarSign, CreditCard, Bell,
  Users, StickyNote, UserPlus, Star, Building,
  Store, Package, ShoppingCart, Wallet, Share2, Ticket,
  Sparkles, Wand2, Type, Mail, FileEdit, MessageSquare, TrendingUp, BarChart3,
  PieChart, LineChart, Timer, AlertTriangle,
  Settings, Shield, Lock
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { SplitButton } from './DropdownMenu';

// Ribbon Button Component
const RibbonButton = ({ icon: Icon, label, onClick, active = false, disabled = false }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={cn(
      "flex flex-col items-center gap-1 px-3 py-2 rounded-md transition-colors min-w-[60px]",
      active && "bg-[var(--accent-soft)]",
      disabled 
        ? "opacity-50 cursor-not-allowed"
        : "hover:bg-[var(--accent-soft)]"
    )}
    data-testid={`ribbon-btn-${label?.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <Icon className={cn("h-5 w-5", active ? "text-[var(--accent)]" : "text-[var(--text-muted)]")} />
    <span className={cn("text-xs", active ? "text-[var(--accent)] font-medium" : "text-[var(--text)]")}>{label}</span>
  </button>
);

// Ribbon Group Component
const RibbonGroup = ({ title, children }) => (
  <div className="flex flex-col h-full">
    <div className="flex items-end gap-1 flex-1 px-2">
      {children}
    </div>
    <div className="text-[10px] text-center text-[var(--text-muted)] border-t border-[var(--border-light)] mt-1 pt-1 px-2">
      {title}
    </div>
  </div>
);

// Separator between groups
const GroupSeparator = () => (
  <div className="w-px h-16 bg-[var(--border-light)] mx-2" />
);

// Home Tab Toolbar
const HomeToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <SplitButton
        label="New"
        icon={Plus}
        onClick={() => navigate('/jobs?new=true')}
        dropdownItems={[
          { icon: Briefcase, label: 'New Job', onClick: () => navigate('/jobs?new=true') },
          { icon: FileText, label: 'New Quote', onClick: () => navigate('/jobs?new=true&type=quote') },
          { icon: Receipt, label: 'New Invoice', onClick: () => navigate('/invoices?new=true') },
        ]}
      />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Quick Actions">
      <RibbonButton icon={Save} label="Save" onClick={() => {}} />
      <RibbonButton icon={Copy} label="Duplicate" onClick={() => {}} />
      <SplitButton
        label="Export"
        icon={FileDown}
        onClick={() => {}}
        dropdownItems={[
          { icon: FileText, label: 'Export PDF', onClick: () => {} },
          { icon: FileDown, label: 'Export CSV', onClick: () => {} },
          { icon: Printer, label: 'Print', onClick: () => window.print() },
        ]}
      />
      <RibbonButton icon={Send} label="Send" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Views">
      <RibbonButton icon={List} label="List" onClick={() => {}} active />
      <RibbonButton icon={Calendar} label="Calendar" onClick={() => {}} />
      <RibbonButton icon={LayoutGrid} label="Kanban" onClick={() => {}} />
      <RibbonButton icon={UserCheck} label="Assigned" onClick={() => {}} />
    </RibbonGroup>
  </div>
);

// Jobs Tab Toolbar
const JobsToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <RibbonButton icon={Plus} label="New Job" onClick={() => navigate('/jobs?new=true')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Status">
      <SplitButton
        label="Status"
        icon={CheckCircle}
        onClick={() => {}}
        dropdownItems={[
          { label: 'Mark as Quote', onClick: () => {} },
          { label: 'Mark as In Progress', onClick: () => {} },
          { label: 'Mark as Complete', onClick: () => {} },
          { label: 'Mark as Invoiced', onClick: () => {} },
        ]}
      />
      <RibbonButton icon={UserCheck} label="Assign" onClick={() => {}} />
      <RibbonButton icon={CalendarDays} label="Due Date" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Output">
      <RibbonButton icon={Printer} label="Work Order" onClick={() => {}} />
      <SplitButton
        label="Export"
        icon={FileDown}
        onClick={() => {}}
        dropdownItems={[
          { icon: FileText, label: 'Export PDF', onClick: () => {} },
          { icon: FileDown, label: 'Export CSV', onClick: () => {} },
        ]}
      />
    </RibbonGroup>
  </div>
);

// Quotes Tab Toolbar
const QuotesToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <RibbonButton icon={Plus} label="New Quote" onClick={() => navigate('/jobs?new=true&type=quote')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Actions">
      <RibbonButton icon={CheckCircle} label="Approve" onClick={() => {}} />
      <RibbonButton icon={ArrowRightCircle} label="To Job" onClick={() => {}} />
      <RibbonButton icon={Send} label="Send" onClick={() => {}} />
      <RibbonButton icon={FileText} label="PDF" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Templates">
      <SplitButton
        label="Template"
        icon={FileCheck}
        onClick={() => {}}
        dropdownItems={[
          { label: 'Basic Quote', onClick: () => {} },
          { label: 'Detailed Estimate', onClick: () => {} },
          { label: 'Custom Template', onClick: () => {} },
        ]}
      />
    </RibbonGroup>
  </div>
);

// Invoices Tab Toolbar
const InvoicesToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <RibbonButton icon={Plus} label="New Invoice" onClick={() => navigate('/invoices?new=true')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Actions">
      <RibbonButton icon={CheckCircle} label="Mark Paid" onClick={() => {}} />
      <RibbonButton icon={Bell} label="Reminder" onClick={() => {}} />
      <RibbonButton icon={FileText} label="PDF" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Payments">
      <RibbonButton icon={CreditCard} label="Payment" onClick={() => {}} />
      <RibbonButton icon={DollarSign} label="View All" onClick={() => {}} />
    </RibbonGroup>
  </div>
);

// Customers Tab Toolbar
const CustomersToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <RibbonButton icon={UserPlus} label="Customer" onClick={() => navigate('/customers?new=true')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Actions">
      <RibbonButton icon={StickyNote} label="Add Note" onClick={() => {}} />
      <RibbonButton icon={FileText} label="Quote" onClick={() => {}} />
      <RibbonButton icon={Receipt} label="Invoice" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Views">
      <RibbonButton icon={Users} label="All" onClick={() => {}} active />
      <RibbonButton icon={Clock} label="Past Due" onClick={() => {}} />
      <RibbonButton icon={Star} label="VIP" onClick={() => {}} />
    </RibbonGroup>
  </div>
);

// Webstores Tab Toolbar
const WebstoresToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="New">
      <RibbonButton icon={Plus} label="Webstore" onClick={() => navigate('/webstores?new=true')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Actions">
      <RibbonButton icon={Package} label="Products" onClick={() => navigate('/products')} />
      <RibbonButton icon={ShoppingCart} label="Orders" onClick={() => {}} />
      <RibbonButton icon={Wallet} label="Payouts" onClick={() => {}} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Marketing">
      <RibbonButton icon={Share2} label="Share" onClick={() => {}} />
      <RibbonButton icon={Ticket} label="Promos" onClick={() => navigate('/promo-codes')} />
    </RibbonGroup>
  </div>
);

// AI Tools Tab Toolbar
const AIToolsToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="Design">
      <RibbonButton icon={LayoutGrid} label="Layout" onClick={() => navigate('/ai-tools')} />
      <RibbonButton icon={Wand2} label="Vectorizer" onClick={() => navigate('/ai-tools')} />
      <RibbonButton icon={Type} label="Font ID" onClick={() => navigate('/ai-tools')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Writing">
      <RibbonButton icon={Mail} label="Emails" onClick={() => navigate('/ai-tools')} />
      <RibbonButton icon={FileEdit} label="Proposals" onClick={() => navigate('/ai-tools')} />
      <RibbonButton icon={MessageSquare} label="Social" onClick={() => navigate('/ai-tools')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Analysis">
      <RibbonButton icon={DollarSign} label="Pricing" onClick={() => navigate('/pricing-calculator')} />
      <RibbonButton icon={TrendingUp} label="Profits" onClick={() => navigate('/financials')} />
    </RibbonGroup>
  </div>
);

// Reports Tab Toolbar
const ReportsToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="Financial">
      <RibbonButton icon={TrendingUp} label="Profit" onClick={() => navigate('/financials')} />
      <RibbonButton icon={BarChart3} label="Revenue" onClick={() => navigate('/financials')} />
      <RibbonButton icon={PieChart} label="Costs" onClick={() => navigate('/financials')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Production">
      <RibbonButton icon={Timer} label="Time/Job" onClick={() => navigate('/productivity')} />
      <RibbonButton icon={AlertTriangle} label="Bottlenecks" onClick={() => navigate('/productivity')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Exports">
      <SplitButton
        label="Export"
        icon={FileDown}
        onClick={() => {}}
        dropdownItems={[
          { icon: FileText, label: 'Export CSV', onClick: () => {} },
          { icon: FileDown, label: 'Export PDF', onClick: () => {} },
        ]}
      />
    </RibbonGroup>
  </div>
);

// Settings Tab Toolbar
const SettingsToolbar = ({ navigate }) => (
  <div className="flex items-stretch h-full">
    <RibbonGroup title="Company">
      <RibbonButton icon={Building} label="Business" onClick={() => navigate('/settings')} />
      <RibbonButton icon={DollarSign} label="Taxes" onClick={() => navigate('/settings')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Users">
      <RibbonButton icon={Shield} label="Roles" onClick={() => navigate('/users')} />
      <RibbonButton icon={Lock} label="Permissions" onClick={() => navigate('/users')} />
    </RibbonGroup>

    <GroupSeparator />

    <RibbonGroup title="Billing">
      <RibbonButton icon={CreditCard} label="Plan" onClick={() => navigate('/billing')} />
      <RibbonButton icon={Receipt} label="Invoices" onClick={() => navigate('/billing')} />
      <RibbonButton icon={Wallet} label="Payment" onClick={() => navigate('/admin/payments')} />
    </RibbonGroup>
  </div>
);

// Main RibbonToolbar Component
export const RibbonToolbar = ({ activeTab }) => {
  const navigate = useNavigate();

  const toolbars = {
    home: <HomeToolbar navigate={navigate} />,
    jobs: <JobsToolbar navigate={navigate} />,
    quotes: <QuotesToolbar navigate={navigate} />,
    invoices: <InvoicesToolbar navigate={navigate} />,
    customers: <CustomersToolbar navigate={navigate} />,
    webstores: <WebstoresToolbar navigate={navigate} />,
    'ai-tools': <AIToolsToolbar navigate={navigate} />,
    reports: <ReportsToolbar navigate={navigate} />,
    settings: <SettingsToolbar navigate={navigate} />,
  };

  return (
    <div 
      className="flex-1 flex items-stretch py-1 px-4 overflow-x-auto"
      data-testid="ribbon-toolbar"
    >
      {toolbars[activeTab] || toolbars.home}
    </div>
  );
};

export default RibbonToolbar;
