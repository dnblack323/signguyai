import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  ArrowLeft,
  Megaphone,
  Wrench,
  Save,
  Trash2,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function formatDateTime(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

export default function PlatformAdminSiteSettings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [announcement, setAnnouncement] = useState(null);
  const [maintenance, setMaintenance] = useState({ enabled: false });

  // Form state
  const [annMessage, setAnnMessage] = useState('');
  const [annSeverity, setAnnSeverity] = useState('info');
  const [annDismissable, setAnnDismissable] = useState(true);
  const [annExpiresAt, setAnnExpiresAt] = useState('');
  const [savingAnn, setSavingAnn] = useState(false);
  const [clearingAnn, setClearingAnn] = useState(false);

  const [maintMessage, setMaintMessage] = useState('');
  const [savingMaint, setSavingMaint] = useState(false);

  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied');
      navigate('/');
    }
  }, [user, navigate]);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const token = getAuthToken();
      if (!token) { navigate('/login'); return; }
      const r = await fetch(`${BACKEND_URL}/api/platform-admin/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error('Failed to load settings');
      const data = await r.json();
      setAnnouncement(data.announcement || null);
      setMaintenance(data.maintenance || { enabled: false });

      // Hydrate the form
      if (data.announcement) {
        setAnnMessage(data.announcement.message || '');
        setAnnSeverity(data.announcement.severity || 'info');
        setAnnDismissable(data.announcement.dismissable !== false);
        setAnnExpiresAt(data.announcement.expires_at || '');
      }
      setMaintMessage((data.maintenance && data.maintenance.message) || '');
    } catch (err) {
      console.error(err);
      toast.error('Failed to load site settings');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    if (user?.role === 'platform_admin') fetchSettings();
  }, [user, fetchSettings]);

  const handleSaveAnnouncement = async () => {
    if (!annMessage.trim()) {
      toast.error('Message is required (use the Clear button to remove the banner)');
      return;
    }
    setSavingAnn(true);
    try {
      const token = getAuthToken();
      const r = await fetch(`${BACKEND_URL}/api/platform-admin/announcement`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: annMessage.trim(),
          severity: annSeverity,
          dismissable: annDismissable,
          expires_at: annExpiresAt || null,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || 'Failed to save');
      toast.success('Announcement live');
      setAnnouncement(data.announcement);
    } catch (err) {
      toast.error(err.message || 'Failed to save announcement');
    } finally {
      setSavingAnn(false);
    }
  };

  const handleClearAnnouncement = async () => {
    setClearingAnn(true);
    try {
      const token = getAuthToken();
      const r = await fetch(`${BACKEND_URL}/api/platform-admin/announcement`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: '' }),
      });
      if (!r.ok) throw new Error('Failed to clear');
      toast.success('Announcement cleared');
      setAnnouncement(null);
      setAnnMessage('');
      setAnnExpiresAt('');
      setAnnSeverity('info');
      setAnnDismissable(true);
    } catch (err) {
      toast.error(err.message || 'Failed to clear announcement');
    } finally {
      setClearingAnn(false);
    }
  };

  const setMaint = async (enabled) => {
    setSavingMaint(true);
    try {
      const token = getAuthToken();
      const r = await fetch(`${BACKEND_URL}/api/platform-admin/maintenance`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          enabled,
          message: maintMessage.trim() || null,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || 'Failed');
      toast.success(enabled ? 'Maintenance mode ON' : 'Maintenance mode OFF');
      setMaintenance(data.maintenance);
    } catch (err) {
      toast.error(err.message || 'Failed to update maintenance mode');
    } finally {
      setSavingMaint(false);
    }
  };

  if (user?.role !== 'platform_admin') return null;

  const announcementActive = !!(announcement && announcement.message);

  return (
    <div className="min-h-screen bg-gray-50 p-6" data-testid="site-settings-page">
      <div className="max-w-5xl mx-auto">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/platform-admin')}
          className="mb-2"
          data-testid="site-settings-back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Platform Admin
        </Button>
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheck className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Site Settings</h1>
            <p className="text-gray-600">Global announcement banner & maintenance mode.</p>
          </div>
        </div>

        {loading ? (
          <Card><CardContent className="py-12 text-center text-gray-500">Loading…</CardContent></Card>
        ) : (
          <div className="space-y-6">
            {/* Announcement */}
            <Card data-testid="site-settings-announcement-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Megaphone className="w-5 h-5 text-blue-600" /> Announcement Banner
                  {announcementActive && (
                    <Badge variant="outline" className="bg-emerald-100 text-emerald-900 border-emerald-300 ml-2">
                      Live
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-gray-700 block mb-1">Message</label>
                  <Textarea
                    value={annMessage}
                    onChange={(e) => setAnnMessage(e.target.value)}
                    rows={2}
                    placeholder="e.g., We're deploying a new release at 11pm ET tonight."
                    data-testid="site-settings-announcement-message"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-medium text-gray-700 block mb-1">Severity</label>
                    <Select value={annSeverity} onValueChange={setAnnSeverity}>
                      <SelectTrigger data-testid="site-settings-announcement-severity">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="info">Info (blue)</SelectItem>
                        <SelectItem value="warning">Warning (amber)</SelectItem>
                        <SelectItem value="critical">Critical (red)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-700 block mb-1">
                      Auto-expire (optional, ISO date-time)
                    </label>
                    <Input
                      value={annExpiresAt}
                      onChange={(e) => setAnnExpiresAt(e.target.value)}
                      placeholder="2026-12-31T23:59:00+00:00"
                      data-testid="site-settings-announcement-expires"
                    />
                  </div>
                  <div className="flex items-end">
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={annDismissable}
                        onChange={(e) => setAnnDismissable(e.target.checked)}
                        data-testid="site-settings-announcement-dismissable"
                      />
                      Allow users to dismiss
                    </label>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={handleSaveAnnouncement}
                    disabled={savingAnn || !annMessage.trim()}
                    data-testid="site-settings-announcement-save-btn"
                  >
                    <Save className="w-4 h-4 mr-1" />
                    {savingAnn ? 'Saving…' : announcementActive ? 'Update' : 'Publish'}
                  </Button>
                  {announcementActive && (
                    <Button
                      variant="outline"
                      onClick={handleClearAnnouncement}
                      disabled={clearingAnn}
                      data-testid="site-settings-announcement-clear-btn"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      {clearingAnn ? 'Clearing…' : 'Clear banner'}
                    </Button>
                  )}
                </div>
                {announcementActive && (
                  <p className="text-xs text-gray-500">
                    Last updated {formatDateTime(announcement.updated_at)}
                    {announcement.updated_by_email && ` by ${announcement.updated_by_email}`}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Maintenance */}
            <Card
              className={maintenance.enabled ? 'border-rose-200' : ''}
              data-testid="site-settings-maintenance-card"
            >
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wrench className="w-5 h-5 text-rose-600" /> Maintenance Mode
                  {maintenance.enabled && (
                    <Badge
                      variant="outline"
                      className="bg-rose-100 text-rose-900 border-rose-300 ml-2"
                      data-testid="site-settings-maintenance-on-badge"
                    >
                      ON
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm text-gray-700 bg-amber-50 border border-amber-200 rounded p-3 flex gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-700 mt-0.5 shrink-0" />
                  <div>
                    While maintenance mode is on, all <strong>write</strong> requests
                    (POST / PUT / PATCH / DELETE) for non-admin users are blocked with
                    HTTP 503. Reads, the auth flow, the Platform Admin area and external
                    webhooks (Stripe, SendGrid) keep working.
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-700 block mb-1">
                    Banner message (shown to users)
                  </label>
                  <Input
                    value={maintMessage}
                    onChange={(e) => setMaintMessage(e.target.value)}
                    placeholder="Routine maintenance — back in 15 minutes"
                    data-testid="site-settings-maintenance-message"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  {maintenance.enabled ? (
                    <Button
                      className="bg-emerald-600 hover:bg-emerald-700"
                      onClick={() => setMaint(false)}
                      disabled={savingMaint}
                      data-testid="site-settings-maintenance-disable-btn"
                    >
                      Disable Maintenance Mode
                    </Button>
                  ) : (
                    <Button
                      variant="destructive"
                      onClick={() => setMaint(true)}
                      disabled={savingMaint}
                      data-testid="site-settings-maintenance-enable-btn"
                    >
                      <Wrench className="w-4 h-4 mr-1" />
                      Enable Maintenance Mode
                    </Button>
                  )}
                </div>
                {maintenance.enabled && (
                  <p className="text-xs text-gray-500">
                    Started {formatDateTime(maintenance.started_at)}
                    {maintenance.started_by_email && ` by ${maintenance.started_by_email}`}
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
