import { useState, useEffect } from 'react';
import { 
  Settings, X, CreditCard, Zap, Crown, Clock, Users, 
  Ticket, ChevronDown, ChevronUp, RefreshCw, Infinity,
  TestTube, Shield
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { cn } from '../lib/utils';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SUBSCRIPTION_MODES = [
  { id: 'founders_edition', name: 'Founders Edition', color: 'bg-amber-500', icon: Crown },
  { id: 'free_trial', name: '48hr Free Trial', color: 'bg-green-500', icon: Clock },
  { id: 'trial_expired', name: 'Trial Expired (Locked)', color: 'bg-red-500', icon: Clock },
  { id: 'os_pro', name: 'OS Pro', color: 'bg-blue-500', icon: Zap },
  { id: 'os_starter', name: 'OS Starter', color: 'bg-slate-500', icon: Users },
  { id: 'webstores_only', name: 'Webstores Only', color: 'bg-emerald-500', icon: CreditCard },
];

const CREDIT_PRESETS = [
  { credits: 999999, label: 'Unlimited', icon: Infinity },
  { credits: 150, label: '150 (Full Month)' },
  { credits: 50, label: '50 (Trial)' },
  { credits: 10, label: '10 (Low)' },
  { credits: 0, label: '0 (Empty)' },
];

export default function DevPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentMode, setCurrentMode] = useState('founders_edition');
  const [credits, setCredits] = useState(999999);
  const [loading, setLoading] = useState(false);
  const [tenantInfo, setTenantInfo] = useState(null);

  // Check if user is admin
  const [isAdmin, setIsAdmin] = useState(false);
  
  useEffect(() => {
    checkAdminStatus();
  }, []);

  const checkAdminStatus = async () => {
    try {
      const token = getAuthToken();
      if (!token) return;
      
      const res = await axios.get(`${API}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Check if admin or founder
      const isAdminUser = res.data.is_admin || res.data.is_founder || 
                          res.data.email === 'thesigntistslab@gmail.com';
      setIsAdmin(isAdminUser);
      
      if (isAdminUser) {
        fetchTenantInfo();
      }
    } catch (err) {
      console.error('Error checking admin status:', err);
    }
  };

  const fetchTenantInfo = async () => {
    try {
      const token = getAuthToken();
      const res = await axios.get(`${API}/billing/trial-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenantInfo(res.data);
      
      // Also get credits
      const creditsRes = await axios.get(`${API}/credits/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCredits(creditsRes.data.total_credits || 0);
    } catch (err) {
      console.error('Error fetching tenant info:', err);
    }
  };

  const updateSubscriptionMode = async (mode) => {
    setLoading(true);
    try {
      const token = getAuthToken();
      await axios.post(`${API}/dev/set-subscription-mode`, 
        { mode },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      setCurrentMode(mode);
      toast.success(`Switched to ${SUBSCRIPTION_MODES.find(m => m.id === mode)?.name}`);
      fetchTenantInfo();
    } catch (err) {
      toast.error('Failed to update subscription mode');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const updateCredits = async (amount) => {
    setLoading(true);
    try {
      const token = getAuthToken();
      await axios.post(`${API}/dev/set-credits`, 
        { credits: amount },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      setCredits(amount);
      toast.success(`Credits set to ${amount === 999999 ? 'Unlimited' : amount}`);
    } catch (err) {
      toast.error('Failed to update credits');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = async () => {
    setLoading(true);
    try {
      const token = getAuthToken();
      await axios.post(`${API}/dev/reset-to-admin`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentMode('founders_edition');
      setCredits(999999);
      toast.success('Reset to Admin defaults');
      fetchTenantInfo();
    } catch (err) {
      toast.error('Failed to reset');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Only show for admin users
  if (!isAdmin) return null;

  return (
    <div className="fixed bottom-6 left-6 z-50">
      {isOpen ? (
        <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-80 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b border-slate-700 bg-slate-800">
            <div className="flex items-center gap-2">
              <TestTube className="h-4 w-4 text-purple-400" />
              <span className="text-sm font-semibold text-white">Dev Panel</span>
              <Badge className="bg-purple-500/20 text-purple-300 text-xs">Admin</Badge>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="p-3 space-y-4 max-h-[70vh] overflow-y-auto">
            {/* Current Status */}
            <div className="p-2 bg-slate-800 rounded-lg">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Current Mode</span>
                <button onClick={fetchTenantInfo} className="hover:text-white">
                  <RefreshCw className="h-3 w-3" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  SUBSCRIPTION_MODES.find(m => m.id === currentMode)?.color || 'bg-gray-500'
                )} />
                <span className="text-white font-medium text-sm">
                  {SUBSCRIPTION_MODES.find(m => m.id === currentMode)?.name || currentMode}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Credits: {credits === 999999 ? '∞ Unlimited' : credits.toLocaleString()}
              </div>
            </div>

            {/* Subscription Mode Selection */}
            <div>
              <div 
                className="flex items-center justify-between cursor-pointer text-xs font-medium text-slate-400 uppercase tracking-wide mb-2"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                <span>Test Subscription Mode</span>
                {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </div>
              
              {isExpanded && (
                <div className="space-y-1">
                  {SUBSCRIPTION_MODES.map(({ id, name, color, icon: Icon }) => (
                    <button
                      key={id}
                      onClick={() => updateSubscriptionMode(id)}
                      disabled={loading}
                      className={cn(
                        "w-full flex items-center gap-2 px-3 py-2 rounded-md text-left transition-all text-sm",
                        currentMode === id 
                          ? "bg-purple-500/20 text-purple-300 ring-1 ring-purple-500/50" 
                          : "hover:bg-slate-800 text-slate-300"
                      )}
                    >
                      <div className={cn("w-2 h-2 rounded-full", color)} />
                      <Icon className="h-3 w-3" />
                      <span>{name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Credit Presets */}
            <div>
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wide">Set Credits</label>
              <div className="mt-2 grid grid-cols-2 gap-1">
                {CREDIT_PRESETS.map(({ credits: amt, label, icon: Icon }) => (
                  <button
                    key={amt}
                    onClick={() => updateCredits(amt)}
                    disabled={loading}
                    className={cn(
                      "flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-all",
                      credits === amt
                        ? "bg-purple-500 text-white"
                        : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                    )}
                  >
                    {Icon && <Icon className="h-3 w-3" />}
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="pt-2 border-t border-slate-700 space-y-1">
              <button
                onClick={() => window.location.href = '/promo-codes'}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left hover:bg-slate-800 text-sm text-slate-300"
              >
                <Ticket className="h-4 w-4 text-slate-400" />
                <span>Manage Promo Codes</span>
              </button>
              <button
                onClick={() => window.location.href = '/admin/payment-settings'}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left hover:bg-slate-800 text-sm text-slate-300"
              >
                <CreditCard className="h-4 w-4 text-slate-400" />
                <span>Payment Settings</span>
              </button>
              <button
                onClick={resetToDefaults}
                disabled={loading}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-left hover:bg-slate-800 text-sm text-amber-400"
              >
                <Shield className="h-4 w-4" />
                <span>Reset to Admin Defaults</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-full bg-purple-600 hover:bg-purple-500 text-white shadow-lg transition-all text-sm font-medium"
          data-testid="dev-panel-toggle"
        >
          <TestTube className="h-4 w-4" />
          <span>Dev Panel</span>
        </button>
      )}
    </div>
  );
}
