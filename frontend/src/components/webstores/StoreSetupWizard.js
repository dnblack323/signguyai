/**
 * Simplified Store Setup Wizard — 3 steps only.
 *
 * Captures only the minimal fields needed to create a store and send the
 * correct questionnaire:  store_type → store name → owner name / email / phone.
 *
 * Branding, dates, fulfillment, payments and review are all DEFERRED to the
 * store detail dialog once the questionnaire has been submitted and staff
 * review is complete.
 *
 * After creation the wizard transitions to a `CreationResult` screen that
 * offers to send the appropriate setup questionnaire immediately. If the email
 * fails it shows a copyable link so staff can share it manually.
 *
 * Compatibility guarantees (unchanged from Phase 3):
 *   - Uses the SAME `formData` state the page already manages.
 *   - Calls the SAME `handleCreateStore` handler via the `onSubmit` prop.
 *   - The wrapping <Dialog> in Webstores.js still controls open / close.
 */
import { useMemo, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { Separator } from '../ui/separator';
import {
  Check, ChevronLeft, ChevronRight, Loader2, AlertTriangle,
  Building2, Mail, Sparkles, Copy, CheckCircle2, ClipboardCheck,
} from 'lucide-react';
import { cn } from '../../lib/utils';

// ──────────────────────────────────────────────────────────────────────────────
// Step definitions — only 3 steps needed for minimal creation
// ──────────────────────────────────────────────────────────────────────────────
const STEPS = [
  { id: 'type',   label: 'Store Type', icon: Sparkles,  optional: false },
  { id: 'basics', label: 'Basics',     icon: Building2, optional: false },
  { id: 'owner',  label: 'Owner Info', icon: Mail,      optional: false },
];

// ── Shared sub-components ────────────────────────────────────────────────────

const StepHeader = ({ activeIdx }) => (
  <div className="flex items-center gap-1 overflow-x-auto pb-2 -mx-1 px-1" data-testid="wizard-stepper">
    {STEPS.map((s, idx) => {
      const Icon = s.icon;
      const isActive  = idx === activeIdx;
      const isComplete = idx < activeIdx;
      return (
        <div key={s.id} className="flex items-center shrink-0">
          <div
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium whitespace-nowrap',
              isActive   && 'bg-blue-600 text-white',
              isComplete && 'bg-emerald-100 text-emerald-700',
              !isActive && !isComplete && 'bg-gray-100 text-gray-500',
            )}
            data-testid={`wizard-step-${s.id}-${isActive ? 'active' : isComplete ? 'done' : 'todo'}`}
          >
            {isComplete ? <Check className="h-3 w-3" /> : <Icon className="h-3 w-3" />}
            <span>{idx + 1}. {s.label}</span>
          </div>
          {idx < STEPS.length - 1 && (
            <div className={cn('h-px w-3', isComplete ? 'bg-emerald-300' : 'bg-gray-200')} />
          )}
        </div>
      );
    })}
  </div>
);

const Field = ({ label, required = false, hint, children, testId }) => (
  <div className="space-y-1" data-testid={testId}>
    <Label className="text-xs flex items-center gap-1">
      {label}
      {required  && <span className="text-red-500">*</span>}
      {!required && <span className="text-[10px] text-gray-400 font-normal">(optional)</span>}
    </Label>
    {children}
    {hint && <p className="text-[11px] text-gray-500">{hint}</p>}
  </div>
);

