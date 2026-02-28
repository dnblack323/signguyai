import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Store, Package, ShoppingCart, CreditCard, Share2, 
  BarChart3, CheckCircle2, ArrowRight, Users, Ticket
} from 'lucide-react';

export default function WebstoresPage() {
  const features = [
    { icon: Package, name: 'Product Management', desc: 'Manage your catalog' },
    { icon: ShoppingCart, name: 'Order Processing', desc: 'Track every order' },
    { icon: CreditCard, name: 'Stripe Connect', desc: 'Get paid directly' },
    { icon: Share2, name: 'Store Sharing', desc: 'Custom links & branding' },
    { icon: Ticket, name: 'Promo Codes', desc: 'Drive sales' },
    { icon: BarChart3, name: 'Analytics', desc: 'Track performance' },
  ];

  const plans = [
    {
      name: 'Launch',
      price: 39,
      path: '/webstore-launch',
      features: [
        '1 Webstore',
        'B2B & Fundraiser Stores',
        'Stripe Connect',
        'Order Management',
        'Basic Analytics',
        '3% Processing Fee',
      ],
    },
    {
      name: 'Growth',
      price: 59,
      path: '/webstore-growth',
      popular: true,
      features: [
        'Up to 5 Webstores',
        'All Store Types',
        'Advanced Branding',
        'Price Overrides',
        'Commission Tracking',
        '2.5% Processing Fee',
      ],
    },
    {
      name: 'Scale',
      price: 99,
      path: '/webstore-scale',
      features: [
        'Unlimited Webstores',
        'Advanced Analytics',
        'Bulk Order Tools',
        'Payout Tracking',
        'All Features',
        '2% Processing Fee',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full mb-6">
            <Store className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 text-sm font-medium">E-Commerce for Sign Shops</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            SignGuy Webstores
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Launch B2B stores, fundraisers, or creator shops. Perfect for sign shops 
            that want to sell online without the full platform.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-white px-8">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 px-8">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Who It's For */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">Who It's For</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-white/5 border border-white/10 rounded-xl text-center">
              <Users className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">B2B Shops</h3>
              <p className="text-sm text-gray-400">Corporate clients with recurring orders</p>
            </div>
            <div className="p-6 bg-white/5 border border-white/10 rounded-xl text-center">
              <Share2 className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Fundraisers</h3>
              <p className="text-sm text-gray-400">Schools, teams, and organizations</p>
            </div>
            <div className="p-6 bg-white/5 border border-white/10 rounded-xl text-center">
              <Package className="w-8 h-8 text-emerald-400 mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Creators</h3>
              <p className="text-sm text-gray-400">Artists and designers selling merch</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">Features</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.name} className="p-6 bg-[#111826] border border-white/10 rounded-xl text-center">
                  <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-6 h-6 text-emerald-400" />
                  </div>
                  <h3 className="font-semibold mb-1">{feature.name}</h3>
                  <p className="text-sm text-gray-400">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Plan Comparison */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-4">Choose Your Plan</h2>
          <p className="text-gray-400 text-center mb-12">Monthly billing only</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card key={plan.name} className={`bg-[#111826] border-2 ${plan.popular ? 'border-emerald-500' : 'border-white/10'}`}>
                {plan.popular && (
                  <div className="bg-emerald-500 text-white text-xs font-bold text-center py-1">
                    MOST POPULAR
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-3xl font-bold">${plan.price}</span>
                    <span className="text-gray-400">/mo</span>
                  </div>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Link to={plan.path}>
                    <Button className={`w-full ${plan.popular ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-white/10 hover:bg-white/20'}`}>
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
