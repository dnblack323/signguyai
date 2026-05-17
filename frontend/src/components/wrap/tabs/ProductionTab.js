import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapChecklistCard from '../WrapChecklistCard';
import WrapDataTable from '../WrapDataTable';
import { Factory, Timer, Printer, ClipboardCheck } from 'lucide-react';

export default function ProductionTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapChecklistCard
          title="Production Checklist"
          icon={ClipboardCheck}
          testId="prod-checklist"
          items={[
            { label: 'Files prepped', done: false },
            { label: 'Print queued', done: false },
            { label: 'Printed', done: false },
            { label: 'Laminated', done: false },
            { label: 'Cut/trimmed', done: false },
            { label: 'QC passed', done: false },
            { label: 'Packaged for install', done: false },
          ]}
        />
        <WrapSectionCard title="Production Tasks" icon={Factory} testId="prod-tasks">
          <WrapDataTable
            testId="prod-tasks-table"
            columns={['Task', 'Assigned To', 'Status', 'Estimated Time', 'Actual Time', 'Notes']}
            rows={[]}
            emptyMessage="No tasks scheduled yet."
          />
        </WrapSectionCard>
        <WrapSectionCard title="Labor Timer" icon={Timer} testId="prod-timer">
          <p className="text-xs text-slate-500">Active labor timers will appear here in phase 2.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Material Staging" icon={Factory} testId="prod-staging">
          <p className="text-xs text-slate-500">Material pick-list and staging status syncs from the inventory module.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Print / Lamination Status" icon={Printer} testId="prod-print">
          <p className="text-xs text-slate-500">RIP queue + lamination scheduling lands in phase 2.</p>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Production AI Helper"
        testId="prod-ai-helper"
        actions={[
          { label: 'Build Checklist' },
          { label: 'Estimate Time' },
          { label: 'Check Bottlenecks' },
          { label: 'Compare Labor' },
          { label: 'Suggest Next Step' },
        ]}
      />
    </div>
  );
}
