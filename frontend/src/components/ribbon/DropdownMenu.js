import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';

export const DropdownMenu = ({ 
  trigger, 
  items, 
  align = 'left',
  className = '',
  triggerClassName = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on ESC
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, []);

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-1 transition-colors",
          triggerClassName
        )}
        data-testid={`dropdown-${trigger.label?.toLowerCase().replace(/\s+/g, '-') || 'menu'}`}
      >
        {trigger.icon && <trigger.icon className="h-4 w-4" />}
        {trigger.label && <span>{trigger.label}</span>}
        <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div 
          className={cn(
            "absolute top-full mt-1 min-w-[180px] bg-[var(--surface)] border border-[var(--border-light)] rounded-lg shadow-xl z-50 py-1 animate-fade-in",
            align === 'right' && "right-0",
            align === 'left' && "left-0"
          )}
        >
          {items.map((item, index) => {
            if (item.separator) {
              return <div key={index} className="h-px bg-[var(--border-light)] my-1" />;
            }

            return (
              <button
                key={index}
                onClick={() => {
                  item.onClick?.();
                  setIsOpen(false);
                }}
                disabled={item.disabled}
                className={cn(
                  "w-full flex items-center gap-3 px-4 py-2 text-sm text-left transition-colors",
                  item.disabled 
                    ? "text-[var(--text-muted)] cursor-not-allowed opacity-50"
                    : "text-[var(--text)] hover:bg-[var(--accent-soft)]",
                  item.danger && !item.disabled && "text-red-500 hover:bg-red-50"
                )}
                data-testid={`dropdown-item-${item.label?.toLowerCase().replace(/\s+/g, '-')}`}
              >
                {item.icon && <item.icon className="h-4 w-4" />}
                <span className="flex-1">{item.label}</span>
                {item.shortcut && (
                  <span className="text-xs text-[var(--text-muted)]">{item.shortcut}</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Split Button - A button with a dropdown arrow
export const SplitButton = ({ 
  label, 
  icon: Icon, 
  onClick, 
  dropdownItems,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on ESC
  useEffect(() => {
    const handleEsc = (event) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, []);

  return (
    <div ref={dropdownRef} className={cn("relative inline-flex", className)}>
      <button
        onClick={onClick}
        className="flex flex-col items-center gap-1 px-3 py-2 hover:bg-[var(--accent-soft)] rounded-l-md transition-colors border-r border-[var(--border-light)]"
        data-testid={`split-btn-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      >
        {Icon && <Icon className="h-5 w-5 text-[var(--accent)]" />}
        <span className="text-xs text-[var(--text)]">{label}</span>
      </button>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center px-1.5 hover:bg-[var(--accent-soft)] rounded-r-md transition-colors"
      >
        <ChevronDown className={cn("h-3 w-3 text-[var(--text-muted)] transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 min-w-[160px] bg-[var(--surface)] border border-[var(--border-light)] rounded-lg shadow-xl z-50 py-1 animate-fade-in">
          {dropdownItems.map((item, index) => {
            if (item.separator) {
              return <div key={index} className="h-px bg-[var(--border-light)] my-1" />;
            }

            return (
              <button
                key={index}
                onClick={() => {
                  item.onClick?.();
                  setIsOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-2 text-sm text-left text-[var(--text)] hover:bg-[var(--accent-soft)] transition-colors"
                data-testid={`split-item-${item.label?.toLowerCase().replace(/\s+/g, '-')}`}
              >
                {item.icon && <item.icon className="h-4 w-4" />}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DropdownMenu;
