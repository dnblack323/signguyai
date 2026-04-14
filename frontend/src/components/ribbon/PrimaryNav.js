import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Briefcase, FileText, Receipt, Users, 
  Store, Sparkles, BarChart3, Settings, MessageCircle,
  Clock, DollarSign, FileCheck, Package, Tag, Calendar,
  ClipboardList, BookOpen, HelpCircle, UserCog, Wallet, Send,
  Shield, Wrench, Mail, FolderOpen, Clipboard
} from 'lucide-react';
import { cn } from '../../lib/utils';

// Primary navigation tabs - Office ribbon style grouped
const primaryNavItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'orders', label: 'Orders', icon: Package, path: '/orders' },
  { id: 'billing', label: 'Billing', icon: Receipt, path: '/invoices' },
  { id: 'customers', label: 'Customers', icon: Users, path: '/customers' },
  { id: 'webstores', label: 'Webstores', icon: Store, path: '/webstores' },
  { id: 'documents', label: 'Documents', icon: FolderOpen, path: '/documents' },
  { id: 'team', label: 'Team', icon: UserCog, path: '/payroll' },
  { id: 'ai-tools', label: 'AI Tools', icon: Sparkles, path: '/ai-tools' },
  { id: 'financials', label: 'Financials', icon: DollarSign, path: '/financials' },
  { id: 'productivity', label: 'Productivity', icon: BarChart3, path: '/productivity' },
  { id: 'reports', label: 'Reports', icon: BarChart3, path: '/financials' },
  { id: 'community', label: 'Community', icon: MessageCircle, path: '/community' },
  { id: 'settings', label: 'Settings', icon: Settings, path: '/settings' },
];

// Sub-navigation items per tab (shown in ActionToolbar)
export const tabSubItems = {
  orders: [
    { label: 'All Orders', icon: Package, path: '/orders' },
    { label: 'Production Board', icon: Wrench, path: '/production-board' },
    { label: 'Approvals', icon: FileCheck, path: '/approvals' },
  ],
  billing: [
    { label: 'Invoices', icon: Receipt, path: '/invoices' },
    { label: 'Payments', icon: DollarSign, path: '/admin/payments' },
    { label: 'Pricing', icon: Tag, path: '/pricing-calculator' },
    { label: 'Billing', icon: Wallet, path: '/billing' },
  ],
  customers: [
    { label: 'All Customers', icon: Users, path: '/customers' },
    { label: 'Admin Portal', icon: Send, path: '/admin-portal' },
  ],
  webstores: [
    { label: 'Stores', icon: Store, path: '/webstores' },
    { label: 'Products', icon: Package, path: '/products' },
  ],
  documents: [
    { label: 'Document Library', icon: FolderOpen, path: '/documents' },
    { label: 'Questionnaires', icon: ClipboardList, path: '/questionnaires' },
  ],
  team: [
    { label: 'Payroll', icon: DollarSign, path: '/payroll' },
    { label: 'Employee Schedule', icon: Calendar, path: '/payroll?tab=schedule' },
    { label: 'Time Clock', icon: Clock, path: '/timeclock' },
    { label: 'Users', icon: Users, path: '/users' },
  ],
  'ai-tools': [
    { label: 'AI Tools', icon: Sparkles, path: '/ai-tools' },
    { label: 'AI Assistant', icon: MessageCircle, path: '/ai-assistant' },
  ],
  financials: [
    { label: 'Daily Sales & Expenses', icon: DollarSign, path: '/financials' },
  ],
  productivity: [
    { label: 'Dashboard', icon: BarChart3, path: '/productivity?view=dashboard' },
    { label: 'Calendar', icon: Calendar, path: '/productivity?view=calendar' },
    { label: 'Kanban Board', icon: Clipboard, path: '/productivity?view=kanban' },
    { label: 'Task List', icon: ClipboardList, path: '/productivity?view=tasks' },
  ],
  reports: [
    { label: 'Profit & Margin Analytics', icon: BarChart3, path: '/reports/profit-margin' },
    { label: 'Sales Analytics', icon: DollarSign, path: '/financials' },
    { label: 'Webstore Analytics', icon: Store, path: '/webstores' },
  ],
  community: [
    { label: 'Community Hub', icon: MessageCircle, path: '/community' },
    { label: 'Documentation', icon: BookOpen, path: '/docs' },
    { label: 'Contact Support', icon: Mail, path: '/contact-support', href: 'mailto:donnell@signguy-ai.com?subject=SignGuy%20AI%20Support%20Request' },
  ],
  settings: [
    { label: 'Company', icon: Settings, path: '/settings' },
    { label: 'Pricing Foundation', icon: DollarSign, path: '/pricing-foundation' },
    { label: 'Import Invoices', icon: ClipboardList, path: '/settings/pricing-setup' },
    { label: 'Email Templates', icon: Mail, path: '/settings/email-templates' },
    { label: 'Daily Digest', icon: Send, path: '/settings/digest' },
    { label: 'Production', icon: Wrench, path: '/settings/production' },
    { label: 'Backup', icon: Shield, path: '/settings/backup' },
    { label: 'Users', icon: Users, path: '/users' },
  ],
};

// Route to nav item mapping
const routeToNavItem = {
  '/dashboard': 'dashboard',
  '/orders': 'orders',
  '/production-board': 'orders',
  '/job-tickets': 'orders',
  '/workflow-templates': 'settings',
  '/approvals': 'orders',
  '/jobs': 'orders',
  '/quotes': 'orders',
  '/settings/pricing-setup': 'settings',
  '/pricing-foundation': 'settings',
  '/invoices': 'billing',
  '/admin/payments': 'billing',
  '/pricing-calculator': 'billing',
  '/billing': 'billing',
  '/customers': 'customers',
  '/admin-portal': 'customers',
  '/webstores': 'webstores',
  '/products': 'webstores',
  '/promo-codes': 'settings',
  '/documents': 'documents',
  '/questionnaires': 'documents',
  '/payroll': 'team',
  '/timeclock': 'team',
  '/users': 'team',
  '/ai-tools': 'ai-tools',
  '/ai-assistant': 'ai-tools',
  '/financials': 'financials',
  '/reports': 'reports',
  '/reports/profit-margin': 'reports',
  '/productivity': 'productivity',
  '/community': 'community',
  '/docs': 'community',
  '/settings': 'settings',
  '/settings/digest': 'settings',
};

export const PrimaryNav = ({ activeTab, onTabChange }) => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const currentPath = location.pathname;
    const searchParams = new URLSearchParams(location.search);

    if (currentPath === '/productivity' && searchParams.get('view') === 'dashboard') {
      onTabChange?.('dashboard');
      return;
    }
    
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
      className="h-12 flex items-center px-4 bg-white border-b border-gray-100 overflow-x-auto scrollbar-none"
      data-testid="primary-nav"
    >
      <div className="flex items-center gap-0.5">
        {primaryNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item)}
              className={cn(
                "relative flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors rounded-md whitespace-nowrap",
                isActive 
                  ? "text-gray-900 bg-blue-50" 
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
              )}
              data-testid={`nav-${item.id}`}
            >
              <Icon className={cn(
                "h-3.5 w-3.5 flex-shrink-0",
                isActive ? "text-blue-600" : "text-gray-400"
              )} />
              <span>{item.label}</span>
              
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
