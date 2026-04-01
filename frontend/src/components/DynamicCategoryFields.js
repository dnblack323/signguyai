import { useState, useEffect, useMemo } from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Loader2 } from 'lucide-react';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}` });
const SIZE_KEYS = ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl'];

const GROUP_LABELS = {
  size_material: 'Size & Material',
  size_media: 'Size & Media',
  size_layout: 'Size & Layout',
  garment_info: 'Garment Information',
  size_breakdown: 'Size Breakdown',
  decoration: 'Decoration Method',
  print_locations: 'Print / Decoration Locations',
  finishing: 'Finishing Options',
  design: 'Design & Artwork',
  production: 'Production & Delivery',
  dimensions: 'Dimensions',
  material: 'Material',
  material_print: 'Material & Print',
  specs: 'Specifications',
  mounting: 'Mounting / Hardware',
  vinyl_details: 'Vinyl Details',
  vinyl_production: 'Vinyl Production',
  installation: 'Installation',
  vehicle_info: 'Vehicle Information',
  coverage: 'Coverage Level',
  paneling: 'Paneling & Production',
  print_options: 'Print Options',
  other: 'Other',
};

const buildGroups = (fields) => fields.reduce((groups, field) => {
  const groupKey = field.group || 'other';
  groups[groupKey] = groups[groupKey] || [];
  groups[groupKey].push(field);
  return groups;
}, {});

const hasRenderableValue = (value) => value !== undefined && value !== '' && value !== false && value !== 0 && value !== null;
const formatLocationLabel = (value) => value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

const SizeBreakdownView = ({ specs, sizeTotal }) => (
  <div className="bg-gray-50 rounded-lg p-3">
    <div className="flex flex-wrap gap-3">
      {SIZE_KEYS.filter((key) => parseInt(specs[key], 10) > 0).map((key) => (
        <Badge key={key} variant="outline" className="text-gray-700">{key.replace('size_', '').toUpperCase()}: {specs[key]}</Badge>
      ))}
      <Badge className="bg-violet-100 text-violet-700">Total: {sizeTotal}</Badge>
    </div>
  </div>
);

const FieldGridView = ({ groupFields, specs, groupKey, sqFootage }) => (
  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
    {groupFields.filter((field) => hasRenderableValue(specs[field.key])).map((field) => (
      <div key={field.key} className="bg-gray-50 rounded-lg p-3">
        <p className="text-xs text-gray-500 uppercase">{field.label}</p>
        <p className="text-gray-900 mt-1 font-medium">{field.type === 'toggle' ? (specs[field.key] ? 'Yes' : 'No') : String(specs[field.key])}</p>
      </div>
    ))}
    {groupKey === 'size_material' && sqFootage > 0 && (
      <div className="bg-violet-50 rounded-lg p-3">
        <p className="text-xs text-violet-600 uppercase">Square Footage</p>
        <p className="text-gray-900 mt-1 font-bold">{sqFootage} sq ft</p>
      </div>
    )}
  </div>
);

const renderStandardField = (field, specs, updateField, sqFootage) => {
  if (field.type === 'calculated') {
    return (
      <div key={field.key} className="bg-violet-50 rounded-lg p-3 border border-violet-200">
        <Label className="text-violet-600 text-xs font-semibold">{field.label}</Label>
        <p className="text-gray-900 font-bold text-lg mt-1">{sqFootage} sq ft</p>
      </div>
    );
  }

  if (field.type === 'toggle') {
    return (
      <div key={field.key} className="flex items-center justify-between bg-gray-50 rounded-lg p-3 border border-gray-200">
        <Label className="text-gray-700 text-sm">{field.label}</Label>
        <Switch checked={specs[field.key] ?? field.default ?? false} onCheckedChange={(value) => updateField(field.key, value)} />
      </div>
    );
  }

  if (field.type === 'select') {
    return (
      <div key={field.key}>
        <Label className="text-gray-500 text-xs">{field.label}{field.required && ' *'}</Label>
        <Select value={specs[field.key] || field.default || ''} onValueChange={(value) => updateField(field.key, value)}>
          <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"><SelectValue placeholder={`Select ${field.label}`} /></SelectTrigger>
          <SelectContent>{(field.options || []).map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent>
        </Select>
      </div>
    );
  }

  if (field.type === 'select_or_text') {
    const isCustom = specs[field.key] === 'custom' || (specs[field.key] && !(field.options || []).some((option) => option.value === specs[field.key]));
    return (
      <div key={field.key} className={isCustom ? 'col-span-2 md:col-span-1' : ''}>
        <Label className="text-gray-500 text-xs">{field.label}</Label>
        <Select value={isCustom ? 'custom' : (specs[field.key] || '')} onValueChange={(value) => updateField(field.key, value)}>
          <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1"><SelectValue placeholder={field.placeholder || `Select ${field.label}`} /></SelectTrigger>
          <SelectContent>{(field.options || []).map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent>
        </Select>
        {isCustom && <Input value={specs[`${field.key}_custom`] || ''} onChange={(event) => updateField(`${field.key}_custom`, event.target.value)} placeholder="Type custom value..." className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-sm mt-1" />}
      </div>
    );
  }

  if (field.type === 'number') {
    return (
      <div key={field.key}>
        <Label className="text-gray-500 text-xs">{field.label}</Label>
        <Input type="number" min={0} value={specs[field.key] || field.default || ''} onChange={(event) => updateField(field.key, parseInt(event.target.value, 10) || 0)} placeholder={field.placeholder || ''} className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1" />
      </div>
    );
  }

  if (field.type === 'textarea') {
    return (
      <div key={field.key} className="col-span-2 md:col-span-3">
        <Label className="text-gray-500 text-xs">{field.label}</Label>
        <Textarea value={specs[field.key] || ''} onChange={(event) => updateField(field.key, event.target.value)} placeholder={field.placeholder || ''} className="bg-gray-50 border-gray-300 text-gray-900 text-sm mt-1" rows={2} />
      </div>
    );
  }

  return (
    <div key={field.key}>
      <Label className="text-gray-500 text-xs">{field.label}{field.required && ' *'}</Label>
      <Input value={specs[field.key] || ''} onChange={(event) => updateField(field.key, event.target.value)} placeholder={field.placeholder || ''} className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-sm mt-1" />
    </div>
  );
};

export default function DynamicCategoryFields({ category, subtype, specs, onChange, mode = 'edit' }) {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!category) return;
    setLoading(true);
    let retries = 0;
    const fetchSchema = () => {
      axios.get(`${API}/job-tickets/schema/${category}`, { headers: hdr() })
        .then((response) => {
          setSchema(response.data);
          if (response.data?.fields && onChange) {
            const defaults = response.data.fields.reduce((acc, field) => {
              if (field.default !== undefined && (specs[field.key] === undefined || specs[field.key] === '')) acc[field.key] = field.default;
              return acc;
            }, {});
            if (Object.keys(defaults).length > 0) onChange({ ...specs, ...defaults });
          }
          setLoading(false);
        })
        .catch(() => {
          if (retries < 2) {
            retries += 1;
            setTimeout(fetchSchema, 500);
            return;
          }
          setSchema(null);
          setLoading(false);
        });
    };
    fetchSchema();
  }, [category, onChange, specs]);

  const sqFootage = useMemo(() => {
    const width = parseFloat(specs.width) || 0;
    const height = parseFloat(specs.height) || 0;
    const unit = (specs.unit_of_measure || 'inches').toLowerCase();
    if (width <= 0 || height <= 0) return 0;
    return unit === 'feet' ? (width * height).toFixed(2) : ((width * height) / 144).toFixed(2);
  }, [specs.height, specs.unit_of_measure, specs.width]);

  const sizeTotal = useMemo(() => SIZE_KEYS.reduce((sum, key) => sum + (parseInt(specs[key], 10) || 0), 0), [specs]);

  if (loading) return <div className="flex items-center gap-2 py-4 text-gray-500 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading fields...</div>;
  if (!schema?.fields) return null;

  const groups = buildGroups(schema.fields);
  const updateField = (key, value) => onChange({ ...specs, [key]: value });
  const toggleLocation = (location) => {
    const current = specs.print_locations || [];
    const updated = current.includes(location) ? current.filter((item) => item !== location) : [...current, location];
    onChange({ ...specs, print_locations: updated });
  };
  const updateLocationDetail = (location, field, value) => {
    const details = { ...(specs.location_details || {}) };
    details[location] = { ...(details[location] || {}), [field]: value };
    onChange({ ...specs, location_details: details });
  };

  if (mode === 'view') {
    return (
      <div className="space-y-4">
        {Object.entries(groups).map(([groupKey, groupFields]) => {
          const hasValues = groupFields.some((field) => hasRenderableValue(specs[field.key]));
          if (!hasValues && groupKey !== 'size_breakdown') return null;
          return (
            <div key={groupKey}>
              <p className="text-xs text-gray-500 uppercase font-semibold mb-2">{GROUP_LABELS[groupKey] || groupKey}</p>
              {groupKey === 'size_breakdown' && sizeTotal > 0 ? (
                <SizeBreakdownView specs={specs} sizeTotal={sizeTotal} />
              ) : groupKey === 'print_locations' && specs.print_locations?.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {specs.print_locations.map((location) => <Badge key={location} variant="outline" className="text-gray-700">{formatLocationLabel(location)}</Badge>)}
                </div>
              ) : (
                <FieldGridView groupFields={groupFields} specs={specs} groupKey={groupKey} sqFootage={sqFootage} />
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dynamic-category-fields">
      {schema.subtypes?.length > 0 && (
        <div>
          <Label className="text-gray-600 text-xs font-semibold uppercase">Product Type / Subtype</Label>
          <Select value={specs.subtype || ''} onValueChange={(value) => updateField('subtype', value)}>
            <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 mt-1"><SelectValue placeholder="Select subtype..." /></SelectTrigger>
            <SelectContent>{schema.subtypes.map((item) => <SelectItem key={item.value} value={item.value}>{item.label}</SelectItem>)}</SelectContent>
          </Select>
        </div>
      )}

      {Object.entries(groups).map(([groupKey, groupFields]) => (
        <div key={groupKey}>
          <p className="text-xs text-gray-500 uppercase font-semibold mb-3 tracking-wide">{GROUP_LABELS[groupKey] || groupKey}</p>
          {groupKey === 'size_breakdown' ? (
            <div>
              <div className="grid grid-cols-5 md:grid-cols-9 gap-2">
                {groupFields.map((field) => (
                  <div key={field.key} className="text-center">
                    <Label className="text-gray-500 text-xs block mb-1">{field.label}</Label>
                    <Input type="number" min={0} value={specs[field.key] || 0} onChange={(event) => updateField(field.key, parseInt(event.target.value, 10) || 0)} className="bg-gray-50 border-gray-300 text-gray-900 h-9 text-center text-sm" />
                  </div>
                ))}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <Badge className={sizeTotal > 0 ? 'bg-violet-100 text-violet-700' : 'bg-gray-100 text-gray-500'}>Total: {sizeTotal}</Badge>
              </div>
            </div>
          ) : groupKey === 'print_locations' ? (
            <div className="space-y-2">
              {groupFields.filter((field) => field.type === 'location_picker').map((field) => (
                <div key={field.key}>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    {(field.options || []).map((location) => {
                      const isSelected = (specs.print_locations || []).includes(location.value);
                      return (
                        <div key={location.value}>
                          <label className={`flex items-center gap-2 p-2.5 rounded-lg border cursor-pointer transition-colors ${isSelected ? 'bg-violet-50 border-violet-300 text-violet-700' : 'bg-gray-50 border-gray-200 text-gray-600 hover:border-gray-300'}`}>
                            <Checkbox checked={isSelected} onCheckedChange={() => toggleLocation(location.value)} />
                            <span className="text-sm font-medium">{location.label}</span>
                          </label>
                          {isSelected && (
                            <div className="mt-1 ml-6 p-2 bg-gray-50 rounded border border-gray-200 space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <div>
                                  <Label className="text-gray-500 text-xs">Art Width</Label>
                                  <Input value={(specs.location_details || {})[location.value]?.art_width || ''} onChange={(event) => updateLocationDetail(location.value, 'art_width', event.target.value)} placeholder="12in" className="bg-white border-gray-300 text-gray-900 h-7 text-xs" />
                                </div>
                                <div>
                                  <Label className="text-gray-500 text-xs">Art Height</Label>
                                  <Input value={(specs.location_details || {})[location.value]?.art_height || ''} onChange={(event) => updateLocationDetail(location.value, 'art_height', event.target.value)} placeholder="14in" className="bg-white border-gray-300 text-gray-900 h-7 text-xs" />
                                </div>
                              </div>
                              <div>
                                <Label className="text-gray-500 text-xs">Location Notes</Label>
                                <Input value={(specs.location_details || {})[location.value]?.notes || ''} onChange={(event) => updateLocationDetail(location.value, 'notes', event.target.value)} placeholder="Special instructions for this location" className="bg-white border-gray-300 text-gray-900 h-7 text-xs" />
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {(specs.print_locations || []).length > 0 && <Badge className="mt-2 bg-violet-100 text-violet-700">{(specs.print_locations || []).length} location(s) selected</Badge>}
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {groupFields.map((field) => renderStandardField(field, specs, updateField, sqFootage))}
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
