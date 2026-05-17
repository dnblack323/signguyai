// Phase 2A: Vehicle Info tab — saves to /api/wrap/items/{id}/vehicle.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapEmptyState from '../WrapEmptyState';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { Switch } from '../../ui/switch';
import { Car, Camera, FileImage, Save } from 'lucide-react';

const EMPTY_VEHICLE = {
  year: '', make: '', model: '', trim: '', body_type: '',
  roof_height: '', wheelbase: '', vehicle_color: '',
  license_plate: '', vin: '',
  existing_graphics: false, existing_wrap: false,
  paint_condition: '', body_condition: '',
  vehicle_notes: '', template_type: '',
  customer_photo_placeholders: [],
};

const TEXT_FIELDS = [
  { key: 'year', label: 'Year', placeholder: '2022' },
  { key: 'make', label: 'Make', placeholder: 'Ford' },
  { key: 'model', label: 'Model', placeholder: 'Transit 250' },
  { key: 'trim', label: 'Trim', placeholder: 'XLT' },
  { key: 'body_type', label: 'Body Type', placeholder: 'High Roof Cargo Van' },
  { key: 'roof_height', label: 'Roof Height', placeholder: 'High / Mid / Low' },
  { key: 'wheelbase', label: 'Wheelbase', placeholder: '148"' },
  { key: 'vehicle_color', label: 'Vehicle Color', placeholder: 'White' },
  { key: 'license_plate', label: 'License Plate (optional)', placeholder: 'ABC-1234' },
  { key: 'vin', label: 'VIN (optional)', placeholder: '17-digit VIN' },
  { key: 'paint_condition', label: 'Paint Condition', placeholder: 'e.g. Excellent / Light swirls' },
  { key: 'body_condition', label: 'Body Condition', placeholder: 'e.g. No dents' },
  { key: 'template_type', label: 'Template / Diagram Type', placeholder: 'High roof transit template' },
];

export default function VehicleInfoTab({ wrapData, onSave, saveStatus }) {
  const [form, setForm] = useState(EMPTY_VEHICLE);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setForm({ ...EMPTY_VEHICLE, ...(wrapData?.vehicle_info || {}) });
    setDirty(false);
  }, [wrapData]);

  const setField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setDirty(true);
  };

  const handleSave = async () => {
    if (!onSave) return;
    const result = await onSave(form);
    if (result?.ok) setDirty(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Vehicle Details"
          icon={Car}
          testId="vehicle-details"
          action={
            <div className="flex items-center gap-2">
              {dirty && (
                <span className="text-[11px] text-amber-700" data-testid="vehicle-unsaved-indicator">
                  Unsaved changes
                </span>
              )}
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saveStatus === 'saving' || !onSave}
                className="bg-violet-600 hover:bg-violet-700 text-white"
                data-testid="vehicle-save-btn"
              >
                <Save className="h-3.5 w-3.5 mr-1" /> Save Vehicle Info
              </Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3">
            {TEXT_FIELDS.map((f) => (
              <div key={f.key} className="space-y-1">
                <Label htmlFor={`vehicle-${f.key}`} className="text-xs">{f.label}</Label>
                <Input
                  id={`vehicle-${f.key}`}
                  data-testid={`vehicle-input-${f.key}`}
                  value={form[f.key] || ''}
                  placeholder={f.placeholder}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              </div>
            ))}
            <div className="flex items-center gap-3 md:col-span-2 mt-1">
              <div className="flex items-center gap-2">
                <Switch
                  id="vehicle-existing-graphics"
                  data-testid="vehicle-toggle-existing_graphics"
                  checked={!!form.existing_graphics}
                  onCheckedChange={(v) => setField('existing_graphics', v)}
                />
                <Label htmlFor="vehicle-existing-graphics" className="text-xs">Existing graphics on vehicle</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="vehicle-existing-wrap"
                  data-testid="vehicle-toggle-existing_wrap"
                  checked={!!form.existing_wrap}
                  onCheckedChange={(v) => setField('existing_wrap', v)}
                />
                <Label htmlFor="vehicle-existing-wrap" className="text-xs">Existing wrap</Label>
              </div>
            </div>
            <div className="md:col-span-2 space-y-1">
              <Label htmlFor="vehicle-notes" className="text-xs">Vehicle Notes</Label>
              <Textarea
                id="vehicle-notes"
                data-testid="vehicle-input-vehicle_notes"
                rows={3}
                value={form.vehicle_notes || ''}
                placeholder="Anything an installer should know about this vehicle."
                onChange={(e) => setField('vehicle_notes', e.target.value)}
              />
            </div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Existing Condition" icon={Camera} testId="vehicle-condition">
          <p className="text-xs text-slate-500">
            Detailed condition notes & damage map will populate from the Inspection tab in a later phase.
          </p>
        </WrapSectionCard>

        <WrapSectionCard title="Template / Diagram" icon={FileImage} testId="vehicle-template">
          {form.template_type
            ? <p className="text-sm text-slate-700">Template: <span className="font-medium">{form.template_type}</span></p>
            : <WrapEmptyState title="Template library will appear here" message="Phase 2B will auto-match by Year/Make/Model." />}
        </WrapSectionCard>

        <WrapSectionCard title="Customer Vehicle Photos" icon={Camera} testId="vehicle-photos">
          <WrapEmptyState title="Photo uploads land in a later phase" message="For now, photos can be attached via the order Assets panel." />
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Vehicle Info AI Helper"
        testId="vehicle-ai-helper"
        actions={[
          { label: 'Autofill Dimensions' },
          { label: 'Suggest Vehicle Type' },
          { label: 'Find Template' },
          { label: 'Estimate Coverage' },
          { label: 'Check Missing Info' },
        ]}
      />
    </div>
  );
}
