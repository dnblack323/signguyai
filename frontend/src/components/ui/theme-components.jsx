import { cn } from '../lib/utils';

// Page header component for consistent styling
export const PageHeader = ({ title, subtitle, children }) => (
  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
    <div>
      <h1 className="text-3xl font-bold font-heading uppercase tracking-tight" style={{ color: '#1A1A1A' }}>
        {title}
      </h1>
      {subtitle && (
        <p className="mt-1 text-sm" style={{ color: '#5A5A5A' }}>
          {subtitle}
        </p>
      )}
    </div>
    {children && <div className="flex items-center gap-3">{children}</div>}
  </div>
);

// Stat card component
export const StatCard = ({ title, value, icon: Icon, subtitle, trend, href, onClick }) => (
  <div 
    className={cn(
      "rounded-xl p-6 transition-all duration-200 hover:shadow-md",
      onClick && "cursor-pointer"
    )}
    style={{ 
      backgroundColor: '#FFFFFF', 
      border: '1px solid #D7DCE2' 
    }}
    onClick={onClick}
  >
    <div className="flex items-start justify-between">
      <div className="space-y-2">
        <p className="text-sm font-medium" style={{ color: '#5A5A5A' }}>{title}</p>
        <p className="text-3xl font-bold font-heading tracking-tight" style={{ color: '#1A1A1A' }}>{value}</p>
        {subtitle && (
          <p className="text-xs" style={{ color: '#5A5A5A' }}>{subtitle}</p>
        )}
      </div>
      <div className="p-3 rounded-lg" style={{ backgroundColor: 'rgba(47, 139, 251, 0.1)' }}>
        <Icon className="h-6 w-6" style={{ color: '#2F8BFB' }} />
      </div>
    </div>
    {trend && (
      <div className="mt-3 flex items-center gap-1 text-sm">
        <span className={trend > 0 ? "text-green-600" : "text-red-600"}>
          {trend > 0 ? '+' : ''}{trend}%
        </span>
        <span style={{ color: '#5A5A5A' }}>from last month</span>
      </div>
    )}
  </div>
);

// Panel/Card container
export const Panel = ({ children, className, noPadding = false }) => (
  <div 
    className={cn("rounded-xl", !noPadding && "p-6", className)}
    style={{ 
      backgroundColor: '#FFFFFF', 
      border: '1px solid #D7DCE2' 
    }}
  >
    {children}
  </div>
);

// Panel header
export const PanelHeader = ({ title, children }) => (
  <div className="flex items-center justify-between mb-4">
    <h2 className="text-lg font-semibold font-heading uppercase tracking-wide" style={{ color: '#1A1A1A' }}>
      {title}
    </h2>
    {children}
  </div>
);

// Tab container
export const TabContainer = ({ children }) => (
  <div 
    className="inline-flex gap-1 p-1 rounded-lg"
    style={{ backgroundColor: '#F5F7FA' }}
  >
    {children}
  </div>
);

// Tab button
export const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={cn(
      "px-4 py-2 rounded-md text-sm font-medium transition-all duration-200"
    )}
    style={{
      backgroundColor: active ? '#2F8BFB' : 'transparent',
      color: active ? '#FFFFFF' : '#1A1A1A'
    }}
  >
    {children}
  </button>
);

// Badge styles
export const StatusBadge = ({ status, children }) => {
  const getStatusStyles = () => {
    switch (status) {
      case 'success':
      case 'paid':
      case 'approved':
      case 'complete':
        return { backgroundColor: 'rgba(34, 197, 94, 0.15)', color: '#16a34a' };
      case 'warning':
      case 'sent':
      case 'pending':
      case 'in_production':
        return { backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#d97706' };
      case 'danger':
      case 'overdue':
      case 'declined':
        return { backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#dc2626' };
      case 'info':
      case 'quoted':
      case 'draft':
        return { backgroundColor: 'rgba(47, 139, 251, 0.15)', color: '#2F8BFB' };
      default:
        return { backgroundColor: '#F5F7FA', color: '#5A5A5A' };
    }
  };

  const styles = getStatusStyles();

  return (
    <span 
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
      style={styles}
    >
      {children}
    </span>
  );
};

// Primary button
export const PrimaryButton = ({ children, onClick, disabled, className, ...props }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={cn(
      "inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
      "hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2",
      disabled && "opacity-50 cursor-not-allowed",
      className
    )}
    style={{ 
      backgroundColor: '#2F8BFB', 
      color: '#FFFFFF',
      boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
    }}
    {...props}
  >
    {children}
  </button>
);

// Secondary button
export const SecondaryButton = ({ children, onClick, disabled, className, ...props }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={cn(
      "inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
      "hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2",
      disabled && "opacity-50 cursor-not-allowed",
      className
    )}
    style={{ 
      backgroundColor: 'transparent', 
      color: '#2F8BFB',
      border: '1px solid #2F8BFB'
    }}
    {...props}
  >
    {children}
  </button>
);

// Table wrapper
export const TableWrapper = ({ children }) => (
  <div 
    className="rounded-xl overflow-hidden"
    style={{ 
      backgroundColor: '#FFFFFF', 
      border: '1px solid #D7DCE2' 
    }}
  >
    {children}
  </div>
);

// Empty state
export const EmptyState = ({ icon: Icon, title, description, action }) => (
  <div className="text-center py-12">
    {Icon && (
      <div className="mx-auto w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: 'rgba(47, 139, 251, 0.1)' }}>
        <Icon className="h-6 w-6" style={{ color: '#2F8BFB' }} />
      </div>
    )}
    <h3 className="text-lg font-medium mb-1" style={{ color: '#1A1A1A' }}>{title}</h3>
    <p className="text-sm mb-4" style={{ color: '#5A5A5A' }}>{description}</p>
    {action}
  </div>
);
