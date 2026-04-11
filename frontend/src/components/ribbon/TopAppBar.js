import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, HelpCircle, LogOut, Settings, User, ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { CreditBalance } from '../credits/CreditBalance';

// Default SignGuy AI logo
const DEFAULT_LOGO = "https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png";

export const TopAppBar = ({ onMobileMenuClick }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { tenant } = useApp();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [profileOpen, setProfileOpen] = useState(false);
  const logoUrl = tenant?.logo_url || DEFAULT_LOGO;
  const logoAlt = tenant?.name || 'SignGuy AI';

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      console.log('Searching for:', searchQuery);
    }
  };

  return (
    <div 
      className="h-16 flex items-center justify-between px-6"
      style={{ backgroundColor: '#0f172a' }}
      data-testid="top-app-bar"
    >
      {/* Left: Logo */}
      <div className="flex items-center">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center hover:opacity-80 transition-opacity"
          data-testid="logo-home-btn"
        >
          <img 
            src={logoUrl} 
            alt={logoAlt} 
            className="h-24 w-auto object-contain max-w-[300px]"
          />
        </button>
        
        {/* Subtle divider */}
        <div className="h-6 w-px bg-slate-600 ml-6" />
      </div>

      {/* Right: Search, Notifications, Help, Profile */}
      <div className="flex items-center gap-4">
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
                className="w-48 px-3 py-1.5 text-sm bg-slate-800 text-white border border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 placeholder-slate-400"
                data-testid="search-input"
              />
            </form>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors"
              data-testid="search-btn"
            >
              <Search className="h-[18px] w-[18px]" />
            </button>
          )}
        </div>

        {/* AI Credits Balance */}
        <CreditBalance compact={true} darkMode={true} />

        {/* Notifications */}
        <button
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors relative"
          data-testid="notifications-btn"
        >
          <Bell className="h-[18px] w-[18px]" />
        </button>

        {/* Help */}
        <button
          onClick={() => window.open('/docs', '_blank')}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors"
          data-testid="help-btn"
        >
          <HelpCircle className="h-[18px] w-[18px]" />
        </button>

        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 p-1.5 hover:bg-slate-700 rounded-md transition-colors"
            data-testid="profile-btn"
          >
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-medium">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <ChevronDown className={cn(
              "h-4 w-4 text-slate-400 transition-transform",
              profileOpen && "rotate-180"
            )} />
          </button>

          {profileOpen && (
            <>
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => setProfileOpen(false)}
              />
              <div className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
                  <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                </div>
                <button
                  onClick={() => { navigate('/settings'); setProfileOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <User className="h-4 w-4" />
                  Account
                </button>
                <button
                  onClick={() => { navigate('/settings'); setProfileOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </button>
                <div className="h-px bg-gray-100 my-1" />
                <button
                  onClick={() => { logout(); setProfileOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TopAppBar;
