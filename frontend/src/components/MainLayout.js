import { useState, useRef, useEffect, useMemo } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt, 
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  Package, LogOut, User, Shield, ChevronRight, Menu, X, Crown, Building2, Settings,
  Eye, ExternalLink, ChevronDown, Lock, Zap, Globe, Ticket
} from 'lucide-react';
import { Button } from './ui/button';
import { useAuth, Permission } from '../context/AuthContext';
import { useTier } from '../context/TierContext';
import { TierBadge } from './UpgradeModal';
import { TrialCountdown } from './TrialLockout';

// Navigation structure with categories, nested items, required permissions, and tier features
const navigationCategories = [
  {
    id: 'home',
    label: 'Home',
    icon: LayoutDashboard,
    isDirectLink: true,  // Special flag for direct navigation
    href: '/',
    items: []
  },
  {
    id: 'sales',
    label: 'Sales',
    icon: FileText,
    items: [
      { name: 'Customers', href: '/customers', icon: Users, permission: Permission.CUSTOMERS_VIEW },
      { name: 'Quotes', href: '/quotes', icon: FileText, permission: Permission.QUOTES_VIEW },
      { name: 'Jobs', href: '/jobs', icon: Briefcase, permission: Permission.JOBS_VIEW },
      { name: 'Invoices', href: '/invoices', icon: Receipt, permission: Permission.INVOICES_VIEW },
    ]
  },
  {
    id: 'operations',
    label: 'Operations',
    icon: Clock,
    items: [
      { name: 'Time Clock', href: '/timeclock', icon: Clock, permission: Permission.TIMECLOCK_VIEW_OWN, tierFeature: { category: 'core_modules', feature: 'time_clock' } },
      { name: 'Payroll', href: '/payroll', icon: DollarSign, permission: Permission.PAYROLL_VIEW, tierFeature: { category: 'core_modules', feature: 'payroll' } },
      { name: 'Productivity', href: '/productivity', icon: CalendarDays },
      { name: 'Financials', href: '/financials', icon: DollarSign, permission: Permission.FINANCIALS_VIEW, tierFeature: { category: 'core_modules', feature: 'financial_tracking' } },
    ]
  },
  {
    id: 'webstores',
    label: 'Webstores',
    icon: Store,
    items: [
      { name: 'Webstores', href: '/webstores', icon: Store, permission: Permission.WEBSTORES_VIEW },
      { name: 'Products', href: '/products', icon: Package, permission: Permission.WEBSTORES_VIEW },
    ]
  },
  {
    id: 'tools',
    label: 'Tools',
    icon: Sparkles,
    items: [
      { name: 'AI Tools', href: '/ai-tools', icon: Sparkles },
      { name: 'Pricing Calculator', href: '/pricing-calculator', icon: DollarSign },
    ]
  },
  {
    id: 'admin',
    label: 'Admin',
    icon: Shield,
    items: [
      { name: 'Users', href: '/users', icon: Shield, permission: Permission.USERS_VIEW },
      { name: 'Company Settings', href: '/settings', icon: Building2, permission: Permission.SETTINGS_VIEW },
      { name: 'Promo Codes', href: '/promo-codes', icon: Ticket, permission: Permission.SETTINGS_VIEW },
      { name: 'Pricing Settings', href: '/pricing-calculator/settings', icon: DollarSign, permission: Permission.SETTINGS_VIEW },
    ]
  },
];

// Tooltip component
const Tooltip = ({ children, content, show }) => {
  if (!show) return children;
  
  return (
    <div className="relative group">
      {children}
      <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[var(--sidebar)] text-[var(--text-on-dark)] text-xs font-medium rounded-md whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 shadow-lg">
        {content}
        <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-[var(--sidebar)]" />
      </div>
    </div>
  );
};

