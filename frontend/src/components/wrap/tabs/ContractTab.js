// Phase 2C: Contract & Approvals tab — real persistence + approval checklist.
import { useEffect, useState } from 'react';
import WrapSectionCard from '../WrapSectionCard';
import WrapAIHelperCard from '../WrapAIHelperCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { FileSignature, ShieldCheck, CreditCard, ClipboardCheck, Save, Check, Send, Eye, Archive, FilePenLine } from 'lucide-react';

const STATUS_STYLE = {
  not_created: 'bg-slate-100 text-slate-700',
  draft: 'bg-blue-100 text-blue-800',
  sent: 'bg-amber-100 text-amber-800',
  viewed: 'bg-violet-100 text-violet-800',
  signed: 'bg-emerald-100 text-emerald-800',
  stored: 'bg-emerald-200 text-emerald-900',
};

const APPROVAL_DEFS = [
  { key: 'quote_approved', label: 'Quote Approved' },
  { key: 'contract_signed', label: 'Contract Signed' },
  { key: 'deposit_paid', label: 'Deposit Paid' },
  { key: 'proof_approved', label: 'Proof Approved' },
  { key: 'inspection_acknowledged', label: 'Inspection Acknowledged' },
  { key: 'final_signoff_completed', label: 'Final Signoff Completed' },
  { key: 'aftercare_sent', label: 'Aftercare Sent' },
];

const EMPTY = {
  contract_template: '', terms_summary: '', contract_notes: '',
  signed_by: '', signed_contract_url: '',
};

