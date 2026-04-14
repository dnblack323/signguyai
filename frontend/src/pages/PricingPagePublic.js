import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  CheckCircle2, Star, ArrowRight, Building2, Store, Cpu, Crown
} from 'lucide-react';

export default function PricingPagePublic() {
  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-12 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <Badge className="mb-4 bg-amber-500/20 text-amber-400 border-amber-500/30">
            <Star className="w-3 h-3 mr-1" />
            Founder Pricing Available
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Choose the product that fits your needs. Start with a free trial.
          </p>
        </div>
      </section>

      {/* Section 1: Shop Management Plans (OS) */}
      <section className="py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Shop Management</h2>
              <p className="text-gray-400">SignGuy AI OS</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Starter */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Starter</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$29</span>
                  <span className="text-gray-400">/mo</span>
                  <p className="text-sm text-amber-400 mt-1">Founder (reg. $39/mo)</p>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    Customer Management
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    Orders & Order Items
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    2 Team Members
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    25 AI Generations/mo
                  </li>
                </ul>
                <Link to="/starter">
                  <Button className="w-full bg-white/10 hover:bg-white/20 text-white">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Pro */}
            <Card className="bg-[#111826] text-white border-2 border-blue-500">
              <div className="bg-blue-500 text-white text-xs font-bold text-center py-1">
                MOST POPULAR
              </div>
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Pro</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$59</span>
                  <span className="text-gray-400">/mo</span>
                  <p className="text-sm text-amber-400 mt-1">Founder (reg. $79/mo)</p>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    Everything in Starter
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    Up to 3 Webstores
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    10 Team Members
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    100 AI Generations/mo
                  </li>
                </ul>
                <Link to="/pro">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Business */}
            <Card className="bg-[#111826] text-white border-amber-500/30">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-xl font-bold text-white">Business</h3>
                  <Crown className="w-4 h-4 text-amber-400" />
                </div>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$99</span>
                  <span className="text-gray-400">/mo</span>
                  <p className="text-sm text-amber-400 mt-1">Founder (reg. $149/mo)</p>
                  <p className="text-xs text-gray-500 mt-1">or $990/year (Founder) | $1490/year</p>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-400" />
                    Everything in Pro
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-400" />
                    Unlimited Webstores
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-400" />
                    Unlimited Team
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-amber-400" />
                    Unlimited AI
                  </li>
                </ul>
                <Link to="/business">
                  <Button className="w-full bg-amber-600 hover:bg-amber-700">Learn More</Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          <p className="text-center text-gray-500 text-sm mt-4">
            Annual billing only available for Business plan
          </p>
        </div>
      </section>

      {/* Section 2: Webstore Plans */}
      <section className="py-12 px-4 bg-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <Store className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">Webstore Plans</h2>
              <p className="text-gray-400">SignGuy Webstores • Monthly billing only</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Launch */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Launch</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$39</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    1 Webstore
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Stripe Connect
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    3% Processing Fee
                  </li>
                </ul>
                <Link to="/webstore-launch">
                  <Button className="w-full bg-white/10 hover:bg-white/20 text-white">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Growth */}
            <Card className="bg-[#111826] text-white border-2 border-emerald-500">
              <div className="bg-emerald-500 text-white text-xs font-bold text-center py-1">
                MOST POPULAR
              </div>
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Growth</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$59</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Up to 5 Webstores
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Advanced Branding
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    2.5% Processing Fee
                  </li>
                </ul>
                <Link to="/webstore-growth">
                  <Button className="w-full bg-emerald-600 hover:bg-emerald-700">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Scale */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Scale</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$99</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Unlimited Webstores
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Advanced Analytics
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    2% Processing Fee
                  </li>
                </ul>
                <Link to="/webstore-scale">
                  <Button className="w-full bg-white/10 hover:bg-white/20 text-white">Learn More</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Section 3: AI Studio Plans */}
      <section className="py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <Cpu className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">AI Studio Plans</h2>
              <p className="text-gray-400">SignGuy AI Studio • Monthly billing only</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Basic */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Basic</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$29</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    AI Text Generation
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    25 Generations/mo
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    10 Assistant Queries
                  </li>
                </ul>
                <Link to="/ai-basic">
                  <Button className="w-full bg-white/10 hover:bg-white/20 text-white">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Pro */}
            <Card className="bg-[#111826] text-white border-2 border-purple-500">
              <div className="bg-purple-500 text-white text-xs font-bold text-center py-1">
                MOST POPULAR
              </div>
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Pro</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$59</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    Text + Image Gen
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    100 Generations/mo
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    50 Assistant Queries
                  </li>
                </ul>
                <Link to="/ai-pro">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700">Learn More</Button>
                </Link>
              </CardContent>
            </Card>

            {/* Max */}
            <Card className="bg-[#111826] text-white border-white/10">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold mb-2 text-white">Max</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-white">$99</span>
                  <span className="text-gray-400">/mo</span>
                </div>
                <ul className="space-y-2 mb-6 text-sm text-gray-300">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    Unlimited Generations
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    Unlimited Queries
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                    Branding Kit Gen
                  </li>
                </ul>
                <Link to="/ai-max">
                  <Button className="w-full bg-white/10 hover:bg-white/20 text-white">Learn More</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-gray-400 mb-6">Start your free trial today. No credit card required.</p>
          <Link to="/login">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8">
              Start Free Trial
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
