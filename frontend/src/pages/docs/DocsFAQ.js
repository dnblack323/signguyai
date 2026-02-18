import { Link } from 'react-router-dom';
import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

const faqs = [
  {
    category: 'Getting Started',
    questions: [
      {
        q: 'How do I start my free trial?',
        a: 'Click "Start Free Trial" on the homepage. Enter your email, password, name, and company name. Your 24-hour trial starts immediately with no credit card required.'
      },
      {
        q: 'What happens after my trial ends?',
        a: 'After 24 hours, you\'ll need to select a subscription plan to continue using SignGuy AI. Your data is preserved during this time.'
      },
      {
        q: 'Can I import existing customer data?',
        a: 'Currently, customers need to be added manually. Bulk import functionality is planned for a future update.'
      }
    ]
  },
  {
    category: 'Quotes & Jobs',
    questions: [
      {
        q: 'How do I create a quote?',
        a: 'Go to Quotes > New Quote, select a customer, add line items with descriptions and prices, then save or send directly to the customer.'
      },
      {
        q: 'Can customers approve quotes online?',
        a: 'Yes! Use the "Share Link" button to generate a customer portal link. Customers can view and approve quotes directly in their portal.'
      },
      {
        q: 'How do I track job progress?',
        a: 'Open any job to see its status timeline. Jobs progress through: Quoted → Approved → In Production → Installed → Complete. Change status using the dropdown.'
      }
    ]
  },
  {
    category: 'AI Tools',
    questions: [
      {
        q: 'What AI tools are included?',
        a: 'SignGuy AI includes 24+ tools: Logo Refresher, Text to Image, Vehicle Wrap Mockup, Blog Creator, Social Post Creator, Sign Designer, and many more across Design, Branding, Business, and Marketing categories.'
      },
      {
        q: 'Do AI tools cost extra?',
        a: 'Basic AI features are included in all plans. Some advanced AI tools may require the AI Tools Add-On depending on your subscription tier.'
      },
      {
        q: 'Can I use AI to draft emails?',
        a: 'Yes! Look for the purple "AI Draft" button when viewing invoices or quotes. It generates professional email text based on the context.'
      }
    ]
  },
  {
    category: 'Employee Portal',
    questions: [
      {
        q: 'How do employees log in?',
        a: 'Employees use a separate portal at /employee-portal/login. They sign in with their email and PIN (default is 1234 or last 4 digits of phone).'
      },
      {
        q: 'What can employees do in their portal?',
        a: 'Clock in/out, take breaks, view assigned tasks, see pay information, and update their profile.'
      },
      {
        q: 'How do I set employee permissions?',
        a: 'When adding an employee, assign them a role: Admin (full access), Manager (manage jobs/customers), or Staff (basic task access).'
      }
    ]
  },
  {
    category: 'Billing & Pricing',
    questions: [
      {
        q: 'What payment methods do you accept?',
        a: 'We accept all major credit cards through Stripe. Enterprise customers can arrange invoicing.'
      },
      {
        q: 'Can I change my plan later?',
        a: 'Yes, you can upgrade or downgrade your plan at any time from Settings > Billing.'
      },
      {
        q: 'Is there a refund policy?',
        a: 'We offer a 30-day money-back guarantee for annual plans. Monthly plans can be cancelled anytime.'
      }
    ]
  }
];

function FAQItem({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-800/50 transition-colors"
      >
        <span className="text-white font-medium">{question}</span>
        {isOpen ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4">
          <p className="text-gray-400">{answer}</p>
        </div>
      )}
    </div>
  );
}

export default function DocsFAQ() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <HelpCircle className="h-4 w-4" />
          Help
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Frequently Asked Questions</h1>
        <p className="text-lg text-gray-400">
          Find answers to common questions about SignGuy AI.
        </p>
      </div>

      {faqs.map((category) => (
        <div key={category.category}>
          <h2 className="text-xl font-semibold text-white mb-4">{category.category}</h2>
          <div className="space-y-2">
            {category.questions.map((faq, i) => (
              <FAQItem key={i} question={faq.q} answer={faq.a} />
            ))}
          </div>
        </div>
      ))}

      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Still have questions?</h3>
        <p className="text-gray-400 mb-4">
          Can't find what you're looking for? We're here to help.
        </p>
        <Link
          to="/contact"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-600 transition-colors"
        >
          Contact Support
        </Link>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/employees" className="text-gray-400 hover:text-white">
          ← Employee Management
        </Link>
        <Link to="/docs" className="text-cyan-400 hover:text-cyan-300">
          Back to Docs Overview
        </Link>
      </div>
    </div>
  );
}
