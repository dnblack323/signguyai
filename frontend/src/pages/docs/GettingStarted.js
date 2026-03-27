import { Link } from 'react-router-dom';
import {
  ArrowRight, CheckCircle, Clock, PlayCircle, Settings, Sparkles,
  Users, FileText, Briefcase
} from 'lucide-react';

const quickStart = [
  {
    title: 'Complete Company Profile',
    bullets: [
      'Open Company Settings and fill in company name, address, phone, business email, and logo.',
      'This information drives invoices, quotes, customer portal branding, and documents.',
      'Treat this as the minimum required setup before daily work starts.'
    ]
  },
  {
    title: 'Connect Stripe',
    bullets: [
      'Open Payment Settings and connect Stripe if you want invoice payments and webstore checkout to work.',
      'If you skip it, payment features stay disabled until later.',
      'The system now uses Stripe Connect for customer-facing payment experiences.'
    ]
  },
  {
    title: 'Choose a Production Workflow',
    bullets: [
      'Simple is the recommended fast-start option: Design → Production → Installation / Completion.',
      'Detailed and Custom workflows can be configured later by category.',
      'This choice controls new production timelines and history visibility.'
    ]
  },
  {
    title: 'Add Your First Employee',
    bullets: [
      'Create at least one employee so clock-in, assigned tickets, and stage tracking can be tested.',
      'Employees use the Employee Portal to see assigned work and act on stages.',
      'You can control sensitive-visibility settings from Company Settings.'
    ]
  },
  {
    title: 'Enter Basic Pricing Values',
    bullets: [
      'At minimum enter Vinyl, Banner Material, Coroplast, and Production Hourly Rate.',
      'These numbers make calculators usable immediately.',
      'You can deepen pricing later with overhead, markup, benchmarks, and category defaults.'
    ]
  },
  {
    title: 'Enable Customer Portal',
    bullets: [
      'Turn on approvals, messaging, document sharing, and invoice payments as needed.',
      'Customers must already exist in the database before they can be invited.',
      'Use the customer detail modal and click Invite to Portal to generate temporary access.'
    ]
  },
  {
    title: 'Create a Test Order',
    bullets: [
      'Create a customer, then create an Order with Job Tickets.',
      'Upload artwork, add job tickets (Quick or Detailed entry), enable production workflow, and test the full order lifecycle.',
      'This is the fastest way to validate the operational loop.'
    ]
  },
  {
    title: 'Run a Customer Portal Test',
    bullets: [
      'Send a proof, a message, and a document.',
      'Confirm the customer can log in, respond, and see the right records.',
      'This verifies portal access before you rely on it with real customers.'
    ]
  }
];

const standardSetup = [
  'Import historical invoices so AI can suggest selling benchmarks.',
  'Configure deeper material, labor, overhead, and target profit settings.',
  'Review categories, category workflows, document organization, and questionnaire templates.',
  'Review AI tool access, notifications, workflow templates, and customer portal behavior.',
  'Run a realistic workflow test using orders, job tickets, proofs, forms, messages, and invoices.'
];

const fullOptimization = [
  'Confirm production analytics and labor-cost capture are usable for reporting.',
  'Use Profit & Margin Analytics to review orders, categories, and customer profitability.',
  'Review customer experience enhancements, automation plans, security, backup tools, and dashboard customization.',
  'Treat Full Optimization as the stage where the platform becomes a strategic shop operating system, not just a tracker.'
];

export default function GettingStarted() {
  return (
    <div className="space-y-12">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <PlayCircle className="h-4 w-4" />
          Introduction
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Getting Started</h1>
        <p className="text-lg text-gray-400">
          SignGuy AI now has a three-stage onboarding model in the live app: Quick Start, Standard Setup, and Full Optimization.
          This page explains that same structure in training language so owners and admins understand what to do first, what can wait, and what to optimize later.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">How to Use This Guide</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: Clock, title: 'Quick Start', desc: 'Get operational fast in about 10 minutes.' },
            { icon: Settings, title: 'Standard Setup', desc: 'Configure the shop so daily usage is accurate and organized.' },
            { icon: Sparkles, title: 'Full Optimization', desc: 'Review analytics, automation, and advanced operational controls.' }
          ].map((item) => (
            <div key={item.title} className="p-4 rounded-lg bg-gray-800/50">
              <item.icon className="h-5 w-5 text-cyan-400 mb-2" />
              <h3 className="font-medium text-white">{item.title}</h3>
              <p className="text-sm text-gray-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Quick Start Setup</h2>
        <div className="space-y-6">
          {quickStart.map((step, index) => (
            <div key={step.title} className="flex gap-4">
              <div className="w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 flex items-center justify-center font-bold flex-shrink-0">
                {index + 1}
              </div>
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-white">{step.title}</h3>
                <ul className="space-y-2">
                  {step.bullets.map((bullet, bulletIndex) => (
                    <li key={bulletIndex} className="flex items-start gap-3 text-gray-300">
                      <CheckCircle className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
          <h2 className="text-xl font-semibold text-white mb-4">Standard Setup (Recommended)</h2>
          <div className="space-y-3">
            {standardSetup.map((item, index) => (
              <div key={index} className="flex items-start gap-3 text-gray-300">
                <div className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 text-sm flex items-center justify-center flex-shrink-0">{index + 1}</div>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
          <h2 className="text-xl font-semibold text-white mb-4">Full Optimization</h2>
          <div className="space-y-3">
            {fullOptimization.map((item, index) => (
              <div key={index} className="flex items-start gap-3 text-gray-300">
                <div className="w-6 h-6 rounded-full bg-amber-500/20 text-amber-400 text-sm flex items-center justify-center flex-shrink-0">{index + 1}</div>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-gradient-to-r from-green-500/20 to-cyan-500/20 border border-green-500/30">
        <h3 className="text-lg font-semibold text-white mb-3">Best Practice</h3>
        <p className="text-gray-300">
          Use the live onboarding hub inside the app when you want the interactive version.
          Use this documentation page when you want the training version that explains why each setup step matters.
        </p>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Recommended Next Reading</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { title: 'Customers', href: '/docs/customers', icon: Users, description: 'Learn customer records, portal invites, and account history.' },
            { title: 'Orders Orders Orders & Job Tickets Job Tickets Job Tickets', href: '/docs/quotes-jobs', icon: Briefcase, description: 'Understand the operational pipeline from order intake to production.' },
            { title: 'Invoicing', href: '/docs/invoicing', icon: FileText, description: 'Review invoices, portal access, and payment flow.' },
          ].map((item) => (
            <Link key={item.href} to={item.href} className="p-5 rounded-xl bg-gray-900/50 border border-gray-800 hover:border-cyan-500/30 transition-all group">
              <item.icon className="h-6 w-6 text-gray-400 group-hover:text-cyan-400 mb-3 transition-colors" />
              <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors">{item.title}</h3>
              <p className="text-sm text-gray-500 mt-1">{item.description}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="text-center py-8 border-t border-gray-800">
        <p className="text-gray-400">
          Need help? Use the onboarding hub in the app, check the FAQ, or contact support.
        </p>
      </div>
    </div>
  );
}
