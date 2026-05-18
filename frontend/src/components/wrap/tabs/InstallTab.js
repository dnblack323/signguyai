// Phase 2D: Install tab — real persistence + issue log + signoff.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { Calendar, Save, Plus, Pencil, Trash2, Check, X, AlertTriangle, ClipboardCheck } from 'lucide-react';

const INSTALL_STATUSES = [
  'not_scheduled', 'scheduled', 'vehicle_received', 'in_progress',
  'installed', 'customer_picked_up', 'complete',
];

const ISSUE_TYPES = [
  'Misprint', 'Wrong size panel', 'Color issue', 'Bad file',
  'Installer mistake', 'Vehicle issue', 'Paint failure', 'Adhesion issue',
  'Weather issue', 'Customer delay', 'Material defect', 'Other',
];

const INSTALL_CHECKLIST_DEFS = [
  ['vehicle_received', 'Vehicle received'],
  ['vehicle_inspected', 'Vehicle inspected'],
  ['surface_cleaned', 'Surface cleaned'],
  ['old_graphics_removed', 'Old graphics removed (if needed)'],
  ['panels_staged', 'Panels staged'],
  ['install_started', 'Install started'],
  ['install_completed', 'Install completed'],
  ['post_heated', 'Post-heated'],
  ['final_inspection_complete', 'Final inspection complete'],
  ['customer_walkthrough_complete', 'Customer walkthrough complete'],
];

const EMPTY = {
  install_status: 'not_scheduled',
  install_date: '', install_start_time: '', install_end_time: '',
  installer_name: '', helper_name: '', install_location: '',
  bay_needed: false,
  customer_dropoff_time: '', customer_pickup_time: '',
  hours_estimated: '', hours_actual: '',
  install_notes: '', completion_notes: '',
};

