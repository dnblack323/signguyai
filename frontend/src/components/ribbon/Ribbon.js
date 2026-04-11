import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings, ChevronDown, Menu
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { RibbonToolbar } from './RibbonToolbar';

// Ribbon tab configuration
const ribbonTabs = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'orders', label: 'Orders', icon: Briefcase },
  { id: 'quotes', label: 'Quotes', icon: FileText },
  { id: 'invoices', label: 'Invoices', icon: Receipt },
  { id: 'customers', label: 'Customers', icon: Users },
  { id: 'webstores', label: 'Webstores', icon: Store },
  { id: 'ai-tools', label: 'AI Tools', icon: Sparkles },
  { id: 'reports', label: 'Reports', icon: BarChart3 },
  { id: 'settings', label: 'Settings', icon: Settings },
];

// Map routes to their corresponding ribbon tabs
const routeToTab = {
  '/dashboard': 'home',
  '/jobs': 'jobs',
  '/quotes': 'quotes',
  '/invoices': 'invoices',
  '/customers': 'customers',
  '/webstores': 'webstores',
  '/products': 'webstores',
  '/promo-codes': 'settings',
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

export const Ribbon = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Sync active tab with current route
  useEffect(() => {
    const currentPath = location.pathname;
    const matchedTab = Object.entries(routeToTab).find(([route]) => 
      currentPath.startsWith(route)
    );
    if (matchedTab) {
      setActiveTab(matchedTab[1]);
    }
  }, [location.pathname]);

  // Handle tab click - just change toolbar, don't navigate
  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false);
  };

  // Navigate to a section's main page
  const navigateToSection = (tabId) => {
    const routes = {
      home: '/dashboard',
      jobs: '/jobs',
      quotes: '/quotes',
      invoices: '/invoices',
      customers: '/customers',
      webstores: '/webstores',
      'ai-tools': '/ai-tools',
      reports: '/financials',
      settings: '/settings',
    };
    navigate(routes[tabId] || '/dashboard');
  };

  return (
    <div 
      className="bg-[var(--surface)] border-b border-[var(--border-light)] shadow-sm"
      data-testid="ribbon"
    >
      {/* Ribbon Tabs Row */}
      <div className="flex items-center border-b border-[var(--border-light)]">
        {/* Desktop Tabs */}
        <div className="hidden lg:flex items-center pl-4 pr-2">
          {ribbonTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab.id)}
                onDoubleClick={() => navigateToSection(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all relative",
                  isActive 
                    ? "text-[var(--accent)] bg-white"
                    : "text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-2)]"
                )}
                data-testid={`ribbon-tab-${tab.id}`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--accent)]" />
                )}
              </button>
            );
          })}
        </div>

        {/* Mobile Tab Selector */}
        <div className="lg:hidden flex-1">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex items-center gap-2 px-4 py-3 w-full text-left"
            data-testid="mobile-tab-selector"
          >
            <Menu className="h-5 w-5 text-[var(--text-muted)]" />
            <span className="font-medium text-[var(--text)]">
              {ribbonTabs.find(t => t.id === activeTab)?.label || 'Home'}
            </span>
            <ChevronDown className={cn(
              "h-4 w-4 text-[var(--text-muted)] ml-auto transition-transform",
              mobileMenuOpen && "rotate-180"
            )} />
          </button>

          {/* Mobile Tab Dropdown */}
          {mobileMenuOpen && (
            <div className="absolute left-0 right-0 top-full bg-[var(--surface)] border-b border-[var(--border-light)] shadow-lg z-50 animate-fade-in">
              {ribbonTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabClick(tab.id)}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 w-full text-left transition-colors",
                      isActive 
                        ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                        : "text-[var(--text)] hover:bg-[var(--surface-2)]"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Ribbon Toolbar Row */}
      <div className="h-20 flex items-stretch">
        <RibbonToolbar activeTab={activeTab} />
      </div>
    </div>
  );
};

export default Ribbon;
