import { Link } from 'react-router-dom';
import { HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

const faqs = [
  {
    category: 'Getting Started',
    questions: [
      { q: 'What is the recommended setup order?', a: 'Use the onboarding order built into the app: Quick Start → Standard Setup → Full Optimization. You can skip non-required steps and finish them later.' },
      { q: 'Do I have to complete every onboarding step?', a: 'No. Required steps should be completed early, but most steps can be marked Finish Later and resumed from the onboarding hub.' },
      { q: 'Can I invite customers to the portal right away?', a: 'Yes, but the customer must already exist in the database. Open the customer detail modal and click Invite to Portal.' },
    ]
  },
  {
    category: 'Customer Portal',
    questions: [
      { q: 'How does a customer log in after being invited?', a: 'They use their email address and the temporary PIN from the invitation email. After login, they should change credentials.' },
      { q: 'What can customers do in the portal?', a: 'They can view jobs, review proofs, send messages, download shared documents, complete forms, and view/pay invoices depending on configuration.' },
      { q: 'Can customers see internal job details?', a: 'No. The portal is designed for customer-facing status and records only.' },
    ]
  },
  {
    category: 'AI & Credits',
    questions: [
      { q: 'How are AI credits charged?', a: 'Low actions use 1 credit, medium actions use 2 credits, and high actions use 3 credits. Monthly credits are used before purchased credits.' },
      { q: 'When are credits deducted?', a: 'Only after a successful AI action. Failed actions do not deduct credits.' },
      { q: 'Why does the credit popup still appear even if I hid it?', a: 'The popup intentionally returns for warning cases such as low balance, cost changes, high-cost actions, or when purchased credits will be used.' },
    ]
  },
  {
    category: 'Jobs & Production',
    questions: [
      { q: 'What is the difference between a quote and a job?', a: 'A quote is a job in the quote stage. The same record can move through approval, production, invoicing, and archive.' },
      { q: 'Where do I see the full job history?', a: 'Open the job and use View Timeline. That panel shows the history feed for proofs, stages, documents, and more.' },
      { q: 'Can employees work from their own portal?', a: 'Yes. Employees can view assigned jobs, track stages, and use clock/time features based on permissions.' },
    ]
  }
];

function FAQItem({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-800/50 transition-colors">
        <span className="text-white font-medium">{question}</span>
        {isOpen ? <ChevronUp className="h-5 w-5 text-gray-500" /> : <ChevronDown className="h-5 w-5 text-gray-500" />}
      </button>
      {isOpen && <div className="px-4 pb-4"><p className="text-gray-400">{answer}</p></div>}
    </div>
  );
}

export default function DocsFAQ() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2"><HelpCircle className="h-4 w-4" /> Help</div>
        <h1 className="text-3xl font-bold text-white mb-4">Frequently Asked Questions</h1>
        <p className="text-lg text-gray-400">Practical answers to the questions that come up most often while setting up and running the platform.</p>
      </div>
      {faqs.map((category) => (
        <div key={category.category}>
          <h2 className="text-xl font-semibold text-white mb-4">{category.category}</h2>
          <div className="space-y-2">
            {category.questions.map((faq, index) => <FAQItem key={index} question={faq.q} answer={faq.a} />)}
          </div>
        </div>
      ))}
      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-center">
        <h3 className="text-lg font-semibold text-white mb-2">Still have questions?</h3>
        <p className="text-gray-400 mb-4">Use the onboarding hub, documentation, or support channels depending on what you need.</p>
        <Link to="/contact" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-600 transition-colors">Contact Support</Link>
      </div>
      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/employees" className="text-gray-400 hover:text-white">← Employee Management</Link>
        <Link to="/docs" className="text-cyan-400 hover:text-cyan-300">Back to Docs Overview</Link>
      </div>
    </div>
  );
}