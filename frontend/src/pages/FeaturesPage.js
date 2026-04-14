import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Users, FileText, Calculator, Receipt, Clock, DollarSign,
  Sparkles, BarChart3, Store, Shield, Zap, CheckCircle2,
  ChevronRight, ArrowRight, Menu, X, Briefcase, Calendar,
  MessageSquare, Palette, Image, Type, Target, TrendingUp,
  ClipboardList, Truck, Settings, Bell, Search, Filter,
  PieChart, CreditCard, UserCheck, Building2, Layers
} from 'lucide-react';

// Feature screenshots mapping
const featureScreenshots = {
  'customers': '/screenshots/feature_customers.jpeg',
  'jobs': '/screenshots/feature_jobs.jpeg',
  'quotes': '/screenshots/feature_quotes.jpeg',
  'invoicing': '/screenshots/feature_invoices.jpeg',
  'webstores': '/screenshots/feature_webstores.jpeg',
  'ai': '/screenshots/feature_ai_tools.jpeg',
  'settings': '/screenshots/feature_settings.jpeg',
  'dashboard': '/screenshots/feature_dashboard.jpeg',
};

export default function FeaturesPage() {
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = [
    { id: 'all', name: 'All Features' },
    { id: 'core', name: 'Core Business' },
    { id: 'ai', name: 'AI Tools' },
    { id: 'portals', name: 'Portals' },
    { id: 'financial', name: 'Financial' },
  ];

  const features = [
    {
      id: 'customers',
      category: 'core',
      icon: Users,
      title: 'Customer Management',
      tagline: 'Your complete CRM built for sign shops',
      description: 'Keep track of every customer interaction, from first contact to repeat business. No more lost emails or forgotten follow-ups.',
      capabilities: [
        'Contact information with multiple addresses',
        'Customer status tracking (Lead, Active, VIP)',
        'Complete job history per customer',
        'Notes and communication log',
        'Quick actions for quotes and jobs',
        'Search and filter customers instantly',
        'Customer portal access management',
      ],
      color: 'from-blue-500 to-cyan-500',
    },
    {
      id: 'jobs',
      category: 'core',
      icon: Briefcase,
      title: 'Order & Production Tracking',
      tagline: 'From quote to completion, never lose track',
      description: 'Visual job management that shows you exactly where every project stands. Track status, time, materials, and profitability.',
      capabilities: [
        '4-layer workflow: Order → Order Item → Quote/Invoice → Production Tasks',
        'Line items with pricing calculator integration',
        'Item-level and order-level drawings, sketches, and markup',
        'Structured signature capture for orders, quotes, proofs, invoices, and more',
        'Order notes and activity log',
        'Due date scheduling',
        'Draft orders, work orders, and production shortcuts',
        'Unified Kanban + Calendar + Task List views',
      ],
      color: 'from-purple-500 to-pink-500',
    },
    {
      id: 'quotes',
      category: 'core',
      icon: Calculator,
      title: 'Smart Pricing & Quotes',
      tagline: '8 specialized calculators for accurate pricing',
      description: 'Stop guessing on prices. Our calculators factor in materials, labor, complexity, and setup fees to give you profitable quotes every time.',
      capabilities: [
        'Vinyl graphics calculator',
        'Vehicle wrap calculator',
        'Banner & large format calculator',
        'Channel letter calculator',
        'Monument sign calculator',
        'A-frame & yard sign calculator',
        'Window graphics calculator',
        'Custom product calculator',
        'Complexity multipliers',
        'Setup fee handling',
        'AI pricing suggestions',
      ],
      color: 'from-green-500 to-emerald-500',
    },
    {
      id: 'invoicing',
      category: 'financial',
      icon: Receipt,
      title: 'Professional Invoicing',
      tagline: 'Get paid faster with professional invoices',
      description: 'Create and send professional invoices in seconds. Track payments, send reminders, and accept online payments.',
      capabilities: [
        'One-click invoice from job',
        'Professional invoice templates',
        'Payment status tracking',
        'Partial payment support',
        'Payment reminders',
        'Online payment integration',
        'Invoice history and reporting',
        'PDF export and email',
      ],
      color: 'from-yellow-500 to-orange-500',
    },
    {
      id: 'time-tracking',
      category: 'core',
      icon: Clock,
      title: 'Time Tracking',
      tagline: 'Know exactly where your time goes',
      description: 'Track time per job, per employee, per task. See real labor costs and improve your estimates with actual data.',
      capabilities: [
        'Start/stop timer on any job',
        'Task type categorization',
        'Employee time logs',
        'Labor cost calculations',
        'Time summaries per job',
        'Billable vs non-billable tracking',
        'Export time reports',
        'Integration with payroll',
      ],
      color: 'from-cyan-500 to-blue-500',
    },
    {
      id: 'payroll',
      category: 'financial',
      icon: DollarSign,
      title: 'Payroll & Financials',
      tagline: 'Business tier power features',
      description: 'Manage employee pay, track profit margins, and get financial insights all in one place.',
      capabilities: [
        'Employee pay tracking',
        'Hourly rate management',
        'Pay period summaries',
        'Profit margin reports',
        'Revenue tracking',
        'Expense categorization',
        'Financial dashboard',
        'Export to accounting software',
      ],
      color: 'from-emerald-500 to-teal-500',
    },
    {
      id: 'ai-tools',
      category: 'ai',
      icon: Sparkles,
      title: 'AI Tools Suite',
      tagline: '15+ AI-powered tools no other software has',
      description: 'Generate logos, design signs, write copy, get pricing suggestions - all powered by cutting-edge AI built right into your workflow.',
      capabilities: [
        'Logo Creator - generate logo concepts',
        'Sign Designer - AI sign mockups',
        'Banner Designer - promotional banners',
        'Mockup Creator - realistic product mockups',
        'Tagline Generator - catchy business taglines',
        'Business Copywriter - marketing copy',
        'Pricing Advisor - AI pricing suggestions',
        'Brand Color Advisor - color palettes',
        'Photo Enhancer - image improvements',
        'Font Identifier - identify fonts from images',
        'And more tools added regularly',
      ],
      color: 'from-violet-500 to-purple-500',
    },
    {
      id: 'customer-portal',
      category: 'portals',
      icon: Shield,
      title: 'Customer Portal',
      tagline: 'Let customers help themselves',
      description: 'Give your customers 24/7 access to view orders, approve artwork, make payments, and communicate with your shop.',
      capabilities: [
        'Branded portal with your logo',
        'Order status visibility',
        'Artwork approval workflow',
        'Review-and-sign customer signature links',
        'Online payment processing',
        'Message your team directly',
        'Download invoices and receipts',
        'Request new quotes',
        'View job history',
      ],
      color: 'from-blue-500 to-indigo-500',
    },
    {
      id: 'employee-portal',
      category: 'portals',
      icon: UserCheck,
      title: 'Employee Portal',
      tagline: 'Mobile-friendly for your team',
      description: 'Your employees get their own simple interface to clock in/out, view tasks, check pay stubs, and stay productive.',
      capabilities: [
        'Simple clock in/out',
        'View assigned jobs and tasks',
        'Time clock history',
        'Pay stub access',
        'Profile management',
        'Mobile-optimized design',
        'Separate login system',
        'Role-based permissions',
      ],
      color: 'from-teal-500 to-cyan-500',
    },
    {
      id: 'webstores',
      category: 'portals',
      icon: Store,
      title: 'Webstore Builder',
      tagline: 'Sell online without the hassle',
      description: 'Create fundraiser stores, B2B ordering portals, or public product catalogs. Let customers order directly.',
      capabilities: [
        'Fundraiser stores for schools/teams',
        'B2B customer ordering portals',
        'Product catalog pages',
        'Custom pricing per store',
        'Order management',
        'Inventory tracking',
        'Branded storefronts',
        'Easy setup wizard',
      ],
      color: 'from-pink-500 to-rose-500',
    },
    {
      id: 'scheduling',
      category: 'core',
      icon: Calendar,
      title: 'Scheduling & Calendar',
      tagline: 'Never miss a deadline',
      description: 'See all your jobs on a calendar, schedule installations, and manage your shop\'s capacity.',
      capabilities: [
        'Unified Month / Week / Day calendar views',
        'Large planning calendar with multiple visible items per day',
        'Shared productivity filters across Calendar, Kanban, Task List, and Dashboard',
        'Persisted Kanban drag-and-drop workflow updates',
        'Inline task list editing with sync across all views',
        'Employee schedule and production timing visibility',
        'Waiting-on-approval and due-today dashboard summaries',
        'Integration with real job, production, and task status',
      ],
      color: 'from-orange-500 to-red-500',
    },
    {
      id: 'signatures',
      category: 'core',
      icon: Shield,
      title: 'Signatures, Drawings & Markup',
      tagline: 'Approvals and sketches tied to the exact record',
      description: 'Capture signatures, order sketches, item-level drawings, and markup notes in the exact workflow step where they belong.',
      capabilities: [
        'Feature-toggle controlled signature system',
        'Customer review-and-sign pages with secure links',
        'Order, quote, proof, invoice, and change approval signatures',
        'Order-level and item-level drawing storage',
        'Markup mode on uploaded images',
        'Autosave drafts, undo, pen size, and color controls',
        'Parent-order visibility without duplicating the true approval record',
      ],
      color: 'from-cyan-500 to-blue-500',
    },
    {
      id: 'messaging',
      category: 'core',
      icon: MessageSquare,
      title: 'Built-in Messaging',
      tagline: 'Keep all communication in one place',
      description: 'Message customers and team members without leaving the app. Everything is tied to the relevant job or customer.',
      capabilities: [
        'Customer messaging',
        'Team communication',
        'Messages tied to jobs',
        'Notification alerts',
        'Message history',
        'File sharing in messages',
        'Read receipts',
        'Email notifications',
      ],
      color: 'from-indigo-500 to-blue-500',
    },
  ];

  const filteredFeatures = activeCategory === 'all' 
    ? features 
    : features.filter(f => f.category === activeCategory);

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-[#2F8BFB]/20 text-[#2F8BFB] border-[#2F8BFB]/30 px-4 py-2">
            <Layers className="w-4 h-4 mr-2" />
            Everything You Need
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
            Features That Actually <span className="text-[#2F8BFB]">Make Sense</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Built by a sign shop owner who was tired of software that didn't understand the business. 
            Every feature exists because we needed it in our own shop.
          </p>
        </div>
      </section>

      {/* Category Filter */}
      <section className="px-4 pb-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-wrap justify-center gap-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`px-4 py-2 rounded-full font-medium transition ${
                  activeCategory === cat.id
                    ? 'bg-[#2F8BFB] text-black'
                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                }`}
              >
                {cat.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Features List */}
      <section className="px-4 pb-20">
        <div className="max-w-7xl mx-auto space-y-16">
          {filteredFeatures.map((feature, index) => (
            <div
              key={feature.id}
              className={`grid lg:grid-cols-2 gap-8 items-center ${
                index % 2 === 1 ? 'lg:flex-row-reverse' : ''
              }`}
            >
              <div className={index % 2 === 1 ? 'lg:order-2' : ''}>
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} mb-6`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-white mb-2">{feature.title}</h2>
                <p className="text-[#2F8BFB] font-medium mb-4">{feature.tagline}</p>
                <p className="text-gray-400 mb-6">{feature.description}</p>
                
                <ul className="space-y-2">
                  {feature.capabilities.map((cap, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300">
                      <CheckCircle2 className="w-5 h-5 text-[#2F8BFB] flex-shrink-0 mt-0.5" />
                      {cap}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className={`${index % 2 === 1 ? 'lg:order-1' : ''}`}>
                <div className={`bg-gradient-to-br ${feature.color} p-1 rounded-2xl`}>
                  {featureScreenshots[feature.id] ? (
                    <img 
                      src={featureScreenshots[feature.id]} 
                      alt={`${feature.title} screenshot`}
                      className="w-full h-auto rounded-xl"
                    />
                  ) : (
                    <div className="bg-[#111826] rounded-xl p-8 h-full min-h-[300px] flex items-center justify-center">
                      <div className="text-center">
                        <feature.icon className="w-24 h-24 text-white/20 mx-auto mb-4" />
                        <p className="text-gray-500">Screenshot coming soon</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-[#111826]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Try These Features?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Join the Founding 100 and get lifetime access to all features.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold text-lg px-8 py-6 h-auto">
                Get Founders Edition
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-amber-500/30 text-amber-400 text-lg px-8 py-6 h-auto hover:bg-amber-500/10">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <PublicFooter />
    </div>
  );
}
