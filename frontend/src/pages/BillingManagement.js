import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import {
  Crown, Sparkles, Shield, CreditCard, Check,
  ExternalLink, RefreshCw, AlertCircle, Loader2,
  Coins, Package, ArrowRight, Zap
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function BillingManagement() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, token } = useAuth();
  const [planData, setPlanData] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/billing' } });
      return;
    }
    const checkoutStatus = searchParams.get('checkout');
    const sessionId = searchParams.get('session_id');
    if (checkoutStatus === 'success' || sessionId) {
      navigate('/billing/success' + (sessionId ? `?session_id=${sessionId}` : ''), { replace: true });
      return;
    }
    if (checkoutStatus === 'cancel') {
      toast.info('Checkout was cancelled. Your plan has not changed.');
      navigate('/billing', { replace: true });
    }
    fetchPlanData();
    fetchPaymentHistory();
  }, [isAuthenticated]);

  const fetchPlanData = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/founders/plan`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPlanData(response.data);
    } catch (error) {
      console.error('Failed to fetch plan:', error);
      toast.error('Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };

  const fetchPaymentHistory = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/payment-history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPaymentHistory(response.data.transactions || []);
    } catch {}
  };

  const handleSubscribe = async (interval) => {
    setCheckoutLoading(interval);
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/founders/checkout`,
        { billing_interval: interval, origin_url: window.location.origin },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Checkout failed');
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleBuyCredits = async (packId) => {
    setCheckoutLoading(packId);
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/founders/purchase-credits`,
        { pack_id: packId, origin_url: window.location.origin },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Purchase failed');
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleManageStripe = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/portal`,
        { return_url: window.location.href },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = response.data.url;
    } catch {
      toast.error('Failed to open Stripe portal');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!planData) return null;

  const { plan, fees, credit_packs, spots, tenant_status, credit_balance } = planData;
  const isSubscribed = tenant_status?.is_subscribed;
  const isFounder = tenant_status?.is_founder;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6" data-testid="billing-page">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Billing & Subscription</h1>
        {isSubscribed && (
          <Button
            onClick={handleManageStripe}
            variant="outline"
            className="border-[#2F8BFB] text-[#2F8BFB] hover:bg-[#2F8BFB]/10"
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Manage in Stripe
          </Button>
        )}
      </div>

      {/* Founders Edition Plan Card */}
      <Card className="bg-[#111826] text-white border-[#1E293B] overflow-hidden">
        <div className="h-2 bg-gradient-to-r from-violet-500 to-purple-500"></div>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-violet-500/10">
                <Crown className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  {plan.plan_name}
                  {isFounder && (
                    <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                      <Crown className="w-3 h-3 mr-1" /> Founder
                    </Badge>
                  )}
                </CardTitle>
                <p className="text-sm text-gray-400">
                  {spots.spots_remaining} of {spots.total_spots} founder spots remaining
                </p>
              </div>
            </div>
            <Badge
              variant="outline"
              className={isSubscribed
                ? 'border-emerald-500/50 text-emerald-400'
                : 'border-yellow-500/50 text-yellow-400'
              }
            >
              {isSubscribed ? 'Active' : 'Not Subscribed'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Pricing */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Monthly</p>
              <p className="text-2xl font-bold text-white">
                ${plan.price_monthly}<span className="text-sm font-normal text-gray-400">/mo</span>
              </p>
              {isFounder && <p className="text-xs text-violet-400 mt-1">Lifetime rate locked</p>}
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Annual</p>
              <p className="text-2xl font-bold text-white">
                ${plan.price_annual}<span className="text-sm font-normal text-gray-400">/yr</span>
              </p>
              <p className="text-xs text-emerald-400 mt-1">Save ${plan.price_monthly * 12 - plan.price_annual}/yr</p>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Promo Code</p>
              <p className="text-lg font-bold text-violet-400">FOUNDERS</p>
              <p className="text-xs text-gray-400 mt-1">50% off at checkout</p>
            </div>
          </div>

          {/* Subscribe Buttons */}
          {!isSubscribed && (
            <div className="flex gap-3">
              <Button
                onClick={() => handleSubscribe('monthly')}
                disabled={checkoutLoading !== null}
                className="flex-1 bg-violet-500 hover:bg-violet-600 text-white font-medium"
                data-testid="subscribe-monthly-btn"
              >
                {checkoutLoading === 'monthly' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Crown className="h-4 w-4 mr-2" />}
                Subscribe Monthly - ${plan.price_monthly}/mo
              </Button>
              <Button
                onClick={() => handleSubscribe('annual')}
                disabled={checkoutLoading !== null}
                variant="outline"
                className="flex-1 border-violet-500/50 text-violet-400 hover:bg-violet-500/10"
                data-testid="subscribe-annual-btn"
              >
                {checkoutLoading === 'annual' ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
                Subscribe Annual - ${plan.price_annual}/yr
              </Button>
            </div>
          )}

          {/* What's Included */}
          <div className="bg-[#0B0F17] rounded-lg p-4">
            <h3 className="font-medium text-white mb-3 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400" />
              Everything Included
            </h3>
            <div className="grid md:grid-cols-2 gap-2 text-sm text-gray-300">
              {['Full Shop Management (CRM, Jobs, Invoices, Payroll)',
                'All AI Tools (28+ tools, Business Assistant, Voice)',
                'Customer & Employee Portals',
                'Unlimited Webstores (B2B, Fundraiser, Creator)',
                'Production Workflow & Timeline',
                'Document Library & Questionnaires',
                `${plan.ai_credits_monthly} AI Credits/month`,
                'Priority Support & Lifetime Pricing Lock',
              ].map((feature) => (
                <div key={feature} className="flex items-start gap-2">
                  <Check className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Processing Fees */}
          <div className="bg-[#0B0F17] rounded-lg p-4">
            <h3 className="font-medium text-white mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#2F8BFB]" />
              Processing Fees
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Platform Processing</span>
                <span className="text-white font-medium">{fees.platform_processing_percent}% + ${fees.platform_processing_fixed.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Webstore Additional Fee</span>
                <span className="text-white font-medium">{fees.webstore_additional_percent}%</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">{fees.note}</p>
          </div>
        </CardContent>
      </Card>

      {/* AI Credits */}
      <Card className="bg-[#111826] text-white border-[#1E293B]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Coins className="w-5 h-5 text-violet-400" />
            AI Credits
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Balance */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-[#0B0F17] rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Monthly Credits</p>
              <p className="text-2xl font-bold text-white">{credit_balance.monthly_credits}</p>
              <p className="text-xs text-gray-500">of {credit_balance.monthly_allowance} / resets monthly</p>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Purchased Credits</p>
              <p className="text-2xl font-bold text-emerald-400">{credit_balance.purchased_credits}</p>
              <p className="text-xs text-gray-500">never expire while active</p>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Total Available</p>
              <p className="text-2xl font-bold text-violet-400">{credit_balance.total_available}</p>
              <p className="text-xs text-gray-500">ready to use</p>
            </div>
          </div>

          {/* Credit Packs */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">Purchase Additional Credits</h3>
            <div className="grid md:grid-cols-3 gap-3">
              {credit_packs.map((pack) => (
                <div
                  key={pack.pack_id}
                  className="bg-[#0B0F17] rounded-lg p-4 border border-[#1E293B] hover:border-violet-500/30 transition"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Package className="w-4 h-4 text-violet-400" />
                    <span className="font-medium text-white">{pack.label}</span>
                  </div>
                  <p className="text-2xl font-bold text-white mb-1">${pack.price}</p>
                  <p className="text-xs text-gray-400 mb-3">{pack.description}</p>
                  <Button
                    onClick={() => handleBuyCredits(pack.pack_id)}
                    disabled={checkoutLoading !== null}
                    className="w-full bg-[#2F8BFB] hover:bg-[#1E7AF0] text-white"
                    size="sm"
                    data-testid={`buy-credits-${pack.pack_id}`}
                  >
                    {checkoutLoading === pack.pack_id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>Buy Now</>
                    )}
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Credit Info */}
          <div className="bg-[#0B0F17] rounded-lg p-4 text-sm text-gray-400 space-y-1">
            <p><Zap className="w-3 h-3 inline mr-1 text-violet-400" />Monthly credits ({credit_balance.monthly_allowance}/mo) reset each billing cycle and do not roll over.</p>
            <p><Zap className="w-3 h-3 inline mr-1 text-emerald-400" />Purchased credits never expire as long as your account is active.</p>
            <p><Zap className="w-3 h-3 inline mr-1 text-blue-400" />Credits are used first from monthly allowance, then from purchased balance.</p>
          </div>
        </CardContent>
      </Card>

      {/* Payment History */}
      <Card className="bg-[#111826] text-white border-[#1E293B]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-[#2F8BFB]" />
            Payment History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paymentHistory.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No payment history yet</p>
          ) : (
            <div className="space-y-3">
              {paymentHistory.slice(0, 10).map((payment) => (
                <div
                  key={payment.id}
                  className="flex items-center justify-between p-3 bg-[#0B0F17] rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${
                      payment.status === 'paid' ? 'bg-emerald-500/10' : 'bg-yellow-500/10'
                    }`}>
                      {payment.status === 'paid' ? (
                        <Check className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <RefreshCw className="w-4 h-4 text-yellow-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-white font-medium">
                        {payment.plan || 'Payment'}
                      </p>
                      <p className="text-sm text-gray-400">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p className="text-white font-medium">
                    ${payment.amount?.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
