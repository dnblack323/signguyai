import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, Home, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings, ChevronRight,
  Plus, Save, Copy, FileDown, Send, List, Calendar,
  CheckCircle, UserCheck, Package, Share2, Wand2,
  TrendingUp, Shield, CreditCard, LogOut
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';

// Ribbon tab configuration with their actions
const mobileRibbonConfig = [
  { 
    id: 'home', 
    label: 'Home', 
    icon: Home,
    actions: [
      { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
      { icon: FileText, label: 'New Quote', route: '/jobs?new=true&type=quote' },
      { icon: Receipt, label: 'New Invoice', route: '/invoices?new=true' },
      { separator: true },
      { icon: List, label: 'View List', route: '/dashboard' },
      { icon: Calendar, label: 'Calendar', route: '/dashboard' },
    ]
  },
  { 
    id: 'jobs', 
    label: 'Jobs', 
    icon: Briefcase,
    actions: [
      { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
      { icon: List, label: 'All Jobs', route: '/jobs' },
      { icon: CheckCircle, label: 'Change Status', action: 'status' },
      { icon: UserCheck, label: 'Assign Tech', action: 'assign' },
    ]
  },
  { 
    id: 'quotes', 
    label: 'Quotes', 
    icon: FileText,
    actions: [
      { icon: Plus, label: 'New Quote', route: '/jobs?new=true&type=quote' },
      { icon: List, label: 'All Quotes', route: '/jobs?filter=quotes' },
      { icon: CheckCircle, label: 'Approve', action: 'approve' },
      { icon: Send, label: 'Send Quote', action: 'send' },
    ]
  },
  { 
    id: 'invoices', 
    label: 'Invoices', 
    icon: Receipt,
    actions: [
      { icon: Plus, label: 'New Invoice', route: '/invoices?new=true' },
      { icon: List, label: 'All Invoices', route: '/invoices' },
      { icon: CheckCircle, label: 'Mark Paid', action: 'paid' },
      { icon: CreditCard, label: 'Take Payment', action: 'payment' },
    ]
  },
  { 
    id: 'customers', 
    label: 'Customers', 
    icon: Users,
    actions: [
      { icon: Plus, label: 'New Customer', route: '/customers?new=true' },
      { icon: List, label: 'All Customers', route: '/customers' },
    ]
  },
  { 
    id: 'webstores', 
    label: 'Webstores', 
    icon: Store,
    actions: [
      { icon: Plus, label: 'New Webstore', route: '/webstores?new=true' },
      { icon: List, label: 'All Webstores', route: '/webstores' },
      { icon: Package, label: 'Products', route: '/products' },
      { icon: Share2, label: 'Promo Codes', route: '/promo-codes' },
    ]
  },
  { 
    id: 'ai-tools', 
    label: 'AI Tools', 
    icon: Sparkles,
    actions: [
      { icon: Sparkles, label: 'AI Tools', route: '/ai-tools' },
      { icon: Wand2, label: 'AI Assistant', route: '/ai-assistant' },
      { icon: FileText, label: 'Documents', route: '/documents' },
      { icon: FileText, label: 'Questionnaires', route: '/questionnaires' },
    ]
  },
  { 
    id: 'reports', 
    label: 'Reports', 
    icon: BarChart3,
    actions: [
      { icon: TrendingUp, label: 'Financials', route: '/financials' },
      { icon: BarChart3, label: 'Productivity', route: '/productivity' },
      { icon: Calendar, label: 'Time Clock', route: '/timeclock' },
    ]
  },
  { 
    id: 'settings', 
    label: 'Settings', 
    icon: Settings,
    actions: [
      { icon: Settings, label: 'Company', route: '/settings' },
      { icon: Shield, label: 'Users', route: '/users' },
      { icon: CreditCard, label: 'Billing', route: '/billing' },
    ]
  },
];

export const MobileRibbonOverlay = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('home');

  const handleActionClick = (action) => {
    if (action.route) {
      navigate(action.route);
      onClose();
    } else if (action.action) {
      // Handle non-route actions
      console.log('Action:', action.action);
    }
  };

  const activeTabConfig = mobileRibbonConfig.find(t => t.id === activeTab);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />

      {/* Overlay Panel */}
      <div className="absolute inset-x-0 top-0 bg-[var(--surface)] max-h-[85vh] overflow-hidden rounded-b-2xl shadow-2xl animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-light)] bg-[var(--surface-2)]">
          <span className="font-semibold text-[var(--text)]">Menu</span>
          <button
            onClick={onClose}
            className="p-2 text-[var(--text-muted)] hover:text-[var(--text)] rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab Selector */}
        <div className="flex overflow-x-auto border-b border-[var(--border-light)] bg-white">
          {mobileRibbonConfig.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex flex-col items-center gap-1 px-4 py-3 min-w-[70px] transition-colors relative",
                  isActive 
                    ? "text-[var(--accent)]"
                    : "text-[var(--text-muted)]"
                )}
              >
                <Icon className="h-5 w-5" />
                <span className="text-xs font-medium">{tab.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-[var(--accent)] rounded-full" />
                )}
              </button>
            );
          })}
        </div>

        {/* Actions List */}
        <div className="overflow-y-auto max-h-[50vh]">
          {activeTabConfig?.actions.map((action, index) => {
            if (action.separator) {
              return <div key={index} className="h-px bg-[var(--border-light)] my-2" />;
            }

            const Icon = action.icon;
            return (
              <button
                key={index}
                onClick={() => handleActionClick(action)}
                className="flex items-center gap-4 w-full px-4 py-3 text-left hover:bg-[var(--surface-2)] transition-colors"
              >
                <div className="w-10 h-10 rounded-lg bg-[var(--accent-soft)] flex items-center justify-center">
                  <Icon className="h-5 w-5 text-[var(--accent)]" />
                </div>
                <span className="flex-1 font-medium text-[var(--text)]">{action.label}</span>
                <ChevronRight className="h-4 w-4 text-[var(--text-muted)]" />
              </button>
            );
          })}
        </div>

        {/* User Section */}
        <div className="border-t border-[var(--border-light)] p-4 bg-[var(--surface-2)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[var(--accent)] flex items-center justify-center text-white font-medium">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-[var(--text)] truncate">{user?.full_name}</p>
              <p className="text-sm text-[var(--text-muted)] truncate">{user?.email}</p>
            </div>
            <button
              onClick={() => {
                logout();
                onClose();
              }}
              className="p-2 text-red-500 hover:bg-red-50 rounded-md"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileRibbonOverlay;
