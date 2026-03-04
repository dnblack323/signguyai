/**
 * ShellCard - Light card component for Dark Shell layout
 * 
 * Used to create white card sections on the dark app shell.
 * Multiple ShellCards with gap create visible dark space between sections.
 */

import { cn } from '../../lib/utils';

export const ShellCard = ({ 
  children, 
  className = '',
  padding = 'default', // 'none' | 'sm' | 'default' | 'lg'
  ...props 
}) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    default: 'p-5 lg:p-6',
    lg: 'p-6 lg:p-8',
  };

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-gray-200 shadow-sm",
        paddingStyles[padding],
        className
      )}
      style={{
        boxShadow: '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03)'
      }}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * ShellCardHeader - Header section within a ShellCard
 */
export const ShellCardHeader = ({ 
  children, 
  className = '',
  ...props 
}) => (
  <div 
    className={cn("flex items-center justify-between mb-4", className)}
    {...props}
  >
    {children}
  </div>
);

/**
 * ShellCardTitle - Title for ShellCard headers
 */
export const ShellCardTitle = ({ 
  children, 
  className = '',
  ...props 
}) => (
  <h2 
    className={cn(
      "text-xl lg:text-2xl font-bold text-gray-900 font-heading uppercase tracking-wide",
      className
    )}
    {...props}
  >
    {children}
  </h2>
);

/**
 * ShellCardSubtitle - Subtitle/description for ShellCard
 */
export const ShellCardSubtitle = ({ 
  children, 
  className = '',
  ...props 
}) => (
  <p 
    className={cn("text-sm text-gray-500", className)}
    {...props}
  >
    {children}
  </p>
);

/**
 * PageStack - Container for stacking multiple ShellCards with gaps
 * This ensures dark background is visible between cards
 */
export const PageStack = ({ 
  children, 
  className = '',
  gap = '24px',
  ...props 
}) => (
  <div 
    className={cn("flex flex-col", className)}
    style={{ gap }}
    {...props}
  >
    {children}
  </div>
);

export default ShellCard;
