import { Link } from 'react-router-dom';
import { Button } from '../../../components/ui/button';
import { PublicNav, PublicFooter } from '../../../components/PublicNav';
import { CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';

export default function ProPlanPage() {
  const features = [
    'Everything in Starter',
    'Online Invoice Payments',
    'Up to 3 Webstores',
    'Advanced Time Clock & Payroll',
    '10 Team Members',
    '100 AI Generations/mo',
    '50 AI Assistant Queries/mo',
    'Customer Portal Access',
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full mb-6">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">OS Plan • Most Popular</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Pro</h1>
            <p className="text-xl text-gray-400 mb-6">For growing sign shops with a team</p>
            <div className="mb-8">
              <span className="text-5xl font-bold">$59</span>
              <span className="text-gray-400 text-xl">/mo</span>
              <p className="text-amber-400 mt-2">Founder pricing (reg. $79/mo)</p>
            </div>
            <Link to="/login">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8">
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
                  <CheckCircle2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
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
