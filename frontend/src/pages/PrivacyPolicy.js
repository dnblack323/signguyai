import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PublicFooter, PublicNav } from '../components/PublicNav';

const LAST_UPDATED = 'June 20, 2026';
const SUPPORT_EMAIL = 'support@signguy-ai.com';
const MAILING_ADDRESS = '413 S Pittsburgh St, Connellsville, PA 15425';

export default function PrivacyPolicy() {
  if (typeof document !== 'undefined') {
    document.title = 'Privacy Policy | SignGuy AI';
  }
  return (
    <div className="min-h-screen bg-[#060A13] text-slate-300" data-testid="privacy-policy-page">
      <PublicNav />
      <div className="max-w-4xl mx-auto px-4 py-24">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-8 transition-colors" data-testid="privacy-back-home-link">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        <h1 className="text-4xl font-bold text-white mb-3">Privacy Policy</h1>
        <p className="text-sm text-slate-500 mb-3">Effective date / Last updated: {LAST_UPDATED}</p>
        <p className="text-slate-200 mb-10" data-testid="privacy-identity-statement">
          SignGuy AI is operated by SignTists Lab, a sole proprietorship owned by Donnell Nicole Black.
        </p>

        <div className="space-y-8 leading-relaxed text-[15px]">
          <section>
            <h2 className="text-xl font-semibold text-white mb-3">1. Who We Are</h2>
            <p>
              Product/Platform: SignGuy AI<br />
              Business/Trade Name: SignTists Lab<br />
              Business Owner: Donnell Nicole Black<br />
              Business Structure: Sole proprietorship
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">2. Data We Collect</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>Account and profile information (name, email, business details, optional phone).</li>
              <li>Tenant business data entered into the platform (customers, quotes, orders, invoices, production and workflow records).</li>
              <li>Customer contact information stored by tenant shops (such as names, emails, phone numbers, and addresses).</li>
              <li>Webstore and portal data, when those modules are used.</li>
              <li>System logs and product analytics needed for platform operation, reliability, and security.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">3. Email Communications</h2>
            <p>
              We may send transactional email messages for account access, security, billing, support, operational updates, and requested service notifications.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">4. SMS/MMS Communications</h2>
            <p>
              Where users opt in, SignGuy AI may send account, billing, support, onboarding, and service-notification texts.
            </p>
            <p className="mt-2 p-3 rounded-lg border border-slate-700 bg-slate-900/50 text-slate-200" data-testid="privacy-sms-statement">
              Mobile information, including phone numbers and SMS consent, is not shared with third parties or affiliates for marketing or promotional purposes. Information may be used only to provide requested services, customer support, transactional notifications, and communications related to the customer’s relationship with the applicable business.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">5. Consent Records</h2>
            <p>
              Where SMS consent is collected for SignGuy AI platform messaging, we retain records including consent timestamp, phone number, source, and disclosure version.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">6. Cookies and Analytics</h2>
            <p>
              We use essential browser/session storage and operational analytics to run and improve the service. We do not state that mobile data is sold or shared for promotional marketing.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">7. Data Security</h2>
            <p>
              We use reasonable technical and organizational safeguards such as encrypted transport, access controls, tenant isolation controls, and monitored infrastructure practices.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">8. Data Sharing</h2>
            <p>
              We may use service providers to process data on our behalf for hosting, messaging delivery, and billing infrastructure. We do not share mobile numbers and SMS consent for third-party marketing or promotional use.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">9. Data Changes and Deletion Requests</h2>
            <p>
              Users may request corrections, updates, or deletion where applicable by contacting us. We will review and respond according to applicable law and service constraints.
            </p>
            <p className="mt-2">
              You can also review our <Link to="/data-deletion" className="text-violet-400 hover:underline">Data Deletion Instructions</Link> page.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-3">10. Contact Information</h2>
            <p>Business Name: SignTists Lab</p>
            <p>Product: SignGuy AI</p>
            <p>Owner: Donnell Nicole Black</p>
            <p className="mt-2">Business Contact Email: <a href={`mailto:${SUPPORT_EMAIL}`} className="text-violet-400 hover:underline">{SUPPORT_EMAIL}</a></p>
            <p>Business Mailing Address: {MAILING_ADDRESS}</p>
          </section>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}
