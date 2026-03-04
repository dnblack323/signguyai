import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt,
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  Package, Shield, Building2, Settings, CreditCard,
  Image as ImageIcon, Mail, Ticket, Plus, X, Check, Bot, MessageSquare
} from 'lucide-react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import { toast } from 'sonner';

// All available shortcuts organized by category
const shortcutCategories = [
  {
    id: 'core',
    name: 'Core',
    shortcuts: [
      { id: 'dashboard', name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { id: 'customers', name: 'Customers', href: '/customers', icon: Users },
      { id: 'jobs', name: 'Jobs', href: '/jobs', icon: Briefcase },
      { id: 'invoices', name: 'Invoices', href: '/invoices', icon: Receipt },
    ]
  },
  {
    id: 'workforce',
    name: 'Workforce',
    shortcuts: [
      { id: 'timeclock', name: 'Time Clock', href: '/timeclock', icon: Clock },
      { id: 'payroll', name: 'Payroll', href: '/payroll', icon: DollarSign },
      { id: 'productivity', name: 'Productivity', href: '/productivity', icon: CalendarDays },
      { id: 'users', name: 'Users', href: '/users', icon: Shield },
    ]
  },
  {
    id: 'finance',
    name: 'Finance',
    shortcuts: [
      { id: 'financials', name: 'Financials', href: '/financials', icon: DollarSign },
      { id: 'pricing', name: 'Calculator', href: '/pricing-calculator', icon: DollarSign },
    ]
  },
  {
    id: 'ai',
    name: 'AI Tools',
    shortcuts: [
      { id: 'ai-tools', name: 'AI Tools', href: '/ai-tools', icon: Sparkles },
      { id: 'ai-assistant', name: 'AI Assistant', href: '/ai-assistant', icon: Bot },
    ]
  },
  {
    id: 'commerce',
    name: 'Commerce',
    shortcuts: [
      { id: 'webstores', name: 'Webstores', href: '/webstores', icon: Store },
      { id: 'products', name: 'Products', href: '/products', icon: Package },
    ]
  },
  {
    id: 'content',
    name: 'Content',
    shortcuts: [
      { id: 'documents', name: 'Documents', href: '/documents', icon: FileText },
      { id: 'approvals', name: 'Approvals', href: '/approvals', icon: ImageIcon },
      { id: 'admin-portal', name: 'Communications', href: '/admin-portal', icon: MessageSquare },
    ]
  },
  {
    id: 'system',
    name: 'System',
    shortcuts: [
      { id: 'settings', name: 'Settings', href: '/settings', icon: Building2 },
    ]
  },
];

// Flatten all shortcuts for lookup
const allShortcuts = shortcutCategories.flatMap(cat => cat.shortcuts);

// Default shortcuts with separators - removed quotes, jobs handles both now
const defaultShortcuts = ['dashboard', 'customers', 'jobs', 'invoices', '|', 'ai-tools', 'ai-assistant'];

const STORAGE_KEY = 'toolbar_shortcuts_v2';

export default function QuickToolbar() {
  const location = useLocation();
  const [shortcuts, setShortcuts] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : defaultShortcuts;
  });
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [tempShortcuts, setTempShortcuts] = useState([]);

  // Save to localStorage when shortcuts change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(shortcuts));
  }, [shortcuts]);

  const openCustomize = () => {
    setTempShortcuts([...shortcuts]);
    setIsCustomizing(true);
  };

  const saveCustomization = () => {
    setShortcuts(tempShortcuts);
    setIsCustomizing(false);
    toast.success('Toolbar customized!');
  };

  const toggleShortcut = (id) => {
    if (tempShortcuts.includes(id)) {
      setTempShortcuts(tempShortcuts.filter(s => s !== id));
    } else {
      setTempShortcuts([...tempShortcuts, id]);
    }
  };

  const addSeparator = () => {
    setTempShortcuts([...tempShortcuts, '|']);
  };

  const removeSeparator = (index) => {
    const newShortcuts = [...tempShortcuts];
    newShortcuts.splice(index, 1);
    setTempShortcuts(newShortcuts);
  };

  return (
    <>
      {/* Toolbar - Dark theme, ICONS ONLY */}
      <div 
        className="hidden lg:flex fixed top-0 left-48 right-0 h-12 z-30 items-center px-4 gap-1 nav-shell border-b border-[var(--border-dark)]"
        data-testid="quick-toolbar"
      >
        {/* Shortcuts - Icons Only */}
        <div className="flex items-center gap-1 overflow-x-auto">
          {shortcuts.map((item, index) => {
            // Render separator
            if (item === '|') {
              return (
                <div 
                  key={`sep-${index}`}
                  className="h-6 w-px bg-[var(--border-dark)] mx-2 flex-shrink-0"
                />
              );
            }
            
            // Render shortcut - ICON ONLY
            const shortcut = allShortcuts.find(s => s.id === item);
            if (!shortcut) return null;
            
            const Icon = shortcut.icon;
            const isActive = location.pathname === shortcut.href;
            
            return (
              <Link
                key={shortcut.id}
                to={shortcut.href}
                title={shortcut.name}
                className={cn(
                  "flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200 flex-shrink-0",
                  isActive 
                    ? "bg-[var(--accent)] text-white" 
                    : "text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--text-on-dark)]"
                )}
              >
                <Icon className="h-5 w-5" />
              </Link>
            );
          })}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Customize Button - Icon Only */}
        <button
          onClick={openCustomize}
          title="Customize toolbar"
          className="flex items-center justify-center w-9 h-9 rounded-lg text-[var(--text-muted-on-dark)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--text-on-dark)] transition-all duration-200"
        >
          <Settings className="h-5 w-5" />
        </button>
      </div>

      {/* Customize Dialog */}
      <Dialog open={isCustomizing} onOpenChange={setIsCustomizing}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-[var(--accent)]" />
              Customize Quick Toolbar
            </DialogTitle>
            <DialogDescription>
              Click shortcuts to add/remove. Use separators to organize into groups.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {/* Current toolbar preview */}
            <div className="p-3 rounded-lg bg-[var(--sidebar)] border border-[var(--border-dark)]">
              <div className="text-xs text-[var(--text-muted-on-dark)] mb-2 flex items-center justify-between">
                <span>Current Toolbar ({tempShortcuts.filter(s => s !== '|').length} shortcuts)</span>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={addSeparator}
                  className="h-6 text-xs text-[var(--text-on-dark)] hover:bg-[var(--sidebar-hover)]"
                >
                  <Plus className="h-3 w-3 mr-1" /> Add Separator
                </Button>
              </div>
              <div className="flex items-center gap-1 flex-wrap min-h-[40px]">
                {tempShortcuts.length === 0 ? (
                  <span className="text-sm text-[var(--text-muted-on-dark)] italic">No shortcuts selected</span>
                ) : (
                  tempShortcuts.map((item, index) => {
                    if (item === '|') {
                      return (
                        <div key={`sep-${index}`} className="flex items-center gap-1 group">
                          <div className="h-8 w-1 bg-[var(--border-dark)] rounded" />
                          <button
                            onClick={() => removeSeparator(index)}
                            className="opacity-0 group-hover:opacity-100 p-0.5 rounded bg-red-500/20 text-red-400 transition-opacity"
                            title="Remove separator"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      );
                    }
                    
                    const shortcut = allShortcuts.find(s => s.id === item);
                    if (!shortcut) return null;
                    const Icon = shortcut.icon;
                    
                    return (
                      <div 
                        key={shortcut.id}
                        className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-[var(--sidebar-hover)] group"
                      >
                        <Icon className="h-4 w-4 text-[var(--text-on-dark)]" />
                        <span className="text-xs font-medium text-[var(--text-on-dark)]">{shortcut.name}</span>
                        <button
                          onClick={() => toggleShortcut(shortcut.id)}
                          className="opacity-0 group-hover:opacity-100 p-0.5 rounded bg-red-500/20 text-red-400 transition-opacity ml-1"
                          title="Remove"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Available shortcuts by category */}
            <div className="space-y-3">
              {shortcutCategories.map((category) => (
                <div key={category.id} className="space-y-2">
                  <span className="text-sm font-semibold text-[var(--text)]">{category.name}</span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {category.shortcuts.map((shortcut) => {
                      const Icon = shortcut.icon;
                      const isSelected = tempShortcuts.includes(shortcut.id);
                      
                      return (
                        <button
                          key={shortcut.id}
                          onClick={() => toggleShortcut(shortcut.id)}
                          className={cn(
                            "flex items-center gap-2 p-2 rounded-lg border-2 transition-all text-left",
                            isSelected
                              ? "border-[var(--accent)] bg-[var(--accent)]/10"
                              : "border-transparent bg-[var(--surface-2)] hover:border-[var(--border-light)]"
                          )}
                        >
                          <div className={cn(
                            "flex items-center justify-center h-7 w-7 rounded-lg flex-shrink-0",
                            isSelected ? "bg-[var(--accent)]" : "bg-[var(--surface)]"
                          )}>
                            <Icon className={cn("h-4 w-4", isSelected ? "text-white" : "text-[var(--text-muted)]")} />
                          </div>
                          <span className="text-xs font-medium truncate flex-1">{shortcut.name}</span>
                          {isSelected && (
                            <Check className="h-4 w-4 text-[var(--accent)] flex-shrink-0" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center pt-4 border-t">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setTempShortcuts(defaultShortcuts)}
            >
              Reset to default
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsCustomizing(false)}>
                Cancel
              </Button>
              <Button onClick={saveCustomization}>
                Save Changes
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
