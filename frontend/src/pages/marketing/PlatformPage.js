import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { PublicNav, PublicFooter } from '../../components/PublicNav';
import {
  Building2, Store, Cpu, Users, FileText, Receipt, 
  Clock, BarChart3, Sparkles, CheckCircle2, ArrowRight,
  Briefcase, Calculator, Package, Palette
} from 'lucide-react';

export default function PlatformPage() {
  const modules = [
    { icon: Users, name: 'Customer Management', desc: 'CRM built for sign shops' },
    { icon: Briefcase, name: 'Jobs & Quotes', desc: 'Track every project' },
    { icon: Receipt, name: 'Invoicing', desc: 'Get paid faster' },
    { icon: Clock, name: 'Time & Payroll', desc: 'Manage your team' },
    { icon: Sparkles, name: 'AI Tools', desc: 'Work smarter' },
    { icon: Store, name: 'Webstores', desc: 'Sell online' },
  ];

  const plans = [
    {
      name: 'Starter',
      price: 39,
      founderPrice: 29,
      path: '/starter',
      features: [
        'Customer Management',
        'Orders Quotes & Jobs Job Tickets',
        'Basic Invoicing',
        'Basic Time Clock',
        '2 Team Members',
        '25 AI Generations/mo',
      ],
    },
    {
      name: 'Pro',
      price: 79,
      founderPrice: 59,
      path: '/pro',
      popular: true,
      features: [
        'Everything in Starter',
        'Online Invoice Payments',
        'Up to 3 Webstores',
        'Advanced Payroll',
        '10 Team Members',
        '100 AI Generations/mo',
      ],
    },
    {
      name: 'Business',
      price: 149,
      founderPrice: 99,
      annualPrice: 1490,
      founderAnnual: 990,
      path: '/business',
      features: [
        'Everything in Pro',
        'Unlimited Webstores',
        'Unlimited Team',
        'Unlimited AI',
        'Advanced Analytics',
        'Priority Support',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full mb-6">
            <Building2 className="w-4 h-4 text-blue-400" />
            <span className="text-blue-400 text-sm font-medium">Shop Management Platform</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            SignGuy AI OS
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            The complete operating system for sign shops. Manage customers, jobs, invoices, 
            employees, webstores, and AI tools — all in one platform.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-white/20 !text-white hover:bg-white/10 hover:!text-white px-8 bg-transparent">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Core Modules */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">Core Modules</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {modules.map((module) => {
              const Icon = module.icon;
              return (
                <div key={module.name} className="p-6 bg-white/5 border border-white/10 rounded-xl text-center">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-6 h-6 text-blue-400" />
                  </div>
                  <h3 className="font-semibold mb-1">{module.name}</h3>
                  <p className="text-sm text-gray-400">{module.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Plan Comparison */}
      <section className="py-16 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-4">Choose Your Plan</h2>
          <p className="text-gray-400 text-center mb-12">Founder pricing available for early adopters</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card key={plan.name} className={`bg-[#111826] text-white border-2 ${plan.popular ? 'border-blue-500' : 'border-white/10'}`}>
                {plan.popular && (
                  <div className="bg-blue-500 text-white text-xs font-bold text-center py-1">
                    MOST POPULAR
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-white">${plan.founderPrice}</span>
                    <span className="text-gray-400">/mo</span>
                    <p className="text-sm text-amber-400 mt-1">Founder pricing (reg. ${plan.price}/mo)</p>
                    {plan.annualPrice && (
                      <p className="text-xs text-gray-500 mt-1">or ${plan.founderAnnual}/year</p>
                    )}
                  </div>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                        <CheckCircle2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Link to={plan.path}>
                    <Button className={`w-full text-white ${plan.popular ? 'bg-blue-600 hover:bg-blue-700' : 'bg-white/10 hover:bg-white/20'}`}>
                      Learn More
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
