// Phase 2A: Measurements & Coverage tab — real CRUD against /api/wrap/items/{id}/areas.
import { useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Ruler, Plus, Pencil, Trash2, Check, X } from 'lucide-react';

const COMPLEXITY_OPTS = ['low', 'medium', 'high'];
const UNIT_OPTS = ['in', 'ft'];

const EMPTY_AREA = {
  area_name: '', width: '', height: '', unit: 'in',
  waste_percent: 15, material: '', laminate: '',
  complexity: 'medium', included: true, notes: '',
};

function num(v) {
  if (v === '' || v === null || v === undefined) return null;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : null;
}

function previewSqft(width, height, unit, waste) {
  const w = num(width); const h = num(height);
  if (w === null || h === null || w <= 0 || h <= 0) return { raw: null, billable: null };
  const raw = unit === 'ft' ? w * h : (w * h) / 144;
  const ws = num(waste) || 0;
  return { raw: Math.round(raw * 100) / 100, billable: Math.round(raw * (1 + ws / 100) * 100) / 100 };
}

function CoverageSummary({ summary }) {
  const s = summary || { total_raw_sqft: 0, total_billable_sqft: 0, average_waste_percent: 0, included_count: 0, excluded_count: 0 };
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm" data-testid="coverage-summary">
      <div><p className="text-[10px] uppercase text-slate-500">Total Raw</p><p className="font-semibold" data-testid="cs-total-raw">{s.total_raw_sqft.toFixed(2)} ft²</p></div>
      <div><p className="text-[10px] uppercase text-slate-500">Avg Waste</p><p className="font-semibold" data-testid="cs-avg-waste">{s.average_waste_percent.toFixed(1)}%</p></div>
      <div><p className="text-[10px] uppercase text-slate-500">Total Billable</p><p className="font-semibold" data-testid="cs-total-billable">{s.total_billable_sqft.toFixed(2)} ft²</p></div>
      <div><p className="text-[10px] uppercase text-slate-500">Included</p><p className="font-semibold text-emerald-700" data-testid="cs-included">{s.included_count}</p></div>
      <div><p className="text-[10px] uppercase text-slate-500">Excluded</p><p className="font-semibold text-rose-700" data-testid="cs-excluded">{s.excluded_count}</p></div>
    </div>
  );
}