export const Sidebar = () => {
  const { user, logout, hasPermission } = useAuth();
  const { checkFeature, requireFeature, tier } = useTier();
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeCategory, setActiveCategory] = useState(null);
  const [flyoutPosition, setFlyoutPosition] = useState({ top: 0 });
  const hoverTimeoutRef = useRef(null);
  const navRef = useRef(null);
  const categoryRefs = useRef({});

  // Filter navigation based on permissions
  const filteredNavigation = useMemo(() => {
    return navigationCategories.map(category => {
      // Keep direct link items (like Home) as-is
      if (category.isDirectLink) {
        return category;
      }
      
      const filteredItems = category.items.filter(item => {
        // If no permission required, show the item
        if (!item.permission) return true;
        // Check if user has the permission
        return hasPermission(item.permission);
      }).map(item => {
        // Add tier check info
        if (item.tierFeature) {
          const tierCheck = checkFeature(item.tierFeature.category, item.tierFeature.feature);
          return { ...item, tierLocked: !tierCheck.allowed, tierStatus: tierCheck.status };
        }
        return item;
      });
      
      return { ...category, items: filteredItems };
    }).filter(category => category.isDirectLink || category.items.length > 0); // Keep direct links and non-empty categories
  }, [hasPermission, checkFeature]);

  // Find active category based on current path
  const findActiveCategory = () => {
    for (const category of filteredNavigation) {
      if (category.items.some(item => item.href === location.pathname)) {
        return category.id;
      }
    }
    return null;
  };

  const currentActiveCategory = findActiveCategory();

  // Handle mouse enter on nav
  const handleNavEnter = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    hoverTimeoutRef.current = setTimeout(() => {
      setIsExpanded(true);
    }, 150);
  };

  // Handle mouse leave on nav
  const handleNavLeave = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    hoverTimeoutRef.current = setTimeout(() => {
      setIsExpanded(false);
      setActiveCategory(null);
    }, 200);
  };

  // Handle category hover
  const handleCategoryEnter = (categoryId) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
    
    // Calculate flyout position
    const categoryEl = categoryRefs.current[categoryId];
    if (categoryEl && navRef.current) {
      const navRect = navRef.current.getBoundingClientRect();
      const catRect = categoryEl.getBoundingClientRect();
      setFlyoutPosition({
        top: catRect.top - navRect.top,
      });
    }
    
    setActiveCategory(categoryId);
  };

  // Handle flyout mouse enter
  const handleFlyoutEnter = () => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, []);

  // Close flyout on navigation
  useEffect(() => {
    setActiveCategory(null);
    setIsExpanded(false);
  }, [location.pathname]);

  const activeCategoryData = filteredNavigation.find(c => c.id === activeCategory);

  // Get role badge color
  const getRoleBadgeColor = () => {
    if (user?.role === 'owner') return '#d97706'; // amber
    if (user?.role === 'admin') return '#2F8BFB'; // blue
    return '#5A5A5A'; // gray for staff
  };

  return (
    <aside
      ref={navRef}
      className={cn(
        "fixed left-0 top-0 z-40 h-screen transition-all duration-300 ease-out nav-shell",
        isExpanded ? "w-64" : "w-16"
      )}
      onMouseEnter={handleNavEnter}
      onMouseLeave={handleNavLeave}
      data-testid="sidebar"
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center px-4 border-b border-[var(--border-dark)]">
          <div className={cn(
            "flex items-center transition-all duration-300",
            isExpanded ? "gap-3" : "justify-center w-full"
          )}>
            {isExpanded ? (
              /* Long logo when expanded */
              <img 
                src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
                alt="SignGuy AI" 
                className="h-10 w-auto object-contain"
              />
            ) : (
              /* Square logo when collapsed */
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                <img 
                  src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/zofnt5d0_sgai%20square.png" 
                  alt="SG" 
                  className="h-8 w-auto object-contain"
                />
              </div>
            )}
          </div>
        </div>

        {/* Navigation Categories */}
        <nav className="flex-1 py-4 overflow-y-auto">
          <div className="space-y-1 px-2">
            {filteredNavigation.map((category) => {
              const Icon = category.icon;
              const isActive = currentActiveCategory === category.id || (category.isDirectLink && location.pathname === category.href);
              const isHovered = activeCategory === category.id;
              
              // Handle direct link items (like Home)
              if (category.isDirectLink) {
                return (
                  <Tooltip 
                    key={category.id} 
                    content={category.label}
                    show={!isExpanded}
                  >
                    <NavLink
                      to={category.href}
                      className={cn(
                        "flex items-center rounded-lg cursor-pointer transition-all duration-200",
                        isExpanded ? "px-3 py-2.5 gap-3" : "justify-center py-2.5",
                        isActive && "bg-[var(--accent)] text-white",
                        !isActive && "text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--text-on-dark)]"
                      )}
                      data-testid={`nav-${category.id}`}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      {isExpanded && (
                        <span className="flex-1 font-medium text-sm">{category.label}</span>
                      )}
                    </NavLink>
                  </Tooltip>
                );
              }
              
              return (
                <Tooltip 
                  key={category.id} 
                  content={category.label}
                  show={!isExpanded}
                >
                  <div
                    ref={el => categoryRefs.current[category.id] = el}
                    className={cn(
                      "flex items-center rounded-lg cursor-pointer transition-all duration-200",
                      isExpanded ? "px-3 py-2.5 gap-3" : "justify-center py-2.5",
                      isActive && !isHovered && "bg-[var(--accent)] text-white",
                      isHovered && "bg-[var(--sidebar-hover)] text-[var(--text-on-dark)]",
                      !isActive && !isHovered && "text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--text-on-dark)]"
                    )}
                    onMouseEnter={() => isExpanded && handleCategoryEnter(category.id)}
                    data-testid={`nav-category-${category.id}`}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {isExpanded && (
                      <>
                        <span className="flex-1 font-medium text-sm">{category.label}</span>
                        <ChevronRight className={cn(
                          "h-4 w-4 transition-transform duration-200",
                          isHovered && "rotate-90"
                        )} />
                      </>
                    )}
                  </div>
                </Tooltip>
              );
            })}
          </div>
        </nav>

        {/* User Section */}
        <div className="border-t border-[var(--border-dark)] p-3 space-y-2">
          {/* Tier Badge */}
          {isExpanded && (
            <div className="px-1 pb-2">
              <TierBadge size="sm" />
            </div>
          )}
          {!isExpanded && (
            <Tooltip content={`${tier?.charAt(0).toUpperCase() + tier?.slice(1) || 'Starter'} Plan`} show={true}>
              <div className="flex justify-center py-1">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
            </Tooltip>
          )}
          
          {user && (
            <>
              <div className={cn(
                "flex items-center rounded-lg bg-[var(--sidebar-hover)] transition-all duration-200",
                isExpanded ? "gap-3 px-3 py-2" : "justify-center py-2"
              )}>
                <div className="w-8 h-8 rounded-full bg-[var(--accent)]/20 flex items-center justify-center flex-shrink-0">
                  {user.role === 'owner' ? (
                    <Crown className="w-4 h-4" style={{ color: '#d97706' }} />
                  ) : (
                    <User className="w-4 h-4 text-[var(--accent)]" />
                  )}
                </div>
                {isExpanded && (
                  <div className="flex-1 min-w-0 animate-fade-in">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-[var(--text-on-dark)] truncate" data-testid="user-name">
                        {user.full_name}
                      </p>
                      <span 
                        className="text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold"
                        style={{ 
                          backgroundColor: `${getRoleBadgeColor()}20`,
                          color: getRoleBadgeColor()
                        }}
                      >
                        {user.role}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-muted-on-dark)] truncate">
                      {user.company_name || user.email}
                    </p>
                  </div>
                )}
              </div>
              
              <Tooltip content="Sign Out" show={!isExpanded}>
                <button
                  onClick={logout}
                  data-testid="logout-btn"
                  className={cn(
                    "flex items-center rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all duration-200 w-full",
                    isExpanded ? "gap-3 px-3 py-2" : "justify-center py-2"
                  )}
                >
                  <LogOut className="h-5 w-5 flex-shrink-0" />
                  {isExpanded && <span className="font-medium text-sm">Sign Out</span>}
                </button>
              </Tooltip>
            </>
          )}
        </div>
      </div>

      {/* Flyout Submenu */}
      {isExpanded && activeCategory && activeCategoryData && (
        <div
          className="absolute left-64 w-56 bg-[var(--sidebar-hover)] rounded-lg shadow-xl border border-[var(--border-dark)] overflow-hidden animate-slide-in"
          style={{ top: flyoutPosition.top }}
          onMouseEnter={handleFlyoutEnter}
          onMouseLeave={handleNavLeave}
        >
          <div className="py-2">
            <div className="px-4 py-2 border-b border-[var(--border-dark)]">
              <span className="text-xs font-semibold text-[var(--text-muted-on-dark)] uppercase tracking-wider">
                {activeCategoryData.label}
              </span>
            </div>
            {activeCategoryData.items.map((item) => {
              const ItemIcon = item.icon;
              const isItemActive = location.pathname === item.href;
              const isLocked = item.tierLocked;
              
              const handleClick = (e) => {
                if (isLocked && item.tierFeature) {
                  e.preventDefault();
                  requireFeature(item.tierFeature.category, item.tierFeature.feature);
                }
              };
              
              return (
                <NavLink
                  key={item.href}
                  to={isLocked ? '#' : item.href}
                  onClick={handleClick}
                  data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 text-sm transition-all duration-150",
                    isLocked && "opacity-60 cursor-pointer",
                    isItemActive && !isLocked
                      ? "bg-[var(--accent)] text-white" 
                      : isLocked
                      ? "text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar)]"
                      : "text-[var(--text-on-dark)] hover:bg-[var(--accent)] hover:text-white"
                  )}
                >
                  <ItemIcon className="h-4 w-4" />
                  <span className="flex-1">{item.name}</span>
                  {isLocked && (
                    <Lock className="h-3.5 w-3.5 text-amber-500" />
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      )}
    </aside>
  );
};

// Mobile Navigation
export const MobileNav = ({ isOpen, onClose }) => {
  const { user, logout, hasPermission } = useAuth();
  const location = useLocation();

  // Filter navigation based on permissions
  const filteredNavigation = useMemo(() => {
    return navigationCategories.map(category => {
      const filteredItems = category.items.filter(item => {
        if (!item.permission) return true;
        return hasPermission(item.permission);
      });
      return { ...category, items: filteredItems };
    }).filter(category => category.items.length > 0);
  }, [hasPermission]);

  // Close on navigation
  useEffect(() => {
    onClose();
  }, [location.pathname, onClose]);

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Mobile Menu */}
      <div className={cn(
        "fixed left-0 top-0 h-full w-72 z-50 nav-shell transform transition-transform duration-300 lg:hidden",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-[var(--border-dark)]">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden">
                <img 
                  src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/zofnt5d0_sgai%20square.png" 
                  alt="SG" 
                  className="h-8 w-auto object-contain"
                />
              </div>
              <span className="text-[var(--text-on-dark)] font-semibold text-lg font-heading">
                SignGuy AI
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-[var(--text-muted-on-dark)] hover:text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)]"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-4 overflow-y-auto">
            {filteredNavigation.map((category) => (
              <div key={category.id} className="mb-4">
                <div className="px-4 py-2">
                  <span className="text-xs font-semibold text-[var(--text-muted-on-dark)] uppercase tracking-wider">
                    {category.label}
                  </span>
                </div>
                <div className="space-y-1 px-2">
                  {category.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.href;
                    
                    return (
                      <NavLink
                        key={item.href}
                        to={item.href}
                        className={cn(
                          "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                          isActive 
                            ? "bg-[var(--accent)] text-white" 
                            : "text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--text-on-dark)]"
                        )}
                      >
                        <Icon className="h-5 w-5" />
                        <span>{item.name}</span>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>

          {/* User Section */}
          {user && (
            <div className="border-t border-[var(--border-dark)] p-4 space-y-3">
              <div className="flex items-center gap-3 px-2">
                <div className="w-10 h-10 rounded-full bg-[var(--accent)]/20 flex items-center justify-center">
                  <User className="w-5 h-5 text-[var(--accent)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text-on-dark)] truncate">
                    {user.full_name}
                  </p>
                  <p className="text-xs text-[var(--text-muted-on-dark)] truncate">
                    {user.company_name || user.email}
                  </p>
                </div>
              </div>
              
              <button
                onClick={logout}
                className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all duration-200"
              >
                <LogOut className="h-5 w-5" />
                <span className="font-medium text-sm">Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export const MainLayout = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewTier, setPreviewTier] = useState(() => localStorage.getItem('preview_tier') || 'tier3');
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Only show preview mode in development OR for founder accounts
  // This prevents regular customers from seeing/using the tier selector
  const isDevelopment = process.env.NODE_ENV === 'development' || 
                        window.location.hostname.includes('preview.emergentagent.com') ||
                        window.location.hostname === 'localhost';
  const isFounder = user?.is_founder === true;
  const showPreviewMode = isDevelopment || isFounder;

  // Save preview tier to localStorage
  useEffect(() => {
    localStorage.setItem('preview_tier', previewTier);
  }, [previewTier]);

  // Get current page title
  const getCurrentPageTitle = () => {
    for (const category of navigationCategories) {
      const item = category.items.find(i => i.href === location.pathname);
      if (item) return item.name;
    }
    return 'Dashboard';
  };

  const pageTitle = getCurrentPageTitle();

  const tierLabels = {
    tier1: { name: 'Starter (Free)', color: 'bg-slate-500' },
    tier2: { name: 'Pro', color: 'bg-blue-500' },
    tier3: { name: 'Business', color: 'bg-amber-500' }
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg)' }}>
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Navigation */}
      <MobileNav isOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 z-30 app-header flex items-center justify-between px-4">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(true)}
            className="text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)]"
            data-testid="mobile-menu-toggle"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <h1 className="ml-4 font-heading font-semibold text-lg text-[var(--text-on-dark)]">
            {pageTitle}
          </h1>
        </div>
        <TrialCountdown />
      </header>

      {/* Desktop Trial Countdown - Fixed top right */}
      <div className="hidden lg:block fixed top-4 right-4 z-40">
        <TrialCountdown />
      </div>

      {/* Main Content */}
      <main className="lg:pl-16 pt-16 lg:pt-0 min-h-screen">
        <div className="p-6 lg:p-8">
          {/* Content wrapper with light surface */}
          <div className="bg-[var(--surface)] rounded-2xl p-6 lg:p-8 min-h-[calc(100vh-4rem)] shadow-sm">
            {children}
          </div>
        </div>
      </main>

      {/* Marketing Site Link - Fixed Bottom Right */}
      <div className="fixed bottom-16 right-4 z-50 flex items-center gap-2">
        {/* Visit Marketing Site */}
        <a
          href="/home"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#00D4FF]/20 border border-[#00D4FF]/30 text-[#00D4FF] hover:bg-[#00D4FF]/30 transition-all shadow-lg"
          data-testid="marketing-site-link"
        >
          <Globe className="h-4 w-4" />
          <span className="text-sm font-medium">View Website</span>
          <ExternalLink className="h-3 w-3" />
        </a>

        {/* Preview Mode Panel */}
        {previewOpen ? (
          <div className="bg-[var(--sidebar)] border border-[var(--border-dark)] rounded-xl shadow-2xl w-72 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-[var(--border-dark)] bg-[var(--accent)]/20">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-[var(--accent)]" />
                <span className="text-sm font-semibold text-[var(--text-on-dark)]">Preview Mode</span>
              </div>
              <button 
                onClick={() => setPreviewOpen(false)}
                className="text-[var(--text-muted-on-dark)] hover:text-[var(--text-on-dark)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Tier Selection */}
            <div className="p-3 space-y-3">
              <div>
                <label className="text-xs font-medium text-[var(--text-muted-on-dark)] uppercase tracking-wide">Subscription Tier</label>
                <div className="mt-2 space-y-1">
                  {Object.entries(tierLabels).map(([tier, { name, color }]) => (
                    <button
                      key={tier}
                      onClick={() => setPreviewTier(tier)}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all",
                        previewTier === tier 
                          ? "bg-[var(--sidebar-hover)] ring-1 ring-[var(--accent)]" 
                          : "hover:bg-[var(--sidebar-hover)]"
                      )}
                    >
                      <div className={cn("w-3 h-3 rounded-full", color)} />
                      <span className="text-sm text-[var(--text-on-dark)]">{name}</span>
                      {previewTier === tier && (
                        <span className="ml-auto text-xs text-[var(--accent)]">Active</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Links */}
              <div className="pt-2 border-t border-[var(--border-dark)]">
                <label className="text-xs font-medium text-[var(--text-muted-on-dark)] uppercase tracking-wide">Quick Access</label>
                <div className="mt-2 space-y-1">
                  <button
                    onClick={() => window.open('/customer-portal/login', '_blank')}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left hover:bg-[var(--sidebar-hover)] transition-all"
                  >
                    <User className="h-4 w-4 text-teal-400" />
                    <span className="text-sm text-[var(--text-on-dark)]">Customer Portal</span>
                    <ExternalLink className="h-3 w-3 ml-auto text-[var(--text-muted-on-dark)]" />
                  </button>
                  <button
                    onClick={() => window.open('/employee-portal/login', '_blank')}
                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left hover:bg-[var(--sidebar-hover)] transition-all"
                  >
                    <Clock className="h-4 w-4 text-purple-400" />
                    <span className="text-sm text-[var(--text-on-dark)]">Employee Portal</span>
                    <ExternalLink className="h-3 w-3 ml-auto text-[var(--text-muted-on-dark)]" />
                  </button>
                </div>
              </div>

              {/* Current Tier Info */}
              <div className="pt-2 border-t border-[var(--border-dark)]">
                <div className="flex items-center gap-2 px-3 py-2 bg-[var(--sidebar-hover)] rounded-lg">
                  <div className={cn("w-2 h-2 rounded-full", tierLabels[previewTier].color)} />
                  <span className="text-xs text-[var(--text-muted-on-dark)]">
                    Viewing as: <span className="text-[var(--text-on-dark)] font-medium">{tierLabels[previewTier].name}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setPreviewOpen(true)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-full shadow-lg transition-all hover:scale-105",
              tierLabels[previewTier].color
            )}
            data-testid="preview-mode-toggle"
          >
            <Eye className="h-4 w-4 text-white" />
            <span className="text-sm font-medium text-white">{tierLabels[previewTier].name}</span>
            <ChevronDown className="h-3 w-3 text-white/80" />
          </button>
        )}
      </div>
    </div>
  );
};

export default MainLayout;
