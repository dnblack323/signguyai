import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapDataTable from '../WrapDataTable';
import WrapActionButtonGroup from '../WrapActionButtonGroup';
import { Ruler, Plus } from 'lucide-react';

export default function MeasurementsTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Coverage Summary" icon={Ruler} testId="meas-coverage">
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><p className="text-[10px] uppercase text-slate-500">Total Sq Ft</p><p className="font-semibold">— ft²</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Billable Sq Ft</p><p className="font-semibold">— ft²</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Waste %</p><p className="font-semibold">—%</p></div>
          </div>
        </WrapSectionCard>
        <WrapSectionCard
          title="Wrapped Areas"
          icon={Ruler}
          testId="meas-areas"
          action={<WrapActionButtonGroup actions={[{ label: 'Add Area', icon: Plus }]} testId="meas-add" />}
        >
          <WrapDataTable
            testId="meas-table"
            columns={['Area', 'Width', 'Height', 'Sq Ft', 'Material', 'Complexity', 'Included', 'Actions']}
            rows={[
              ['Driver Side', '—', '—', '—', 'Printed Wrap', 'Medium', 'Yes', 'Edit'],
              ['Passenger Side', '—', '—', '—', 'Printed Wrap', 'Medium', 'Yes', 'Edit'],
            ]}
          />
        </WrapSectionCard>
        <WrapSectionCard title="Waste Factor" icon={Ruler} testId="meas-waste">
          <p className="text-sm text-slate-700">Default waste factor: <span className="font-medium">15%</span> (phase 2 reads tenant default).</p>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Measurements AI Helper"
        testId="meas-ai-helper"
        actions={[
          { label: 'Estimate Missing Dimensions' },
          { label: 'Suggest Waste Factor' },
          { label: 'Check Missing Areas' },
          { label: 'Compare to Vehicle Type' },
          { label: 'Suggest Billable Sq Ft' },
        ]}
      />
    </div>
  );
}
