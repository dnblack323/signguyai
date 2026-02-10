import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Building2, Phone, MapPin, Globe, Save, AlertTriangle, Crown } from 'lucide-react';
import { toast } from 'sonner';

export default function CompanySettings() {
  const { hasPermission, isOwner } = useAuth();
  const canEditSettings = hasPermission(Permission.SETTINGS_EDIT) || isOwner;
  
  const { getTenant, updateTenant } = useApp();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tenant, setTenant] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'USA',
    website: '',
    logo_url: ''
  });

  useEffect(() => {
    loadTenant();
  }, []);

  const loadTenant = async () => {
    setLoading(true);
    try {
      const data = await getTenant();
      setTenant(data);
      setFormData({
        name: data.name || '',
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        state: data.state || '',
        zip_code: data.zip_code || '',
        country: data.country || 'USA',
        website: data.website || '',
        logo_url: data.logo_url || ''
      });
    } catch (err) {
      console.error('Error loading tenant:', err);
      toast.error('Failed to load company settings');
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    
    setSaving(true);
    try {
      // Only send non-empty fields
      const updateData = {};
      Object.entries(formData).forEach(([key, value]) => {
        if (value && value.trim() !== '') {
          updateData[key] = value.trim();
        }
      });
      
      const updated = await updateTenant(updateData);
      setTenant(updated);
      toast.success('Company settings updated successfully');
    } catch (err) {
      console.error('Error updating tenant:', err);
      toast.error('Failed to update company settings');
    }
    setSaving(false);
  };

  const planBadge = (plan) => {
    const colors = {
      free: 'bg-gray-100 text-gray-700',
      pro: 'bg-blue-100 text-blue-700',
      business: 'bg-purple-100 text-purple-700',
      enterprise: 'bg-amber-100 text-amber-700'
    };
    return (
      <Badge className={colors[plan] || colors.free}>
        {plan.toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#2F8BFB]"></div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4" style={{ color: '#d97706' }} />
        <h2 className="text-xl font-semibold mb-2" style={{ color: '#1A1A1A' }}>No Company Found</h2>
        <p style={{ color: '#5A5A5A' }}>Your account is not associated with a company.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>Company Settings</h1>
          <p style={{ color: '#5A5A5A' }}>Manage your sign shop's information and preferences</p>
        </div>
        <div className="flex items-center gap-3">
          {planBadge(tenant.plan)}
          {isOwner && (
            <Badge className="bg-amber-100 text-amber-700 flex items-center gap-1">
              <Crown className="h-3 w-3" />
              Owner
            </Badge>
          )}
        </div>
      </div>

      {/* Company Info Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2" style={{ color: '#1A1A1A' }}>
            <Building2 className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Company Information
          </CardTitle>
          <CardDescription style={{ color: '#5A5A5A' }}>
            Basic information about your sign shop
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Company Name */}
              <div className="space-y-2">
                <Label htmlFor="name" style={{ color: '#1A1A1A' }}>Company Name *</Label>
                <Input
                  id="name"
                  data-testid="company-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Your Sign Shop Name"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="phone" style={{ color: '#1A1A1A' }}>Phone</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: '#5A5A5A' }} />
                  <Input
                    id="phone"
                    data-testid="company-phone-input"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    placeholder="555-123-4567"
                    disabled={!canEditSettings}
                    className="pl-10"
                    style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                  />
                </div>
              </div>

              {/* Address */}
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="address" style={{ color: '#1A1A1A' }}>Street Address</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: '#5A5A5A' }} />
                  <Input
                    id="address"
                    data-testid="company-address-input"
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    placeholder="123 Main Street"
                    disabled={!canEditSettings}
                    className="pl-10"
                    style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                  />
                </div>
              </div>

              {/* City */}
              <div className="space-y-2">
                <Label htmlFor="city" style={{ color: '#1A1A1A' }}>City</Label>
                <Input
                  id="city"
                  data-testid="company-city-input"
                  value={formData.city}
                  onChange={(e) => setFormData({...formData, city: e.target.value})}
                  placeholder="Phoenix"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>

              {/* State */}
              <div className="space-y-2">
                <Label htmlFor="state" style={{ color: '#1A1A1A' }}>State</Label>
                <Input
                  id="state"
                  data-testid="company-state-input"
                  value={formData.state}
                  onChange={(e) => setFormData({...formData, state: e.target.value})}
                  placeholder="AZ"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>

              {/* ZIP */}
              <div className="space-y-2">
                <Label htmlFor="zip_code" style={{ color: '#1A1A1A' }}>ZIP Code</Label>
                <Input
                  id="zip_code"
                  data-testid="company-zip-input"
                  value={formData.zip_code}
                  onChange={(e) => setFormData({...formData, zip_code: e.target.value})}
                  placeholder="85001"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>

              {/* Country */}
              <div className="space-y-2">
                <Label htmlFor="country" style={{ color: '#1A1A1A' }}>Country</Label>
                <Input
                  id="country"
                  data-testid="company-country-input"
                  value={formData.country}
                  onChange={(e) => setFormData({...formData, country: e.target.value})}
                  placeholder="USA"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>

              {/* Website */}
              <div className="space-y-2">
                <Label htmlFor="website" style={{ color: '#1A1A1A' }}>Website</Label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: '#5A5A5A' }} />
                  <Input
                    id="website"
                    data-testid="company-website-input"
                    value={formData.website}
                    onChange={(e) => setFormData({...formData, website: e.target.value})}
                    placeholder="https://yoursignshop.com"
                    disabled={!canEditSettings}
                    className="pl-10"
                    style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                  />
                </div>
              </div>

              {/* Logo URL */}
              <div className="space-y-2">
                <Label htmlFor="logo_url" style={{ color: '#1A1A1A' }}>Logo URL</Label>
                <Input
                  id="logo_url"
                  data-testid="company-logo-input"
                  value={formData.logo_url}
                  onChange={(e) => setFormData({...formData, logo_url: e.target.value})}
                  placeholder="https://example.com/logo.png"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>
            </div>

            {/* Save Button */}
            {canEditSettings && (
              <div className="flex justify-end pt-4 border-t" style={{ borderColor: '#D7DCE2' }}>
                <Button 
                  type="submit" 
                  disabled={saving}
                  data-testid="save-settings-btn"
                  style={{ background: '#2F8BFB' }}
                  className="text-white hover:opacity-90"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Account Info Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle style={{ color: '#1A1A1A' }}>Account Details</CardTitle>
          <CardDescription style={{ color: '#5A5A5A' }}>
            Information about your SignGuy AI subscription
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm" style={{ color: '#5A5A5A' }}>Subscription Plan</p>
              <p className="text-lg font-semibold capitalize" style={{ color: '#1A1A1A' }}>{tenant.plan}</p>
            </div>
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm" style={{ color: '#5A5A5A' }}>Account Status</p>
              <p className="text-lg font-semibold" style={{ color: tenant.is_active ? '#10b981' : '#ef4444' }}>
                {tenant.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm" style={{ color: '#5A5A5A' }}>Created</p>
              <p className="text-lg font-semibold" style={{ color: '#1A1A1A' }}>
                {new Date(tenant.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
