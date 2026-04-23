import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Users, FileText, Calculator, Receipt, Clock, DollarSign,
  Sparkles, BarChart3, Store, Shield, CheckCircle2,
  ArrowRight, Briefcase, Calendar,
  MessageSquare, ClipboardList, Settings,
  CreditCard, UserCheck, Layers
} from 'lucide-react';

// Feature screenshots mapping
const featureScreenshots = {
  'customers': '/screenshots/feature_customers.jpeg',
  'jobs': '/screenshots/feature_jobs.jpeg',
  'quotes': '/screenshots/feature_quotes.jpeg',
  'invoicing': '/screenshots/feature_invoices.jpeg',
  'platform-payments': '/screenshots/feature_invoices.jpeg',
  'time-tracking': '/screenshots/feature_time_clock.jpeg',
  'payroll': '/screenshots/feature_dashboard.jpeg',
  'ai-tools': '/screenshots/feature_ai_tools.jpeg',
  'customer-portal': '/screenshots/feature_dashboard.jpeg',
  'employee-portal': '/screenshots/feature_time_clock.jpeg',
  'webstores': '/screenshots/feature_webstores.jpeg',
  'scheduling': '/screenshots/feature_dashboard.jpeg',
  'signatures': '/screenshots/feature_jobs.jpeg',
  'messaging': '/screenshots/feature_dashboard.jpeg',
  'intake-forms': '/screenshots/feature_customers.jpeg',
  'reporting': '/screenshots/feature_dashboard.jpeg',
  'admin-controls': '/screenshots/feature_settings.jpeg',
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
      title: 'Smart Pricing & Detailed Order Items',
      tagline: 'Category calculators built for real sign shop quoting',
      description: 'Quote confidently with detailed category logic and live estimate updates that react instantly as specs change.',
      capabilities: [
        'Digital Print, Cut Vinyl, Rigid Signs, Banners, Vehicle Graphics, Apparel',
        'Services, Promotional, and Custom pricing modes',
        'Live estimate panel with rush, setup, labor, and material impacts',
        'Progressive field reveal logic so only relevant controls are shown',
        'Duplicate, variation, and cross-category conversion workflow',
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
      id: 'platform-payments',
      category: 'financial',
      icon: CreditCard,
      title: 'Platform Billing + Stripe Connect',
      tagline: 'Subscriptions, customer payments, and payout operations',
      description: 'Run SaaS billing and merchant payment flows in one system with clear status visibility and reconciliation coverage.',
      capabilities: [
        'Plan checkout, trial handling, and billing state visibility',
        'Stripe Connect onboarding for merchant payout readiness',
        'Connect status monitoring and recovery paths',
        'Invoice payment reconciliation via webhook and fallback polling',
        'Refund-aware invoice state synchronization',
        'Credit pack purchases for AI usage',
      ],
      color: 'from-orange-500 to-amber-500',
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
        'Timeclock with working / lunch / clock-out states',
        'Task type categorization and employee time logs',
        'Labor cost calculations',
        'Time summaries per job',
        'Timezone-aware shift rendering',
        'Stale shift protection and cleanup',
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
        'Pay period summaries with worksheet editing',
        'Paid in Full action by employee and pay period',
        'Configurable adjustments panel visibility from settings',
        'Profit margin reports',
        'Revenue tracking',
        'Expense categorization',
        'Financial dashboard and exports',
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
      description: 'Generate assets, draft content, assist with operational tasks, and speed up quoting with AI embedded directly in workflow screens.',
      capabilities: [
        'Logo Creator - generate logo concepts',
        'Sign Designer - AI sign mockups',
        'Banner Designer - promotional banners',
        'Mockup Creator - realistic product mockups',
        'Tagline Generator - catchy business taglines',
        'Business Copywriter - marketing copy',
        'Pricing Advisor - AI pricing suggestions',
        'Brand Color Advisor - color palettes',
        'AI business assistant with multi-turn chat',
        'AI services prefill for structured estimates',
        'Voice transcription and document extraction workflows',
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
      description: 'Give customers 24/7 self-service for approvals, payments, status visibility, and communication without back-and-forth chaos.',
      capabilities: [
        'Branded portal with your logo',
        'Order status visibility',
        'Artwork and proof approval workflow',
        'Review-and-sign customer signature links',
        'Online payment processing',
        'Message your team directly',
        'Documents, invoices, and receipts access',
        'Appointments and profile management',
        'Questionnaire/form history visibility',
        'Request new quotes',
        'View order history',
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
        'Simple clock in/out + lunch states',
        'View assigned jobs and tasks',
        'Task completion synced to admin workflow',
        'Time clock history and schedule visibility',
        'Pay period and pay stub access',
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
        'Order management and checkout flow',
        'Inventory tracking',
        'Convert webstore orders into internal production orders',
        'Store analytics and payout tracking tools',
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
      description: 'Coordinate production timelines, appointments, and team schedules in one connected planning view.',
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
        'Public secure signature links for customer approvals',
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
    {
      id: 'intake-forms',
      category: 'portals',
      icon: FileText,
      title: 'Questionnaires & Intake Forms',
      tagline: 'Capture better requirements before work starts',
      description: 'Collect structured customer intake with public forms and keep submissions tied to the right records.',
      capabilities: [
        'Public questionnaire links for new requests',
        'Custom field types with required-field validation',
        'Submission tracking in admin workflow',
        'File upload support in intake forms',
        'Portal-side form history visibility',
        'Faster handoff from intake to quoting',
      ],
      color: 'from-fuchsia-500 to-purple-500',
    },
    {
      id: 'reporting',
      category: 'financial',
      icon: BarChart3,
      title: 'Reports, Productivity & Margin Analytics',
      tagline: 'See what is profitable and where operations are stuck',
      description: 'Understand performance across orders, labor, cash flow, and margins with drill-down reporting views.',
      capabilities: [
        'Profit margin analytics by order and category',
        'Revenue, expenses, and aging visibility',
        'Productivity board linking jobs, appointments, and tasks',
        'Payroll and time exports for reconciliation',
        'Dashboard widgets for due-today and waiting approvals',
        'CSV exports for external analysis',
      ],
      color: 'from-sky-500 to-cyan-500',
    },
    {
      id: 'admin-controls',
      category: 'core',
      icon: Settings,
      title: 'Admin Controls, Team Access & Onboarding',
      tagline: 'Set rules once, keep the shop aligned',
      description: 'Control permissions, branding, defaults, and onboarding flows so your team can work consistently at scale.',
      capabilities: [
        'Team invites, role-based permissions, and access control',
        'Company settings, branding, and operational defaults',
        'Pricing foundation and materials configuration',
        'Email template and digest settings',
        'Guided onboarding checklist and setup flows',
        'Customer and employee portal permission controls',
      ],
      color: 'from-slate-500 to-blue-500',
    },
  ];

  const coverageHighlights = [
    {
      id: 'coverage-commerce',
      icon: CreditCard,
      title: 'Commerce Coverage',
      items: [
        'Quote → Order → Invoice flow',
        'Stripe billing and trials',
        'Stripe Connect payout operations',
        'Refund-aware reconciliation',
      ],
    },
    {
      id: 'coverage-ops',
      icon: Briefcase,
      title: 'Operations Coverage',
      items: [
        'Production board and task execution',
        'Scheduling and workforce views',
        'Timeclock + payroll worksheets',
        'Approvals, proofs, and signatures',
      ],
    },
    {
      id: 'coverage-portals',
      icon: UserCheck,
      title: 'Portal Coverage',
      items: [
        'Customer portal modules',
        'Employee portal modules',
        'Public intake forms',
        'Branded webstores',
      ],
    },
    {
      id: 'coverage-admin',
      icon: ClipboardList,
      title: 'Admin Coverage',
      items: [
        'Team roles and permissions',
        'Company and pricing settings',
        'Onboarding workflows',
        'Financial and productivity reporting',
      ],
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
                data-testid={`features-category-${cat.id}`}
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

      <section className="px-4 pb-14" data-testid="features-coverage-highlights">
        <div className="max-w-7xl mx-auto grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {coverageHighlights.map((highlight) => (
            <div key={highlight.id} className="rounded-2xl border border-white/10 bg-white/5 p-5" data-testid={highlight.id}>
              <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#2F8BFB]/20 text-[#2F8BFB]">
                <highlight.icon className="h-5 w-5" />
              </div>
              <h3 className="mb-3 text-lg font-semibold text-white">{highlight.title}</h3>
              <ul className="space-y-2">
                {highlight.items.map((item) => (
                  <li key={item} className="text-sm text-gray-300">• {item}</li>
                ))}
              </ul>
            </div>
          ))}
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
                      data-testid={`feature-screenshot-${feature.id}`}
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
