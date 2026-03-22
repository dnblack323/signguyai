import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Lock, Clock, Rocket, ArrowRight, Star, Loader2, Tag } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { useAuth } from '../context/AuthContext';

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

  // Grace period - read-only mode with banner
  if (trialStatus?.is_grace_period && trialStatus?.read_only) {
    return (
      <>
        <GracePeriodBanner daysRemaining={trialStatus.grace_days_remaining} />
        {children}
      </>
    );
  }

  // Otherwise, render children normally
  return children;
};

const LockoutScreen = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [promoCode, setPromoCode] = useState('');
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoMessage, setPromoMessage] = useState(null);

  const handleApplyPromo = async () => {
    if (!promoCode.trim()) return;
    setPromoLoading(true);
    setPromoMessage(null);
    try {
      const res = await axios.post(`${API_URL}/api/billing/apply-promo`, 
        { code: promoCode },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setPromoMessage({ type: 'success', text: res.data.message || 'Promo code applied!' });
      setTimeout(() => window.location.reload(), 1500);
    } catch (err) {
      setPromoMessage({ type: 'error', text: err.response?.data?.detail || 'Invalid promo code' });
    } finally {
      setPromoLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[var(--bg-primary)]">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-red-500/5 via-transparent to-transparent" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl" />
      
      <div className="relative min-h-screen flex flex-col items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          {/* Lock Icon */}
          <div className="relative mx-auto mb-8">
            <div className="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center mx-auto">
              <Lock className="w-12 h-12 text-red-500" />
            </div>
            <div className="absolute -top-2 -right-2 w-10 h-10 rounded-full bg-violet-500 flex items-center justify-center shadow-lg animate-bounce">
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

          {/* CTA Buttons */}
          <div className="space-y-4 mb-8">
            <Button
              onClick={() => navigate('/pricing')}
              className="w-full sm:w-auto px-8 py-6 text-lg bg-gradient-to-r from-violet-500 to-purple-500 hover:opacity-90 text-white font-semibold shadow-lg shadow-violet-500/25"
              data-testid="lockout-subscribe-btn"
            >
              <Rocket className="w-5 h-5 mr-2" />
              Get Founders Edition - $99/mo
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>

          {/* Promo Code Input */}
          <div className="mb-8 max-w-sm mx-auto">
            <p className="text-sm text-[var(--text-secondary)] mb-2">Have a promo code?</p>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" />
                <Input
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                  placeholder="Enter code"
                  className="pl-9 font-mono bg-[var(--card-bg)] border-[var(--border-color)] text-[var(--text-primary)]"
                  data-testid="lockout-promo-input"
                  onKeyDown={(e) => e.key === 'Enter' && handleApplyPromo()}
                />
              </div>
              <Button
                onClick={handleApplyPromo}
                disabled={promoLoading || !promoCode.trim()}
                variant="outline"
                className="border-[var(--border-color)]"
                data-testid="lockout-promo-apply-btn"
              >
                {promoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Apply'}
              </Button>
            </div>
            {promoMessage && (
              <p className={`text-sm mt-2 ${promoMessage.type === 'success' ? 'text-green-400' : 'text-red-400'}`}
                 data-testid="lockout-promo-message">
                {promoMessage.text}
              </p>
            )}
          </div>

          {/* Founder spots reminder */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/30 mb-8">
            <Star className="w-4 h-4 text-violet-500" />
            <span className="text-sm text-violet-400">
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
                  <div className="w-1.5 h-1.5 rounded-full bg-violet-500" />
                  {feature}
                </div>
              ))}
            </div>
          </div>

          {/* Founder pricing reminder */}
          <p className="mt-8 text-sm text-[var(--text-secondary)]">
            <span className="text-violet-400 font-semibold">Founders Edition</span> — 
            All features, lifetime locked pricing, no restrictions
          </p>
        </div>
      </div>
    </div>
  );
};

// Grace period banner - read-only mode notification
const GracePeriodBanner = ({ daysRemaining }) => {
  const navigate = useNavigate();
  const days = Math.ceil(daysRemaining || 0);
  const isUrgent = days <= 3;

  return (
    <div className={`fixed top-0 left-0 right-0 z-[60] px-4 py-3 text-center text-sm font-medium ${
      isUrgent
        ? 'bg-red-600 text-white'
        : 'bg-violet-600 text-white'
    }`} data-testid="grace-period-banner">
      <div className="max-w-4xl mx-auto flex items-center justify-center gap-3 flex-wrap">
        <Lock className="w-4 h-4 flex-shrink-0" />
        <span>
          Your subscription has lapsed. You have <strong>{days} day{days !== 1 ? 's' : ''}</strong> of read-only access remaining.
          You can view data and download backups, but cannot add new data.
        </span>
        <button
          onClick={() => navigate('/pricing')}
          className={`px-4 py-1 rounded-full text-xs font-bold transition ${
            isUrgent
              ? 'bg-white text-red-600 hover:bg-red-50'
              : 'bg-white text-violet-600 hover:bg-violet-50'
          }`}
          data-testid="grace-period-resubscribe-btn"
        >
          Resubscribe Now
        </button>
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
        : 'bg-violet-500/10 text-violet-500 border border-violet-500/30'
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
