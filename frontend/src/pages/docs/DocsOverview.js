import { Link } from 'react-router-dom';
import { 
  PlayCircle, Users, Briefcase, Receipt, Sparkles, 
  Calculator, Clock, UserCog, ArrowRight, Zap
} from 'lucide-react';

const quickLinks = [
  {
    title: 'Getting Started',
    description: 'New to SignGuy AI? Start here to set up your account and create your first quote.',
    href: '/docs/getting-started',
    icon: PlayCircle,
    color: 'bg-green-500/10 text-green-400 border-green-500/20'
  },
  {
    title: 'Customers',
    description: 'Learn how to manage your customer database and give them portal access.',
    href: '/docs/customers',
    icon: Users,
    color: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
  },
  {
    title: 'Quotes & Jobs',
    description: 'Create quotes, convert them to jobs, and track project progress.',
    href: '/docs/quotes-jobs',
    icon: Briefcase,
    color: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
  },
  {
    title: 'Invoicing',
    description: 'Generate invoices, track payments, and manage your accounts receivable.',
    href: '/docs/invoicing',
    icon: Receipt,
    color: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  },
  {
    title: 'AI Tools Suite',
    description: 'Explore 24+ AI-powered tools for design, branding, and marketing.',
    href: '/docs/ai-tools',
    icon: Sparkles,
    color: 'bg-pink-500/10 text-pink-400 border-pink-500/20'
  },
  {
    title: 'Pricing Calculator',
    description: 'Calculate accurate pricing with built-in profit margins and AI recommendations.',
    href: '/docs/pricing-calculator',
    icon: Calculator,
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  },
];

export default function DocsOverview() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm mb-6">
          <Zap className="h-4 w-4" />
          Documentation
        </div>
        <h1 className="text-4xl font-bold text-white mb-4">
          Welcome to SignGuy AI Documentation
        </h1>
        <p className="text-lg text-gray-400 max-w-2xl mx-auto">
          Everything you need to know about running your sign shop with SignGuy AI. 
          From getting started to advanced features, we've got you covered.
        </p>
      </div>

      {/* Quick Start Banner */}
      <Link 
        to="/docs/getting-started"
        className="block p-6 rounded-xl bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 hover:border-cyan-400/50 transition-all group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-cyan-500/20">
              <PlayCircle className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white group-hover:text-cyan-400 transition-colors">
                New to SignGuy AI?
              </h3>
              <p className="text-gray-400">
                Follow our quick start guide to set up your shop in under 10 minutes
              </p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
        </div>
      </Link>

      {/* Quick Links Grid */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Browse by Feature</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {quickLinks.map((link) => {
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                to={link.href}
                className={`p-5 rounded-xl border ${link.color} hover:scale-[1.02] transition-all group`}
              >
                <div className="flex items-start gap-4">
                  <Icon className="h-6 w-6 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-white group-hover:text-current transition-colors">
                      {link.title}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">
                      {link.description}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Additional Resources */}
      <div className="border-t border-gray-800 pt-8">
        <h2 className="text-xl font-semibold text-white mb-6">Additional Resources</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/docs/time-tracking"
            className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <Clock className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">Time Tracking</h3>
            <p className="text-sm text-gray-500">Track time on jobs and manage employee hours</p>
          </Link>
          <Link
            to="/docs/employees"
            className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <UserCog className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">Employee Management</h3>
            <p className="text-sm text-gray-500">Set up employees and manage permissions</p>
          </Link>
          <Link
            to="/docs/faq"
            className="p-4 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <Zap className="h-5 w-5 text-gray-400 mb-2" />
            <h3 className="font-medium text-white">FAQ</h3>
            <p className="text-sm text-gray-500">Answers to common questions</p>
          </Link>
        </div>
      </div>

      {/* Help Footer */}
      <div className="text-center py-8 border-t border-gray-800">
        <p className="text-gray-400">
          Can't find what you're looking for?{' '}
          <Link to="/contact" className="text-cyan-400 hover:underline">
            Contact Support
          </Link>
        </p>
      </div>
    </div>
  );
}
