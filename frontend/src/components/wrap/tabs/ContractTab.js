import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapChecklistCard from '../WrapChecklistCard';
import WrapEmptyState from '../WrapEmptyState';
import { FileSignature, ShieldCheck, CreditCard, ClipboardCheck } from 'lucide-react';

export default function ContractTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Contract Status" icon={FileSignature} testId="contract-status">
          <p className="text-sm text-slate-700">Status: <span className="font-medium text-amber-700">Not Sent</span></p>
          <p className="text-xs text-slate-500 mt-1">Phase 2 wires up the e-sign flow.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Signed Contract Storage" icon={ShieldCheck} testId="contract-storage">
          <WrapEmptyState title="No signed contracts yet" />
        </WrapSectionCard>
        <WrapChecklistCard
          title="Approval Checklist"
          icon={ClipboardCheck}
          testId="contract-approvals"
          items={[
            { label: 'Quote Approved', done: false },
            { label: 'Contract Signed', done: false },
            { label: 'Deposit Paid', done: false },
            { label: 'Proof Approved', done: false },
            { label: 'Inspection Acknowledged', done: false },
            { label: 'Final Signoff Completed', done: false },
          ]}
        />
        <WrapSectionCard title="Payment Approval" icon={CreditCard} testId="contract-payment">
          <WrapEmptyState title="Payment activity will appear here" message="Linked from the main order's invoice + Stripe flow." />
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Contract AI Helper"
        testId="contract-ai-helper"
        actions={[
          { label: 'Draft Contract' },
          { label: 'Check Contract' },
          { label: 'Summarize Terms' },
          { label: 'Write Contract Email' },
          { label: 'Write Approval Reminder' },
        ]}
      />
    </div>
  );
}
