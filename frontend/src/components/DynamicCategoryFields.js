import { useState, useEffect } from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Loader2 } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}` });

/**
 * Renders dynamic category-specific fields for job tickets.
 * Fetches field schema from /api/job-tickets/schema/{category}.
 * All options come from backend (enums + pricing settings).
 */
export default function DynamicCategoryFields({ category, specs, onChange, mode = 'edit' }) {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    axios.get(`${API}/job-tickets/schema/${category}`, { headers: hdr() })
      .then(res => setSchema(res.data))
      .catch(() => setSchema(null))
      .finally(() => setLoading(false));
  }, [category]);

  if (loading) return <div className="flex items-center gap-2 py-4 text-gray-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading fields...</div>;
  if (!schema?.fields) return null;

  const fields = schema.fields;
  const groups = {};
  fields.forEach(f => {
    const g = f.group || 'other';
    if (!groups[g]) groups[g] = [];
    groups[g].push(f);
  });

  const GROUP_LABELS = {
    dimensions: 'Dimensions',
    material: 'Material',
    specs: 'Specifications',
    finishing: 'Finishing',
    production: 'Production',
    other: 'Other',
  };

  const updateField = (key, value) => {
    onChange({ ...specs, [key]: value });
  };

  if (mode === 'view') {
    return (
      <div className="space-y-4">
        {Object.entries(groups).map(([groupKey, groupFields]) => {
          const hasValues = groupFields.some(f => specs[f.key]);
          if (!hasValues) return null;
          return (
            <div key={groupKey}>
              <p className="text-xs text-gray-500 uppercase font-medium mb-2">{GROUP_LABELS[groupKey] || groupKey}</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {groupFields.filter(f => specs[f.key] !== undefined && specs[f.key] !== '' && specs[f.key] !== false).map(f => (
                  <div key={f.key} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 uppercase">{f.label}</p>
                    <p className="text-gray-900 mt-1">
                      {f.type === 'toggle' ? (specs[f.key] ? 'Yes' : 'No') : String(specs[f.key])}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="dynamic-category-fields">
      {Object.entries(groups).map(([groupKey, groupFields]) => (
        <div key={groupKey}>
          <p className="text-xs text-gray-500 uppercase font-medium mb-2">{GROUP_LABELS[groupKey] || groupKey}</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {groupFields.map(f => {
              if (f.type === 'toggle') {
                return (
                  <div key={f.key} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                    <Label className="text-gray-700 text-sm">{f.label}</Label>
                    <Switch
                      checked={specs[f.key] ?? f.default ?? false}
                      onCheckedChange={v => updateField(f.key, v)}
                    />
                  </div>
                );
              }
              if (f.type === 'select' && f.options) {
                return (
                  <div key={f.key}>
                    <Label className="text-gray-500 text-xs">{f.label}</Label>
                    <Select value={specs[f.key] || ''} onValueChange={v => updateField(f.key, v)}>
                      <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-sm mt-1">
                        <SelectValue placeholder={`Select ${f.label}`} />
                      </SelectTrigger>
                      <SelectContent>
                        {f.options.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                );
              }
              return (
                <div key={f.key}>
                  <Label className="text-gray-500 text-xs">{f.label}</Label>
                  <Input
                    value={specs[f.key] || ''}
                    onChange={e => updateField(f.key, e.target.value)}
                    placeholder={f.placeholder || ''}
                    className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-sm mt-1"
                  />
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {schema.pricing_config && (
        <div className="flex flex-wrap gap-2 pt-2">
          <Badge variant="outline" className="text-xs text-gray-500">Min: ${schema.pricing_config.minimum_charge}</Badge>
          <Badge variant="outline" className="text-xs text-gray-500">Markup: {schema.pricing_config.default_markup}x</Badge>
          <Badge variant="outline" className="text-xs text-gray-500">Target: {schema.pricing_config.target_margin}%</Badge>
        </div>
      )}
    </div>
  );
}
