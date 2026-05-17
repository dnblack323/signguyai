import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapDataTable from '../WrapDataTable';
import WrapEmptyState from '../WrapEmptyState';
import { Camera, ShieldAlert, MousePointer2 } from 'lucide-react';

export default function InspectionTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Vehicle Diagram" icon={MousePointer2} testId="insp-diagram">
          <WrapEmptyState title="Diagram tool launches in phase 2" message="Tap-to-mark damage on a vehicle silhouette." />
        </WrapSectionCard>
        <WrapSectionCard title="Damage List" icon={ShieldAlert} testId="insp-damage">
          <WrapDataTable
            testId="insp-damage-table"
            columns={['Location', 'Damage Type', 'Severity', 'Photo', 'Notes', 'Installer']}
            rows={[]}
            emptyMessage="No damage logged yet."
          />
        </WrapSectionCard>
        <WrapSectionCard title="Inspection Photos" icon={Camera} testId="insp-photos">
          <WrapEmptyState title="No inspection photos uploaded" />
        </WrapSectionCard>
        <WrapSectionCard title="Customer Acknowledgment" icon={ShieldAlert} testId="insp-ack">
          <p className="text-xs text-slate-500">Customer e-signature of the pre-install damage disclaimer will land here in phase 2.</p>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Inspection AI Helper"
        testId="insp-ai-helper"
        actions={[
          { label: 'Summarize Damage' },
          { label: 'Create Inspection Summary' },
          { label: 'Flag Paint Risk' },
          { label: 'Create Damage Disclaimer' },
          { label: 'Check Missing Photos' },
        ]}
      />
    </div>
  );
}
