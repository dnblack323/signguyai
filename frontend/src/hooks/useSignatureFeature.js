import { useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const useSignatureFeature = () => {
  const { tenant, fetchTenant } = useApp();

  useEffect(() => {
    if (!tenant) {
      fetchTenant();
    }
  }, [tenant, fetchTenant]);

  const signatureSettings = tenant?.signature_settings || {};

  return {
    loading: !tenant,
    enabled: !!signatureSettings.enabled,
    settings: signatureSettings,
  };
};