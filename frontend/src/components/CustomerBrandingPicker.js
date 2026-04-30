/**
 * CustomerBrandingPicker
 * ----------------------
 * A small dropdown that lets an AI tool optionally attach to a customer's
 * Branding Profile. When a customer is picked, fetches the profile and
 * exposes both `customerId` and `profile` to the parent via `onChange`.
 *
 * Used on Idea Brainstormer, Logo Creator, Branding Kit Generator.
 */

import { useEffect, useState, useCallback } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { User, Wand2 } from 'lucide-react';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const headers = () => ({ Authorization: `Bearer ${getAuthToken()}` });

export default function CustomerBrandingPicker({ value, onChange, onPrefill }) {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);

  // Load customer list once
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await axios.get(`${API}/customers`, { headers: headers() });
        if (cancelled) return;
        const list = Array.isArray(r.data) ? r.data : (r.data?.items || []);
        setCustomers(list);
      } catch {
        // silent — picker is optional
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const fetchProfile = useCallback(async (customerId) => {
    if (!customerId) {
      setProfile(null);
      onChange?.({ customerId: null, profile: null });
      return;
    }
    setLoading(true);
    try {
      const r = await axios.get(`${API}/customers/${customerId}/branding`, { headers: headers() });
      setProfile(r.data || {});
      onChange?.({ customerId, profile: r.data || {} });
    } catch (err) {
      console.error('Failed to load branding profile', err);
      toast.error('Failed to load this customer\'s branding profile');
      setProfile(null);
      onChange?.({ customerId, profile: null });
    } finally {
      setLoading(false);
    }
  }, [onChange]);

  // Sync internal profile when parent sets `value` externally (e.g. URL deep-link)
  useEffect(() => {
    if (value && (!profile || profile?._customer_id !== value)) {
      let cancelled = false;
      (async () => {
        try {
          const r = await axios.get(`${API}/customers/${value}/branding`, { headers: headers() });
          if (cancelled) return;
          setProfile({ ...(r.data || {}), _customer_id: value });
        } catch {
          if (!cancelled) setProfile(null);
        }
      })();
      return () => { cancelled = true; };
    }
    if (!value && profile) {
      setProfile(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const handleSelect = (val) => {
    const next = val === '__none' ? null : val;
    fetchProfile(next);
  };

  const handlePrefill = () => {
    if (profile && onPrefill) onPrefill(profile);
  };

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-md p-3 space-y-2"
         data-testid="customer-branding-picker">
      <div className="flex items-center gap-2 text-sm font-semibold text-purple-900">
        <User className="w-4 h-4" />
        Attach to a customer's Branding Profile
        <span className="text-xs font-normal text-purple-700 ml-1">(optional)</span>
      </div>
      <div className="flex gap-2 items-center">
        <Select value={value || '__none'} onValueChange={handleSelect}>
          <SelectTrigger
            className="flex-1 bg-white"
            data-testid="customer-branding-picker-select"
          >
            <SelectValue placeholder="Select a customer…" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__none">— None —</SelectItem>
            {customers.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.display_name || c.company || c.name || c.email}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {profile && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={handlePrefill}
            disabled={loading}
            data-testid="customer-branding-picker-prefill-btn"
          >
            <Wand2 className="w-3 h-3 mr-1" />
            Pre-fill from profile
          </Button>
        )}
      </div>
      {profile && (
        <div className="text-xs text-purple-800 bg-white rounded px-2 py-1 border border-purple-100">
          Loaded: {profile.business_name || '(no name)'} ·{' '}
          {profile.industry || 'no industry'} · {(profile.taglines || []).length} taglines ·{' '}
          {(profile.logos || []).length} saved logos
        </div>
      )}
    </div>
  );
}
