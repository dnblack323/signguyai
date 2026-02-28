import { useNavigate } from 'react-router-dom';
import { 
  Plus, Save, Copy, FileDown, Send, Calendar, LayoutGrid, UserCheck,
  Printer, CheckCircle, UserPlus, Package, Share2, Wand2, TrendingUp,
  Building, Shield, CreditCard, ChevronDown
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useState, useRef, useEffect } from 'react';

// Ghost button component for toolbar
const ToolbarButton = ({ icon: Icon, label, onClick, active = false }) => (
  <button
    onClick={onClick}
    className={cn(
      "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors",
      active 
        ? "text-blue-600 bg-blue-50" 
        : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
    )}
    data-testid={`toolbar-btn-${label?.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <Icon className="h-4 w-4" />
    <span>{label}</span>
  </button>
);

// Dropdown button for toolbar
const ToolbarDropdown = ({ icon: Icon, label, items }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition-colors"
      >
        <Icon className="h-4 w-4" />
        <span>{label}</span>
        <ChevronDown className={cn("h-3 w-3 transition-transform", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 min-w-[140px] bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1">
          {items.map((item, idx) => (
            <button
              key={idx}
              onClick={() => { item.onClick?.(); setIsOpen(false); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 transition-colors"
            >
              {item.icon && <item.icon className="h-3.5 w-3.5" />}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Separator between groups
const ToolbarSeparator = () => (
  <div className="w-px h-5 bg-gray-200 mx-2" />
);

// Toolbar configurations per nav item
const toolbarConfigs = {
  dashboard: {
    groups: [
      {
        items: [
          { type: 'dropdown', icon: Plus, label: 'New', items: [
            { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
            { icon: FileDown, label: 'New Quote', route: '/jobs?new=true&type=quote' },
            { icon: CreditCard, label: 'New Invoice', route: '/invoices?new=true' },
          ]},
        ]
      },
      {
        items: [
          { type: 'button', icon: Calendar, label: 'Calendar' },
          { type: 'button', icon: LayoutGrid, label: 'Kanban' },
          { type: 'button', icon: UserCheck, label: 'Assigned' },
        ]
      },
    ]
  },
  jobs: {
    groups: [
      {
        items: [
          { type: 'button', icon: Plus, label: 'New Job', route: '/jobs?new=true' },
        ]
      },
      {
        items: [
          { type: 'button', icon: CheckCircle, label: 'Status' },
          { type: 'button', icon: UserCheck, label: 'Assign' },
          { type: 'button', icon: Calendar, label: 'Due Date' },
        ]
      },
      {
        items: [
          { type: 'button', icon: Printer, label: 'Work Order' },
          { type: 'dropdown', icon: FileDown, label: 'Export', items: [
            { label: 'Export PDF' },
            { label: 'Export CSV' },
          ]},
        ]
      },
    ]
  },
  quotes: {
    groups: [
      {
        items: [
          { type: 'button', icon: Plus, label: 'New Quote', route: '/jobs?new=true&type=quote' },
        ]
      },
      {
        items: [
          { type: 'button', icon: CheckCircle, label: 'Approve' },
          { type: 'button', icon: Send, label: 'Send' },
          { type: 'button', icon: Copy, label: 'Duplicate' },
        ]
      },
    ]
  },
  invoices: {
    groups: [
      {
        items: [
          { type: 'button', icon: Plus, label: 'New Invoice', route: '/invoices?new=true' },
        ]
      },
      {
        items: [
          { type: 'button', icon: CheckCircle, label: 'Mark Paid' },
          { type: 'button', icon: Send, label: 'Send' },
          { type: 'button', icon: CreditCard, label: 'Payment' },
        ]
      },
    ]
  },
  customers: {
    groups: [
      {
        items: [
          { type: 'button', icon: UserPlus, label: 'New Customer', route: '/customers?new=true' },
        ]
      },
      {
        items: [
          { type: 'button', icon: FileDown, label: 'Quote' },
          { type: 'button', icon: CreditCard, label: 'Invoice' },
        ]
      },
    ]
  },
  webstores: {
    groups: [
      {
        items: [
          { type: 'button', icon: Plus, label: 'New Store', route: '/webstores?new=true' },
        ]
      },
      {
        items: [
          { type: 'button', icon: Package, label: 'Products', route: '/products' },
          { type: 'button', icon: Share2, label: 'Promos', route: '/promo-codes' },
        ]
      },
    ]
  },
  'ai-tools': {
    groups: [
      {
        items: [
          { type: 'button', icon: Wand2, label: 'AI Tools', route: '/ai-tools' },
          { type: 'button', icon: TrendingUp, label: 'Pricing', route: '/pricing-calculator' },
        ]
      },
    ]
  },
  reports: {
    groups: [
      {
        items: [
          { type: 'button', icon: TrendingUp, label: 'Financials', route: '/financials' },
          { type: 'button', icon: Calendar, label: 'Productivity', route: '/productivity' },
        ]
      },
      {
        items: [
          { type: 'dropdown', icon: FileDown, label: 'Export', items: [
            { label: 'Export CSV' },
            { label: 'Export PDF' },
          ]},
        ]
      },
    ]
  },
  settings: {
    groups: [
      {
        items: [
          { type: 'button', icon: Building, label: 'Company', route: '/settings' },
          { type: 'button', icon: Shield, label: 'Users', route: '/users' },
          { type: 'button', icon: CreditCard, label: 'Billing', route: '/billing' },
        ]
      },
    ]
  },
};

export const ActionToolbar = ({ activeTab }) => {
  const navigate = useNavigate();
  const config = toolbarConfigs[activeTab] || toolbarConfigs.dashboard;

  const handleAction = (item) => {
    if (item.route) {
      navigate(item.route);
    } else if (item.onClick) {
      item.onClick();
    }
  };

  return (
    <div 
      className="h-10 flex items-center px-6 bg-gray-50/50 border-b border-gray-100"
      data-testid="action-toolbar"
    >
      <div className="flex items-center">
        {config.groups.map((group, groupIdx) => (
          <div key={groupIdx} className="flex items-center">
            {groupIdx > 0 && <ToolbarSeparator />}
            {group.items.map((item, itemIdx) => {
              if (item.type === 'dropdown') {
                return (
                  <ToolbarDropdown
                    key={itemIdx}
                    icon={item.icon}
                    label={item.label}
                    items={item.items.map(subItem => ({
                      ...subItem,
                      onClick: () => subItem.route ? navigate(subItem.route) : subItem.onClick?.()
                    }))}
                  />
                );
              }
              return (
                <ToolbarButton
                  key={itemIdx}
                  icon={item.icon}
                  label={item.label}
                  onClick={() => handleAction(item)}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActionToolbar;
