import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Crown, Check, Sparkles, Shield, Coins,
  Package, Users, Zap, ArrowRight, Loader2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const FEATURES = [
  'Full Shop Management (CRM, Orders, Job Tickets, Invoices)',
  'Employee Payroll & Time Tracking',
  'Customer & Employee Portals',
  '28+ AI Tools (Design, Business, Marketing)',
  'AI Business Assistant with Voice',
  'Unlimited Webstores (B2B, Fundraiser, Creator)',
  'Unified Productivity (Dashboard, Calendar, Kanban, Task List)',
  'Customer Signatures + Drawings + Image Markup',
  'Production Workflow & Timeline',
  'Document Library & Questionnaires',
  'Artwork Proofs & Approvals',
  'Pricing Calculator (8 Categories)',
  '150 AI Credits per Month',
  'Priority Support',
  'Lifetime Pricing Lock',
  'All Future Features Included',
];

export default function PricingPlansV2() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const [spots, setSpots] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(null);

  const fetchSpots = useCallback(async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/founders/spots`);
      setSpots(response.data);
    } catch (error) {
      console.error('Failed to fetch founder spots:', error);
    }
  }, []);

  useEffect(() => {
    fetchSpots();
  }, [fetchSpots]);

  const handleCheckout = async (interval) => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/pricing-plans' } });
      return;
    }
    setCheckoutLoading(interval);
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/founders/checkout`,
        { billing_interval: interval, origin_url: window.location.origin },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Checkout failed');
    } finally {
      setCheckoutLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30 mb-4 px-3 py-1">
            <Crown className="w-3 h-3 mr-1" /> Limited to {spots?.total_spots || 100} Founding Members
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">
            Founders Edition
          </h1>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Get everything SignGuy AI has to offer at a locked-in rate. 
            Be one of the first {spots?.total_spots || 100} and keep this price forever.
          </p>
          {spots && (
            <div className="mt-4 inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20 rounded-full px-4 py-2">
              <Users className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-violet-300">
                <strong>{spots.spots_remaining}</strong> of {spots.total_spots} spots remaining
              </span>
            </div>
          )}
        </div>

        {/* Pricing Card */}
        <Card className="bg-[#111826] border-violet-500/30 overflow-hidden mb-12" data-testid="founders-pricing-card">
          <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500"></div>
          <CardContent className="p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left - Pricing */}
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-3 rounded-xl bg-violet-500/10">
                    <Crown className="w-8 h-8 text-violet-400" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">Founders Edition</h2>
                    <p className="text-gray-400">Everything. Forever price.</p>
                  </div>
                </div>

                {/* Monthly */}
                <div className="bg-[#0B0F17] rounded-xl p-5 mb-3 border border-[#1E293B]">
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      <p className="text-sm text-gray-400">Monthly</p>
                      <p className="text-3xl font-bold">$99<span className="text-base font-normal text-gray-400">/mo</span></p>
                    </div>
                    <Badge className="bg-violet-500/20 text-violet-400 text-xs">FOUNDERS price</Badge>
                  </div>
                  <Button
                    onClick={() => handleCheckout('monthly')}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-violet-500 hover:bg-violet-600 text-white font-semibold"
                    data-testid="checkout-monthly-btn"
                  >
                    {checkoutLoading === 'monthly' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ArrowRight className="h-4 w-4 mr-2" />}
                    Subscribe Monthly
                  </Button>
                </div>

                {/* Annual */}
                <div className="bg-[#0B0F17] rounded-xl p-5 border border-violet-500/20">
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      <p className="text-sm text-gray-400">Annual</p>
                      <p className="text-3xl font-bold">$594<span className="text-base font-normal text-gray-400">/yr</span></p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400 text-xs">Save $594/yr</Badge>
                  </div>
                  <Button
                    onClick={() => handleCheckout('annual')}
                    disabled={checkoutLoading !== null}
                    variant="outline"
                    className="w-full border-violet-500/50 text-violet-400 hover:bg-violet-500/10"
                    data-testid="checkout-annual-btn"
                  >
                    {checkoutLoading === 'annual' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
                    Subscribe Annual
                  </Button>
                </div>

                {/* Promo */}
                <div className="mt-4 bg-violet-500/5 border border-violet-500/20 rounded-lg p-3 text-center">
                  <p className="text-sm text-violet-300">
                    Use promo code <strong className="text-violet-400">FOUNDERS</strong> at checkout for 50% off
                  </p>
                </div>
              </div>

              {/* Right - Features */}
              <div>
                <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-violet-400" />
                  Everything Included
                </h3>
                <div className="space-y-2.5">
                  {FEATURES.map((feature) => (
                    <div key={feature} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-300">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Credit Packs */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-center mb-2">AI Credit Packs</h2>
          <p className="text-center text-gray-400 mb-6">
            Need more AI power? Purchased credits never expire while active.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { id: 'pack_small', credits: 100, price: 10, label: '100 Credits' },
              { id: 'pack_medium', credits: 300, price: 25, label: '300 Credits', popular: true },
              { id: 'pack_large', credits: 1000, price: 60, label: '1000 Credits', best: true },
            ].map((pack) => (
              <Card
                key={pack.id}
                className={`bg-[#111826] border-[#1E293B] ${pack.popular ? 'border-[#2F8BFB]/50' : ''} ${pack.best ? 'border-violet-500/50' : ''}`}
              >
                <CardContent className="p-6 text-center">
                  <Package className="w-8 h-8 text-violet-400 mx-auto mb-3" />
                  <h3 className="font-bold text-lg text-white mb-1">{pack.label}</h3>
                  <p className="text-3xl font-bold text-white mb-1">${pack.price}</p>
                  <p className="text-xs text-gray-400 mb-4">
                    ${(pack.price / pack.credits * 100).toFixed(0)}c per credit
                    {pack.best && ' - 40% savings'}
                    {pack.popular && ' - 17% savings'}
                  </p>
                  <Button
                    onClick={() => {
                      if (!isAuthenticated) {
                        navigate('/login');
                        return;
                      }
                      // Navigate to billing to purchase
                      navigate('/billing');
                    }}
                    variant="outline"
                    className="w-full border-[#2F8BFB]/50 text-[#2F8BFB] hover:bg-[#2F8BFB]/10"
                    size="sm"
                  >
                    <Coins className="w-4 h-4 mr-2" />
                    Buy Credits
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Fees & Info */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <Card className="bg-[#111826] border-[#1E293B]">
            <CardContent className="p-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#2F8BFB]" />
                Processing Fees
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Platform Processing</span>
                  <span className="text-white">2.2% + $0.20</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Webstore Additional</span>
                  <span className="text-white">2.0%</span>
                </div>
                <p className="text-xs text-gray-500 pt-2 border-t border-[#1E293B]">
                  Stripe's standard fees (2.9% + $0.30) apply in addition.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111826] border-[#1E293B]">
            <CardContent className="p-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-violet-400" />
                How AI Credits Work
              </h3>
              <div className="space-y-2 text-sm text-gray-300">
                <p>150 credits included monthly with your plan.</p>
                <p>Monthly credits reset each billing cycle (no rollover).</p>
                <p>Purchased credits never expire while your account is active.</p>
                <p>Monthly credits are used first, then purchased.</p>
                <p>Each AI action costs 1-3 credits depending on complexity.</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* FAQ */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-center mb-6">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {[
              { q: 'What does "lifetime pricing lock" mean?', a: 'Your $99/mo rate (or $594/yr) will never increase. Even when we add new features or raise prices for new customers, your Founders rate stays the same.' },
              { q: 'What happens when all 100 Founder spots are taken?', a: 'The Founders Edition will close permanently. New customers will need to wait for our regular tier pricing to launch at higher rates.' },
              { q: 'Do monthly credits roll over?', a: 'No. Your 150 monthly credits reset each billing cycle. However, credits you purchase separately never expire as long as your account is active.' },
              { q: 'What is the FOUNDERS promo code?', a: 'Enter FOUNDERS at checkout to get 50% off your subscription. This works on both monthly and annual plans.' },
              { q: 'Can I cancel anytime?', a: 'Yes. Cancel through Stripe anytime. Your access continues through the current billing period. If you rejoin later, Founder pricing is preserved if spots are still available.' },
            ].map((faq) => (
              <Card key={faq.q} className="bg-[#111826] border-[#1E293B]">
                <CardContent className="p-5">
                  <h3 className="font-medium text-white mb-2">{faq.q}</h3>
                  <p className="text-sm text-gray-400">{faq.a}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
