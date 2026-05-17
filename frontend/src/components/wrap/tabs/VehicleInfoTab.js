import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapEmptyState from '../WrapEmptyState';
import { Car, Camera, FileImage } from 'lucide-react';

const FIELDS = [
  { label: 'Year', value: '2022' },
  { label: 'Make', value: 'Ford' },
  { label: 'Model', value: 'Transit 250' },
  { label: 'Trim', value: '—' },
  { label: 'Body Type', value: 'High Roof Cargo Van' },
  { label: 'Roof Height', value: '—' },
  { label: 'Wheelbase', value: '—' },
  { label: 'Vehicle Color', value: 'White' },
  { label: 'Existing Graphics', value: 'None' },
  { label: 'Paint/Body Condition', value: '—' },
];

export default function VehicleInfoTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Vehicle Details" icon={Car} testId="vehicle-details">
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            {FIELDS.map((f) => (
              <div key={f.label}>
                <p className="text-[10px] uppercase tracking-wide text-slate-500">{f.label}</p>
                <p className="text-slate-700">{f.value}</p>
              </div>
            ))}
          </div>
        </WrapSectionCard>
        <WrapSectionCard title="Existing Condition" icon={Camera} testId="vehicle-condition">
          <WrapEmptyState title="No condition notes yet" message="Inspector notes and damage map will populate from the Inspection tab." />
        </WrapSectionCard>
        <WrapSectionCard title="Template / Diagram" icon={FileImage} testId="vehicle-template">
          <WrapEmptyState title="Template library will appear here" message="Phase 2 will match by Year/Make/Model." />
        </WrapSectionCard>
        <WrapSectionCard title="Customer Vehicle Photos" icon={Camera} testId="vehicle-photos">
          <WrapEmptyState title="No customer-submitted photos yet" message="Drag & drop, customer portal upload, and AI labelling come in phase 2." />
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