function AreaForm({ initial, onCancel, onSubmit, busy, testIdPrefix }) {
  const [form, setForm] = useState(initial || EMPTY_AREA);
  const preview = previewSqft(form.width, form.height, form.unit, form.waste_percent);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const submit = () => {
    const payload = {
      area_name: form.area_name || 'Untitled Area',
      width: num(form.width),
      height: num(form.height),
      unit: form.unit || 'in',
      waste_percent: num(form.waste_percent) ?? 0,
      material: form.material || '',
      laminate: form.laminate || '',
      complexity: form.complexity || 'medium',
      included: !!form.included,
      notes: form.notes || '',
    };
    onSubmit(payload);
  };
  return (
    <div className="space-y-3 p-3 bg-violet-50/50 rounded-md border border-violet-200" data-testid={`${testIdPrefix}-form`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <div className="md:col-span-2">
          <Label className="text-xs">Area Name</Label>
          <Input value={form.area_name} onChange={(e) => set('area_name', e.target.value)} placeholder="Driver Side" data-testid={`${testIdPrefix}-input-name`} />
        </div>
        <div>
          <Label className="text-xs">Width</Label>
          <Input type="number" value={form.width} onChange={(e) => set('width', e.target.value)} placeholder="120" data-testid={`${testIdPrefix}-input-width`} />
        </div>
        <div>
          <Label className="text-xs">Height</Label>
          <Input type="number" value={form.height} onChange={(e) => set('height', e.target.value)} placeholder="72" data-testid={`${testIdPrefix}-input-height`} />
        </div>
        <div>
          <Label className="text-xs">Unit</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.unit} onChange={(e) => set('unit', e.target.value)} data-testid={`${testIdPrefix}-input-unit`}>
            {UNIT_OPTS.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>
        <div>
          <Label className="text-xs">Waste %</Label>
          <Input type="number" value={form.waste_percent} onChange={(e) => set('waste_percent', e.target.value)} data-testid={`${testIdPrefix}-input-waste`} />
        </div>
        <div>
          <Label className="text-xs">Material</Label>
          <Input value={form.material} onChange={(e) => set('material', e.target.value)} placeholder="3M IJ180Cv3" data-testid={`${testIdPrefix}-input-material`} />
        </div>
        <div>
          <Label className="text-xs">Laminate</Label>
          <Input value={form.laminate} onChange={(e) => set('laminate', e.target.value)} placeholder="3M 8519" data-testid={`${testIdPrefix}-input-laminate`} />
        </div>
        <div>
          <Label className="text-xs">Complexity</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.complexity} onChange={(e) => set('complexity', e.target.value)} data-testid={`${testIdPrefix}-input-complexity`}>
            {COMPLEXITY_OPTS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div className="md:col-span-3">
          <Label className="text-xs">Notes</Label>
          <Input value={form.notes} onChange={(e) => set('notes', e.target.value)} placeholder="optional" data-testid={`${testIdPrefix}-input-notes`} />
        </div>
        <div className="flex items-center gap-2 mt-5">
          <input type="checkbox" id={`${testIdPrefix}-included`} checked={!!form.included} onChange={(e) => set('included', e.target.checked)} data-testid={`${testIdPrefix}-input-included`} />
          <Label htmlFor={`${testIdPrefix}-included`} className="text-xs">Include in quote</Label>
        </div>
      </div>
      <div className="flex items-center justify-between pt-1">
        <p className="text-xs text-slate-600">
          Preview: <span className="font-medium">{preview.raw !== null ? `${preview.raw} ft² raw · ${preview.billable} ft² billable` : 'enter width × height'}</span>
        </p>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={onCancel} data-testid={`${testIdPrefix}-cancel`}>
            <X className="h-3.5 w-3.5 mr-1" /> Cancel
          </Button>
          <Button size="sm" onClick={submit} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid={`${testIdPrefix}-submit`}>
            <Check className="h-3.5 w-3.5 mr-1" /> Save Area
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function MeasurementsTab({ wrapData, onAddArea, onUpdateArea, onDeleteArea, saveStatus }) {
  const areas = wrapData?.wrapped_areas || [];
  const summary = wrapData?.coverage_summary;
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const busy = saveStatus === 'saving';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard title="Coverage Summary" icon={Ruler} testId="meas-coverage">
          <CoverageSummary summary={summary} />
        </WrapSectionCard>

        <WrapSectionCard
          title="Wrapped Areas"
          icon={Ruler}
          testId="meas-areas"
          action={
            !showAdd && (
              <Button
                size="sm"
                onClick={() => { setShowAdd(true); setEditingId(null); }}
                className="bg-violet-600 hover:bg-violet-700 text-white"
                data-testid="meas-add-btn"
              >
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Area
              </Button>
            )
          }
        >
          {showAdd && (
            <div className="mb-3">
              <AreaForm
                onCancel={() => setShowAdd(false)}
                onSubmit={async (p) => {
                  await onAddArea?.(p);
                  setShowAdd(false);
                }}
                busy={busy}
                testIdPrefix="meas-add"
              />
            </div>
          )}

          {areas.length === 0 && !showAdd ? (
            <p className="text-sm text-slate-500 italic py-3" data-testid="meas-empty">
              No wrapped areas yet. Click <span className="font-medium">Add Area</span> to begin.
            </p>
          ) : (
            <div className="space-y-2" data-testid="meas-areas-list">
              {areas.map((a) => {
                if (editingId === a.id) {
                  return (
                    <AreaForm
                      key={a.id}
                      initial={a}
                      onCancel={() => setEditingId(null)}
                      onSubmit={async (p) => {
                        await onUpdateArea?.(a.id, p);
                        setEditingId(null);
                      }}
                      busy={busy}
                      testIdPrefix={`meas-edit-${a.id}`}
                    />
                  );
                }
                return (
                  <div
                    key={a.id}
                    className="flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md bg-white"
                    data-testid={`meas-area-row-${a.id}`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-sm text-slate-800">{a.area_name || 'Untitled Area'}</p>
                        {!a.included && (
                          <span className="text-[10px] uppercase tracking-wide bg-rose-50 text-rose-700 px-1.5 py-0.5 rounded border border-rose-200">
                            Excluded
                          </span>
                        )}
                        <span className="text-[10px] uppercase tracking-wide bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                          {a.complexity || 'medium'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        {a.width || '—'} × {a.height || '—'} {a.unit || 'in'} · raw {a.raw_sqft ?? '—'} ft² · billable {a.billable_sqft ?? '—'} ft² · waste {a.waste_percent ?? 0}%
                      </p>
                      {(a.material || a.laminate) && (
                        <p className="text-xs text-slate-500">
                          {a.material || '—'}{a.laminate ? ` / ${a.laminate}` : ''}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onUpdateArea?.(a.id, { included: !a.included })}
                        disabled={busy}
                        className="text-xs h-7"
                        data-testid={`meas-toggle-included-${a.id}`}
                      >
                        {a.included ? 'Exclude' : 'Include'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => { setEditingId(a.id); setShowAdd(false); }}
                        disabled={busy}
                        className="text-xs h-7"
                        data-testid={`meas-edit-btn-${a.id}`}
                      >
                        <Pencil className="h-3 w-3 mr-1" /> Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onDeleteArea?.(a.id)}
                        disabled={busy}
                        className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50"
                        data-testid={`meas-delete-btn-${a.id}`}
                      >
                        <Trash2 className="h-3 w-3 mr-1" /> Delete
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Waste Factor" icon={Ruler} testId="meas-waste">
          <p className="text-sm text-slate-700">
            Default waste factor on new areas: <span className="font-medium">15%</span>. Adjust per-area as needed.
          </p>
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Measurements AI Helper"
        testId="meas-ai-helper"
        actions={[
          { label: 'Estimate Missing Dimensions' },
          { label: 'Suggest Waste Factor' },
          { label: 'Check Missing Areas' },
          { label: 'Compare to Vehicle Type' },
          { label: 'Suggest Billable Sq Ft' },
        ]}
      />
    </div>
  );
}
