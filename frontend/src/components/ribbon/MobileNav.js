import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  X, LayoutDashboard, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings, ChevronDown, LogOut,
  Plus, Calendar, Package, TrendingUp, CreditCard, FolderOpen,
  UserCog, Clock, MessageCircle, Shield, Wrench, FileCheck,
  Send, BookOpen, Tag, DollarSign, Wallet, ClipboardList
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';

const DEFAULT_LOGO = "https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png";

const mobileNavItems = [
  { 
    id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard',
    children: []
  },
  { 
    id: 'orders', label: 'Orders', icon: Package, path: '/orders',
    children: [
      { label: 'All Orders', path: '/orders' },
      { label: 'New Order', path: '/orders/new' },
      { label: 'Production Board', path: '/production-board' },
      { label: 'Approvals', path: '/approvals' },
    ]
  },
  { 
    id: 'billing', label: 'Billing', icon: Receipt, path: '/invoices',
    children: [
      { label: 'Invoices', path: '/invoices' },
      { label: 'Payments', path: '/admin/payments' },
      { label: 'Pricing Calculator', path: '/pricing-calculator' },
      { label: 'Billing & Plan', path: '/billing' },
    ]
  },
  { 
    id: 'customers', label: 'Customers', icon: Users, path: '/customers',
    children: [
      { label: 'All Customers', path: '/customers' },
      { label: 'Admin Portal', path: '/admin-portal' },
    ]
  },
  { 
    id: 'webstores', label: 'Webstores', icon: Store, path: '/webstores',
    children: [
      { label: 'All Stores', path: '/webstores' },
      { label: 'Products', path: '/products' },
    ]
  },
  { 
    id: 'documents', label: 'Documents', icon: FolderOpen, path: '/documents',
    children: [
      { label: 'Document Library', path: '/documents' },
      { label: 'Questionnaires', path: '/questionnaires' },
    ]
  },
  { 
    id: 'team', label: 'Team', icon: UserCog, path: '/payroll',
    children: [
      { label: 'Payroll', path: '/payroll' },
      { label: 'Employee Schedule', path: '/payroll?tab=schedule' },
      { label: 'Time Clock', path: '/timeclock' },
      { label: 'Users', path: '/users' },
    ]
  },
  { 
    id: 'ai-tools', label: 'AI Tools', icon: Sparkles, path: '/ai-tools',
    children: [
      { label: 'AI Tool Suite', path: '/ai-tools' },
      { label: 'AI Assistant', path: '/ai-assistant' },
    ]
  },
  { 
    id: 'reports', label: 'Reports', icon: BarChart3, path: '/financials',
    children: [
      { label: 'Financials', path: '/financials' },
      { label: 'Productivity', path: '/productivity' },
      { label: 'Profit & Margin', path: '/reports/profit-margin' },
    ]
  },
  { 
    id: 'community', label: 'Community', icon: MessageCircle, path: '/community',
    children: []
  },
  { 
    id: 'settings', label: 'Settings', icon: Settings, path: '/settings',
    children: [
      { label: 'Company Settings', path: '/settings' },
      { label: 'Materials & Pricing', path: '/materials' },
      { label: 'Workflow Templates', path: '/workflow-templates' },
      { label: 'Billing & Plan', path: '/billing' },
      { label: 'Promo Codes', path: '/promo-codes' },
      { label: 'Production Workflow', path: '/settings/production' },
      { label: 'Backup & Restore', path: '/settings/backup' },
      { label: 'Onboarding', path: '/onboarding' },
    ]
  },
];

export const MobileNav = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { tenant } = useApp();
  const [expandedItem, setExpandedItem] = useState(null);

  const logoUrl = tenant?.logo_url || DEFAULT_LOGO;
  const logoAlt = tenant?.name || 'SignGuy AI';

  const handleNavClick = (item) => {
    if (item.children.length > 0) {
      // Has children: toggle expand, don't close nav
      setExpandedItem(expandedItem === item.id ? null : item.id);
    } else {
      // No children: navigate and close
      navigate(item.path);
      onClose();
    }
  };

  const handleChildClick = (path) => {
    navigate(path);
    onClose();
  };

  const toggleExpand = (e, itemId) => {
    e.stopPropagation();
    setExpandedItem(expandedItem === itemId ? null : itemId);
  };

  const isActive = (itemPath) => {
    const basePath = itemPath.split('?')[0];
    return location.pathname === basePath || location.pathname.startsWith(basePath + '/');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden" data-testid="mobile-nav">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="absolute inset-y-0 left-0 w-[280px] bg-[#0B0F17] border-r border-slate-800 flex flex-col shadow-2xl">
        {/* Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-slate-800">
          <img src={logoUrl} alt={logoAlt} className="h-6 w-auto max-w-[130px] object-contain" />
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-md transition-colors" data-testid="mobile-nav-close">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-2">
          {mobileNavItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            const expanded = expandedItem === item.id;
            const hasChildren = item.children.length > 0;

            return (
              <div key={item.id} data-testid={`mobile-nav-${item.id}`}>
                <div className="flex items-center">
                  <button
                    onClick={() => handleNavClick(item)}
                    className={cn(
                      "flex-1 flex items-center gap-3 px-4 py-3 text-sm transition-colors",
                      active 
                        ? "text-violet-400 bg-violet-500/10 font-medium" 
                        : "text-slate-300 hover:bg-slate-800/50"
                    )}
                  >
                    <Icon className={cn("h-5 w-5 flex-shrink-0", active ? "text-violet-400" : "text-slate-500")} />
                    <span>{item.label}</span>
                  </button>
                  {hasChildren && (
                    <button
                      onClick={(e) => toggleExpand(e, item.id)}
                      className="px-3 py-3 text-slate-500 hover:text-slate-300 transition-colors"
                      data-testid={`mobile-nav-expand-${item.id}`}
                    >
                      <ChevronDown className={cn("h-4 w-4 transition-transform", expanded && "rotate-180")} />
                    </button>
                  )}
                </div>

                {expanded && hasChildren && (
                  <div className="bg-slate-900/50 border-l-2 border-violet-500/30 ml-4">
                    {item.children.map((child, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleChildClick(child.path)}
                        className={cn(
                          "w-full flex items-center gap-2 px-4 pl-8 py-2.5 text-sm transition-colors",
                          isActive(child.path) ? "text-violet-400 font-medium" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                        )}
                        data-testid={`mobile-nav-child-${child.label.toLowerCase().replace(/\s+/g, '-')}`}
                      >
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-600 flex-shrink-0" />
                        <span>{child.label}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* User section */}
        <div className="border-t border-slate-800 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-violet-600 flex items-center justify-center text-white font-medium text-sm">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); onClose(); }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-md transition-colors"
            data-testid="mobile-nav-logout"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

export default MobileNav;
