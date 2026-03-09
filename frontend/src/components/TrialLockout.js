import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Lock, Clock, Rocket, ArrowRight, Star, Tag, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const TrialLockout = ({ children }) => {
  const navigate = useNavigate();
  const { isAuthenticated, token, user } = useAuth();
  const [trialStatus, setTrialStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkInterval, setCheckInterval] = useState(null);

  useEffect(() => {
    if (isAuthenticated && token) {
      checkTrialStatus();
      
      // Check every minute for trial expiry
      const interval = setInterval(checkTrialStatus, 60000);
      setCheckInterval(interval);
      
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  const checkTrialStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/trial-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to check trial status:', error);
      // On error, assume not locked to avoid blocking legitimate users
      setTrialStatus({ is_locked: false });
    } finally {
      setLoading(false);
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Trial lockout - show lockout screen if trial is expired
  if (trialStatus?.is_locked) {
    return <LockoutScreen />;
  }

  // Otherwise, render children normally
  return children;
};

const LockoutScreen = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [promoCode, setPromoCode] = useState('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [promoLoading, setPromoLoading] = useState(false);

  const handleCheckout = async (billingInterval = 'monthly') => {
    if (!token) {
      toast.error('Please log in first');
      return;
    }

    setCheckoutLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/checkout/founders`,
        {
          billing_interval: billingInterval,
          origin_url: window.location.origin
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Redirect to Stripe checkout - promo codes can be entered there
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
      setCheckoutLoading(false);
    }
  };

  const handleApplyPromoCode = async () => {
    if (!promoCode.trim()) {
      toast.error('Please enter a promo code');
      return;
    }

    if (!token) {
      toast.error('Please log in first');
      return;
    }

    setPromoLoading(true);
    try {
      // Try the new apply-promo endpoint first
      let response;
      try {
        response = await axios.post(
          `${API_URL}/api/billing/apply-promo`,
          { promo_code: promoCode.trim() },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } catch (e) {
        // If that fails, try the promo-codes/redeem endpoint
        response = await axios.post(
          `${API_URL}/api/promo-codes/redeem/${promoCode.trim().toUpperCase()}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      }

      if (response.data.success || response.data.access_granted) {
        toast.success(response.data.message || 'Promo code applied!');
        // Reload to check new trial status
        window.location.reload();
      } else if (response.data.message) {
        toast.info(response.data.message);
      } else {
        toast.error('Invalid promo code');
      }
    } catch (error) {
      console.error('Promo error:', error);
      const detail = error.response?.data?.detail;
      if (detail) {
        toast.error(detail);
      } else {
        toast.error('Failed to apply promo code');
      }
    } finally {
      setPromoLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[var(--bg-primary)]">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-red-500/5 via-transparent to-transparent" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
      
      <div className="relative min-h-screen flex flex-col items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          {/* Lock Icon */}
          <div className="relative mx-auto mb-8">
            <div className="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center mx-auto">
              <Lock className="w-12 h-12 text-red-500" />
            </div>
            <div className="absolute -top-2 -right-2 w-10 h-10 rounded-full bg-amber-500 flex items-center justify-center shadow-lg animate-bounce">
              <Clock className="w-5 h-5 text-white" />
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)] mb-4">
            Your Free Trial Has Ended
          </h1>
          
          <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-md mx-auto">
            Your 48-hour free trial is over. Subscribe to continue using SignGuy AI 
            and keep running your sign shop like a pro.
          </p>

          {/* Promo Code Section */}
          <div className="mb-6 p-4 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
            <div className="flex items-center gap-2 mb-3">
              <Tag className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-medium text-[var(--text-primary)]">Have a promo code?</span>
            </div>
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Enter promo code"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                className="flex-1 bg-[var(--bg-secondary)] border-[var(--border-color)]"
                onKeyDown={(e) => e.key === 'Enter' && handleApplyPromoCode()}
              />
              <Button
                onClick={handleApplyPromoCode}
                disabled={promoLoading}
                variant="outline"
                className="px-4"
              >
                {promoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Apply'}
              </Button>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3 mb-8">
            <Button
              onClick={() => handleCheckout('monthly')}
              disabled={checkoutLoading}
              className="w-full sm:w-auto px-8 py-6 text-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-90 text-black font-semibold shadow-lg shadow-amber-500/25"
              data-testid="get-founders-monthly-btn"
            >
              {checkoutLoading ? (
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              ) : (
                <Rocket className="w-5 h-5 mr-2" />
              )}
              Get Founders Edition - $99/mo
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            
            <div className="text-sm text-[var(--text-secondary)]">or</div>
            
            <Button
              onClick={() => handleCheckout('annual')}
              disabled={checkoutLoading}
              variant="outline"
              className="w-full sm:w-auto px-6 py-4"
              data-testid="get-founders-annual-btn"
            >
              Annual Plan - $594/year (Save 50% with FOUNDERS code)
            </Button>
          </div>

          {/* Founder spots reminder */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/30 mb-8">
            <Star className="w-4 h-4 text-amber-500" />
            <span className="text-sm text-amber-400">
              Only 100 Founder spots available - lock in lifetime pricing!
            </span>
          </div>

          {/* What you get */}
          <div className="bg-[var(--card-bg)] rounded-xl p-6 border border-[var(--border-color)] text-left">
            <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
              What You'll Unlock
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                'Customer Management',
                'Quotes & Jobs',
                'Invoicing',
                'Time Clock',
                '150 AI Credits/mo',
                'Unlimited Webstores',
                'Analytics',
                'And much more...'
              ].map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-[var(--text-primary)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  {feature}
                </div>
              ))}
            </div>
          </div>

          {/* Founder pricing reminder */}
          <p className="mt-8 text-sm text-[var(--text-secondary)]">
            <span className="text-amber-400 font-semibold">Founders Edition</span> — 
            All features, lifetime locked pricing, no restrictions
          </p>
          
          {/* Note about promo at checkout */}
          <p className="mt-4 text-xs text-[var(--text-secondary)]">
            You can also enter promo codes at the Stripe checkout page
          </p>
        </div>
      </div>
    </div>
  );
};

// Trial countdown banner component (for header/sidebar use)
export const TrialCountdown = () => {
  const { isAuthenticated, token } = useAuth();
  const [trialStatus, setTrialStatus] = useState(null);

  useEffect(() => {
    if (isAuthenticated && token) {
      checkTrialStatus();
      const interval = setInterval(checkTrialStatus, 60000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, token]);

  const checkTrialStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/trial-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to check trial status:', error);
    }
  };

  if (!trialStatus?.is_trial) return null;

  const timeRemaining = trialStatus.hours_remaining 
    ? `${Math.floor(trialStatus.hours_remaining)}h ${Math.round((trialStatus.hours_remaining % 1) * 60)}m`
    : trialStatus.days_remaining
    ? `${Math.floor(trialStatus.days_remaining)} days`
    : null;

  if (!timeRemaining) return null;

  const isUrgent = (trialStatus.hours_remaining && trialStatus.hours_remaining < 4) ||
                   (trialStatus.days_remaining && trialStatus.days_remaining < 2);

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
      isUrgent 
        ? 'bg-red-500/10 text-red-500 border border-red-500/30'
        : 'bg-amber-500/10 text-amber-500 border border-amber-500/30'
    }`}>
      <Clock className="w-3.5 h-3.5" />
      <span>
        {trialStatus.trial_type === 'free_trial' ? 'Free trial: ' : 'Trial: '}
        {timeRemaining} left
      </span>
    </div>
  );
};

export default TrialLockout;
