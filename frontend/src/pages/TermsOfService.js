import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PublicFooter, PublicNav } from '../components/PublicNav';

const LAST_UPDATED = 'June 20, 2026';
const SUPPORT_EMAIL = 'support@signguy-ai.com';
const MAILING_ADDRESS = '413 S Pittsburgh St, Connellsville, PA 15425';

export default function TermsOfService() {
  if (typeof document !== 'undefined') {
    document.title = 'Terms of Service | SignGuy AI';
  }
  return (
    <div className="min-h-screen bg-[#060A13] text-slate-300" data-testid="terms-of-service-page">
      <PublicNav />
      <div className="max-w-4xl mx-auto px-4 py-24">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors" data-testid="terms-back-home-link">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <h1 className="text-4xl font-bold text-white mb-3">Terms of Service</h1>
        <p className="text-sm text-slate-500 mb-3">Effective date / Last updated: {LAST_UPDATED}</p>
        <p className="text-slate-200 mb-10" data-testid="terms-identity-statement">
          These Terms govern use of SignGuy AI, a software platform operated by SignTists Lab, a sole proprietorship owned by Donnell Nicole Black.
        </p>

        <div className="space-y-8 leading-relaxed text-[15px]">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Service Description</h2>
            <p>
              SignGuy AI is a SaaS platform for sign shops, wrap shops, print businesses, and related visual-branding companies. The platform includes customer management, quotes, orders, invoices, production workflows, customer portals, webstores, reporting, and messaging features.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. SaaS Subscription Relationship</h2>
            <p>
              Your subscription grants your business access to SignGuy AI as a hosted software service. Access, features, and pricing depend on your subscribed plan and billing status. Use of the platform is subject to these Terms and the <Link to="/privacy" className="text-violet-400 hover:underline">Privacy Policy</Link>.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. Account Responsibilities</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>You must provide accurate account information and keep credentials secure.</li>
              <li>You are responsible for all activity under your account and users you authorize.</li>
              <li>You must use the service in compliance with applicable laws and communication regulations.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. Tenant Responsibility for Customer Communications</h2>
            <p>
              Each tenant (shop/business using SignGuy AI) is solely responsible for communications sent to its own customers, including email and SMS/MMS content, timing, recipient lists, and consent records.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. SMS/MMS Compliance Responsibilities</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Each tenant must obtain valid consent before sending SMS/MMS messages to customers.</li>
              <li>Tenants must provide required disclosures and clear opt-out instructions where required.</li>
              <li>Tenants must use their own business identity in customer messaging.</li>
              <li>Tenants may not present SignGuy AI as the sender unless SignGuy AI itself sends platform-related messages.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. Prohibited Use</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>No spam, unlawful messaging, or abusive content.</li>
              <li>No purchased, scraped, or non-consented contact lists for texting/email campaigns.</li>
              <li>No attempts to bypass platform safeguards, tenant isolation, or service controls.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Payment and Subscription Terms</h2>
            <p>
              Subscription pricing, renewal, billing cadence, and cancellation conditions are defined by the active plan and checkout terms shown at purchase time. Additional processing and usage-based fees may apply based on enabled features.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, the service is provided on an &quot;as is&quot; and &quot;as available&quot; basis, without warranties of uninterrupted or error-free operation. SignTists Lab disclaims liability for indirect, incidental, special, or consequential damages. Direct liability, if any, is limited to amounts paid for the service under applicable law.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Governing Law</h2>
            <p>
              Governing law and venue placeholders apply as configured in your signed agreement or order form where applicable.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Contact Information</h2>
            <p>For questions regarding these Terms:</p>
            <p className="mt-2">Support Email: <a href={`mailto:${SUPPORT_EMAIL}`} className="text-violet-400 hover:underline">{SUPPORT_EMAIL}</a></p>
            <p>Business Mailing Address: {MAILING_ADDRESS}</p>
            <p className="mt-2 text-slate-400">Business Name: SignTists Lab · Product: SignGuy AI · Owner: Donnell Nicole Black</p>
          </section>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}
