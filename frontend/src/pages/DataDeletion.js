import { Link } from 'react-router-dom';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import { Mail, Trash2, ShieldCheck, Settings } from 'lucide-react';

const LAST_UPDATED = 'April 25, 2026';

export default function DataDeletion() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      <PublicNav />

      <main className="flex-1 max-w-3xl mx-auto w-full px-6 py-16 space-y-12">

        {/* Header */}
        <header className="space-y-3">
          <div className="inline-flex items-center gap-2 text-xs font-medium text-teal-400 uppercase tracking-widest">
            <ShieldCheck className="h-4 w-4" />
            Privacy &amp; Data Rights
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold leading-tight">
            Data Deletion Instructions
          </h1>
          <p className="text-gray-400 text-sm">Last updated: {LAST_UPDATED}</p>
        </header>

        {/* Intro */}
        <section className="space-y-4 text-gray-300 leading-relaxed">
          <p>
            SignGuy AI OS respects user privacy and provides a clear process for users and
            business tenants to request deletion of account data and data connected to
            Facebook/Meta and other third-party integrations.
          </p>
          <p>
            If you connected a Facebook Business Page, Meta account, Gmail account, or any
            other third-party integration to SignGuy AI OS, you may request that we
            disconnect that integration and delete the associated stored data.
          </p>
        </section>

        {/* How to request */}
        <section className="space-y-5">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Mail className="h-5 w-5 text-teal-400" />
            How to Request Data Deletion
          </h2>
          <p className="text-gray-300 leading-relaxed">
            Send a deletion request by email to:
          </p>
          <a
            href="mailto:support@signguy-ai.com"
            className="inline-block bg-teal-500/10 border border-teal-500/30 text-teal-300 font-mono px-5 py-3 rounded-lg hover:bg-teal-500/20 transition-colors"
            data-testid="deletion-contact-email"
          >
            support@signguy-ai.com
          </a>

          <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-3">
            <p className="text-sm font-medium text-white">Please include in your request:</p>
            <ul className="space-y-2 text-gray-300 text-sm">
              {[
                'Your full name',
                'Business name',
                'Login email address used for SignGuy AI OS',
                'Connected Facebook Page name, if applicable',
                'The type of data you want deleted',
                'Any additional details needed to identify your account',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-teal-400 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* What we will do */}
        <section className="space-y-5">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Trash2 className="h-5 w-5 text-teal-400" />
            What Happens After You Request Deletion
          </h2>
          <p className="text-gray-300 leading-relaxed">
            After receiving a valid deletion request, we will:
          </p>
          <ul className="space-y-2 text-gray-300 text-sm">
            {[
              'Verify account or business ownership when necessary',
              'Disconnect the related third-party integration',
              'Delete stored integration tokens and access credentials',
              'Delete or anonymize stored integration data where legally and technically permitted',
              'Confirm completion by email once the request has been processed',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-teal-400 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* Examples */}
        <section className="space-y-5">
          <h2 className="text-xl font-semibold text-white">Examples of Data That May Be Deleted</h2>
          <ul className="space-y-2 text-gray-300 text-sm">
            {[
              'Connected Facebook Page integration records',
              'Stored Facebook Messenger message records',
              'Stored Gmail or third-party integration records',
              'OAuth tokens and connection records',
              'Imported customer messages connected to third-party integrations',
              'Account profile data, if full account deletion is requested',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-teal-400 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* Retained data */}
        <section className="space-y-5">
          <h2 className="text-xl font-semibold text-white">Data That May Be Retained</h2>
          <p className="text-gray-300 leading-relaxed">
            Some records may be retained when required for:
          </p>
          <ul className="space-y-2 text-gray-300 text-sm">
            {[
              'Billing records',
              'Security and access logs',
              'Fraud prevention',
              'Legal compliance obligations',
              'Completed business transactions',
              'Audit trails connected to invoices, payments, or production orders',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-gray-500 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* Self-service disconnect */}
        <section className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Settings className="h-5 w-5 text-teal-400" />
            Disconnect an Integration Without Deleting Your Account
          </h2>
          <p className="text-gray-300 text-sm leading-relaxed">
            To disconnect a third-party integration without requesting full data deletion,
            log in to your SignGuy AI OS account and navigate to:
          </p>
          <div className="inline-block bg-teal-500/10 border border-teal-500/30 text-teal-300 text-sm font-mono px-4 py-2 rounded-lg">
            Settings &gt; Integrations
          </div>
          <p className="text-gray-400 text-sm">
            From there you can disconnect any connected service at any time.
          </p>
        </section>

        {/* Contact */}
        <section className="border-t border-white/10 pt-10 space-y-3">
          <h2 className="text-lg font-semibold text-white">Contact Us</h2>
          <p className="text-gray-300 text-sm">For questions about this policy or to submit a data request:</p>
          <a
            href="mailto:support@signguy-ai.com"
            className="text-teal-400 hover:text-teal-300 transition-colors text-sm font-medium"
          >
            support@signguy-ai.com
          </a>
          <p className="text-gray-500 text-xs pt-2">Last updated: {LAST_UPDATED}</p>
        </section>

      </main>

      <PublicFooter />
    </div>
  );
}
