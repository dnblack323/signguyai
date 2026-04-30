/**
 * PlatformAdminBroadcastEmail
 * --------------------------
 * Platform-Admin-only page for sending a one-off email to one or more tenant
 * owners. Always supports a "Send test to me first" mode so the admin can
 * preview the rendered email before committing to the full audience.
 */

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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '../components/ui/dialog';
import { ArrowLeft, Send, AlertTriangle, CheckCircle2, Mail } from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TARGETS = [
  { value: 'all_owners', label: 'All tenant owners' },
  { value: 'active_only', label: 'Only active tenants' },
  { value: 'suspended_only', label: 'Only suspended tenants' },
  { value: 'founders_only', label: 'Only founders' },
];

// Convert a plain-text body into safe-ish HTML (paragraphs by blank line, line
// breaks within paragraphs preserved). Keeps it simple — no markdown parsing.
function plainTextToHtml(text) {
  const escape = (s) => s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim().length > 0);
  return paragraphs
    .map((p) => `<p>${escape(p).replace(/\n/g, '<br/>')}</p>`)
    .join('\n');
}

export default function PlatformAdminBroadcastEmail() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [target, setTarget] = useState('all_owners');
  const [audienceCounts, setAudienceCounts] = useState(null);
  const [testTo, setTestTo] = useState('');
  const [sending, setSending] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  // Guard: platform admin only
  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied: Platform Admin privileges required');
      navigate('/');
    }
  }, [user, navigate]);

  const loadAudienceCounts = useCallback(async () => {
    try {
      const r = await fetch(
        `${BACKEND_URL}/api/platform-admin/broadcast-email/audience-counts`,
        { headers: { Authorization: `Bearer ${getAuthToken()}` } },
      );
      if (r.ok) setAudienceCounts(await r.json());
    } catch {
      // non-fatal
    }
  }, []);

  useEffect(() => {
    if (user?.role === 'platform_admin') {
      loadAudienceCounts();
      // Pre-fill test address with the admin's own email for convenience.
      setTestTo(user.email || '');
    }
  }, [user, loadAudienceCounts]);

  const matchedCount = audienceCounts ? audienceCounts[target] || 0 : null;

  const validate = () => {
    if (!subject.trim()) {
      toast.error('Please enter a subject');
      return false;
    }
    if (!body.trim()) {
      toast.error('Please enter an email body');
      return false;
    }
    return true;
  };

  const sendRequest = async ({ asTest }) => {
    if (!validate()) return null;
    if (asTest && !testTo.trim()) {
      toast.error('Please enter a test recipient');
      return null;
    }
    setSending(true);
    setLastResult(null);
    try {
      const r = await fetch(`${BACKEND_URL}/api/platform-admin/broadcast-email`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject,
          html_body: plainTextToHtml(body),
          target,
          test_to: asTest ? testTo.trim() : null,
        }),
      });
      const data = await r.json();
      if (!r.ok) {
        toast.error(data?.detail || 'Failed to send broadcast email');
        return null;
      }
      setLastResult({ ...data, asTest });
      toast.success(
        asTest
          ? `Test email sent to ${testTo}`
          : `Sent to ${data.sent_count}/${data.matched_recipients} tenants`,
      );
      return data;
    } catch (err) {
      toast.error(err.message || 'Failed to send');
      return null;
    } finally {
      setSending(false);
    }
  };

  const handleSendTest = () => sendRequest({ asTest: true });

  const handleSendBroadcastConfirmed = async () => {
    setConfirmOpen(false);
    await sendRequest({ asTest: false });
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="platform-admin-broadcast-page">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" onClick={() => navigate('/platform-admin')} data-testid="broadcast-back-btn">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <Send className="w-7 h-7 text-blue-600" /> Broadcast Email
            </h1>
            <p className="text-gray-600">Send a one-off email to one or more tenant owners.</p>
          </div>
        </div>

        {/* Compose */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Mail className="w-4 h-4" /> Compose</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium block mb-1">Subject</label>
              <Input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., New feature: Customer Branding Profile"
                data-testid="broadcast-subject-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium block mb-1">Body (plain text)</label>
              <Textarea
                rows={10}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder={'Hi {tenant owner},\n\nA quick update from the SignGuy AI team...\n\nBlank lines start a new paragraph.'}
                data-testid="broadcast-body-textarea"
              />
              <p className="text-xs text-gray-500 mt-1">
                Plain-text input is auto-wrapped in HTML paragraphs. Blank lines create new paragraphs; single newlines become line breaks.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium block mb-1">Audience</label>
                <Select value={target} onValueChange={setTarget}>
                  <SelectTrigger data-testid="broadcast-audience-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TARGETS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="text-xs text-gray-500 mt-1">
                  {matchedCount !== null ? (
                    <>This will email <strong>{matchedCount}</strong> tenant owner{matchedCount === 1 ? '' : 's'}.</>
                  ) : (
                    'Loading audience count...'
                  )}
                </div>
              </div>

              <div>
                <label className="text-sm font-medium block mb-1">Test recipient</label>
                <Input
                  value={testTo}
                  onChange={(e) => setTestTo(e.target.value)}
                  placeholder="you@example.com"
                  data-testid="broadcast-test-to-input"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Used by "Send test to me" only. Won't be emailed when sending the broadcast.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Button
                variant="outline"
                onClick={handleSendTest}
                disabled={sending}
                data-testid="broadcast-send-test-btn"
              >
                <Send className="w-4 h-4 mr-1" /> Send test to {testTo || '...'}
              </Button>
              <Button
                onClick={() => setConfirmOpen(true)}
                disabled={sending || !matchedCount}
                data-testid="broadcast-send-broadcast-btn"
              >
                <Send className="w-4 h-4 mr-1" /> Send to {matchedCount ?? '?'} tenants
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Result */}
        {lastResult && (
          <Card className="mt-6 border-green-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-800">
                <CheckCircle2 className="w-4 h-4" /> Last send result
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <Badge variant="outline">{lastResult.asTest ? 'Test send' : 'Broadcast'}</Badge>
              </div>
              <div>Matched recipients: <strong>{lastResult.matched_recipients}</strong></div>
              <div>Successfully sent: <strong className="text-green-700">{lastResult.sent_count}</strong></div>
              <div>Failed: <strong className={lastResult.failed_count ? 'text-red-700' : ''}>{lastResult.failed_count}</strong></div>
              {lastResult.failed?.length > 0 && (
                <div className="mt-2 text-xs">
                  <div className="font-medium text-red-700 mb-1">First failures:</div>
                  <ul className="list-disc pl-5 space-y-0.5">
                    {lastResult.failed.map((f, i) => (
                      <li key={i}><code>{f.email}</code> — {f.error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Confirm dialog */}
        <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <DialogContent data-testid="broadcast-confirm-dialog">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-700">
                <AlertTriangle className="w-5 h-5" /> Send to {matchedCount} tenant owner{matchedCount === 1 ? '' : 's'}?
              </DialogTitle>
              <DialogDescription>
                This will send the email to every tenant owner matching the audience filter.
                This action is logged in the Admin Audit Log and cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="text-sm bg-gray-50 p-3 rounded space-y-1">
              <div><span className="text-gray-500">Subject:</span> <strong>{subject}</strong></div>
              <div><span className="text-gray-500">Audience:</span> <strong>{TARGETS.find(t => t.value === target)?.label}</strong></div>
              <div><span className="text-gray-500">Recipients:</span> <strong>{matchedCount}</strong></div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setConfirmOpen(false)}>Cancel</Button>
              <Button onClick={handleSendBroadcastConfirmed} disabled={sending} data-testid="broadcast-confirm-send-btn">
                <Send className="w-4 h-4 mr-1" /> Yes, send now
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
