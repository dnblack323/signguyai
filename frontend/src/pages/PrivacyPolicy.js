import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-[#060A13] text-slate-300" data-testid="privacy-policy-page">
      <div className="max-w-3xl mx-auto px-4 py-16">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <h1 className="text-4xl font-bold text-white mb-2">Privacy Policy</h1>
        <p className="text-sm text-slate-500 mb-10">Last updated: March 20, 2026</p>

        <div className="space-y-8 leading-relaxed text-[15px]">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Introduction</h2>
            <p>SignGuy AI ("we," "our," "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Platform. This policy complies with applicable data protection regulations including GDPR.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. Information We Collect</h2>
            <p className="mb-2"><strong className="text-white">Account Information:</strong> Name, email address, company name, phone number, and password (hashed).</p>
            <p className="mb-2"><strong className="text-white">Business Data:</strong> Customer records, job details, invoices, quotes, employee information, time entries, and financial data you enter into the Platform.</p>
            <p className="mb-2"><strong className="text-white">Payment Information:</strong> Billing details are processed securely by Stripe. We do not store full credit card numbers.</p>
            <p className="mb-2"><strong className="text-white">Usage Data:</strong> Pages visited, features used, AI tool usage, credit consumption, and session information.</p>
            <p><strong className="text-white">AI Interaction Data:</strong> Prompts sent to AI tools, generated content, and voice input/output transcriptions.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>To provide and maintain the Platform and its features.</li>
              <li>To process payments and manage subscriptions.</li>
              <li>To power AI-driven tools and personalized business insights.</li>
              <li>To send transactional emails (invoices, notifications, password resets).</li>
              <li>To improve the Platform based on usage patterns.</li>
              <li>To comply with legal obligations.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. AI Data Processing</h2>
            <p>When you use AI-powered features, your input data is processed by third-party AI providers (OpenAI). AI-generated content is stored in your tenant's data. We do not use your business data to train AI models. Voice input is transcribed using OpenAI Whisper and is not retained beyond the session.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. Third-Party Services</h2>
            <p className="mb-2">We share data with the following third-party services as necessary to operate the Platform:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-white">Stripe:</strong> Payment processing, subscription management, and webstore transactions.</li>
              <li><strong className="text-white">SendGrid:</strong> Transactional email delivery (invoices, notifications).</li>
              <li><strong className="text-white">OpenAI:</strong> AI text generation, image generation, speech-to-text, and text-to-speech.</li>
              <li><strong className="text-white">MongoDB Atlas:</strong> Database hosting and storage.</li>
            </ul>
            <p className="mt-2">Each third-party service operates under its own privacy policy and data protection standards.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. Data Security</h2>
            <p>We implement industry-standard security measures including encrypted connections (HTTPS/TLS), hashed passwords (bcrypt), JWT-based authentication, role-based access control, and multi-tenant data isolation. Despite these measures, no method of electronic storage is 100% secure.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Data Retention</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Active account data is retained as long as your subscription is active.</li>
              <li>After account termination, data is retained for 30 days before permanent deletion.</li>
              <li>Payment records may be retained longer as required by law.</li>
              <li>AI interaction history is retained for your reference and can be deleted upon request.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Your Rights (GDPR)</h2>
            <p className="mb-2">You have the right to:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-white">Access:</strong> Request a copy of your personal data.</li>
              <li><strong className="text-white">Rectification:</strong> Correct inaccurate personal data.</li>
              <li><strong className="text-white">Erasure:</strong> Request deletion of your personal data ("right to be forgotten").</li>
              <li><strong className="text-white">Portability:</strong> Export your data in a machine-readable format (JSON).</li>
              <li><strong className="text-white">Restriction:</strong> Restrict processing of your personal data.</li>
              <li><strong className="text-white">Objection:</strong> Object to processing based on legitimate interests.</li>
            </ul>
            <p className="mt-2">To exercise these rights, contact us at <a href="mailto:privacy@signguyai.com" className="text-violet-400 hover:underline">privacy@signguyai.com</a>.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Cookies</h2>
            <p>We use essential browser storage for authentication and session management. Auth tokens are stored with session-first handling, and persistent storage is used only when explicitly requested (for example, with a remembered login). We do not use third-party tracking cookies or advertising pixels. Analytics data is collected server-side without marketing cookies.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Children's Privacy</h2>
            <p>The Platform is not intended for individuals under 18 years of age. We do not knowingly collect personal information from children.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">11. Changes to This Policy</h2>
            <p>We may update this Privacy Policy periodically. We will notify you of significant changes via email or in-app notification. The "Last updated" date at the top of this page indicates when the policy was last revised.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">12. Contact Us</h2>
            <p>For privacy-related inquiries, data requests, or concerns:</p>
            <p className="mt-2">Email: <a href="mailto:privacy@signguyai.com" className="text-violet-400 hover:underline">privacy@signguyai.com</a></p>
          </section>
        </div>

        <div className="mt-16 pt-8 border-t border-slate-800 text-center text-sm text-slate-500">
          &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
        </div>
      </div>
    </div>
  );
}
