import { useEffect, useState } from 'react';
import { Zap, Shield, Rocket, Loader2 } from 'lucide-react';
import { getPreferences, updatePreferences } from '../../utils/assistantPrefsApi';

const MODES = [
  { id: 'quick', label: 'Quick', icon: Zap, hint: 'Fewer prompts, run immediately.' },
  { id: 'guided', label: 'Guided', icon: Shield, hint: 'Always confirm before writes.' },
  { id: 'power', label: 'Power', icon: Rocket, hint: 'Show everything, keep me safe.' },
];

/**
 * Small pill group that reads & writes /preferences.
 * Exposes the selected mode up via onChange so the parent can use it in decisions
 * (e.g., skip confirmation in "quick" mode).
 */
export default function AssistantModeSwitcher({ token, value, onChange }) {
  const [mode, setMode] = useState(value || 'guided');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    getPreferences(token)
      .then((d) => {
        if (cancelled) return;
        const m = d?.mode || 'guided';
        setMode(m);
        onChange?.(m);
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const select = async (next) => {
    if (next === mode || saving) return;
    setSaving(true);
    const prev = mode;
    setMode(next);
    onChange?.(next);
    try {
      await updatePreferences(token, { mode: next });
    } catch {
      setMode(prev);
      onChange?.(prev);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="flex items-center gap-0.5 rounded-full bg-violet-100/70 p-0.5 border border-violet-200"
      data-testid="assistant-mode-switcher"
    >
      {MODES.map((m) => {
        const Icon = m.icon;
        const active = mode === m.id;
        return (
          <button
            key={m.id}
            type="button"
            title={m.hint}
            onClick={() => select(m.id)}
            disabled={loading || saving}
            data-testid={`assistant-mode-${m.id}`}
            className={`inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold rounded-full transition ${
              active
                ? 'bg-white text-violet-700 shadow-sm'
                : 'text-violet-600 hover:text-violet-800'
            } ${(loading || saving) ? 'opacity-60' : ''}`}
          >
            {saving && active ? <Loader2 className="h-3 w-3 animate-spin" /> : <Icon className="h-3 w-3" />}
            {m.label}
          </button>
        );
      })}
    </div>
  );
}
