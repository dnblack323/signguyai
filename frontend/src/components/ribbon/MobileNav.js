import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  X, LayoutDashboard, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings, ChevronRight, LogOut,
  Plus, Calendar, Package, TrendingUp, CreditCard
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';

const mobileNavItems = [
  { 
    id: 'dashboard', 
    label: 'Dashboard', 
    icon: LayoutDashboard, 
    path: '/dashboard',
    actions: []
  },
  { 
    id: 'jobs', 
    label: 'Jobs', 
    icon: Briefcase, 
    path: '/jobs',
    actions: [
      { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
    ]
  },
  { 
    id: 'quotes', 
    label: 'Quotes', 
    icon: FileText, 
    path: '/jobs?filter=quotes',
    actions: [
      { icon: Plus, label: 'New Quote', route: '/jobs?new=true&type=quote' },
    ]
  },
  { 
    id: 'invoices', 
    label: 'Invoices', 
    icon: Receipt, 
    path: '/invoices',
    actions: [
      { icon: Plus, label: 'New Invoice', route: '/invoices?new=true' },
    ]
  },
  { 
    id: 'customers', 
    label: 'Customers', 
    icon: Users, 
    path: '/customers',
    actions: []
  },
  { 
    id: 'webstores', 
    label: 'Webstores', 
    icon: Store, 
    path: '/webstores',
    actions: [
      { icon: Package, label: 'Products', route: '/products' },
    ]
  },
  { 
    id: 'ai-tools', 
    label: 'AI Tools', 
    icon: Sparkles, 
    path: '/ai-tools',
    actions: [
      { icon: TrendingUp, label: 'Pricing Calculator', route: '/pricing-calculator' },
    ]
  },
  { 
    id: 'reports', 
    label: 'Reports', 
    icon: BarChart3, 
    path: '/financials',
    actions: [
      { icon: Calendar, label: 'Productivity', route: '/productivity' },
    ]
  },
  { 
    id: 'settings', 
    label: 'Settings', 
    icon: Settings, 
    path: '/settings',
    actions: [
      { icon: CreditCard, label: 'Billing', route: '/billing' },
    ]
  },
];

export const MobileNav = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [expandedItem, setExpandedItem] = useState(null);

  const handleNavClick = (item) => {
    if (item.actions.length > 0) {
      setExpandedItem(expandedItem === item.id ? null : item.id);
    } else {
      navigate(item.path);
      onClose();
    }
  };

  const handleActionClick = (route) => {
    navigate(route);
    onClose();
  };

  const isActive = (item) => {
    if (item.id === 'quotes') {
      return location.pathname === '/jobs' && location.search.includes('filter=quotes');
    }
    return location.pathname.startsWith(item.path.split('?')[0]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Slide-out panel */}
      <div className="absolute inset-y-0 left-0 w-72 bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          <img 
            src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
            alt="SignGuy AI" 
            className="h-7 w-auto"
          />
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-4">
          {mobileNavItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            const expanded = expandedItem === item.id;

            return (
              <div key={item.id}>
                <button
                  onClick={() => handleNavClick(item)}
                  className={cn(
                    "w-full flex items-center justify-between px-4 py-3 text-sm transition-colors",
                    active 
                      ? "text-blue-600 bg-blue-50 font-medium" 
                      : "text-gray-700 hover:bg-gray-50"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={cn(
                      "h-5 w-5",
                      active ? "text-blue-600" : "text-gray-400"
                    )} />
                    <span>{item.label}</span>
                  </div>
                  {item.actions.length > 0 && (
                    <ChevronRight className={cn(
                      "h-4 w-4 text-gray-400 transition-transform",
                      expanded && "rotate-90"
                    )} />
                  )}
                </button>

                {/* Expanded actions */}
                {expanded && item.actions.length > 0 && (
                  <div className="bg-gray-50 py-1">
                    {item.actions.map((action, idx) => {
                      const ActionIcon = action.icon;
                      return (
                        <button
                          key={idx}
                          onClick={() => handleActionClick(action.route)}
                          className="w-full flex items-center gap-3 px-4 pl-12 py-2.5 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
                        >
                          <ActionIcon className="h-4 w-4 text-gray-400" />
                          <span>{action.label}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* User section */}
        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); onClose(); }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors"
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
