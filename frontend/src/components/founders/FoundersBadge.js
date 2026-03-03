import { Crown } from 'lucide-react';
import { Badge } from '../ui/badge';

export const FoundersBadge = ({ size = 'default' }) => {
  const sizeClasses = {
    small: 'px-2 py-0.5 text-[10px]',
    default: 'px-3 py-1 text-xs',
    large: 'px-4 py-1.5 text-sm'
  };

  return (
    <Badge 
      className={`bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30 ${sizeClasses[size]}`}
      data-testid="founders-badge"
    >
      <Crown className={`mr-1 ${size === 'small' ? 'w-3 h-3' : 'w-4 h-4'}`} />
      Founding Shop
    </Badge>
  );
};

export default FoundersBadge;
