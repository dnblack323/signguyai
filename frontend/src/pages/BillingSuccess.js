import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useAuth } from '../context/AuthContext';
import { useTier } from '../context/TierContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function BillingSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const { refreshTierData } = useTier();
  const [status, setStatus] = useState('checking'); // checking, success, error
  const [paymentInfo, setPaymentInfo] = useState(null);

  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (sessionId && token) {
      pollPaymentStatus();
    }
  }, [sessionId, token]);

  const pollPaymentStatus = async (attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus('error');
      return;
    }

    try {
      const response = await axios.get(
        `${API_URL}/api/billing/checkout/status/${sessionId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.payment_status === 'paid') {
        setStatus('success');
        setPaymentInfo(response.data);
        // Refresh tier data to update the app state
        if (refreshTierData) {
          await refreshTierData();
        }
        return;
      }

      if (response.data.status === 'expired') {
        setStatus('error');
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
    } catch (error) {
      console.error('Error checking payment:', error);
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
      } else {
        setStatus('error');
      }
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {status === 'checking' && (
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
            </div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
              Processing Payment...
            </h1>
            <p className="text-[var(--text-secondary)]">
              Please wait while we confirm your payment.
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            {/* Success Animation */}
            <div className="relative w-24 h-24 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full bg-green-500/20 animate-ping" />
              <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <CheckCircle className="w-12 h-12 text-white" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
              Welcome, Founder! 🎉
            </h1>
            
            <p className="text-lg text-[var(--text-secondary)] mb-6">
              Your payment was successful. You now have full access to all features.
            </p>

            {paymentInfo && (
              <div className="bg-[var(--card-bg)] rounded-xl p-4 mb-6 border border-[var(--border-color)]">
                <div className="flex justify-between items-center">
                  <span className="text-[var(--text-secondary)]">Amount Paid</span>
                  <span className="text-xl font-bold text-[var(--text-primary)]">
                    ${paymentInfo.amount} {paymentInfo.currency?.toUpperCase()}
                  </span>
                </div>
              </div>
            )}

            {/* Founder Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/30 mb-8">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-semibold text-amber-500">
                Founder Member Pricing Locked In Forever
              </span>
            </div>

            <Button
              onClick={() => navigate('/')}
              className="w-full py-6 bg-gradient-to-r from-blue-500 to-indigo-600 hover:opacity-90 text-white text-base font-semibold"
            >
              Go to Dashboard
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">😕</span>
            </div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-2">
              Something Went Wrong
            </h1>
            <p className="text-[var(--text-secondary)] mb-6">
              We couldn't verify your payment. If you were charged, please contact support.
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => navigate('/pricing-plans')}
                className="flex-1"
              >
                Try Again
              </Button>
              <Button
                onClick={() => navigate('/')}
                className="flex-1"
              >
                Go Home
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
