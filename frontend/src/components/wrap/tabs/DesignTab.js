// Phase 2C: Design & Mockups tab — real persistence + proof versions.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import WrapEmptyState from '../WrapEmptyState';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { ClipboardList, Upload, Wand2, Eye, CheckCircle2, Save, Plus, Trash2, Send } from 'lucide-react';

const EMPTY = {
  design_brief: '', style_direction: '', brand_colors: '', required_text: '',
  services_to_feature: '', design_notes: '', artwork_notes: '',
  mockup_status: 'not_started', proof_status: 'not_started',
  revision_notes: '',
};

const Q_STATUS = [
  { v: 'not_sent', label: 'Not Sent', cls: 'bg-slate-100 text-slate-700' },
  { v: 'sent', label: 'Sent', cls: 'bg-amber-100 text-amber-800' },
  { v: 'completed', label: 'Completed', cls: 'bg-emerald-100 text-emerald-800' },
  { v: 'reviewed', label: 'Reviewed', cls: 'bg-violet-100 text-violet-800' },
];

const PROOF_STATUS = [
  { v: 'not_started', label: 'Not Started' },
  { v: 'draft', label: 'Draft' },
  { v: 'sent', label: 'Sent' },
  { v: 'revision_requested', label: 'Revision Requested' },
  { v: 'approved', label: 'Approved' },
];

