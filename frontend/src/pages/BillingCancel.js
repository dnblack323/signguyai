import { useNavigate } from 'react-router-dom';
import { XCircle, ArrowLeft, HelpCircle } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function BillingCancel() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 rounded-full bg-[var(--bg-secondary)] flex items-center justify-center mx-auto mb-6">
          <XCircle className="w-10 h-10 text-[var(--text-secondary)]" />
        </div>

        <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
          Payment Cancelled
        </h1>
        
        <p className="text-[var(--text-secondary)] mb-8">
          No worries! Your card was not charged. You can try again whenever you're ready.
        </p>

        <div className="space-y-3">
          <Button
            onClick={() => navigate('/pricing-plans')}
            className="w-full py-6 bg-gradient-to-r from-blue-500 to-indigo-600 hover:opacity-90 text-white text-base font-semibold"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Pricing
          </Button>

          <Button
            variant="outline"
            onClick={() => navigate('/')}
            className="w-full border-[var(--border-color)] text-[var(--text-secondary)]"
          >
            Return to Dashboard
          </Button>
        </div>

        {/* Help Section */}
        <div className="mt-8 p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
          <div className="flex items-start gap-3 text-left">
            <HelpCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)] mb-1">
                Have questions?
              </p>
              <p className="text-sm text-[var(--text-secondary)]">
                Not sure which plan is right for you? We're happy to help you decide.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
