import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Users, FileText, Receipt, Clock, DollarSign, Sparkles,
  BarChart3, Store, CheckCircle2, ArrowRight, Building2, Cpu,
  Briefcase, Calendar, ChevronDown, Crown, Coins, CreditCard,
  Zap, Shield, AlertCircle, Info
} from 'lucide-react';

export default function LandingPage() {
  const [activeFaq, setActiveFaq] = useState(null);

  const featureHighlights = [
    { icon: Users, title: 'Customer Management', desc: 'Full CRM built for sign shops' },
    { icon: Briefcase, title: 'Jobs & Quotes', desc: 'Track every project to completion' },
    { icon: Receipt, title: 'Invoicing', desc: 'Get paid faster with online payments' },
    { icon: Clock, title: 'Time & Payroll', desc: 'Track time and pay your team' },
    { icon: Sparkles, title: 'AI Tools', desc: '15+ tools for text, images, and analysis' },
    { icon: Store, title: 'Webstores', desc: 'Sell online with custom stores' },
  ];

  // Updated FAQs with all required transparency info
  const faqs = [
    {
      q: 'What is SignGuy AI?',
      a: 'SignGuy AI is a complete operating system for sign shops. It includes shop management, e-commerce webstores, and AI tools - all built specifically for the sign industry.'
    },
    {
      q: 'How does the 48-hour free trial work?',
      a: 'Start exploring instantly with no credit card required. You get access to all features plus 50 AI credits. We include sample customers, jobs, and a webstore so you can see exactly how everything works. After 48 hours, subscribe to Founders Edition to continue.'
    },
    {
      q: 'What is Founders Edition?',
      a: 'Founders Edition is our exclusive early adopter plan limited to just 100 shops. You get lifetime locked pricing at $99/month with all features included and 150 AI credits per month.'
    },
    {
      q: 'Do unused monthly credits roll over?',
      a: 'No. Monthly credits expire on your billing date. Purchased credits remain valid while your subscription is active.'
    },
    {
      q: 'When are my credits added?',
      a: 'Monthly credits are added after your subscription payment is successfully processed.'
    },
    {
      q: 'Do purchased credits expire?',
      a: 'Purchased credits remain available as long as your subscription stays active.'
    },
    {
      q: 'Why do some AI tools cost more credits?',
      a: 'More advanced AI tools require more computing resources, so some actions may cost more than basic AI features. Most actions cost 1-3 credits, though some advanced tools may require more.'
    },
    {
      q: 'What are the fees and what do they cover?',
      a: 'Platform Processing Fee (2.2% + $0.20): Covers secure payment processing via Stripe, fraud protection, encrypted data storage, platform infrastructure, and continuous feature updates. Additional Webstore Fee (2.0%): Only charged when you make sales through your webstores. Covers hosted storefront infrastructure, CDN delivery, order management, and secure checkout.'
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Section 1: Hero - Founders Edition Focused */}
      <section className="pt-20 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          {/* 48-Hour Free Trial Badge */}
          <Badge className="mb-3 bg-green-500/20 text-green-400 border border-green-500/30 px-4 py-1.5">
            <Clock className="w-4 h-4 mr-2" />
            48-Hour Free Trial - No Credit Card Required
          </Badge>
          
          <Badge className="mb-6 bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30 px-4 py-1.5 ml-2">
            <Crown className="w-4 h-4 mr-2" />
            Founders Edition - Only 100 Spots
          </Badge>
          
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            The AI-Powered Operating System<br />
            <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">for Sign Shops</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Manage customers, jobs, invoices, employees, webstores, and AI tools — 
            everything your sign shop needs in one platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold px-8 py-6 text-lg h-auto">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/features">
              <Button size="lg" variant="outline" className="border-white/20 !text-white hover:bg-white/10 hover:!text-white px-8 py-6 text-lg h-auto bg-transparent">
                Explore Features
              </Button>
            </Link>
          </div>

          {/* Quick Stats */}
          <div className="mt-12 flex flex-wrap justify-center gap-8">
            <div className="text-center">
              <p className="text-3xl font-bold text-white">$99</p>
              <p className="text-sm text-gray-500">per month</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">150</p>
              <p className="text-sm text-gray-500">AI credits/month</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-white">100%</p>
              <p className="text-sm text-gray-500">features included</p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Founder Promotion Banner */}
      <section className="py-6 px-4 bg-gradient-to-r from-amber-600/20 via-orange-600/20 to-amber-600/20 border-y border-amber-500/30">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Crown className="w-6 h-6 text-amber-400" />
            <h3 className="text-xl font-bold text-amber-400">Founder Launch Offer</h3>
          </div>
          <p className="text-white mb-2">
            Promo code <span className="font-mono bg-amber-500/30 px-2 py-0.5 rounded text-amber-300">FOUNDERS</span> gives <span className="font-bold">50% off the annual plan</span>
          </p>
          <p className="text-amber-200/80">Available for the first 100 customers only</p>
          <p className="text-sm text-gray-400 mt-3">
            Founder customers retain $99/month pricing after the first year as long as their subscription remains active. Future customers may pay higher prices.
          </p>
        </div>
      </section>

      {/* Section 3: Main Pricing Card */}
      <section className="py-20 px-4 bg-white/5">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">Simple, Transparent Pricing</h2>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            One plan, all features, no surprises.
          </p>

          {/* Founder Plan Pricing Card */}
          <Card className="bg-[#111826] text-white border-2 border-amber-500/50 max-w-xl mx-auto overflow-hidden">
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-3 text-center">
              <span className="text-black font-bold uppercase tracking-wide">Founder Plan</span>
            </div>
            <CardContent className="p-8">
              {/* Price */}
              <div className="text-center mb-6">
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-5xl font-bold text-white">$99</span>
                  <span className="text-xl text-gray-400">/ month</span>
                </div>
                <p className="text-sm text-amber-400 mt-2">or $1,188/year ($594 with FOUNDERS code)</p>
              </div>

              {/* Feature Summary */}
              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-gray-300">All features unlocked</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-gray-300">150 AI credits included each month</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-gray-300">Purchase additional credits anytime</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-gray-300">No feature tiers</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <span className="text-gray-300">Stripe required for payment processing features</span>
                </div>
              </div>

              {/* AI Credit Summary */}
              <div className="bg-white/5 rounded-lg p-4 mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span className="font-semibold text-white">AI Credit Summary</span>
                </div>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• AI tools typically cost 1–3 credits</li>
                  <li>• Some advanced tools may require higher credit amounts</li>
                </ul>
              </div>

              {/* Credit Packs */}
              <div className="border-t border-white/10 pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <Coins className="w-4 h-4 text-amber-400" />
                  <span className="font-semibold text-white">Credit Packs</span>
                </div>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-white">100</p>
                    <p className="text-xs text-gray-400">credits</p>
                    <p className="text-amber-400 font-semibold">$10</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-white">300</p>
                    <p className="text-xs text-gray-400">credits</p>
                    <p className="text-amber-400 font-semibold">$25</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-3 text-center">
                    <p className="text-lg font-bold text-white">1000</p>
                    <p className="text-xs text-gray-400">credits</p>
                    <p className="text-amber-400 font-semibold">$60</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Purchased credits never expire while subscription remains active.
                </p>
              </div>

              {/* CTA */}
              <div className="mt-8">
                <Link to="/register">
                  <Button className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold py-6 text-lg h-auto">
                    Start Free Trial
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Section 4: How AI Credits Work */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Zap className="w-8 h-8 text-amber-400" />
            <h2 className="text-2xl md:text-3xl font-bold text-center">How AI Credits Work</h2>
          </div>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Simple and transparent credit system for all AI features.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Monthly Credits */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-semibold">Monthly Credits</h3>
                </div>
                <p className="text-gray-400 mb-4">
                  Every account receives <span className="text-white font-semibold">150 AI credits each month</span>.
                </p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-400">Monthly credits expire on the billing date</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-400">Monthly credits are used before purchased credits</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Purchased Credits */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <Coins className="w-5 h-5 text-green-400" />
                  </div>
                  <h3 className="text-lg font-semibold">Purchased Credits</h3>
                </div>
                <p className="text-gray-400 mb-4">
                  Buy additional credits anytime. <span className="text-white font-semibold">They never expire</span> during your subscription.
                </p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-400">Purchased credits remain valid while subscription is active</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-400">Used only after monthly credits are depleted</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Credit Cost Note */}
          <div className="mt-8 bg-white/5 border border-white/10 rounded-xl p-6 text-center">
            <Info className="w-6 h-6 text-amber-400 mx-auto mb-3" />
            <p className="text-gray-300">
              Credit costs depend on compute intensity. Most AI actions cost between <span className="text-white font-semibold">1–3 credits</span>, though some advanced tools may require more.
            </p>
          </div>
        </div>
      </section>

      {/* Section 5: Billing & Payments */}
      <section className="py-20 px-4 bg-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-4">
            <CreditCard className="w-8 h-8 text-amber-400" />
            <h2 className="text-2xl md:text-3xl font-bold text-center">Billing & Payments</h2>
          </div>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Secure, transparent billing powered by Stripe.
          </p>

          <div className="space-y-4 max-w-2xl mx-auto">
            <div className="bg-[#111826] border border-white/10 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <CreditCard className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-2">Stripe Integration Required</h4>
                  <p className="text-gray-400 text-sm">
                    Subscription billing is processed through Stripe. Stripe must be connected before accepting payments through webstores or invoices.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-[#111826] border border-white/10 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-5 h-5 text-green-400" />
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-2">Credit Refill Timing</h4>
                  <p className="text-gray-400 text-sm">
                    Monthly AI credits are added only after a successful payment confirmation.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-[#111826] border border-amber-500/30 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-2">Failed Payment Policy</h4>
                  <p className="text-gray-400 text-sm">
                    If payment fails, new monthly credits will not be issued until payment is resolved.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 6: AI Usage Transparency */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-amber-400" />
            <h2 className="text-2xl md:text-3xl font-bold text-center">AI Usage Transparency</h2>
          </div>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Always know what you're spending before you spend it.
          </p>

          {/* Example UI */}
          <div className="max-w-md mx-auto">
            <div className="bg-[#111826] border border-white/20 rounded-xl overflow-hidden shadow-2xl">
              <div className="bg-white/5 px-4 py-3 border-b border-white/10">
                <p className="text-sm text-gray-400">Before running an AI action:</p>
              </div>
              <div className="p-6">
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-4">
                  <p className="text-amber-400 font-medium mb-2">This action will cost 2 credits.</p>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Remaining credits:</span>
                    <span className="text-white font-semibold">118</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <input type="checkbox" className="rounded border-gray-600" />
                  <span>Do not show this message again</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 7: What's Included */}
      <section className="py-20 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">Everything You Need, One Price</h2>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Founders Edition includes all features with no restrictions. No upsells, no tiers.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Shop Management */}
            <Card className="bg-[#111826] text-white border-amber-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-amber-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Building2 className="w-7 h-7 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Shop Management</h3>
                <p className="text-gray-400 mb-4">
                  Customers, jobs, quotes, invoices, payroll, time tracking, tasks, and reporting.
                </p>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Unlimited customers & jobs
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Online invoice payments
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Employee time clock
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Webstores */}
            <Card className="bg-[#111826] text-white border-amber-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-amber-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Store className="w-7 h-7 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Webstores</h3>
                <p className="text-gray-400 mb-4">
                  Sell online with B2B stores, fundraisers, and creator shops. Stripe Connect included.
                </p>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Unlimited stores
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Custom branding
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Automatic payouts
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* AI Tools */}
            <Card className="bg-[#111826] text-white border-amber-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-amber-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Sparkles className="w-7 h-7 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">AI Tools</h3>
                <p className="text-gray-400 mb-4">
                  15+ AI tools for text, images, mockups, and business intelligence.
                </p>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    150 credits/month
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Image generation
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    AI business assistant
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Section 8: Feature Highlights */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">Everything Your Shop Needs</h2>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            All the tools to run your sign shop efficiently, powered by AI.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {featureHighlights.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="p-6 bg-white/5 border border-white/10 rounded-xl">
                  <div className="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-amber-400" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-400">{feature.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-12">
            <Link to="/features">
              <Button variant="outline" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 bg-transparent">
                See All Features
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Section 9: CTA - Founders Edition */}
      <section className="py-20 px-4 bg-gradient-to-b from-amber-900/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <Crown className="w-12 h-12 mx-auto mb-4 text-amber-400" />
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Join the Founding 100
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Lock in $99/month forever. All features included. Limited spots available.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold px-8 py-6 text-lg h-auto">
                Get Founders Edition
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 px-8 py-6 text-lg h-auto bg-transparent">
                View Full Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Section 10: Fair Usage Notice */}
      <section className="py-8 px-4 bg-white/5 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 text-gray-500 text-sm">
            <Shield className="w-4 h-4" />
            <span>Excessive automated usage may be rate-limited to maintain platform performance and reliability.</span>
          </div>
        </div>
      </section>

      {/* Section 11: FAQ Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div 
                key={idx} 
                className="bg-white/5 border border-white/10 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setActiveFaq(activeFaq === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <span className="font-medium">{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${activeFaq === idx ? 'rotate-180' : ''}`} />
                </button>
                {activeFaq === idx && (
                  <div className="px-6 pb-6 text-gray-400">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
