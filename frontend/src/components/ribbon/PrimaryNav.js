import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings
} from 'lucide-react';
import { cn } from '../../lib/utils';

// Primary navigation tabs - text first, subtle icons
const primaryNavItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'jobs', label: 'Jobs', icon: Briefcase, path: '/jobs' },
  { id: 'quotes', label: 'Quotes', icon: FileText, path: '/jobs?filter=quotes' },
  { id: 'invoices', label: 'Invoices', icon: Receipt, path: '/invoices' },
  { id: 'customers', label: 'Customers', icon: Users, path: '/customers' },
  { id: 'webstores', label: 'Webstores', icon: Store, path: '/webstores' },
  { id: 'ai-tools', label: 'AI Tools', icon: Sparkles, path: '/ai-tools' },
  { id: 'reports', label: 'Reports', icon: BarChart3, path: '/financials' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

// Route to nav item mapping
const routeToNavItem = {
  '/dashboard': 'dashboard',
  '/jobs': 'jobs',
  '/quotes': 'quotes',
  '/invoices': 'invoices',
  '/customers': 'customers',
  '/webstores': 'webstores',
  '/products': 'webstores',
  '/promo-codes': 'webstores',
  '/ai-tools': 'ai-tools',
  '/ai-assistant': 'ai-tools',
  '/approvals': 'ai-tools',
  '/documents': 'ai-tools',
  '/questionnaires': 'ai-tools',
  '/pricing-calculator': 'ai-tools',
  '/financials': 'reports',
  '/productivity': 'reports',
  '/timeclock': 'reports',
  '/payroll': 'reports',
  '/settings': 'settings',
  '/users': 'settings',
  '/billing': 'settings',
  '/admin/payments': 'settings',
};

export const PrimaryNav = ({ activeTab, onTabChange }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Sync active tab with current route
  useEffect(() => {
    const currentPath = location.pathname;
    const searchParams = new URLSearchParams(location.search);
    
    // Check for quotes filter
    if (currentPath === '/jobs' && searchParams.get('filter') === 'quotes') {
      onTabChange?.('quotes');
      return;
    }
    
    // Find matching nav item
    const matchedItem = Object.entries(routeToNavItem).find(([route]) => 
      currentPath.startsWith(route)
    );
    if (matchedItem) {
      onTabChange?.(matchedItem[1]);
    }
  }, [location, onTabChange]);

  const handleNavClick = (item) => {
    onTabChange?.(item.id);
    navigate(item.path);
  };

  return (
    <nav 
      className="h-12 flex items-center px-6 bg-white border-b border-gray-100"
      data-testid="primary-nav"
    >
      <div className="flex items-center gap-1">
        {primaryNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item)}
              className={cn(
                "relative flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors rounded-md",
                isActive 
                  ? "text-gray-900 bg-blue-50" 
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
              )}
              data-testid={`nav-${item.id}`}
            >
              <Icon className={cn(
                "h-4 w-4 flex-shrink-0",
                isActive ? "text-blue-600" : "text-gray-400"
              )} />
              <span>{item.label}</span>
              
              {/* Active indicator - bottom border */}
              {isActive && (
                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-blue-600 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default PrimaryNav;
