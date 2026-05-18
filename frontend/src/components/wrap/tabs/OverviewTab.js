// Phase 2E: Overview tab — real read-only summary cards built from wrapData/order/customer.
// No editing here; each card has a "Go to tab" button.
import WrapSectionCard from '../WrapSectionCard';
import { Button } from '../../ui/button';
import { User, Car, Layers, Ruler, DollarSign, ClipboardList, FileSignature, ClipboardCheck, Factory, Calendar, LifeBuoy, Sparkles } from 'lucide-react';
import { getNextBestAction } from '../summaryHelpers';

const money = (n) => (n === null || n === undefined || Number.isNaN(Number(n))
  ? '—'
  : `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

function GoTo({ tab, onJumpToTab, testId }) {
  if (!onJumpToTab) return null;
  return (
    <Button size="sm" variant="outline" onClick={() => onJumpToTab(tab)} className="text-xs h-7" data-testid={testId}>
      Go to tab
    </Button>
  );
}

function Row({ label, value, testId }) {
  return (
    <div className="flex justify-between gap-3 text-sm py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800 text-right break-words" data-testid={testId}>{value || '—'}</span>
    </div>
  );
}

function YesNo({ value }) {
  return <span className={`text-xs font-medium ${value ? 'text-emerald-700' : 'text-slate-500'}`}>{value ? 'Yes' : 'No'}</span>;
}

export default function OverviewTab({ wrapData, header, onJumpToTab }) {
  const v = wrapData?.vehicle_info || {};
  const coverage = wrapData?.coverage_summary || {};
  const snapshot = wrapData?.pricing_snapshot;
  const pricing = wrapData?.pricing || {};
  const design = wrapData?.design || {};
  const contract = wrapData?.contract || {};
  const approvals = wrapData?.approvals || {};
  const inspection = wrapData?.inspection || {};
  const production = wrapData?.production || {};
  const install = wrapData?.install || {};
  const aftercare = wrapData?.aftercare || {};
  const tasks = production.tasks || [];
  const completedTasks = tasks.filter((t) => t.status === 'complete').length;
  const openIssues = (install.issues || []).filter((i) => !i.resolved).length;
  const followupCompleted = ['followup_24h', 'followup_7d', 'followup_30d'].filter((k) => aftercare[k]).length;

  const nba = getNextBestAction(wrapData);

  return (
    <div className="space-y-3" data-testid="overview-tab">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <WrapSectionCard title="Customer" icon={User} testId="overview-customer" action={<GoTo tab="contract" onJumpToTab={onJumpToTab} testId="overview-customer-goto" />}>
          <Row label="Customer" value={header?.customer_name} testId="overview-customer-name" />
          <Row label="Business" value={header?.business_name} />
          <Row label="Order" value={header?.order_number} testId="overview-order-number" />
        </WrapSectionCard>

        <WrapSectionCard title="Vehicle" icon={Car} testId="overview-vehicle" action={<GoTo tab="vehicle" onJumpToTab={onJumpToTab} testId="overview-vehicle-goto" />}>
          <Row label="Year/Make/Model" value={[v.year, v.make, v.model].filter(Boolean).join(' ')} testId="overview-vehicle-ymm" />
          <Row label="Trim" value={v.trim} />
          <Row label="Body Type" value={v.body_type} />
          <Row label="Color" value={v.vehicle_color} />
          <Row label="Wrap Type" value={header?.wrap_type} />
        </WrapSectionCard>

        <WrapSectionCard title="Wrap Summary" icon={Layers} testId="overview-wrap" action={<GoTo tab="ai" onJumpToTab={onJumpToTab} testId="overview-wrap-goto" />}>
          <Row label="Wrap Type" value={header?.wrap_type} />
          <Row label="Current Status" value={(install.install_status === 'complete' && 'Complete') || (production.production_status && production.production_status.replace(/_/g, ' ')) || 'Lead'} testId="overview-wrap-status" />
          <Row label="Next Best Action" value={nba.label} testId="overview-nba" />
        </WrapSectionCard>

        <WrapSectionCard title="Measurements" icon={Ruler} testId="overview-measurements" action={<GoTo tab="measurements" onJumpToTab={onJumpToTab} testId="overview-meas-goto" />}>
          <Row label="Total Raw" value={`${(coverage.total_raw_sqft || 0).toFixed(2)} ft²`} testId="overview-total-raw" />
          <Row label="Total Billable" value={`${(coverage.total_billable_sqft || 0).toFixed(2)} ft²`} testId="overview-total-billable" />
          <Row label="Included Areas" value={coverage.included_count ?? 0} testId="overview-included-count" />
          <Row label="Excluded Areas" value={coverage.excluded_count ?? 0} testId="overview-excluded-count" />
        </WrapSectionCard>

        <WrapSectionCard title="Pricing" icon={DollarSign} testId="overview-money" action={<GoTo tab="pricing" onJumpToTab={onJumpToTab} testId="overview-pricing-goto" />}>
          <Row label="Quoted Price" value={money(snapshot?.quoted_price)} testId="overview-quoted-price" />
          <Row label="Estimated Profit" value={money(snapshot?.estimated_profit)} testId="overview-profit" />
          <Row label="Estimated Margin" value={snapshot ? `${Number(snapshot.estimated_margin_percent || 0).toFixed(1)}%` : '—'} testId="overview-margin" />
          <Row label="Pricing Method" value={(pricing.pricing_method || 'material_labor_markup').replace(/_/g, ' ')} testId="overview-pricing-method" />
        </WrapSectionCard>

        <WrapSectionCard title="Design & Proofs" icon={ClipboardList} testId="overview-design" action={<GoTo tab="design" onJumpToTab={onJumpToTab} testId="overview-design-goto" />}>
          <Row label="Questionnaire" value={(design.questionnaire_status || 'not_sent').replace(/_/g, ' ')} testId="overview-q-status" />
          <Row label="Mockup" value={(design.mockup_status || 'not_started').replace(/_/g, ' ')} />
          <Row label="Proof" value={(design.proof_status || 'not_started').replace(/_/g, ' ')} testId="overview-proof-status" />
          <Row label="Revisions" value={design.revision_count || 0} />
        </WrapSectionCard>

        <WrapSectionCard title="Contract & Approvals" icon={FileSignature} testId="overview-checklist" action={<GoTo tab="contract" onJumpToTab={onJumpToTab} testId="overview-contract-goto" />}>
          <Row label="Contract Status" value={(contract.contract_status || 'not_created').replace(/_/g, ' ')} testId="overview-contract-status" />
          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-xs mt-1">
            <div className="flex justify-between"><span className="text-slate-500">Quote Approved</span><YesNo value={approvals.quote_approved} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Contract Signed</span><YesNo value={approvals.contract_signed} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Deposit Paid</span><YesNo value={approvals.deposit_paid} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Proof Approved</span><YesNo value={approvals.proof_approved} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Inspection Ack</span><YesNo value={approvals.inspection_acknowledged} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Final Signoff</span><YesNo value={approvals.final_signoff_completed} /></div>
            <div className="flex justify-between"><span className="text-slate-500">Aftercare Sent</span><YesNo value={approvals.aftercare_sent} /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Inspection" icon={ClipboardCheck} testId="overview-inspection" action={<GoTo tab="inspection" onJumpToTab={onJumpToTab} testId="overview-inspection-goto" />}>
          <Row label="Status" value={(inspection.inspection_status || 'not_started').replace(/_/g, ' ')} />
          <Row label="Damage Markers" value={(inspection.damage_markers || []).length} testId="overview-damage-count" />
          <Row label="Customer Ack" value={inspection.customer_acknowledged ? 'Yes' : 'No'} />
        </WrapSectionCard>

        <WrapSectionCard title="Production" icon={Factory} testId="overview-production" action={<GoTo tab="production" onJumpToTab={onJumpToTab} testId="overview-production-goto" />}>
          <Row label="Status" value={(production.production_status || 'not_started').replace(/_/g, ' ')} testId="overview-production-status" />
          <Row label="Ready for Install" value={production.ready_for_install ? 'Yes' : 'No'} />
          <Row label="Tasks Completed" value={`${completedTasks} / ${tasks.length}`} testId="overview-tasks-progress" />
          <Row label="Assigned To" value={production.assigned_to} />
        </WrapSectionCard>

        <WrapSectionCard title="Install" icon={Calendar} testId="overview-install" action={<GoTo tab="install" onJumpToTab={onJumpToTab} testId="overview-install-goto" />}>
          <Row label="Status" value={(install.install_status || 'not_scheduled').replace(/_/g, ' ')} testId="overview-install-status" />
          <Row label="Install Date" value={install.install_date} />
          <Row label="Installer" value={install.installer_name} />
          <Row label="Actual Hours" value={install.hours_actual} />
          <Row label="Customer Signoff" value={install.customer_signoff ? 'Yes' : 'No'} />
          <Row label="Open Issues" value={openIssues} testId="overview-open-issues" />
        </WrapSectionCard>

        <WrapSectionCard title="Aftercare" icon={LifeBuoy} testId="overview-aftercare" action={<GoTo tab="aftercare" onJumpToTab={onJumpToTab} testId="overview-aftercare-goto" />}>
          <Row label="Status" value={(aftercare.aftercare_status || 'not_sent').replace(/_/g, ' ')} />
          <Row label="Sent" value={aftercare.aftercare_sent ? 'Yes' : 'No'} testId="overview-aftercare-sent" />
          <Row label="Viewed" value={aftercare.customer_viewed ? 'Yes' : 'No'} />
          <Row label="Acknowledged" value={aftercare.customer_acknowledged ? 'Yes' : 'No'} />
          <Row label="Follow-ups" value={`${followupCompleted} / 3`} />
        </WrapSectionCard>

        <WrapSectionCard title="Next Best Action" icon={Sparkles} testId="overview-next-action">
          <p className="text-sm text-slate-800" data-testid="overview-nba-label">{nba.label}</p>
          {onJumpToTab && nba.tab !== 'overview' && (
            <Button size="sm" className="mt-2 bg-violet-600 hover:bg-violet-700 text-white" onClick={() => onJumpToTab(nba.tab)} data-testid="overview-nba-go">
              Go to {nba.tab}
            </Button>
          )}
        </WrapSectionCard>
      </div>
    </div>
  );
}
