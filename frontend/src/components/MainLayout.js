import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt, 
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  ChevronLeft, ChevronRight, Menu
} from 'lucide-react';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import ThemeToggle from './ThemeToggle';
import { useTheme } from '../context/ThemeContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Customers', href: '/customers', icon: Users },
  { name: 'Quotes', href: '/quotes', icon: FileText },
  { name: 'Jobs', href: '/jobs', icon: Briefcase },
  { name: 'Invoices', href: '/invoices', icon: Receipt },
  { type: 'separator', label: 'Operations' },
  { name: 'Time Clock', href: '/timeclock', icon: Clock },
  { name: 'Payroll', href: '/payroll', icon: DollarSign },
  { name: 'Productivity', href: '/productivity', icon: CalendarDays },
  { name: 'Financials', href: '/financials', icon: DollarSign },
  { type: 'separator', label: 'Tools' },
  { name: 'AI Tools', href: '/ai-tools', icon: Sparkles },
  { name: 'Webstores', href: '/webstores', icon: Store },
];

export const Sidebar = ({ collapsed, onToggle }) => {
  const { theme } = useTheme();
  
  return (
    <aside 
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r border-border/50 transition-all duration-300",
        theme === 'dark' ? "bg-[#0F1115]" : "bg-white",
        collapsed ? "w-16" : "w-64"
      )}
      data-testid="sidebar"
    >
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <img 
                src="https://customer-assets.emergentagent.com/job_cc25406f-f7f9-4d81-8429-039b5b2a7159/artifacts/dmeif3yx_1766814558812.png" 
                alt="The Sign Guy PA" 
                className="h-10 w-auto"
              />
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 mx-auto rounded-md bg-primary/20 flex items-center justify-center overflow-hidden">
              <img 
                src="https://customer-assets.emergentagent.com/job_cc25406f-f7f9-4d81-8429-039b5b2a7159/artifacts/dmeif3yx_1766814558812.png" 
                alt="SG" 
                className="h-8 w-auto object-contain"
              />
            </div>
          )}
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 px-3 py-4">
          <nav className="space-y-1">
            {navigation.map((item, idx) => {
              if (item.type === 'separator') {
                return (
                  <div key={idx} className="pt-4 pb-2">
                    {!collapsed && (
                      <span className="px-3 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        {item.label}
                      </span>
                    )}
                    {collapsed && <Separator className="my-2" />}
                  </div>
                );
              }
              
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.href}
                  to={item.href}
                  data-testid={`nav-${item.name.toLowerCase().replace(' ', '-')}`}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      isActive
                        ? "bg-primary/10 text-primary border border-primary/30"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                      collapsed && "justify-center px-2"
                    )
                  }
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && <span>{item.name}</span>}
                </NavLink>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Theme Toggle & Collapse */}
        <div className="border-t border-border/50 p-3 space-y-2">
          <ThemeToggle collapsed={collapsed} />
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className={cn("w-full", collapsed && "px-2")}
            data-testid="sidebar-toggle"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            {!collapsed && <span className="ml-2">Collapse</span>}
          </Button>
        </div>
      </div>
    </aside>
  );
};

export const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { theme } = useTheme();

  // Get current page title
  const currentNav = navigation.find(n => n.href === location.pathname);
  const pageTitle = currentNav?.name || 'Dashboard';

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </div>

      {/* Mobile Header */}
      <div className={cn(
        "lg:hidden fixed top-0 left-0 right-0 h-16 border-b border-border z-50 flex items-center px-4",
        theme === 'dark' ? "bg-card" : "bg-white"
      )}>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileOpen(!mobileOpen)}
          data-testid="mobile-menu-toggle"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="ml-4 font-bold font-heading text-lg">{pageTitle}</span>
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div className={cn(
        "lg:hidden fixed left-0 top-0 z-50 h-full w-64 border-r border-border/50 transition-transform duration-300",
        theme === 'dark' ? "bg-[#0F1115]" : "bg-white",
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} />
      </div>

      {/* Main Content */}
      <main 
        className={cn(
          "min-h-screen transition-all duration-300 pt-16 lg:pt-0",
          collapsed ? "lg:pl-16" : "lg:pl-64"
        )}
      >
        <div className="p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
