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
      { q: 'What can customers do in the portal?', a: 'They can view orders, review proofs, send messages, download shared documents, complete forms, view/pay invoices, approve quotes, and request appointments.' },
      { q: 'Can customers see internal order details?', a: 'No. The portal is designed for customer-facing status and records only. Internal notes, production stages, and pricing breakdowns are hidden.' },
      { q: 'Can customers request appointments?', a: 'Yes. Customers can submit appointment requests through the portal specifying type, date, time, and location. You receive an email notification and can confirm or reject the request.' },
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
    category: 'Orders & Production',
    questions: [
      { q: 'What is the difference between a quote and an order?', a: 'A quote is a financial document you send to a customer for approval. Once approved, it converts to an order which tracks production.' },
      { q: 'Where do I see the full order history?', a: 'Open the order and use View Timeline. That panel shows the history feed for proofs, stages, documents, signatures, and more.' },
      { q: 'Can employees work from their own portal?', a: 'Yes. Employees can view assigned orders, track stages, and use clock/time features based on permissions.' },
      { q: 'How do signatures work?', a: 'You can capture customer signatures directly on orders using the signature modal. Signatures are stored with signer name, timestamp, and IP address for verification.' },
      { q: 'What are order drawings?', a: 'The drawing/whiteboard feature lets you create sketches, measurement notes, or install diagrams directly on orders. Supports pen, arrow, circle, and text tools with autosave.' },
    ]
  },
  {
    category: 'Billing & Payments',
    questions: [
      { q: 'How do customer payments work?', a: 'Connect Stripe in Settings → Payment Settings. Customers can pay invoices via the portal or through emailed payment links. Payments go directly to your Stripe balance.' },
      { q: 'Are tax-exempt customers handled?', a: 'Yes. Mark a customer as tax-exempt in their profile and invoices will automatically calculate zero tax for them.' },
      { q: 'Can I track partial payments?', a: 'Yes. The system supports partial payments and tracks remaining balances on invoices.' },
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
            {category.questions.map((faq) => <FAQItem key={faq.q} question={faq.q} answer={faq.a} />)}
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