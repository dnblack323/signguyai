import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { PublicNav, PublicFooter } from '../../components/PublicNav';
import {
  Cpu, Sparkles, Wand2, Type, Image, MessageSquare,
  FileText, Palette, CheckCircle2, ArrowRight, Brain
} from 'lucide-react';

export default function AIStudioPage() {
  const tools = [
    { icon: Type, name: 'Text Generation', desc: 'Proposals, emails, social posts' },
    { icon: Image, name: 'Image Generation', desc: 'Mockups and designs' },
    { icon: MessageSquare, name: 'AI Assistant', desc: 'Business insights on demand' },
    { icon: FileText, name: 'Document AI', desc: 'Contracts and templates' },
    { icon: Palette, name: 'Branding Kits', desc: 'Consistent brand assets' },
    { icon: Brain, name: 'Industry AI', desc: 'Sign-specific knowledge' },
  ];

  const plans = [
    {
      name: 'Basic',
      price: 29,
      path: '/ai-basic',
      features: [
        'AI Text Generation',
        '25 Generations/month',
        'AI Business Assistant',
        '10 Assistant Queries/mo',
        'Sign Industry Templates',
      ],
    },
    {
      name: 'Pro',
      price: 59,
      path: '/ai-pro',
      popular: true,
      features: [
        'Everything in Basic',
        'AI Image Generation',
        '100 Generations/month',
        '50 Assistant Queries/mo',
        'Advanced Prompts',
      ],
    },
    {
      name: 'Max',
      price: 99,
      path: '/ai-max',
      features: [
        'Everything in Pro',
        'Unlimited Generations',
        'Unlimited Queries',
        'Branding Kit Generator',
        'Campaign Builder',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 border border-purple-500/30 rounded-full mb-6">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span className="text-purple-400 text-sm font-medium">AI Tools for Sign Shops</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            SignGuy AI Studio
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Access our full suite of AI tools standalone. Perfect for designers and shops 
            already using other management software.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/login">
              <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-white px-8">
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

      {/* AI Tools */}
      <section className="py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">AI Tools Included</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {tools.map((tool) => {
              const Icon = tool.icon;
              return (
                <div key={tool.name} className="p-6 bg-white/5 border border-white/10 rounded-xl text-center">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-6 h-6 text-purple-400" />
                  </div>
                  <h3 className="font-semibold mb-1">{tool.name}</h3>
                  <p className="text-sm text-gray-400">{tool.desc}</p>
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
          <p className="text-gray-400 text-center mb-12">Monthly billing only</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card key={plan.name} className={`bg-[#111826] text-white border-2 ${plan.popular ? 'border-purple-500' : 'border-white/10'}`}>
                {plan.popular && (
                  <div className="bg-purple-500 text-white text-xs font-bold text-center py-1">
                    MOST POPULAR
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-white">${plan.price}</span>
                    <span className="text-gray-400">/mo</span>
                  </div>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                        <CheckCircle2 className="w-4 h-4 text-purple-400 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Link to={plan.path}>
                    <Button className={`w-full text-white ${plan.popular ? 'bg-purple-600 hover:bg-purple-700' : 'bg-white/10 hover:bg-white/20'}`}>
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
