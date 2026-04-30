import { Link } from 'react-router-dom';
import {
  ArrowRight, Briefcase, Calculator, Clock, FileText, PlayCircle,
  Receipt, Sparkles, Store, Users, Zap, FolderOpen
} from 'lucide-react';

const primaryLinks = [
  {
    title: 'Getting Started',
    description: 'Follow the same Quick Start, Standard Setup, and Full Optimization structure used in the live onboarding hub.',
    href: '/docs/getting-started',
    icon: PlayCircle,
    color: 'bg-green-500/10 text-green-400 border-green-500/20'
  },
  {
    title: 'Customers',
    description: 'Customer records, portal invitations, the customer branding profile, account history, orders, quotes, invoices, and portal access.',
    href: '/docs/customers',
    icon: Users,
    color: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
  },
  {
    title: 'Document Library',
    description: 'Store and organize artwork, templates, questionnaires, contracts, and shared files.',
    href: '/docs/document-library',
    icon: FolderOpen,
    color: 'bg-teal-500/10 text-teal-400 border-teal-500/20'
  },
  {
    title: 'Orders, Order Items & Production',
    description: 'Unified order pipeline, order detail tabs, timeline/history, assignments, and production workflow.',
    href: '/docs/quotes-jobs',
    icon: Briefcase,
    color: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
  },
  {
    title: 'Invoicing & Payments',
    description: 'Invoices, portal invoice viewing, PDF download, Stripe-connected payments, and payment tracking.',
    href: '/docs/invoicing',
    icon: Receipt,
    color: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  },
  {
    title: 'AI Tools & Credits',
    description: 'What every AI tool does, how credits work, and where AI is embedded across the platform.',
    href: '/docs/ai-tools',
    icon: Sparkles,
    color: 'bg-pink-500/10 text-pink-400 border-pink-500/20'
  },
  {
    title: 'Pricing System',
    description: 'Company cost settings, calculators, historical invoice analysis, selling benchmarks, and profit math.',
    href: '/docs/pricing-calculator',
    icon: Calculator,
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  },
];

const systemMap = [
  'Customers feed Orders, Order Items, Invoices, Messages, Forms, and Customer Portal access.',
  'Orders are the master container. Order Items inside each order hold production specs, dynamic category fields, and pricing. Production tasks auto-generate from workflow templates.',
  'Pricing settings and historical invoice analysis power calculators, benchmark reporting, and quote quality.',
  'Production workflow and employee stage tracking feed time data, payroll, and future analytics.',
  'AI tools are credit-gated and logged, with monthly credits used before purchased credits.',
  'Customer Portal, Employee Portal, and onboarding all tie back to tenant-specific configuration.'
];

export default function DocsOverview() {
  return (
    <div className="space-y-12">
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-6">
          <Zap className="h-4 w-4" /> Documentation
        </div>
        <h1 className="text-4xl font-bold text-white mb-4">Welcome to SignGuy AI Documentation</h1>
        <p className="text-lg text-gray-400 max-w-3xl mx-auto">
          This documentation is written as training material, not just a reference list.
          It explains how the system is organized, what each module does, and how the pieces work together in daily shop operations.
        </p>
      </div>

      <Link
        to="/docs/getting-started"
        className="block p-6 rounded-xl bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 hover:border-cyan-400/50 transition-all group"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-cyan-500/20">
              <PlayCircle className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">Start with Guided Setup</h3>
              <p className="text-gray-400">Use this if you want the documentation version of the Quick Start → Standard Setup → Full Optimization path.</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
        </div>
      </Link>

      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Browse by Major System</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {primaryLinks.map((link) => {
            const Icon = link.icon;
            return (
              <Link key={link.href} to={link.href} className={`p-5 rounded-xl border ${link.color} hover:scale-[1.02] transition-all group`}>
                <div className="flex items-start gap-4">
                  <Icon className="h-6 w-6 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-white group-hover:text-current transition-colors">{link.title}</h3>
                    <p className="text-sm text-gray-400 mt-1">{link.description}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4">How the Platform Is Structured</h2>
        <div className="space-y-3">
          {systemMap.map((item, index) => (
            <div key={index} className="flex items-start gap-3 text-gray-300">
              <div className="w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center flex-shrink-0">{index + 1}</div>
              <p>{item}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Additional Training Sections</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link to="/docs/time-tracking" className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors">
            <Clock className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">Time & Payroll</h3>
            <p className="text-sm text-gray-500">Order time, employee time, and payroll concepts</p>
          </Link>
          <Link to="/docs/employees" className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors">
            <Users className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">Employees</h3>
            <p className="text-sm text-gray-500">Portal access, assignments, permissions, production stages</p>
          </Link>
          <Link to="/docs/webstores" className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors">
            <Store className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">Webstores</h3>
            <p className="text-sm text-gray-500">Store setup, products, orders, branding, payments</p>
          </Link>
          <Link to="/docs/faq" className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors">
            <FileText className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">FAQ</h3>
            <p className="text-sm text-gray-500">Operational answers to common setup and usage questions</p>
          </Link>
        </div>
      </div>

      <div className="text-center py-8 border-t border-gray-800">
        <p className="text-gray-400">
          Need module-level help while reading? Open the in-app onboarding, customer portal, employee portal, or pricing setup flows to follow the same steps live.
        </p>
      </div>
    </div>
  );
}
