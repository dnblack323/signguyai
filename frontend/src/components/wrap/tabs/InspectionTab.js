// Phase 2E + 2F: Inspection tab — real persistence + damage markers CRUD
// plus visual click-to-add damage diagram.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapVehicleDiagram from '../WrapVehicleDiagram';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { ClipboardCheck, Plus, Pencil, Trash2, Check, X, AlertTriangle, Car, Eye } from 'lucide-react';

const INSPECTION_STATUSES = ['not_started', 'in_progress', 'completed', 'acknowledged'];
const DAMAGE_TYPES = [
  'Dent', 'Scratch', 'Rust', 'Paint Chip', 'Clear Coat Failure',
  'Loose Trim', 'Cracked Part', 'Previous Wrap', 'Adhesive Residue', 'Other Concern',
];
const SEVERITIES = ['Low', 'Medium', 'High', 'Severe'];
const DIAGRAM_TYPES = [
  '', 'Generic Van', 'Generic Pickup', 'Generic Box Truck', 'Generic Trailer',
  'Generic SUV', 'Generic Sedan', 'Generic Ambulance', 'Generic Bus',
  'Generic Race Car', 'Custom / Other',
];

const SEVERITY_CLS = {
  Low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Medium: 'bg-amber-50 text-amber-800 border-amber-200',
  High: 'bg-orange-50 text-orange-800 border-orange-200',
  Severe: 'bg-rose-50 text-rose-800 border-rose-200',
};

