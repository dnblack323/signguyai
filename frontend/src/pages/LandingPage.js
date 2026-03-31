import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Users, FileText, Receipt, Clock, DollarSign, Sparkles,
  BarChart3, Store, CheckCircle2, ArrowRight, Building2, Cpu,
  Briefcase, Calendar, ChevronDown, Crown, Coins
} from 'lucide-react';

export default function LandingPage() {
  const [activeFaq, setActiveFaq] = useState(null);

  const featureHighlights = [
    { icon: Users, title: 'Customer Management', desc: 'Full CRM built for sign shops' },
    { icon: Briefcase, title: 'Orders & Job Tickets', desc: 'Track every project to completion' },
    { icon: Calendar, title: 'Unified Productivity', desc: 'Calendar, Kanban, Task List, Dashboard' },
    { icon: Receipt, title: 'Invoicing', desc: 'Get paid faster with online payments' },
    { icon: Clock, title: 'Time & Payroll', desc: 'Track time and pay your team' },
    { icon: Sparkles, title: 'AI Tools', desc: '15+ tools for text, images, and analysis' },
    { icon: Store, title: 'Webstores', desc: 'Sell online with custom stores' },
  ];

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
      a: 'Founders Edition is our exclusive early adopter plan limited to just 100 shops. You get lifetime locked pricing at $99/month with all features included and 150 AI credits per month. Founder customers retain this pricing as long as their subscription remains active.'
    },
    {
      q: 'How do AI credits work?',
      a: 'You get 150 AI credits each month. Different AI actions cost 1-3 credits. Monthly credits are used before purchased credits. If you need more, you can buy credit packs that never expire while your subscription is active.'
    },
    {
      q: 'Do unused monthly credits roll over?',
      a: 'No. Monthly credits expire on your billing date. Purchased credits remain valid while your subscription is active.'
    },
    {
      q: 'Do purchased credits expire?',
      a: 'Purchased credits remain available as long as your subscription stays active.'
    },
    {
      q: 'What are the fees and what do they cover?',
      a: 'Platform Processing Fee (2.2% + $0.20): Covers secure payment processing via Stripe, fraud protection, encrypted data storage, platform infrastructure, and continuous feature updates. Compare: Stripe alone charges 2.9% + $0.30. Additional Webstore Fee (2.0%): Only charged when you make sales through your webstores. Covers hosted storefront infrastructure, CDN delivery, order management, and secure checkout. No sales means no fee. Our fees are transparent and competitive — you\'re getting more value at a lower cost than payment processing alone.'
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
          
          <Badge className="mb-6 bg-gradient-to-r from-violet-500/20 to-purple-500/20 text-violet-400 border border-violet-500/30 px-4 py-1.5 ml-2">
            <Crown className="w-4 h-4 mr-2" />
            Founders Edition - Only 100 Spots
          </Badge>
          
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            The AI-Powered Operating System<br />
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">for Sign Shops</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Manage customers, jobs, invoices, employees, webstores, and AI tools — 
            everything your sign shop needs in one platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white font-semibold px-8 py-6 text-lg h-auto">
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

      {/* Section 2: What's Included */}
      <section className="py-20 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">Everything You Need, One Price</h2>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Founders Edition includes all features with no restrictions. No upsells, no tiers.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Shop Management */}
            <Card className="bg-[#111826] text-white border-violet-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-violet-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Building2 className="w-7 h-7 text-violet-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Shop Management</h3>
                <p className="text-gray-400 mb-4">
                  Customers, 4-layer order workflow, unified productivity, signatures, drawings, payroll, and reporting.
                </p>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Unified orders, job tickets, quotes, invoices, and production workflow
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Unified Productivity: Dashboard, Calendar, Kanban, Task List
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    Signatures, sketches, and markup tied to exact records
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Webstores */}
            <Card className="bg-[#111826] text-white border-violet-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-violet-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Store className="w-7 h-7 text-violet-400" />
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
            <Card className="bg-[#111826] text-white border-violet-500/30">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-violet-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Sparkles className="w-7 h-7 text-violet-400" />
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

      {/* Section 3: Feature Highlights */}
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
                  <div className="w-12 h-12 bg-violet-500/20 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-violet-400" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-400">{feature.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-12">
            <Link to="/features">
              <Button variant="outline" className="border-violet-500/30 text-violet-400 hover:bg-violet-500/10 bg-transparent">
                See All Features
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Section 4: CTA - Founders Edition */}
      <section className="py-20 px-4 bg-gradient-to-b from-violet-900/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <Crown className="w-12 h-12 mx-auto mb-4 text-violet-400" />
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Join the Founding 100
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Lock in $99/month forever. All features included. Limited spots available.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white font-semibold px-8 py-6 text-lg h-auto">
                Get Founders Edition
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing-plans">
              <Button size="lg" variant="outline" className="border-violet-500/30 text-violet-400 hover:bg-violet-500/10 px-8 py-6 text-lg h-auto bg-transparent">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
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