export default function ContractTab({
  wrapData,
  onSaveContract,
  onContractAction,
  onUpdateApprovals,
  onDraftQuoteMessage,
  saveStatus,
}) {
  const contract = wrapData?.contract || {};
  const approvals = wrapData?.approvals || {};
  const [form, setForm] = useState(EMPTY);
  const [dirty, setDirty] = useState(false);
  const busy = saveStatus === 'saving';

  useEffect(() => {
    const c = wrapData?.contract || {};
    setForm({
      contract_template: c.contract_template || '',
      terms_summary: c.terms_summary || '',
      contract_notes: c.contract_notes || '',
      signed_by: c.signed_by || '',
      signed_contract_url: c.signed_contract_url || '',
    });
    setDirty(false);
  }, [wrapData]);

  const set = (k, v) => { setForm((f) => ({ ...f, [k]: v })); setDirty(true); };

  const handleSave = async () => {
    const ok = await onSaveContract?.(form);
    if (ok) setDirty(false);
  };

  const status = contract.contract_status || 'not_created';
  const statusClass = STATUS_STYLE[status] || STATUS_STYLE.not_created;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
      <div className="space-y-3">
        <WrapSectionCard
          title="Contract Status"
          icon={FileSignature}
          testId="contract-status"
          action={
            <div className="flex items-center gap-2 flex-wrap">
              {dirty && <span className="text-[11px] text-amber-700" data-testid="contract-unsaved-indicator">Unsaved changes</span>}
              <Button size="sm" onClick={handleSave} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="contract-save-btn"><Save className="h-3.5 w-3.5 mr-1" /> Save Contract</Button>
            </div>
          }
        >
          <div className="flex items-center gap-2 flex-wrap mb-3">
            <span className="text-xs text-slate-500">Status:</span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${statusClass}`} data-testid="contract-status-chip">{status.replace(/_/g, ' ')}</span>
            {contract.contract_id && <span className="text-[11px] text-slate-500">ID: {contract.contract_id}</span>}
            {contract.contract_sent_at && <span className="text-[11px] text-amber-700" data-testid="contract-sent-at">Sent: {new Date(contract.contract_sent_at).toLocaleString()}</span>}
            {contract.contract_viewed_at && <span className="text-[11px] text-violet-700" data-testid="contract-viewed-at">Viewed: {new Date(contract.contract_viewed_at).toLocaleString()}</span>}
            {contract.contract_signed_at && <span className="text-[11px] text-emerald-700" data-testid="contract-signed-at">Signed: {new Date(contract.contract_signed_at).toLocaleString()}</span>}
          </div>
          <div className="flex flex-wrap gap-2" data-testid="contract-actions">
            <Button size="sm" variant="outline" onClick={() => onContractAction?.('generate_draft')} disabled={busy} data-testid="contract-action-generate_draft"><FilePenLine className="h-3.5 w-3.5 mr-1" /> Generate Draft</Button>
            <Button size="sm" variant="outline" onClick={() => onContractAction?.('send')} disabled={busy} data-testid="contract-action-send"><Send className="h-3.5 w-3.5 mr-1" /> Send Contract</Button>
            <Button size="sm" variant="outline" onClick={() => onContractAction?.('mark_viewed')} disabled={busy} data-testid="contract-action-mark_viewed"><Eye className="h-3.5 w-3.5 mr-1" /> Mark Viewed</Button>
            <Button size="sm" variant="outline" onClick={() => onContractAction?.('mark_signed', { signed_by: form.signed_by })} disabled={busy} data-testid="contract-action-mark_signed"><Check className="h-3.5 w-3.5 mr-1" /> Mark Signed</Button>
            <Button size="sm" variant="outline" onClick={() => onContractAction?.('store_signed', { signed_contract_url: form.signed_contract_url })} disabled={busy} data-testid="contract-action-store_signed"><Archive className="h-3.5 w-3.5 mr-1" /> Store Signed</Button>
            <Button size="sm" variant="outline" onClick={() => window.alert('Document download will be connected in a later phase.')} data-testid="contract-action-download"><FileSignature className="h-3.5 w-3.5 mr-1" /> Download (placeholder)</Button>
          </div>
        </WrapSectionCard>

        <WrapSectionCard title="Contract Details" icon={FileSignature} testId="contract-details">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div><Label className="text-xs">Contract Template</Label><Input value={form.contract_template} onChange={(e) => set('contract_template', e.target.value)} placeholder="Standard Wrap Contract" data-testid="contract-input-template" /></div>
            <div><Label className="text-xs">Signed By</Label><Input value={form.signed_by} onChange={(e) => set('signed_by', e.target.value)} placeholder="Customer name" data-testid="contract-input-signed_by" /></div>
            <div className="md:col-span-2"><Label className="text-xs">Signed Contract URL (placeholder)</Label><Input value={form.signed_contract_url} onChange={(e) => set('signed_contract_url', e.target.value)} placeholder="Paste a link if storing externally" data-testid="contract-input-signed_url" /></div>
            <div className="md:col-span-2"><Label className="text-xs">Terms Summary</Label><Textarea rows={5} value={form.terms_summary} onChange={(e) => set('terms_summary', e.target.value)} placeholder="A short plain-language summary of the contract" data-testid="contract-input-terms_summary" /></div>
            <div className="md:col-span-2"><Label className="text-xs">Contract Notes</Label><Textarea rows={2} value={form.contract_notes} onChange={(e) => set('contract_notes', e.target.value)} data-testid="contract-input-notes" /></div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Accepted terms: <span className="font-medium" data-testid="contract-accepted-terms">{contract.accepted_terms ? 'Yes' : 'No'}</span></p>
        </WrapSectionCard>

        <WrapSectionCard title="Signed Contract Storage" icon={ShieldCheck} testId="contract-storage">
          {contract.signed_contract_url ? (
            <a className="text-sm text-violet-700 underline" href={contract.signed_contract_url} target="_blank" rel="noreferrer" data-testid="contract-storage-link">{contract.signed_contract_url}</a>
          ) : (
            <p className="text-xs text-slate-500 italic">No signed contract stored yet. Paste a URL in the field above and click "Store Signed".</p>
          )}
        </WrapSectionCard>

        <WrapSectionCard
          title="Approval Checklist"
          icon={ClipboardCheck}
          testId="contract-approvals"
        >
          <ul className="space-y-1.5" data-testid="approval-checklist">
            {APPROVAL_DEFS.map((a) => {
              const done = !!approvals[a.key];
              const ts = approvals[`${a.key}_at`];
              return (
                <li key={a.key} className="flex items-center justify-between gap-3 py-1">
                  <label className="flex items-center gap-2 cursor-pointer text-sm" data-testid={`approval-row-${a.key}`}>
                    <input
                      type="checkbox"
                      checked={done}
                      onChange={(e) => onUpdateApprovals?.({ [a.key]: e.target.checked })}
                      disabled={busy}
                      data-testid={`approval-toggle-${a.key}`}
                    />
                    <span className={done ? 'line-through text-slate-500' : 'text-slate-700'}>{a.label}</span>
                  </label>
                  {ts && <span className="text-[10px] text-slate-500" data-testid={`approval-ts-${a.key}`}>{new Date(ts).toLocaleString()}</span>}
                </li>
              );
            })}
          </ul>
        </WrapSectionCard>

        <WrapSectionCard
          title="Payment & Quote Communications"
          icon={CreditCard}
          testId="contract-payment"
          action={
            <Button size="sm" onClick={onDraftQuoteMessage} disabled={busy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="contract-draft-quote-btn">
              <Send className="h-3.5 w-3.5 mr-1" /> Draft Updated Quote Message
            </Button>
          }
        >
          <p className="text-xs text-slate-500">
            Use the button to compose an updated-quote email based on the current wrap pricing,
            vehicle, and customer info. Payment link generation will be connected in a later phase.
          </p>
        </WrapSectionCard>
      </div>

      <WrapAIHelperCard
        title="Contract Draft AI"
        testId="contract-ai-helper"
        actions={[
          { label: 'Draft Contract' },
          { label: 'Check Contract' },
          { label: 'Summarize Terms' },
          { label: 'Write Contract Email' },
          { label: 'Write Approval Reminder' },
        ]}
      />
    </div>
  );
}
