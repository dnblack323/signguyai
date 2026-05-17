import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapActionButtonGroup from '../WrapActionButtonGroup';
import WrapEmptyState from '../WrapEmptyState';
import { Heart, FileText, Send, CheckCircle2, CalendarClock } from 'lucide-react';

export default function AftercareTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Aftercare Status" icon={Heart} testId="aftercare-status">
          <p className="text-sm text-slate-700">Status: <span className="font-medium text-amber-700">Not Sent</span></p>
        </WrapSectionCard>
        <WrapSectionCard title="Aftercare PDF" icon={FileText} testId="aftercare-pdf">
          <WrapEmptyState title="PDF will be generated in phase 2" />
        </WrapSectionCard>
        <WrapSectionCard title="Customer Acknowledgment" icon={CheckCircle2} testId="aftercare-ack">
          <p className="text-xs text-slate-500">Customer view + acknowledge tracking arrives in phase 2.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Follow-Up Reminder" icon={CalendarClock} testId="aftercare-followup">
          <p className="text-xs text-slate-500">Auto-scheduled 30/90-day check-ins.</p>
        </WrapSectionCard>
        <WrapActionButtonGroup
          testId="aftercare-actions"
          actions={[
            { label: 'Generate Aftercare', icon: FileText },
            { label: 'Send Aftercare', icon: Send },
            { label: 'Mark Viewed', icon: CheckCircle2 },
            { label: 'Schedule Follow-Up', icon: CalendarClock },
          ]}
        />
      </div>
      <WrapAIHelperCard
        title="Aftercare AI Helper"
        testId="aftercare-ai-helper"
        actions={[
          { label: 'Generate Aftercare' },
          { label: 'Customize by Material' },
          { label: 'Write Aftercare Email' },
          { label: 'Write Warranty Explanation' },
          { label: 'Write Review Request' },
          { label: 'Suggest Follow-Up' },
        ]}
      />
    </div>
  );
}
