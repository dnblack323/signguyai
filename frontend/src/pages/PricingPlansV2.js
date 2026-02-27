import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Crown, Sparkles, Zap, Check, Star, Building2, 
  ArrowRight, Shield, Rocket, Store, Cpu, Palette,
  ChevronDown, ChevronUp, Gift, Users, BarChart3,
  Lock, Menu, X, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Product line configurations
const productLineConfig = {
  os: {
    name: 'SignGuy AI OS',
    tagline: 'Complete Shop Management',
    description: 'Everything you need to run your sign shop - customers, jobs, invoices, employees, and more.',
    icon: Building2,
    gradient: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-500/10',
    color: 'blue',
    hasFounderPricing: true,
  },
  webstores: {
    name: 'SignGuy Webstores',
    tagline: 'Sell Online, Your Way',
    description: 'Launch B2B stores, fundraisers, or creator shops. No shop management features - just commerce.',
    icon: Store,
    gradient: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-500/10',
    color: 'emerald',
    hasFounderPricing: false,
  },
  ai_studio: {
    name: 'SignGuy AI Studio',
    tagline: 'AI-Powered Creativity',
    description: 'Access our full suite of AI tools - text generation, image creation, and business assistant.',
    icon: Cpu,
    gradient: 'from-purple-500 to-pink-600',
    bgColor: 'bg-purple-500/10',
    color: 'purple',
    hasFounderPricing: false,
  },
};

// Plan tier configurations
const planTierConfig = {
  os_starter: { icon: Zap, popular: false },
  os_pro: { icon: Sparkles, popular: true },
  os_business: { icon: Crown, popular: false },
  ws_launch: { icon: Rocket, popular: false },
  ws_growth: { icon: BarChart3, popular: true },
  ws_scale: { icon: Store, popular: false },
  ai_basic: { icon: Palette, popular: false },
  ai_pro: { icon: Sparkles, popular: true },
  ai_max: { icon: Crown, popular: false },
};

// Features by plan (simplified display)
const planFeatures = {
  os_starter: [
    'Customer Management',
    'Quotes & Jobs',
    'Basic Invoicing (No Online Payments)',
    'Basic Time Clock',
    '2 Team Members',
    '25 AI Text Generations/mo',
    '10 AI Assistant Queries/mo',
  ],
  os_pro: [
    'Everything in Starter, plus:',
    'Online Invoice Payments (1% fee)',
    'Up to 3 Webstores (3% fee)',
    'Advanced Time Clock & Payroll',
    '10 Team Members',
    '100 AI Generations/mo',
    '50 AI Assistant Queries/mo',
    'Customer Portal Access',
  ],
  os_business: [
    'Everything in Pro, plus:',
    'Unlimited Webstores (2% fee)',
    'Unlimited Team Members',
    'Unlimited AI Generations',
    'Unlimited AI Queries',
    'Full Business Data AI Access',
    'Advanced Analytics & Financials',
    'Priority Support',
  ],
  ws_launch: [
    '1 Webstore',
    'B2B & Fundraiser Stores',
    'Stripe Connect Integration',
    'Order Management',
    'Basic Analytics',
    '3% Processing Fee',
  ],
  ws_growth: [
    'Up to 5 Webstores',
    'All Store Types (incl. Creator)',
    'Advanced Branding',
    'Price Overrides',
    'Commission Tracking',
    '2.5% Processing Fee',
  ],
  ws_scale: [
    'Unlimited Webstores',
    'Advanced Analytics',
    'Bulk Order Tools',
    'Payout Tracking',
    'Full Customization',
    '2% Processing Fee',
  ],
  ai_basic: [
    '25 AI Text Generations/mo',
    '10 AI Assistant Queries/mo',
    'No Image Generation',
    'No Business Data Access',
  ],
  ai_pro: [
    '100 AI Text Generations/mo',
    '50 AI Assistant Queries/mo',
    'Image Generation Included',
    'No Business Data Access',
  ],
  ai_max: [
    'Unlimited AI Generations',
    'Unlimited AI Queries',
    'Full Image Generation',
    'Branding Kit Generator',
    'Campaign Builder',
    'Pricing Intelligence',
  ],
};

