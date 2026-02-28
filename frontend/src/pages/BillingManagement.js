import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Crown, Sparkles, Zap, Check, ArrowRight, Shield, 
  Building2, Store, Cpu, CreditCard, Calendar, 
  ChevronRight, AlertCircle, RefreshCw, ExternalLink
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Product line configurations
const productLineConfig = {
  os: {
    name: 'SignGuy AI OS',
    icon: Building2,
    gradient: 'from-blue-500 to-indigo-600',
    color: 'blue',
  },
  webstores: {
    name: 'SignGuy Webstores',
    icon: Store,
    gradient: 'from-emerald-500 to-teal-600',
    color: 'emerald',
  },
  ai_studio: {
    name: 'SignGuy AI Studio',
    icon: Cpu,
    gradient: 'from-purple-500 to-pink-600',
    color: 'purple',
  },
};

const planIconMap = {
  os_starter: Zap,
  os_pro: Sparkles,
  os_business: Crown,
  ws_launch: Zap,
  ws_growth: Sparkles,
  ws_scale: Crown,
  ai_basic: Zap,
  ai_pro: Sparkles,
  ai_max: Crown,
};

export default function BillingManagement() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancelLoading, setCancelLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/billing' } });
      return;
    }
    fetchSubscription();
    fetchPaymentHistory();
  }, [isAuthenticated]);

  const fetchSubscription = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/billing/subscription/v2`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSubscription(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
      toast.error('Failed to load subscription data');
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
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await axios.post(
        `${API_URL}/api/billing/portal`,
        { return_url: window.location.href },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      window.location.href = response.data.url;
    } catch (error) {
      console.error('Portal error:', error);
      toast.error('Failed to open billing portal');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="p-6">
        <Card className="bg-[#111826] text-white border-[#1E293B]">
          <CardContent className="p-8 text-center">
            <AlertCircle className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">No Active Subscription</h2>
            <p className="text-gray-400 mb-6">Choose a plan to get started with SignGuy AI</p>
            <Link to="/pricing-plans">
              <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0]">
                View Plans <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const productConfig = productLineConfig[subscription.product_line] || productLineConfig.os;
  const ProductIcon = productConfig.icon;
  const PlanIcon = planIconMap[subscription.plan_type] || Zap;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Billing & Subscription</h1>
        <Button 
          onClick={handleManageSubscription}
          variant="outline"
          className="border-[#2F8BFB] text-[#2F8BFB] hover:bg-[#2F8BFB]/10"
        >
          <ExternalLink className="w-4 h-4 mr-2" />
          Manage in Stripe
        </Button>
      </div>

      {/* Current Plan Card */}
      <Card className="bg-[#111826] text-white border-[#1E293B] overflow-hidden">
        <div className={`h-2 bg-gradient-to-r ${productConfig.gradient}`}></div>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl bg-${productConfig.color}-500/10`}>
                <ProductIcon className={`w-6 h-6 text-${productConfig.color}-400`} />
              </div>
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  {subscription.plan_display_name}
                  {subscription.is_founder && (
                    <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                      <Crown className="w-3 h-3 mr-1" /> Founder #{subscription.founder_number || ''}
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>{subscription.product_line_display}</CardDescription>
              </div>
            </div>
            <Badge 
              variant="outline" 
              className={subscription.status === 'active' 
                ? 'border-emerald-500/50 text-emerald-400' 
                : 'border-yellow-500/50 text-yellow-400'
              }
            >
              {subscription.status === 'active' ? 'Active' : subscription.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Pricing Info */}
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Current Rate</p>
              <p className="text-2xl font-bold text-white">
                ${subscription.is_founder 
                  ? subscription.pricing?.founder_monthly 
                  : subscription.pricing?.monthly}
                <span className="text-sm font-normal text-gray-400">/mo</span>
              </p>
              {subscription.is_founder && (
                <p className="text-xs text-amber-400 mt-1">Founder rate locked in</p>
              )}
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Billing Cycle</p>
              <p className="text-lg font-semibold text-white capitalize">
                {subscription.billing_interval}
              </p>
            </div>
            <div className="bg-[#0B0F17] rounded-lg p-4">
              <p className="text-sm text-gray-400 mb-1">Next Billing Date</p>
              <p className="text-lg font-semibold text-white">
                {subscription.current_period_end 
                  ? new Date(subscription.current_period_end).toLocaleDateString()
                  : 'N/A'}
              </p>
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
                <span className="text-gray-400">Invoice Payments</span>
                <span className="text-white font-medium">
                  {subscription.processing_fees?.invoice === 0 
                    ? 'Not Available' 
                    : `${subscription.processing_fees?.invoice}%`}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Webstore Sales</span>
                <span className="text-white font-medium">
                  {subscription.processing_fees?.webstore === 0 
                    ? 'Not Available' 
                    : `${subscription.processing_fees?.webstore}%`}
                </span>
              </div>
            </div>
          </div>

          {/* Upgrade Options */}
          {subscription.upgrade_options && subscription.upgrade_options.length > 0 && (
            <div>
              <h3 className="font-medium text-white mb-3">Upgrade Options</h3>
              <div className="flex flex-wrap gap-3">
                {subscription.upgrade_options.map(option => (
                  <Link 
                    key={option.plan_type}
                    to={`/pricing-plans`}
                    className="flex items-center gap-2 px-4 py-2 bg-[#0B0F17] rounded-lg hover:bg-[#1a2235] transition"
                  >
                    <span className="text-gray-300">{option.display_name}</span>
                    <span className="text-gray-500">•</span>
                    <span className="text-[#2F8BFB]">${option.monthly_price}/mo</span>
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  </Link>
                ))}
              </div>
            </div>
          )}
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
              {paymentHistory.slice(0, 5).map((payment) => (
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
                        {payment.plan || 'Subscription Payment'}
                      </p>
                      <p className="text-sm text-gray-400">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-medium">
                      ${payment.amount?.toFixed(2)} {payment.currency?.toUpperCase()}
                    </p>
                    {payment.is_founder && (
                      <Badge className="bg-amber-500/20 text-amber-400 text-xs">
                        Founder
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid md:grid-cols-2 gap-4">
        <Link to="/pricing-plans">
          <Card className="bg-[#111826] text-white border-[#1E293B] hover:border-[#2F8BFB]/50 transition cursor-pointer">
            <CardContent className="p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#2F8BFB]/10 rounded-lg">
                  <ArrowRight className="w-5 h-5 text-[#2F8BFB]" />
                </div>
                <div>
                  <p className="text-white font-medium">Compare Plans</p>
                  <p className="text-sm text-gray-400">See all available options</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500" />
            </CardContent>
          </Card>
        </Link>
        <Link to="/settings">
          <Card className="bg-[#111826] text-white border-[#1E293B] hover:border-[#2F8BFB]/50 transition cursor-pointer">
            <CardContent className="p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#2F8BFB]/10 rounded-lg">
                  <Calendar className="w-5 h-5 text-[#2F8BFB]" />
                </div>
                <div>
                  <p className="text-white font-medium">Account Settings</p>
                  <p className="text-sm text-gray-400">Manage your account</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500" />
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
