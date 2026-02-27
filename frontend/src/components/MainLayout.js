import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Eye, ExternalLink, ChevronDown, X, User, Clock, Globe } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../context/AuthContext';
import { TopAppBar, Ribbon, MobileRibbonOverlay } from './ribbon';
import { TrialCountdown } from './TrialLockout';

// Total header height: TopAppBar (56px) + Ribbon (approx 112px) = 168px
const HEADER_HEIGHT = 168;

export const MainLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewProductLine, setPreviewProductLine] = useState(() => 
    localStorage.getItem('preview_product_line') || 'os_business'
  );
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
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
    os_business: { name: 'OS Business (Full Access)', color: 'bg-amber-500', productLine: 'os' },
    os_pro: { name: 'OS Pro', color: 'bg-blue-500', productLine: 'os' },
    os_starter: { name: 'OS Starter', color: 'bg-slate-500', productLine: 'os' },
    webstores_only: { name: 'Webstores Only', color: 'bg-emerald-500', productLine: 'webstores' },
    ai_studio_only: { name: 'AI Studio Only', color: 'bg-purple-500', productLine: 'ai_studio' },
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--bg)' }}>
      {/* Fixed Header: Top App Bar + Ribbon */}
      <header className="fixed top-0 left-0 right-0 z-40">
        {/* Row 1: Top App Bar */}
        <TopAppBar onMobileMenuClick={() => setMobileMenuOpen(true)} />
        
        {/* Row 2: Ribbon (Desktop only - hidden on mobile) */}
        <div className="hidden lg:block">
          <Ribbon />
        </div>
      </header>

      {/* Mobile Ribbon Overlay */}
      <MobileRibbonOverlay 
        isOpen={mobileMenuOpen} 
        onClose={() => setMobileMenuOpen(false)} 
      />

      {/* Trial Countdown - Fixed top right, below header on desktop */}
      <div className="hidden lg:block fixed top-[180px] right-4 z-30">
        <TrialCountdown />
      </div>

      {/* Mobile Trial Countdown */}
      <div className="lg:hidden fixed top-16 right-4 z-30">
        <TrialCountdown />
      </div>

      {/* Main Content - with padding for fixed header */}
      <main 
        className="min-h-screen"
        style={{ paddingTop: HEADER_HEIGHT }}
      >
        {/* Mobile: smaller padding since ribbon is hidden */}
        <div className="lg:hidden" style={{ marginTop: -112 }} />
        
        <div className="p-3 sm:p-6 lg:p-8">
          {/* Content wrapper with light surface */}
          <div className="bg-[var(--surface)] rounded-xl sm:rounded-2xl p-4 sm:p-6 lg:p-8 min-h-[calc(100vh-12rem)] shadow-sm">
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
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#2F8BFB]/20 border border-[#2F8BFB]/30 text-[#2F8BFB] hover:bg-[#2F8BFB]/30 transition-all shadow-lg"
          data-testid="marketing-site-link"
        >
          <Globe className="h-4 w-4" />
          <span className="text-sm font-medium">View Website</span>
          <ExternalLink className="h-3 w-3" />
        </a>

        {/* Preview Mode Panel - Only visible in dev/preview or for founders */}
        {showPreviewMode && (previewOpen ? (
          <div className="bg-[var(--sidebar)] border border-[var(--border-dark)] rounded-xl shadow-2xl w-80 overflow-hidden max-h-[80vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-[var(--border-dark)] bg-[var(--accent)]/20 sticky top-0">
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

            <div className="p-3 space-y-4">
              {/* Product Line Selection */}
              <div>
                <label className="text-xs font-medium text-[var(--text-muted-on-dark)] uppercase tracking-wide">View As Product Line</label>
                <p className="text-xs text-[var(--text-muted-on-dark)] mt-1 mb-2">Preview what different customers see</p>
                <div className="space-y-1">
                  {Object.entries(productLineLabels).map(([key, { name, color, productLine }]) => (
                    <button
                      key={key}
                      onClick={() => setPreviewProductLine(key)}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-all",
                        previewProductLine === key 
                          ? "bg-[var(--sidebar-hover)] ring-1 ring-[var(--accent)]" 
                          : "hover:bg-[var(--sidebar-hover)]"
                      )}
                      data-testid={`preview-${key}`}
                    >
                      <div className={cn("w-3 h-3 rounded-full", color)} />
                      <div className="flex-1">
                        <span className="text-sm text-[var(--text-on-dark)]">{name}</span>
                        {productLine !== 'os' && (
                          <span className="ml-2 text-xs text-[var(--text-muted-on-dark)]">
                            ({productLine === 'webstores' ? 'No shop features' : 'AI tools only'})
                          </span>
                        )}
                      </div>
                      {previewProductLine === key && (
                        <span className="text-xs text-[var(--accent)]">Active</span>
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

              {/* Current View Info */}
              <div className="pt-2 border-t border-[var(--border-dark)]">
                <div className="flex items-center gap-2 px-3 py-2 bg-[var(--sidebar-hover)] rounded-lg">
                  <div className={cn("w-2 h-2 rounded-full", productLineLabels[previewProductLine]?.color || 'bg-slate-500')} />
                  <span className="text-xs text-[var(--text-muted-on-dark)]">
                    Viewing as: <span className="text-[var(--text-on-dark)] font-medium">{productLineLabels[previewProductLine]?.name || 'OS Business'}</span>
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
              productLineLabels[previewProductLine]?.color || 'bg-amber-500'
            )}
            data-testid="preview-mode-toggle"
          >
            <Eye className="h-4 w-4 text-white" />
            <span className="text-sm font-medium text-white">{productLineLabels[previewProductLine]?.name || 'OS Business'}</span>
            <ChevronDown className="h-3 w-3 text-white/80" />
          </button>
        ))}
      </div>
    </div>
  );
};

// Export Sidebar as a no-op for backwards compatibility if imported elsewhere
export const Sidebar = () => null;
export const MobileNav = () => null;

export default MainLayout;
