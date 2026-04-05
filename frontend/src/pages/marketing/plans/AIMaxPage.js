import { Link } from 'react-router-dom';
import { Button } from '../../../components/ui/button';
import { PublicNav, PublicFooter } from '../../../components/PublicNav';
import { CheckCircle2, ArrowRight, Crown } from 'lucide-react';

export default function AIMaxPage() {
  const features = [
    'Everything in Pro',
    'Unlimited Generations',
    'Unlimited Queries',
    'Branding Kit Generator',
    'Campaign Builder',
    'Content Calendar',
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/30 rounded-full mb-6">
              <Crown className="w-4 h-4 text-purple-400" />
              <span className="text-purple-400 text-sm font-medium">AI Studio Plan</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Max</h1>
            <p className="text-xl text-gray-400 mb-6">Unlimited AI for power users</p>
            <div className="mb-8">
              <span className="text-5xl font-bold">$99</span>
              <span className="text-gray-400 text-xl">/mo</span>
            </div>
            <Link to="/login">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-white px-8">
                Start Free Trial
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-8">
            <h2 className="text-xl font-bold mb-6">What's Included</h2>
            <ul className="space-y-4">
              {features.map((feature) => (
                <li key={feature} className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5 text-purple-400 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-8 text-center">
            <Link to="/ai-studio" className="text-purple-400 hover:text-purple-300">
              ← Back to AI Studio Overview
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
