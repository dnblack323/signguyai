import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard, Users, FileText, Briefcase, Receipt,
  Clock, DollarSign, CalendarDays, Sparkles, Store,
  Package, Shield, Building2, Settings, CreditCard,
  ImageIcon, Mail, Ticket, GripVertical, Plus, X, Check
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

// All available shortcuts
const allShortcuts = [
  { id: 'dashboard', name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, color: 'text-blue-500' },
  { id: 'customers', name: 'Customers', href: '/customers', icon: Users, color: 'text-green-500' },
  { id: 'quotes', name: 'Quotes', href: '/quotes', icon: FileText, color: 'text-purple-500' },
  { id: 'jobs', name: 'Jobs', href: '/jobs', icon: Briefcase, color: 'text-orange-500' },
  { id: 'invoices', name: 'Invoices', href: '/invoices', icon: Receipt, color: 'text-red-500' },
  { id: 'timeclock', name: 'Time Clock', href: '/timeclock', icon: Clock, color: 'text-cyan-500' },
  { id: 'payroll', name: 'Payroll', href: '/payroll', icon: DollarSign, color: 'text-emerald-500' },
  { id: 'productivity', name: 'Productivity', href: '/productivity', icon: CalendarDays, color: 'text-indigo-500' },
  { id: 'financials', name: 'Financials', href: '/financials', icon: DollarSign, color: 'text-yellow-500' },
  { id: 'ai-tools', name: 'AI Tools', href: '/ai-tools', icon: Sparkles, color: 'text-pink-500' },
  { id: 'ai-assistant', name: 'AI Assistant', href: '/ai-assistant', icon: Sparkles, color: 'text-violet-500' },
  { id: 'webstores', name: 'Webstores', href: '/webstores', icon: Store, color: 'text-teal-500' },
  { id: 'products', name: 'Products', href: '/products', icon: Package, color: 'text-amber-500' },
  { id: 'documents', name: 'Documents', href: '/documents', icon: FileText, color: 'text-slate-500' },
  { id: 'approvals', name: 'Approvals', href: '/approvals', icon: ImageIcon, color: 'text-rose-500' },
  { id: 'pricing', name: 'Calculator', href: '/pricing-calculator', icon: DollarSign, color: 'text-lime-500' },
  { id: 'users', name: 'Users', href: '/users', icon: Shield, color: 'text-sky-500' },
  { id: 'settings', name: 'Settings', href: '/settings', icon: Building2, color: 'text-gray-500' },
];

// Default shortcuts
const defaultShortcuts = ['dashboard', 'customers', 'quotes', 'jobs', 'invoices', 'ai-tools'];

const STORAGE_KEY = 'toolbar_shortcuts';
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
    } else if (tempShortcuts.length < 10) {
      setTempShortcuts([...tempShortcuts, id]);
    } else {
      toast.error('Maximum 10 shortcuts allowed');
    }
  };

  const activeShortcuts = shortcuts
    .map(id => allShortcuts.find(s => s.id === id))
    .filter(Boolean);

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
        <div className="flex items-center gap-1">
          {activeShortcuts.map((shortcut) => {
            const Icon = shortcut.icon;
            const isActive = location.pathname === shortcut.href;
            
            return (
              <Link
                key={shortcut.id}
                to={shortcut.href}
                title={shortcut.name}
                className={cn(
                  "flex items-center justify-center rounded-lg transition-all duration-150 hover:scale-105",
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
        <div className="h-6 w-px bg-[var(--border-light)] mx-2" />

        {/* Customize Button */}
        <button
          onClick={openCustomize}
          title="Customize toolbar"
          className={cn(
            "flex items-center justify-center rounded-lg transition-all hover:bg-[var(--surface-2)]",
            sizeClasses[iconSize]
          )}
        >
          <Settings className={cn(iconSizeClasses[iconSize], "text-[var(--text-muted)]")} />
        </button>

        {/* Size Toggle */}
        <div className="ml-auto flex items-center gap-1 text-xs text-[var(--text-muted)]">
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
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-[var(--accent)]" />
              Customize Quick Toolbar
            </DialogTitle>
            <DialogDescription>
              Select up to 10 shortcuts to show in your toolbar. Click to toggle.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            {/* Selected count */}
            <div className="flex items-center justify-between mb-4 text-sm">
              <span className="text-[var(--text-muted)]">
                {tempShortcuts.length} of 10 shortcuts selected
              </span>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setTempShortcuts(defaultShortcuts)}
              >
                Reset to default
              </Button>
            </div>

            {/* Shortcuts Grid */}
            <div className="grid grid-cols-3 gap-2">
              {allShortcuts.map((shortcut) => {
                const Icon = shortcut.icon;
                const isSelected = tempShortcuts.includes(shortcut.id);
                
                return (
                  <button
                    key={shortcut.id}
                    onClick={() => toggleShortcut(shortcut.id)}
                    className={cn(
                      "flex items-center gap-2 p-3 rounded-lg border-2 transition-all text-left",
                      isSelected
                        ? "border-[var(--accent)] bg-[var(--accent)]/10"
                        : "border-transparent bg-[var(--surface-2)] hover:border-[var(--border-light)]"
                    )}
                  >
                    <div className={cn(
                      "flex items-center justify-center h-8 w-8 rounded-lg",
                      isSelected ? "bg-[var(--accent)]" : "bg-[var(--surface)]"
                    )}>
                      <Icon className={cn("h-4 w-4", isSelected ? "text-white" : shortcut.color)} />
                    </div>
                    <span className="text-sm font-medium truncate flex-1">{shortcut.name}</span>
                    {isSelected && (
                      <Check className="h-4 w-4 text-[var(--accent)] flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setIsCustomizing(false)}>
              Cancel
            </Button>
            <Button onClick={saveCustomization}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
