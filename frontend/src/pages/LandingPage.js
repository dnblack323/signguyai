import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Users, FileText, Receipt, Clock, DollarSign, Sparkles,
  BarChart3, Store, CheckCircle2, ArrowRight, Building2, Cpu,
  Briefcase, Calendar, ChevronDown
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

  const faqs = [
    {
      q: 'What is SignGuy AI?',
      a: 'SignGuy AI is a complete operating system for sign shops. It includes shop management (OS), e-commerce (Webstores), and AI tools (AI Studio) - all built specifically for the sign industry.'
    },
    {
      q: 'How is it different from other sign shop software?',
      a: 'Built by a sign shop owner who understands the industry. Modern interface, AI-powered features, and includes everything from CRM to webstores in one platform.'
    },
    {
      q: 'Is there a free trial?',
      a: 'Yes! Start with a 24-hour free trial, no credit card required. You can extend your trial for $19.99 which credits toward your first subscription.'
    },
    {
      q: 'Can I use just the webstore or just AI tools?',
      a: 'Absolutely. We offer three products: OS (full shop management), Webstores (e-commerce only), and AI Studio (AI tools only). Choose what fits your needs.'
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Section 1: Hero - OS Focused */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full mb-6">
            <Building2 className="w-4 h-4 text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Built by a Sign Shop, For Sign Shops</span>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            The AI-Powered Operating System<br />
            <span className="text-blue-400">for Sign Shops</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Manage customers, jobs, invoices, employees, webstores, and AI tools — 
            everything your sign shop needs in one platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg h-auto">
                Start with OS
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/webstores">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8 py-6 text-lg h-auto">
                Explore Webstores
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Section 2: Three Product Blocks */}
      <section className="py-20 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4">Three Products, One Ecosystem</h2>
          <p className="text-gray-400 text-center mb-12 max-w-2xl mx-auto">
            Choose the product that fits your needs, or combine them for the complete experience.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* OS Block */}
            <Card className="bg-[#111826] border-blue-500/30 hover:border-blue-500/50 transition-colors">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-blue-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Building2 className="w-7 h-7 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">SignGuy AI OS</h3>
                <p className="text-gray-400 mb-6">
                  Complete shop management platform. Customers, jobs, invoices, payroll, webstores, and AI tools included.
                </p>
                <Link to="/platform">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">
                    Explore Platform
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Webstores Block */}
            <Card className="bg-[#111826] border-emerald-500/30 hover:border-emerald-500/50 transition-colors">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-emerald-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Store className="w-7 h-7 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">SignGuy Webstores</h3>
                <p className="text-gray-400 mb-6">
                  Sell online with B2B stores, fundraisers, and creator shops. Perfect if you use other management software.
                </p>
                <Link to="/webstores">
                  <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
                    Explore Webstores
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* AI Studio Block */}
            <Card className="bg-[#111826] border-purple-500/30 hover:border-purple-500/50 transition-colors">
              <CardContent className="p-8">
                <div className="w-14 h-14 bg-purple-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Cpu className="w-7 h-7 text-purple-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">SignGuy AI Studio</h3>
                <p className="text-gray-400 mb-6">
                  Access our full AI toolkit standalone. Text generation, image creation, and business assistant.
                </p>
                <Link to="/ai-studio">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">
                    Explore AI Studio
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
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
                  <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-blue-400" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-400">{feature.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="text-center mt-12">
            <Link to="/platform">
              <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
                See All Features
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Section 4: CTA - OS Primary */}
      <section className="py-20 px-4 bg-gradient-to-b from-blue-900/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Transform Your Sign Shop?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join hundreds of sign shops running on SignGuy AI. Start your free trial today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg h-auto">
                Start Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8 py-6 text-lg h-auto">
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
