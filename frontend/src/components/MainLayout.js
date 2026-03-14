import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, Eye, ExternalLink, ChevronDown, X, User, Clock, Globe, Download } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { TopAppBar, PrimaryNav, ActionToolbar, MobileNav } from './ribbon';
import { TrialCountdown } from './TrialLockout';
import DevPanel from './DevPanel';
import FloatingAssistant from './FloatingAssistant';

// Total header height: TopAppBar (64px) + PrimaryNav (48px) + ActionToolbar (40px) = 152px
const HEADER_HEIGHT = 152;
const MOBILE_HEADER_HEIGHT = 64;

export const MainLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewProductLine, setPreviewProductLine] = useState(() => 
    localStorage.getItem('preview_product_line') || 'os_business'
  );
  const [scrolled, setScrolled] = useState(false);
  const [showBackupReminder, setShowBackupReminder] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { api } = useApp();

  // Check backup status for owner
  const checkBackup = useCallback(async () => {
    if (user?.role !== 'owner') return;
    const dismissed = sessionStorage.getItem('backup_reminder_dismissed');
    if (dismissed) return;
    try {
      const res = await api.get('/backup/status');
      if (res.data?.needs_reminder) setShowBackupReminder(true);
    } catch { /* ignore */ }
  }, [user?.role, api]);

  useEffect(() => { checkBackup(); }, [checkBackup]);
  
  // Track scroll for shadow effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 0);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Only show preview mode in development OR for founder accounts
  const isDevelopment = process.env.NODE_ENV === 'development' || 
                        window.location.hostname.includes('preview.emergentagent.com') ||
                        window.location.hostname === 'localhost';
  const isFounder = user?.is_founder === true;
  const showPreviewMode = isDevelopment || isFounder;

  // Save preview settings to localStorage
  useEffect(() => {
    localStorage.setItem('preview_product_line', previewProductLine);
    window.dispatchEvent(new Event('previewProductLineChanged'));
  }, [previewProductLine]);

  // Product Line preview options
  const productLineLabels = {
    os_business: { name: 'OS Business', color: 'bg-amber-500', productLine: 'os' },
    os_pro: { name: 'OS Pro', color: 'bg-blue-500', productLine: 'os' },
    os_starter: { name: 'OS Starter', color: 'bg-slate-500', productLine: 'os' },
    webstores_only: { name: 'Webstores Only', color: 'bg-emerald-500', productLine: 'webstores' },
    ai_studio_only: { name: 'AI Studio Only', color: 'bg-purple-500', productLine: 'ai_studio' },
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0f172a' }}>
      {/* Fixed Header - Light */}
      <header 
        className={cn(
          "fixed top-0 left-0 right-0 z-40 bg-white transition-shadow",
          scrolled && "shadow-md"
        )}
      >
        {/* Mobile Header */}
        <div className="lg:hidden h-16 flex items-center justify-between px-4 border-b border-gray-200">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
            data-testid="mobile-menu-btn"
          >
            <Menu className="h-5 w-5" />
          </button>
          
          <img 
            src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
            alt="SignGuy AI" 
            className="h-7 w-auto"
          />
          
          <div className="w-9" /> {/* Spacer for balance */}
        </div>

        {/* Desktop Header */}
        <div className="hidden lg:block">
          {/* Top App Bar: Logo + Right icons */}
          <TopAppBar onMobileMenuClick={() => setMobileMenuOpen(true)} />
          
          {/* Primary Navigation */}
          <PrimaryNav activeTab={activeTab} onTabChange={setActiveTab} />
          
          {/* Action Toolbar */}
          <ActionToolbar activeTab={activeTab} />
        </div>
      </header>

      {/* Mobile Navigation */}
      <MobileNav 
        isOpen={mobileMenuOpen} 
        onClose={() => setMobileMenuOpen(false)} 
      />

      {/* Trial Countdown */}
      <div className="hidden lg:block fixed top-4 right-24 z-30">
        <TrialCountdown />
      </div>

      {/* Main Content - Dark Shell Background */}
      <main 
        className="min-h-screen transition-all"
        style={{ 
          paddingTop: typeof window !== 'undefined' && window.innerWidth >= 1024 
            ? HEADER_HEIGHT 
            : MOBILE_HEADER_HEIGHT,
          backgroundColor: '#0f172a'
        }}
      >
        {/* Content wrapper - centered with max-width, TRANSPARENT background */}
        <div 
          className="p-4 lg:p-6"
          style={{ backgroundColor: 'transparent' }}
        >
          <div 
            className="max-w-[1400px] mx-auto"
            style={{ backgroundColor: 'transparent' }}
          >
            {/* Weekly backup reminder */}
            {showBackupReminder && (
              <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between" data-testid="backup-reminder">
                <div className="flex items-center gap-3">
                  <Download className="w-5 h-5 text-amber-400" />
                  <p className="text-sm text-amber-300">
                    It's been over a week since your last backup.{' '}
                    <button onClick={() => navigate('/settings/backup')} className="underline font-medium text-amber-400 hover:text-amber-300">
                      Download a backup now
                    </button>
                  </p>
                </div>
                <button onClick={() => { setShowBackupReminder(false); sessionStorage.setItem('backup_reminder_dismissed', '1'); }} className="text-gray-500 hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
            {/* Children render their own cards - no wrapper card here */}
            {children}
          </div>
        </div>
      </main>

      {/* Marketing Site Link - Fixed Bottom Right */}
      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2">
        {/* Visit Marketing Site */}
        <a
          href="/home"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2 rounded-full bg-white border border-gray-200 text-gray-600 hover:text-gray-900 hover:border-gray-300 transition-all shadow-sm text-sm"
          data-testid="marketing-site-link"
        >
          <Globe className="h-4 w-4" />
          <span className="font-medium">Website</span>
        </a>

        {/* Preview Mode Panel */}
        {showPreviewMode && (previewOpen ? (
          <div className="bg-white border border-gray-200 rounded-xl shadow-lg w-72 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-gray-100 bg-gray-50">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-900">Preview Mode</span>
              </div>
              <button 
                onClick={() => setPreviewOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-3 space-y-3">
              {/* Product Line Selection */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">View As</label>
                <div className="mt-2 space-y-1">
                  {Object.entries(productLineLabels).map(([key, { name, color }]) => (
                    <button
                      key={key}
                      onClick={() => setPreviewProductLine(key)}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-md text-left transition-all text-sm",
                        previewProductLine === key 
                          ? "bg-blue-50 text-blue-700 ring-1 ring-blue-200" 
                          : "hover:bg-gray-50 text-gray-600"
                      )}
                      data-testid={`preview-${key}`}
                    >
                      <div className={cn("w-2 h-2 rounded-full", color)} />
                      <span>{name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Links */}
              <div className="pt-2 border-t border-gray-100">
                <button
                  onClick={() => window.open('/customer-portal/login', '_blank')}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left hover:bg-gray-50 text-sm text-gray-600"
                >
                  <User className="h-4 w-4 text-gray-400" />
                  <span>Customer Portal</span>
                  <ExternalLink className="h-3 w-3 ml-auto text-gray-400" />
                </button>
                <button
                  onClick={() => window.open('/employee-portal/login', '_blank')}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left hover:bg-gray-50 text-sm text-gray-600"
                >
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span>Employee Portal</span>
                  <ExternalLink className="h-3 w-3 ml-auto text-gray-400" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setPreviewOpen(true)}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-full shadow-sm transition-all text-sm font-medium text-white",
              productLineLabels[previewProductLine]?.color || 'bg-amber-500'
            )}
            data-testid="preview-mode-toggle"
          >
            <Eye className="h-4 w-4" />
            <span>{productLineLabels[previewProductLine]?.name || 'Preview'}</span>
          </button>
        ))}
      </div>

      {/* Dev Panel - Admin Only */}
      <DevPanel />
      
      {/* Floating AI Assistant - Always visible */}
      <FloatingAssistant />
    </div>
  );
};

export default MainLayout;
