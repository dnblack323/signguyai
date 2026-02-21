import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt,
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  Package, Shield, Building2, Settings, CreditCard,
  ImageIcon, Mail, Ticket, GripVertical, Plus, X, Check,
  Minus, MessageSquare, Bot
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
    color: 'bg-blue-500',
    shortcuts: [
      { id: 'dashboard', name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, color: 'text-blue-500' },
      { id: 'customers', name: 'Customers', href: '/customers', icon: Users, color: 'text-green-500' },
      { id: 'quotes', name: 'Quotes', href: '/quotes', icon: FileText, color: 'text-purple-500' },
      { id: 'jobs', name: 'Jobs', href: '/jobs', icon: Briefcase, color: 'text-orange-500' },
      { id: 'invoices', name: 'Invoices', href: '/invoices', icon: Receipt, color: 'text-red-500' },
    ]
  },
  {
    id: 'workforce',
    name: 'Workforce',
    color: 'bg-cyan-500',
    shortcuts: [
      { id: 'timeclock', name: 'Time Clock', href: '/timeclock', icon: Clock, color: 'text-cyan-500' },
      { id: 'payroll', name: 'Payroll', href: '/payroll', icon: DollarSign, color: 'text-emerald-500' },
      { id: 'productivity', name: 'Productivity', href: '/productivity', icon: CalendarDays, color: 'text-indigo-500' },
      { id: 'users', name: 'Users', href: '/users', icon: Shield, color: 'text-sky-500' },
    ]
  },
  {
    id: 'finance',
    name: 'Finance',
    color: 'bg-yellow-500',
    shortcuts: [
      { id: 'financials', name: 'Financials', href: '/financials', icon: DollarSign, color: 'text-yellow-500' },
      { id: 'pricing', name: 'Calculator', href: '/pricing-calculator', icon: DollarSign, color: 'text-lime-500' },
    ]
  },
  {
    id: 'ai',
    name: 'AI Tools',
    color: 'bg-pink-500',
    shortcuts: [
      { id: 'ai-tools', name: 'AI Tools', href: '/ai-tools', icon: Sparkles, color: 'text-pink-500' },
      { id: 'ai-assistant', name: 'AI Assistant', href: '/ai-assistant', icon: Bot, color: 'text-violet-500' },
    ]
  },
  {
    id: 'commerce',
    name: 'Commerce',
    color: 'bg-teal-500',
    shortcuts: [
      { id: 'webstores', name: 'Webstores', href: '/webstores', icon: Store, color: 'text-teal-500' },
      { id: 'products', name: 'Products', href: '/products', icon: Package, color: 'text-amber-500' },
    ]
  },
  {
    id: 'content',
    name: 'Content',
    color: 'bg-slate-500',
    shortcuts: [
      { id: 'documents', name: 'Documents', href: '/documents', icon: FileText, color: 'text-slate-500' },
      { id: 'approvals', name: 'Approvals', href: '/approvals', icon: ImageIcon, color: 'text-rose-500' },
      { id: 'messages', name: 'Messages', href: '/messages', icon: MessageSquare, color: 'text-blue-400' },
    ]
  },
  {
    id: 'system',
    name: 'System',
    color: 'bg-gray-500',
    shortcuts: [
      { id: 'settings', name: 'Settings', href: '/settings', icon: Building2, color: 'text-gray-500' },
    ]
  },
];

// Flatten all shortcuts for lookup
const allShortcuts = shortcutCategories.flatMap(cat => cat.shortcuts);

// Default shortcuts with separators (use '|' for separator)
const defaultShortcuts = ['dashboard', 'customers', 'quotes', 'jobs', 'invoices', '|', 'ai-tools', 'ai-assistant'];

const STORAGE_KEY = 'toolbar_shortcuts_v2';
const SIZE_KEY = 'toolbar_size';

