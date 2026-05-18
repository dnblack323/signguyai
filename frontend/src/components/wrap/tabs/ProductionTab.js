// Phase 2D: Production tab — real persistence + checklist + task CRUD.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { Factory, Save, Plus, Pencil, Trash2, Check, X, Boxes, Printer } from 'lucide-react';

const STATUSES = [
  'not_started', 'files_ready', 'printing', 'printed',
  'laminated', 'trimming', 'staged', 'ready_for_install', 'complete',
];

const CHECKLIST_DEFS = [
  ['files_ready', 'Files ready'],
  ['materials_pulled', 'Materials pulled'],
  ['printed', 'Printed'],
  ['laminated', 'Laminated'],
  ['outgassed', 'Outgassed'],
  ['trimmed', 'Trimmed'],
  ['panels_labeled', 'Panels labeled'],
  ['install_kit_ready', 'Install kit ready'],
  ['prep_complete', 'Prep complete'],
  ['ready_for_install', 'Ready for install'],
];

const TASK_STATUSES = ['not_started', 'in_progress', 'blocked', 'complete'];

function TaskForm({ initial, onCancel, onSubmit, busy, testIdPrefix }) {
  const [form, setForm] = useState(initial || { task_name: '', assigned_to: '', status: 'not_started', estimated_minutes: '', notes: '' });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const submit = () => onSubmit({
    task_name: form.task_name || 'Untitled Task',
    assigned_to: form.assigned_to || '',
    status: form.status || 'not_started',
    estimated_minutes: form.estimated_minutes === '' || form.estimated_minutes === null ? null : Number(form.estimated_minutes),
    notes: form.notes || '',
  });
  return (
    <div className="p-3 bg-violet-50/50 rounded-md border border-violet-200 space-y-2" data-testid={`${testIdPrefix}-form`}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
        <div className="md:col-span-2"><Label className="text-xs">Task</Label><Input value={form.task_name} onChange={(e) => set('task_name', e.target.value)} data-testid={`${testIdPrefix}-name`} /></div>
        <div><Label className="text-xs">Assigned</Label><Input value={form.assigned_to} onChange={(e) => set('assigned_to', e.target.value)} data-testid={`${testIdPrefix}-assigned`} /></div>
        <div>
          <Label className="text-xs">Status</Label>
          <select className="w-full border rounded h-9 px-2 text-sm" value={form.status} onChange={(e) => set('status', e.target.value)} data-testid={`${testIdPrefix}-status`}>
            {TASK_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
        <div><Label className="text-xs">Est. Minutes</Label><Input type="number" value={form.estimated_minutes} onChange={(e) => set('estimated_minutes', e.target.value)} data-testid={`${testIdPrefix}-est`} /></div>
        <div className="md:col-span-3"><Label className="text-xs">Notes</Label><Input value={form.notes} onChange={(e) => set('notes', e.target.value)} data-testid={`${testIdPrefix}-notes`} /></div>
      </div>
      <div className="flex items-center justify-end gap-2 pt-1">
        <Button size="sm" variant="outline" onClick={onCancel} data-testid={`${testIdPrefix}-cancel`}><X className="h-3.5 w-3.5 mr-1" /> Cancel</Button>
        <Button size="sm" onClick={submit} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid={`${testIdPrefix}-submit`}><Check className="h-3.5 w-3.5 mr-1" /> Save Task</Button>
      </div>
    </div>
  );
}

export default function ProductionTab({
  wrapData,
  onSaveProduction,
  onToggleChecklist,
  onLoadDefaults,
  onAddTask,
  onUpdateTask,
  onDeleteTask,
  saveStatus,
}) {
  const production = wrapData?.production || {};
  const tasks = production.tasks || [];
  const [form, setForm] = useState({ production_status: 'not_started', assigned_to: '', production_notes: '' });
  const [dirty, setDirty] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({
      production_status: production.production_status || 'not_started',
      assigned_to: production.assigned_to || '',
      production_notes: production.production_notes || '',
    });
    setDirty(false);
  }, [wrapData]);  // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const ok = await onSaveProduction?.(form);
    if (ok) setDirty(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Production Status"
          icon={Factory}
          testId="prod-status"
          action={
            <div className="flex items-center gap-2 flex-wrap">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="prod-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="prod-save-btn"><Save className="h-3.5 w-3.5 mr-1" /> Save Production</Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <Label className="text-xs">Status</Label>
              <select className="w-full border rounded h-9 px-2 text-sm" value={form.production_status} onChange={(e) => set('production_status', e.target.value)} data-testid="prod-select-status">
                {STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div className="md:col-span-2"><Label className="text-xs">Assigned To</Label><Input value={form.assigned_to} onChange={(e) => set('assigned_to', e.target.value)} placeholder="Production lead" data-testid="prod-input-assigned_to" /></div>
            <div className="md:col-span-3"><Label className="text-xs">Production Notes</Label><Textarea rows={2} value={form.production_notes} onChange={(e) => set('production_notes', e.target.value)} data-testid="prod-input-notes" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Production Checklist" icon={Boxes} testId="prod-checklist">
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-y-1 gap-x-4" data-testid="prod-checklist-list">
            {CHECKLIST_DEFS.map(([key, label]) => {
              const done = !!production[key];
              const ts = production[`${key}_at`];
              return (
                <li key={key} className="flex items-center justify-between gap-3 py-0.5">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={done}
                      onChange={(e) => onToggleChecklist?.(key, e.target.checked)}
                      disabled={busy}
                      data-testid={`prod-toggle-${key}`}
                    />
                    <span className={done ? 'line-through text-slate-500' : 'text-slate-700'}>{label}</span>
                  </label>
                  {ts && <span className="text-[10px] text-slate-500" data-testid={`prod-ts-${key}`}>{new Date(ts).toLocaleString()}</span>}
                </li>
              );
            })}
          </ul>
        </WrapSectionCard>

        <WrapSectionCard
          title="Production Tasks"
          icon={Printer}
          testId="prod-tasks"
          action={
            <div className="flex items-center gap-2">
              {tasks.length === 0 && (
                <Button size="sm" variant="outline" onClick={onLoadDefaults} disabled={busy} data-testid="prod-load-defaults-btn">
                  Load Default Wrap Tasks
                </Button>
              )}
              {!showAdd && (
                <Button size="sm" onClick={() => { setShowAdd(true); setEditingId(null); }} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="prod-add-task-btn">
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Task
                </Button>
              )}
            </div>
          }
        >
          {showAdd && (
            <div className="mb-3">
              <TaskForm
                onCancel={() => setShowAdd(false)}
                onSubmit={async (p) => { await onAddTask?.(p); setShowAdd(false); }}
                busy={busy}
                testIdPrefix="prod-task-add"
              />
            </div>
          )}
          {tasks.length === 0 && !showAdd ? (
            <p className="text-sm text-slate-500 italic py-2" data-testid="prod-tasks-empty">
              No production tasks yet. Click <span className="font-medium">Load Default Wrap Tasks</span> or <span className="font-medium">Add Task</span>.
            </p>
          ) : (
            <div className="space-y-2" data-testid="prod-tasks-list">
              {tasks.map((t) => {
                if (editingId === t.id) {
                  return (
                    <TaskForm
                      key={t.id}
                      initial={{ ...t, estimated_minutes: t.estimated_minutes ?? '' }}
                      onCancel={() => setEditingId(null)}
                      onSubmit={async (p) => { await onUpdateTask?.(t.id, p); setEditingId(null); }}
                      busy={busy}
                      testIdPrefix={`prod-task-edit-${t.id}`}
                    />
                  );
                }
                const statusCls = t.status === 'complete'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : t.status === 'in_progress' ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : t.status === 'blocked' ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200';
                return (
                  <div key={t.id} className="flex flex-wrap items-center justify-between gap-3 p-2 border rounded-md bg-white" data-testid={`prod-task-row-${t.id}`}>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className={`font-medium text-sm ${t.status === 'complete' ? 'line-through text-slate-500' : 'text-slate-800'}`}>{t.task_name}</p>
                        <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${statusCls}`}>{(t.status || 'not_started').replace(/_/g, ' ')}</span>
                        {t.completed_at && <span className="text-[10px] text-emerald-700">{new Date(t.completed_at).toLocaleDateString()}</span>}
                      </div>
                      <p className="text-xs text-slate-500">
                        {t.assigned_to || '—'} · est {t.estimated_minutes ?? '—'}m{t.actual_minutes != null ? ` · actual ${t.actual_minutes}m` : ''}
                        {t.notes ? ` · ${t.notes}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      {t.status !== 'complete' && (
                        <Button size="sm" variant="outline" className="text-xs h-7 bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100" onClick={() => onUpdateTask?.(t.id, { status: 'complete' })} disabled={busy} data-testid={`prod-task-complete-${t.id}`}><Check className="h-3 w-3 mr-1" /> Complete</Button>
                      )}
                      <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => { setEditingId(t.id); setShowAdd(false); }} disabled={busy} data-testid={`prod-task-edit-${t.id}`}><Pencil className="h-3 w-3 mr-1" /> Edit</Button>
                      <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={() => onDeleteTask?.(t.id)} disabled={busy} data-testid={`prod-task-delete-${t.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Production AI Helper"
        testId="prod-ai-helper"
        actions={[
          { label: 'Build Checklist' },
          { label: 'Estimate Time' },
          { label: 'Check Bottlenecks' },
          { label: 'Compare Labor' },
          { label: 'Suggest Next Step' },
        ]}
      />
    </div>
  );
}
