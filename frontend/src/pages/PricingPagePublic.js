import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  CheckCircle2, Star, Sparkles, ArrowRight, Menu, X,
  Zap, Clock, Shield, HelpCircle, Gift, Users, Crown
} from 'lucide-react';

export default function PricingPagePublic() {
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' or 'annual'

  const tiers = [
    {
      name: 'Starter Shop',
      icon: Zap,
      iconColor: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      description: 'Perfect for small shops just getting started',
      founderPrice: 79,
      regularPrice: 129,
      annualPrice: 79 * 11, // 1 month free
      savings: 50,
      features: [
        'Customer Management',
        'Quotes & Jobs',
        'Basic Invoicing',
        '1 Webstore',
        '25 AI generations/month',
        '1 Team member',
        '100MB Storage',
        'Email Support',
      ],
      popular: false,
    },
    {
      name: 'Growth Shop',
      icon: Users,
      iconColor: 'text-[#2F8BFB]',
      bgColor: 'bg-[#2F8BFB]/10',
      description: 'For growing shops that need more power',
      founderPrice: 129,
      regularPrice: 229,
      annualPrice: 129 * 11, // 1 month free
      savings: 100,
      inheritText: 'Everything in Starter, plus:',
      features: [
        '5 Webstores',
        '100 AI generations/month',
        '5 Team members',
        '1GB Storage',
        'Time Clock & Payroll',
        'Kanban & Calendar',
        'Advanced Analytics',
        'Priority Support',
      ],
      popular: true,
    },
    {
      name: 'Pro Shop',
      icon: Crown,
      iconColor: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
      description: 'Full power for serious operations',
      founderPrice: 199,
      regularPrice: 379,
      annualPrice: 199 * 11, // 1 month free
      savings: 180,
      inheritText: 'Everything in Growth, plus:',
      features: [
        'Unlimited Webstores',
        'Unlimited AI generations',
        'Unlimited Team members',
        '5GB Storage',
        'B2B Features',
        'BNPL Payments',
        'Custom Reports',
        'SMS Notifications',
        'API Access',
        'Dedicated Support',
      ],
      popular: false,
    },
  ];

  const faqs = [
    {
      question: 'What happens after my free trial?',
      answer: 'After your 24-hour free trial, you can purchase an Extended Trial ($19.99 for 14 days) to keep testing, or subscribe to a monthly plan to become a Founder.',
    },
    {
      question: 'What is the Extended Trial?',
      answer: 'The Extended Trial gives you 14 more days to test SignGuy AI for just $19.99. If you then subscribe to a monthly plan, your $19.99 is credited toward your first month!',
    },
    {
      question: 'How do I become a Founder?',
      answer: 'Subscribe to any monthly plan (Starter, Growth, or Pro). The first 100 paying subscribers become Founders with locked-in pricing forever. Extended Trial purchases do not count toward Founder status.',
    },
    {
      question: 'What is "Founder" pricing?',
      answer: 'Founders get their subscription rate locked in forever - your monthly price never increases even when we raise prices. Plus no onboarding fees, early feature access, and direct developer contact.',
    },
    {
      question: 'Do you offer annual billing?',
      answer: 'Yes! Pay annually and get 1 month free (pay for 11 months, get 12). Annual billing also locks in Founder pricing.',
    },
    {
      question: 'Can I change plans later?',
      answer: 'Absolutely! You can upgrade or downgrade at any time. Changes take effect on your next billing cycle. Founder pricing applies to whatever tier you choose.',
    },
    {
      question: 'Do you offer refunds?',
      answer: 'Yes, we offer a 30-day money-back guarantee. If SignGuy AI isn\'t right for your shop, we\'ll refund your payment.',
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards (Visa, MasterCard, American Express) through our secure Stripe payment processor.',
    },
  ];

  const founderBenefits = [
    { icon: Gift, title: 'Lifetime Pricing', desc: 'Your rate never increases, even when we raise prices.' },
    { icon: Shield, title: 'No Onboarding Fees', desc: 'Save up to $599 that future customers will pay.' },
    { icon: Zap, title: 'Early Feature Access', desc: 'Be first to try new features before public release.' },
    { icon: Users, title: 'Direct Developer Access', desc: 'Questions? Suggestions? Talk directly with me.' },
    { icon: Star, title: 'Shape the Product', desc: 'Your feedback directly influences what we build.' },
    { icon: Crown, title: 'Founding Member Badge', desc: 'Show off your early supporter status.' },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-400 border-yellow-500/30 px-4 py-2">
            <Star className="w-4 h-4 mr-2" />
            Founder Pricing — Only 100 of 100 spots left!
            <Star className="w-4 h-4 ml-2" />
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4">
            Lock In
          </h1>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#2F8BFB] to-green-400 mb-6">
            Founder Pricing Forever
          </h2>
          <p className="text-lg text-gray-400 max-w-3xl mx-auto mb-8">
            Join the first 100 shops and keep these special rates for life — as long as your subscription stays active.
          </p>

          {/* Free Trial Button */}
          <div className="flex justify-center mb-12">
            <Link to="/register">
              <Button className="bg-[#2F8BFB]/10 hover:bg-[#2F8BFB]/20 border border-[#2F8BFB]/30 text-[#2F8BFB] px-6 py-3 rounded-full">
                <Clock className="w-4 h-4 mr-2" />
                <span>Start with a <span className="text-white">24-hour free trial</span></span>
              </Button>
            </Link>
          </div>
          <p className="text-sm text-gray-500 -mt-8 mb-8">Full access, no credit card required</p>

          {/* Billing Cycle Toggle */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <span className={`text-sm ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`}>Monthly</span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                billingCycle === 'annual' ? 'bg-[#2F8BFB]' : 'bg-gray-600'
              }`}
            >
              <span
                className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${
                  billingCycle === 'annual' ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm ${billingCycle === 'annual' ? 'text-white' : 'text-gray-500'}`}>
              Annual
              <Badge className="ml-2 bg-green-500/20 text-green-400 border-green-500/30 text-xs">
                1 Month Free
              </Badge>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="px-4 pb-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6 items-start">
            {tiers.map((tier) => {
              const Icon = tier.icon;
              const displayPrice = billingCycle === 'annual' 
                ? Math.round(tier.annualPrice / 12) 
                : tier.founderPrice;
              const totalAnnual = tier.annualPrice;
              
              return (
                <Card
                  key={tier.name}
                  className={`bg-[#111826] border-white/10 relative overflow-hidden ${
                    tier.popular ? 'border-[#2F8BFB] md:scale-105 z-10' : ''
                  }`}
                >
                  {tier.popular && (
                    <div className="absolute -top-0 left-1/2 -translate-x-1/2">
                      <Badge className="bg-[#2F8BFB] text-black border-0 px-4 py-1 font-semibold rounded-b-lg rounded-t-none">
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  <CardContent className="p-6 pt-8">
                    {/* Tier Header */}
                    <div className="flex items-center gap-3 mb-2">
                      <div className={`w-10 h-10 rounded-lg ${tier.bgColor} flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${tier.iconColor}`} />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white">{tier.name}</h3>
                        <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-500/30">
                          FOUNDER
                        </Badge>
                      </div>
                    </div>
                    
                    <p className="text-gray-400 text-sm mb-4">{tier.description}</p>
                    
                    {/* Pricing */}
                    <div className="mb-1">
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-[#2F8BFB]">${displayPrice}</span>
                        <span className="text-gray-500">/month</span>
                      </div>
                      <div className="text-sm text-gray-500 line-through">
                        ${tier.regularPrice}/mo after founder-phase
                      </div>
                      {billingCycle === 'annual' && (
                        <div className="text-xs text-[#2F8BFB] mt-1">
                          ${totalAnnual}/year (1 month free!)
                        </div>
                      )}
                    </div>

                    <div className="text-sm text-green-400 mb-1">
                      Save ${tier.savings}/month forever
                    </div>
                    <div className="text-xs text-gray-500 mb-4 flex items-center gap-1">
                      <Gift className="w-3 h-3" />
                      No onboarding fee (saves up to $599)
                    </div>

                    <Link to="/login">
                      <Button
                        className={`w-full mb-4 ${
                          tier.popular
                            ? 'bg-[#2F8BFB] hover:bg-[#1E7AF0] text-black font-semibold'
                            : 'bg-white/5 hover:bg-white/10 border border-white/10'
                        }`}
                      >
                        Get Started <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </Link>

                    {/* Features */}
                    {tier.inheritText && (
                      <p className="text-sm text-[#2F8BFB] mb-2">{tier.inheritText}</p>
                    )}
                    <ul className="space-y-2">
                      {tier.features.map((feature, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm">
                          <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
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

      {/* Extended Trial */}
      <section className="px-4 pb-12">
        <div className="max-w-3xl mx-auto">
          <Card className="bg-[#111826] border-green-500/30">
            <CardContent className="p-6 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-1">Need More Time to Decide?</h3>
                  <p className="text-gray-400 text-sm">
                    Get a <span className="text-green-400 font-medium">14-day extended trial</span> for just $19.99. Full platform access with all features unlocked.
                  </p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <Badge className="text-xs bg-green-500/10 text-green-400 border-green-500/30">Full platform access</Badge>
                    <Badge className="text-xs bg-green-500/10 text-green-400 border-green-500/30">All features unlocked</Badge>
                    <Badge className="text-xs bg-green-500/10 text-green-400 border-green-500/30">Live support access</Badge>
                  </div>
                </div>
              </div>
              <div className="text-center flex-shrink-0">
                <div className="text-3xl font-bold text-white">$19.99</div>
                <Link to="/register">
                  <Button className="mt-2 bg-green-500 hover:bg-green-600 text-white">
                    Start Extended Trial
                  </Button>
                </Link>
                <p className="text-xs text-gray-500 mt-2">Credits toward Business subscription</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* AI Tools Add-On */}
      <section className="px-4 pb-12">
        <div className="max-w-3xl mx-auto">
          <Card className="bg-gradient-to-r from-purple-500/5 to-pink-500/5 border-purple-500/30">
            <CardContent className="p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">AI Tools Pack</h3>
                  <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-500/30">
                    FOUNDER PRICING
                  </Badge>
                </div>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Already using another management system? Get access to all our AI tools as a standalone subscription.
              </p>
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-300 mb-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Design Tools
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Copywriter
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Social Media Content
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Branding Tools
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Business Document Generator
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  Image Analysis
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  AI Price Suggestions
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-purple-400" />
                  Works standalone or with any plan
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-3xl font-bold text-purple-400">$49</span>
                  <span className="text-gray-500">/month</span>
                  <div className="text-sm text-gray-500 line-through">$89/mo later</div>
                </div>
                <Link to="/register">
                  <Button className="bg-purple-500 hover:bg-purple-600">
                    Get AI Tools
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Why Become a Founder */}
      <section className="px-4 py-16 bg-[#0B0F14]">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">Why Become a Founder?</h2>
          <p className="text-gray-400 text-center mb-12">
            The first 100 shops get exclusive benefits that will never be offered again.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {founderBenefits.map((benefit, i) => {
              const Icon = benefit.icon;
              return (
                <Card key={i} className="bg-[#111826] border-white/10">
                  <CardContent className="p-6">
                    <div className="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center mb-3">
                      <Icon className="w-5 h-5 text-yellow-400" />
                    </div>
                    <h3 className="font-bold text-white mb-1">{benefit.title}</h3>
                    <p className="text-gray-400 text-sm">{benefit.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-4 py-16">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <Card key={index} className="bg-[#111826] border-white/10">
                <CardContent className="p-6">
                  <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-[#2F8BFB]" />
                    {faq.question}
                  </h3>
                  <p className="text-gray-400 ml-7">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Banner */}
      <section className="px-4 pb-16">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-3 px-6 py-3 rounded-full border border-white/10 bg-[#111826]">
            <div className="w-3 h-3 rounded-full bg-green-400"></div>
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
