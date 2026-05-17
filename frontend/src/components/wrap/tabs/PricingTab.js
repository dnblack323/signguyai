// Phase 2B: Pricing & Materials tab — full editable pricing + materials CRUD.
// Reads coverage_summary.total_billable_sqft and pricing_snapshot from
// /api/wrap/items/{id}. Saves to /api/wrap/items/{id}/pricing and
// /api/wrap/items/{id}/materials. "Apply to Order" pushes quoted_price
// into the JobTicket so the main Orders Dashboard reflects it.

import { useEffect, useMemo, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { DollarSign, Package, Send, Calculator, Save, Plus, Pencil, Trash2, Check, X } from 'lucide-react';

const MATERIAL_TYPES = [
  { value: 'printed_wrap_vinyl', label: 'Printed Wrap Vinyl' },
  { value: 'color_change_vinyl', label: 'Color Change Vinyl' },
  { value: 'laminate', label: 'Laminate' },
  { value: 'window_perf', label: 'Window Perf' },
  { value: 'transfer_tape', label: 'Transfer Tape' },
  { value: 'knifeless_tape', label: 'Knifeless Tape' },
  { value: 'primer', label: 'Primer' },
  { value: 'edge_sealer', label: 'Edge Sealer' },
  { value: 'cleaning_prep_supply', label: 'Cleaning / Prep Supply' },
  { value: 'other', label: 'Other' },
];

const DEFAULT_PRICING = {
  pricing_method: 'material_labor_markup',
  price_per_sqft: 0,
  design_hours: 0,
  production_hours: 0,
  install_hours: 0,
  labor_rate: 75,
  removal_fee: 0,
  prep_fee: 0,
  rush_fee: 0,
  travel_fee: 0,
  setup_design_fee: 0,
  misc_cost: 0,
  laminate_cost: 0,
  ink_consumables_cost: 0,
  markup_percent: 30,
  manual_quoted_price: '',
};

const EMPTY_MATERIAL = {
  material_name: '', brand: '', product_code: '', material_type: 'printed_wrap_vinyl',
  roll_width: '', sqft_used: '', cost_per_sqft: '',
  supplier: '', in_stock: false, ordered: false, notes: '',
};

const money = (n) => (n === null || n === undefined || Number.isNaN(Number(n))
  ? '—'
  : `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

function MaterialForm({ initial, onCancel, onSubmit, busy, testIdPrefix }) {
  const [form, setForm] = useState(initial || EMPTY_MATERIAL);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const sub = () => onSubmit({
    material_name: form.material_name || 'Untitled',
    brand: form.brand || '',
    product_code: form.product_code || '',
    material_type: form.material_type || 'other',
    roll_width: form.roll_width || '',
    sqft_used: form.sqft_used === '' ? null : Number(form.sqft_used),
    cost_per_sqft: form.cost_per_sqft === '' ? null : Number(form.cost_per_sqft),
    supplier: form.supplier || '',
    in_stock: !!form.in_stock,
    ordered: !!form.ordered,
    notes: form.notes || '',
  });
  return (
    <div className="p-3 bg-violet-50/50 rounded-md border border-violet-200 space-y-2" data-testid={`${testIdPrefix}-form`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <div className="md:col-span-2"><Label className="text-xs">Material Name</Label><Input value={form.material_name} onChange={(e) => set('material_name', e.target.value)} placeholder="Printed Wrap Vinyl" data-testid={`${testIdPrefix}-name`} /></div>
        <div><Label className="text-xs">Brand</Label><Input value={form.brand} onChange={(e) => set('brand', e.target.value)} placeholder="3M IJ180Cv3" data-testid={`${testIdPrefix}-brand`} /></div>
        <div><Label className="text-xs">Product Code</Label><Input value={form.product_code} onChange={(e) => set('product_code', e.target.value)} data-testid={`${testIdPrefix}-code`} /></div>
        <div>
          <Label className="text-xs">Type</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.material_type} onChange={(e) => set('material_type', e.target.value)} data-testid={`${testIdPrefix}-type`}>
            {MATERIAL_TYPES.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
        </div>
        <div><Label className="text-xs">Roll Width</Label><Input value={form.roll_width} onChange={(e) => set('roll_width', e.target.value)} placeholder='60"' data-testid={`${testIdPrefix}-roll`} /></div>
        <div><Label className="text-xs">Sq Ft Used</Label><Input type="number" value={form.sqft_used} onChange={(e) => set('sqft_used', e.target.value)} data-testid={`${testIdPrefix}-sqft`} /></div>
        <div><Label className="text-xs">Cost / Sq Ft</Label><Input type="number" value={form.cost_per_sqft} onChange={(e) => set('cost_per_sqft', e.target.value)} data-testid={`${testIdPrefix}-cps`} /></div>
        <div className="md:col-span-2"><Label className="text-xs">Supplier</Label><Input value={form.supplier} onChange={(e) => set('supplier', e.target.value)} placeholder="Grimco" data-testid={`${testIdPrefix}-supplier`} /></div>
        <div className="md:col-span-2"><Label className="text-xs">Notes</Label><Input value={form.notes} onChange={(e) => set('notes', e.target.value)} data-testid={`${testIdPrefix}-notes`} /></div>
        <div className="flex items-center gap-3 md:col-span-2 mt-5">
          <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={!!form.in_stock} onChange={(e) => set('in_stock', e.target.checked)} data-testid={`${testIdPrefix}-instock`} /> In stock</label>
          <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={!!form.ordered} onChange={(e) => set('ordered', e.target.checked)} data-testid={`${testIdPrefix}-ordered`} /> Ordered</label>
        </div>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button size="sm" variant="outline" onClick={onCancel} data-testid={`${testIdPrefix}-cancel`}><X className="h-3.5 w-3.5 mr-1" /> Cancel</Button>
        <Button size="sm" onClick={sub} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid={`${testIdPrefix}-submit`}><Check className="h-3.5 w-3.5 mr-1" /> Save Material</Button>
      </div>
    </div>
  );
}

export default function PricingTab({
  header, wrapData,
  onSavePricing, onRecalculate, onApplyPrice,
  onAddMaterial, onUpdateMaterial, onDeleteMaterial,
  saveStatus,
}) {
  const coverage = wrapData?.coverage_summary || { total_billable_sqft: 0, total_raw_sqft: 0 };
  const materials = wrapData?.materials || [];
  const snapshot = wrapData?.pricing_snapshot;

  const [pricing, setPricing] = useState({ ...DEFAULT_PRICING });
  const [dirty, setDirty] = useState(false);
  const [showAddMat, setShowAddMat] = useState(false);
  const [editingMatId, setEditingMatId] = useState(null);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    const incoming = wrapData?.pricing || {};
    const merged = { ...DEFAULT_PRICING, ...incoming };
    if (merged.manual_quoted_price === null || merged.manual_quoted_price === undefined) {
      merged.manual_quoted_price = '';
    }
    setPricing(merged);
    setDirty(false);
  }, [wrapData]);

  const setField = (key, value) => {
    setPricing((p) => ({ ...p, [key]: value }));
    setDirty(true);
  };

  // Local preview math (mirrors backend) so user sees numbers move while typing.
  const localSnapshot = useMemo(() => {
    const n = (v) => { const x = Number(v); return Number.isFinite(x) ? x : 0; };
    const billable = n(coverage.total_billable_sqft);
    const labor = (n(pricing.design_hours) + n(pricing.production_hours) + n(pricing.install_hours)) * n(pricing.labor_rate);
    const matSum = (materials || []).reduce((s, m) => s + n(m.total_material_cost), 0);
    const materialTotal = matSum + n(pricing.laminate_cost) + n(pricing.ink_consumables_cost);
    const baseCost = materialTotal + labor + n(pricing.removal_fee) + n(pricing.prep_fee) + n(pricing.travel_fee) + n(pricing.misc_cost);
    const markupAmount = baseCost * n(pricing.markup_percent) / 100;
    const mlmSuggested = baseCost + markupAmount + n(pricing.setup_design_fee) + n(pricing.rush_fee);
    const perSqft = billable * n(pricing.price_per_sqft) + n(pricing.setup_design_fee) + n(pricing.rush_fee) + n(pricing.travel_fee) + n(pricing.prep_fee) + n(pricing.removal_fee) + n(pricing.misc_cost);
    const manual = pricing.manual_quoted_price === '' || pricing.manual_quoted_price === null ? null : n(pricing.manual_quoted_price);
    let suggested = mlmSuggested;
    let quoted = mlmSuggested;
    let method = pricing.pricing_method || 'material_labor_markup';
    if (method === 'manual' && manual !== null) { quoted = manual; suggested = manual; }
    else if (method === 'per_sqft') { suggested = perSqft; quoted = manual !== null ? manual : perSqft; }
    else { quoted = manual !== null ? manual : mlmSuggested; }
    const profit = quoted - baseCost;
    const margin = quoted ? (profit / quoted) * 100 : 0;
    return {
      total_billable_sqft: billable, total_labor_cost: labor, material_total: materialTotal,
      base_cost: baseCost, markup_amount: markupAmount, suggested_price: suggested,
      per_sqft_price: perSqft, quoted_price: quoted, estimated_profit: profit, estimated_margin_percent: margin,
    };
  }, [pricing, materials, coverage]);

  const view = dirty ? localSnapshot : (snapshot || localSnapshot);

  const handleSavePricing = async () => {
    const payload = {
      ...pricing,
      manual_quoted_price: pricing.manual_quoted_price === '' ? null : Number(pricing.manual_quoted_price),
    };
    const ok = await onSavePricing?.(payload);
    if (ok) setDirty(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Pricing Summary"
          icon={DollarSign}
          testId="pricing-summary"
          action={
            <div className="flex items-center gap-2">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="pricing-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" variant="outline" onClick={onRecalculate} disabled={busy} data-testid="pricing-recalc-btn"><Calculator className="h-3.5 w-3.5 mr-1" /> Recalculate</Button>
              <Button size="sm" onClick={handleSavePricing} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="pricing-save-btn"><Save className="h-3.5 w-3.5 mr-1" /> Save Pricing</Button>
              <Button size="sm" variant="outline" onClick={onApplyPrice} disabled={busy} className="bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100" data-testid="pricing-apply-btn"><Send className="h-3.5 w-3.5 mr-1" /> Apply to Order</Button>
            </div>
          }
        >
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 text-sm">
            <div><p className="text-[10px] uppercase text-slate-500">Billable Sq Ft</p><p className="font-semibold" data-testid="pricing-billable-sqft">{view.total_billable_sqft.toFixed(2)} ft²</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Material Total</p><p className="font-semibold" data-testid="pricing-material-total">{money(view.material_total)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Labor</p><p className="font-semibold" data-testid="pricing-labor-total">{money(view.total_labor_cost)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Base Cost</p><p className="font-semibold" data-testid="pricing-base-cost">{money(view.base_cost)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Quoted</p><p className="font-semibold text-violet-700" data-testid="pricing-quoted">{money(view.quoted_price)}</p></div>
            <div>
              <p className="text-[10px] uppercase text-slate-500">Profit / Margin</p>
              <p className="font-semibold" data-testid="pricing-profit-margin">
                <span className={view.estimated_profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}>{money(view.estimated_profit)}</span>
                {' '}<span className="text-xs text-slate-500">({view.estimated_margin_percent.toFixed(1)}%)</span>
              </p>
            </div>
          </div>
          {snapshot && (
            <p className="text-[11px] text-slate-500 mt-2" data-testid="pricing-snapshot-meta">
              Last saved snapshot: {snapshot.computed_at ? new Date(snapshot.computed_at).toLocaleString() : '—'} ·
              method <span className="font-medium">{snapshot.pricing_method}</span> ·
              suggested {money(snapshot.suggested_price)}
            </p>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Pricing Method" icon={DollarSign} testId="pricing-method">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-3">
            {[
              ['material_labor_markup', 'Material + Labor + Markup'],
              ['per_sqft', 'Per Square Foot'],
              ['manual', 'Manual Override'],
            ].map(([val, label]) => (
              <label
                key={val}
                className={`flex items-center gap-2 p-2 border rounded cursor-pointer ${pricing.pricing_method === val ? 'border-violet-500 bg-violet-50' : 'border-slate-200'}`}
                data-testid={`pricing-method-${val}`}
              >
                <input
                  type="radio"
                  name="pricing-method"
                  value={val}
                  checked={pricing.pricing_method === val}
                  onChange={(e) => setField('pricing_method', e.target.value)}
                />
                <span className="text-sm">{label}</span>
              </label>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div><Label className="text-xs">Price / Sq Ft</Label><Input type="number" value={pricing.price_per_sqft} onChange={(e) => setField('price_per_sqft', e.target.value)} data-testid="pricing-input-price_per_sqft" /></div>
            <div><Label className="text-xs">Manual Quoted Price (override)</Label><Input type="number" value={pricing.manual_quoted_price} onChange={(e) => setField('manual_quoted_price', e.target.value)} placeholder="leave blank for auto" data-testid="pricing-input-manual_quoted_price" /></div>
            <div><Label className="text-xs">Markup %</Label><Input type="number" value={pricing.markup_percent} onChange={(e) => setField('markup_percent', e.target.value)} data-testid="pricing-input-markup_percent" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Labor" icon={DollarSign} testId="pricing-labor">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div><Label className="text-xs">Design Hours</Label><Input type="number" value={pricing.design_hours} onChange={(e) => setField('design_hours', e.target.value)} data-testid="pricing-input-design_hours" /></div>
            <div><Label className="text-xs">Production Hours</Label><Input type="number" value={pricing.production_hours} onChange={(e) => setField('production_hours', e.target.value)} data-testid="pricing-input-production_hours" /></div>
            <div><Label className="text-xs">Install Hours</Label><Input type="number" value={pricing.install_hours} onChange={(e) => setField('install_hours', e.target.value)} data-testid="pricing-input-install_hours" /></div>
            <div><Label className="text-xs">Labor Rate ($/hr)</Label><Input type="number" value={pricing.labor_rate} onChange={(e) => setField('labor_rate', e.target.value)} data-testid="pricing-input-labor_rate" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Fees & Other Costs" icon={DollarSign} testId="pricing-fees">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ['removal_fee', 'Removal Fee'],
              ['prep_fee', 'Prep / Cleaning Fee'],
              ['rush_fee', 'Rush Fee'],
              ['travel_fee', 'Travel Fee'],
              ['setup_design_fee', 'Setup / Design Fee'],
              ['laminate_cost', 'Laminate Cost'],
              ['ink_consumables_cost', 'Ink / Consumables'],
              ['misc_cost', 'Misc Cost'],
            ].map(([k, label]) => (
              <div key={k}>
                <Label className="text-xs">{label}</Label>
                <Input type="number" value={pricing[k]} onChange={(e) => setField(k, e.target.value)} data-testid={`pricing-input-${k}`} />
              </div>
            ))}
          </div>
        </WrapSectionCard>

        <WrapSectionCard
          title="Materials Used"
          icon={Package}
          testId="pricing-materials"
          action={!showAddMat && <Button size="sm" onClick={() => { setShowAddMat(true); setEditingMatId(null); }} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="material-add-btn"><Plus className="h-3.5 w-3.5 mr-1" /> Add Material</Button>}
        >
          {showAddMat && (
            <div className="mb-3">
              <MaterialForm
                onCancel={() => setShowAddMat(false)}
                onSubmit={async (p) => { await onAddMaterial?.(p); setShowAddMat(false); }}
                busy={busy}
                testIdPrefix="material-add"
              />
            </div>
          )}
          {materials.length === 0 && !showAddMat ? (
            <p className="text-sm text-slate-500 italic py-3" data-testid="materials-empty">
              No materials added yet. Click <span className="font-medium">Add Material</span> to begin.
            </p>
          ) : (
            <div className="space-y-2" data-testid="materials-list">
              {materials.map((m) => {
                if (editingMatId === m.id) {
                  return (
                    <MaterialForm
                      key={m.id}
                      initial={{ ...m, sqft_used: m.sqft_used ?? '', cost_per_sqft: m.cost_per_sqft ?? '' }}
                      onCancel={() => setEditingMatId(null)}
                      onSubmit={async (p) => { await onUpdateMaterial?.(m.id, p); setEditingMatId(null); }}
                      busy={busy}
                      testIdPrefix={`material-edit-${m.id}`}
                    />
                  );
                }
                return (
                  <div
                    key={m.id}
                    className="flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md bg-white"
                    data-testid={`material-row-${m.id}`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-sm text-slate-800">{m.material_name || 'Untitled'}</p>
                        {m.brand && <span className="text-xs text-slate-500">{m.brand}</span>}
                        {m.in_stock && <span className="text-[10px] uppercase bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-200">In Stock</span>}
                        {m.ordered && <span className="text-[10px] uppercase bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200">Ordered</span>}
                      </div>
                      <p className="text-xs text-slate-500">
                        {(MATERIAL_TYPES.find((t) => t.value === m.material_type) || {}).label || m.material_type}
                        {' · '}
                        {m.sqft_used ?? '—'} ft² × {money(m.cost_per_sqft)} = <span className="font-medium text-slate-700">{money(m.total_material_cost)}</span>
                        {m.supplier ? ` · ${m.supplier}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => { setEditingMatId(m.id); setShowAddMat(false); }} disabled={busy} data-testid={`material-edit-btn-${m.id}`}><Pencil className="h-3 w-3 mr-1" /> Edit</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={() => onDeleteMaterial?.(m.id)} disabled={busy} data-testid={`material-delete-btn-${m.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Profit Estimate" icon={DollarSign} testId="pricing-profit">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><p className="text-[10px] uppercase text-slate-500">Suggested Price</p><p className="font-semibold" data-testid="pricing-suggested">{money(view.suggested_price)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Quoted Price</p><p className="font-semibold text-violet-700" data-testid="pricing-quoted-2">{money(view.quoted_price)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Estimated Profit</p><p className={`font-semibold ${view.estimated_profit >= 0 ? 'text-emerald-700' : 'text-rose-700'}`} data-testid="pricing-profit-val">{money(view.estimated_profit)}</p></div>
            <div><p className="text-[10px] uppercase text-slate-500">Estimated Margin</p><p className="font-semibold" data-testid="pricing-margin-val">{view.estimated_margin_percent.toFixed(1)}%</p></div>
          </div>
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
