/**
 * CustomerBrandingTab — embedded inside the customer detail drawer.
 * Displays the saved branding profile and a few CTAs to push it into
 * the AI tools (Logo Creator / Branding Kit Generator / Idea Brainstormer).
 */

import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Palette, Wand2, PenTool, Lightbulb, Save, X } from 'lucide-react';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const headers = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const TEXT_FIELDS = [
  ['business_name', 'Business / Brand Name'],
  ['industry', 'Industry'],
  ['target_audience', 'Target Audience'],
  ['brand_personality', 'Brand Personality'],
  ['competitors', 'Competitors'],
  ['differentiation', 'Differentiation / USP'],
  ['things_to_avoid', 'Things to Avoid'],
  ['brand_voice_notes', 'Brand Voice Notes'],
];

const fmt = (iso) => {
  if (!iso) return '';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
};

export default function CustomerBrandingTab({ customerId }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/customers/${customerId}/branding`, { headers: headers() });
      setProfile(r.data || {});
      setDraft(r.data || {});
    } catch (err) {
      console.error('Load branding failed', err);
      setProfile({});
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const r = await axios.put(`${API}/customers/${customerId}/branding`, draft, {
        headers: headers(),
      });
      setProfile(r.data);
      setDraft(r.data);
      setEditing(false);
      toast.success('Branding profile saved');
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || 'Failed to save branding profile');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveLogo = async (logoId) => {
    if (!profile?.logos) return;
    const next = { ...profile, logos: profile.logos.filter((l) => l.id !== logoId) };
    setSaving(true);
    try {
      const r = await axios.put(`${API}/customers/${customerId}/branding`, next, {
        headers: headers(),
      });
      setProfile(r.data);
      setDraft(r.data);
      toast.success('Logo removed');
    } catch (err) {
      toast.error('Failed to remove logo');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveTagline = async (tagline) => {
    if (!profile?.taglines) return;
    const next = {
      ...profile,
      taglines: profile.taglines.filter((t) => t !== tagline),
      selected_tagline: profile.selected_tagline === tagline ? null : profile.selected_tagline,
    };
    setSaving(true);
    try {
      const r = await axios.put(`${API}/customers/${customerId}/branding`, next, {
        headers: headers(),
      });
      setProfile(r.data);
      setDraft(r.data);
    } catch {
      toast.error('Failed to remove tagline');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="py-8 text-sm text-gray-500 text-center">Loading branding profile…</div>;
  }

  const isEmpty =
    !profile?.business_name &&
    !profile?.brand_kit_text &&
    !(profile?.taglines || []).length &&
    !(profile?.logos || []).length &&
    !(profile?.brand_colors || []).length;

  return (
    <div className="space-y-4" data-testid="customer-branding-tab">
      {/* CTAs */}
      <div className="flex flex-wrap gap-2">
        <Link to={`/ai-tools?tool=branding_kit_generator&customer=${customerId}`}>
          <Button size="sm" variant="outline" data-testid="branding-tab-cta-kit">
            <Palette className="w-4 h-4 mr-1" /> Create Brand Kit
          </Button>
        </Link>
        <Link to={`/ai-tools?tool=logo_creator&customer=${customerId}`}>
          <Button size="sm" variant="outline" data-testid="branding-tab-cta-logo">
            <PenTool className="w-4 h-4 mr-1" /> Logo Concepts
          </Button>
        </Link>
        <Link to={`/ai-tools?tool=idea_brainstormer&customer=${customerId}`}>
          <Button size="sm" variant="outline" data-testid="branding-tab-cta-ideas">
            <Lightbulb className="w-4 h-4 mr-1" /> Brainstorm Ideas
          </Button>
        </Link>
        <div className="flex-1" />
        {!editing ? (
          <Button size="sm" variant="ghost" onClick={() => setEditing(true)} data-testid="branding-tab-edit-btn">
            Edit
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => { setDraft(profile); setEditing(false); }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving} data-testid="branding-tab-save-btn">
              <Save className="w-4 h-4 mr-1" /> {saving ? 'Saving…' : 'Save'}
            </Button>
          </div>
        )}
      </div>

      {isEmpty && !editing && (
        <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
          <Wand2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="font-medium">No branding info saved yet.</p>
          <p className="text-xs mt-1">
            Use the AI tools above (with this customer selected) to generate ideas
            and save them here.
          </p>
        </div>
      )}

      {/* Text fields */}
      {(!isEmpty || editing) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {TEXT_FIELDS.map(([key, label]) => (
            <div key={key}>
              <label className="text-xs font-medium text-gray-700 block mb-1">{label}</label>
              {editing ? (
                key === 'target_audience' || key === 'brand_voice_notes' || key === 'differentiation' ? (
                  <Textarea
                    rows={2}
                    value={draft[key] || ''}
                    onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                  />
                ) : (
                  <Input
                    value={draft[key] || ''}
                    onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                  />
                )
              ) : (
                <div className="text-sm text-gray-900 bg-gray-50 rounded px-2 py-1.5 min-h-[32px]">
                  {profile?.[key] || <span className="text-gray-400">—</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Brand colors */}
      {(profile?.brand_colors?.length > 0 || editing) && (
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Brand Colors</label>
          {editing ? (
            <Input
              placeholder="Comma-separated hex codes, e.g., #FF0000, #00AA00"
              value={(draft.brand_colors || []).join(', ')}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  brand_colors: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                })
              }
            />
          ) : (
            <div className="flex flex-wrap gap-2">
              {(profile.brand_colors || []).map((hex, i) => (
                <div key={i} className="flex items-center gap-2 bg-white border rounded px-2 py-1 text-xs">
                  <span
                    className="inline-block w-4 h-4 rounded border"
                    style={{ background: hex }}
                  />
                  <code>{hex}</code>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Taglines */}
      {(profile?.taglines?.length > 0) && (
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Saved Taglines</label>
          <div className="space-y-1">
            {profile.taglines.map((t, i) => (
              <div
                key={i}
                className={`flex items-center gap-2 px-2 py-1.5 rounded border text-sm ${
                  profile.selected_tagline === t
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-white border-gray-200'
                }`}
              >
                {profile.selected_tagline === t && (
                  <Badge variant="outline" className="bg-emerald-100 text-emerald-900 border-emerald-300 text-xs">
                    Selected
                  </Badge>
                )}
                <span className="flex-1">{t}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTagline(t)}
                  className="text-gray-400 hover:text-red-600"
                  title="Remove"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logos */}
      {profile?.logos?.length > 0 && (
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">
            Saved Logo Concepts (raster)
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {profile.logos.map((l) => (
              <div key={l.id} className="bg-white border rounded p-2 relative">
                <button
                  type="button"
                  onClick={() => handleRemoveLogo(l.id)}
                  className="absolute top-1 right-1 bg-white/80 hover:bg-red-100 rounded-full p-1"
                  title="Remove"
                >
                  <X className="w-3 h-3 text-gray-600" />
                </button>
                <img src={l.image_url} alt={l.summary || 'Logo concept'} className="w-full h-auto rounded" />
                <div className="text-xs text-gray-700 mt-1 truncate">{l.summary || '—'}</div>
                <div className="text-[10px] text-gray-400">{fmt(l.saved_at)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Brand kit */}
      {profile?.brand_kit_text && (
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Saved Brand Kit</label>
          <pre className="text-xs whitespace-pre-wrap bg-gray-50 border rounded p-3 max-h-60 overflow-y-auto">
            {profile.brand_kit_text}
          </pre>
        </div>
      )}

      {profile?.updated_at && (
        <div className="text-xs text-gray-400 text-right">
          Last updated {fmt(profile.updated_at)}
          {profile.updated_by_email && ` by ${profile.updated_by_email}`}
        </div>
      )}
    </div>
  );
}
