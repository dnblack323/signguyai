import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { 
  Loader2, User, Mail, Phone, Building2, Shield, Bell, 
  Camera, FileText, CheckCircle, AlertCircle, Lock
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PortalProfile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState(null);
  const [editedProfile, setEditedProfile] = useState({});
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' });
  const [changingPassword, setChangingPassword] = useState(false);
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  const fetchProfile = useCallback(async () => {
    const token = localStorage.getItem('portal_token');
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/portal/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(data);
        setEditedProfile({
          name: data.name || '',
          phone: data.phone || '',
          profile_image_url: data.profile_image_url || '',
          is_tax_exempt: data.is_tax_exempt || false,
          tax_exempt_document_url: data.tax_exempt_document_url || '',
          notification_preferences: data.notification_preferences || {
            email_messages: true,
            email_orders: true,
            email_approvals: true,
            email_payments: true
          }
        });
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleSaveProfile = async () => {
    const token = localStorage.getItem('portal_token');
    setSaving(true);

    try {
      const response = await fetch(`${API_URL}/api/portal/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editedProfile)
      });

      if (response.ok) {
        const updated = await response.json();
        setProfile(updated);
        localStorage.setItem('portal_customer_name', updated.name);
        toast.success('Profile updated successfully!');
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to update profile');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (passwords.new !== passwords.confirm) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwords.new.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    const token = localStorage.getItem('portal_token');
    setChangingPassword(true);

    try {
      const response = await fetch(`${API_URL}/api/portal/change-password?current_password=${encodeURIComponent(passwords.current)}&new_password=${encodeURIComponent(passwords.new)}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setShowPasswordDialog(false);
        setPasswords({ current: '', new: '', confirm: '' });
        toast.success('Password changed successfully!');
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to change password');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleNotificationChange = (key, value) => {
    setEditedProfile({
      ...editedProfile,
      notification_preferences: {
        ...editedProfile.notification_preferences,
        [key]: value
      }
    });
  };

  if (loading) {
    return (
      <PortalLayout activeNav="profile" customerName={customerName}>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  return (
    <PortalLayout activeNav="profile" customerName={customerName}>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Your Profile</h2>
          <p className="text-slate-600 mt-1">Manage your account settings</p>
        </div>

        <Tabs defaultValue="info" className="space-y-6">
          <TabsList className="bg-slate-100">
            <TabsTrigger value="info">Personal Info</TabsTrigger>
            <TabsTrigger value="tax">Tax Exempt</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          {/* Personal Info */}
          <TabsContent value="info">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Personal Information</CardTitle>
                <CardDescription>Update your contact details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Profile Image */}
                <div className="flex items-center gap-4">
                  <div className="w-20 h-20 rounded-full bg-slate-200 flex items-center justify-center overflow-hidden">
                    {editedProfile.profile_image_url ? (
                      <img 
                        src={editedProfile.profile_image_url} 
                        alt="Profile" 
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <User className="h-10 w-10 text-slate-400" />
                    )}
                  </div>
                  <div>
                    <Label htmlFor="profile_image" className="text-slate-700">Profile Photo URL</Label>
                    <Input
                      id="profile_image"
                      value={editedProfile.profile_image_url}
                      onChange={(e) => setEditedProfile({ ...editedProfile, profile_image_url: e.target.value })}
                      placeholder="https://..."
                      className="mt-1 w-72"
                    />
                  </div>
                </div>

                <Separator />

                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name" className="text-slate-700">Full Name</Label>
                    <div className="relative mt-1">
                      <User className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        id="name"
                        value={editedProfile.name}
                        onChange={(e) => setEditedProfile({ ...editedProfile, name: e.target.value })}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-700">Email</Label>
                    <div className="relative mt-1">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        value={profile?.email || ''}
                        disabled
                        className="pl-10 bg-slate-50"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Contact the shop to change email</p>
                  </div>
                  <div>
                    <Label htmlFor="phone" className="text-slate-700">Phone</Label>
                    <div className="relative mt-1">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        id="phone"
                        value={editedProfile.phone}
                        onChange={(e) => setEditedProfile({ ...editedProfile, phone: e.target.value })}
                        placeholder="(555) 123-4567"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-700">Company</Label>
                    <div className="relative mt-1">
                      <Building2 className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                      <Input
                        value={profile?.company || ''}
                        disabled
                        className="pl-10 bg-slate-50"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Contact the shop to change</p>
                  </div>
                </div>

                <div className="pt-4">
                  <Button 
                    className="bg-teal-500 hover:bg-teal-600"
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tax Exempt */}
          <TabsContent value="tax">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Tax Exempt Status</CardTitle>
                <CardDescription>Manage your tax exemption documentation</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      editedProfile.is_tax_exempt ? 'bg-green-100' : 'bg-slate-200'
                    }`}>
                      <Shield className={`h-5 w-5 ${
                        editedProfile.is_tax_exempt ? 'text-green-600' : 'text-slate-400'
                      }`} />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">Tax Exempt</p>
                      <p className="text-sm text-slate-500">
                        {editedProfile.is_tax_exempt ? 'Your account is marked as tax exempt' : 'Enable tax exempt status'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    checked={editedProfile.is_tax_exempt}
                    onCheckedChange={(checked) => setEditedProfile({ ...editedProfile, is_tax_exempt: checked })}
                  />
                </div>

                {editedProfile.is_tax_exempt && (
                  <div>
                    <Label className="text-slate-700">Tax Exempt Document URL</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={editedProfile.tax_exempt_document_url}
                        onChange={(e) => setEditedProfile({ ...editedProfile, tax_exempt_document_url: e.target.value })}
                        placeholder="Link to your tax exempt certificate..."
                        className="flex-1"
                      />
                      {editedProfile.tax_exempt_document_url && (
                        <a href={editedProfile.tax_exempt_document_url} target="_blank" rel="noopener noreferrer">
                          <Button variant="outline">
                            <FileText className="h-4 w-4 mr-2" />
                            View
                          </Button>
                        </a>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      Upload your tax exempt certificate to a file hosting service and paste the link here
                    </p>
                  </div>
                )}

                <div className="pt-4">
                  <Button 
                    className="bg-teal-500 hover:bg-teal-600"
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications */}
          <TabsContent value="notifications">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Notification Preferences</CardTitle>
                <CardDescription>Choose what emails you'd like to receive</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { key: 'email_messages', label: 'New Messages', desc: 'When you receive a new message from the shop' },
                  { key: 'email_orders', label: 'Order Updates', desc: 'Status changes on your orders' },
                  { key: 'email_approvals', label: 'Artwork Proofs', desc: 'When a new proof is ready for review' },
                  { key: 'email_payments', label: 'Payment & Invoices', desc: 'New invoices and payment confirmations' },
                ].map((item) => (
                  <div key={item.key} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Bell className="h-5 w-5 text-slate-400" />
                      <div>
                        <p className="font-medium text-slate-900">{item.label}</p>
                        <p className="text-sm text-slate-500">{item.desc}</p>
                      </div>
                    </div>
                    <Switch
                      checked={editedProfile.notification_preferences?.[item.key] ?? true}
                      onCheckedChange={(checked) => handleNotificationChange(item.key, checked)}
                    />
                  </div>
                ))}

                <div className="pt-4">
                  <Button 
                    className="bg-teal-500 hover:bg-teal-600"
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                    Save Preferences
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security */}
          <TabsContent value="security">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Security</CardTitle>
                <CardDescription>Manage your password</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Lock className="h-5 w-5 text-slate-400" />
                    <div>
                      <p className="font-medium text-slate-900">Password</p>
                      <p className="text-sm text-slate-500">Change your portal password</p>
                    </div>
                  </div>
                  <Button 
                    variant="outline"
                    onClick={() => setShowPasswordDialog(true)}
                  >
                    Change Password
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Change Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label className="text-slate-700">Current Password</Label>
              <Input
                type="password"
                value={passwords.current}
                onChange={(e) => setPasswords({ ...passwords, current: e.target.value })}
                className="mt-1"
              />
            </div>
            <div>
              <Label className="text-slate-700">New Password</Label>
              <Input
                type="password"
                value={passwords.new}
                onChange={(e) => setPasswords({ ...passwords, new: e.target.value })}
                placeholder="Min 6 characters"
                className="mt-1"
              />
            </div>
            <div>
              <Label className="text-slate-700">Confirm New Password</Label>
              <Input
                type="password"
                value={passwords.confirm}
                onChange={(e) => setPasswords({ ...passwords, confirm: e.target.value })}
                className="mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
              Cancel
            </Button>
            <Button 
              className="bg-teal-500 hover:bg-teal-600"
              onClick={handleChangePassword}
              disabled={changingPassword || !passwords.current || !passwords.new || !passwords.confirm}
            >
              {changingPassword && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Change Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PortalLayout>
  );
}