function IssueForm({ initial, onCancel, onSubmit, busy, testIdPrefix }) {
  const [form, setForm] = useState(initial || { issue_type: 'Other', area: '', description: '', photo_placeholder: '' });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  return (
    <div className="p-3 bg-violet-50/50 rounded-md border border-violet-200 space-y-2" data-testid={`${testIdPrefix}-form`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <div>
          <Label className="text-xs">Issue Type</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.issue_type} onChange={(e) => set('issue_type', e.target.value)} data-testid={`${testIdPrefix}-type`}>
            {ISSUE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div><Label className="text-xs">Area</Label><Input value={form.area} onChange={(e) => set('area', e.target.value)} placeholder="driver door" data-testid={`${testIdPrefix}-area`} /></div>
        <div className="md:col-span-2"><Label className="text-xs">Photo Placeholder</Label><Input value={form.photo_placeholder} onChange={(e) => set('photo_placeholder', e.target.value)} placeholder="filename or note" data-testid={`${testIdPrefix}-photo`} /></div>
        <div className="md:col-span-4"><Label className="text-xs">Description</Label><Textarea rows={2} value={form.description} onChange={(e) => set('description', e.target.value)} data-testid={`${testIdPrefix}-desc`} /></div>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button size="sm" variant="outline" onClick={onCancel} data-testid={`${testIdPrefix}-cancel`}><X className="h-3.5 w-3.5 mr-1" /> Cancel</Button>
        <Button size="sm" onClick={() => onSubmit(form)} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid={`${testIdPrefix}-submit`}><Check className="h-3.5 w-3.5 mr-1" /> Save Issue</Button>
      </div>
    </div>
  );
}

export default function InstallTab({
  wrapData,
  onSaveInstall,
  onSignoffToggle,
  onChecklistToggle,
  onAddIssue,
  onUpdateIssue,
  onDeleteIssue,
  saveStatus,
}) {
  const install = wrapData?.install || {};
  const issues = install.issues || [];
  const checklist = install.checklist || {};
  const [form, setForm] = useState(EMPTY);
  const [dirty, setDirty] = useState(false);
  const [showAddIssue, setShowAddIssue] = useState(false);
  const [editingIssueId, setEditingIssueId] = useState(null);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({
      ...EMPTY,
      ...install,
      install_date: install.install_date || '',
      hours_estimated: install.hours_estimated ?? '',
      hours_actual: install.hours_actual ?? '',
    });
    setDirty(false);
  }, [wrapData]);  // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const payload = {
      install_status: form.install_status,
      install_date: form.install_date || null,
      install_start_time: form.install_start_time,
      install_end_time: form.install_end_time,
      installer_name: form.installer_name,
      helper_name: form.helper_name,
      install_location: form.install_location,
      bay_needed: !!form.bay_needed,
      customer_dropoff_time: form.customer_dropoff_time,
      customer_pickup_time: form.customer_pickup_time,
      hours_estimated: form.hours_estimated === '' ? null : Number(form.hours_estimated),
      hours_actual: form.hours_actual === '' ? null : Number(form.hours_actual),
      install_notes: form.install_notes,
      completion_notes: form.completion_notes,
    };
    const ok = await onSaveInstall?.(payload);
    if (ok) setDirty(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Install Schedule"
          icon={Calendar}
          testId="install-schedule"
          action={
            <div className="flex items-center gap-2 flex-wrap">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="install-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="install-save-btn"><Save className="h-3.5 w-3.5 mr-1" /> Save Install</Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Label className="text-xs">Install Status</Label>
              <select className="w-full border rounded h-9 px-2 text-sm" value={form.install_status} onChange={(e) => set('install_status', e.target.value)} data-testid="install-select-status">
                {INSTALL_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div><Label className="text-xs">Install Date</Label><Input type="date" value={form.install_date} onChange={(e) => set('install_date', e.target.value)} data-testid="install-input-date" /></div>
            <div className="grid grid-cols-2 gap-2">
              <div><Label className="text-xs">Start</Label><Input type="time" value={form.install_start_time} onChange={(e) => set('install_start_time', e.target.value)} data-testid="install-input-start" /></div>
              <div><Label className="text-xs">End</Label><Input type="time" value={form.install_end_time} onChange={(e) => set('install_end_time', e.target.value)} data-testid="install-input-end" /></div>
            </div>
            <div><Label className="text-xs">Installer</Label><Input value={form.installer_name} onChange={(e) => set('installer_name', e.target.value)} data-testid="install-input-installer" /></div>
            <div><Label className="text-xs">Helper</Label><Input value={form.helper_name} onChange={(e) => set('helper_name', e.target.value)} data-testid="install-input-helper" /></div>
            <div><Label className="text-xs">Install Location</Label><Input value={form.install_location} onChange={(e) => set('install_location', e.target.value)} placeholder="Bay 2" data-testid="install-input-location" /></div>
            <div className="flex items-center gap-2 mt-5">
              <input type="checkbox" id="install-bay-needed" checked={!!form.bay_needed} onChange={(e) => set('bay_needed', e.target.checked)} data-testid="install-toggle-bay_needed" />
              <Label htmlFor="install-bay-needed" className="text-xs">Bay needed</Label>
            </div>
            <div><Label className="text-xs">Customer Drop-off Time</Label><Input value={form.customer_dropoff_time} onChange={(e) => set('customer_dropoff_time', e.target.value)} data-testid="install-input-dropoff" /></div>
            <div><Label className="text-xs">Customer Pickup Time</Label><Input value={form.customer_pickup_time} onChange={(e) => set('customer_pickup_time', e.target.value)} data-testid="install-input-pickup" /></div>
            <div><Label className="text-xs">Estimated Hours</Label><Input type="number" value={form.hours_estimated} onChange={(e) => set('hours_estimated', e.target.value)} data-testid="install-input-est_hours" /></div>
            <div><Label className="text-xs">Actual Hours</Label><Input type="number" value={form.hours_actual} onChange={(e) => set('hours_actual', e.target.value)} data-testid="install-input-actual_hours" /></div>
            <div className="md:col-span-3"><Label className="text-xs">Install Notes</Label><Textarea rows={2} value={form.install_notes} onChange={(e) => set('install_notes', e.target.value)} data-testid="install-input-notes" /></div>
            <div className="md:col-span-3"><Label className="text-xs">Completion Notes</Label><Textarea rows={2} value={form.completion_notes} onChange={(e) => set('completion_notes', e.target.value)} data-testid="install-input-completion_notes" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Install Checklist" icon={ClipboardCheck} testId="install-checklist">
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-y-1 gap-x-4" data-testid="install-checklist-list">
            {INSTALL_CHECKLIST_DEFS.map(([k, label]) => {
              const done = !!checklist[k];
              return (
                <li key={k} className="flex items-center gap-2 py-0.5">
                  <input
                    type="checkbox"
                    checked={done}
                    onChange={(e) => onChecklistToggle?.(k, e.target.checked)}
                    disabled={busy}
                    data-testid={`install-checklist-toggle-${k}`}
                  />
                  <span className={`text-sm ${done ? 'line-through text-slate-500' : 'text-slate-700'}`}>{label}</span>
                </li>
              );
            })}
          </ul>
        </WrapSectionCard>

        <WrapSectionCard title="Customer Signoff" icon={Check} testId="install-signoff">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="install-customer-signoff"
              checked={!!install.customer_signoff}
              onChange={(e) => onSignoffToggle?.(e.target.checked)}
              disabled={busy}
              data-testid="install-toggle-customer_signoff"
            />
            <Label htmlFor="install-customer-signoff" className="text-sm font-medium">Customer signed off on install</Label>
            {install.customer_signoff_at && <span className="text-[11px] text-emerald-700" data-testid="install-signoff-at">{new Date(install.customer_signoff_at).toLocaleString()}</span>}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            When install status is <code>complete</code> AND customer signs off, <span className="font-medium">approvals.final_signoff_completed</span> is auto-set.
          </p>
        </WrapSectionCard>

        <WrapSectionCard
          title="Install Issue Log"
          icon={AlertTriangle}
          testId="install-issues"
          action={
            !showAddIssue && (
              <Button size="sm" onClick={() => { setShowAddIssue(true); setEditingIssueId(null); }} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="install-add-issue-btn">
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Issue
              </Button>
            )
          }
        >
          {showAddIssue && (
            <div className="mb-3">
              <IssueForm
                onCancel={() => setShowAddIssue(false)}
                onSubmit={async (p) => { await onAddIssue?.(p); setShowAddIssue(false); }}
                busy={busy}
                testIdPrefix="install-issue-add"
              />
            </div>
          )}
          {issues.length === 0 && !showAddIssue ? (
            <p className="text-sm text-slate-500 italic py-2" data-testid="install-issues-empty">No issues logged.</p>
          ) : (
            <div className="space-y-2" data-testid="install-issues-list">
              {issues.map((iss) => {
                if (editingIssueId === iss.id) {
                  return (
                    <IssueForm
                      key={iss.id}
                      initial={iss}
                      onCancel={() => setEditingIssueId(null)}
                      onSubmit={async (p) => { await onUpdateIssue?.(iss.id, p); setEditingIssueId(null); }}
                      busy={busy}
                      testIdPrefix={`install-issue-edit-${iss.id}`}
                    />
                  );
                }
                return (
                  <div key={iss.id} className="flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md bg-white" data-testid={`install-issue-row-${iss.id}`}>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-sm text-slate-800">{iss.issue_type}</p>
                        {iss.area && <span className="text-xs text-slate-500">@ {iss.area}</span>}
                        {iss.resolved
                          ? <span className="text-[10px] uppercase bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-200">Resolved</span>
                          : <span className="text-[10px] uppercase bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">Open</span>}
                        {iss.resolved_at && <span className="text-[10px] text-emerald-700">{new Date(iss.resolved_at).toLocaleDateString()}</span>}
                      </div>
                      {iss.description && <p className="text-xs text-slate-500">{iss.description}</p>}
                      {iss.resolution_notes && <p className="text-xs text-emerald-700">Resolution: {iss.resolution_notes}</p>}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => onUpdateIssue?.(iss.id, { resolved: !iss.resolved })} disabled={busy} data-testid={`install-issue-toggle-${iss.id}`}>{iss.resolved ? 'Reopen' : 'Mark Resolved'}</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => { setEditingIssueId(iss.id); setShowAddIssue(false); }} disabled={busy} data-testid={`install-issue-edit-btn-${iss.id}`}><Pencil className="h-3 w-3 mr-1" /> Edit</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={() => onDeleteIssue?.(iss.id)} disabled={busy} data-testid={`install-issue-delete-btn-${iss.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Install AI Helper"
        testId="install-ai-helper"
        actions={[
          { label: 'Build Install Checklist' },
          { label: 'Estimate Install Time' },
          { label: 'Write Drop-Off Message' },
          { label: 'Summarize Issues' },
          { label: 'Write Pickup Message' },
        ]}
      />
    </div>
  );
}