export default function PricingPlansV2() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const [plans, setPlans] = useState({});
  const [founderStatus, setFounderStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [selectedProductLine, setSelectedProductLine] = useState('os');
  const [billingInterval, setBillingInterval] = useState('monthly');
  const [expandedFAQ, setExpandedFAQ] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    fetchPlans();
    fetchFounderStatus();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/plans/all`);
      // API returns array of { product_line, display_name, plans: [...] }
      const grouped = {};
      response.data.forEach(productLine => {
        grouped[productLine.product_line] = productLine.plans;
      });
      setPlans(grouped);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      toast.error('Failed to load pricing');
    } finally {
      setLoading(false);
    }
  };

  const fetchFounderStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/plans/founder-status`);
      setFounderStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch founder status:', error);
    }
  };

  const handleCheckout = async (planType, useFounder = false) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/pricing-plans', planType } });
      return;
    }

    setCheckoutLoading(planType);

    try {
      const response = await axios.post(
        `${API_URL}/api/billing/checkout/v2`,
        {
          plan_type: planType,
          billing_interval: billingInterval,
          use_founder_pricing: useFounder,
          origin_url: window.location.origin,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start checkout');
    } finally {
      setCheckoutLoading(null);
    }
  };

  const currentPlans = plans[selectedProductLine] || [];
  const currentConfig = productLineConfig[selectedProductLine];

  const faqs = [
    {
      question: 'Which product line should I choose?',
      answer: 'Choose OS if you want full shop management (customers, jobs, invoices, employees). Choose Webstores if you only need to sell online. Choose AI Studio if you just want access to our AI tools without the other features.',
    },
    {
      question: 'What is Founder pricing?',
      answer: 'The first 100 subscribers to any OS plan become Founders and lock in their rate forever. Founder pricing is only available for OS plans, not Webstores or AI Studio.',
    },
    {
      question: 'Can I switch between product lines?',
      answer: 'Yes! You can upgrade, downgrade, or switch product lines at any time. Changes take effect on your next billing cycle.',
    },
    {
      question: 'What are processing fees?',
      answer: 'Processing fees are charged on payments you receive through our platform (invoice payments and webstore sales). They cover secure payment processing, compliance, and infrastructure. Stripe\'s base fees (2.9% + $0.30) apply separately.',
    },
    {
      question: 'Is annual billing available?',
      answer: 'Annual billing is currently only available for OS Business plan. It includes discounted pricing and founder annual rates.',
    },
    {
      question: 'Do you offer refunds?',
      answer: 'Yes, we offer a 30-day money-back guarantee on all plans. If SignGuy AI isn\'t right for you, we\'ll refund your payment.',
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0B0F17]/90 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/home" className="flex items-center gap-3">
              <img 
                src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
                alt="TheSignGuy AI" 
                className="h-10 w-auto" 
              />
            </Link>
            
            <div className="hidden md:flex items-center gap-6">
              <Link to="/features" className="text-gray-300 hover:text-white transition">Features</Link>
              <Link to="/pricing-plans" className="text-[#2F8BFB] font-medium">Pricing</Link>
              <Link to="/about" className="text-gray-300 hover:text-white transition">About</Link>
              <Link to="/docs" className="text-gray-300 hover:text-white transition">Docs</Link>
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0]">Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" className="text-gray-300 hover:text-white">Log In</Button>
                  </Link>
                  <Link to="/login">
                    <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0]">Get Started</Button>
                  </Link>
                </>
              )}
            </div>

            <button 
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 bg-[#0B0F17] pt-16 md:hidden">
          <div className="flex flex-col p-6 gap-4">
            <Link to="/features" className="text-lg py-2" onClick={() => setMobileMenuOpen(false)}>Features</Link>
            <Link to="/pricing-plans" className="text-lg py-2 text-[#2F8BFB]" onClick={() => setMobileMenuOpen(false)}>Pricing</Link>
            <Link to="/about" className="text-lg py-2" onClick={() => setMobileMenuOpen(false)}>About</Link>
            <Link to="/docs" className="text-lg py-2" onClick={() => setMobileMenuOpen(false)}>Docs</Link>
            <hr className="border-white/10 my-2" />
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button className="w-full bg-[#2F8BFB] hover:bg-[#1E7AF0]">Log In / Sign Up</Button>
            </Link>
          </div>
        </div>
      )}

      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">
            Choose Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#2F8BFB] to-purple-500">SignGuy</span> Plan
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Three product lines, nine plans. Pick what fits your business.
          </p>
        </div>

        {/* Founder Banner */}
        {founderStatus && founderStatus.founder_available && (
          <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 rounded-xl p-4 mb-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <Crown className="w-6 h-6 text-amber-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-amber-400">Founder Spots Available!</h3>
                  <p className="text-sm text-gray-300">
                    {founderStatus.founder_spots_remaining} of {founderStatus.founder_spots_total} spots remaining
                  </p>
                </div>
              </div>
              <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                OS Plans Only
              </Badge>
            </div>
          </div>
        )}

        {/* Product Line Tabs */}
        <div className="flex flex-wrap justify-center gap-3 mb-8">
          {Object.entries(productLineConfig).map(([key, config]) => {
            const Icon = config.icon;
            const isActive = selectedProductLine === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedProductLine(key)}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all ${
                  isActive 
                    ? `bg-gradient-to-r ${config.gradient} text-white shadow-lg` 
                    : 'bg-[#111826] text-gray-300 hover:bg-[#1a2235]'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{config.name}</span>
              </button>
            );
          })}
        </div>

        {/* Product Line Description */}
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold mb-2">{currentConfig.tagline}</h2>
          <p className="text-gray-400 max-w-xl mx-auto">{currentConfig.description}</p>
          {currentConfig.hasFounderPricing && founderStatus?.founder_available && (
            <Badge className="mt-3 bg-amber-500/20 text-amber-400 border-amber-500/30">
              <Crown className="w-3 h-3 mr-1" /> Founder Pricing Available
            </Badge>
          )}
        </div>

        {/* Billing Toggle (only for OS Business) */}
        {selectedProductLine === 'os' && (
          <div className="flex justify-center mb-8">
            <div className="bg-[#111826] rounded-lg p-1 flex gap-1">
              <button
                onClick={() => setBillingInterval('monthly')}
                className={`px-4 py-2 rounded-md transition ${
                  billingInterval === 'monthly' ? 'bg-[#2F8BFB] text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingInterval('annual')}
                className={`px-4 py-2 rounded-md transition ${
                  billingInterval === 'annual' ? 'bg-[#2F8BFB] text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                Annual <span className="text-xs opacity-75">(Business only)</span>
              </button>
            </div>
          </div>
        )}

        {/* Plans Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {currentPlans.map((plan) => {
            const tierConfig = planTierConfig[plan.plan_type] || { icon: Zap, popular: false };
            const Icon = tierConfig.icon;
            const features = planFeatures[plan.plan_type] || [];
            const isPopular = tierConfig.popular;
            const canUseFounder = currentConfig.hasFounderPricing && founderStatus?.founder_available;
            const showAnnual = selectedProductLine === 'os' && billingInterval === 'annual' && plan.plan_type === 'os_business';
            
            const displayPrice = canUseFounder 
              ? (showAnnual ? plan.founder_price_annual : plan.founder_price_monthly)
              : (showAnnual ? plan.price_annual : plan.price_monthly);
            
            const regularPrice = showAnnual ? plan.price_annual : plan.price_monthly;

            return (
              <Card 
                key={plan.plan_type}
                className={`relative bg-[#111826] border-[#1E293B] overflow-hidden ${
                  isPopular ? 'ring-2 ring-[#2F8BFB]' : ''
                }`}
              >
                {isPopular && (
                  <div className="absolute top-0 right-0 bg-[#2F8BFB] text-white text-xs font-medium px-3 py-1 rounded-bl-lg">
                    Most Popular
                  </div>
                )}
                
                <CardHeader className="pb-4">
                  <div className={`w-12 h-12 rounded-xl ${currentConfig.bgColor} flex items-center justify-center mb-4`}>
                    <Icon className={`w-6 h-6 text-${currentConfig.color}-400`} />
                  </div>
                  <CardTitle className="text-white text-xl">{plan.display_name}</CardTitle>
                  <p className="text-gray-400 text-sm">{plan.description}</p>
                </CardHeader>

                <CardContent>
                  {/* Pricing */}
                  <div className="mb-6">
                    {canUseFounder && plan.founder_price_monthly && (
                      <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 mb-2">
                        <Crown className="w-3 h-3 mr-1" /> Founder Price
                      </Badge>
                    )}
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-white">
                        ${displayPrice}
                      </span>
                      <span className="text-gray-400">
                        /{showAnnual ? 'year' : 'month'}
                      </span>
                    </div>
                    {canUseFounder && plan.founder_price_monthly && (
                      <p className="text-sm text-gray-500 mt-1">
                        <span className="line-through">${regularPrice}</span> regular price
                      </p>
                    )}
                    {showAnnual && plan.plan_type === 'os_business' && (
                      <p className="text-sm text-emerald-400 mt-1">
                        Save ${(plan.price_monthly * 12) - plan.price_annual} per year
                      </p>
                    )}
                  </div>

                  {/* Features */}
                  <ul className="space-y-3 mb-6">
                    {features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <Check className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* CTA Buttons */}
                  <div className="space-y-2">
                    {canUseFounder && plan.founder_price_monthly ? (
                      <>
                        <Button
                          onClick={() => handleCheckout(plan.plan_type, true)}
                          disabled={checkoutLoading === plan.plan_type}
                          className={`w-full bg-gradient-to-r ${currentConfig.gradient} hover:opacity-90`}
                        >
                          {checkoutLoading === plan.plan_type ? (
                            <span className="flex items-center gap-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
                              Loading...
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              <Crown className="w-4 h-4" />
                              Get Founder Pricing
                            </span>
                          )}
                        </Button>
                        <Button
                          onClick={() => handleCheckout(plan.plan_type, false)}
                          disabled={checkoutLoading === plan.plan_type}
                          variant="outline"
                          className="w-full border-[#2F8BFB]/50 text-[#2F8BFB] hover:bg-[#2F8BFB]/10"
                        >
                          Regular Price
                        </Button>
                      </>
                    ) : (
                      <Button
                        onClick={() => handleCheckout(plan.plan_type, false)}
                        disabled={checkoutLoading === plan.plan_type}
                        className={`w-full bg-gradient-to-r ${currentConfig.gradient} hover:opacity-90`}
                      >
                        {checkoutLoading === plan.plan_type ? (
                          <span className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white"></div>
                            Loading...
                          </span>
                        ) : (
                          <span className="flex items-center gap-2">
                            Get Started
                            <ArrowRight className="w-4 h-4" />
                          </span>
                        )}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Processing Fees Section */}
        <div className="bg-[#111826] border border-[#1E293B] rounded-xl p-6 mb-16">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#2F8BFB]" />
            Processing Fees
          </h3>
          <p className="text-gray-400 mb-6">
            Processing fees are charged on payments you receive through our platform. 
            Stripe's base fees (2.9% + $0.30) apply separately.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <h4 className="font-semibold text-blue-400 mb-2">OS Plans</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>Starter: No online payments</li>
                <li>Pro: 1% invoice, 3% webstore</li>
                <li>Business: 1% invoice, 2% webstore</li>
              </ul>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <h4 className="font-semibold text-emerald-400 mb-2">Webstore Plans</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>Launch: 3% on sales</li>
                <li>Growth: 2.5% on sales</li>
                <li>Scale: 2% on sales</li>
              </ul>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <h4 className="font-semibold text-purple-400 mb-2">AI Studio Plans</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>No processing fees</li>
                <li>AI tools only</li>
              </ul>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mb-16">
          <h3 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h3>
          <div className="max-w-3xl mx-auto space-y-3">
            {faqs.map((faq, idx) => (
              <div 
                key={idx}
                className="bg-[#111826] border border-[#1E293B] rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedFAQ(expandedFAQ === idx ? null : idx)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left"
                >
                  <span className="font-medium">{faq.question}</span>
                  {expandedFAQ === idx ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </button>
                {expandedFAQ === idx && (
                  <div className="px-6 pb-4 text-gray-400">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="text-center bg-gradient-to-r from-[#2F8BFB]/20 to-purple-500/20 border border-[#2F8BFB]/30 rounded-xl p-8">
          <h3 className="text-2xl font-bold mb-2">Ready to transform your sign shop?</h3>
          <p className="text-gray-400 mb-6">Start your free trial today. No credit card required.</p>
          <Link to="/login">
            <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0] px-8 py-3 text-lg">
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-[#0B0F17] border-t border-white/10 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-gray-400 text-sm">
            © 2025 TheSignGuy AI. All rights reserved.
          </div>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/about" className="text-gray-400 hover:text-white transition">About</Link>
            <Link to="/contact" className="text-gray-400 hover:text-white transition">Contact</Link>
            <Link to="/docs" className="text-gray-400 hover:text-white transition">Docs</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
