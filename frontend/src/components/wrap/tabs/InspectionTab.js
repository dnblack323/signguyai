// Phase 2E: Inspection tab — real persistence + damage markers CRUD.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { ClipboardCheck, Plus, Pencil, Trash2, Check, X, AlertTriangle, Car } from 'lucide-react';

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
  const [form, setForm] = useState(initial || { area: '', damage_type: 'Other Concern', severity: 'Low', photo_placeholder: '', notes: '' });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
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
        <div><Label className="text-xs">Photo Placeholder</Label><Input value={form.photo_placeholder} onChange={(e) => set('photo_placeholder', e.target.value)} data-testid={`${testIdPrefix}-photo`} /></div>
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
    inspection_date: '', inspection_notes: '',
  });
  const [dirty, setDirty] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({
      inspection_status: inspection.inspection_status || 'not_started',
      vehicle_diagram_type: inspection.vehicle_diagram_type || '',
      inspected_by: inspection.inspected_by || '',
      inspection_date: inspection.inspection_date || '',
      inspection_notes: inspection.inspection_notes || '',
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
    };
    const ok = await onSaveInspection?.(payload);
    if (ok) setDirty(false);
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
          <p className="text-[11px] text-slate-500 mt-2">Visual drag-and-drop damage diagram will be added in a later phase.</p>
        </WrapSectionCard>

        <WrapSectionCard
          title="Damage Marker List"
          icon={AlertTriangle}
          testId="insp-damage"
          action={
            !showAdd && (
              <Button size="sm" onClick={() => { setShowAdd(true); setEditingId(null); }} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="insp-add-marker-btn">
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Marker
              </Button>
            )
          }
        >
          {showAdd && (
            <div className="mb-3">
              <MarkerForm
                onCancel={() => setShowAdd(false)}
                onSubmit={async (p) => { await onAddMarker?.(p); setShowAdd(false); }}
                busy={busy}
                testIdPrefix="insp-marker-add"
              />
            </div>
          )}
          {markers.length === 0 && !showAdd ? (
            <p className="text-sm text-slate-500 italic py-2" data-testid="insp-markers-empty">No damage markers logged.</p>
          ) : (
            <div className="space-y-2" data-testid="insp-markers-list">
              {markers.map((m) => {
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
                return (
                  <div key={m.id} className="flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md bg-white" data-testid={`insp-marker-row-${m.id}`}>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-sm text-slate-800">{m.damage_type}</p>
                        {m.area && <span className="text-xs text-slate-500">@ {m.area}</span>}
                        <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${SEVERITY_CLS[m.severity] || SEVERITY_CLS.Low}`}>{m.severity}</span>
                      </div>
                      {m.notes && <p className="text-xs text-slate-500">{m.notes}</p>}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => { setEditingId(m.id); setShowAdd(false); }} disabled={busy} data-testid={`insp-marker-edit-btn-${m.id}`}><Pencil className="h-3 w-3 mr-1" /> Edit</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={() => onDeleteMarker?.(m.id)} disabled={busy} data-testid={`insp-marker-delete-btn-${m.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
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
            Mirrors into <span className="font-medium">approvals.inspection_acknowledged</span>.
          </p>
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Inspection AI Helper"
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
