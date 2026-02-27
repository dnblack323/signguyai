import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Search, Bell, HelpCircle, User, ChevronRight, 
  LogOut, Settings, CreditCard, Menu, LayoutDashboard,
  FileDown, Upload, Building2, Users, Folder
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { DropdownMenu } from './DropdownMenu';

export const TopAppBar = ({ onMobileMenuClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Generate breadcrumbs from current path
  const getBreadcrumbs = () => {
    const pathSegments = location.pathname.split('/').filter(Boolean);
    if (pathSegments.length <= 1) return null;

    const breadcrumbs = pathSegments.map((segment, index) => {
      const path = '/' + pathSegments.slice(0, index + 1).join('/');
      const label = segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ');
      return { label, path };
    });

    return breadcrumbs;
  };

  const breadcrumbs = getBreadcrumbs();

  // File menu items
  const fileMenuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', onClick: () => navigate('/dashboard') },
    { separator: true },
    { icon: Building2, label: 'Company Settings', onClick: () => navigate('/settings') },
    { icon: CreditCard, label: 'Billing', onClick: () => navigate('/billing') },
    { icon: Users, label: 'Users', onClick: () => navigate('/users') },
    { separator: true },
    { icon: Upload, label: 'Import Data', onClick: () => {} },
    { icon: FileDown, label: 'Export Data', onClick: () => {} },
    { separator: true },
    { icon: LogOut, label: 'Logout', onClick: logout, danger: true },
  ];

  // Profile menu items
  const profileMenuItems = [
    { icon: User, label: 'Account Settings', onClick: () => navigate('/settings') },
    { icon: Settings, label: 'Preferences', onClick: () => navigate('/settings') },
    { separator: true },
    { icon: LogOut, label: 'Sign Out', onClick: logout, danger: true },
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Implement global search
      console.log('Searching for:', searchQuery);
    }
  };

  return (
    <div 
      className="h-14 flex items-center justify-between px-4 bg-[var(--sidebar)] border-b border-[var(--border-dark)]"
      data-testid="top-app-bar"
    >
      {/* Left Section: File Menu + Logo */}
      <div className="flex items-center gap-4">
        {/* Mobile Menu Button */}
        <button
          onClick={onMobileMenuClick}
          className="lg:hidden p-2 text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)] rounded-md"
          data-testid="mobile-menu-btn"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* File Menu */}
        <div className="hidden lg:block">
          <DropdownMenu
            trigger={{ icon: Folder, label: 'File' }}
            items={fileMenuItems}
            triggerClassName="px-3 py-1.5 text-sm text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)] rounded-md"
          />
        </div>

        {/* Logo - Click to go to Dashboard */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          data-testid="logo-home-btn"
        >
          <img 
            src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
            alt="SignGuy AI" 
            className="h-8 w-auto object-contain"
          />
        </button>

        {/* Breadcrumbs - Desktop only, when on sub-pages */}
        {breadcrumbs && breadcrumbs.length > 1 && (
          <div className="hidden lg:flex items-center gap-1 ml-4 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.path} className="flex items-center gap-1">
                {index > 0 && <ChevronRight className="h-3 w-3 text-[var(--text-muted-on-dark)]" />}
                <button
                  onClick={() => navigate(crumb.path)}
                  className={cn(
                    "hover:text-[var(--accent)] transition-colors",
                    index === breadcrumbs.length - 1 
                      ? "text-[var(--text-on-dark)] font-medium"
                      : "text-[var(--text-muted-on-dark)]"
                  )}
                >
                  {crumb.label}
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Right Section: Search, Notifications, Help, Profile */}
      <div className="flex items-center gap-2">
        {/* Search */}
        <div className="relative">
          {searchOpen ? (
            <form onSubmit={handleSearch} className="flex items-center">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                autoFocus
                onBlur={() => !searchQuery && setSearchOpen(false)}
                className="w-48 px-3 py-1.5 text-sm bg-[var(--sidebar-hover)] text-[var(--text-on-dark)] border border-[var(--border-dark)] rounded-md focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
                data-testid="search-input"
              />
            </form>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="p-2 text-[var(--text-muted-on-dark)] hover:text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)] rounded-md transition-colors"
              data-testid="search-btn"
            >
              <Search className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Notifications */}
        <button
          className="p-2 text-[var(--text-muted-on-dark)] hover:text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)] rounded-md transition-colors relative"
          data-testid="notifications-btn"
        >
          <Bell className="h-5 w-5" />
          {/* Notification badge - uncomment when implementing notifications
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          */}
        </button>

        {/* Help */}
        <button
          onClick={() => window.open('/docs', '_blank')}
          className="p-2 text-[var(--text-muted-on-dark)] hover:text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)] rounded-md transition-colors"
          data-testid="help-btn"
        >
          <HelpCircle className="h-5 w-5" />
        </button>

        {/* Profile Dropdown */}
        <DropdownMenu
          trigger={{ 
            icon: () => (
              <div className="w-8 h-8 rounded-full bg-[var(--accent)] flex items-center justify-center text-white text-sm font-medium">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
            )
          }}
          items={profileMenuItems}
          align="right"
          triggerClassName="p-1 hover:bg-[var(--sidebar-hover)] rounded-full"
        />
      </div>
    </div>
  );
};

export default TopAppBar;
