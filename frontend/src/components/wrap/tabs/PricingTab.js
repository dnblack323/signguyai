import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapDataTable from '../WrapDataTable';
import WrapActionButtonGroup from '../WrapActionButtonGroup';
import { DollarSign, Package, Send } from 'lucide-react';

export default function PricingTab({ header }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Pricing Summary" icon={DollarSign} testId="pricing-summary">
          <div className="grid grid-cols-4 gap-3 text-sm">
            <div><p className="text-[10px] uppercase text-slate-500">Materials</p><p className="font-semibold">—</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Labor</p><p className="font-semibold">—</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Quote</p><p className="font-semibold">${(header.quoted_price || 0).toLocaleString()}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Profit</p><p className="font-semibold text-emerald-700">—</p></div>
          </div>
        </WrapSectionCard>
        <WrapSectionCard title="Materials Used" icon={Package} testId="pricing-materials">
          <WrapDataTable
            testId="pricing-materials-table"
            columns={['Material', 'Brand', 'Sq Ft Used', 'Cost', 'In Stock', 'Notes']}
            rows={[
              ['Printed Wrap', '3M IJ180Cv3', '—', '—', '—', '—'],
              ['Laminate', '3M 8519', '—', '—', '—', '—'],
            ]}
          />
        </WrapSectionCard>
        <WrapSectionCard title="Labor Estimate" icon={DollarSign} testId="pricing-labor">
          <p className="text-xs text-slate-500">Production + install labor breakdown will sync from category defaults in phase 2.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Profit Estimate" icon={DollarSign} testId="pricing-profit">
          <p className="text-xs text-slate-500">True cost vs selling price comparison populates from the standardized pricing API.</p>
        </WrapSectionCard>
        <WrapSectionCard title="Quote Actions" icon={Send} testId="pricing-actions">
          <WrapActionButtonGroup
            testId="pricing-quote-actions"
            actions={[
              { label: 'Send Quote', icon: Send },
              { label: 'Re-Calculate' },
              { label: 'Open Pricing Calculator' },
            ]}
          />
        </WrapSectionCard>
      </div>
      <WrapAIHelperCard
        title="Pricing AI Helper"
        testId="pricing-ai-helper"
        actions={[
          { label: 'Suggest Price' },
          { label: 'Check Profit' },
          { label: 'Recommend Material' },
          { label: 'Compare to Shop Defaults' },
          { label: 'Write Quote Explanation' },
        ]}
      />
    </div>
  );
}
