import { PublicNav, PublicFooter } from '../components/PublicNav';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />
      
      <div className="max-w-4xl mx-auto px-4 py-20">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-gray-400 mb-8">Last updated: March 2026</p>
        
        <div className="prose prose-invert max-w-none space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">1. Introduction</h2>
            <p className="text-gray-300 leading-relaxed">
              SignGuy AI ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy 
              explains how we collect, use, disclose, and safeguard your information when you use our Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-medium text-white mt-4 mb-2">2.1 Information You Provide</h3>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Account information (name, email, password)</li>
              <li>Business information (company name, address, phone)</li>
              <li>Customer data you input into the Service</li>
              <li>Payment information (processed by Stripe)</li>
              <li>Communications with us</li>
            </ul>

            <h3 className="text-xl font-medium text-white mt-4 mb-2">2.2 Information Collected Automatically</h3>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Usage data (features used, pages visited)</li>
              <li>Device information (browser type, operating system)</li>
              <li>IP address and location data</li>
              <li>Cookies and similar tracking technologies</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">3. How We Use Your Information</h2>
            <p className="text-gray-300 leading-relaxed mb-3">We use collected information to:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Provide and maintain the Service</li>
              <li>Process payments and subscriptions</li>
              <li>Send transactional emails (invoices, notifications)</li>
              <li>Improve and personalize the Service</li>
              <li>Provide customer support</li>
              <li>Detect and prevent fraud</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">4. AI Features and Data Processing</h2>
            <div className="text-gray-300 leading-relaxed space-y-3">
              <p>
                Our AI features process data you provide to generate content, suggestions, and insights. 
                This processing includes:
              </p>
              <ul className="list-disc list-inside space-y-1">
                <li>Text content generation for emails, descriptions, and marketing</li>
                <li>Image generation for mockups and designs</li>
                <li>Business analytics and recommendations</li>
              </ul>
              <p>
                AI-generated content is created based on your inputs and is stored in your account. 
                We do not use your business data to train AI models for other customers.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">5. Data Sharing and Disclosure</h2>
            <p className="text-gray-300 leading-relaxed mb-3">We may share your information with:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li><strong>Service Providers:</strong> Stripe for payments, SendGrid for emails, cloud hosting providers</li>
              <li><strong>AI Providers:</strong> For processing AI features (data is not retained by providers)</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
              <li><strong>Business Transfers:</strong> In connection with a merger or acquisition</li>
            </ul>
            <p className="text-gray-300 leading-relaxed mt-3">
              We do not sell your personal information to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">6. Data Security</h2>
            <p className="text-gray-300 leading-relaxed">
              We implement appropriate technical and organizational measures to protect your data, including:
            </p>
            <ul className="list-disc list-inside text-gray-300 mt-2 space-y-1">
              <li>Encryption of data in transit (HTTPS/TLS)</li>
              <li>Secure password hashing</li>
              <li>Access controls and authentication</li>
              <li>Regular security assessments</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">7. Data Retention</h2>
            <p className="text-gray-300 leading-relaxed">
              We retain your data for as long as your account is active or as needed to provide the Service. 
              After account deletion, we may retain certain data as required by law or for legitimate 
              business purposes (e.g., resolving disputes, enforcing agreements).
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">8. Your Rights</h2>
            <p className="text-gray-300 leading-relaxed mb-3">Depending on your location, you may have the right to:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Access your personal data</li>
              <li>Correct inaccurate data</li>
              <li>Delete your data</li>
              <li>Export your data</li>
              <li>Opt out of marketing communications</li>
              <li>Restrict or object to processing</li>
            </ul>
            <p className="text-gray-300 leading-relaxed mt-3">
              To exercise these rights, contact us at privacy@signguy.ai.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">9. Cookies</h2>
            <p className="text-gray-300 leading-relaxed">
              We use cookies and similar technologies to maintain sessions, remember preferences, 
              and analyze usage. You can control cookies through your browser settings, but some 
              features may not function properly without them.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">10. Children's Privacy</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service is not intended for users under 18 years of age. We do not knowingly 
              collect information from children. If you believe we have collected data from a minor, 
              please contact us immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">11. International Data Transfers</h2>
            <p className="text-gray-300 leading-relaxed">
              Your data may be transferred to and processed in countries other than your own. 
              We ensure appropriate safeguards are in place for such transfers in compliance 
              with applicable data protection laws.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">12. Changes to This Policy</h2>
            <p className="text-gray-300 leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of significant 
              changes by email or through the Service. Your continued use after changes constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">13. Contact Us</h2>
            <p className="text-gray-300 leading-relaxed">
              For privacy-related questions or requests, contact us at:
            </p>
            <div className="mt-2 text-gray-300">
              <p>Email: privacy@signguy.ai</p>
              <p>Support: support@signguy.ai</p>
            </div>
          </section>
        </div>
      </div>
      
      <PublicFooter />
    </div>
  );
}
