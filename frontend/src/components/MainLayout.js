import { useState, useRef, useEffect, useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt, 
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  Package, LogOut, User, Shield, ChevronRight, Menu, X, Crown
} from 'lucide-react';
import { Button } from './ui/button';
import { useAuth, Permission } from '../context/AuthContext';

// Navigation structure with categories, nested items, and required permissions
const navigationCategories = [
  {
    id: 'main',
    label: 'Main',
    icon: LayoutDashboard,
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    ]
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
      { name: 'Time Clock', href: '/timeclock', icon: Clock, permission: Permission.TIMECLOCK_VIEW_OWN },
      { name: 'Payroll', href: '/payroll', icon: DollarSign, permission: Permission.PAYROLL_VIEW },
      { name: 'Productivity', href: '/productivity', icon: CalendarDays },
      { name: 'Financials', href: '/financials', icon: DollarSign, permission: Permission.FINANCIALS_VIEW },
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
      { name: 'AI Tools', href: '/ai-tools', icon: Sparkles, permission: Permission.AI_TOOLS_USE },
    ]
  },
  {
    id: 'admin',
    label: 'Admin',
    icon: Shield,
    items: [
      { name: 'Users', href: '/users', icon: Shield, permission: Permission.USERS_VIEW },
    ]
  },
];

// Tooltip component
const Tooltip = ({ children, content, show }) => {
  if (!show) return children;
  
  return (
    <div className="relative group">
      {children}
      <div className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#2E2E2E] text-[#F2F2F2] text-xs font-medium rounded-md whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 shadow-lg">
        {content}
        <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-[#2E2E2E]" />
      </div>
    </div>
  );
};

export const Sidebar = () => {
  const { user, logout, hasPermission } = useAuth();
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
      const filteredItems = category.items.filter(item => {
        // If no permission required, show the item
        if (!item.permission) return true;
        // Check if user has the permission
        return hasPermission(item.permission);
      });
      
      return { ...category, items: filteredItems };
    }).filter(category => category.items.length > 0); // Remove empty categories
  }, [hasPermission]);

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

  const activeCategoryData = navigationCategories.find(c => c.id === activeCategory);

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
        <div className="flex h-16 items-center px-4 border-b border-white/10">
          <div className={cn(
            "flex items-center transition-all duration-300",
            isExpanded ? "gap-3" : "justify-center w-full"
          )}>
            <div className="w-8 h-8 rounded-lg bg-[#2F8BFB]/20 flex items-center justify-center flex-shrink-0 overflow-hidden">
              <img 
                src="https://customer-assets.emergentagent.com/job_cc25406f-f7f9-4d81-8429-039b5b2a7159/artifacts/dmeif3yx_1766814558812.png" 
                alt="SG" 
                className="h-7 w-auto object-contain"
              />
            </div>
            {isExpanded && (
              <span className="text-[#F2F2F2] font-semibold text-lg font-heading animate-fade-in whitespace-nowrap">
                SignGuy AI
              </span>
            )}
          </div>
        </div>

        {/* Navigation Categories */}
        <nav className="flex-1 py-4 overflow-y-auto">
          <div className="space-y-1 px-2">
            {navigationCategories.map((category) => {
              const Icon = category.icon;
              const isActive = currentActiveCategory === category.id;
              const isHovered = activeCategory === category.id;
              
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
                      isActive && !isHovered && "bg-[#2F8BFB] text-white",
                      isHovered && "bg-[#3A3A3A] text-white",
                      !isActive && !isHovered && "text-[#BDBDBD] hover:bg-[#3A3A3A] hover:text-[#F2F2F2]"
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
        <div className="border-t border-white/10 p-3 space-y-2">
          {user && (
            <>
              <div className={cn(
                "flex items-center rounded-lg bg-white/5 transition-all duration-200",
                isExpanded ? "gap-3 px-3 py-2" : "justify-center py-2"
              )}>
                <div className="w-8 h-8 rounded-full bg-[#2F8BFB]/20 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-[#2F8BFB]" />
                </div>
                {isExpanded && (
                  <div className="flex-1 min-w-0 animate-fade-in">
                    <p className="text-sm font-medium text-[#F2F2F2] truncate" data-testid="user-name">
                      {user.full_name}
                    </p>
                    <p className="text-xs text-[#BDBDBD] truncate">
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
          className="absolute left-64 w-56 bg-[#3A3A3A] rounded-lg shadow-xl border border-white/10 overflow-hidden animate-slide-in"
          style={{ top: flyoutPosition.top }}
          onMouseEnter={handleFlyoutEnter}
          onMouseLeave={handleNavLeave}
        >
          <div className="py-2">
            <div className="px-4 py-2 border-b border-white/10">
              <span className="text-xs font-semibold text-[#BDBDBD] uppercase tracking-wider">
                {activeCategoryData.label}
              </span>
            </div>
            {activeCategoryData.items.map((item) => {
              const ItemIcon = item.icon;
              const isItemActive = location.pathname === item.href;
              
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 text-sm transition-all duration-150",
                    isItemActive 
                      ? "bg-[#2F8BFB] text-white" 
                      : "text-[#F2F2F2] hover:bg-[#2F8BFB] hover:text-white"
                  )}
                >
                  <ItemIcon className="h-4 w-4" />
                  <span>{item.name}</span>
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
  const { user, logout } = useAuth();
  const location = useLocation();

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
          <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#2F8BFB]/20 flex items-center justify-center overflow-hidden">
                <img 
                  src="https://customer-assets.emergentagent.com/job_cc25406f-f7f9-4d81-8429-039b5b2a7159/artifacts/dmeif3yx_1766814558812.png" 
                  alt="SG" 
                  className="h-7 w-auto object-contain"
                />
              </div>
              <span className="text-[#F2F2F2] font-semibold text-lg font-heading">
                SignGuy AI
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-[#BDBDBD] hover:text-[#F2F2F2] hover:bg-white/10"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-4 overflow-y-auto">
            {navigationCategories.map((category) => (
              <div key={category.id} className="mb-4">
                <div className="px-4 py-2">
                  <span className="text-xs font-semibold text-[#BDBDBD] uppercase tracking-wider">
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
                            ? "bg-[#2F8BFB] text-white" 
                            : "text-[#BDBDBD] hover:bg-[#3A3A3A] hover:text-[#F2F2F2]"
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
            <div className="border-t border-white/10 p-4 space-y-3">
              <div className="flex items-center gap-3 px-2">
                <div className="w-10 h-10 rounded-full bg-[#2F8BFB]/20 flex items-center justify-center">
                  <User className="w-5 h-5 text-[#2F8BFB]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#F2F2F2] truncate">
                    {user.full_name}
                  </p>
                  <p className="text-xs text-[#BDBDBD] truncate">
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
  const location = useLocation();

  // Get current page title
  const getCurrentPageTitle = () => {
    for (const category of navigationCategories) {
      const item = category.items.find(i => i.href === location.pathname);
      if (item) return item.name;
    }
    return 'Dashboard';
  };

  const pageTitle = getCurrentPageTitle();

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--panel-bg)' }}>
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile Navigation */}
      <MobileNav isOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 z-30 app-header flex items-center px-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileOpen(true)}
          className="text-[#F2F2F2] hover:bg-white/10"
          data-testid="mobile-menu-toggle"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="ml-4 font-heading font-semibold text-lg text-[#F2F2F2]">
          {pageTitle}
        </h1>
      </header>

      {/* Main Content */}
      <main className="lg:pl-16 pt-16 lg:pt-0 min-h-screen">
        <div className="p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
