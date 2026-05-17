// Phase 1: Right sidebar with the 6 always-visible context panels.
import WrapSectionCard from './WrapSectionCard';
import WrapChecklistCard from './WrapChecklistCard';
import WrapAIHelperCard from './WrapAIHelperCard';
import { Activity, Compass, ListChecks, NotebookPen, UserCheck } from 'lucide-react';

export default function WrapSidebar({ header }) {
  return (
    <div className="space-y-3" data-testid="wrap-sidebar">
      <WrapSectionCard title="Current Status" icon={Activity} testId="wrap-sidebar-status">
        <p className="text-sm font-medium text-amber-700">{header.status}</p>
        <p className="text-xs text-slate-500 mt-1">Last updated just now (placeholder).</p>
      </WrapSectionCard>

      <WrapSectionCard title="Next Best Action" icon={Compass} testId="wrap-sidebar-next">
        <p className="text-sm text-slate-700">Send design questionnaire to customer.</p>
        <p className="text-xs text-slate-500 mt-1">Phase 2 will compute this from real workflow state.</p>
      </WrapSectionCard>

      <WrapChecklistCard
        title="Critical Checklist"
        icon={ListChecks}
        testId="wrap-sidebar-checklist"
        items={[
          { label: 'Customer info confirmed', done: true },
          { label: 'Vehicle photos uploaded', done: false },
          { label: 'Measurements captured',   done: false },
          { label: 'Quote sent',              done: false },
          { label: 'Deposit collected',       done: false },
        ]}
      />

      <WrapAIHelperCard
        title="AI Suggestions"
        description="Quick context-aware actions"
        testId="wrap-sidebar-ai"
        actions={[
          { label: 'Suggest Next Step' },
          { label: 'Summarize Job Health' },
          { label: 'Write Customer Update' },
        ]}
      />

      <WrapSectionCard title="Internal Notes" icon={NotebookPen} testId="wrap-sidebar-notes">
        <p className="text-xs text-slate-500 italic">No internal notes yet — phase 2 will let staff jot notes here.</p>
      </WrapSectionCard>

      <WrapSectionCard title="Customer Portal Status" icon={UserCheck} testId="wrap-sidebar-portal">
        <p className="text-xs text-slate-700">Portal: <span className="font-medium">Not yet invited</span></p>
        <p className="text-xs text-slate-500 mt-1">Portal access wires up in phase 2.</p>
      </WrapSectionCard>
    </div>
  );
}