export default function QuickToolbar() {
  const location = useLocation();
  const [shortcuts, setShortcuts] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : defaultShortcuts;
  });
  const [iconSize, setIconSize] = useState(() => {
    return localStorage.getItem(SIZE_KEY) || 'small';
  });
  const [isCustomizing, setIsCustomizing] = useState(false);
  const [tempShortcuts, setTempShortcuts] = useState([]);

  // Save to localStorage when shortcuts change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(shortcuts));
  }, [shortcuts]);

  useEffect(() => {
    localStorage.setItem(SIZE_KEY, iconSize);
  }, [iconSize]);

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

  const moveItem = (index, direction) => {
    const newShortcuts = [...tempShortcuts];
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= newShortcuts.length) return;
    [newShortcuts[index], newShortcuts[newIndex]] = [newShortcuts[newIndex], newShortcuts[index]];
    setTempShortcuts(newShortcuts);
  };

  const sizeClasses = {
    small: 'h-7 w-7',
    medium: 'h-9 w-9',
    large: 'h-11 w-11'
  };

  const iconSizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-5 w-5',
    large: 'h-6 w-6'
  };

  return (
    <>
      {/* Toolbar */}
      <div 
        className="hidden lg:flex fixed top-0 left-16 right-0 h-12 z-30 items-center px-4 gap-1"
        style={{ 
          backgroundColor: 'var(--surface)',
          borderBottom: '1px solid var(--border-light)'
        }}
      >
        {/* Shortcuts */}
        <div className="flex items-center gap-1 overflow-x-auto">
          {shortcuts.map((item, index) => {
            // Render separator
            if (item === '|') {
              return (
                <div 
                  key={`sep-${index}`}
                  className="h-6 w-px bg-[var(--border-light)] mx-1 flex-shrink-0"
                />
              );
            }
            
            // Render shortcut
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
                  "flex items-center justify-center rounded-lg transition-all duration-150 hover:scale-105 flex-shrink-0",
                  sizeClasses[iconSize],
                  isActive 
                    ? "bg-[var(--accent)] text-white shadow-sm" 
                    : "hover:bg-[var(--surface-2)]"
                )}
              >
                <Icon className={cn(iconSizeClasses[iconSize], isActive ? 'text-white' : shortcut.color)} />
              </Link>
            );
          })}
        </div>

        {/* Divider */}
        <div className="h-6 w-px bg-[var(--border-light)] mx-2 flex-shrink-0" />

        {/* Customize Button */}
        <button
          onClick={openCustomize}
          title="Customize toolbar"
          className={cn(
            "flex items-center justify-center rounded-lg transition-all hover:bg-[var(--surface-2)] flex-shrink-0",
            sizeClasses[iconSize]
          )}
        >
          <Settings className={cn(iconSizeClasses[iconSize], "text-[var(--text-muted)]")} />
        </button>

        {/* Size Toggle */}
        <div className="ml-auto flex items-center gap-1 text-xs text-[var(--text-muted)] flex-shrink-0">
          <span className="mr-1">Size:</span>
          {['small', 'medium', 'large'].map((size) => (
            <button
              key={size}
              onClick={() => setIconSize(size)}
              className={cn(
                "px-2 py-1 rounded transition-all",
                iconSize === size 
                  ? "bg-[var(--accent)] text-white" 
                  : "hover:bg-[var(--surface-2)]"
              )}
            >
              {size.charAt(0).toUpperCase()}
            </button>
          ))}
        </div>
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
            <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border-light)]">
              <div className="text-xs text-[var(--text-muted)] mb-2 flex items-center justify-between">
                <span>Current Toolbar ({tempShortcuts.filter(s => s !== '|').length} shortcuts)</span>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={addSeparator}
                  className="h-6 text-xs"
                >
                  <Plus className="h-3 w-3 mr-1" /> Add Separator
                </Button>
              </div>
              <div className="flex items-center gap-1 flex-wrap min-h-[40px]">
                {tempShortcuts.length === 0 ? (
                  <span className="text-sm text-[var(--text-muted)] italic">No shortcuts selected</span>
                ) : (
                  tempShortcuts.map((item, index) => {
                    if (item === '|') {
                      return (
                        <div key={`sep-${index}`} className="flex items-center gap-1 group">
                          <div className="h-8 w-1 bg-[var(--border-light)] rounded" />
                          <button
                            onClick={() => removeSeparator(index)}
                            className="opacity-0 group-hover:opacity-100 p-0.5 rounded bg-red-500/10 text-red-500 transition-opacity"
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
                        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[var(--surface)] border border-[var(--border-light)] group"
                      >
                        <Icon className={cn("h-4 w-4", shortcut.color)} />
                        <span className="text-xs font-medium">{shortcut.name}</span>
                        <button
                          onClick={() => toggleShortcut(shortcut.id)}
                          className="opacity-0 group-hover:opacity-100 p-0.5 rounded bg-red-500/10 text-red-500 transition-opacity ml-1"
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
                  <div className="flex items-center gap-2">
                    <div className={cn("h-2 w-2 rounded-full", category.color)} />
                    <span className="text-sm font-semibold text-[var(--text)]">{category.name}</span>
                  </div>
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
                            <Icon className={cn("h-4 w-4", isSelected ? "text-white" : shortcut.color)} />
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
