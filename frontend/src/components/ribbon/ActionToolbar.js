import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Plus, Save, Copy, FileDown, Send, Calendar, LayoutGrid, UserCheck,
  Printer, CheckCircle, UserPlus, Package, Share2, Wand2, TrendingUp,
  Building, Shield, CreditCard, ChevronDown, Clock, DollarSign,
  FolderOpen, ClipboardList, Mail, BookOpen, MessageCircle, Wrench,
  FileCheck, Users, Wallet, Tag, Store
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useState, useRef, useEffect } from 'react';
import { tabSubItems } from './PrimaryNav';

const ToolbarButton = ({ icon: Icon, label, onClick, active = false, route, currentPath, href }) => {
  const isActive = active || (route && currentPath?.startsWith(route));
  
  if (href) {
    return (
      <a
        href={href}
        target={href.startsWith('mailto') ? undefined : '_blank'}
        rel="noopener noreferrer"
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
        data-testid={`toolbar-btn-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      >
        <Icon className="h-4 w-4" />
        <span>{label}</span>
      </a>
    );
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors",
        isActive 
          ? "text-blue-600 bg-blue-100 border border-blue-200" 
          : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
      )}
      data-testid={`toolbar-btn-${label?.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );
};

const ToolbarSeparator = () => (
  <div className="w-px h-5 bg-gray-200 mx-2" />
);

// Quick action configs per tab
const quickActions = {
  dashboard: [
    { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
    { icon: FileDown, label: 'New Quote', route: '/jobs?new=true&type=quote' },
    { icon: CreditCard, label: 'New Invoice', route: '/invoices?new=true' },
  ],
  jobs: [
    { icon: Plus, label: 'New Job', route: '/jobs?new=true' },
    { icon: Printer, label: 'Work Order' },
  ],
  billing: [
    { icon: Plus, label: 'New Invoice', route: '/invoices?new=true' },
  ],
  customers: [
    { icon: UserPlus, label: 'New Customer', route: '/customers?new=true' },
  ],
  webstores: [
    { icon: Plus, label: 'New Store', route: '/webstores?new=true' },
  ],
};

export const ActionToolbar = ({ activeTab }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  
  const subItems = tabSubItems[activeTab] || [];
  const actions = quickActions[activeTab] || [];

  return (
    <div 
      className="h-10 flex items-center px-4 bg-gray-50/80 border-b border-gray-100"
      data-testid="action-toolbar"
    >
      <div className="flex items-center">
        {/* Sub-navigation items */}
        {subItems.map((item, idx) => (
          <ToolbarButton
            key={idx}
            icon={item.icon}
            label={item.label}
            route={item.path}
            href={item.href}
            currentPath={currentPath}
            onClick={() => item.path && navigate(item.path)}
          />
        ))}

        {/* Separator + Quick actions */}
        {subItems.length > 0 && actions.length > 0 && <ToolbarSeparator />}
        
        {actions.map((item, idx) => (
          <ToolbarButton
            key={`action-${idx}`}
            icon={item.icon}
            label={item.label}
            route={item.route}
            currentPath={currentPath}
            onClick={() => item.route ? navigate(item.route) : item.onClick?.()}
          />
        ))}
      </div>
    </div>
  );
};

export default ActionToolbar;