// ──────────────────────────────────────────────────────────────────────────────
// CreationResult — shown after successful store creation
// ──────────────────────────────────────────────────────────────────────────────
function CreationResult({ store, onDone, onSendQuestionnaire }) {
  const [sending, setSending]             = useState(false);
  const [sent, setSent]                   = useState(false);
  const [emailFailed, setEmailFailed]     = useState(false);
  const [link, setLink]                   = useState(null);
  const [overrideEmail, setOverrideEmail] = useState(store?.owner_email || '');
  const [copied, setCopied]               = useState(false);

  const storeTypeLabel = {
    business:  'Business',
    fundraiser:'Fundraiser',
    creator:   'Creator / Team',
    event:     'Event',
  }[store?.store_type] || store?.store_type;

  const handleSend = async () => {
    if (!overrideEmail?.trim()) return;
    setSending(true);
    setEmailFailed(false);
    try {
      const result = await onSendQuestionnaire(store.id, overrideEmail.trim());
      if (result?.email_sent) {
        setSent(true);
      } else {
        setEmailFailed(true);
        setLink(result?.link || null);
      }
    } catch {
      setEmailFailed(true);
    } finally {
      setSending(false);
    }
  };

  const copyLink = () => {
    if (!link) return;
    navigator.clipboard.writeText(link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="space-y-4" data-testid="wizard-creation-result">
      {/* ── Success header ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg p-3">
        <CheckCircle2 className="h-6 w-6 text-green-600 shrink-0" />
        <div>
          <p className="font-semibold text-green-900">"{store?.name}" created</p>
          <p className="text-xs text-green-700">
            Store is in <strong>pending</strong> state. Send the questionnaire so the owner can fill in the rest.
          </p>
        </div>
      </div>

      {/* ── Questionnaire card ─────────────────────────────────────── */}
      <div className="border rounded-lg p-4 space-y-3">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="h-4 w-4 text-blue-600" />
          <p className="text-sm font-semibold">Send Setup Questionnaire</p>
          <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded capitalize">
            {storeTypeLabel}
          </span>
        </div>
        <p className="text-xs text-gray-500">
          This sends the appropriate questionnaire for this store type so the owner can fill in
          event details, fulfillment preferences, and their Stripe setup. Staff reviews the answers
          before the store goes live.
        </p>

        {sent ? (
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded p-2.5">
            <Check className="h-4 w-4 text-green-600 shrink-0" />
            <p className="text-sm font-medium text-green-800">
              Questionnaire sent to <strong>{overrideEmail}</strong>
            </p>
          </div>
        ) : (
          <>
            <Field label="Send to email" required hint="The questionnaire link will be emailed here.">
              <Input
                type="email"
                value={overrideEmail}
                onChange={(e) => setOverrideEmail(e.target.value)}
                placeholder="owner@example.com"
                data-testid="questionnaire-email-input"
              />
            </Field>

            {/* ── Email-failed fallback ──────────────────────────── */}
            {emailFailed && (
              <div
                className="bg-amber-50 border border-amber-200 rounded p-3 space-y-2"
                data-testid="questionnaire-link-fallback"
              >
                <p className="text-xs font-medium text-amber-800 flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                  Email could not be sent. Copy this link and share it directly with the owner:
                </p>
                {link && (
                  <div className="flex items-center gap-2">
                    <code
                      className="flex-1 text-[11px] bg-white border rounded px-2 py-1.5 overflow-hidden text-ellipsis whitespace-nowrap select-all"
                      data-testid="questionnaire-copy-link"
                    >
                      {link}
                    </code>
                    <Button
                      size="icon"
                      variant="outline"
                      className="shrink-0 h-8 w-8"
                      onClick={copyLink}
                      data-testid="copy-link-btn"
                    >
                      {copied
                        ? <Check className="h-3.5 w-3.5 text-green-600" />
                        : <Copy className="h-3.5 w-3.5" />}
                    </Button>
                  </div>
                )}
              </div>
            )}

            <Button
              onClick={handleSend}
              disabled={sending || !overrideEmail?.trim()}
              className="w-full bg-blue-600 hover:bg-blue-700"
              data-testid="send-questionnaire-btn"
            >
              {sending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Sending…</>
              ) : emailFailed ? (
                <><Mail className="h-4 w-4 mr-2" /> Retry Send</>
              ) : (
                <><Mail className="h-4 w-4 mr-2" /> Send Questionnaire</>
              )}
            </Button>

            {!store?.owner_email && !overrideEmail && (
              <p className="text-[11px] text-amber-600">
                No owner email was provided. Enter one above or skip to share the link later.
              </p>
            )}
          </>
        )}
      </div>

      <Separator />

      <div className="flex items-center justify-between pt-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={onDone}
          data-testid="wizard-skip-questionnaire-btn"
        >
          {sent ? 'Done' : 'Skip for now'}
        </Button>
        {sent && (
          <Button onClick={onDone} data-testid="wizard-done-btn">
            View Store
          </Button>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Main wizard component
// ──────────────────────────────────────────────────────────────────────────────
export default function StoreSetupWizard({
  storeTypes,
  formData,
  setFormData,
  creatingStore,
  onSubmit,
  onCancel,
  // Result state — supplied by Webstores.js after store is created
  createdStore,
  onSendQuestionnaire,
}) {
  const [stepIdx, setStepIdx] = useState(0);
  const [touched, setTouched] = useState({});
  const currentStep = STEPS[stepIdx];

  // ---------- Validation ----------
  const stepErrors = useMemo(() => {
    const errs = {};
    if (!formData.store_type) errs.type = 'Pick a store type to continue.';
    if (!formData.name?.trim()) errs.name = 'Store name is required.';
    if (!formData.owner_name?.trim()) errs.owner_name = 'Owner / organization name is required.';
    if (formData.owner_email && !/^\S+@\S+\.\S+$/.test(formData.owner_email)) {
      errs.owner_email = 'Looks like that email is not valid.';
    }
    return errs;
  }, [formData]);

  const errorsForStep = (id) => {
    if (id === 'type')  return stepErrors.type       ? [stepErrors.type]       : [];
    if (id === 'basics') return stepErrors.name       ? [stepErrors.name]       : [];
    if (id === 'owner') return [stepErrors.owner_name, stepErrors.owner_email].filter(Boolean);
    return [];
  };

  const canGoNext = errorsForStep(currentStep.id).length === 0;
  const isLast    = stepIdx === STEPS.length - 1;

  const goNext = () => {
    if (!canGoNext) { setTouched((t) => ({ ...t, [currentStep.id]: true })); return; }
    setStepIdx((i) => Math.min(i + 1, STEPS.length - 1));
  };
  const goPrev = () => setStepIdx((i) => Math.max(i - 1, 0));

  // After creation: show result / questionnaire screen
  if (createdStore) {
    return (
      <CreationResult
        store={createdStore}
        onDone={onCancel}
        onSendQuestionnaire={onSendQuestionnaire}
      />
    );
  }

  const canCreate = !['type', 'name', 'owner_name'].some((k) => stepErrors[k]);

  return (
    <div className="space-y-4" data-testid="store-setup-wizard">
      <StepHeader activeIdx={stepIdx} />
      <Separator />

      {/* ── Step content ─────────────────────────────────────────────── */}
      <div className="min-h-[220px]">

        {/* Step 1 — Store Type */}
        {currentStep.id === 'type' && (
          <div className="space-y-3" data-testid="wizard-pane-type">
            <Label className="text-sm">
              Select a store type to get started <span className="text-red-500">*</span>
            </Label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {storeTypes.map((type) => {
                const Icon   = type.icon;
                const active = formData.store_type === type.value;
                return (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, store_type: type.value })}
                    className={cn(
                      'p-3 rounded-lg border-2 text-left transition-all',
                      active ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-300',
                    )}
                    data-testid={`wizard-type-${type.value}`}
                  >
                    <Icon className={cn('h-5 w-5 mb-2', active ? 'text-blue-600' : 'text-gray-500')} />
                    <p className="font-medium text-sm text-gray-900">{type.label}</p>
                    <p className="text-[11px] text-gray-500">{type.description}</p>
                  </button>
                );
              })}
            </div>
            {touched.type && stepErrors.type && (
              <p className="text-xs text-red-600">{stepErrors.type}</p>
            )}
          </div>
        )}

        {/* Step 2 — Basics */}
        {currentStep.id === 'basics' && (
          <div className="space-y-3" data-testid="wizard-pane-basics">
            <Field label="Store Name" required testId="wizard-name-field">
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., ABC Company Store"
                data-testid="wizard-name-input"
                autoFocus
              />
            </Field>
            <Field label="Description" hint="Shown on the public storefront header.">
              <Textarea
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Store description (optional)…"
                data-testid="wizard-description-input"
              />
            </Field>
            <div className="flex items-center justify-between bg-gray-50 border rounded p-2">
              <div>
                <Label className="text-xs">Public Store</Label>
                <p className="text-[11px] text-gray-500">Anyone with the link can browse and order.</p>
              </div>
              <Switch
                checked={formData.is_public}
                onCheckedChange={(v) => setFormData({ ...formData, is_public: v })}
                data-testid="wizard-public-switch"
              />
            </div>
            {touched.basics && stepErrors.name && (
              <p className="text-xs text-red-600">{stepErrors.name}</p>
            )}
          </div>
        )}

        {/* Step 3 — Owner Info */}
        {currentStep.id === 'owner' && (
          <div className="space-y-3" data-testid="wizard-pane-owner">
            <Field label="Owner / Organization Name" required testId="wizard-owner-field">
              <Input
                value={formData.owner_name}
                onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                placeholder="Company or individual name"
                data-testid="wizard-owner-input"
                autoFocus
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Contact Email" hint="Used to send the setup questionnaire.">
                <Input
                  type="email"
                  value={formData.owner_email}
                  onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                  placeholder="email@example.com"
                  data-testid="wizard-owner-email-input"
                />
              </Field>
              <Field label="Contact Phone">
                <Input
                  value={formData.owner_phone}
                  onChange={(e) => setFormData({ ...formData, owner_phone: e.target.value })}
                  placeholder="(555) 123-4567"
                  data-testid="wizard-owner-phone-input"
                />
              </Field>
            </div>
            {touched.owner && stepErrors.owner_name && (
              <p className="text-xs text-red-600">{stepErrors.owner_name}</p>
            )}
            {stepErrors.owner_email && (
              <p className="text-xs text-red-600">{stepErrors.owner_email}</p>
            )}
            <div className="bg-blue-50 border border-blue-200 rounded p-2.5 text-xs text-blue-800">
              After creation, a questionnaire will be sent to the owner to collect event details,
              fulfillment preferences, and Stripe setup. Branding, dates, and pricing are configured there.
            </div>
          </div>
        )}
      </div>

      <Separator />

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-2 pt-1">
        <Button
          type="button"
          variant="ghost"
          onClick={onCancel}
          disabled={creatingStore}
          data-testid="wizard-cancel-btn"
        >
          Cancel
        </Button>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={goPrev}
            disabled={stepIdx === 0 || creatingStore}
            data-testid="wizard-prev-btn"
          >
            <ChevronLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          {!isLast ? (
            <Button type="button" onClick={goNext} disabled={creatingStore} data-testid="wizard-next-btn">
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button
              type="button"
              onClick={onSubmit}
              disabled={creatingStore || !canCreate}
              data-testid="wizard-submit-btn"
              className="bg-blue-600 hover:bg-blue-700"
            >
              {creatingStore ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Creating…</>
              ) : (
                <>Create Store <Check className="h-4 w-4 ml-1" /></>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