function MarkerForm({ initial, onCancel, onSubmit, busy, testIdPrefix }) {
  const [form, setForm] = useState(initial || {
    area: '', damage_type: 'Other Concern', severity: 'Low',
    photo_placeholder: '', notes: '', marker_label: '',
    x_percent: null, y_percent: null,
  });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const hasPos = typeof form.x_percent === 'number' && typeof form.y_percent === 'number';
  return (
    <div className="p-3 bg-violet-50/50 rounded-md border border-violet-200 space-y-2" data-testid={`${testIdPrefix}-form`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <div><Label className="text-xs">Area</Label><Input value={form.area} onChange={(e) => set('area', e.target.value)} placeholder="left fender" data-testid={`${testIdPrefix}-area`} /></div>
        <div>
          <Label className="text-xs">Damage Type</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.damage_type} onChange={(e) => set('damage_type', e.target.value)} data-testid={`${testIdPrefix}-type`}>
            {DAMAGE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <Label className="text-xs">Severity</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.severity} onChange={(e) => set('severity', e.target.value)} data-testid={`${testIdPrefix}-severity`}>
            {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div><Label className="text-xs">Marker Label</Label><Input value={form.marker_label || ''} onChange={(e) => set('marker_label', e.target.value)} placeholder="#1 / front left" data-testid={`${testIdPrefix}-label`} /></div>
        <div className="md:col-span-2"><Label className="text-xs">Photo Placeholder</Label><Input value={form.photo_placeholder} onChange={(e) => set('photo_placeholder', e.target.value)} data-testid={`${testIdPrefix}-photo`} /></div>
        <div className="md:col-span-2 flex items-end gap-2">
          {hasPos ? (
            <p className="text-[11px] text-violet-700" data-testid={`${testIdPrefix}-pos`}>
              On diagram: {form.x_percent}% × {form.y_percent}%
              <button type="button" className="ml-2 underline" onClick={() => { set('x_percent', null); set('y_percent', null); }}>
                clear
              </button>
            </p>
          ) : (
            <p className="text-[11px] text-slate-500">No diagram position. (Optional — use the diagram above to pin.)</p>
          )}
        </div>
        <div className="md:col-span-4"><Label className="text-xs">Notes</Label><Textarea rows={2} value={form.notes} onChange={(e) => set('notes', e.target.value)} data-testid={`${testIdPrefix}-notes`} /></div>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button size="sm" variant="outline" onClick={onCancel} data-testid={`${testIdPrefix}-cancel`}><X className="h-3.5 w-3.5 mr-1" /> Cancel</Button>
        <Button size="sm" onClick={() => onSubmit(form)} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid={`${testIdPrefix}-submit`}><Check className="h-3.5 w-3.5 mr-1" /> Save Marker</Button>
      </div>
    </div>
  );
}

export default function InspectionTab({
  wrapData,
  onSaveInspection,
  onAckToggle,
  onAddMarker,
  onUpdateMarker,
  onDeleteMarker,
  saveStatus,
}) {
  const inspection = wrapData?.inspection || {};
  const markers = inspection.damage_markers || [];
  const [form, setForm] = useState({
    inspection_status: 'not_started', vehicle_diagram_type: '', inspected_by: '',
    inspection_date: '', inspection_notes: '', customer_visible: false,
  });
  const [dirty, setDirty] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [pendingPosition, setPendingPosition] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [highlightedId, setHighlightedId] = useState(null);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({
      inspection_status: inspection.inspection_status || 'not_started',
      vehicle_diagram_type: inspection.vehicle_diagram_type || '',
      inspected_by: inspection.inspected_by || '',
      inspection_date: inspection.inspection_date || '',
      inspection_notes: inspection.inspection_notes || '',
      customer_visible: !!inspection.customer_visible,
    });
    setDirty(false);
  }, [wrapData]);  // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const payload = {
      inspection_status: form.inspection_status,
      vehicle_diagram_type: form.vehicle_diagram_type,
      inspected_by: form.inspected_by,
      inspection_date: form.inspection_date || null,
      inspection_notes: form.inspection_notes,
      customer_visible: !!form.customer_visible,
    };
    const ok = await onSaveInspection?.(payload);
    if (ok) setDirty(false);
  };

  const openAddWithPosition = ({ x_percent, y_percent }) => {
    setPendingPosition({ x_percent, y_percent });
    setShowAdd(true);
    setEditingId(null);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Pre-Install Inspection"
          icon={ClipboardCheck}
          testId="insp-diagram"
          action={
            <div className="flex items-center gap-2 flex-wrap">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="insp-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="insp-save-btn">Save Inspection</Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Label className="text-xs">Inspection Status</Label>
              <select className="w-full border rounded h-9 px-2 text-sm" value={form.inspection_status} onChange={(e) => set('inspection_status', e.target.value)} data-testid="insp-select-status">
                {INSPECTION_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs">Vehicle Diagram Type</Label>
              <select className="w-full border rounded h-9 px-2 text-sm" value={form.vehicle_diagram_type} onChange={(e) => set('vehicle_diagram_type', e.target.value)} data-testid="insp-select-diagram">
                {DIAGRAM_TYPES.map((d) => <option key={d || 'none'} value={d}>{d || '— Select —'}</option>)}
              </select>
            </div>
            <div><Label className="text-xs">Inspected By</Label><Input value={form.inspected_by} onChange={(e) => set('inspected_by', e.target.value)} data-testid="insp-input-inspected_by" /></div>
            <div><Label className="text-xs">Inspection Date</Label><Input type="date" value={form.inspection_date} onChange={(e) => set('inspection_date', e.target.value)} data-testid="insp-input-date" /></div>
            <div className="md:col-span-3"><Label className="text-xs">Inspection Notes</Label><Textarea rows={2} value={form.inspection_notes} onChange={(e) => set('inspection_notes', e.target.value)} data-testid="insp-input-notes" /></div>
          </div>

          <div className="mt-3">
            <WrapVehicleDiagram
              diagramType={form.vehicle_diagram_type}
              markers={markers}
              selectedId={highlightedId}
              onAdd={openAddWithPosition}
              onSelect={(id) => {
                setHighlightedId(id);
                if (typeof window !== 'undefined') {
                  const el = document.querySelector(`[data-testid="insp-marker-row-${id}"]`);
                  if (el && el.scrollIntoView) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
              }}
              testId="insp-diagram-svg"
            />
          </div>

          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-100">
            <input
              type="checkbox"
              id="insp-customer-visible"
              checked={!!form.customer_visible}
              onChange={(e) => set('customer_visible', e.target.checked)}
              data-testid="insp-toggle-customer_visible"
            />
            <Label htmlFor="insp-customer-visible" className="text-sm">
              Share inspection report with customer in Customer Portal
            </Label>
            <Eye className="h-3.5 w-3.5 text-slate-400" />
          </div>
        </WrapSectionCard>

        <WrapSectionCard
          title="Damage Marker List"
          icon={AlertTriangle}
          testId="insp-damage"
          action={
            !showAdd && (
              <Button size="sm" onClick={() => { setShowAdd(true); setEditingId(null); setPendingPosition(null); }} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="insp-add-marker-btn">
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Marker
              </Button>
            )
          }
        >
          {showAdd && (
            <div className="mb-3">
              <MarkerForm
                initial={pendingPosition ? {
                  area: '', damage_type: 'Other Concern', severity: 'Low',
                  photo_placeholder: '', notes: '', marker_label: '',
                  x_percent: pendingPosition.x_percent, y_percent: pendingPosition.y_percent,
                } : null}
                onCancel={() => { setShowAdd(false); setPendingPosition(null); }}
                onSubmit={async (p) => {
                  await onAddMarker?.(p);
                  setShowAdd(false);
                  setPendingPosition(null);
                }}
                busy={busy}
                testIdPrefix="insp-marker-add"
              />
            </div>
          )}
          {markers.length === 0 && !showAdd ? (
            <p className="text-sm text-slate-500 italic py-2" data-testid="insp-markers-empty">No damage markers logged.</p>
          ) : (
            <div className="space-y-2" data-testid="insp-markers-list">
              {markers.map((m, idx) => {
                if (editingId === m.id) {
                  return (
                    <MarkerForm
                      key={m.id}
                      initial={m}
                      onCancel={() => setEditingId(null)}
                      onSubmit={async (p) => { await onUpdateMarker?.(m.id, p); setEditingId(null); }}
                      busy={busy}
                      testIdPrefix={`insp-marker-edit-${m.id}`}
                    />
                  );
                }
                const hasPos = typeof m.x_percent === 'number' && typeof m.y_percent === 'number';
                const isHighlighted = highlightedId === m.id;
                return (
                  <div
                    key={m.id}
                    className={`flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md transition-colors ${isHighlighted ? 'border-violet-400 bg-violet-50' : 'border-slate-200 bg-white'}`}
                    data-testid={`insp-marker-row-${m.id}`}
                    onClick={() => setHighlightedId(m.id)}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {hasPos && (
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-violet-600 text-white">
                            #{idx + 1}
                          </span>
                        )}
                        <p className="font-medium text-sm text-slate-800">{m.damage_type}</p>
                        {m.area && <span className="text-xs text-slate-500">@ {m.area}</span>}
                        {m.marker_label && <span className="text-xs italic text-violet-600">{m.marker_label}</span>}
                        <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${SEVERITY_CLS[m.severity] || SEVERITY_CLS.Low}`}>{m.severity}</span>
                      </div>
                      {m.notes && <p className="text-xs text-slate-500">{m.notes}</p>}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={(e) => { e.stopPropagation(); setEditingId(m.id); setShowAdd(false); }} disabled={busy} data-testid={`insp-marker-edit-btn-${m.id}`}><Pencil className="h-3 w-3 mr-1" /> Edit</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={(e) => { e.stopPropagation(); onDeleteMarker?.(m.id); }} disabled={busy} data-testid={`insp-marker-delete-btn-${m.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Customer Acknowledgement" icon={Car} testId="insp-ack">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="insp-customer-ack"
              checked={!!inspection.customer_acknowledged}
              onChange={(e) => onAckToggle?.(e.target.checked)}
              disabled={busy}
              data-testid="insp-toggle-customer_acknowledged"
            />
            <Label htmlFor="insp-customer-ack" className="text-sm font-medium">Customer acknowledged pre-install condition</Label>
            {inspection.customer_acknowledged_at && <span className="text-[11px] text-emerald-700" data-testid="insp-ack-at">{new Date(inspection.customer_acknowledged_at).toLocaleString()}</span>}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Mirrors into <span className="font-medium">approvals.inspection_acknowledged</span>. The customer can also acknowledge from the Customer Portal once the report is marked customer-visible.
          </p>
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Inspection Summary & Report AI"
        testId="insp-ai-helper"
        actions={[
          { label: 'Summarize Damage' },
          { label: 'Suggest Repair Steps' },
          { label: 'Flag Wrap Risk' },
          { label: 'Write Acknowledgement Email' },
          { label: 'Compare to Previous Inspection' },
        ]}
      />
    </div>
  );
}
