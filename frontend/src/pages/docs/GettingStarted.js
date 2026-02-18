import { Link } from 'react-router-dom';
import { 
  CheckCircle, ArrowRight, Users, FileText, Briefcase,
  Settings, PlayCircle, Clock, Sparkles
} from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Create Your Account',
    description: 'Sign up with your email and set up your sign shop profile.',
    details: [
      'Go to the SignGuy AI homepage and click "Start Free Trial"',
      'Enter your email, password, full name, and company name',
      'Your 24-hour free trial starts immediately - no credit card required',
      'You\'ll be automatically logged into your new dashboard'
    ],
    tip: 'Use a strong password with at least 8 characters, including numbers and symbols.'
  },
  {
    number: '02',
    title: 'Add Your First Customer',
    description: 'Set up a customer record to start creating quotes.',
    details: [
      'Navigate to Customers from the sidebar',
      'Click "Add Customer" in the top right',
      'Enter customer name, email, phone, and company (if applicable)',
      'Click "Create" to save the customer'
    ],
    link: { text: 'Learn more about Customers', href: '/docs/customers' },
    tip: 'Adding an email enables you to send quotes and invoices directly to the customer.'
  },
  {
    number: '03',
    title: 'Create Your First Quote',
    description: 'Build a professional quote with line items and pricing.',
    details: [
      'Navigate to Quotes from the sidebar',
      'Click "New Quote" in the top right',
      'Select your customer from the dropdown',
      'Add line items with descriptions, quantities, and prices',
      'Use the Pricing Calculator for accurate pricing (click the calculator icon)',
      'Save as Draft or Send directly to the customer'
    ],
    link: { text: 'Learn more about Quotes', href: '/docs/quotes-jobs' },
    tip: 'The AI Pricing Advisor can suggest optimal pricing - look for the purple sparkle button!'
  },
  {
    number: '04',
    title: 'Convert Quote to Job',
    description: 'Once approved, turn your quote into an active job.',
    details: [
      'Open the approved quote by clicking the eye icon',
      'Click "Convert to Job" button',
      'The job will be created with all quote details',
      'Track progress through the job status timeline'
    ],
    link: { text: 'Learn more about Jobs', href: '/docs/quotes-jobs' },
    tip: 'Jobs automatically track through stages: Quoted → Approved → In Production → Installed → Complete'
  },
  {
    number: '05',
    title: 'Generate an Invoice',
    description: 'Bill your customer for completed work.',
    details: [
      'Navigate to Invoices from the sidebar',
      'Click "New Invoice"',
      'Select the customer and optionally link to a job',
      'The total can be auto-filled from the job',
      'Send via email with one click'
    ],
    link: { text: 'Learn more about Invoicing', href: '/docs/invoicing' },
    tip: 'Use the "AI Draft" button to generate professional email text for your invoices.'
  }
];

const nextSteps = [
  {
    title: 'Explore AI Tools',
    description: '24+ AI-powered tools for design, branding, and marketing',
    href: '/docs/ai-tools',
    icon: Sparkles
  },
  {
    title: 'Set Up Employees',
    description: 'Add team members and give them portal access',
    href: '/docs/employees',
    icon: Users
  },
  {
    title: 'Configure Time Tracking',
    description: 'Track time on jobs for accurate labor costing',
    href: '/docs/time-tracking',
    icon: Clock
  }
];

export default function GettingStarted() {
  return (
    <div className="space-y-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <PlayCircle className="h-4 w-4" />
          Introduction
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Getting Started</h1>
        <p className="text-lg text-gray-400">
          Welcome to SignGuy AI! This guide will walk you through the basics of setting up 
          your sign shop and creating your first quote. You'll be up and running in about 10 minutes.
        </p>
      </div>

      {/* What You'll Learn */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">What You'll Learn</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            'Create your SignGuy AI account',
            'Add your first customer',
            'Build and send a professional quote',
            'Convert quotes to active jobs',
            'Generate and send invoices'
          ].map((item, index) => (
            <div key={index} className="flex items-center gap-2 text-gray-300">
              <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-8">
        <h2 className="text-xl font-semibold text-white">Step-by-Step Setup</h2>
        
        {steps.map((step, index) => (
          <div key={index} className="relative">
            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="absolute left-6 top-16 bottom-0 w-px bg-gray-800" />
            )}
            
            <div className="flex gap-6">
              {/* Step Number */}
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
                <span className="text-cyan-400 font-bold">{step.number}</span>
              </div>
              
              {/* Step Content */}
              <div className="flex-1 pb-8">
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-gray-400 mb-4">{step.description}</p>
                
                {/* Details List */}
                <ol className="space-y-2 mb-4">
                  {step.details.map((detail, detailIndex) => (
                    <li key={detailIndex} className="flex items-start gap-3 text-gray-300">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-800 text-xs flex items-center justify-center text-gray-500">
                        {detailIndex + 1}
                      </span>
                      <span>{detail}</span>
                    </li>
                  ))}
                </ol>
                
                {/* Tip Box */}
                {step.tip && (
                  <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200 text-sm">
                    <strong className="text-amber-400">Tip:</strong> {step.tip}
                  </div>
                )}
                
                {/* Learn More Link */}
                {step.link && (
                  <Link 
                    to={step.link.href}
                    className="inline-flex items-center gap-2 mt-4 text-cyan-400 hover:text-cyan-300 text-sm"
                  >
                    {step.link.text}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Success Message */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-green-500/20 to-cyan-500/20 border border-green-500/30">
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-lg bg-green-500/20">
            <CheckCircle className="h-6 w-6 text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">You're All Set!</h3>
            <p className="text-gray-300">
              Congratulations! You now know the basics of SignGuy AI. You've created a customer, 
              built a quote, converted it to a job, and generated an invoice. You're ready to 
              start running your sign shop like a pro.
            </p>
          </div>
        </div>
      </div>

      {/* Next Steps */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">What's Next?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {nextSteps.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                to={item.href}
                className="p-5 rounded-xl bg-gray-900/50 border border-gray-800 hover:border-cyan-500/30 hover:bg-gray-900 transition-all group"
              >
                <Icon className="h-6 w-6 text-gray-400 group-hover:text-cyan-400 mb-3 transition-colors" />
                <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors">
                  {item.title}
                </h3>
                <p className="text-sm text-gray-500 mt-1">{item.description}</p>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Need Help */}
      <div className="text-center py-8 border-t border-gray-800">
        <p className="text-gray-400">
          Need help? Check our{' '}
          <Link to="/docs/faq" className="text-cyan-400 hover:underline">FAQ</Link>
          {' '}or{' '}
          <Link to="/contact" className="text-cyan-400 hover:underline">contact support</Link>.
        </p>
      </div>
    </div>
  );
}
