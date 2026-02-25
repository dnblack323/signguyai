/**
 * Upgrade Prompt Components
 * 
 * Components for prompting users to upgrade when they hit feature limits
 * or try to access features not in their plan.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Sparkles, ArrowRight, Crown, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { usePlan } from '../contexts/PlanContext';

/**
 * Full-page upgrade prompt for locked features
 */
export const UpgradePromptPage = ({ 
  feature, 
  featureDescription, 
  suggestedPlan = 'Pro',
  benefits = []
}) => {
  const navigate = useNavigate();
  const { planDisplayName, isFounder } = usePlan();

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <Card className="max-w-lg w-full text-center border-2 border-dashed border-gray-300">
        <CardHeader>
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl">Upgrade to Unlock {feature}</CardTitle>
          <CardDescription className="text-base mt-2">
            {featureDescription}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-2">
              Your current plan: <span className="font-semibold">{planDisplayName}</span>
              {isFounder() && <Crown className="w-4 h-4 inline ml-1 text-amber-500" />}
            </p>
            <p className="text-sm text-gray-600">
              Required plan: <span className="font-semibold text-purple-600">{suggestedPlan} or higher</span>
            </p>
          </div>

          {benefits.length > 0 && (
            <div className="text-left">
              <p className="text-sm font-medium text-gray-700 mb-2">With {suggestedPlan}, you'll also get:</p>
              <ul className="space-y-2">
                {benefits.map((benefit, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                    <Sparkles className="w-4 h-4 text-purple-500" />
                    {benefit}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex flex-col gap-3">
            <Button 
              onClick={() => navigate('/pricing-plans')}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              View Upgrade Options
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button 
              variant="ghost"
              onClick={() => navigate(-1)}
            >
              Go Back
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

/**
 * Inline upgrade banner for within pages
 */
export const UpgradeBanner = ({ 
  feature, 
  message, 
  compact = false 
}) => {
  const navigate = useNavigate();

  if (compact) {
    return (
      <div className="flex items-center justify-between bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-600" />
          <span className="text-sm text-gray-700">{message}</span>
        </div>
        <Button 
          size="sm" 
          variant="outline"
          onClick={() => navigate('/pricing-plans')}
          className="text-purple-600 border-purple-300 hover:bg-purple-50"
        >
          Upgrade
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
          <Lock className="w-5 h-5 text-purple-600" />
        </div>
        <div className="flex-1">
          <p className="font-medium text-gray-900">{feature} is a premium feature</p>
          <p className="text-sm text-gray-600 mt-1">{message}</p>
        </div>
        <Button 
          onClick={() => navigate('/pricing-plans')}
          className="bg-purple-600 hover:bg-purple-700"
        >
          Upgrade Now
        </Button>
      </div>
    </div>
  );
};

/**
 * Usage limit indicator with upgrade prompt
 */
export const UsageLimitIndicator = ({ 
  feature, 
  used, 
  limit, 
  period = 'this month' 
}) => {
  const navigate = useNavigate();
  const percentage = limit ? Math.min((used / limit) * 100, 100) : 0;
  const isAtLimit = used >= limit;
  const isNearLimit = percentage >= 80;

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{feature}</span>
        <span className={`text-sm font-medium ${isAtLimit ? 'text-red-600' : isNearLimit ? 'text-amber-600' : 'text-gray-600'}`}>
          {used} / {limit === Infinity ? '∞' : limit}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all ${
            isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-amber-500' : 'bg-green-500'
          }`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      {isAtLimit && (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm text-red-600">Limit reached {period}</span>
          <Button 
            size="sm" 
            onClick={() => navigate('/pricing-plans')}
            className="bg-purple-600 hover:bg-purple-700"
          >
            Upgrade for More
          </Button>
        </div>
      )}
      {isNearLimit && !isAtLimit && (
        <p className="text-xs text-amber-600 mt-2">
          You're approaching your limit. Consider upgrading for more.
        </p>
      )}
    </div>
  );
};

/**
 * Feature-gated wrapper component
 * Renders children if feature is available, otherwise shows upgrade prompt
 */
export const FeatureGate = ({ 
  category, 
  feature, 
  children, 
  fallback,
  showUpgradePrompt = true 
}) => {
  const { hasFeature, loading } = usePlan();

  if (loading) {
    return <div className="animate-pulse bg-gray-100 rounded-lg h-32" />;
  }

  if (hasFeature(category, feature)) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (showUpgradePrompt) {
    return (
      <UpgradeBanner 
        feature={feature.replace(/_/g, ' ')}
        message="Upgrade your plan to access this feature."
        compact
      />
    );
  }

  return null;
};

export default FeatureGate;
