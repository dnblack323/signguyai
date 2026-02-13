import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Crown, Sparkles, Zap, Check, Star, Clock, 
  ArrowRight, Shield, Rocket, Building2, Users,
  BarChart3, Lock, Gift
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { useTier } from '../context/TierContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Plan icons and colors
const planConfig = {
  paid_trial: { 
    icon: Rocket, 
    gradient: 'from-emerald-500 to-teal-600',
    bgGlow: 'bg-emerald-500/10'
  },
  pro_monthly: { 
    icon: Sparkles, 
    gradient: 'from-blue-500 to-indigo-600',
    bgGlow: 'bg-blue-500/10'
  },
  pro_yearly: { 
    icon: Sparkles, 
    gradient: 'from-blue-500 to-indigo-600',
    bgGlow: 'bg-blue-500/10'
  },
  business_monthly: { 
    icon: Crown, 
    gradient: 'from-amber-500 to-orange-600',
    bgGlow: 'bg-amber-500/10'
  },
  business_yearly: { 
    icon: Crown, 
    gradient: 'from-amber-500 to-orange-600',
    bgGlow: 'bg-amber-500/10'
  },
};

export default function PricingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const { tier } = useTier();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly'); // monthly or yearly

  useEffect(() => {
    fetchPricing();
  }, []);

  const fetchPricing = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/pricing`);
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
      toast.error('Failed to load pricing');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (planId) => {
    if (!isAuthenticated) {
      // Redirect to login with return URL
      navigate('/?redirect=/pricing-plans');
      return;
    }

    setCheckoutLoading(planId);

    try {
      const response = await axios.post(
        `${API_URL}/api/billing/checkout`,
        {
          plan: planId,
          origin_url: window.location.origin
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error('Failed to start checkout. Please try again.');
      setCheckoutLoading(null);
    }
  };

  // Filter plans based on billing cycle
  const getDisplayPlans = () => {
    const trial = plans.find(p => p.id === 'paid_trial');
    const proPlan = plans.find(p => p.id === (billingCycle === 'yearly' ? 'pro_yearly' : 'pro_monthly'));
    const businessPlan = plans.find(p => p.id === (billingCycle === 'yearly' ? 'business_yearly' : 'business_monthly'));
    
    return [trial, proPlan, businessPlan].filter(Boolean);
  };

  const displayPlans = getDisplayPlans();

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-transparent" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          {/* Founder Badge */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30">
              <Star className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-semibold text-amber-500">
                Founder Member Pricing — Limited Time
              </span>
              <Star className="w-4 h-4 text-amber-500" />
            </div>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-center text-[var(--text-primary)] mb-6">
            Lock In Your Rate
            <span className="block mt-2 bg-gradient-to-r from-blue-500 to-amber-500 bg-clip-text text-transparent">
              Forever
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-[var(--text-secondary)] text-center max-w-2xl mx-auto mb-8">
            Join as a Founder Member and keep these special rates for life — 
            as long as your account stays active.
          </p>

          {/* Billing Toggle */}
          <div className="flex justify-center mb-12">
            <div className="inline-flex items-center p-1 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  billingCycle === 'monthly'
                    ? 'bg-[var(--card-bg)] text-[var(--text-primary)] shadow-sm'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                  billingCycle === 'yearly'
                    ? 'bg-[var(--card-bg)] text-[var(--text-primary)] shadow-sm'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Yearly
                <span className="px-2 py-0.5 rounded-full bg-green-500/20 text-green-500 text-xs font-semibold">
                  Save 32%
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid md:grid-cols-3 gap-8 lg:gap-6">
          {displayPlans.map((plan, index) => {
            const config = planConfig[plan.id] || planConfig.pro_monthly;
            const Icon = config.icon;
            const isPopular = plan.is_popular || plan.id.includes('pro_');
            const isTrial = plan.id === 'paid_trial';
            
            return (
              <div
                key={plan.id}
                className={`relative rounded-2xl border transition-all duration-300 hover:scale-[1.02] ${
                  isPopular 
                    ? 'border-blue-500/50 shadow-xl shadow-blue-500/10' 
                    : 'border-[var(--border-color)]'
                } bg-[var(--card-bg)]`}
              >
                {/* Popular Badge */}
                {isPopular && !isTrial && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <div className="px-4 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold shadow-lg">
                      Most Popular
                    </div>
                  </div>
                )}

                {/* Trial Badge */}
                {isTrial && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <div className="px-4 py-1.5 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-semibold shadow-lg flex items-center gap-1.5">
                      <Gift className="w-4 h-4" />
                      Try Everything
                    </div>
                  </div>
                )}

                <div className="p-6 lg:p-8">
                  {/* Plan Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.gradient} flex items-center justify-center`}>
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-[var(--text-primary)]">
                        {isTrial ? '14-Day Trial' : plan.tier === 'pro' ? 'Pro' : 'Business'}
                      </h3>
                      <p className="text-sm text-[var(--text-secondary)]">
                        {isTrial ? 'Full Pro Access' : plan.interval === 'year' ? 'Billed Yearly' : 'Billed Monthly'}
                      </p>
                    </div>
                  </div>

                  {/* Pricing */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-[var(--text-primary)]">
                        ${plan.amount}
                      </span>
                      {!isTrial && (
                        <span className="text-[var(--text-secondary)]">
                          /{plan.interval === 'year' ? 'year' : 'mo'}
                        </span>
                      )}
                    </div>
                    
                    {/* Regular Price Strikethrough */}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-[var(--text-secondary)] line-through">
                        ${plan.regular_price}
                      </span>
                      <span className="text-sm font-semibold text-green-500">
                        {isTrial ? '50% off' : `Save $${Math.round(plan.regular_price - plan.amount)}`}
                      </span>
                    </div>

                    {/* Monthly Equivalent for Yearly */}
                    {plan.monthly_equivalent && (
                      <p className="text-sm text-[var(--text-secondary)] mt-1">
                        That's just ${plan.monthly_equivalent}/month
                      </p>
                    )}

                    {/* Trial Credit Note */}
                    {isTrial && (
                      <p className="text-sm text-emerald-500 mt-2 flex items-center gap-1">
                        <Check className="w-4 h-4" />
                        Credits toward subscription
                      </p>
                    )}
                  </div>

                  {/* CTA Button */}
                  <Button
                    onClick={() => handleSelectPlan(plan.id)}
                    disabled={checkoutLoading === plan.id}
                    className={`w-full py-6 text-base font-semibold mb-6 ${
                      isPopular
                        ? `bg-gradient-to-r ${config.gradient} hover:opacity-90 text-white`
                        : 'bg-[var(--bg-secondary)] hover:bg-[var(--bg-primary)] text-[var(--text-primary)] border border-[var(--border-color)]'
                    }`}
                  >
                    {checkoutLoading === plan.id ? (
                      <span className="flex items-center gap-2">
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Processing...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        {isTrial ? 'Start Trial' : 'Get Started'}
                        <ArrowRight className="w-5 h-5" />
                      </span>
                    )}
                  </Button>

                  {/* Features */}
                  <div className="space-y-3">
                    <p className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                      {isTrial ? 'Includes:' : 'Everything in ' + (plan.tier === 'business' ? 'Pro, plus:' : 'Starter, plus:')}
                    </p>
                    {plan.features?.map((feature, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${config.gradient} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                          <Check className="w-3 h-3 text-white" />
                        </div>
                        <span className="text-sm text-[var(--text-primary)]">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Founder Benefits Section */}
        <div className="mt-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
              Why Become a Founder Member?
            </h2>
            <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
              Early supporters get exclusive benefits that will never be offered again.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-4">
                <Lock className="w-6 h-6 text-amber-500" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                Locked-In Pricing
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Your rate never increases. Even when we raise prices for new customers, 
                you keep your Founder rate forever.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-blue-500" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                Direct Access
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Founders get direct access to the dev team. Your feedback shapes the product. 
                Request features and see them built.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center mb-4">
                <BarChart3 className="w-6 h-6 text-emerald-500" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                Early Features
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                Be the first to try new features before they're released to everyone else. 
                Help us build the future of sign shop software.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ or Trust Section */}
        <div className="mt-20 text-center">
          <div className="inline-flex items-center gap-4 px-6 py-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
            <Shield className="w-5 h-5 text-green-500" />
            <span className="text-sm text-[var(--text-secondary)]">
              Secure payments via Stripe • Cancel anytime • 30-day money-back guarantee
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
