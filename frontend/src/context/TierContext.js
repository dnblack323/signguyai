import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;
// Phase-launch feature flag: when true, every tenant is treated as Founders
// and all credit/feature gating is bypassed in the UI. Flip to "false" (or
// remove from .env) to bring back tier-based gating once Pro/Business/Starter
// re-launch.
const SHOW_FOUNDERS_ONLY = (process.env.REACT_APP_SHOW_FOUNDERS_ONLY || 'true').toLowerCase() === 'true';

const TierContext = createContext(null);

export const TierProvider = ({ children }) => {
  const { isAuthenticated, token } = useAuth();
  const [tierData, setTierData] = useState(null);
  const [usage, setUsage] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgradeModal, setUpgradeModal] = useState({ open: false, feature: null, data: null });

  // Fetch tier data when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchTierData();
      fetchUsage();
    } else {
      setTierData(null);
      setUsage([]);
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  const fetchTierData = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/tiers/my-plan`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTierData(response.data);
    } catch (error) {
      console.error('Failed to fetch tier data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsage = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/tiers/usage`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsage(response.data.usage || []);
    } catch (error) {
      console.error('Failed to fetch usage:', error);
    }
  };

  // Check if a feature is accessible
  const checkFeature = useCallback((category, feature) => {
    // Phase-launch override: everyone is on Founders → all features ON.
    if (SHOW_FOUNDERS_ONLY) return { allowed: true, status: 'on' };

    if (!tierData?.features) return { allowed: true, status: 'on' }; // Default allow if no tier data
    
    const categoryData = tierData.features[category];
    if (!categoryData) return { allowed: true, status: 'on' };
    
    const featureData = categoryData[feature];
    if (!featureData) return { allowed: true, status: 'on' };
    
    const status = featureData.status;
    
    if (status === 'off') {
      return { allowed: false, status: 'off', message: 'This feature requires an upgrade' };
    }
    
    if (status === 'limited') {
      const usageRecord = usage.find(u => u.feature === `${category}.${feature}`);
      const currentUsage = usageRecord?.current || featureData.current_usage || 0;
      const limit = featureData.limit || 0;
      const remaining = Math.max(0, limit - currentUsage);
      
      return {
        allowed: remaining > 0,
        status: 'limited',
        limit,
        currentUsage,
        remaining,
        message: remaining <= 0 ? `You've reached your limit of ${limit}` : null
      };
    }
    
    return { allowed: true, status: 'on' };
  }, [tierData, usage]);

  // Check feature and show upgrade modal if blocked
  const requireFeature = useCallback(async (category, feature) => {
    // Phase-launch override: skip the gate entirely.
    if (SHOW_FOUNDERS_ONLY) return true;

    const result = checkFeature(category, feature);
    
    if (!result.allowed) {
      // Fetch upgrade prompt data
      try {
        const response = await axios.get(
          `${API_URL}/api/tiers/upgrade-prompt/${category}/${feature}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setUpgradeModal({
          open: true,
          feature: `${category}.${feature}`,
          data: response.data
        });
      } catch (error) {
        console.error('Failed to fetch upgrade prompt:', error);
        setUpgradeModal({
          open: true,
          feature: `${category}.${feature}`,
          data: {
            message: 'This feature requires an upgrade',
            cta_text: 'Upgrade Now'
          }
        });
      }
      return false;
    }
    
    return true;
  }, [checkFeature, token]);

  // Use a limited feature (increment usage)
  const useFeature = useCallback(async (category, feature) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/tiers/use/${category}/${feature}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update local usage
      await fetchUsage();
      
      return { success: true, remaining: response.data.remaining };
    } catch (error) {
      if (error.response?.status === 403) {
        // Feature limit reached, show upgrade modal
        await requireFeature(category, feature);
        return { success: false, error: 'limit_reached' };
      }
      return { success: false, error: error.message };
    }
  }, [token, requireFeature]);

  const closeUpgradeModal = () => {
    setUpgradeModal({ open: false, feature: null, data: null });
  };

  const value = {
    tier: SHOW_FOUNDERS_ONLY ? 'founders_edition' : (tierData?.tier || 'starter'),
    tierDisplayName: SHOW_FOUNDERS_ONLY ? 'Founders Edition' : (tierData?.tier_display_name || 'Starter'),
    features: tierData?.features || {},
    usage,
    loading,
    showFoundersOnly: SHOW_FOUNDERS_ONLY,
    checkFeature,
    requireFeature,
    useFeature,
    upgradeModal,
    closeUpgradeModal,
    refreshTierData: fetchTierData,
    refreshUsage: fetchUsage
  };

  return (
    <TierContext.Provider value={value}>
      {children}
    </TierContext.Provider>
  );
};

export const useTier = () => {
  const context = useContext(TierContext);
  if (!context) {
    throw new Error('useTier must be used within a TierProvider');
  }
  return context;
};

// Hook for checking a specific feature
export const useFeatureGate = (category, feature) => {
  const { checkFeature, requireFeature } = useTier();
  
  const result = checkFeature(category, feature);
  
  return {
    ...result,
    require: () => requireFeature(category, feature)
  };
};

export default TierContext;
