import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  CheckCircle2, Star, Sparkles, ArrowRight,
  Zap, Shield, Crown, Store, Cpu, Building2,
  BarChart3, Rocket, Palette
} from 'lucide-react';

// Product line configurations
const productLines = [
  {
    id: 'os',
    name: 'SignGuy AI OS',
    tagline: 'Complete Shop Management',
    description: 'Everything you need to run your sign shop - customers, jobs, invoices, employees, webstores, and AI tools.',
    icon: Building2,
    color: 'blue',
    hasFounderPricing: true,
    plans: [
      {
        id: 'os_starter',
        name: 'Starter',
        price: 39,
        founderPrice: 29,
        annual: 390,
        founderAnnual: 290,
        icon: Zap,
        popular: false,
        features: [
          'Customer Management',
          'Quotes & Jobs',
          'Basic Invoicing',
          'Basic Time Clock',
          '2 Team Members',
          '25 AI Text Generations/mo',
          '10 AI Assistant Queries/mo',
        ],
      },
      {
        id: 'os_pro',
        name: 'Pro',
        price: 79,
        founderPrice: 59,
        annual: 790,
        founderAnnual: 590,
        icon: Sparkles,
        popular: true,
        features: [
          'Everything in Starter, plus:',
          'Online Invoice Payments',
          'Up to 3 Webstores',
          'Advanced Time Clock & Payroll',
          '10 Team Members',
          '100 AI Generations/mo',
          '50 AI Assistant Queries/mo',
          'Customer Portal Access',
        ],
      },
      {
        id: 'os_business',
        name: 'Business',
        price: 149,
        founderPrice: 99,
        annual: 1490,
        founderAnnual: 990,
        icon: Crown,
        popular: false,
        features: [
          'Everything in Pro, plus:',
          'Unlimited Webstores',
          'Unlimited Team Members',
          'Unlimited AI Generations',
          'Full Business Data AI',
          'Advanced Analytics',
          'Priority Support',
        ],
      },
    ],
  },
  {
    id: 'webstores',
    name: 'SignGuy Webstores',
    tagline: 'Sell Online, Your Way',
    description: 'Launch B2B stores, fundraisers, or creator shops. Perfect for existing sign shops using other software.',
    icon: Store,
    color: 'emerald',
    hasFounderPricing: false,
    plans: [
      {
        id: 'ws_launch',
        name: 'Launch',
        price: 39,
        annual: 390,
        icon: Rocket,
        popular: false,
        features: [
          '1 Webstore',
          'B2B & Fundraiser Stores',
          'Stripe Connect Integration',
          'Order Management',
          'Basic Store Analytics',
          '3% Processing Fee',
        ],
      },
      {
        id: 'ws_growth',
        name: 'Growth',
        price: 59,
        annual: 590,
        icon: BarChart3,
        popular: true,
        features: [
          'Up to 5 Webstores',
          'All Store Types (incl. Creator)',
          'Advanced Branding',
          'Price Overrides',
          'Commission Tracking',
          '2.5% Processing Fee',
        ],
      },
      {
        id: 'ws_scale',
        name: 'Scale',
        price: 99,
        annual: 990,
        icon: Store,
        popular: false,
        features: [
          'Unlimited Webstores',
          'Advanced Analytics',
          'Bulk Order Tools',
          'Payout Tracking',
          'All Premium Features',
          '2% Processing Fee',
        ],
      },
    ],
  },
  {
    id: 'ai_studio',
    name: 'SignGuy AI Studio',
    tagline: 'AI-Powered Creativity',
    description: 'Access our full suite of AI tools standalone. Great for designers and shops using other management software.',
    icon: Cpu,
    color: 'purple',
    hasFounderPricing: false,
    plans: [
      {
        id: 'ai_basic',
        name: 'AI Basic',
        price: 29,
        annual: 290,
        icon: Palette,
        popular: false,
        features: [
          'AI Text Generation',
          '25 Generations/month',
          'AI Business Assistant',
          '10 Assistant Queries/mo',
          'Sign Industry Templates',
        ],
      },
      {
        id: 'ai_pro',
        name: 'AI Pro',
        price: 59,
        annual: 590,
        icon: Sparkles,
        popular: true,
        features: [
          'Everything in Basic, plus:',
          'AI Image Generation',
          '100 Generations/month',
          '50 Assistant Queries/mo',
          'Advanced Prompts',
        ],
      },
      {
        id: 'ai_max',
        name: 'AI Max',
        price: 99,
        annual: 990,
        icon: Crown,
        popular: false,
        features: [
          'Everything in Pro, plus:',
          'Unlimited Generations',
          'Unlimited Queries',
          'Branding Kit Generator',
          'Campaign Builder',
          'Content Calendar',
        ],
      },
    ],
  },
];

