import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  CheckCircle2, X, Star, Sparkles, ArrowRight, Menu,
  Zap, Users, Calculator, Clock, Store, Shield, HelpCircle
} from 'lucide-react';

export default function PricingPagePublic() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [billingCycle, setBillingCycle] = useState('monthly');

  const tiers = [
    {
      name: 'Starter',
      description: 'Perfect for small shops just getting started',
      monthlyFounder: 29,
      monthlyRegular: 49,
      yearlyFounder: 290,
      yearlyRegular: 490,
      features: [
        { name: 'Up to 3 users', included: true },
        { name: 'Customer management', included: true },
        { name: 'Job tracking & quotes', included: true },
        { name: 'Basic invoicing', included: true },
        { name: '3 pricing calculators', included: true },
        { name: 'Customer portal', included: true },
        { name: 'Email support', included: true },
        { name: 'Employee portal', included: false },
        { name: 'Webstore builder', included: false },
        { name: 'Payroll management', included: false },
        { name: 'Financial reports', included: false },
        { name: 'API access', included: false },
      ],
      popular: false,
      cta: 'Start Free Trial',
    },
    {
      name: 'Pro',
      description: 'For growing shops that need more power',
      monthlyFounder: 59,
      monthlyRegular: 99,
      yearlyFounder: 590,
      yearlyRegular: 990,
      features: [
        { name: 'Up to 10 users', included: true },
        { name: 'Everything in Starter', included: true },
        { name: 'All 8 pricing calculators', included: true },
        { name: 'Employee portal & time clock', included: true },
        { name: 'Webstore builder', included: true },
        { name: 'Advanced reporting', included: true },
        { name: 'Priority support', included: true },
        { name: 'Job time tracking', included: true },
        { name: 'Payroll management', included: false },
        { name: 'Financial reports', included: false },
        { name: 'Multi-location', included: false },
        { name: 'API access', included: false },
      ],
      popular: true,
      cta: 'Start Free Trial',
    },
    {
      name: 'Business',
      description: 'Full power for serious operations',
      monthlyFounder: 99,
      monthlyRegular: 149,
      yearlyFounder: 990,
      yearlyRegular: 1490,
      features: [
        { name: 'Unlimited users', included: true },
        { name: 'Everything in Pro', included: true },
        { name: 'Payroll management', included: true },
        { name: 'Financial reports', included: true },
        { name: 'Multi-location support', included: true },
        { name: 'API access', included: true },
        { name: 'Dedicated support', included: true },
        { name: 'Custom integrations', included: true },
        { name: 'White-label options', included: true },
        { name: 'Advanced analytics', included: true },
        { name: 'Priority feature requests', included: true },
        { name: 'Onboarding assistance', included: true },
      ],
      popular: false,
      cta: 'Start Free Trial',
    },
  ];

  const faqs = [
    {
      question: 'What happens after my free trial?',
      answer: 'After your 24-hour free trial, you can choose a plan that fits your shop. Your data is saved, so you can pick up right where you left off.',
    },
    {
      question: 'Can I change plans later?',
      answer: 'Absolutely! You can upgrade or downgrade at any time. Changes take effect on your next billing cycle.',
    },
    {
      question: 'What is "Founding Member" pricing?',
      answer: 'Founding members who sign up during our launch period get locked into lower prices forever. These rates won\'t increase as long as you maintain your subscription.',
    },
    {
      question: 'Do you offer refunds?',
      answer: 'Yes, we offer a 30-day money-back guarantee. If SignGuy AI isn\'t right for your shop, we\'ll refund your payment.',
    },
    {
      question: 'Can I pay annually?',
      answer: 'Yes! Annual billing saves you 2 months compared to monthly billing. That\'s like getting 2 months free.',
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit cards (Visa, MasterCard, American Express) through our secure payment processor.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <Link to="/home" className="flex items-center gap-3">
              <img src="/logo.png" alt="TheSignGuy AI" className="h-14 w-auto" />
            </Link>
            
            <div className="hidden md:flex items-center gap-8">
              <Link to="/features" className="text-gray-300 hover:text-white transition">Features</Link>
              <Link to="/pricing" className="text-[#00D4FF] font-medium">Pricing</Link>
              <Link to="/about" className="text-gray-300 hover:text-white transition">About</Link>
              <Link to="/contact" className="text-gray-300 hover:text-white transition">Contact</Link>
              <Link to="/login">
                <Button variant="ghost" className="text-gray-300 hover:text-white">Log In</Button>
              </Link>
              <Link to="/register">
                <Button className="bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold">
                  Start Free Trial
                </Button>
              </Link>
            </div>

            <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden bg-[#111111] border-t border-white/10 p-4">
            <div className="flex flex-col gap-4">
              <Link to="/features" className="text-gray-300 hover:text-white">Features</Link>
              <Link to="/pricing" className="text-[#00D4FF]">Pricing</Link>
              <Link to="/about" className="text-gray-300 hover:text-white">About</Link>
              <Link to="/contact" className="text-gray-300 hover:text-white">Contact</Link>
              <Link to="/login" className="text-gray-300 hover:text-white">Log In</Link>
              <Link to="/register">
                <Button className="w-full bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold">Start Free Trial</Button>
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-yellow-500/20 text-yellow-400 border-yellow-500/30 px-4 py-2">
            <Star className="w-4 h-4 mr-2" />
            Founding Member Pricing - Lock In Your Rate Forever
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
            Simple, Transparent <span className="text-[#00D4FF]">Pricing</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            No hidden fees. No per-user surprises. Just straightforward pricing that makes sense for sign shops.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-4 mb-12">
            <span className={billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}>Monthly</span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
              className="relative w-14 h-7 bg-[#111111] rounded-full border border-white/20"
            >
              <div
                className={`absolute top-1 w-5 h-5 bg-[#00D4FF] rounded-full transition-all ${
                  billingCycle === 'yearly' ? 'left-8' : 'left-1'
                }`}
              />
            </button>
            <span className={billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}>
              Yearly <span className="text-green-400 text-sm">(Save 2 months)</span>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="px-4 pb-20">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8">
            {tiers.map((tier) => (
              <Card
                key={tier.name}
                className={`bg-[#111111] border-white/10 relative ${
                  tier.popular ? 'border-[#00D4FF] scale-105 z-10' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <Badge className="bg-[#00D4FF] text-black border-0 px-4 py-1 font-semibold">
                      Most Popular
                    </Badge>
                  </div>
                )}
                <CardContent className="p-8">
                  <h3 className="text-2xl font-bold text-white mb-2">{tier.name}</h3>
                  <p className="text-gray-400 text-sm mb-6">{tier.description}</p>
                  
                  <div className="mb-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-[#00D4FF]">
                        ${billingCycle === 'monthly' ? tier.monthlyFounder : tier.yearlyFounder}
                      </span>
                      <span className="text-gray-500">
                        /{billingCycle === 'monthly' ? 'month' : 'year'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 line-through">
                      ${billingCycle === 'monthly' ? tier.monthlyRegular : tier.yearlyRegular}/{billingCycle === 'monthly' ? 'month' : 'year'} regular
                    </div>
                  </div>

                  <div className="text-xs text-yellow-400 mb-6">
                    Founding member rate - locked forever
                  </div>

                  <Link to="/register">
                    <Button
                      className={`w-full mb-6 ${
                        tier.popular
                          ? 'bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold'
                          : 'bg-white/10 hover:bg-white/20'
                      }`}
                    >
                      {tier.cta}
                    </Button>
                  </Link>

                  <ul className="space-y-3">
                    {tier.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        {feature.included ? (
                          <CheckCircle2 className="w-5 h-5 text-[#00D4FF] flex-shrink-0" />
                        ) : (
                          <X className="w-5 h-5 text-gray-600 flex-shrink-0" />
                        )}
                        <span className={feature.included ? 'text-gray-300' : 'text-gray-600'}>
                          {feature.name}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* AI Add-On */}
      <section className="px-4 pb-20">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <Badge className="mb-4 bg-purple-500/20 text-purple-400 border-purple-500/30">
                    <Sparkles className="w-4 h-4 mr-2" />
                    For Existing Software Users
                  </Badge>
                  <h3 className="text-2xl font-bold text-white mb-2">AI Tools Add-On</h3>
                  <p className="text-gray-400">
                    Already happy with your current sign shop software? Get access to all 15+ AI tools 
                    without switching. Generate logos, design signs, write copy, and more.
                  </p>
                </div>
                <div className="text-center flex-shrink-0">
                  <div className="text-4xl font-bold text-purple-400">$19</div>
                  <div className="text-gray-500">/month</div>
                  <Link to="/register">
                    <Button className="mt-4 bg-purple-500 hover:bg-purple-600">
                      Get AI Tools
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="px-4 pb-20">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Compare Plans</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-4 px-4 text-gray-400 font-medium">Feature</th>
                  <th className="py-4 px-4 text-white">Starter</th>
                  <th className="py-4 px-4 text-[#00D4FF]">Pro</th>
                  <th className="py-4 px-4 text-white">Business</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Users</td>
                  <td className="py-4 px-4 text-center">3</td>
                  <td className="py-4 px-4 text-center">10</td>
                  <td className="py-4 px-4 text-center">Unlimited</td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Pricing Calculators</td>
                  <td className="py-4 px-4 text-center">3</td>
                  <td className="py-4 px-4 text-center">8</td>
                  <td className="py-4 px-4 text-center">8</td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Customer Portal</td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Employee Portal</td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Webstore Builder</td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Payroll & Financials</td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">API Access</td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><X className="w-5 h-5 text-gray-600 mx-auto" /></td>
                  <td className="py-4 px-4 text-center"><CheckCircle2 className="w-5 h-5 text-green-400 mx-auto" /></td>
                </tr>
                <tr className="border-b border-white/5">
                  <td className="py-4 px-4 text-gray-300">Support</td>
                  <td className="py-4 px-4 text-center">Email</td>
                  <td className="py-4 px-4 text-center">Priority</td>
                  <td className="py-4 px-4 text-center">Dedicated</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="px-4 pb-20">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Pricing FAQ</h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <Card key={index} className="bg-[#111111] border-white/10">
                <CardContent className="p-6">
                  <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-[#00D4FF]" />
                    {faq.question}
                  </h3>
                  <p className="text-gray-400 ml-7">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-[#111111]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Start Your Free Trial Today
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            No credit card required. See why sign shops are making the switch.
          </p>
          <Link to="/register">
            <Button size="lg" className="bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold text-lg px-8 py-6 h-auto">
              Start Your Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <img src="/logo.png" alt="TheSignGuy AI" className="h-12 w-auto mb-4" />
              <p className="text-gray-400 text-sm">
                The AI-powered operating system for serious sign shops.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link to="/features" className="hover:text-white transition">Features</Link></li>
                <li><Link to="/pricing" className="hover:text-white transition">Pricing</Link></li>
                <li><Link to="/home#faq" className="hover:text-white transition">FAQ</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link to="/about" className="hover:text-white transition">About</Link></li>
                <li><Link to="/contact" className="hover:text-white transition">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
