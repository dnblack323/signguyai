import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import { CheckCircle2, ArrowRight, Crown } from 'lucide-react';

export default function BusinessPlanPage() {
  const features = [
    'Everything in Pro',
    'Unlimited Webstores',
    'Unlimited Team Members',
    'Unlimited AI Generations',
    'Full Business Data AI',
    'Advanced Analytics',
    'Priority Support',
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/30 rounded-full mb-6">
              <Crown className="w-4 h-4 text-amber-400" />
              <span className="text-amber-400 text-sm font-medium">OS Plan • Enterprise</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Business</h1>
            <p className="text-xl text-gray-400 mb-6">For established sign shops needing everything</p>
            
            {/* Pricing Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-xl mx-auto mb-8">
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <p className="text-sm text-gray-400 mb-2">Monthly</p>
                <span className="text-4xl font-bold">$99</span>
                <span className="text-gray-400">/mo</span>
                <p className="text-amber-400 text-sm mt-2">Founder pricing (reg. $149/mo)</p>
              </div>
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-6">
                <p className="text-sm text-amber-400 mb-2">Annual</p>
                <span className="text-4xl font-bold">$990</span>
                <span className="text-gray-400">/year</span>
                <p className="text-amber-400 text-sm mt-2">Founder pricing (reg. $1490/yr)</p>
              </div>
            </div>
            
            <Link to="/login">
              <Button size="lg" className="bg-amber-600 hover:bg-amber-700 text-white px-8">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-8">
            <h2 className="text-xl font-bold mb-6">What's Included</h2>
            <ul className="space-y-4">
              {features.map((feature, idx) => (
                <li key={idx} className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-amber-400 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-8 text-center">
            <Link to="/platform" className="text-blue-400 hover:text-blue-300">
              ← Back to Platform Overview
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
