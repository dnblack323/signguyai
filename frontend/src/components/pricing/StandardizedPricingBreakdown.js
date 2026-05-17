// Phase 3: Standardized pricing breakdown display.
// Renders the Phase 2 standardized response from POST /api/pricing/calculate
// without removing/changing the legacy display blocks in PricingCalculator.js.

import { useState } from 'react';
import {
  Layers, Wrench, PenTool, Settings, Package, ShieldCheck, Truck,
  ChevronDown, ChevronUp, Info, AlertCircle, CheckCircle, DollarSign,
} from 'lucide-react';

const BUCKETS = [
  { key: 'materials',   costField: 'material_cost',    label: 'Materials',   Icon: Package },
  { key: 'labor',       costField: 'labor_cost',       label: 'Labor',       Icon: Wrench },
  { key: 'design',      costField: 'design_cost',      label: 'Design',      Icon: PenTool },
  { key: 'setup',       costField: 'setup_cost',       label: 'Setup',       Icon: Settings },
  { key: 'finishing',   costField: 'finishing_cost',   label: 'Finishing',   Icon: Layers },
  { key: 'hardware',    costField: 'hardware_cost',    label: 'Hardware',    Icon: Settings },
  { key: 'install',     costField: 'install_cost',     label: 'Install',     Icon: ShieldCheck },
  { key: 'outsourcing', costField: 'outsourcing_cost', label: 'Outsourcing', Icon: Truck },
];

function MarginHealthBanner({ calculation, finalPrice, formatCurrency }) {
  const sellingPrice = Number(finalPrice ?? calculation.selling_price ?? calculation.suggested_price ?? 0);
  const trueCost = Number(calculation.true_cost ?? calculation.production_cost ?? 0);
  // If a manual quote (finalPrice) was provided, the displayed profit must
  // reflect that. Otherwise fall back to the backend-computed profit.
  const profitAmount = (finalPrice != null && finalPrice !== '')
    ? sellingPrice - trueCost
    : Number(calculation.profit_amount ?? 0);
  const profitMargin = sellingPrice > 0
    ? Math.round((profitAmount / sellingPrice) * 1000) / 10
    : Number(calculation.profit_margin_percent ?? 0);

  const issues = [];
  if (profitAmount < 0) {
    issues.push({
      level: 'error',
      msg: `Negative profit: ${formatCurrency(profitAmount)} — selling price is below true cost.`,
    });
  } else if (sellingPrice < trueCost) {
    issues.push({
      level: 'error',
      msg: `Selling price (${formatCurrency(sellingPrice)}) is below true cost (${formatCurrency(trueCost)}).`,
    });
  }
  if (profitAmount >= 0 && profitMargin < 20) {
    issues.push({
      level: 'warning',
      msg: `Profit margin is ${profitMargin}% — below the 20% recommended floor.`,
    });
  }

  if (issues.length === 0) return null;

  const isError = issues.some((i) => i.level === 'error');
  return (
    <div
      className={`p-3 rounded-lg border ${isError ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'}`}
      data-testid="pricing-margin-health-banner"
    >
      <div className={`flex items-center gap-2 text-sm font-medium ${isError ? 'text-red-800' : 'text-amber-800'}`}>
        <AlertCircle className="h-4 w-4" />
        Pricing health check
      </div>
      <ul className={`mt-1 ml-6 text-sm list-disc ${isError ? 'text-red-700' : 'text-amber-700'}`}>
        {issues.map((it, idx) => (
          <li key={idx} data-testid={`pricing-margin-health-${it.level}-${idx}`}>{it.msg}</li>
        ))}
      </ul>
    </div>
  );
}

