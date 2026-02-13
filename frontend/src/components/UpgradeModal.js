import { useTier } from '../context/TierContext';
import { Button } from './ui/button';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter 
} from './ui/dialog';
import { Crown, Sparkles, Zap, X, Check, ArrowRight } from 'lucide-react';

// Tier colors and icons
const tierConfig = {
  starter: { color: 'slate', icon: Zap, gradient: 'from-slate-500 to-slate-600' },
  pro: { color: 'blue', icon: Sparkles, gradient: 'from-blue-500 to-blue-600' },
  business: { color: 'amber', icon: Crown, gradient: 'from-amber-500 to-amber-600' }
};

// Feature display names
const featureDisplayNames = {
  // AI Tools
  'ai_tools.image_generation': 'AI Image Generation',
  'ai_tools.monthly_generations': 'AI Generations',
  'ai_tools.save_to_job': 'Save AI Results to Jobs',
  
  // Core Modules
  'core_modules.kanban': 'Kanban Board',
  'core_modules.time_clock': 'Time Clock',
  'core_modules.payroll': 'Payroll',
  'core_modules.calendar': 'Calendar',
  'core_modules.financial_tracking': 'Financial Tracking',
  'core_modules.job_log': 'Job Activity Log',
  
  // Webstores
  'webstores.num_stores': 'Webstores',
  'webstores.business_stores': 'Business Stores',
  'webstores.creator_stores': 'Creator/Affiliate Stores',
  'webstores.branding_colors': 'Custom Brand Colors',
  'webstores.branding_banner': 'Custom Banners',
  'webstores.analytics_advanced': 'Advanced Analytics',
  'webstores.payout_tracking': 'Payout Tracking',
  'webstores.leaderboard': 'Leaderboard',
  
  // Customer Portal
  'customer_portal.messaging': 'Customer Messaging',
  'customer_portal.appointments': 'Appointments',
  'customer_portal.bnpl_options': 'Buy Now Pay Later',
  
  // Team
  'team.team_members': 'Team Members',
  'team.role_management': 'Role Management',
  'team.custom_roles': 'Custom Roles',
  'team.activity_logs': 'Activity Logs',
  
  // Pricing
  'pricing.cost_tracking': 'Cost Tracking',
  'pricing.profit_margin_display': 'Profit Margins',
  'pricing.ai_price_suggestions': 'AI Price Suggestions',
  'pricing.local_market_analysis': 'Market Analysis',
  
  // Analytics
  'analytics.category_breakdown': 'Category Breakdown',
  'analytics.profit_analysis': 'Profit Analysis',
  'analytics.export_reports': 'Export Reports',
  'analytics.custom_reports': 'Custom Reports',
  
  // B2B
  'b2b.b2b_access': 'B2B Features',
  'b2b.volume_discounts': 'Volume Discounts',
  'b2b.net_terms': 'Net Payment Terms',
  
  // Integrations
  'integrations.paypal': 'PayPal',
  'integrations.affirm': 'Affirm',
  'integrations.klarna': 'Klarna',
  'integrations.twilio': 'SMS Notifications',
  'integrations.quickbooks': 'QuickBooks',
  'integrations.zapier': 'Zapier',
};

