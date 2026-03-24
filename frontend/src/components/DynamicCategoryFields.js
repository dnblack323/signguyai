import { useState, useEffect, useMemo } from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Card, CardContent } from './ui/card';
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}` });

const GROUP_LABELS = {
  size_material: 'Size & Material',
  garment_info: 'Garment Information',
  size_breakdown: 'Size Breakdown',
  decoration: 'Decoration Method',
  print_locations: 'Print / Decoration Locations',
  finishing: 'Finishing Options',
  design: 'Design & Artwork',
  production: 'Production & Delivery',
  dimensions: 'Dimensions',
  material: 'Material',
  specs: 'Specifications',
  other: 'Other',
};

export default function DynamicCategoryFields({ category, subtype, specs, onChange, mode = 'edit' }) {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedLocations, setExpandedLocations] = useState({});

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    axios.get(`${API}/job-tickets/schema/${category}`, { headers: hdr() })
      .then(res => setSchema(res.data))
      .catch(() => setSchema(null))
      .finally(() => setLoading(false));
  }, [category]);

  // Auto-calculate square footage for banners
  const sqFootage = useMemo(() => {
    const w = parseFloat(specs.width) || 0;
    const h = parseFloat(specs.height) || 0;
    const unit = specs.unit_of_measure || 'feet';
    if (w <= 0 || h <= 0) return 0;
    if (unit === 'inches') return ((w * h) / 144).toFixed(2);
    return (w * h).toFixed(2);
  }, [specs.width, specs.height, specs.unit_of_measure]);

  // Auto-calculate size total for apparel
  const sizeTotal = useMemo(() => {
    return ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl']
      .reduce((sum, k) => sum + (parseInt(specs[k]) || 0), 0);
  }, [specs]);

  if (loading) return <div className="flex items-center gap-2 py-4 text-gray-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading fields...</div>;
  if (!schema?.fields) return null;

  const fields = schema.fields;
  const groups = {};
  fields.forEach(f => {
    const g = f.group || 'other';
    if (!groups[g]) groups[g] = [];
    groups[g].push(f);
  });

  const updateField = (key, value) => {
    onChange({ ...specs, [key]: value });
  };

  const toggleLocation = (loc) => {
    const current = specs.print_locations || [];
    const updated = current.includes(loc)
      ? current.filter(l => l !== loc)
      : [...current, loc];
    onChange({ ...specs, print_locations: updated });
  };

  const updateLocationDetail = (loc, field, value) => {
    const details = { ...(specs.location_details || {}) };
    if (!details[loc]) details[loc] = {};
    details[loc][field] = value;
    onChange({ ...specs, location_details: details });
  };

  // VIEW MODE
  if (mode === 'view') {
    return (
      <div className="space-y-4">
        {Object.entries(groups).map(([groupKey, groupFields]) => {
          const hasValues = groupFields.some(f => {
            const v = specs[f.key];
            return v !== undefined && v !== '' && v !== false && v !== 0 && v !== null;
          });
          if (!hasValues && groupKey !== 'size_breakdown') return null;
          return (
            <div key={groupKey}>
              <p className="text-xs text-gray-500 uppercase font-semibold mb-2">{GROUP_LABELS[groupKey] || groupKey}</p>
              {groupKey === 'size_breakdown' && sizeTotal > 0 ? (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex flex-wrap gap-3">
                    {['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl']
                      .filter(k => parseInt(specs[k]) > 0)
                      .map(k => <Badge key={k} variant="outline" className="text-gray-700">{k.replace('size_', '').toUpperCase()}: {specs[k]}</Badge>)}
                    <Badge className="bg-violet-100 text-violet-700">Total: {sizeTotal}</Badge>
                  </div>
                </div>
              ) : groupKey === 'print_locations' && specs.print_locations?.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {specs.print_locations.map(loc => <Badge key={loc} variant="outline" className="text-gray-700">{loc.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</Badge>)}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {groupFields.filter(f => {
                    const v = specs[f.key];
                    return v !== undefined && v !== '' && v !== false && v !== 0;
                  }).map(f => (
                    <div key={f.key} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 uppercase">{f.label}</p>
                      <p className="text-gray-900 mt-1 font-medium">
                        {f.type === 'toggle' ? (specs[f.key] ? 'Yes' : 'No') : String(specs[f.key])}
                      </p>
                    </div>
                  ))}
                  {groupKey === 'size_material' && sqFootage > 0 && (
                    <div className="bg-violet-50 rounded-lg p-3">
                      <p className="text-xs text-violet-600 uppercase">Square Footage</p>
                      <p className="text-gray-900 mt-1 font-bold">{sqFootage} sq ft</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  // EDIT MODE
  return (
    <div className="space-y-6" data-testid="dynamic-category-fields">
      {/* Subtype selector */}
      {schema.subtypes?.length > 0 && (
        <div>
          <Label className="text-gray-600 text-xs font-semibold uppercase">Product Type / Subtype</Label>
          <Select value={specs.subtype || ''} onValueChange={v => updateField('subtype', v)}>
            <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 mt-1"><SelectValue placeholder="Select subtype..." /></SelectTrigger>
            <SelectContent>{schema.subtypes.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>
      )}

      {Object.entries(groups).map(([groupKey, groupFields]) => (
        <div key={groupKey}>
          <p className="text-xs text-gray-500 uppercase font-semibold mb-3 tracking-wide">{GROUP_LABELS[groupKey] || groupKey}</p>

          {/* SIZE BREAKDOWN — special grid for apparel */}
          {groupKey === 'size_breakdown' ? (
            <div>
              <div className="grid grid-cols-5 md:grid-cols-9 gap-2">
                {groupFields.map(f => (
                  <div key={f.key} className="text-center">
                    <Label className="text-gray-500 text-xs block mb-1">{f.label}</Label>
                    <Input
                      type="number" min={0}
                      value={specs[f.key] || 0}
                      onChange={e => updateField(f.key, parseInt(e.target.value) || 0)}
                      className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-center text-sm"
                    />
                  </div>
                ))}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Badge className={`${sizeTotal > 0 ? 'bg-violet-100 text-violet-700' : 'bg-gray-100 text-gray-500'}`}>
                  Total: {sizeTotal}
                </Badge>
              </div>
            </div>

          /* PRINT LOCATIONS — checkbox grid with per-location details */
          ) : groupKey === 'print_locations' ? (
            <div className="space-y-2">
              {groupFields.filter(f => f.type === 'location_picker').map(f => (
                <div key={f.key}>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    {(f.options || []).map(loc => {
                      const isSelected = (specs.print_locations || []).includes(loc.value);
                      return (
                        <div key={loc.value}>
                          <label className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-colors ${isSelected ? 'bg-violet-50 border-violet-300 text-violet-700' : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'}`}>
                            <Checkbox checked={isSelected} onCheckedChange={() => toggleLocation(loc.value)} />
                            <span className="text-sm font-medium">{loc.label}</span>
                          </label>
                          {isSelected && (
                            <div className="mt-1 ml-6 p-2 bg-gray-50 rounded border border-gray-200 space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <div>
                                  <Label className="text-gray-500 text-xs">Art Width</Label>
                                  <Input
                                    value={(specs.location_details || {})[loc.value]?.art_width || ''}
                                    onChange={e => updateLocationDetail(loc.value, 'art_width', e.target.value)}
                                    placeholder="12in"
                                    className="bg-white border-gray-300 text-gray-900 h-7 text-xs"
                                  />
                                </div>
                                <div>
                                  <Label className="text-gray-500 text-xs">Art Height</Label>
                                  <Input
                                    value={(specs.location_details || {})[loc.value]?.art_height || ''}
                                    onChange={e => updateLocationDetail(loc.value, 'art_height', e.target.value)}
                                    placeholder="14in"
                                    className="bg-white border-gray-300 text-gray-900 h-7 text-xs"
                                  />
                                </div>
                              </div>
                              <div>
                                <Label className="text-gray-500 text-xs">Location Notes</Label>
                                <Input
                                  value={(specs.location_details || {})[loc.value]?.notes || ''}
                                  onChange={e => updateLocationDetail(loc.value, 'notes', e.target.value)}
                                  placeholder="Special instructions for this location"
                                  className="bg-white border-gray-300 text-gray-900 h-7 text-xs"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {(specs.print_locations || []).length > 0 && (
                    <Badge className="mt-2 bg-violet-100 text-violet-700">{(specs.print_locations || []).length} location(s) selected</Badge>
                  )}
                </div>
              ))}
            </div>

          /* STANDARD FIELD GRID */
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {groupFields.map(f => {
                // Calculated field (square footage)
                if (f.type === 'calculated') {
                  return (
                    <div key={f.key} className="bg-violet-50 rounded-lg p-3 border border-violet-200">
                      <Label className="text-violet-600 text-xs font-semibold">{f.label}</Label>
                      <p className="text-gray-900 font-bold text-lg mt-1">{sqFootage} sq ft</p>
                    </div>
                  );
                }
                // Toggle
                if (f.type === 'toggle') {
                  return (
                    <div key={f.key} className="flex items-center justify-between bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <Label className="text-gray-700 text-sm">{f.label}</Label>
                      <Switch checked={specs[f.key] ?? f.default ?? false} onCheckedChange={v => updateField(f.key, v)} />
                    </div>
                  );
                }
                // Select dropdown
                if (f.type === 'select') {
                  return (
                    <div key={f.key}>
                      <Label className="text-gray-500 text-xs">{f.label}{f.required && ' *'}</Label>
                      <Select value={specs[f.key] || f.default || ''} onValueChange={v => updateField(f.key, v)}>
                        <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"><SelectValue placeholder={`Select ${f.label}`} /></SelectTrigger>
                        <SelectContent>{(f.options || []).map(opt => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  );
                }
                // Select or text (apparel brand)
                if (f.type === 'select_or_text') {
                  const isCustom = specs[f.key] === 'custom' || (specs[f.key] && !(f.options || []).some(o => o.value === specs[f.key]));
                  return (
                    <div key={f.key} className={isCustom ? 'col-span-2 md:col-span-1' : ''}>
                      <Label className="text-gray-500 text-xs">{f.label}</Label>
                      <Select value={isCustom ? 'custom' : (specs[f.key] || '')} onValueChange={v => updateField(f.key, v)}>
                        <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"><SelectValue placeholder={f.placeholder || `Select ${f.label}`} /></SelectTrigger>
                        <SelectContent>{(f.options || []).map(opt => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent>
                      </Select>
                      {isCustom && (
                        <Input
                          value={specs[`${f.key}_custom`] || ''}
                          onChange={e => updateField(`${f.key}_custom`, e.target.value)}
                          placeholder="Type custom value..."
                          className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-sm mt-1"
                        />
                      )}
                    </div>
                  );
                }
                // Number
                if (f.type === 'number') {
                  return (
                    <div key={f.key}>
                      <Label className="text-gray-500 text-xs">{f.label}</Label>
                      <Input
                        type="number" min={0}
                        value={specs[f.key] || f.default || ''}
                        onChange={e => updateField(f.key, parseInt(e.target.value) || 0)}
                        placeholder={f.placeholder || ''}
                        className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"
                      />
                    </div>
                  );
                }
                // Textarea
                if (f.type === 'textarea') {
                  return (
                    <div key={f.key} className="col-span-2 md:col-span-3">
                      <Label className="text-gray-500 text-xs">{f.label}</Label>
                      <Textarea
                        value={specs[f.key] || ''}
                        onChange={e => updateField(f.key, e.target.value)}
                        placeholder={f.placeholder || ''}
                        className="bg-gray-50 border-gray-300 text-gray-900 text-sm mt-1"
                        rows={2}
                      />
                    </div>
                  );
                }
                // Default text input
                return (
                  <div key={f.key}>
                    <Label className="text-gray-500 text-xs">{f.label}{f.required && ' *'}</Label>
                    <Input
                      value={specs[f.key] || ''}
                      onChange={e => updateField(f.key, e.target.value)}
                      placeholder={f.placeholder || ''}
                      className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}

      {schema.pricing_config && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200">
          <Badge variant="outline" className="text-xs text-gray-500">Min: ${schema.pricing_config.minimum_charge}</Badge>
          <Badge variant="outline" className="text-xs text-gray-500">Markup: {schema.pricing_config.default_markup}x</Badge>
          <Badge variant="outline" className="text-xs text-gray-500">Target: {schema.pricing_config.target_margin}%</Badge>
        </div>
      )}
    </div>
  );
}