function TopSummary({ calculation, formatCurrency, finalPrice }) {
  const sellingPrice = Number(finalPrice ?? calculation.selling_price ?? calculation.suggested_price ?? 0);
  const trueCost = Number(calculation.true_cost ?? calculation.production_cost ?? 0);
  const profitAmount = (finalPrice != null && finalPrice !== '')
    ? sellingPrice - trueCost
    : Number(calculation.profit_amount ?? 0);
  const profitMargin = sellingPrice > 0
    ? Math.round((profitAmount / sellingPrice) * 1000) / 10
    : Number(calculation.profit_margin_percent ?? 0);
  const method = calculation.pricing_method_used || '—';

  return (
    <div
      className="grid grid-cols-2 md:grid-cols-5 gap-3"
      data-testid="pricing-standardized-summary"
    >
      <div className="p-3 bg-teal-50 rounded-lg border border-teal-100" data-testid="std-summary-selling-price">
        <p className="text-[11px] uppercase tracking-wide text-teal-700">Selling Price</p>
        <p className="text-lg font-semibold text-teal-800">{formatCurrency(sellingPrice)}</p>
      </div>
      <div className="p-3 bg-slate-50 rounded-lg border border-slate-200" data-testid="std-summary-true-cost">
        <p className="text-[11px] uppercase tracking-wide text-slate-600">True Cost</p>
        <p className="text-lg font-semibold text-slate-800">{formatCurrency(trueCost)}</p>
        <p className="text-[10px] text-slate-500">base + overhead</p>
      </div>
      <div
        className={`p-3 rounded-lg border ${profitAmount >= 0 ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-200'}`}
        data-testid="std-summary-profit"
      >
        <p className={`text-[11px] uppercase tracking-wide ${profitAmount >= 0 ? 'text-green-700' : 'text-red-700'}`}>Profit</p>
        <p className={`text-lg font-semibold ${profitAmount >= 0 ? 'text-green-800' : 'text-red-800'}`}>
          {formatCurrency(profitAmount)}
        </p>
      </div>
      <div
        className={`p-3 rounded-lg border ${profitMargin >= 20 ? 'bg-green-50 border-green-100' : 'bg-amber-50 border-amber-200'}`}
        data-testid="std-summary-margin"
      >
        <p className={`text-[11px] uppercase tracking-wide ${profitMargin >= 20 ? 'text-green-700' : 'text-amber-700'}`}>Margin</p>
        <p className={`text-lg font-semibold ${profitMargin >= 20 ? 'text-green-800' : 'text-amber-800'}`}>
          {profitMargin}%
        </p>
      </div>
      <div className="p-3 bg-violet-50 rounded-lg border border-violet-100" data-testid="std-summary-method">
        <p className="text-[11px] uppercase tracking-wide text-violet-700">Pricing Method</p>
        <p className="text-sm font-semibold text-violet-800 truncate" title={method}>{method}</p>
      </div>
    </div>
  );
}

