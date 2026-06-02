import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Building2, Phone, MapPin, Globe, Save, AlertTriangle, Crown, Timer, Clock, Users, Shield, Eye, EyeOff, Upload, X, Image as ImageIcon, Palette, FileText, Mail, Receipt } from 'lucide-react';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CompanySettings() {
  const { hasPermission, isOwner } = useAuth();
  const canViewSettings = hasPermission(Permission.SETTINGS_VIEW) || isOwner();
  const canEditSettings = hasPermission(Permission.SETTINGS_EDIT) || isOwner();
  
  const { getTenant, updateTenant, fetchTenant } = useApp();
  const navigate = useNavigate();
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
    logo_url: '',
    default_tax_rate: ''
  });
  
  // Time tracking settings
  const [timeTrackingSettings, setTimeTrackingSettings] = useState({
    track_per_job: true,
    track_per_line_item: false,
    enable_employee_portal: false,
    enable_kiosk_mode: false,
    auto_suggest_on_status_change: true
  });
  const [savingTimeSettings, setSavingTimeSettings] = useState(false);

  // Employee Portal Permissions
  const [employeePortalSettings, setEmployeePortalSettings] = useState({
    can_view_tasks: true,
    can_view_schedule: true,
    can_view_pay_stubs: true,
    can_view_time_clock: true,
    can_edit_profile: true,
    can_see_job_details: false,
    can_see_customer_info: false,
    can_see_pricing: false
  });
  const [savingPortalSettings, setSavingPortalSettings] = useState(false);
  const [signatureSettings, setSignatureSettings] = useState({
    enabled: false,
    link_expiry_days: 7,
  });
  const [savingSignatureSettings, setSavingSignatureSettings] = useState(false);
  const [payrollSettings, setPayrollSettings] = useState({
    default_cycle: 'weekly',
    pay_week_start_day: 'monday',
    show_payroll_adjustments: false,
  });
  const [savingPayrollSettings, setSavingPayrollSettings] = useState(false);

  // Branding & template preferences (invoice / email / document)
  const DEFAULT_BRANDING = {
    primary_color: '#0D9488',
    secondary_color: '#14B8A6',
    invoice_accent_color: '',
    invoice_show_logo: true,
    invoice_logo_position: 'left',
    invoice_show_company_info: true,
    invoice_footer_text: '',
    invoice_payment_terms: '',
    email_from_name: '',
    email_show_logo: true,
    email_header_color: '',
    email_signature: '',
    document_show_logo: true,
    document_header_text: '',
    document_footer_text: '',
  };
  const [brandingSettings, setBrandingSettings] = useState(DEFAULT_BRANDING);
  const [savingBranding, setSavingBranding] = useState(false);
  const setBrand = (key, value) => setBrandingSettings((prev) => ({ ...prev, [key]: value }));

  // Logo upload state
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const logoInputRef = useRef(null);

  useEffect(() => {
    loadTenant();
  }, []);

  const loadTenant = async () => {
    setLoading(true);
    try {
      const data = await getTenant();
      setTenant(data);
      if (data.branding_settings) {
        setBrandingSettings({ ...DEFAULT_BRANDING, ...data.branding_settings });
      }
      setFormData({
        name: data.name || '',
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        state: data.state || '',
        zip_code: data.zip_code || '',
        country: data.country || 'USA',
        website: data.website || '',
        logo_url: '',
        default_tax_rate: data.default_tax_rate != null ? String(data.default_tax_rate) : ''
      });
      // Fetch logo separately if tenant has one
      if (data.has_logo) {
        try {
          const token = getAuthToken();
          const logoRes = await axios.get(`${API}/tenant/logo`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (logoRes.data?.logo_url) {
            setFormData(prev => ({ ...prev, logo_url: logoRes.data.logo_url }));
          }
        } catch (e) {
          console.error('Error fetching logo:', e);
        }
      }
      // Load time tracking settings from tenant
      if (data.time_tracking_settings) {        setTimeTrackingSettings({
          track_per_job: data.time_tracking_settings.track_per_job ?? true,
          track_per_line_item: data.time_tracking_settings.track_per_line_item ?? false,
          enable_employee_portal: data.time_tracking_settings.enable_employee_portal ?? false,
          enable_kiosk_mode: data.time_tracking_settings.enable_kiosk_mode ?? false,
          auto_suggest_on_status_change: data.time_tracking_settings.auto_suggest_on_status_change ?? true
        });
      }
      // Load employee portal permissions
      if (data.employee_portal_settings) {
        setEmployeePortalSettings({
          can_view_tasks: data.employee_portal_settings.can_view_tasks ?? true,
          can_view_schedule: data.employee_portal_settings.can_view_schedule ?? true,
          can_view_pay_stubs: data.employee_portal_settings.can_view_pay_stubs ?? true,
          can_view_time_clock: data.employee_portal_settings.can_view_time_clock ?? true,
          can_edit_profile: data.employee_portal_settings.can_edit_profile ?? true,
          can_see_job_details: data.employee_portal_settings.can_see_job_details ?? false,
          can_see_customer_info: data.employee_portal_settings.can_see_customer_info ?? false,
          can_see_pricing: data.employee_portal_settings.can_see_pricing ?? false
        });
      }
      setSignatureSettings({
        enabled: data.signature_settings?.enabled ?? false,
        link_expiry_days: data.signature_settings?.link_expiry_days ?? 7,
      });
      setPayrollSettings({
        default_cycle: data.payroll_settings?.default_cycle ?? 'weekly',
        pay_week_start_day: data.payroll_settings?.pay_week_start_day ?? 'monday',
        show_payroll_adjustments: data.payroll_settings?.show_payroll_adjustments ?? false,
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
        if (key === 'default_tax_rate') {
          if (value !== '' && value != null) {
            updateData[key] = parseFloat(value) || 0;
          }
        } else if (key !== 'logo_url' && value && value.trim() !== '') {
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

  const handleSaveTimeSettings = async () => {
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    
    setSavingTimeSettings(true);
    try {
      await updateTenant({ time_tracking_settings: timeTrackingSettings });
      toast.success('Time tracking settings updated');
    } catch (err) {
      console.error('Error updating time settings:', err);
      toast.error('Failed to update time tracking settings');
    }
    setSavingTimeSettings(false);
  };

  const handleSavePortalSettings = async () => {
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    
    setSavingPortalSettings(true);
    try {
      await updateTenant({ employee_portal_settings: employeePortalSettings });
      toast.success('Employee portal permissions updated');
    } catch (err) {
      console.error('Error updating portal settings:', err);
      toast.error('Failed to update employee portal permissions');
    }
    setSavingPortalSettings(false);
  };

  const handleSaveSignatureSettings = async () => {
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    setSavingSignatureSettings(true);
    try {
      await updateTenant({ signature_settings: signatureSettings });
      toast.success('Signature settings updated');
    } catch (err) {
      console.error('Error updating signature settings:', err);
      toast.error('Failed to update signature settings');
    }
    setSavingSignatureSettings(false);
  };

  const handleSavePayrollSettings = async () => {
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    setSavingPayrollSettings(true);
    try {
      await updateTenant({ payroll_settings: payrollSettings });
      toast.success('Payroll settings updated');
    } catch (err) {
      console.error('Error updating payroll settings:', err);
      toast.error('Failed to update payroll settings');
    }
    setSavingPayrollSettings(false);
  };

  const handleSaveBranding = async () => {
    if (!canEditSettings) {
      toast.error('You do not have permission to edit settings');
      return;
    }
    setSavingBranding(true);
    try {
      await updateTenant({ branding_settings: brandingSettings });
      toast.success('Branding & template preferences saved');
    } catch (err) {
      console.error('Error updating branding settings:', err);
      toast.error(err?.response?.data?.detail || 'Failed to save branding settings');
    }
    setSavingBranding(false);
  };

  // Logo upload handler
  const handleLogoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif', 'image/svg+xml'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Invalid file type. Please upload PNG, JPEG, WebP, GIF, or SVG');
      return;
    }

    // Validate file size (3MB max)
    if (file.size > 3 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 3MB');
      return;
    }

    setUploadingLogo(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', file);

      const token = getAuthToken();
      const response = await axios.post(`${API}/tenant/upload-logo`, formDataUpload, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      // Update local state with new logo
      setFormData({ ...formData, logo_url: response.data.logo_url });
      setTenant({ ...tenant, logo_url: response.data.logo_url });
      
      // Update global tenant state so header logo updates immediately
      await fetchTenant();
      
      toast.success('Logo uploaded successfully! Header logo updated.');
    } catch (err) {
      console.error('Error uploading logo:', err);
      toast.error(err.response?.data?.detail || 'Failed to upload logo');
    }
    setUploadingLogo(false);
    
    // Reset the file input by forcing re-mount
    if (logoInputRef.current) {
      logoInputRef.current.value = null;
      logoInputRef.current.type = '';
      logoInputRef.current.type = 'file';
    }
  };

  // Logo delete handler
  const handleLogoDelete = async () => {
    if (!window.confirm('Are you sure you want to remove the company logo?')) return;

    setUploadingLogo(true);
    try {
      const token = getAuthToken();
      await axios.delete(`${API}/tenant/logo`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      // Update local state
      setFormData({ ...formData, logo_url: '' });
      setTenant({ ...tenant, logo_url: null });
      
      // Update global tenant state so header logo reverts
      await fetchTenant();
      
      toast.success('Logo removed. Header reverted to default.');
    } catch (err) {
      console.error('Error deleting logo:', err);
      toast.error('Failed to remove logo');
    }
    setUploadingLogo(false);
  };

  const planBadge = (plan) => {
    const planName = plan || 'free';
    const colors = {
      free: 'bg-gray-100 text-gray-700',
      pro: 'bg-blue-100 text-blue-700',
      business: 'bg-purple-100 text-purple-700',
      enterprise: 'bg-amber-100 text-amber-700',
      founders: 'bg-violet-100 text-violet-700'
    };
    return (
      <Badge className={colors[planName] || colors.free}>
        {planName.toUpperCase()}
      </Badge>
    );
  };

  // Permission denied view
  if (!canViewSettings) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4" style={{ color: '#d97706' }} />
        <h2 className="text-xl font-semibold mb-2 text-gray-900">Access Denied</h2>
        <p className="text-gray-500">You don't have permission to view company settings.</p>
      </div>
    );
  }

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
        <h2 className="text-xl font-semibold mb-2 text-gray-900">No Company Found</h2>
        <p className="text-gray-500">Your account is not associated with a company.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-settings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Company Settings</h1>
          <p className="text-gray-400">Manage your sign shop's information and preferences</p>
        </div>
        <div className="flex items-center gap-3">
          {planBadge(tenant.plan)}
          {isOwner() && (
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
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Building2 className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Company Information
          </CardTitle>
          <CardDescription className="text-gray-500">
            Basic information about your sign shop
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Company Name */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-gray-900">Company Name *</Label>
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
                <Label htmlFor="phone" className="text-gray-900">Phone</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
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
                <Label htmlFor="address" className="text-gray-900">Street Address</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
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
                <Label htmlFor="city" className="text-gray-900">City</Label>
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
                <Label htmlFor="state" className="text-gray-900">State</Label>
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
                <Label htmlFor="zip_code" className="text-gray-900">ZIP Code</Label>
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
                <Label htmlFor="country" className="text-gray-900">Country</Label>
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
                <Label htmlFor="website" className="text-gray-900">Website</Label>
                <div className="relative">
                  <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
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

              {/* Default Tax Rate */}
              <div className="space-y-2">
                <Label htmlFor="default_tax_rate" className="text-gray-900">Default Tax Rate (%)</Label>
                <p className="text-xs text-gray-500">Applied to invoices for non-tax-exempt customers.</p>
                <Input
                  id="default_tax_rate"
                  type="number"
                  step="0.001"
                  min="0"
                  max="100"
                  data-testid="company-tax-rate-input"
                  value={formData.default_tax_rate}
                  onChange={(e) => setFormData({...formData, default_tax_rate: e.target.value})}
                  placeholder="e.g. 6 or 8.5"
                  disabled={!canEditSettings}
                  style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
                />
              </div>
            </div>

            {/* Company Logo Upload Section */}
            <div className="pt-6 border-t" style={{ borderColor: '#D7DCE2' }}>
              <Label className="text-gray-900 text-base font-medium">Company Logo</Label>
              <p className="text-sm mb-4 text-gray-500">
                Upload your company logo. It will appear on invoices, quotes, and customer portals.
              </p>
              
              <div className="flex items-start gap-6">
                {/* Logo Preview */}
                <div 
                  className="w-32 h-32 rounded-lg border-2 border-dashed flex items-center justify-center overflow-hidden"
                  style={{ 
                    borderColor: formData.logo_url ? '#2F8BFB' : '#D7DCE2',
                    background: formData.logo_url ? '#FFFFFF' : '#F5F7FA'
                  }}
                >
                  {formData.logo_url ? (
                    <img 
                      src={formData.logo_url} 
                      alt="Company Logo" 
                      className="w-full h-full object-contain p-2"
                    />
                  ) : (
                    <div className="text-center p-4">
                      <ImageIcon className="h-8 w-8 mx-auto mb-2 text-gray-500" />
                      <p className="text-xs text-gray-500">No logo</p>
                    </div>
                  )}
                </div>

                {/* Upload Controls */}
                <div className="flex-1 space-y-3">
                  <input
                    type="file"
                    ref={logoInputRef}
                    onChange={handleLogoUpload}
                    accept="image/png,image/jpeg,image/jpg,image/webp,image/gif,image/svg+xml"
                    className="hidden"
                    data-testid="logo-file-input"
                  />
                  
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => logoInputRef.current?.click()}
                      disabled={!canEditSettings || uploadingLogo}
                      data-testid="upload-logo-btn"
                      className="flex items-center gap-2"
                    >
                      <Upload className="h-4 w-4" />
                      {uploadingLogo ? 'Uploading...' : formData.logo_url ? 'Change Logo' : 'Upload Logo'}
                    </Button>
                    
                    {formData.logo_url && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleLogoDelete}
                        disabled={!canEditSettings || uploadingLogo}
                        data-testid="delete-logo-btn"
                        className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:border-red-300"
                      >
                        <X className="h-4 w-4" />
                        Remove
                      </Button>
                    )}
                  </div>
                  
                  <p className="text-xs text-gray-500">
                    Supported formats: PNG, JPEG, WebP, GIF, SVG. Max size: 3MB
                  </p>
                </div>
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

      {/* Branding & Templates Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }} data-testid="branding-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Palette className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Branding & Templates
          </CardTitle>
          <CardDescription className="text-gray-500">
            Control how your logo, colors, and text appear on invoices, emails, and generated documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Brand Colors */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Brand Colors</h3>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-900">Primary Color</Label>
                <div className="flex items-center gap-3">
                  <input type="color" value={brandingSettings.primary_color || '#0D9488'} onChange={(e) => setBrand('primary_color', e.target.value)} disabled={!canEditSettings} className="h-10 w-14 rounded border cursor-pointer" data-testid="branding-primary-color" />
                  <Input value={brandingSettings.primary_color || ''} onChange={(e) => setBrand('primary_color', e.target.value)} disabled={!canEditSettings} className="font-mono" placeholder="#0D9488" />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-900">Secondary Color</Label>
                <div className="flex items-center gap-3">
                  <input type="color" value={brandingSettings.secondary_color || '#14B8A6'} onChange={(e) => setBrand('secondary_color', e.target.value)} disabled={!canEditSettings} className="h-10 w-14 rounded border cursor-pointer" data-testid="branding-secondary-color" />
                  <Input value={brandingSettings.secondary_color || ''} onChange={(e) => setBrand('secondary_color', e.target.value)} disabled={!canEditSettings} className="font-mono" placeholder="#14B8A6" />
                </div>
              </div>
            </div>
          </div>

          {/* Invoice Branding */}
          <div className="space-y-4 border-t pt-6" style={{ borderColor: '#EEF1F4' }}>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 uppercase tracking-wide">
              <Receipt className="h-4 w-4" style={{ color: '#2F8BFB' }} /> Invoice Layout & Branding
            </h3>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-900">Accent Color <span className="text-gray-400 font-normal">(defaults to primary)</span></Label>
                <div className="flex items-center gap-3">
                  <input type="color" value={brandingSettings.invoice_accent_color || brandingSettings.primary_color || '#0D9488'} onChange={(e) => setBrand('invoice_accent_color', e.target.value)} disabled={!canEditSettings} className="h-10 w-14 rounded border cursor-pointer" data-testid="branding-invoice-accent-color" />
                  <Input value={brandingSettings.invoice_accent_color || ''} onChange={(e) => setBrand('invoice_accent_color', e.target.value)} disabled={!canEditSettings} className="font-mono" placeholder="Leave blank to use primary" />
                </div>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-900">Logo Position</Label>
                <Select value={brandingSettings.invoice_logo_position || 'left'} onValueChange={(v) => setBrand('invoice_logo_position', v)} disabled={!canEditSettings}>
                  <SelectTrigger data-testid="branding-invoice-logo-position"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="left">Left</SelectItem>
                    <SelectItem value="center">Center</SelectItem>
                    <SelectItem value="right">Right</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex items-center justify-between rounded-lg border p-3" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <Label className="text-gray-900">Show logo on invoices</Label>
                <Switch checked={brandingSettings.invoice_show_logo} onCheckedChange={(c) => setBrand('invoice_show_logo', c)} disabled={!canEditSettings} data-testid="branding-invoice-show-logo" />
              </div>
              <div className="flex items-center justify-between rounded-lg border p-3" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <Label className="text-gray-900">Show company address</Label>
                <Switch checked={brandingSettings.invoice_show_company_info} onCheckedChange={(c) => setBrand('invoice_show_company_info', c)} disabled={!canEditSettings} data-testid="branding-invoice-show-company" />
              </div>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-900">Payment Terms</Label>
                <Input value={brandingSettings.invoice_payment_terms || ''} onChange={(e) => setBrand('invoice_payment_terms', e.target.value)} disabled={!canEditSettings} placeholder="e.g. Net 30" data-testid="branding-invoice-payment-terms" />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-900">Invoice Footer Text</Label>
                <Input value={brandingSettings.invoice_footer_text || ''} onChange={(e) => setBrand('invoice_footer_text', e.target.value)} disabled={!canEditSettings} placeholder="Thank you for your business!" data-testid="branding-invoice-footer" />
              </div>
            </div>
          </div>

          {/* Email Branding */}
          <div className="space-y-4 border-t pt-6" style={{ borderColor: '#EEF1F4' }}>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 uppercase tracking-wide">
              <Mail className="h-4 w-4" style={{ color: '#2F8BFB' }} /> Email Branding
            </h3>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-900">Email "From" Name <span className="text-gray-400 font-normal">(defaults to company name)</span></Label>
                <Input value={brandingSettings.email_from_name || ''} onChange={(e) => setBrand('email_from_name', e.target.value)} disabled={!canEditSettings} placeholder={formData.name || 'Your Company'} data-testid="branding-email-from-name" />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-900">Email Header Color <span className="text-gray-400 font-normal">(defaults to primary)</span></Label>
                <div className="flex items-center gap-3">
                  <input type="color" value={brandingSettings.email_header_color || brandingSettings.primary_color || '#0D9488'} onChange={(e) => setBrand('email_header_color', e.target.value)} disabled={!canEditSettings} className="h-10 w-14 rounded border cursor-pointer" data-testid="branding-email-header-color" />
                  <Input value={brandingSettings.email_header_color || ''} onChange={(e) => setBrand('email_header_color', e.target.value)} disabled={!canEditSettings} className="font-mono" placeholder="Leave blank to use primary" />
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3 md:w-1/2" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
              <Label className="text-gray-900">Show logo in email header</Label>
              <Switch checked={brandingSettings.email_show_logo} onCheckedChange={(c) => setBrand('email_show_logo', c)} disabled={!canEditSettings} data-testid="branding-email-show-logo" />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Email Signature</Label>
              <Textarea value={brandingSettings.email_signature || ''} onChange={(e) => setBrand('email_signature', e.target.value)} disabled={!canEditSettings} rows={3} placeholder={'Best regards,\nThe Team'} data-testid="branding-email-signature" />
              <p className="text-xs text-gray-400">Appended to the bottom of every email you send to customers.</p>
            </div>
            <p className="text-xs text-gray-500 rounded-lg p-3" style={{ background: '#F0F7FF' }}>
              Once saved, your outgoing emails are wrapped with your logo, header color, and signature automatically.
            </p>
          </div>

          {/* Document Branding */}
          <div className="space-y-4 border-t pt-6" style={{ borderColor: '#EEF1F4' }}>
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 uppercase tracking-wide">
              <FileText className="h-4 w-4" style={{ color: '#2F8BFB' }} /> Document Branding
            </h3>
            <div className="flex items-center justify-between rounded-lg border p-3 md:w-1/2" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
              <Label className="text-gray-900">Show logo on generated PDFs</Label>
              <Switch checked={brandingSettings.document_show_logo} onCheckedChange={(c) => setBrand('document_show_logo', c)} disabled={!canEditSettings} data-testid="branding-document-show-logo" />
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <Label className="text-gray-900">Document Header Text</Label>
                <Input value={brandingSettings.document_header_text || ''} onChange={(e) => setBrand('document_header_text', e.target.value)} disabled={!canEditSettings} placeholder="e.g. Official Document" data-testid="branding-document-header" />
              </div>
              <div className="space-y-2">
                <Label className="text-gray-900">Document Footer Text</Label>
                <Input value={brandingSettings.document_footer_text || ''} onChange={(e) => setBrand('document_footer_text', e.target.value)} disabled={!canEditSettings} placeholder="e.g. Confidential" data-testid="branding-document-footer" />
              </div>
            </div>
          </div>

          {canEditSettings && (
            <div className="flex justify-end border-t pt-4" style={{ borderColor: '#D7DCE2' }}>
              <Button onClick={handleSaveBranding} disabled={savingBranding} data-testid="save-branding-btn" style={{ background: '#2F8BFB' }} className="text-white hover:opacity-90">
                <Save className="mr-2 h-4 w-4" />
                {savingBranding ? 'Saving...' : 'Save Branding & Templates'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Clock className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Payroll Preferences
          </CardTitle>
          <CardDescription className="text-gray-500">
            Set the default payroll cycle and the day your payroll week begins. The worksheet still allows any custom date range by default.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-gray-900">Default Payroll Cycle</Label>
              <Select value={payrollSettings.default_cycle} onValueChange={(value) => setPayrollSettings({ ...payrollSettings, default_cycle: value })} disabled={!canEditSettings}>
                <SelectTrigger data-testid="company-payroll-default-cycle-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="biweekly">Biweekly</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Pay Week Starts On</Label>
              <Select value={payrollSettings.pay_week_start_day} onValueChange={(value) => setPayrollSettings({ ...payrollSettings, pay_week_start_day: value })} disabled={!canEditSettings}>
                <SelectTrigger data-testid="company-payroll-week-start-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map((day) => (
                    <SelectItem key={day} value={day}>{day.charAt(0).toUpperCase() + day.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded-lg border p-4" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <Label className="text-gray-900">Show Payroll Adjustments Panel</Label>
                <p className="text-sm text-gray-500">Toggle the left-side Adjustments panel in Payroll worksheet.</p>
              </div>
              <Switch
                checked={payrollSettings.show_payroll_adjustments}
                onCheckedChange={(checked) => setPayrollSettings({ ...payrollSettings, show_payroll_adjustments: checked })}
                disabled={!canEditSettings}
                data-testid="company-payroll-show-adjustments-toggle"
              />
            </div>
          </div>

          {canEditSettings && (
            <div className="flex justify-end border-t pt-4" style={{ borderColor: '#D7DCE2' }}>
              <Button onClick={handleSavePayrollSettings} disabled={savingPayrollSettings} data-testid="save-payroll-settings-btn" style={{ background: '#2F8BFB' }} className="text-white hover:opacity-90">
                <Save className="mr-2 h-4 w-4" />
                {savingPayrollSettings ? 'Saving...' : 'Save Payroll Preferences'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Naming Convention Settings Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Shield className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Naming Conventions
          </CardTitle>
          <CardDescription className="text-gray-500">
            Configure how orders and order items are automatically named
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <p className="font-medium text-gray-700">Order Name Format</p>
            <p className="text-gray-500 text-xs">DISPLAYNAME-MMDDYY (all caps). Duplicates get letter suffix: FRANKSMITH-041226a</p>
            <p className="font-medium text-gray-700 mt-3">Order Item Name Format</p>
            <p className="text-gray-500 text-xs">displayname-category-mmddyy (lowercase). Example: franksmith-banner-041226</p>
            <p className="font-medium text-gray-700 mt-3">Display Name</p>
            <p className="text-gray-500 text-xs">Defaults to company name (no spaces). Editable per customer.</p>
          </div>
        </CardContent>
      </Card>

      {/* Time Tracking Settings Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Timer className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Time Tracking Settings
          </CardTitle>
          <CardDescription className="text-gray-500">
            Configure how employees track time on jobs
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Tracking Level */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider text-gray-500">
              Tracking Level
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Track Time Per Job</Label>
                  <p className="text-sm text-gray-500">Log time at the order level (e.g., "Worked on Banner Order")</p>
                </div>
                <Switch
                  checked={timeTrackingSettings.track_per_job}
                  onCheckedChange={(checked) => setTimeTrackingSettings({...timeTrackingSettings, track_per_job: checked})}
                  disabled={!canEditSettings}
                  data-testid="track-per-job-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Track Time Per Line Item</Label>
                  <p className="text-sm text-gray-500">Log time on specific items (e.g., "Worked on 24x36 Banner")</p>
                </div>
                <Switch
                  checked={timeTrackingSettings.track_per_line_item}
                  onCheckedChange={(checked) => setTimeTrackingSettings({...timeTrackingSettings, track_per_line_item: checked})}
                  disabled={!canEditSettings}
                  data-testid="track-per-line-item-toggle"
                />
              </div>
            </div>
          </div>

          {/* Access Methods */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider text-gray-500">
              Employee Access
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Employee Portal Time Tracking</Label>
                  <p className="text-sm text-gray-500">Let employees track time from their portal</p>
                </div>
                <Switch
                  checked={timeTrackingSettings.enable_employee_portal}
                  onCheckedChange={(checked) => setTimeTrackingSettings({...timeTrackingSettings, enable_employee_portal: checked})}
                  disabled={!canEditSettings}
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Kiosk Mode</Label>
                  <p className="text-sm text-gray-500">Shop floor tablet with PIN login and job scanning</p>
                </div>
                <Switch
                  checked={timeTrackingSettings.enable_kiosk_mode}
                  onCheckedChange={(checked) => setTimeTrackingSettings({...timeTrackingSettings, enable_kiosk_mode: checked})}
                  disabled={!canEditSettings}
                />
              </div>
            </div>
          </div>

          {/* Automation */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider text-gray-500">
              Automation
            </h4>
            <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
              <div>
                <Label className="font-medium text-gray-900">Auto-Suggest on Status Change</Label>
                <p className="text-sm text-gray-500">Prompt to start/stop timer when job status changes</p>
              </div>
              <Switch
                checked={timeTrackingSettings.auto_suggest_on_status_change}
                onCheckedChange={(checked) => setTimeTrackingSettings({...timeTrackingSettings, auto_suggest_on_status_change: checked})}
                disabled={!canEditSettings}
                data-testid="auto-suggest-toggle"
              />
            </div>
          </div>

          {/* Save Button */}
          {canEditSettings && (
            <div className="flex justify-end pt-4 border-t" style={{ borderColor: '#D7DCE2' }}>
              <Button 
                onClick={handleSaveTimeSettings}
                disabled={savingTimeSettings}
                data-testid="save-time-settings-btn"
                style={{ background: '#2F8BFB' }}
                className="text-white hover:opacity-90"
              >
                <Save className="h-4 w-4 mr-2" />
                {savingTimeSettings ? 'Saving...' : 'Save Time Settings'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Employee Portal Permissions Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Users className="h-5 w-5" style={{ color: '#2F8BFB' }} />
            Employee Portal Permissions
          </CardTitle>
          <CardDescription className="text-gray-500">
            Control what employees can see and do in their portal
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Basic Visibility */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider flex items-center gap-2 text-gray-500">
              <Eye className="h-4 w-4" />
              Portal Sections
            </h4>
            <div className="grid gap-3">
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Tasks</Label>
                  <p className="text-sm text-gray-500">View assigned tasks and to-dos</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_view_tasks}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_view_tasks: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-view-tasks-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Schedule</Label>
                  <p className="text-sm text-gray-500">View work schedule and shifts</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_view_schedule}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_view_schedule: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-view-schedule-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Pay Stubs</Label>
                  <p className="text-sm text-gray-500">View payroll history and pay stubs</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_view_pay_stubs}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_view_pay_stubs: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-view-pay-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Time Clock</Label>
                  <p className="text-sm text-gray-500">Clock in/out and track breaks</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_view_time_clock}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_view_time_clock: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-view-time-clock-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
                <div>
                  <Label className="font-medium text-gray-900">Edit Profile</Label>
                  <p className="text-sm text-gray-500">Update their own contact information</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_edit_profile}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_edit_profile: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-edit-profile-toggle"
                />
              </div>
            </div>
          </div>

          {/* Sensitive Information */}
          <div className="space-y-4">
            <h4 className="font-medium text-sm uppercase tracking-wider flex items-center gap-2 text-gray-500">
              <Shield className="h-4 w-4" />
              Sensitive Information Access
            </h4>
            <div className="grid gap-3">
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#FFF9E6' }}>
                <div>
                  <Label className="font-medium text-gray-900">Order Details</Label>
                  <p className="text-sm text-gray-500">See full job specifications and notes</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_see_job_details}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_see_job_details: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-see-job-details-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#FFF9E6' }}>
                <div>
                  <Label className="font-medium text-gray-900">Customer Information</Label>
                  <p className="text-sm text-gray-500">See customer names and contact details</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_see_customer_info}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_see_customer_info: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-see-customer-toggle"
                />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#FFF9E6' }}>
                <div>
                  <Label className="font-medium text-gray-900">Pricing Information</Label>
                  <p className="text-sm text-gray-500">See job prices and financial details</p>
                </div>
                <Switch
                  checked={employeePortalSettings.can_see_pricing}
                  onCheckedChange={(checked) => setEmployeePortalSettings({...employeePortalSettings, can_see_pricing: checked})}
                  disabled={!canEditSettings}
                  data-testid="emp-see-pricing-toggle"
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          {canEditSettings && (
            <div className="flex justify-end pt-4 border-t" style={{ borderColor: '#D7DCE2' }}>
              <Button 
                onClick={handleSavePortalSettings}
                disabled={savingPortalSettings}
                data-testid="save-portal-settings-btn"
                style={{ background: '#2F8BFB' }}
                className="text-white hover:opacity-90"
              >
                <Save className="h-4 w-4 mr-2" />
                {savingPortalSettings ? 'Saving...' : 'Save Portal Permissions'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Account Info Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="text-gray-900">Account Details</CardTitle>
          <CardDescription className="text-gray-500">
            Information about your SignGuy AI subscription
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm text-gray-500">Subscription Plan</p>
              <p className="text-lg font-semibold capitalize text-gray-900">{tenant.plan}</p>
            </div>
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm text-gray-500">Account Status</p>
              <p className="text-lg font-semibold" style={{ color: tenant.is_active ? '#10b981' : '#ef4444' }}>
                {tenant.is_active ? 'Active' : 'Inactive'}
              </p>
            </div>
            <div className="p-4 rounded-lg" style={{ background: '#F5F7FA' }}>
              <p className="text-sm text-gray-500">Created</p>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(tenant.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pricing Setup Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="text-gray-900">Pricing Setup</CardTitle>
          <CardDescription className="text-gray-500">
            Configure cost settings and import historical invoices for AI benchmark review
          </CardDescription>
        </CardHeader>
        <CardContent>
          <button
            onClick={() => navigate('/settings/pricing-setup')}
            className="w-full p-4 rounded-lg text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
            style={{ background: '#F5F7FA' }}
            data-testid="settings-pricing-setup-link"
          >
            <div>
              <p className="font-medium text-gray-900">Historical Invoice Import & Pricing Setup</p>
              <p className="text-sm mt-1 text-gray-500">Review AI-generated selling benchmarks before saving them to pricing settings</p>
            </div>
            <span className="text-gray-500">&rarr;</span>
          </button>
        </CardContent>
      </Card>

      {/* Data Management Card */}
      <Card className="border" style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}>
        <CardHeader>
          <CardTitle className="text-gray-900">Signature Capture</CardTitle>
          <CardDescription className="text-gray-500">
            Enable or hide all customer-facing and internal signature tools across orders, proofs, invoices, and documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-lg border" style={{ borderColor: '#D7DCE2', background: '#F5F7FA' }}>
            <div>
              <Label className="font-medium text-gray-900">Enable Signatures</Label>
              <p className="text-sm text-gray-500">When disabled, signature-related UI is hidden throughout the app.</p>
            </div>
            <Switch
              checked={signatureSettings.enabled}
              onCheckedChange={(checked) => setSignatureSettings((current) => ({ ...current, enabled: checked }))}
              disabled={!canEditSettings}
              data-testid="signature-feature-toggle"
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="signature-expiry-days" className="text-gray-900">Signature Link Expiry (days)</Label>
              <Input
                id="signature-expiry-days"
                type="number"
                min="1"
                max="30"
                value={signatureSettings.link_expiry_days}
                onChange={(e) => setSignatureSettings((current) => ({ ...current, link_expiry_days: parseInt(e.target.value, 10) || 7 }))}
                disabled={!canEditSettings}
                data-testid="signature-expiry-days-input"
                style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}
              />
            </div>
          </div>
          {canEditSettings && (
            <div className="flex justify-end pt-2">
              <Button onClick={handleSaveSignatureSettings} disabled={savingSignatureSettings} data-testid="save-signature-settings-btn" style={{ background: '#2F8BFB' }} className="text-white hover:opacity-90">
                <Save className="h-4 w-4 mr-2" />
                {savingSignatureSettings ? 'Saving...' : 'Save Signature Settings'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  );
}
