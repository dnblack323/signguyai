import { useState, useEffect, useCallback } from 'react';
import { Coins, AlertTriangle, Zap } from 'lucide-react';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthToken = () => localStorage.getItem('auth_token');

export const CreditMeter = ({ 
  variant = 'default', // 'default' | 'compact' | 'dashboard'
  onBuyCredits,
  className 
}) => {
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCredits = useCallback(async () => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch(`${API_URL}/api/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCredits(data);
      }
    } catch (error) {
      console.error('Failed to fetch credits:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCredits();
    const interval = setInterval(fetchCredits, 60000);
    return () => clearInterval(interval);
  }, [fetchCredits]);

  useEffect(() => {
    const handleRefresh = () => fetchCredits();
    window.addEventListener('creditsRefresh', handleRefresh);
    return () => window.removeEventListener('creditsRefresh', handleRefresh);
  }, [fetchCredits]);

  if (loading || !credits) {
    return null;
  }

  const { total_credits, monthly_credits, purchased_credits, is_low_credits, days_until_refill } = credits;
  const monthlyPercent = Math.round((monthly_credits / 150) * 100);

  // Dashboard variant - full card style
  if (variant === 'dashboard') {
    return (
      <div className={cn("p-4 rounded-lg border bg-card", className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              is_low_credits ? "bg-amber-500/20" : "bg-blue-500/20"
            )}>
              {is_low_credits ? (
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              ) : (
                <Coins className="w-4 h-4 text-blue-500" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium">AI Credits</p>
              <p className="text-xs text-muted-foreground">
                {days_until_refill} days until refill
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{total_credits}</p>
            <p className="text-xs text-muted-foreground">available</p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Monthly ({monthly_credits}/150)</span>
            <span className="text-muted-foreground">+{purchased_credits} purchased</span>
          </div>
          <Progress value={monthlyPercent} className="h-2" />
        </div>

        {is_low_credits && (
          <div className="mt-3 flex items-center justify-between p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
            <span className="text-xs text-amber-600">Credits running low</span>
            {onBuyCredits && (
              <Button 
                size="sm" 
                variant="outline" 
                onClick={onBuyCredits}
                className="h-7 text-xs border-amber-500 text-amber-600 hover:bg-amber-500/10"
              >
                Buy Credits
              </Button>
            )}
          </div>
        )}
      </div>
    );
  }

  // Compact variant - inline style
  if (variant === 'compact') {
    return (
      <div className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm",
        is_low_credits ? "bg-amber-50 text-amber-700" : "bg-gray-50 text-gray-700",
        className
      )}>
        <Coins className="w-4 h-4" />
        <span className="font-medium">{total_credits}</span>
        {is_low_credits && (
          <AlertTriangle className="w-3 h-3 text-amber-500" />
        )}
      </div>
    );
  }

  // Default variant - medium detail
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-lg border",
        is_low_credits 
          ? "bg-amber-50 border-amber-200" 
          : "bg-blue-50 border-blue-200"
      )}>
        <Zap className={cn(
          "w-4 h-4",
          is_low_credits ? "text-amber-500" : "text-blue-500"
        )} />
        <div>
          <p className="text-sm font-semibold">{total_credits} credits</p>
          <p className="text-xs text-muted-foreground">
            {monthly_credits} monthly • {purchased_credits} purchased
          </p>
        </div>
      </div>
      {is_low_credits && onBuyCredits && (
        <Button 
          size="sm" 
          onClick={onBuyCredits}
          className="bg-amber-500 hover:bg-amber-600 text-white"
        >
          Buy More
        </Button>
      )}
    </div>
  );
};

export default CreditMeter;