export default function DesignTab({
  wrapData,
  onSaveDesign,
  onSendQuestionnaire,
  onAddProof,
  onUpdateProof,
  onDeleteProof,
  saveStatus,
}) {
  const design = wrapData?.design || {};
  const [form, setForm] = useState(EMPTY);
  const [dirty, setDirty] = useState(false);
  const [proofLabel, setProofLabel] = useState('');
  const busy = saveStatus === 'saving';

  useEffect(() => {
    setForm({ ...EMPTY, ...(wrapData?.design || {}) });
    setDirty(false);
  }, [wrapData]);

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const ok = await onSaveDesign?.({
      design_brief: form.design_brief,
      style_direction: form.style_direction,
      brand_colors: form.brand_colors,
      required_text: form.required_text,
      services_to_feature: form.services_to_feature,
      design_notes: form.design_notes,
      artwork_notes: form.artwork_notes,
      mockup_status: form.mockup_status,
      proof_status: form.proof_status,
      revision_notes: form.revision_notes,
    });
    if (ok) setDirty(false);
  };

  const qStatus = Q_STATUS.find((q) => q.v === (design.questionnaire_status || 'not_sent')) || Q_STATUS[0];
  const proofs = design.proof_versions || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Design Brief"
          icon={ClipboardList}
          testId="design-brief"
          action={
            <div className="flex items-center gap-2">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="design-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="design-save-btn">
                <Save className="h-3.5 w-3.5 mr-1" /> Save Design
              </Button>
            </div>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div><Label className="text-xs">Style Direction</Label><Input value={form.style_direction || ''} onChange={(e) => set('style_direction', e.target.value)} placeholder="Bold, modern, clean" data-testid="design-input-style_direction" /></div>
            <div><Label className="text-xs">Brand Colors</Label><Input value={form.brand_colors || ''} onChange={(e) => set('brand_colors', e.target.value)} placeholder="Navy + White + Gold" data-testid="design-input-brand_colors" /></div>
            <div><Label className="text-xs">Required Text</Label><Input value={form.required_text || ''} onChange={(e) => set('required_text', e.target.value)} placeholder="Phone, URL, slogan" data-testid="design-input-required_text" /></div>
            <div><Label className="text-xs">Services to Feature</Label><Input value={form.services_to_feature || ''} onChange={(e) => set('services_to_feature', e.target.value)} placeholder="What the wrap is selling" data-testid="design-input-services_to_feature" /></div>
            <div className="md:col-span-2"><Label className="text-xs">Design Brief</Label><Textarea rows={3} value={form.design_brief || ''} onChange={(e) => set('design_brief', e.target.value)} placeholder="One-line summary of the visual direction" data-testid="design-input-design_brief" /></div>
            <div className="md:col-span-2"><Label className="text-xs">Design Notes</Label><Textarea rows={2} value={form.design_notes || ''} onChange={(e) => set('design_notes', e.target.value)} data-testid="design-input-design_notes" /></div>
          </div>
        </WrapSectionCard>

        <WrapSectionCard
          title="Design Questionnaire"
          icon={ClipboardList}
          testId="design-questionnaire"
          action={
            <Button size="sm" onClick={onSendQuestionnaire} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="design-send-questionnaire-btn">
              <Send className="h-3.5 w-3.5 mr-1" /> Send Questionnaire
            </Button>
          }
        >
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-500">Status:</span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${qStatus.cls}`} data-testid="design-questionnaire-status">{qStatus.label}</span>
            {design.questionnaire_sent_at && <span className="text-[11px] text-slate-500">Sent: {new Date(design.questionnaire_sent_at).toLocaleString()}</span>}
            {design.questionnaire_completed_at && <span className="text-[11px] text-emerald-700">Completed: {new Date(design.questionnaire_completed_at).toLocaleString()}</span>}
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Customer delivery of the questionnaire link will be connected in a later phase.
          </p>
        </WrapSectionCard>

        <WrapSectionCard
          title="Artwork & References"
          icon={Upload}
          testId="design-artwork"
        >
          <Label className="text-xs">Artwork Notes</Label>
          <Textarea rows={2} value={form.artwork_notes || ''} onChange={(e) => set('artwork_notes', e.target.value)} placeholder="Where artwork lives, missing pieces, etc." data-testid="design-input-artwork_notes" />
          <p className="text-[11px] text-slate-500 mt-2">Real artwork uploads will use the order's existing Assets panel.</p>
        </WrapSectionCard>

        <WrapSectionCard
          title="AI Mockup (placeholder)"
          icon={Wand2}
          testId="design-mockup"
        >
          <div className="flex items-center gap-2">
            <Label className="text-xs">Mockup Status</Label>
            <select
              className="border rounded h-8 px-2 text-xs"
              value={form.mockup_status || 'not_started'}
              onChange={(e) => set('mockup_status', e.target.value)}
              data-testid="design-select-mockup_status"
            >
              <option value="not_started">Not Started</option>
              <option value="requested">Requested</option>
              <option value="generated">Generated</option>
              <option value="reviewed">Reviewed</option>
            </select>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Real AI mockup generation will be connected in a later phase.</p>
        </WrapSectionCard>

        <WrapSectionCard
          title="Proof Versions"
          icon={Eye}
          testId="design-proofs"
          action={
            <div className="flex items-center gap-2">
              <Input value={proofLabel} onChange={(e) => setProofLabel(e.target.value)} placeholder="V1 Mockup" className="h-8 w-32 text-xs" data-testid="design-proof-label" />
              <Button size="sm" onClick={async () => { if (!proofLabel) return; await onAddProof?.({ label: proofLabel, notes: '' }); setProofLabel(''); }} disabled={busy || !proofLabel} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="design-add-proof-btn">
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Proof
              </Button>
            </div>
          }
        >
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <span className="text-xs text-slate-500">Overall proof status:</span>
            <select
              className="border rounded h-8 px-2 text-xs"
              value={form.proof_status || 'not_started'}
              onChange={(e) => set('proof_status', e.target.value)}
              data-testid="design-select-proof_status"
            >
              {PROOF_STATUS.map((s) => <option key={s.v} value={s.v}>{s.label}</option>)}
            </select>
            {design.approved_proof_id && <span className="text-[11px] text-emerald-700">Approved proof set</span>}
          </div>
          {proofs.length === 0 ? (
            <WrapEmptyState title="No proofs yet" message='Add a proof above, then mark it Approved to update the workflow.' />
          ) : (
            <div className="space-y-2" data-testid="design-proofs-list">
              {proofs.map((p) => (
                <div key={p.id} className="flex items-center justify-between gap-3 p-2 border rounded-md bg-white" data-testid={`design-proof-row-${p.id}`}>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-sm text-slate-800">{p.label || 'Proof'}</p>
                      <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${p.status === 'approved' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>{p.status}</span>
                      {p.approved_at && <span className="text-[10px] text-emerald-700">{new Date(p.approved_at).toLocaleDateString()}</span>}
                    </div>
                    {p.notes && <p className="text-xs text-slate-500">{p.notes}</p>}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button size="sm" variant="outline" className="text-xs h-7" onClick={() => onUpdateProof?.(p.id, { status: 'sent' })} disabled={busy} data-testid={`proof-send-${p.id}`}>Mark Sent</Button>
                    <Button size="sm" variant="outline" className="text-xs h-7 bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100" onClick={() => onUpdateProof?.(p.id, { status: 'approved' })} disabled={busy} data-testid={`proof-approve-${p.id}`}><CheckCircle2 className="h-3 w-3 mr-1" /> Approve</Button>
                    <Button size="sm" variant="outline" className="text-xs h-7 text-rose-700 border-rose-200 hover:bg-rose-50" onClick={() => onDeleteProof?.(p.id)} disabled={busy} data-testid={`proof-delete-${p.id}`}><Trash2 className="h-3 w-3 mr-1" /> Delete</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="Revision Notes" icon={ClipboardList} testId="design-revisions">
          <Textarea rows={2} value={form.revision_notes || ''} onChange={(e) => set('revision_notes', e.target.value)} placeholder="What changed between proof rounds" data-testid="design-input-revision_notes" />
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Design AI Helper"
        testId="design-ai-helper"
        actions={[
          { label: 'Summarize Answers' },
          { label: 'Create Design Brief' },
          { label: 'Check Artwork Quality' },
          { label: 'Generate Mockup' },
          { label: 'Write Proof Message' },
        ]}
      />
    </div>
  );
}
