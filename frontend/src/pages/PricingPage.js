import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Crown, Sparkles, Zap, Check, Star, Clock, 
  ArrowRight, Shield, Rocket, Building2, Users,
  BarChart3, Lock, Gift, Cpu, Palette, MessageSquare,
  FileText, TrendingUp
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Tier icons and colors
const tierConfig = {
  tier_1: { 
    icon: Zap, 
    gradient: 'from-slate-500 to-slate-600',
    bgGlow: 'bg-slate-500/10',
    color: 'slate'
  },
  tier_2: { 
    icon: Sparkles, 
    gradient: 'from-blue-500 to-indigo-600',
    bgGlow: 'bg-blue-500/10',
    color: 'blue'
  },
  tier_3: { 
    icon: Crown, 
    gradient: 'from-amber-500 to-orange-600',
    bgGlow: 'bg-amber-500/10',
    color: 'amber'
  },
  ai_addon: {
    icon: Cpu,
    gradient: 'from-purple-500 to-pink-600',
    bgGlow: 'bg-purple-500/10',
    color: 'purple'
  },
  extended_trial: {
    icon: Rocket,
    gradient: 'from-emerald-500 to-teal-600',
    bgGlow: 'bg-emerald-500/10',
    color: 'emerald'
  }
};

export default function PricingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const [pricingData, setPricingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [selectedAddons, setSelectedAddons] = useState({});

  useEffect(() => {
    fetchPricing();
  }, []);

  const fetchPricing = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/pricing`);
      setPricingData(response.data);
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
      toast.error('Failed to load pricing');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (planId, includeAddon = false) => {
    if (!isAuthenticated) {
      navigate('/?redirect=/pricing-plans');
      return;
    }

    setCheckoutLoading(planId);

    try {
      const response = await axios.post(
        `${API_URL}/api/billing/checkout`,
        {
          plan: planId,
          include_ai_addon: includeAddon || selectedAddons[planId],
          origin_url: window.location.origin
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error('Failed to start checkout. Please try again.');
      setCheckoutLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const { plans, addon, trial, is_founder_pricing, founders_remaining, founder_benefits } = pricingData || {};

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-amber-500/5 via-transparent to-transparent" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          {/* Founder Badge */}
          {is_founder_pricing && (
            <div className="flex justify-center mb-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 animate-pulse">
                <Star className="w-4 h-4 text-amber-500" />
                <span className="text-sm font-semibold text-amber-500">
                  Founder Pricing — Only {founders_remaining} of 100 spots left!
                </span>
                <Star className="w-4 h-4 text-amber-500" />
              </div>
            </div>
          )}

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-center text-[var(--text-primary)] mb-6">
            {is_founder_pricing ? (
              <>
                Lock In
                <span className="block mt-2 bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent">
                  Founder Pricing Forever
                </span>
              </>
            ) : (
              <>
                Choose Your
                <span className="block mt-2 bg-gradient-to-r from-blue-500 to-indigo-600 bg-clip-text text-transparent">
                  Perfect Plan
                </span>
              </>
            )}
          </h1>

          <p className="text-lg sm:text-xl text-[var(--text-secondary)] text-center max-w-2xl mx-auto mb-8">
            {is_founder_pricing 
              ? "Join the first 100 shops and keep these special rates for life — as long as your subscription stays active."
              : "Choose the plan that fits your shop. Upgrade or downgrade anytime."
            }
          </p>

          {/* Free Trial Banner */}
          <div className="flex justify-center mb-12">
            <div className="inline-flex items-center gap-4 px-6 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
              <Clock className="w-5 h-5 text-emerald-500" />
              <div className="text-left">
                <p className="text-sm font-semibold text-emerald-500">Start with a 24-hour free trial</p>
                <p className="text-xs text-[var(--text-secondary)]">Full access, no credit card required</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="grid md:grid-cols-3 gap-8 lg:gap-6">
          {plans?.map((plan, index) => {
            const config = tierConfig[plan.id] || tierConfig.tier_2;
            const Icon = config.icon;
            const isPopular = plan.is_popular;
            
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
                {isPopular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <div className="px-4 py-1.5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold shadow-lg">
                      Most Popular
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
                        {plan.display_name}
                      </h3>
                      {is_founder_pricing && (
                        <span className="text-xs font-semibold text-amber-500">FOUNDER</span>
                      )}
                    </div>
                  </div>

                  {/* Pricing */}
                  <div className="mb-6">
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-[var(--text-primary)]">
                        ${plan.amount}
                      </span>
                      <span className="text-[var(--text-secondary)]">/month</span>
                    </div>
                    
                    {/* Standard Price */}
                    {plan.standard_price && is_founder_pricing && (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm text-[var(--text-secondary)] line-through">
                          ${plan.standard_price}/mo after founder phase
                        </span>
                      </div>
                    )}

                    {/* Savings */}
                    {plan.savings && plan.savings > 0 && is_founder_pricing && (
                      <p className="text-sm font-semibold text-green-500 mt-1">
                        Save ${plan.savings}/month forever
                      </p>
                    )}

                    {/* Onboarding fee note */}
                    {plan.onboarding_fee === 0 && is_founder_pricing && (
                      <p className="text-xs text-amber-500 mt-2 flex items-center gap-1">
                        <Gift className="w-3 h-3" />
                        No onboarding fee (saves up to $599)
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
                        Get Started
                        <ArrowRight className="w-5 h-5" />
                      </span>
                    )}
                  </Button>

                  {/* Features */}
                  <div className="space-y-3">
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
      </div>

      {/* Extended Trial Section */}
      {trial && (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
          <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 p-6 lg:p-8">
            <div className="flex flex-col md:flex-row md:items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                    <Rocket className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-[var(--text-primary)]">
                    Need More Time to Decide?
                  </h3>
                </div>
                <p className="text-[var(--text-secondary)] mb-4">
                  Get a <span className="font-semibold text-emerald-500">14-day extended trial</span> for just ${trial.amount}. 
                  Full platform access with all features unlocked.
                </p>
                <div className="flex flex-wrap gap-3">
                  {trial.features?.slice(0, 3).map((feature, i) => (
                    <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-xs text-emerald-600">
                      <Check className="w-3 h-3" />
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-col items-center">
                <div className="text-3xl font-bold text-[var(--text-primary)] mb-2">
                  ${trial.amount}
                </div>
                <Button
                  onClick={() => handleSelectPlan('extended_trial')}
                  disabled={checkoutLoading === 'extended_trial'}
                  className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:opacity-90 text-white px-6"
                >
                  {checkoutLoading === 'extended_trial' ? 'Processing...' : 'Start Extended Trial'}
                </Button>
                <p className="text-xs text-[var(--text-secondary)] mt-2 text-center">
                  Credits toward Tier 3 subscription
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Tools Add-On Section */}
      {addon && (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
          <div className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-500/5 to-pink-500/5 p-6 lg:p-8">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-[var(--text-primary)]">
                      {addon.display_name}
                    </h3>
                    {is_founder_pricing && (
                      <span className="text-xs font-semibold text-amber-500">FOUNDER PRICING</span>
                    )}
                  </div>
                </div>
                <p className="text-[var(--text-secondary)] mb-4">
                  Already using another management system? Get access to all our AI tools as a standalone subscription.
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {addon.features?.map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-[var(--text-primary)]">
                      <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                      {feature}
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex flex-col items-center justify-center">
                <div className="text-center mb-3">
                  <div className="text-3xl font-bold text-[var(--text-primary)]">
                    ${addon.amount}
                  </div>
                  <div className="text-sm text-[var(--text-secondary)]">/month</div>
                  {addon.standard_price && is_founder_pricing && (
                    <div className="text-xs text-[var(--text-secondary)] line-through">
                      ${addon.standard_price}/mo later
                    </div>
                  )}
                </div>
                <Button
                  onClick={() => handleSelectPlan('ai_addon')}
                  disabled={checkoutLoading === 'ai_addon'}
                  className="bg-gradient-to-r from-purple-500 to-pink-600 hover:opacity-90 text-white px-6"
                >
                  {checkoutLoading === 'ai_addon' ? 'Processing...' : 'Get AI Tools'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Founder Benefits Section */}
      {is_founder_pricing && founder_benefits?.length > 0 && (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-[var(--text-primary)] mb-4">
              Why Become a Founder?
            </h2>
            <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
              The first 100 shops get exclusive benefits that will never be offered again.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Lock, title: "Lifetime Pricing", desc: "Your rate never increases, even when we raise prices." },
              { icon: Gift, title: "No Onboarding Fees", desc: "Save up to $599 that future customers will pay." },
              { icon: Rocket, title: "Early Feature Access", desc: "Be first to try new features before public release." },
              { icon: MessageSquare, title: "Direct Developer Access", desc: "Questions? Suggestions? Talk directly with me." },
              { icon: Users, title: "Shape the Product", desc: "Your feedback directly influences what we build." },
              { icon: Shield, title: "Founding Member Badge", desc: "Show off your early supporter status." },
            ].map((benefit, i) => (
              <div key={i} className="p-5 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
                <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center mb-3">
                  <benefit.icon className="w-5 h-5 text-amber-500" />
                </div>
                <h3 className="text-base font-semibold text-[var(--text-primary)] mb-1">
                  {benefit.title}
                </h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  {benefit.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trust Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="text-center">
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
