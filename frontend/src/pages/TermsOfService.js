import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-[#060A13] text-slate-300" data-testid="terms-of-service-page">
      <div className="max-w-3xl mx-auto px-4 py-16">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <h1 className="text-4xl font-bold text-white mb-2">Terms of Service</h1>
        <p className="text-sm text-slate-500 mb-10">Last updated: March 20, 2026</p>

        <div className="space-y-8 leading-relaxed text-[15px]">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Agreement to Terms</h2>
            <p>By accessing or using SignGuy AI ("the Platform"), you agree to be bound by these Terms of Service. If you do not agree, you may not use the Platform. These terms constitute a legally binding agreement between you and SignGuy AI.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. Description of Service</h2>
            <p>SignGuy AI is a multi-tenant SaaS operating system designed for sign shops, print shops, and custom graphics businesses. The Platform provides customer management, job tracking, invoicing, AI-powered design and business tools, webstore hosting, employee management, and related services.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. Account Registration</h2>
            <p>You must provide accurate information when creating an account. You are responsible for maintaining the security of your account credentials. Each account is associated with a single tenant (business). You must be at least 18 years old to use the Platform.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. Subscription &amp; Billing</h2>
            <p className="mb-2">SignGuy AI operates on a subscription model:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-white">Founders Edition:</strong> $99/month or $594/year (50% annual discount).</li>
              <li>A 48-hour free trial is provided to new accounts.</li>
              <li>Subscriptions renew automatically unless cancelled before the billing period ends.</li>
              <li>Refunds are handled on a case-by-case basis within 14 days of charge.</li>
              <li>Promotional codes may be available and are subject to their own terms.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. Platform Processing Fees</h2>
            <p className="mb-2">The following fees apply to transactions processed through the Platform:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li><strong className="text-white">Platform fee:</strong> 2.2% + $0.20 per transaction on invoices and payments.</li>
              <li><strong className="text-white">Webstore fee:</strong> An additional 2% on webstore sales.</li>
              <li>Third-party payment processor fees (Stripe) are separate and apply at their standard rates.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. AI Credits</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Founders Edition includes 150 AI credits per month.</li>
              <li>Monthly credits do not roll over and reset each billing cycle.</li>
              <li>Purchased credit packs never expire while your subscription is active.</li>
              <li>AI credits are consumed by AI-powered tools at rates of 1-3 credits per action.</li>
              <li>Credit packs are available for purchase: 100 ($10), 300 ($25), and 1,000 ($60).</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Acceptable Use</h2>
            <p className="mb-2">You agree not to:</p>
            <ul className="list-disc pl-6 space-y-1">
              <li>Use the Platform for any unlawful purpose.</li>
              <li>Attempt to access other tenants' data or bypass security measures.</li>
              <li>Use AI tools to generate harmful, misleading, or illegal content.</li>
              <li>Reverse engineer, decompile, or disassemble any part of the Platform.</li>
              <li>Resell or redistribute Platform access without authorization.</li>
              <li>Upload malicious files or attempt to exploit vulnerabilities.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Intellectual Property</h2>
            <p>The Platform, its design, features, and underlying technology are the property of SignGuy AI. Content you create using the Platform (jobs, invoices, designs, etc.) remains your property. AI-generated content is provided under a royalty-free license for your business use.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Data &amp; Privacy</h2>
            <p>Your use of the Platform is also governed by our <Link to="/privacy" className="text-violet-400 hover:underline">Privacy Policy</Link>. We take reasonable measures to protect your data but cannot guarantee absolute security. You are responsible for maintaining backups of your critical business data.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Limitation of Liability</h2>
            <p>SignGuy AI is provided "as is" without warranties of any kind. We are not liable for any indirect, incidental, or consequential damages arising from your use of the Platform. Our total liability shall not exceed the amount you paid in the 12 months preceding the claim.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">11. Termination</h2>
            <p>You may cancel your subscription at any time. We reserve the right to suspend or terminate accounts that violate these terms. Upon termination, your data will be retained for 30 days, after which it may be permanently deleted.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">12. Changes to Terms</h2>
            <p>We may update these terms from time to time. Material changes will be communicated via email or in-app notification. Continued use of the Platform after changes constitutes acceptance of the revised terms.</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">13. Contact</h2>
            <p>For questions about these terms, contact us at <a href="mailto:support@signguyai.com" className="text-violet-400 hover:underline">support@signguyai.com</a>.</p>
          </section>
        </div>

        <div className="mt-16 pt-8 border-t border-slate-800 text-center text-sm text-slate-500">
          &copy; {new Date().getFullYear()} SignGuy AI. All rights reserved.
        </div>
      </div>
    </div>
  );
}
