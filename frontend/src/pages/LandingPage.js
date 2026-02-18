import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Users, FileText, Calculator, Receipt, Clock, DollarSign,
  Sparkles, BarChart3, Store, Shield, Zap, CheckCircle2,
  ChevronRight, Star, ArrowRight, Play, Menu, X,
  Briefcase, Calendar, MessageSquare, Palette, Image, Type,
  Target, TrendingUp, Award, Heart, Rocket, Building2
} from 'lucide-react';

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeFaq, setActiveFaq] = useState(null);
  const [activeScreenshot, setActiveScreenshot] = useState(0);

  const screenshots = [
    { name: 'Dashboard', description: 'Your command center', image: 'https://static.prod-images.emergentagent.com/jobs/9b7f34b8-177f-48ad-b4d8-74cf608027f1/images/c7c7e53bbdea412dae0b7c1f809015dd6ea9ace26dbdf12ab1299d6d28eba2a9.png' },
    { name: 'Jobs', description: 'Track every project', image: 'https://static.prod-images.emergentagent.com/jobs/9b7f34b8-177f-48ad-b4d8-74cf608027f1/images/fc831c9f1ca385f87d32514cb1d4f338ef4875c08e16ed7a1fede6b636e0f299.png' },
    { name: 'AI Tools', description: '24+ AI-powered tools', image: 'https://static.prod-images.emergentagent.com/jobs/9b7f34b8-177f-48ad-b4d8-74cf608027f1/images/d5a686159ed4e8884634e06a28b4c222375a998899ba1aabf6b0b8689ad7f957.png' },
    { name: 'Pricing Calculator', description: '8 specialized calculators', image: 'https://static.prod-images.emergentagent.com/jobs/9b7f34b8-177f-48ad-b4d8-74cf608027f1/images/c9f9486bf66063359dddc2676f85d066b1e0f262da3d4b1572a295560f7f04be.png' },
  ];

  const features = [
    { icon: Users, title: 'Customer Management', description: 'Full CRM with contact history, status tracking, and customer portal access' },
    { icon: Briefcase, title: 'Job Tracking', description: 'Visual timeline from quote to completion with status updates and time tracking' },
    { icon: Calculator, title: 'Smart Pricing', description: '8 specialized calculators for signs, wraps, banners, and more with AI suggestions' },
    { icon: Receipt, title: 'Invoicing', description: 'Professional invoices with payment tracking, reminders, and online payments' },
    { icon: Clock, title: 'Time Tracking', description: 'Track time per job, per employee with automatic labor cost calculations' },
    { icon: DollarSign, title: 'Payroll & Financials', description: 'Employee pay tracking, profit margins, and financial reporting' },
    { icon: Sparkles, title: '15+ AI Tools', description: 'Logo creator, sign designer, tagline generator, pricing advisor, and more' },
    { icon: Store, title: 'Webstores', description: 'Create fundraiser stores, B2B portals, and customer ordering pages' },
    { icon: Shield, title: 'Customer Portal', description: 'Let customers view orders, approve artwork, and make payments online' },
    { icon: Users, title: 'Employee Portal', description: 'Mobile-friendly time clock, task management, and pay stub access' },
    { icon: Calendar, title: 'Scheduling', description: 'Job scheduling with calendar views and deadline tracking' },
    { icon: MessageSquare, title: 'Messaging', description: 'Built-in communication with customers and team members' },
  ];

  const aiTools = [
    { icon: Image, name: 'Logo Creator', generates: 'images' },
    { icon: Palette, name: 'Sign Designer', generates: 'images' },
    { icon: Image, name: 'Banner Designer', generates: 'images' },
    { icon: Target, name: 'Mockup Creator', generates: 'images' },
    { icon: Type, name: 'Tagline Generator', generates: 'text' },
    { icon: Sparkles, name: 'Business Copywriter', generates: 'text' },
    { icon: Calculator, name: 'Pricing Advisor', generates: 'text' },
    { icon: Palette, name: 'Brand Color Advisor', generates: 'text' },
    { icon: Image, name: 'Photo Enhancer', generates: 'analysis' },
    { icon: Type, name: 'Font Identifier', generates: 'analysis' },
  ];

  const pricingTiers = [
    {
      name: 'Starter Shop',
      founding: 79,
      regular: 129,
      description: 'Perfect for small shops getting started',
      features: [
        'Customer Management',
        'Quotes & Jobs',
        'Basic Invoicing',
        '1 Webstore',
        '25 AI generations/month',
        '1 Team member',
        '100MB Storage',
        'Email Support',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Growth Shop',
      founding: 129,
      regular: 229,
      description: 'For growing shops that need more power',
      features: [
        'Everything in Starter, plus:',
        '5 Webstores',
        '100 AI generations/month',
        '5 Team members',
        '1GB Storage',
        'Time Clock & Payroll',
        'Advanced Analytics',
        'Priority Support',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Pro Shop',
      founding: 199,
      regular: 379,
      description: 'Full power for serious operations',
      features: [
        'Everything in Growth, plus:',
        'Unlimited Everything',
        'B2B Features',
        'BNPL Payments',
        'Custom Reports',
        'SMS Notifications',
        'API Access',
        'Dedicated Support',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
  ];

  const faqs = [
    {
      question: 'Is there a free trial?',
      answer: 'Yes! Every new account gets a 24-hour free trial with full access to all features. No credit card required to start.',
    },
    {
      question: 'Can I import my existing customer data?',
      answer: 'Absolutely. We support CSV imports for customers, and we can help you migrate from other sign shop software.',
    },
    {
      question: 'What makes SignGuy AI different from shopVOX or Cyrious?',
      answer: 'SignGuy AI was built by an actual sign shop owner who was frustrated with existing solutions. We include AI tools that no other sign shop software has, and we listen to our users. If you need a feature, just ask - we\'ll build it.',
    },
    {
      question: 'How does the AI tools work?',
      answer: 'Our AI tools use advanced language and image models to help you create logos, design signs, write copy, and get pricing suggestions. It\'s like having a design assistant and business consultant built right in.',
    },
    {
      question: 'Can my employees access the system?',
      answer: 'Yes! The Employee Portal gives your team a simple interface to clock in/out, view their tasks, check pay stubs, and more. You control what they can access.',
    },
    {
      question: 'What happens after the founding pricing period?',
      answer: 'Founders who sign up during launch keep their founding rate forever, as long as they maintain their subscription. We reward early believers.',
    },
    {
      question: 'I already have software I like. Can I just use the AI tools?',
      answer: 'Yes! We offer an AI Tools Add-On for $49/month (founder price) that gives you access to all 24+ AI tools without switching your main software.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="TheSignGuy AI" className="h-14 w-auto" />
            </div>
            
            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-300 hover:text-white transition">Features</a>
              <a href="#ai-tools" className="text-gray-300 hover:text-white transition">AI Tools</a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition">Pricing</a>
              <Link to="/docs" className="text-gray-300 hover:text-white transition">Docs</Link>
              <Link to="/login">
                <Button variant="ghost" className="text-gray-300 hover:text-white">Log In</Button>
              </Link>
              <Link to="/register">
                <Button className="bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold">
                  Start Free Trial
                </Button>
              </Link>
            </div>

            {/* Mobile menu button */}
            <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#111111] border-t border-white/10 p-4">
            <div className="flex flex-col gap-4">
              <a href="#features" className="text-gray-300 hover:text-white">Features</a>
              <a href="#ai-tools" className="text-gray-300 hover:text-white">AI Tools</a>
              <a href="#pricing" className="text-gray-300 hover:text-white">Pricing</a>
              <Link to="/docs" className="text-gray-300 hover:text-white">Docs</Link>
              <Link to="/login" className="text-gray-300 hover:text-white">Log In</Link>
              <Link to="/register">
                <Button className="w-full bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold">Start Free Trial</Button>
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#00D4FF]/10 via-transparent to-transparent" />
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-[#00D4FF]/15 rounded-full blur-3xl" />
        <div className="absolute top-40 right-1/4 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl" />
        
        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto">
            <Badge className="mb-6 bg-[#00D4FF]/20 text-[#00D4FF] border-[#00D4FF]/30 px-4 py-2">
              <Rocket className="w-4 h-4 mr-2" />
              Founding Member Pricing - Limited Time
            </Badge>
            
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight">
              The <span className="text-[#00D4FF]">AI-Powered</span> Operating System for{' '}
              <span className="text-white">Serious Sign Shops</span>
            </h1>
            
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Manage customers, jobs, quotes, invoices, employees, and more — with 15+ AI tools that no other sign shop software has. Built by a sign shop owner who knows exactly what you need.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link to="/register">
                <Button size="lg" className="bg-[#00D4FF] hover:bg-[#00B8E6] text-black font-semibold text-lg px-8 py-6 h-auto">
                  Start Your Free Trial
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <a href="#demo">
                <Button size="lg" variant="outline" className="border-[#00D4FF]/30 text-[#00D4FF] text-lg px-8 py-6 h-auto hover:bg-[#00D4FF]/10">
                  <Play className="w-5 h-5 mr-2" />
                  Watch Demo
                </Button>
              </a>
            </div>

            {/* Stats Bar */}
            <div className="flex flex-wrap justify-center gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-[#00D4FF]">15+</div>
                <div className="text-gray-500">AI Tools</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-[#00D4FF]">8</div>
                <div className="text-gray-500">Pricing Calculators</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-[#00D4FF]">∞</div>
                <div className="text-gray-500">Possibilities</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-[#00D4FF]">24hr</div>
                <div className="text-gray-500">Free Trial</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Built by a Sign Shop Owner Section */}
      <section className="py-20 px-4 bg-gradient-to-b from-[#111111] to-[#0a0a0a]">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
                <Heart className="w-4 h-4 mr-2" />
                Our Story
              </Badge>
              <h2 className="text-3xl sm:text-4xl font-bold mb-6">
                Built by a Sign Shop Owner,<br />
                <span className="text-[#00D4FF]">For Sign Shop Owners</span>
              </h2>
              <div className="space-y-4 text-gray-300">
                <p>
                  I built SignGuy AI for my own sign shop because I was tired of software made by people who've never stepped foot in a production facility. The existing options were either bloated, overpriced, or built by committees who didn't understand our industry.
                </p>
                <p>
                  When I realized how much it transformed my business, I knew I had to share it. This isn't backed by venture capitalists or built by a team that's never held a squeegee. It's built by someone who knows the difference between cast and calendered vinyl.
                </p>
                <p className="text-[#00D4FF] font-semibold">
                  As a founding member, you're not just a customer — you're a partner. Need a feature? Tell me. Don't like something? I'll fix it. This software grows with your input.
                </p>
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-[#00D4FF]/20 to-[#0066CC]/20 rounded-2xl p-8 border border-white/10">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#0a0a0a] rounded-xl p-4 text-center">
                    <Building2 className="w-8 h-8 text-[#00D4FF] mx-auto mb-2" />
                    <div className="text-sm text-gray-400">Built by</div>
                    <div className="font-semibold">Real Shop Owner</div>
                  </div>
                  <div className="bg-[#0a0a0a] rounded-xl p-4 text-center">
                    <Award className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                    <div className="text-sm text-gray-400">Not backed by</div>
                    <div className="font-semibold">VC or Investors</div>
                  </div>
                  <div className="bg-[#0a0a0a] rounded-xl p-4 text-center">
                    <MessageSquare className="w-8 h-8 text-green-400 mx-auto mb-2" />
                    <div className="text-sm text-gray-400">Features</div>
                    <div className="font-semibold">You Request</div>
                  </div>
                  <div className="bg-[#0a0a0a] rounded-xl p-4 text-center">
                    <TrendingUp className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                    <div className="text-sm text-gray-400">Constant</div>
                    <div className="font-semibold">Updates</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Screenshots Section */}
      <section id="demo" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">See It In Action</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              A modern, intuitive interface that your whole team will actually enjoy using
            </p>
          </div>

          <div className="bg-[#111111] rounded-2xl border border-white/10 overflow-hidden">
            {/* Screenshot tabs */}
            <div className="flex border-b border-white/10 overflow-x-auto">
              {screenshots.map((screen, index) => (
                <button
                  key={screen.name}
                  onClick={() => setActiveScreenshot(index)}
                  className={`px-6 py-4 font-medium whitespace-nowrap transition ${
                    activeScreenshot === index
                      ? 'bg-[#00D4FF]/20 text-[#00D4FF] border-b-2 border-[#00D4FF]'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {screen.name}
                </button>
              ))}
            </div>
            
            {/* Screenshot display */}
            <div className="p-4">
              <div className="bg-[#0a0a0a] rounded-lg overflow-hidden">
                <img
                  src={screenshots[activeScreenshot].image}
                  alt={screenshots[activeScreenshot].name}
                  className="w-full h-auto"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675"><rect fill="%230d1f35" width="1200" height="675"/><text fill="%23666" font-family="system-ui" font-size="24" x="50%" y="50%" text-anchor="middle">' + screenshots[activeScreenshot].name + ' Screenshot</text></svg>';
                  }}
                />
              </div>
              <p className="text-center text-gray-400 mt-4">{screenshots[activeScreenshot].description}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 px-4 bg-[#111111]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/20 text-blue-400 border-blue-500/30">
              Everything You Need
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              One Platform, Every Tool
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              From first quote to final payment, SignGuy AI handles your entire workflow
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="bg-white border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all group">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-600 transition">
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-gray-600 text-sm">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* AI Tools Section */}
      <section id="ai-tools" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/20 text-blue-400 border-blue-500/30">
              <Sparkles className="w-4 h-4 mr-2" />
              AI-Powered
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              15+ AI Tools No Other Software Has
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Generate logos, design signs, write copy, get pricing suggestions — all powered by cutting-edge AI
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {aiTools.map((tool, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-400 hover:shadow-md transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center group-hover:bg-blue-600 transition">
                    <tool.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 text-sm">{tool.name}</div>
                    <div className="text-xs text-gray-500">Generates {tool.generates}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-gray-400 mb-4">
              Already happy with your current software but want AI superpowers?
            </p>
            <Badge className="bg-blue-500 text-white border-blue-600 px-6 py-3 text-lg">
              AI Tools Add-On: Just $49/month (founder price)
            </Badge>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-12 px-4 bg-[#1a1a1a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <Badge className="mb-3 bg-blue-500/20 text-blue-400 border-blue-500/30">
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Compare
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold mb-2">
              See How We Stack Up
            </h2>
            <p className="text-gray-400 text-sm max-w-2xl mx-auto">
              We're not just another sign shop software. See the difference.
            </p>
          </div>

          <div className="overflow-x-auto bg-white rounded-xl shadow-lg">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 text-gray-700 font-semibold">Feature</th>
                  <th className="py-3 px-4">
                    <div className="text-blue-600 font-bold">SignGuy AI</div>
                    <div className="text-xs text-gray-500">That's us!</div>
                  </th>
                  <th className="py-3 px-4 text-gray-600">shopVOX</th>
                  <th className="py-3 px-4 text-gray-600">Cyrious</th>
                  <th className="py-3 px-4 text-gray-600">SignTracker</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { feature: 'AI-Powered Tools (24+ tools)', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'AI Email Drafting', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'AI Business Assistant', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'Built-in Pricing Calculators', signguy: '8 Types', shopvox: 'Basic', cyrious: 'Basic', signtracker: 'Limited' },
                  { feature: 'Customer Portal', signguy: true, shopvox: true, cyrious: false, signtracker: false },
                  { feature: 'Employee Portal', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'Time Tracking per Job', signguy: true, shopvox: 'Add-on', cyrious: true, signtracker: false },
                  { feature: 'Visual Job Timeline', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'Webstore Builder', signguy: true, shopvox: true, cyrious: false, signtracker: false },
                  { feature: 'Online Payments', signguy: true, shopvox: true, cyrious: false, signtracker: false },
                  { feature: 'Scheduling & Calendar', signguy: true, shopvox: 'Add-on', cyrious: true, signtracker: false },
                  { feature: 'Payroll & Time Clock', signguy: true, shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'Expense Tracking', signguy: true, shopvox: false, cyrious: 'Add-on', signtracker: false },
                  { feature: 'Logo/Design Generator', signguy: 'AI', shopvox: false, cyrious: false, signtracker: false },
                  { feature: 'Mobile-Friendly', signguy: true, shopvox: 'Partial', cyrious: false, signtracker: true },
                  { feature: 'Starting Price', signguy: '$79/mo', shopvox: '$99/mo', cyrious: '$150/mo', signtracker: '$79/mo' },
                  { feature: 'Founder Price', signguy: '$79/mo', shopvox: 'N/A', cyrious: 'N/A', signtracker: 'N/A' },
                ].map((row, index) => (
                  <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-800">{row.feature}</td>
                    <td className="py-3 px-4 text-center">
                      {typeof row.signguy === 'boolean' ? (
                        row.signguy ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="w-5 h-5 text-red-400 mx-auto" />
                        )
                      ) : (
                        <span className="text-blue-600 font-semibold">{row.signguy}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {typeof row.shopvox === 'boolean' ? (
                        row.shopvox ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="w-5 h-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-600">{row.shopvox}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {typeof row.cyrious === 'boolean' ? (
                        row.cyrious ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="w-5 h-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-600">{row.cyrious}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {typeof row.signtracker === 'boolean' ? (
                        row.signtracker ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="w-5 h-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-600">{row.signtracker}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/20 text-blue-400 border-blue-500/30">
              <Star className="w-4 h-4 mr-2" />
              Founding Member Pricing
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Lock In Your Rate Forever
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Founding members keep these prices for life. Regular pricing increases soon.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingTiers.map((tier, index) => (
              <Card
                key={index}
                className={`bg-white border-gray-200 relative shadow-lg ${
                  tier.popular ? 'border-blue-500 border-2 scale-105' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <Badge className="bg-blue-500 text-white border-0 px-4 py-1">
                      Most Popular
                    </Badge>
                  </div>
                )}
                <CardContent className="p-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                  <p className="text-gray-500 text-sm mb-6">{tier.description}</p>
                  
                  <div className="mb-6">
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-blue-600">${tier.founding}</span>
                      <span className="text-gray-500">/month</span>
                    </div>
                    <div className="text-sm text-gray-400 line-through">${tier.regular}/month regular</div>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {tier.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-gray-700">
                        <CheckCircle2 className="w-5 h-5 text-blue-500 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Link to="/register">
                    <Button
                      className={`w-full ${
                        tier.popular
                          ? 'bg-blue-500 hover:bg-blue-600 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                      }`}
                    >
                      {tier.cta}
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* AI Add-On */}
          <div className="mt-16 max-w-3xl mx-auto">
            <Card className="bg-white border-blue-200 shadow-lg">
              <CardContent className="p-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                  <div>
                    <Badge className="mb-2 bg-blue-500/20 text-blue-600 border-blue-500/30">
                      <Sparkles className="w-4 h-4 mr-2" />
                      For Existing Software Users
                    </Badge>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">AI Tools Add-On</h3>
                    <p className="text-gray-600">
                      Love your current software but want AI superpowers? Get access to all 24+ AI tools without switching.
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-blue-600">$49</div>
                    <div className="text-gray-600">/month founder</div>
                    <div className="text-sm text-gray-400 line-through">$89/mo later</div>
                    <Link to="/register">
                      <Button className="mt-4 bg-blue-500 hover:bg-blue-600 text-white">
                        Get AI Tools
                      </Button>
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-4 bg-[#1a1a1a]">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-gray-400">Got questions? We've got answers.</p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm"
              >
                <button
                  onClick={() => setActiveFaq(activeFaq === index ? null : index)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left"
                >
                  <span className="font-medium text-gray-900">{faq.question}</span>
                  <ChevronRight
                    className={`w-5 h-5 text-gray-500 transition-transform ${
                      activeFaq === index ? 'rotate-90' : ''
                    }`}
                  />
                </button>
                {activeFaq === index && (
                  <div className="px-6 pb-4 text-gray-600">{faq.answer}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Transform Your Sign Shop?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join the sign shop revolution. Start your free trial today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-[#00D4FF] to-[#0066CC] hover:from-[#00B8E6] hover:to-blue-700 text-lg px-8 py-6 h-auto">
                Start Your Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <a href="mailto:support@signguyai.com">
              <Button size="lg" variant="outline" className="border-white/20 text-lg px-8 py-6 h-auto hover:bg-white/10">
                Contact Us
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src="/logo.png" alt="TheSignGuy AI" className="h-12 w-auto" />
              </div>
              <p className="text-gray-400 text-sm">
                The AI-powered operating system for serious sign shops.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#ai-tools" className="hover:text-white transition">AI Tools</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#faq" className="hover:text-white transition">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved. Built with love for the sign industry.
          </div>
        </div>
      </footer>
    </div>
  );
}
