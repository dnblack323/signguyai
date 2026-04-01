import { useEffect, useState, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import {
  Mail, Clock, Plus, Trash2, Send, Loader2, CheckCircle, History
} from 'lucide-react';
import { toast } from 'sonner';

export default function DigestSettings() {
  const { api } = useApp();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [settings, setSettings] = useState({
    enabled: false,
    schedule_time: '07:00',
    recipients: [],
  });
  const [newEmail, setNewEmail] = useState('');
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const loadSettings = useCallback(async () => {
    try {
      const [settingsRes, historyRes] = await Promise.all([
        api.get('/digest/settings'),
        api.get('/digest/history?limit=5'),
      ]);
      setSettings(settingsRes.data);
      setHistory(historyRes.data || []);
    } catch (err) {
      console.error('Failed to load digest settings', err);
    }
    setLoading(false);
  }, [api]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const saveSettings = async (updates) => {
    setSaving(true);
    try {
      const res = await api.put('/digest/settings', updates);
      setSettings(res.data);
      toast.success('Digest settings saved');
    } catch (err) {
      toast.error('Failed to save settings');
    }
    setSaving(false);
  };

  const addRecipient = () => {
    const email = newEmail.trim().toLowerCase();
    if (!email || !email.includes('@')) {
      toast.error('Please enter a valid email address');
      return;
    }
    if (settings.recipients.includes(email)) {
      toast.error('Email already added');
      return;
    }
    const updated = [...settings.recipients, email];
    setSettings(prev => ({ ...prev, recipients: updated }));
    saveSettings({ recipients: updated });
    setNewEmail('');
  };

  const removeRecipient = (email) => {
    const updated = settings.recipients.filter(e => e !== email);
    setSettings(prev => ({ ...prev, recipients: updated }));
    saveSettings({ recipients: updated });
  };

  const sendNow = async () => {
    setSending(true);
    try {
      const res = await api.post('/digest/send');
      toast.success(res.data.message || 'Digest sent!');
      loadSettings();
    } catch (err) {
      toast.error('Failed to send digest');
    }
    setSending(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="digest-settings">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white font-heading">Daily Digest</h1>
          <p className="text-sm text-gray-400 mt-1">
            Receive a morning email summary of your shop's daily status
          </p>
        </div>
        <Button
          onClick={sendNow}
          disabled={sending || settings.recipients.length === 0}
          data-testid="send-digest-now-btn"
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {sending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
          Send Now
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schedule Settings */}
        <Card className="bg-white border-gray-200">
          <CardHeader>
            <CardTitle className="text-base text-gray-900 flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-500" />
              Schedule
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-sm font-medium text-gray-900">Enable Daily Digest</Label>
                <p className="text-xs text-gray-500 mt-0.5">
                  Automatically send the digest email at the scheduled time
                </p>
              </div>
              <Switch
                checked={settings.enabled}
                onCheckedChange={(checked) => {
                  setSettings(prev => ({ ...prev, enabled: checked }));
                  saveSettings({ enabled: checked });
                }}
                data-testid="digest-enabled-toggle"
              />
            </div>

            <div>
              <Label className="text-sm font-medium text-gray-900">Send Time (UTC)</Label>
              <Input
                type="time"
                value={settings.schedule_time}
                onChange={(e) => {
                  setSettings(prev => ({ ...prev, schedule_time: e.target.value }));
                }}
                onBlur={() => saveSettings({ schedule_time: settings.schedule_time })}
                className="mt-1.5 w-40 bg-white border-gray-300 text-gray-900"
                data-testid="digest-schedule-time"
              />
              <p className="text-xs text-gray-500 mt-1">
                Time is in UTC. The digest will be sent at this time every day.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Recipients */}
        <Card className="bg-white border-gray-200">
          <CardHeader>
            <CardTitle className="text-base text-gray-900 flex items-center gap-2">
              <Mail className="h-5 w-5 text-purple-500" />
              Recipients
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                type="email"
                placeholder="Enter email address"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addRecipient()}
                className="bg-white border-gray-300 text-gray-900 placeholder:text-gray-400"
                data-testid="digest-add-email-input"
              />
              <Button
                onClick={addRecipient}
                size="sm"
                className="bg-purple-600 hover:bg-purple-700 text-white px-3"
                data-testid="digest-add-email-btn"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {settings.recipients.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No recipients added yet. Add at least one email to enable the digest.
              </p>
            ) : (
              <div className="space-y-2">
                {settings.recipients.map((email) => (
                  <div
                    key={email}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-gray-50 border border-gray-200"
                    data-testid={`digest-recipient-${email}`}
                  >
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-800">{email}</span>
                    </div>
                    <button
                      onClick={() => removeRecipient(email)}
                      className="p-1 hover:bg-red-50 rounded text-gray-400 hover:text-red-500 transition-colors"
                      data-testid={`digest-remove-${email}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Digest Preview Info */}
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-base text-gray-900 flex items-center gap-2">
            <Mail className="h-5 w-5 text-emerald-500" />
            What's Included in the Digest
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: 'Employees Scheduled Today', icon: '👥' },
              { label: 'Jobs Due Today', icon: '📋' },
              { label: 'Overdue Invoices', icon: '⚠️' },
              { label: 'Pending Approvals', icon: '✅' },
              { label: "Yesterday's Revenue", icon: '💰' },
              { label: 'Unread Messages', icon: '💬' },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 p-3 rounded-lg bg-gray-50 border border-gray-100"
              >
                <span className="text-lg">{item.icon}</span>
                <span className="text-sm text-gray-700">{item.label}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Send History */}
      <Card className="bg-white border-gray-200">
        <CardHeader className="cursor-pointer" onClick={() => setShowHistory(!showHistory)}>
          <CardTitle className="text-base text-gray-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-gray-500" />
              Recent Sends
            </div>
            <span className="text-xs text-gray-400">{showHistory ? 'Hide' : 'Show'}</span>
          </CardTitle>
        </CardHeader>
        {showHistory && (
          <CardContent>
            {history.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No digests sent yet</p>
            ) : (
              <div className="space-y-2">
                {history.map((log) => (
                  <div key={log.id || log.sent_at} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 border border-gray-100">
                    <div>
                      <p className="text-sm text-gray-800">
                        {new Date(log.sent_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                        {' '}at{' '}
                        {new Date(log.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      <p className="text-xs text-gray-500">
                        {log.type === 'scheduled' ? 'Auto-scheduled' : `Sent by ${log.triggered_by}`}
                        {' · '}
                        {log.recipients?.length || 0} recipient{(log.recipients?.length || 0) !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}
