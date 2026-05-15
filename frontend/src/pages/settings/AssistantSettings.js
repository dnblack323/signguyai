import { useEffect, useState, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Switch } from '../../components/ui/switch';
import { Label } from '../../components/ui/label';
import { Loader2, Sparkles, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

/**
 * AI Assistant Settings — pick a personality and toggle low-risk action
 * auto-confirmation.
 *
 * Backend:
 *   GET /api/ai/assistant/personality → { selected, skip_confirm, options[] }
 *   PUT /api/ai/assistant/personality   { personality?, skip_confirm? }
 */
export default function AssistantSettings() {
  const { api } = useApp();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState('ops_partner');
  const [skipConfirm, setSkipConfirm] = useState([]);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/ai/assistant/personality');
      setOptions(data.options || []);
      setSelected(data.selected || 'ops_partner');
      setSkipConfirm(data.skip_confirm || []);
    } catch (err) {
      toast.error('Failed to load assistant settings');
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { load(); }, [load]);

  const choose = async (key) => {
    setSelected(key);
    setSaving(true);
    try {
      await api.put('/ai/assistant/personality', { personality: key });
      toast.success('Personality updated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const toggleSkip = async (action_type, checked) => {
    const next = checked
      ? Array.from(new Set([...skipConfirm, action_type]))
      : skipConfirm.filter((a) => a !== action_type);
    setSkipConfirm(next);
    try {
      await api.put('/ai/assistant/personality', { skip_confirm: next });
    } catch (err) {
      toast.error('Failed to save preference');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6" data-testid="assistant-settings-page">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-500" /> AI Assistant
        </h1>
        <p className="text-slate-500 text-sm mt-1">
          Pick how your assistant talks to you. You can change this anytime.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Personality</CardTitle>
          <CardDescription>Choose the voice that fits how you work.</CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-2 gap-3">
          {options.map((opt) => {
            const active = selected === opt.key;
            return (
              <button
                key={opt.key}
                type="button"
                onClick={() => choose(opt.key)}
                disabled={saving}
                className={`text-left rounded-lg border p-4 transition ${
                  active
                    ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-300'
                    : 'border-slate-200 hover:border-purple-300'
                }`}
                data-testid={`personality-option-${opt.key}`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-slate-900">{opt.name}</span>
                  {active && <CheckCircle2 className="h-4 w-4 text-purple-600" />}
                </div>
                <p className="text-xs text-slate-600">{opt.tagline}</p>
                {opt.default && !active && (
                  <p className="text-[10px] text-slate-400 mt-1">Default</p>
                )}
              </button>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" /> Confirmation preferences
          </CardTitle>
          <CardDescription>
            Skip the confirmation for low-risk drafts. Charging cards, sending invoices,
            and any payment action always require a confirm.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between gap-4 border rounded-md p-3">
            <div className="space-y-0.5">
              <Label className="text-sm font-medium" htmlFor="skip-draft-email">
                Auto-open email drafts
              </Label>
              <p className="text-xs text-slate-500">
                {'When you say "email <customer>", jump straight to the draft instead of asking first.'}
              </p>
            </div>
            <Switch
              id="skip-draft-email"
              checked={skipConfirm.includes('draft_email')}
              onCheckedChange={(v) => toggleSkip('draft_email', v)}
              data-testid="skip-draft-email-toggle"
            />
          </div>
        </CardContent>
      </Card>

      <p className="text-xs text-slate-400 text-center pt-2">
        Voice & memory improvements are on the roadmap. Today this controls tone + skip-confirm only.
      </p>

      {saving && (
        <div className="fixed bottom-4 right-4 bg-slate-900 text-white text-xs px-3 py-2 rounded-md flex items-center gap-2 shadow-lg">
          <Loader2 className="h-3 w-3 animate-spin" /> Saving…
        </div>
      )}

      <div className="flex justify-end">
        <Button
          variant="outline"
          onClick={() => window.history.back()}
          data-testid="assistant-settings-back"
        >
          Back
        </Button>
      </div>
    </div>
  );
}
