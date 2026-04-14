import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { 
  Book, Home, Users, FileText, Receipt, Sparkles, Calculator,
  Clock, UserCog, HelpCircle, ChevronRight, ChevronDown,
  Search, ArrowLeft, Briefcase, PlayCircle, Store, Shield, DollarSign, Columns,
  Menu, X, FolderOpen
} from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';

const docsNavigation = [
  {
    title: 'Introduction',
    items: [
      { title: 'Overview', href: '/docs', icon: Book },
      { title: 'Getting Started', href: '/docs/getting-started', icon: PlayCircle },
    ]
  },
  {
    title: 'Core Features',
    items: [
      { title: 'Customers', href: '/docs/customers', icon: Users },
      { title: 'Document Library', href: '/docs/document-library', icon: FolderOpen },
      { title: 'Orders & Order Items', href: '/docs/quotes-jobs', icon: Briefcase },
      { title: 'Invoicing', href: '/docs/invoicing', icon: Receipt },
      { title: 'Pricing Calculator', href: '/docs/pricing-calculator', icon: Calculator },
    ]
  },
  {
    title: 'Advanced Features',
    items: [
      { title: 'AI Tools Suite', href: '/docs/ai-tools', icon: Sparkles },
      { title: 'Time Tracking', href: '/docs/time-tracking', icon: Clock },
      { title: 'Employee Management', href: '/docs/employees', icon: UserCog },
      { title: 'Webstores', href: '/docs/webstores', icon: Store },
      { title: 'Customer Portal', href: '/docs/customer-portal', icon: Shield },
      { title: 'Financial Tracking', href: '/docs/financials', icon: DollarSign },
      { title: 'Productivity Tools', href: '/docs/productivity', icon: Columns },
    ]
  },
  {
    title: 'Help',
    items: [
      { title: 'FAQ', href: '/docs/faq', icon: HelpCircle },
    ]
  }
];

export default function DocsLayout() {
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState(
    docsNavigation.map(section => section.title)
  );

  const toggleSection = (title) => {
    setExpandedSections(prev => 
      prev.includes(title) 
        ? prev.filter(t => t !== title)
        : [...prev, title]
    );
  };

  const isActive = (href) => location.pathname === href;

  // Close mobile menu on navigation
  const handleNavClick = () => {
    setMobileMenuOpen(false);
  };

  const SidebarContent = () => (
    <nav className="space-y-6">
      {docsNavigation.map((section) => (
        <div key={section.title}>
          <button
            onClick={() => toggleSection(section.title)}
            className="flex items-center justify-between w-full text-xs font-semibold uppercase tracking-wider text-gray-500 hover:text-gray-300 mb-2"
          >
            {section.title}
            {expandedSections.includes(section.title) ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {expandedSections.includes(section.title) && (
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      to={item.href}
                      onClick={handleNavClick}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                        isActive(item.href)
                          ? 'bg-cyan-500/10 text-cyan-400 font-medium'
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {item.title}
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-800 bg-[#0a0a0f]/95 backdrop-blur">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 text-gray-400 hover:text-white"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            
            <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="h-4 w-4" />
              <span className="text-sm hidden sm:inline">Back to App</span>
            </Link>
            <div className="h-6 w-px bg-gray-700 hidden sm:block" />
            <div className="flex items-center gap-2">
              <Book className="h-5 w-5 text-cyan-400" />
              <span className="font-semibold text-white text-sm sm:text-base">SignGuy AI Docs</span>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-4">
            <div className="relative w-48 lg:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
              <Input
                type="text"
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-gray-900 border-gray-700 text-white placeholder:text-gray-500"
              />
            </div>
          </div>
        </div>
        
        {/* Mobile Search */}
        <div className="sm:hidden px-4 pb-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
            <Input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-gray-900 border-gray-700 text-white placeholder:text-gray-500 w-full"
            />
          </div>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 z-40 bg-black/60"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <div className="flex">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block sticky top-[73px] h-[calc(100vh-73px)] w-64 border-r border-gray-800 bg-[#0a0a0f]">
          <ScrollArea className="h-full py-6 px-4">
            <SidebarContent />
          </ScrollArea>
        </aside>

        {/* Mobile Sidebar */}
        <aside 
          className={`lg:hidden fixed left-0 top-[73px] h-[calc(100vh-73px)] w-72 border-r border-gray-800 bg-[#0a0a0f] z-50 transform transition-transform duration-300 ${
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <ScrollArea className="h-full py-6 px-4">
            <SidebarContent />
          </ScrollArea>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-h-[calc(100vh-73px)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-8 py-8 sm:py-12">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
