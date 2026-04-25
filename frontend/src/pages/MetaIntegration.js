import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
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
} from '../components/ui/dialog';
import {
  AlertTriangle, CheckCircle, Link2, Link2Off, RefreshCw,
  MessageSquare, Zap, Settings, ExternalLink, Facebook, Loader2, Info
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const authHeader = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const CREATE_MODE_OPTIONS = [
  { value: 'lead', label: 'Draft Lead (recommended)' },
  { value: 'draft_order', label: 'Draft Order' },
  { value: 'message_only', label: 'Message Only (no auto-create)' },
];

export default function MetaIntegration() {
  const { user } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [pageSelectOpen, setPageSelectOpen] = useState(false);
  const [availablePages, setAvailablePages] = useState([]);
  const [tmpToken, setTmpToken] = useState(null);
  const [loadingPages, setLoadingPages] = useState(false);
  const [connectingPage, setConnectingPage] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/integrations/meta/status`, { headers: authHeader() });
      setStatus(res.data);
    } catch {
      toast.error('Failed to load Meta integration status');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    // Handle OAuth callback query params
    const params = new URLSearchParams(window.location.search);
    const oauthSuccess = params.get('oauth_success');
    const tmp = params.get('tmp');
    const error = params.get('error');

    if (error) {
      toast.error(`Facebook connection failed: ${params.get('error_desc') || error}`);
      window.history.replaceState({}, '', window.location.pathname);
    } else if (oauthSuccess && tmp) {
      setTmpToken(tmp);
      setPageSelectOpen(true);
      window.history.replaceState({}, '', window.location.pathname);
      loadAvailablePages(tmp);
    }
  }, [fetchStatus]);

  const loadAvailablePages = async (tmp) => {
    setLoadingPages(true);
    try {
      const res = await axios.get(`${API_URL}/api/integrations/meta/pages`, {
        params: { tmp },
        headers: authHeader(),
      });
      setAvailablePages(res.data.pages || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to fetch your Facebook Pages');
      setPageSelectOpen(false);
    } finally {
      setLoadingPages(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const res = await axios.post(`${API_URL}/api/integrations/meta/connect/start`, {}, { headers: authHeader() });
      window.location.href = res.data.auth_url;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start Facebook connection');
      setConnecting(false);
    }
  };

  const handleConnectPage = async (page) => {
    setConnectingPage(page.id);
    try {
      await axios.post(
        `${API_URL}/api/integrations/meta/pages/connect`,
        {
          page_id: page.id,
          page_name: page.name,
          page_access_token: page.access_token,
          category: page.category,
          ai_enabled: true,
          create_mode: 'lead',
        },
        { headers: authHeader() }
      );
      toast.success(`"${page.name}" connected successfully`);
      setPageSelectOpen(false);
      await fetchStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to connect page');
    } finally {
      setConnectingPage(null);
    }
  };

  const handleDisconnect = async (page) => {
    if (!window.confirm(`Disconnect "${page.page_name}"? Existing messages will be preserved.`)) return;
    try {
      await axios.delete(`${API_URL}/api/integrations/meta/pages/${page.page_id}`, { headers: authHeader() });
      toast.success(`"${page.page_name}" disconnected`);
      await fetchStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to disconnect page');
    }
  };

  const handleSettingChange = async (pageId, field, value) => {
    try {
      await axios.patch(
        `${API_URL}/api/integrations/meta/pages/${pageId}/settings`,
        { [field]: value },
        { headers: authHeader() }
      );
      await fetchStatus();
    } catch {
      toast.error('Failed to update settings');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const connectedPages = (status?.pages || []).filter(p => p.status === 'active');
  const disconnectedPages = (status?.pages || []).filter(p => p.status !== 'active');

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Facebook className="h-6 w-6 text-blue-600" />
            Facebook / Meta Messenger
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Connect your Facebook Business Pages to receive and process quote requests via Messenger.
          </p>
        </div>
        <Button
          onClick={handleConnect}
          disabled={connecting || !status?.app_configured}
          className="bg-blue-600 hover:bg-blue-700 text-white"
          data-testid="meta-connect-btn"
        >
          {connecting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Link2 className="h-4 w-4 mr-2" />}
          Connect Facebook Page
        </Button>
      </div>

      {/* App not configured warning */}
      {!status?.app_configured && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-4 pb-4">
            <div className="flex gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-amber-800 text-sm">Meta App Not Configured</p>
                <p className="text-amber-700 text-xs mt-1">
                  Add <code className="bg-amber-100 px-1 rounded">META_APP_ID</code> and{' '}
                  <code className="bg-amber-100 px-1 rounded">META_APP_SECRET</code> to your{' '}
                  <code className="bg-amber-100 px-1 rounded">.env</code> file, then restart the server.
                  See setup instructions below.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connected pages */}
      {connectedPages.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
            Connected Pages
          </h3>
          {connectedPages.map(page => (
            <PageCard
              key={page.page_id}
              page={page}
              onDisconnect={() => handleDisconnect(page)}
              onSettingChange={handleSettingChange}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {connectedPages.length === 0 && status?.app_configured && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <Facebook className="h-10 w-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No Pages connected yet</p>
            <p className="text-gray-400 text-sm mt-1">
              Click "Connect Facebook Page" to link your business Page inbox.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Disconnected/inactive pages */}
      {disconnectedPages.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Disconnected Pages
          </h3>
          {disconnectedPages.map(page => (
            <div key={page.page_id} className="flex items-center justify-between p-3 rounded-lg border border-dashed bg-gray-50">
              <div>
                <p className="font-medium text-gray-600 text-sm">{page.page_name}</p>
                <p className="text-xs text-gray-400">{page.page_id}</p>
              </div>
              <Badge variant="outline" className="text-gray-400">Disconnected</Badge>
            </div>
          ))}
        </div>
      )}

      {/* Setup Instructions */}
      <SetupInstructions />

      {/* Page Select Modal */}
      <Dialog open={pageSelectOpen} onOpenChange={setPageSelectOpen}>
        <DialogContent className="max-w-lg" data-testid="page-select-modal">
          <DialogHeader>
            <DialogTitle>Select Facebook Pages to Connect</DialogTitle>
          </DialogHeader>
          {loadingPages ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : availablePages.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
              <p className="text-gray-600 font-medium">No Pages Found</p>
              <p className="text-gray-400 text-sm mt-1">
                Your Facebook account does not manage any Pages, or the required permissions were not granted.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {availablePages.map(page => (
                <div
                  key={page.id}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-blue-50 hover:border-blue-200 transition-colors"
                >
                  <div>
                    <p className="font-medium text-sm">{page.name}</p>
                    <p className="text-xs text-gray-400">{page.category} · ID: {page.id}</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleConnectPage(page)}
                    disabled={connectingPage === page.id}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    data-testid={`connect-page-${page.id}`}
                  >
                    {connectingPage === page.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Connect'
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Page Card Component ────────────────────────────────────────────────────────
function PageCard({ page, onDisconnect, onSettingChange }) {
  return (
    <Card className="border-green-200 bg-green-50/40">
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
              <Facebook className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold text-sm" data-testid="page-name">{page.page_name}</p>
                <Badge className="bg-green-100 text-green-700 border-green-200 text-xs">Active</Badge>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">Page ID: {page.page_id}</p>
              {page.last_webhook_at && (
                <p className="text-xs text-gray-400">
                  Last message: {new Date(page.last_webhook_at).toLocaleString()}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs text-gray-400">{page.message_count || 0} messages</span>
            <Button
              variant="ghost"
              size="sm"
              className="text-red-500 hover:text-red-700"
              onClick={onDisconnect}
              data-testid={`disconnect-page-${page.page_id}`}
            >
              <Link2Off className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Page settings */}
        <div className="mt-4 pt-3 border-t border-green-200 grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-gray-600">AI Message Scanning</Label>
            <Switch
              checked={page.ai_enabled !== false}
              onCheckedChange={v => onSettingChange(page.page_id, 'ai_enabled', v)}
              data-testid={`ai-enabled-${page.page_id}`}
            />
          </div>
          <div>
            <Label className="text-xs text-gray-600 mb-1 block">On Quote Request, Create:</Label>
            <Select
              value={page.create_mode || 'lead'}
              onValueChange={v => onSettingChange(page.page_id, 'create_mode', v)}
            >
              <SelectTrigger className="h-7 text-xs" data-testid={`create-mode-${page.page_id}`}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CREATE_MODE_OPTIONS.map(o => (
                  <SelectItem key={o.value} value={o.value} className="text-xs">{o.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {page.webhook_subscribed === false && (
          <div className="mt-3 flex items-center gap-2 text-amber-600 text-xs">
            <AlertTriangle className="h-3.5 w-3.5" />
            Webhook not subscribed — messages may not be received. Reconnect to fix.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Setup Instructions ─────────────────────────────────────────────────────────
function SetupInstructions() {
  const [open, setOpen] = useState(false);
  return (
    <Card className="border-blue-100">
      <CardHeader className="pb-2 pt-4 cursor-pointer" onClick={() => setOpen(o => !o)}>
        <CardTitle className="text-sm flex items-center gap-2 font-medium">
          <Info className="h-4 w-4 text-blue-500" />
          Meta App Setup Instructions
          <span className="text-xs text-blue-500 ml-auto">{open ? 'Hide' : 'Show'}</span>
        </CardTitle>
      </CardHeader>
      {open && (
        <CardContent className="pt-0 pb-4 text-sm text-gray-600 space-y-3">
          <ol className="list-decimal list-inside space-y-2">
            <li>
              Go to{' '}
              <a href="https://developers.facebook.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline inline-flex items-center gap-1">
                developers.facebook.com <ExternalLink className="h-3 w-3" />
              </a>{' '}
              and create a new App (type: <strong>Business</strong>).
            </li>
            <li>Under <strong>Products</strong>, add <strong>Messenger</strong>.</li>
            <li>
              In App Settings → Basic, copy your <strong>App ID</strong> and <strong>App Secret</strong>.
              Add them to <code className="bg-gray-100 px-1 rounded text-xs">/app/backend/.env</code>:
              <pre className="bg-gray-100 rounded p-2 text-xs mt-1 overflow-x-auto">
{`META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here`}
              </pre>
            </li>
            <li>
              In <strong>Facebook Login for Business</strong>, set the Valid OAuth Redirect URI to:
              <pre className="bg-gray-100 rounded p-2 text-xs mt-1 overflow-x-auto">
                {`${process.env.REACT_APP_BACKEND_URL}/api/integrations/meta/oauth/callback`}
              </pre>
            </li>
            <li>
              In <strong>Webhooks</strong>, subscribe to Page events, set the Callback URL to:
              <pre className="bg-gray-100 rounded p-2 text-xs mt-1 overflow-x-auto">
                {`${process.env.REACT_APP_BACKEND_URL}/api/integrations/meta/webhook`}
              </pre>
              Use verify token: <code className="bg-gray-100 px-1 rounded text-xs font-mono">signguy_meta_webhook_2026</code>
            </li>
            <li>Subscribe to: <strong>messages</strong>, <strong>messaging_postbacks</strong>.</li>
            <li>Restart the backend server after updating .env.</li>
          </ol>
        </CardContent>
      )}
    </Card>
  );
}
