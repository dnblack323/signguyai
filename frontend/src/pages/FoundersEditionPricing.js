import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  CheckCircle2, Star, ArrowRight, Sparkles, Crown, 
  Zap, Users, Store, Shield, Cpu, Clock, CreditCard,
  Coins, Percent, AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function FoundersEditionPricing() {
  const navigate = useNavigate();
  const [founders, setFounders] = useState({ spots_remaining: 100, spots_claimed: 0 });
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [promoCode, setPromoCode] = useState('');
  const [promoApplied, setPromoApplied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFoundersAvailability();
  }, []);

  const fetchFoundersAvailability = async () => {
    try {
      const response = await fetch(`${API_URL}/api/plans/founders-edition`);
      if (response.ok) {
        const data = await response.json();
        setFounders(data.availability);
      }
    } catch (error) {
      console.error('Failed to fetch founders availability:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPromo = () => {
    if (promoCode.toUpperCase() === 'FOUNDERS') {
      setPromoApplied(true);
      setBillingCycle('annual');
    }
  };

  const features = [
    { icon: Users, title: 'Unlimited Team Members', desc: 'Add your whole crew' },
    { icon: Store, title: 'Unlimited Webstores', desc: 'B2B, Fundraiser, Creator stores' },
    { icon: Sparkles, title: '150 AI Credits/Month', desc: 'Generate content, images, more' },
    { icon: Shield, title: 'All Features Unlocked', desc: 'No restrictions, ever' },
    { icon: Cpu, title: 'AI Business Assistant', desc: 'Data-aware queries' },
    { icon: Clock, title: 'Time Clock & Payroll', desc: 'Full workforce management' },
  ];

  const includedFeatures = [
    'Customer Management',
    'Quotes & Jobs',
    'Invoicing with Online Payments',
    'Customer Portal',
    'Artwork Approvals',
    'Time Clock & Payroll',
    'Task Management',
    'AI Image Generation',
    'AI Text Generation',
    'AI Business Assistant',
    'Branding Kit Generator',
    'Campaign Builder',
    'Pricing Intelligence',
    'Webstore Management',
    'Stripe Connect Integration',
    'Advanced Analytics',
    'Email Templates',
    'Document Storage',
  ];

  const spotsPercentage = Math.round((founders.spots_claimed / 100) * 100);

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-4 bg-gradient-to-r from-amber-500/30 to-orange-500/30 text-amber-300 border-amber-500/50 px-4 py-1.5">
            <Crown className="w-4 h-4 mr-2" />
            Limited to 100 Founding Shops
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-white via-amber-100 to-amber-300 bg-clip-text text-transparent">
            Founders Edition
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
            Lock in lifetime pricing. Get everything. No limits.
          </p>
          
          {/* Spots Remaining Counter */}
          <div className="inline-flex items-center gap-3 bg-[#111826] border border-amber-500/30 rounded-full px-6 py-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-amber-300 font-semibold">
                {founders.spots_remaining} spots remaining
              </span>
            </div>
            <div className="w-px h-6 bg-gray-700" />
            <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-500"
                style={{ width: `${spotsPercentage}%` }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Main Pricing Card */}
      <section className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-b from-[#111826] to-[#0d1420] border-2 border-amber-500/50 overflow-hidden">
            {/* Header Banner */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-black text-center py-2 font-bold">
              <Crown className="inline w-4 h-4 mr-2" />
              FOUNDERS EDITION - LIFETIME LOCKED PRICING
            </div>
            
            <CardContent className="p-8">
              <div className="grid md:grid-cols-2 gap-8">
                {/* Left: Pricing */}
                <div>
                  {/* Billing Toggle */}
                  <div className="flex items-center gap-2 mb-6 bg-[#0B0F17] rounded-lg p-1">
                    <button
                      onClick={() => setBillingCycle('monthly')}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        billingCycle === 'monthly' 
                          ? 'bg-amber-500 text-black' 
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Monthly
                    </button>
                    <button
                      onClick={() => setBillingCycle('annual')}
                      className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                        billingCycle === 'annual' 
                          ? 'bg-amber-500 text-black' 
                          : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Annual
                      <Badge className="ml-2 bg-green-500/20 text-green-400 text-[10px]">
                        6 Months FREE
                      </Badge>
                    </button>
                  </div>

                  {/* Price Display */}
                  <div className="mb-6">
                    {billingCycle === 'monthly' ? (
                      <div>
                        <span className="text-5xl font-bold text-white">$99</span>
                        <span className="text-xl text-gray-400">/month</span>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-5xl font-bold text-white">$594</span>
                          <span className="text-xl text-gray-400">/year</span>
                        </div>
                        <p className="text-green-400 mt-1 flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" />
                          Pay for 6 months, get 12 months
                        </p>
                        {promoApplied && (
                          <Badge className="mt-2 bg-green-500/20 text-green-400">
                            FOUNDERS code applied!
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Promo Code */}
                  {billingCycle === 'monthly' && (
                    <div className="mb-6 p-4 bg-[#0B0F17] rounded-lg border border-dashed border-amber-500/30">
                      <p className="text-sm text-amber-300 mb-2">Have a promo code?</p>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Enter code"
                          value={promoCode}
                          onChange={(e) => setPromoCode(e.target.value)}
                          className="bg-[#111826] border-gray-700 text-white"
                        />
                        <Button 
                          onClick={handleApplyPromo}
                          variant="outline" 
                          className="border-amber-500 text-amber-400 hover:bg-amber-500/20"
                        >
                          Apply
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        Use code FOUNDERS for annual discount
                      </p>
                    </div>
                  )}

                  {/* Fees Breakdown */}
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 flex items-center gap-2">
                        <Percent className="w-4 h-4" />
                        Platform Processing Fee
                      </span>
                      <span className="text-white">2.2% + $0.20</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400 flex items-center gap-2">
                        <Store className="w-4 h-4" />
                        Webstore Sales Fee
                      </span>
                      <span className="text-white">2.0%</span>
                    </div>
                  </div>

                  {/* CTA Button */}
                  <Button 
                    onClick={() => navigate('/register')}
                    className="w-full py-6 text-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-bold"
                    data-testid="get-founders-btn"
                  >
                    Get Founders Edition
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                  
                  <p className="text-center text-xs text-gray-500 mt-3">
                    No credit card required to start
                  </p>
                </div>

                {/* Right: Features */}
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-400" />
                    Everything Included
                  </h3>
                  
                  {/* Highlight Features */}
                  <div className="grid grid-cols-2 gap-3 mb-6">
                    {features.map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-2 p-3 bg-[#0B0F17] rounded-lg">
                        <feature.icon className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-white">{feature.title}</p>
                          <p className="text-xs text-gray-500">{feature.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* AI Credits Info */}
                  <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Coins className="w-5 h-5 text-blue-400" />
                      <span className="font-semibold text-white">AI Credits System</span>
                    </div>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• 150 credits included monthly</li>
                      <li>• 1-3 credits per AI action</li>
                      <li>• Buy more anytime (never expire)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* All Features List */}
      <section className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">
            Full Feature List
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {includedFeatures.map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2 text-gray-300">
                <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Credit Packs Section */}
      <section className="py-12 px-4 bg-[#111826]/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Badge className="mb-4 bg-blue-500/20 text-blue-400">
              <Coins className="w-3 h-3 mr-1" />
              AI Credit Packs
            </Badge>
            <h2 className="text-2xl font-bold">Need More AI Power?</h2>
            <p className="text-gray-400">Buy credit packs anytime. They never expire.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 100 Credits */}
            <Card className="bg-[#0B0F17] border-gray-700">
              <CardContent className="p-6 text-center">
                <Coins className="w-8 h-8 mx-auto mb-3 text-gray-400" />
                <h3 className="text-lg font-bold text-white">100 Credits</h3>
                <p className="text-3xl font-bold text-white my-2">$10</p>
                <p className="text-sm text-gray-500">$0.10 per credit</p>
              </CardContent>
            </Card>

            {/* 300 Credits - Popular */}
            <Card className="bg-[#0B0F17] border-2 border-blue-500 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge className="bg-blue-500 text-white">POPULAR</Badge>
              </div>
              <CardContent className="p-6 text-center">
                <Coins className="w-8 h-8 mx-auto mb-3 text-blue-400" />
                <h3 className="text-lg font-bold text-white">300 Credits</h3>
                <p className="text-3xl font-bold text-white my-2">$25</p>
                <p className="text-sm text-green-400">17% savings</p>
              </CardContent>
            </Card>

            {/* 1000 Credits */}
            <Card className="bg-[#0B0F17] border-gray-700">
              <CardContent className="p-6 text-center">
                <Coins className="w-8 h-8 mx-auto mb-3 text-purple-400" />
                <h3 className="text-lg font-bold text-white">1000 Credits</h3>
                <p className="text-3xl font-bold text-white my-2">$60</p>
                <p className="text-sm text-green-400">40% savings</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-12 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <div className="p-4 bg-[#111826] rounded-lg">
              <h3 className="font-semibold text-white mb-2">What is Founders Edition?</h3>
              <p className="text-gray-400 text-sm">
                Founders Edition is our exclusive early adopter plan, limited to just 100 shops. You get lifetime locked pricing at $99/month with all features included and no restrictions.
              </p>
            </div>
            <div className="p-4 bg-[#111826] rounded-lg">
              <h3 className="font-semibold text-white mb-2">What happens to my pricing after the founder period?</h3>
              <p className="text-gray-400 text-sm">
                Your $99/month pricing is locked forever. When we release new pricing tiers, your rate stays the same. That's the founder guarantee.
              </p>
            </div>
            <div className="p-4 bg-[#111826] rounded-lg">
              <h3 className="font-semibold text-white mb-2">How do AI credits work?</h3>
              <p className="text-gray-400 text-sm">
                You get 150 AI credits each month. Different AI actions cost 1-3 credits. If you run low, you can buy credit packs that never expire. Monthly credits reset at the start of each billing period.
              </p>
            </div>
            <div className="p-4 bg-[#111826] rounded-lg">
              <h3 className="font-semibold text-white mb-2">What are the processing fees?</h3>
              <p className="text-gray-400 text-sm">
                We charge 2.2% + $0.20 on all payment transactions (invoices, payments). Webstore sales have an additional 2% fee. These fees cover payment processing and platform costs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <Crown className="w-12 h-12 mx-auto mb-4 text-amber-400" />
          <h2 className="text-3xl font-bold mb-4">Join the Founding 100</h2>
          <p className="text-gray-400 mb-8">
            Lock in lifetime pricing before spots run out.
          </p>
          <Button 
            onClick={() => navigate('/register')}
            size="lg"
            className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-bold px-8 py-6 text-lg"
          >
            Get Founders Edition Now
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
          <p className="text-sm text-gray-500 mt-4">
            {founders.spots_remaining} of 100 spots remaining
          </p>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
