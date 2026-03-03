import { useState, useEffect, useCallback } from 'react';
import { Coins, AlertTriangle, Plus, Loader2, Sparkles } from 'lucide-react';
import { cn } from '../../lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Helper to get auth token
const getAuthToken = () => localStorage.getItem('auth_token');

export const CreditBalance = ({ compact = false }) => {
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchaseModalOpen, setPurchaseModalOpen] = useState(false);

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
  }, [getAuthToken]);

  useEffect(() => {
    fetchCredits();
    // Refresh credits every 60 seconds
    const interval = setInterval(fetchCredits, 60000);
    return () => clearInterval(interval);
  }, [fetchCredits]);

  // Listen for credit refresh events (after purchases)
  useEffect(() => {
    const handleRefresh = () => fetchCredits();
    window.addEventListener('creditsRefresh', handleRefresh);
    return () => window.removeEventListener('creditsRefresh', handleRefresh);
  }, [fetchCredits]);

  if (loading) {
    return (
      <div className="flex items-center gap-1.5 px-2 py-1">
        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!credits) return null;

  const { total_credits, monthly_credits, purchased_credits, is_low_credits, days_until_refill } = credits;

  if (compact) {
    return (
      <button
        onClick={() => setPurchaseModalOpen(true)}
        className={cn(
          "flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-colors",
          is_low_credits 
            ? "bg-amber-50 text-amber-700 hover:bg-amber-100" 
            : "bg-gray-50 text-gray-700 hover:bg-gray-100"
        )}
        data-testid="credit-balance-btn"
      >
        {is_low_credits ? (
          <AlertTriangle className="h-3.5 w-3.5" />
        ) : (
          <Coins className="h-3.5 w-3.5" />
        )}
        <span className="text-sm font-medium">{total_credits}</span>
        <CreditPurchaseModal 
          open={purchaseModalOpen} 
          onOpenChange={setPurchaseModalOpen}
          credits={credits}
          onPurchaseComplete={fetchCredits}
        />
      </button>
    );
  }

  return (
    <>
      <button
        onClick={() => setPurchaseModalOpen(true)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all",
          is_low_credits 
            ? "bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 text-amber-800 hover:border-amber-300" 
            : "bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 text-blue-800 hover:border-blue-300"
        )}
        data-testid="credit-balance-expanded-btn"
      >
        <div className="flex items-center gap-1.5">
          {is_low_credits ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : (
            <Sparkles className="h-4 w-4 text-blue-500" />
          )}
          <span className="font-semibold">{total_credits}</span>
          <span className="text-xs opacity-75">credits</span>
        </div>
        {is_low_credits && (
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-amber-100 border-amber-300 text-amber-700">
            LOW
          </Badge>
        )}
      </button>
      <CreditPurchaseModal 
        open={purchaseModalOpen} 
        onOpenChange={setPurchaseModalOpen}
        credits={credits}
        onPurchaseComplete={fetchCredits}
      />
    </>
  );
};

export const CreditPurchaseModal = ({ open, onOpenChange, credits, onPurchaseComplete }) => {
  const [packs, setPacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [purchasing, setPurchasing] = useState(null);

  useEffect(() => {
    if (open) {
      fetchPacks();
    }
  }, [open]);

  const fetchPacks = async () => {
    setLoading(true);
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_URL}/api/credits/packs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPacks(data.packs || []);
      }
    } catch (error) {
      console.error('Failed to fetch packs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (packType) => {
    setPurchasing(packType);
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_URL}/api/credits/purchase`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pack_type: packType })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
        }
      } else {
        toast.error('Failed to start checkout');
      }
    } catch (error) {
      console.error('Purchase error:', error);
      toast.error('Failed to process purchase');
    } finally {
      setPurchasing(null);
    }
  };

  const monthlyPercent = credits ? Math.round((credits.monthly_credits / 150) * 100) : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-500" />
            AI Credits
          </DialogTitle>
        </DialogHeader>

        {/* Current Balance */}
        {credits && (
          <div className="space-y-4 mb-6">
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Balance</p>
                <p className="text-3xl font-bold text-blue-900">{credits.total_credits}</p>
              </div>
              <Coins className="h-10 w-10 text-blue-400" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs text-gray-500">Monthly Credits</p>
                  <span className="text-xs text-gray-400">
                    {credits.days_until_refill}d until refill
                  </span>
                </div>
                <p className="text-lg font-semibold">{credits.monthly_credits}</p>
                <Progress value={monthlyPercent} className="h-1.5 mt-2" />
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 mb-1">Purchased Credits</p>
                <p className="text-lg font-semibold">{credits.purchased_credits}</p>
                <p className="text-xs text-green-600 mt-1">Never expire</p>
              </div>
            </div>

            {credits.is_low_credits && (
              <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <p className="text-sm">
                  Your credits are running low. Purchase more to continue using AI features.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Credit Packs */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm text-gray-700">Buy Credit Packs</h4>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-2">
              {packs.map((pack) => (
                <div
                  key={pack.pack_type}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg border transition-colors",
                    pack.pack_type === 'pack_300' 
                      ? "border-blue-200 bg-blue-50/50" 
                      : "border-gray-200 hover:border-gray-300"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center",
                      pack.pack_type === 'pack_100' && "bg-gray-100",
                      pack.pack_type === 'pack_300' && "bg-blue-100",
                      pack.pack_type === 'pack_1000' && "bg-purple-100"
                    )}>
                      <Coins className={cn(
                        "h-5 w-5",
                        pack.pack_type === 'pack_100' && "text-gray-600",
                        pack.pack_type === 'pack_300' && "text-blue-600",
                        pack.pack_type === 'pack_1000' && "text-purple-600"
                      )} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{pack.display_name}</p>
                        {pack.pack_type === 'pack_300' && (
                          <Badge className="bg-blue-500 text-[10px] px-1.5">POPULAR</Badge>
                        )}
                        {pack.pack_type === 'pack_1000' && (
                          <Badge variant="outline" className="text-[10px] px-1.5 border-purple-300 text-purple-700">
                            40% OFF
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-gray-500">{pack.credits} credits • {pack.per_credit}/credit</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handlePurchase(pack.pack_type)}
                    disabled={purchasing === pack.pack_type}
                    className={cn(
                      pack.pack_type === 'pack_300' && "bg-blue-600 hover:bg-blue-700"
                    )}
                    data-testid={`buy-pack-${pack.pack_type}`}
                  >
                    {purchasing === pack.pack_type ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      pack.price_display
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}

          <p className="text-xs text-gray-500 text-center mt-4">
            Purchased credits never expire • Secure payment via Stripe
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CreditBalance;
