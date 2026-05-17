// Phase 1: Overview tab — summary cards + AI helper.
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapChecklistCard from '../WrapChecklistCard';
import { User, Car, Layers, DollarSign, ClipboardCheck, Bot } from 'lucide-react';

export default function OverviewTab({ header }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Customer Summary" icon={User} testId="overview-customer">
          <p><span className="text-slate-500">Customer:</span> {header.customer_name}</p>
          {header.business_name && <p><span className="text-slate-500">Business:</span> {header.business_name}</p>}
          <p className="text-xs text-slate-500 mt-1">Phone, email and contact log will appear here in phase 2.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Vehicle Summary" icon={Car} testId="overview-vehicle">
          <p>{header.vehicle}</p>
          <p className="text-xs text-slate-500 mt-1">Year/make/model details & body type pull from the Vehicle Info tab.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Wrap Summary" icon={Layers} testId="overview-wrap">
          <p><span className="text-slate-500">Type:</span> {header.wrap_type}</p>
          <p className="text-xs text-slate-500 mt-1">Coverage, material brand and waste % will sync from Measurements & Pricing.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Money Summary" icon={DollarSign} testId="overview-money">
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div><p className="text-[10px] uppercase text-slate-500">Quoted</p><p className="font-semibold">${(header.quoted_price || 0).toLocaleString()}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Deposit</p><p className="font-semibold">{header.deposit_status}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Balance</p><p className="font-semibold text-rose-700">${(header.balance_due || 0).toLocaleString()}</p></div>
          </div>
        </WrapSectionCard>
        <WrapChecklistCard
          title="Critical Checklist"
          icon={ClipboardCheck}
          testId="overview-checklist"
          items={[
            { label: 'Customer info confirmed', done: true },
            { label: 'Vehicle photos uploaded', done: false },
            { label: 'Measurements captured', done: false },
            { label: 'Quote sent', done: false },
            { label: 'Contract signed', done: false },
            { label: 'Deposit paid', done: false },
            { label: 'Proof approved', done: false },
          ]}
        />
        <WrapSectionCard title="AI Job Assistant" icon={Bot} testId="overview-ai-job">
          <p className="text-xs text-slate-500">Job-level AI workspace lives on the AI Assistant tab. The card to the right surfaces the most-used quick actions for the Overview context.</p>
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Overview AI Helper"
        description="Context-aware AI for this section"
        testId="overview-ai-helper"
        actions={[
          { label: 'Check Missing Info' },
          { label: 'Suggest Next Step' },
          { label: 'Summarize Job Health' },
          { label: 'Check Profit Risk' },
          { label: 'Write Follow-Up' },
        ]}
      />
    </div>
  );
}