function BucketSection({ bucket, items, totalCost, formatCurrency }) {
  const { label, Icon, key } = bucket;
  const showAsCurrency = (k) => typeof k === 'string' && (k.includes('cost') || k.includes('price'));
  return (
    <div
      className="border border-slate-200 rounded-lg overflow-hidden bg-white"
      data-testid={`std-bucket-${key}`}
    >
      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-slate-600" />
          <span className="text-sm font-medium text-slate-700">{label}</span>
        </div>
        <span className="text-sm font-semibold text-slate-800" data-testid={`std-bucket-${key}-total`}>
          {formatCurrency(totalCost)}
        </span>
      </div>
      {items.length > 0 && (
        <table className="w-full text-xs">
          <thead className="bg-slate-50/60 text-slate-500">
            <tr>
              <th className="text-left px-3 py-1 font-normal">Item</th>
              <th className="text-right px-3 py-1 font-normal">Qty</th>
              <th className="text-left px-2 py-1 font-normal">Unit</th>
              <th className="text-right px-3 py-1 font-normal">Unit Cost</th>
              <th className="text-right px-3 py-1 font-normal">Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, idx) => (
              <tr key={idx} className="border-t border-slate-100" data-testid={`std-bucket-${key}-row-${idx}`}>
                <td className="px-3 py-1 text-slate-700">
                  {it.name || '—'}
                  {it.notes ? (
                    <span className="ml-1 text-[10px] text-slate-400">({it.notes})</span>
                  ) : null}
                </td>
                <td className="px-3 py-1 text-right text-slate-600">
                  {typeof it.quantity === 'number' ? Math.round(it.quantity * 100) / 100 : it.quantity ?? ''}
                </td>
                <td className="px-2 py-1 text-slate-500">{it.unit || ''}</td>
                <td className="px-3 py-1 text-right text-slate-600">
                  {typeof it.unit_cost === 'number' ? formatCurrency(it.unit_cost) : it.unit_cost ?? ''}
                </td>
                <td className="px-3 py-1 text-right text-slate-800 font-medium">
                  {typeof it.total_cost === 'number' ? formatCurrency(it.total_cost) : it.total_cost ?? ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function OverheadBasisPanel({ overheadCost, overheadBasis, formatCurrency }) {
  const [open, setOpen] = useState(false);
  if (!overheadBasis || Object.keys(overheadBasis).length === 0) {
    return (
      <div className="text-xs text-slate-500" data-testid="std-overhead-basis-empty">
        Overhead: {formatCurrency(overheadCost || 0)} (basis details not provided by this calculator)
      </div>
    );
  }

  return (
    <div className="border border-violet-200 bg-violet-50/50 rounded-lg" data-testid="std-overhead-basis-panel">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm"
        data-testid="std-overhead-basis-toggle"
      >
        <span className="flex items-center gap-2 text-violet-900 font-medium">
          <Info className="h-4 w-4" />
          How overhead was calculated · {formatCurrency(overheadCost || 0)}
        </span>
        {open ? <ChevronUp className="h-4 w-4 text-violet-700" /> : <ChevronDown className="h-4 w-4 text-violet-700" />}
      </button>
      {open && (
        <div className="px-3 pb-3 text-xs text-violet-900 space-y-1.5">
          {overheadBasis.formula && (
            <div className="font-mono text-[11px] bg-white/80 rounded px-2 py-1 break-words">
              {overheadBasis.formula}
            </div>
          )}
          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
            {overheadBasis.basis_amount !== undefined && (
              <>
                <span className="text-violet-700">Basis amount</span>
                <span className="text-right font-medium">{formatCurrency(overheadBasis.basis_amount)}</span>
              </>
            )}
            {overheadBasis.overhead_percentage !== undefined && (
              <>
                <span className="text-violet-700">Overhead %</span>
                <span className="text-right font-medium">{overheadBasis.overhead_percentage}%</span>
              </>
            )}
            {overheadBasis.labor_hours !== undefined && (
              <>
                <span className="text-violet-700">Labor hours</span>
                <span className="text-right font-medium">{overheadBasis.labor_hours}</span>
              </>
            )}
            {overheadBasis.shop_overhead_per_hour !== undefined && (
              <>
                <span className="text-violet-700">Shop overhead / hr</span>
                <span className="text-right font-medium">{formatCurrency(overheadBasis.shop_overhead_per_hour)}</span>
              </>
            )}
            {overheadBasis.overhead_excludes_setup_cost !== undefined && (
              <>
                <span className="text-violet-700">Excludes setup cost</span>
                <span className="text-right font-medium">
                  {overheadBasis.overhead_excludes_setup_cost ? 'Yes' : 'No'}
                </span>
              </>
            )}
          </div>
          {Array.isArray(overheadBasis.basis_components) && overheadBasis.basis_components.length > 0 && (
            <div>
              <p className="text-violet-700 mt-1.5">Basis components:</p>
              <ul className="ml-4 list-disc text-violet-900">
                {overheadBasis.basis_components.map((c, idx) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>
          )}
          {overheadBasis.notes && (
            <p className="mt-1.5 italic text-violet-700">{overheadBasis.notes}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function StandardizedPricingBreakdown({ calculation, formatCurrency, finalPrice }) {
  if (!calculation || typeof calculation !== 'object') return null;

  const breakdown = calculation.breakdown || {};
  const metadata = breakdown.metadata || {};
  const overheadBasis = metadata.overhead_basis;

  // Filter buckets: include only those with a non-zero total OR a non-empty array.
  const visibleBuckets = BUCKETS.map((b) => {
    const items = Array.isArray(breakdown[b.key]) ? breakdown[b.key] : [];
    const total = Number(calculation[b.costField] ?? 0);
    return { bucket: b, items, total };
  }).filter(({ items, total }) => items.length > 0 || total > 0);

  const overheadCost = Number(calculation.overhead_cost ?? 0);

  return (
    <div className="space-y-3 pt-2" data-testid="standardized-pricing-breakdown">
      <div className="flex items-center gap-2">
        <CheckCircle className="h-4 w-4 text-teal-600" />
        <h3 className="text-sm font-semibold text-slate-800">Standardized Cost Breakdown</h3>
      </div>

      <MarginHealthBanner
        calculation={calculation}
        finalPrice={finalPrice}
        formatCurrency={formatCurrency}
      />

      <TopSummary
        calculation={calculation}
        finalPrice={finalPrice}
        formatCurrency={formatCurrency}
      />

      {visibleBuckets.length > 0 && (
        <div className="grid gap-2" data-testid="std-buckets">
          {visibleBuckets.map(({ bucket, items, total }) => (
            <BucketSection
              key={bucket.key}
              bucket={bucket}
              items={items}
              totalCost={total}
              formatCurrency={formatCurrency}
            />
          ))}
        </div>
      )}

      <OverheadBasisPanel
        overheadCost={overheadCost}
        overheadBasis={overheadBasis}
        formatCurrency={formatCurrency}
      />
    </div>
  );
}
