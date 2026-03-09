import { PublicNav, PublicFooter } from '../components/PublicNav';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />
      
      <div className="max-w-4xl mx-auto px-4 py-20">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-400 mb-8">Last updated: March 2026</p>
        
        <div className="prose prose-invert max-w-none space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">1. Agreement to Terms</h2>
            <p className="text-gray-300 leading-relaxed">
              By accessing or using SignGuy AI ("the Service"), you agree to be bound by these Terms of Service. 
              If you disagree with any part of these terms, you may not access the Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">2. Description of Service</h2>
            <p className="text-gray-300 leading-relaxed">
              SignGuy AI is a cloud-based business management platform designed for sign shops. The Service includes:
            </p>
            <ul className="list-disc list-inside text-gray-300 mt-2 space-y-1">
              <li>Customer relationship management</li>
              <li>Job and quote management</li>
              <li>Invoicing and payment processing</li>
              <li>Employee time tracking and payroll</li>
              <li>E-commerce webstores</li>
              <li>AI-powered tools and content generation</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">3. Account Registration</h2>
            <p className="text-gray-300 leading-relaxed">
              To use the Service, you must create an account and provide accurate, complete information. 
              You are responsible for maintaining the security of your account credentials and for all 
              activities that occur under your account.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">4. Subscription and Billing</h2>
            <div className="text-gray-300 leading-relaxed space-y-3">
              <p><strong className="text-white">4.1 Founders Edition:</strong> The Founders Edition subscription is $99 per month or $1,188 per year. The FOUNDERS promo code provides 50% off the first annual payment for the first 100 customers.</p>
              <p><strong className="text-white">4.2 AI Credits:</strong> Each subscription includes 150 AI credits per month. Monthly credits expire on your billing date and do not roll over. Additional credit packs may be purchased and do not expire during an active subscription.</p>
              <p><strong className="text-white">4.3 Payment:</strong> All payments are processed through Stripe. By subscribing, you authorize us to charge your payment method on a recurring basis.</p>
              <p><strong className="text-white">4.4 Cancellation:</strong> You may cancel your subscription at any time. Access continues until the end of the current billing period.</p>
              <p><strong className="text-white">4.5 Refunds:</strong> Subscription fees are non-refundable except as required by law.</p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">5. Platform Fees</h2>
            <div className="text-gray-300 leading-relaxed space-y-3">
              <p><strong className="text-white">5.1 Processing Fee:</strong> A platform processing fee of 2.2% + $0.20 applies to payments processed through the Service.</p>
              <p><strong className="text-white">5.2 Webstore Fee:</strong> An additional 2.0% fee applies to sales made through webstores.</p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">6. Acceptable Use</h2>
            <p className="text-gray-300 leading-relaxed mb-3">You agree not to:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-1">
              <li>Use the Service for any illegal purpose</li>
              <li>Violate any laws in your jurisdiction</li>
              <li>Infringe on intellectual property rights</li>
              <li>Transmit malware or harmful code</li>
              <li>Attempt to gain unauthorized access to the Service</li>
              <li>Use automated systems to abuse the AI features</li>
              <li>Resell or redistribute the Service without authorization</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">7. Intellectual Property</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service and its original content, features, and functionality are owned by SignGuy AI 
              and are protected by copyright, trademark, and other intellectual property laws. 
              You retain ownership of content you create using the Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">8. Data and Privacy</h2>
            <p className="text-gray-300 leading-relaxed">
              Your use of the Service is also governed by our Privacy Policy. By using the Service, 
              you consent to our collection and use of data as described in the Privacy Policy.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">9. Third-Party Services</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service integrates with third-party services including Stripe for payments and 
              AI providers for content generation. Your use of these services is subject to their 
              respective terms and policies.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">10. Limitation of Liability</h2>
            <p className="text-gray-300 leading-relaxed">
              To the maximum extent permitted by law, SignGuy AI shall not be liable for any indirect, 
              incidental, special, consequential, or punitive damages, including loss of profits, data, 
              or business opportunities arising from your use of the Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">11. Disclaimer of Warranties</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service is provided "as is" without warranties of any kind, either express or implied. 
              We do not guarantee that the Service will be uninterrupted, secure, or error-free.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">12. Termination</h2>
            <p className="text-gray-300 leading-relaxed">
              We reserve the right to suspend or terminate your account at any time for violation of 
              these Terms. Upon termination, your right to use the Service ceases immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">13. Changes to Terms</h2>
            <p className="text-gray-300 leading-relaxed">
              We may update these Terms from time to time. We will notify you of significant changes 
              by email or through the Service. Continued use after changes constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">14. Contact</h2>
            <p className="text-gray-300 leading-relaxed">
              For questions about these Terms, please contact us at support@signguy.ai.
            </p>
          </section>
        </div>
      </div>
      
      <PublicFooter />
    </div>
  );
}