export const UpgradeModal = () => {
  const { upgradeModal, closeUpgradeModal, tier } = useTier();
  const { open, feature, data } = upgradeModal;
  
  if (!open || !data) return null;
  
  const unlockTier = data.unlock_tier || 'pro';
  const config = tierConfig[unlockTier] || tierConfig.pro;
  const TierIcon = config.icon;
  
  const featureName = featureDisplayNames[feature] || feature?.split('.').pop()?.replace(/_/g, ' ');
  
  const handleUpgrade = () => {
    // For now, just close and show a message
    // In production, this would redirect to Stripe checkout
    closeUpgradeModal();
    // You could emit an event or navigate to a billing page here
  };
  
  return (
    <Dialog open={open} onOpenChange={closeUpgradeModal}>
      <DialogContent className="sm:max-w-md bg-[var(--card-bg)] border-[var(--border-color)]">
        <DialogHeader className="space-y-4">
          {/* Icon Badge */}
          <div className="mx-auto">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-lg`}>
              <TierIcon className="w-8 h-8 text-white" />
            </div>
          </div>
          
          <DialogTitle className="text-xl text-center text-[var(--text-primary)]">
            Unlock {featureName}
          </DialogTitle>
          
          <DialogDescription className="text-center text-[var(--text-secondary)]">
            {data.message || `Upgrade to ${data.unlock_tier_name} to access this feature.`}
          </DialogDescription>
        </DialogHeader>
        
        {/* Upgrade Card */}
        <div className="my-4 p-4 rounded-xl bg-gradient-to-br from-[var(--bg-primary)] to-[var(--bg-secondary)] border border-[var(--border-color)]">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TierIcon className={`w-5 h-5 text-${config.color}-500`} />
              <span className="font-semibold text-[var(--text-primary)]">
                {data.unlock_tier_name || 'Pro'} Plan
              </span>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-[var(--text-primary)]">
                ${data.unlock_price_monthly || 49}
              </span>
              <span className="text-[var(--text-secondary)] text-sm">/mo</span>
            </div>
          </div>
          
          {/* Features Preview */}
          <div className="space-y-2 mt-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
              <Check className="w-4 h-4 text-green-500" />
              <span>{featureName}</span>
            </div>
            {unlockTier === 'pro' && (
              <>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>100 AI generations/month</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>5 Team members</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>Advanced Analytics</span>
                </div>
              </>
            )}
            {unlockTier === 'business' && (
              <>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>Unlimited everything</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>B2B & Creator features</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <Check className="w-4 h-4 text-green-500" />
                  <span>All integrations</span>
                </div>
              </>
            )}
          </div>
        </div>
        
        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button
            variant="outline"
            onClick={closeUpgradeModal}
            className="flex-1 border-[var(--border-color)] text-[var(--text-secondary)]"
          >
            Maybe Later
          </Button>
          <Button
            onClick={handleUpgrade}
            className={`flex-1 bg-gradient-to-r ${config.gradient} hover:opacity-90 text-white`}
          >
            {data.cta_text || 'Upgrade Now'}
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </DialogFooter>
        
        {/* Yearly savings note */}
        {data.unlock_price_yearly && (
          <p className="text-center text-xs text-[var(--text-secondary)] mt-2">
            Save ${Math.round(data.unlock_price_monthly * 12 - data.unlock_price_yearly)} with yearly billing
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
};

// Component to wrap content that requires a feature
export const FeatureGate = ({ 
  category, 
  feature, 
  children, 
  fallback = null,
  showUpgradeButton = true 
}) => {
  const { checkFeature, requireFeature } = useTier();
  const result = checkFeature(category, feature);
  
  if (result.allowed) {
    return children;
  }
  
  if (fallback) {
    return fallback;
  }
  
  if (showUpgradeButton) {
    return (
      <FeatureLockedPlaceholder 
        category={category} 
        feature={feature} 
        onUpgrade={() => requireFeature(category, feature)}
      />
    );
  }
  
  return null;
};

// Placeholder shown when feature is locked
export const FeatureLockedPlaceholder = ({ category, feature, onUpgrade }) => {
  const featureName = featureDisplayNames[`${category}.${feature}`] || feature?.replace(/_/g, ' ');
  
  return (
    <div className="flex flex-col items-center justify-center p-8 rounded-xl bg-[var(--bg-secondary)] border border-dashed border-[var(--border-color)]">
      <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mb-4">
        <Sparkles className="w-6 h-6 text-blue-500" />
      </div>
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
        {featureName}
      </h3>
      <p className="text-sm text-[var(--text-secondary)] mb-4 text-center">
        Upgrade your plan to unlock this feature
      </p>
      <Button onClick={onUpgrade} size="sm" className="bg-blue-500 hover:bg-blue-600 text-white">
        <Sparkles className="w-4 h-4 mr-2" />
        Unlock Feature
      </Button>
    </div>
  );
};

// Badge showing current tier
export const TierBadge = ({ size = 'md' }) => {
  const { tier, tierDisplayName } = useTier();
  const config = tierConfig[tier] || tierConfig.starter;
  const TierIcon = config.icon;
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  };
  
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r ${config.gradient} text-white font-medium ${sizeClasses[size]}`}>
      <TierIcon className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />
      {tierDisplayName}
    </span>
  );
};

// Usage indicator for limited features
export const UsageIndicator = ({ category, feature, showLabel = true }) => {
  const { checkFeature } = useTier();
  const result = checkFeature(category, feature);
  
  if (result.status !== 'limited') return null;
  
  const percentage = result.limit > 0 ? (result.currentUsage / result.limit) * 100 : 0;
  const isLow = percentage >= 80;
  const isExhausted = percentage >= 100;
  
  return (
    <div className="space-y-1">
      {showLabel && (
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-secondary)]">
            {result.currentUsage} / {result.limit} used
          </span>
          <span className={isExhausted ? 'text-red-500' : isLow ? 'text-amber-500' : 'text-[var(--text-secondary)]'}>
            {result.remaining} remaining
          </span>
        </div>
      )}
      <div className="h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            isExhausted ? 'bg-red-500' : isLow ? 'bg-amber-500' : 'bg-blue-500'
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};

export default UpgradeModal;
