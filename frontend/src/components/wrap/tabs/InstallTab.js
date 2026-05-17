import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapChecklistCard from '../WrapChecklistCard';
import WrapDataTable from '../WrapDataTable';
import { CalendarClock, ClipboardCheck, UserCog, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function InstallTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Install Schedule" icon={CalendarClock} testId="install-schedule">
          <p className="text-sm text-slate-700">Install date: <span className="font-medium">Not scheduled</span></p>
          <p className="text-xs text-slate-500 mt-1">Phase 2 wires the appointment system.</p>
        </WrapSectionCard>
        <WrapChecklistCard
          title="Install Checklist"
          icon={ClipboardCheck}
          testId="install-checklist"
          items={[
            { label: 'Vehicle pre-cleaned', done: false },
            { label: 'Surface prepped', done: false },
            { label: 'Panels applied', done: false },
            { label: 'Seams squeegeed', done: false },
            { label: 'Edges post-heated', done: false },
            { label: 'Final QC walk-around', done: false },
          ]}
        />
        <WrapSectionCard title="Installer Assignment" icon={UserCog} testId="install-installer">
          <p className="text-xs text-slate-500">Assign installers in phase 2. Linked to the team scheduler.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Install Issue Log" icon={AlertTriangle} testId="install-issues">
          <WrapDataTable
            testId="install-issues-table"
            columns={['Issue Type', 'Area', 'Description', 'Photo', 'Resolved']}
            rows={[]}
            emptyMessage="No issues logged yet."
          />
        </WrapSectionCard>
        <WrapSectionCard title="Completion Signoff" icon={CheckCircle2} testId="install-signoff">
          <p className="text-xs text-slate-500">Customer signoff capture lands in phase 2.</p>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Install AI Helper"
        testId="install-ai-helper"
        actions={[
          { label: 'Build Install Checklist' },
          { label: 'Estimate Install Time' },
          { label: 'Write Drop-Off Message' },
          { label: 'Summarize Issues' },
          { label: 'Write Pickup Message' },
        ]}
      />
    </div>
  );
}
