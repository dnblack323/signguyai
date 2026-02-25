/**
 * Plan Context Provider
 * 
 * Provides plan information and feature gating to the entire app.
 * Controls UI visibility based on the user's subscription plan and product line.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const PlanContext = createContext();

export const usePlan = () => {
  const context = useContext(PlanContext);
  if (!context) {
    throw new Error('usePlan must be used within a PlanProvider');
  }
  return context;
};

export const PlanProvider = ({ children }) => {
  const [planInfo, setPlanInfo] = useState(null);
  const [features, setFeatures] = useState(null);
  const [uiVisibility, setUiVisibility] = useState({
    show_jobs_ui: true,
    show_payroll_ui: true,
    show_time_clock_ui: true,
    show_financials_ui: true,
    show_ai_assistant_ui: true,
    product_line: 'os',
    plan_type: 'os_starter',
    display_name: 'Starter',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  const fetchPlanInfo = useCallback(async (token) => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch plan info and UI visibility in parallel
      const [planResponse, visibilityResponse, featuresResponse] = await Promise.all([
        fetch(`${API_URL}/api/plans/my-plan`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/plans/my-ui-visibility`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/plans/my-features`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (planResponse.ok) {
        const planData = await planResponse.json();
        setPlanInfo(planData);
      }

      if (visibilityResponse.ok) {
        const visibilityData = await visibilityResponse.json();
        setUiVisibility(visibilityData);
      }

      if (featuresResponse.ok) {
        const featuresData = await featuresResponse.json();
        setFeatures(featuresData);
      }
    } catch (err) {
      console.error('Error fetching plan info:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  // Check if a specific feature is available
  const hasFeature = useCallback((category, feature) => {
    if (!features?.features) return false;
    const categoryFeatures = features.features[category];
    if (!categoryFeatures) return false;
    const featureValue = categoryFeatures[feature];
    if (!featureValue) return false;
    return featureValue.status === 'on' || featureValue.status === 'limited';
  }, [features]);

  // Check if a feature has remaining usage
  const getFeatureRemaining = useCallback((category, feature) => {
    if (!features?.features) return null;
    const categoryFeatures = features.features[category];
    if (!categoryFeatures) return null;
    const featureValue = categoryFeatures[feature];
    if (!featureValue) return null;
    if (featureValue.status === 'on') return Infinity;
    if (featureValue.status === 'limited') {
      return featureValue.remaining ?? (featureValue.limit - (featureValue.current_usage || 0));
    }
    return 0;
  }, [features]);

  // Get feature limit
  const getFeatureLimit = useCallback((category, feature) => {
    if (!features?.features) return null;
    const categoryFeatures = features.features[category];
    if (!categoryFeatures) return null;
    const featureValue = categoryFeatures[feature];
    if (!featureValue) return null;
    if (featureValue.status === 'on') return Infinity;
    return featureValue.limit;
  }, [features]);

  // UI visibility helpers
  const shouldShowJobs = () => uiVisibility.show_jobs_ui;
  const shouldShowPayroll = () => uiVisibility.show_payroll_ui;
  const shouldShowTimeClock = () => uiVisibility.show_time_clock_ui;
  const shouldShowFinancials = () => uiVisibility.show_financials_ui;
  const shouldShowAIAssistant = () => uiVisibility.show_ai_assistant_ui;

  // Product line checks
  const isOSPlan = () => uiVisibility.product_line === 'os';
  const isWebstorePlan = () => uiVisibility.product_line === 'webstores';
  const isAIStudioPlan = () => uiVisibility.product_line === 'ai_studio';

  // Processing fees
  const getInvoiceFeePercent = () => planInfo?.processing_fees?.invoice_fee_percent ?? 0;
  const getWebstoreFeePercent = () => planInfo?.processing_fees?.webstore_fee_percent ?? 0;
  const hasOnlinePayments = () => planInfo?.processing_fees?.online_payments_enabled ?? false;
  const hasStripeConnect = () => planInfo?.processing_fees?.stripe_connect_enabled ?? false;

  // Founder status
  const isFounder = () => planInfo?.is_founder ?? false;
  const getFounderNumber = () => planInfo?.subscription?.founder_number ?? null;

  const value = {
    // Raw data
    planInfo,
    features,
    uiVisibility,
    loading,
    error,

    // Actions
    fetchPlanInfo,
    
    // Feature checks
    hasFeature,
    getFeatureRemaining,
    getFeatureLimit,

    // UI visibility
    shouldShowJobs,
    shouldShowPayroll,
    shouldShowTimeClock,
    shouldShowFinancials,
    shouldShowAIAssistant,

    // Product line
    isOSPlan,
    isWebstorePlan,
    isAIStudioPlan,
    productLine: uiVisibility.product_line,
    planType: uiVisibility.plan_type,
    planDisplayName: uiVisibility.display_name,

    // Processing fees
    getInvoiceFeePercent,
    getWebstoreFeePercent,
    hasOnlinePayments,
    hasStripeConnect,

    // Founder
    isFounder,
    getFounderNumber,
  };

  return (
    <PlanContext.Provider value={value}>
      {children}
    </PlanContext.Provider>
  );
};

export default PlanContext;