// Color configurations
const colorConfig = {
  blue: {
    gradient: 'from-blue-500 to-indigo-600',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    text: 'text-blue-400',
    button: 'bg-blue-600 hover:bg-blue-700',
    badge: 'bg-blue-500',
  },
  emerald: {
    gradient: 'from-emerald-500 to-teal-600',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    button: 'bg-emerald-600 hover:bg-emerald-700',
    badge: 'bg-emerald-500',
  },
  purple: {
    gradient: 'from-purple-500 to-pink-600',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
    text: 'text-purple-400',
    button: 'bg-purple-600 hover:bg-purple-700',
    badge: 'bg-purple-500',
  },
};

export default function PricingPagePublic() {
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [activeProduct, setActiveProduct] = useState('os');

  const activeProductLine = productLines.find(p => p.id === activeProduct);
  const colors = colorConfig[activeProductLine?.color || 'blue'];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-4 bg-amber-500/20 text-amber-400 border-amber-500/30">
            <Star className="w-3 h-3 mr-1" />
            Founder Pricing Available - Limited Spots!
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Choose Your <span className="text-[#2F8BFB]">Perfect Plan</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
            Three product lines to match exactly what you need. Start with a 24-hour free trial.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 py-2 rounded-lg transition ${
                billingCycle === 'monthly'
                  ? 'bg-[#2F8BFB] text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-4 py-2 rounded-lg transition ${
                billingCycle === 'annual'
                  ? 'bg-[#2F8BFB] text-white'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20'
              }`}
            >
              Annual
              <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                Save 2 months
              </span>
            </button>
          </div>
        </div>
      </section>

      {/* Product Line Selector */}
      <section className="px-4 pb-8">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {productLines.map((product) => {
              const Icon = product.icon;
              const isActive = activeProduct === product.id;
              const prodColors = colorConfig[product.color];

              return (
                <button
                  key={product.id}
                  onClick={() => setActiveProduct(product.id)}
                  className={`p-6 rounded-xl border-2 transition-all text-left ${
                    isActive
                      ? `${prodColors.border} ${prodColors.bg}`
                      : 'border-white/10 hover:border-white/20 bg-white/5'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${prodColors.gradient} flex items-center justify-center mb-4`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className={`text-lg font-bold mb-1 ${isActive ? prodColors.text : 'text-white'}`}>
                    {product.name}
                  </h3>
                  <p className="text-sm text-gray-400">{product.tagline}</p>
                  {product.hasFounderPricing && (
                    <Badge className="mt-3 bg-amber-500/20 text-amber-400 border-amber-500/30 text-xs">
                      Founder Pricing Available
                    </Badge>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Product Description */}
      <section className="px-4 pb-8">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-gray-400">{activeProductLine?.description}</p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="px-4 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {activeProductLine?.plans.map((plan) => {
              const Icon = plan.icon;
              const price = billingCycle === 'annual' 
                ? (activeProductLine.hasFounderPricing ? plan.founderAnnual : plan.annual)
                : (activeProductLine.hasFounderPricing ? plan.founderPrice : plan.price);
              const monthlyEquivalent = billingCycle === 'annual' ? Math.round(price / 12) : price;

              return (
                <Card
                  key={plan.id}
                  className={`relative bg-[#111826] border-2 transition-all ${
                    plan.popular
                      ? `${colors.border} shadow-lg shadow-${activeProductLine.color}-500/20`
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  {plan.popular && (
                    <div className={`absolute -top-3 left-1/2 -translate-x-1/2 ${colors.badge} text-white text-xs font-bold px-3 py-1 rounded-full`}>
                      MOST POPULAR
                    </div>
                  )}

                  <CardContent className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colors.gradient} flex items-center justify-center`}>
                        <Icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                      </div>
                    </div>

                    <div className="mb-6">
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-bold text-white">${monthlyEquivalent}</span>
                        <span className="text-gray-400">/mo</span>
                      </div>
                      {billingCycle === 'annual' && (
                        <p className="text-sm text-gray-500 mt-1">
                          Billed ${price}/year
                        </p>
                      )}
                      {activeProductLine.hasFounderPricing && (
                        <p className="text-xs text-amber-400 mt-2">
                          <Star className="w-3 h-3 inline mr-1" />
                          Founder pricing (reg. ${billingCycle === 'annual' ? plan.annual : plan.price}/mo)
                        </p>
                      )}
                    </div>

                    <Link to="/login">
                      <Button
                        className={`w-full mb-6 ${
                          plan.popular
                            ? `${colors.button} text-white`
                            : 'bg-white/10 hover:bg-white/20 text-white'
                        }`}
                      >
                        Start Free Trial
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </Link>

                    <ul className="space-y-3">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${colors.text}`} />
                          <span className="text-gray-300">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Founder Benefits */}
      <section className="px-4 pb-16">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/30">
            <CardContent className="p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-amber-500 flex items-center justify-center">
                  <Crown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Founder Benefits</h3>
                  <p className="text-amber-400 text-sm">Only for SignGuy AI OS plans</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  'Lifetime locked-in pricing',
                  'No onboarding fees (save up to $599)',
                  'Early access to new features',
                  'Direct input into product development',
                  'Priority support channel',
                  'Limited to first 100 shops',
                ].map((benefit, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-amber-400" />
                    <span className="text-gray-300">{benefit}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-4 pb-16">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
          
          <div className="space-y-4">
            {[
              {
                q: 'What happens after the 24-hour free trial?',
                a: 'After your free trial, you can choose any plan to continue. You can also extend your trial for $19.99 which credits toward your subscription.',
              },
              {
                q: 'Can I switch between product lines?',
                a: 'Yes! You can switch between OS, Webstores, and AI Studio at any time. Your data is preserved and billing is prorated.',
              },
              {
                q: 'What are processing fees?',
                a: 'Processing fees apply to webstore transactions on top of Stripe\'s standard fees. They range from 2-3% depending on your plan.',
              },
              {
                q: 'Is there a contract or commitment?',
                a: 'No contracts! Pay monthly or annually. Cancel anytime. Annual plans save you 2 months.',
              },
            ].map((item, idx) => (
              <div key={idx} className="bg-[#111826] rounded-xl p-6 border border-white/10">
                <h3 className="font-semibold text-white mb-2">{item.q}</h3>
                <p className="text-gray-400 text-sm">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 pb-16">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to transform your sign shop?</h2>
          <p className="text-gray-400 mb-6">
            Start your free 24-hour trial today. No credit card required.
          </p>
          <Link to="/login">
            <Button size="lg" className="bg-[#2F8BFB] hover:bg-[#1E7AF0] text-white font-semibold text-lg px-8 py-6 h-auto">
              Start Your Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Trust Banner */}
      <section className="px-4 pb-16">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full border border-white/10 bg-[#111826]">
            <Shield className="w-5 h-5 text-green-400" />
            <span className="text-gray-300 text-sm">
              Secure payments via Stripe • Cancel anytime • 30-day money-back guarantee
            </span>
          </div>
        </div>
      </section>

      {/* Footer */}
      <PublicFooter />
    </div>
  );
}
