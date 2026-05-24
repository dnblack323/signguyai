/**
 * Phase 3 — Store Setup Wizard.
 *
 * Replaces the previously single-screen "Create Webstore" form with a
 * 9-step staged setup wizard. The wizard captures store-level data only —
 * no product-level pricing fields are introduced here (per Phase 3 rules).
 *
 * Compatibility guarantees:
 *   - Uses the SAME `formData` state object the page already managed.
 *   - Calls the SAME `handleCreateStore` submit handler on the final step.
 *   - Logo / banner upload handlers reuse the page-level helpers.
 *   - The wrapping <Dialog> in Webstores.js still controls open/close.
 */
import { useMemo, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../ui/select';
import {
  Check, ChevronLeft, ChevronRight, Loader2, AlertTriangle,
  Image as ImageIcon, X, Upload, CalendarDays, Heart,
  CreditCard, Mail, Building2, Palette, ClipboardCheck, Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const STEPS = [
  { id: 'type',         label: 'Store Type',     icon: Sparkles,       optional: false },
  { id: 'basics',       label: 'Basics',         icon: Building2,      optional: false },
  { id: 'owner',        label: 'Owner',          icon: Mail,           optional: false },
  { id: 'branding',     label: 'Branding',       icon: Palette,        optional: true  },
  { id: 'dates',        label: 'Dates',          icon: CalendarDays,   optional: true  },
  { id: 'fulfillment',  label: 'Fulfillment',    icon: Upload,         optional: true  },
  { id: 'questionnaire',label: 'Questionnaire',  icon: ClipboardCheck, optional: true  },
  { id: 'payments',     label: 'Payments',       icon: CreditCard,     optional: true  },
  { id: 'review',       label: 'Review',         icon: Check,          optional: false },
];

const StepHeader = ({ activeIdx }) => (
  <div className="flex items-center gap-1 overflow-x-auto pb-2 -mx-1 px-1" data-testid="wizard-stepper">
    {STEPS.map((s, idx) => {
      const Icon = s.icon;
      const isActive = idx === activeIdx;
      const isComplete = idx < activeIdx;
      return (
        <div key={s.id} className="flex items-center shrink-0">
          <div
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium whitespace-nowrap',
              isActive && 'bg-blue-600 text-white',
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
      {required && <span className="text-red-500">*</span>}
      {!required && <span className="text-[10px] text-gray-400 font-normal">(optional)</span>}
    </Label>
    {children}
    {hint && <p className="text-[11px] text-gray-500">{hint}</p>}
  </div>
);

const RecommendedFlag = ({ label }) => (
  <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
    <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
    <span>{label}</span>
  </div>
);

export default function StoreSetupWizard({
  storeTypes,
  formData,
  setFormData,
  creatingStore,
  onSubmit,
  onCancel,
  // Optional image upload props from the page
  logoPreview,
  logoFile,
  onLogoSelect,
  onClearLogo,
  bannerPreview,
  bannerFile,
  onBannerSelect,
  onClearBanner,
}) {
  const [stepIdx, setStepIdx] = useState(0);
  const [touched, setTouched] = useState({});
  const currentStep = STEPS[stepIdx];

  // Type aliases — backend already normalises creator/b2b legacy types.
  const isEvent = formData.store_type === 'event';
  const isFundraiser = formData.store_type === 'fundraiser';
  const isCreator = formData.store_type === 'creator';

  // ---------- Validation per step ----------
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

  // Map which errors apply to which step so we can block Next.
  const errorsForStep = (id) => {
    if (id === 'type') return stepErrors.type ? [stepErrors.type] : [];
    if (id === 'basics') return stepErrors.name ? [stepErrors.name] : [];
    if (id === 'owner') {
      return [stepErrors.owner_name, stepErrors.owner_email].filter(Boolean);
    }
    return [];
  };

  const canGoNext = errorsForStep(currentStep.id).length === 0;
  const isLast = stepIdx === STEPS.length - 1;

  const goNext = () => {
    if (!canGoNext) {
      setTouched((t) => ({ ...t, [currentStep.id]: true }));
      return;
    }
    setStepIdx((i) => Math.min(i + 1, STEPS.length - 1));
  };
  const goPrev = () => setStepIdx((i) => Math.max(i - 1, 0));

  // Recommended-but-missing items surfaced on the Review screen.
  const recommendedWarnings = useMemo(() => {
    const warnings = [];
    if (!formData.owner_email) warnings.push('Contact email — needed to send the owner onboarding link.');
    if (!formData.description) warnings.push('Store description — improves storefront SEO and trust.');
    if (!logoFile && !logoPreview) warnings.push('Storefront logo — adds brand recognition.');
    if (isEvent && !formData.event_name) warnings.push('Event name — required for the event store experience.');
    if (isEvent && !formData.event_start_date && !formData.event_end_date) {
      warnings.push('Event date(s) — used in the storefront countdown.');
    }
    if (isEvent && !formData.order_deadline) {
      warnings.push('Order deadline — required to gate late orders.');
    }
    if (isFundraiser && (!formData.fundraiser_goal || Number(formData.fundraiser_goal) <= 0)) {
      warnings.push('Fundraiser goal — needed for the progress bar.');
    }
    if (isFundraiser && !formData.fundraiser_end_date) {
      warnings.push('Fundraiser end date — used in the storefront countdown.');
    }
    return warnings;
  }, [formData, isEvent, isFundraiser, logoFile, logoPreview]);

  const updateLocked = (patch) => setFormData({
    ...formData,
    locked_settings: { ...(formData.locked_settings || {}), ...patch },
  });

  return (
    <div className="space-y-4" data-testid="store-setup-wizard">
      <StepHeader activeIdx={stepIdx} />
      <Separator />

      {/* ---------- STEP CONTENT ---------- */}
      <div className="min-h-[280px]">
        {/* Step 1 — Store Type */}
        {currentStep.id === 'type' && (
          <div className="space-y-3" data-testid="wizard-pane-type">
            <Label className="text-sm">Store Type <span className="text-red-500">*</span></Label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {storeTypes.map((type) => {
                const Icon = type.icon;
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
            <Field label="Store Name" required>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., ABC Company Store"
                data-testid="wizard-name-input"
              />
            </Field>
            <Field label="Description" hint="Shown on the public storefront header.">
              <Textarea
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Store description…"
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

        {/* Step 3 — Owner */}
        {currentStep.id === 'owner' && (
          <div className="space-y-3" data-testid="wizard-pane-owner">
            <Field label="Owner / Organization Name" required>
              <Input
                value={formData.owner_name}
                onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                placeholder="Company or individual name"
                data-testid="wizard-owner-input"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Contact Email" hint="Used to send the owner Stripe + portal onboarding email.">
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
          </div>
        )}

        {/* Step 4 — Branding */}
        {currentStep.id === 'branding' && (
          <div className="space-y-4" data-testid="wizard-pane-branding">
            {/* Logo */}
            <div className="space-y-2">
              <Label className="text-xs">Logo (optional)</Label>
              <div className="flex items-center gap-3">
                {(logoPreview || logoFile) ? (
                  <div className="relative w-16 h-16 rounded border bg-white flex items-center justify-center overflow-hidden">
                    <img src={logoPreview} alt="logo preview" className="max-w-full max-h-full object-contain" />
                    <button
                      type="button"
                      onClick={onClearLogo}
                      className="absolute -top-1 -right-1 bg-white border rounded-full p-0.5 shadow"
                      aria-label="Remove logo"
                    >
                      <X className="h-3 w-3 text-gray-500" />
                    </button>
                  </div>
                ) : (
                  <div className="w-16 h-16 rounded border-2 border-dashed border-gray-200 flex items-center justify-center text-gray-300">
                    <ImageIcon className="h-6 w-6" />
                  </div>
                )}
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={onLogoSelect}
                    data-testid="wizard-logo-input"
                  />
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 border rounded hover:bg-gray-50">
                    <Upload className="h-3.5 w-3.5" /> Upload Logo
                  </span>
                </label>
              </div>
            </div>

            {/* Banner */}
            <div className="space-y-2">
              <Label className="text-xs">Banner (optional)</Label>
              <div className="flex items-center gap-3">
                {(bannerPreview || bannerFile) ? (
                  <div className="relative w-32 h-12 rounded border bg-white overflow-hidden">
                    <img src={bannerPreview} alt="banner preview" className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={onClearBanner}
                      className="absolute -top-1 -right-1 bg-white border rounded-full p-0.5 shadow"
                      aria-label="Remove banner"
                    >
                      <X className="h-3 w-3 text-gray-500" />
                    </button>
                  </div>
                ) : (
                  <div className="w-32 h-12 rounded border-2 border-dashed border-gray-200 flex items-center justify-center text-gray-300">
                    <ImageIcon className="h-5 w-5" />
                  </div>
                )}
                <label className="cursor-pointer">
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={onBannerSelect}
                    data-testid="wizard-banner-input"
                  />
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 border rounded hover:bg-gray-50">
                    <Upload className="h-3.5 w-3.5" /> Upload Banner
                  </span>
                </label>
              </div>
            </div>

            {/* Primary color */}
            <Field label="Accent Color">
              <div className="flex gap-2 items-center">
                <input
                  type="color"
                  value={formData.branding?.primary_color || '#0D9488'}
                  onChange={(e) => setFormData({
                    ...formData,
                    branding: { ...(formData.branding || {}), primary_color: e.target.value },
                  })}
                  className="h-9 w-12 rounded border bg-white cursor-pointer p-0"
                  data-testid="wizard-color-input"
                />
                <Input
                  value={formData.branding?.primary_color || '#0D9488'}
                  onChange={(e) => setFormData({
                    ...formData,
                    branding: { ...(formData.branding || {}), primary_color: e.target.value },
                  })}
                  className="w-28 font-mono text-sm"
                />
              </div>
            </Field>
          </div>
        )}

        {/* Step 5 — Dates / Availability */}
        {currentStep.id === 'dates' && (
          <div className="space-y-3" data-testid="wizard-pane-dates">
            {!isEvent && !isFundraiser && (
              <p className="text-sm text-gray-500">
                This step is only required for Event and Fundraiser stores. You can skip ahead.
              </p>
            )}

            {isEvent && (
              <>
                <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-900">
                  <CalendarDays className="h-4 w-4 text-orange-500" /> Event Details
                </h4>
                <Field label="Event Name" hint="Shown on the storefront hero.">
                  <Input
                    value={formData.event_name}
                    onChange={(e) => setFormData({ ...formData, event_name: e.target.value })}
                    placeholder="e.g., Johnson Benefit Dinner 2026"
                    data-testid="wizard-event-name-input"
                  />
                </Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Event Type">
                    <Select
                      value={formData.event_type || ''}
                      onValueChange={(v) => setFormData({ ...formData, event_type: v })}
                    >
                      <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="one_time">One-time event</SelectItem>
                        <SelectItem value="annual">Annual event</SelectItem>
                        <SelectItem value="seasonal">Seasonal event</SelectItem>
                        <SelectItem value="recurring">Recurring event</SelectItem>
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field label="Event Location">
                    <Input
                      value={formData.event_location}
                      onChange={(e) => setFormData({ ...formData, event_location: e.target.value })}
                      placeholder="Venue or city"
                    />
                  </Field>
                  <Field label="Event Start Date">
                    <Input
                      type="date"
                      value={formData.event_start_date}
                      onChange={(e) => setFormData({ ...formData, event_start_date: e.target.value })}
                      data-testid="wizard-event-start-date"
                    />
                  </Field>
                  <Field label="Event End Date">
                    <Input
                      type="date"
                      value={formData.event_end_date}
                      onChange={(e) => setFormData({ ...formData, event_end_date: e.target.value })}
                    />
                  </Field>
                  <Field label="Order Deadline" hint="Stops accepting orders after this date if auto-close is on.">
                    <Input
                      type="date"
                      value={formData.order_deadline}
                      onChange={(e) => setFormData({ ...formData, order_deadline: e.target.value })}
                      data-testid="wizard-order-deadline"
                    />
                  </Field>
                </div>
              </>
            )}

            {isFundraiser && (
              <>
                <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-900">
                  <Heart className="h-4 w-4 text-pink-500" /> Fundraiser Dates
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Start Date">
                    <Input
                      type="date"
                      value={formData.fundraiser_start_date}
                      onChange={(e) => setFormData({ ...formData, fundraiser_start_date: e.target.value })}
                    />
                  </Field>
                  <Field label="End Date">
                    <Input
                      type="date"
                      value={formData.fundraiser_end_date}
                      onChange={(e) => setFormData({ ...formData, fundraiser_end_date: e.target.value })}
                    />
                  </Field>
                </div>
              </>
            )}
          </div>
        )}

        {/* Step 6 — Fulfillment */}
        {currentStep.id === 'fulfillment' && (
          <div className="space-y-4" data-testid="wizard-pane-fulfillment">
            {isEvent && (
              <div className="space-y-3">
                <Field label="Pickup / Delivery Date">
                  <Input
                    type="date"
                    value={formData.pickup_delivery_date}
                    onChange={(e) => setFormData({ ...formData, pickup_delivery_date: e.target.value })}
                  />
                </Field>
                <Field label="Pickup / Delivery Instructions">
                  <Textarea
                    rows={2}
                    value={formData.pickup_delivery_instructions}
                    onChange={(e) => setFormData({ ...formData, pickup_delivery_instructions: e.target.value })}
                    placeholder="e.g., Items available at the venue check-in table"
                  />
                </Field>
                <div className="flex items-center justify-between bg-gray-50 border rounded p-2">
                  <div>
                    <Label className="text-xs">Auto-close after deadline</Label>
                    <p className="text-[11px] text-gray-500">Stop accepting orders after the order deadline.</p>
                  </div>
                  <Switch
                    checked={formData.auto_close_after_deadline}
                    onCheckedChange={(v) => setFormData({ ...formData, auto_close_after_deadline: v })}
                    data-testid="wizard-auto-close-switch"
                  />
                </div>
                <div className="flex items-center justify-between bg-gray-50 border rounded p-2">
                  <div>
                    <Label className="text-xs">Allow late orders</Label>
                    <p className="text-[11px] text-gray-500">Customers can still order after the deadline with a notice.</p>
                  </div>
                  <Switch
                    checked={formData.allow_late_orders}
                    onCheckedChange={(v) => setFormData({ ...formData, allow_late_orders: v })}
                  />
                </div>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Label className="text-sm font-semibold">Shipping &amp; Handling Fee</Label>
                <Badge variant="outline" className="text-[10px] bg-amber-50 text-amber-700 border-amber-200">Store-Level</Badge>
              </div>
              <p className="text-[11px] text-gray-500">
                Flat per-order fee at checkout. Per-product costs (base / production / retail) are configured later, when products are added.
              </p>
              <div className="flex items-center justify-between bg-gray-50 border rounded p-2">
                <div>
                  <Label className="text-xs">Bundle individual fees into one</Label>
                  <p className="text-[11px] text-gray-500">Replace separate fees with a single bundled rate.</p>
                </div>
                <Switch
                  checked={!!formData.locked_settings?.shipping_handling_enabled}
                  onCheckedChange={(v) => updateLocked({ shipping_handling_enabled: v })}
                  data-testid="wizard-sh-enabled-switch"
                />
              </div>
              {formData.locked_settings?.shipping_handling_enabled && (
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Bundle Fee ($)">
                    <Input
                      type="number" min="0" step="0.01"
                      value={formData.locked_settings.shipping_handling_fee}
                      onChange={(e) => updateLocked({ shipping_handling_fee: e.target.value })}
                      data-testid="wizard-sh-fee-input"
                    />
                  </Field>
                  <Field label="Label (shown to customer)">
                    <Input
                      value={formData.locked_settings.shipping_handling_label}
                      onChange={(e) => updateLocked({ shipping_handling_label: e.target.value })}
                      placeholder="e.g., Shipping & Handling"
                    />
                  </Field>
                  <div className="col-span-2">
                    <Field label="Description">
                      <Input
                        value={formData.locked_settings.shipping_handling_description}
                        onChange={(e) => updateLocked({ shipping_handling_description: e.target.value })}
                        placeholder="Shown at checkout"
                      />
                    </Field>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 7 — Questionnaire handoff note */}
        {currentStep.id === 'questionnaire' && (
          <div className="space-y-3" data-testid="wizard-pane-questionnaire">
            {isEvent ? (
              <div className="rounded-md border border-orange-200 bg-orange-50 p-3 text-sm text-orange-900 space-y-2">
                <p className="font-medium flex items-center gap-2">
                  <ClipboardCheck className="h-4 w-4" /> Event Store Setup Questionnaire
                </p>
                <p className="text-xs">
                  After this store is created you'll be able to send the owner the official
                  Event Store setup questionnaire (event details, fulfillment preferences,
                  fundraiser flags, Stripe Connect setup). Tenant-controlled financial values
                  are sent as read-only and cannot be overwritten by the owner.
                </p>
                <p className="text-xs italic">No action needed in this step — just continue.</p>
              </div>
            ) : (
              <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                <p>Questionnaire handoff applies to Event stores only. You can skip this step.</p>
              </div>
            )}
          </div>
        )}

        {/* Step 8 — Payments / Stripe / Fundraiser / Creator settings */}
        {currentStep.id === 'payments' && (
          <div className="space-y-4" data-testid="wizard-pane-payments">
            {isFundraiser && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <Heart className="h-4 w-4 text-pink-500" /> Fundraiser Profit Share
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Goal Amount ($)">
                    <Input
                      type="number" min="0"
                      value={formData.fundraiser_goal}
                      onChange={(e) => setFormData({ ...formData, fundraiser_goal: parseFloat(e.target.value) || 0 })}
                      data-testid="wizard-fundraiser-goal"
                    />
                  </Field>
                  <Field label="Fundraiser Profit Share (%)" hint="Portion of profit that goes to the fundraiser; the shop keeps the rest.">
                    <Input
                      type="number" min="0" max="100"
                      value={formData.fundraiser_profit_percent}
                      onChange={(e) => setFormData({ ...formData, fundraiser_profit_percent: parseFloat(e.target.value) || 0 })}
                    />
                  </Field>
                </div>
              </div>
            )}

            {isCreator && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold">Creator Commission</h4>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Commission Type">
                    <Select
                      value={formData.creator_commission_type}
                      onValueChange={(v) => setFormData({ ...formData, creator_commission_type: v })}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">Percentage of Profit</SelectItem>
                        <SelectItem value="fixed">Fixed Amount per Item</SelectItem>
                      </SelectContent>
                    </Select>
                  </Field>
                  <Field label={formData.creator_commission_type === 'percentage' ? 'Commission %' : 'Amount per Item ($)'}>
                    <Input
                      type="number" min="0"
                      value={formData.creator_commission_value}
                      onChange={(e) => setFormData({ ...formData, creator_commission_value: parseFloat(e.target.value) || 0 })}
                    />
                  </Field>
                </div>
              </div>
            )}

            <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900 space-y-1">
              <p className="font-medium flex items-center gap-2">
                <CreditCard className="h-4 w-4" /> Stripe Connect
              </p>
              <p className="text-xs">
                Once the store is created, send the owner an onboarding link from the store's
                Stripe Connection card to let them collect payouts. The store can stay in
                "pending" status until Stripe is fully connected.
              </p>
            </div>
          </div>
        )}

        {/* Step 9 — Review & Create */}
        {currentStep.id === 'review' && (
          <div className="space-y-3" data-testid="wizard-pane-review">
            <div className="rounded-md border bg-white p-3 text-sm space-y-1.5" data-testid="wizard-review-summary">
              <div className="flex justify-between"><span className="text-gray-500">Store Type</span><span className="font-medium">{formData.store_type || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Name</span><span className="font-medium">{formData.name || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Owner</span><span className="font-medium">{formData.owner_name || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Email</span><span className="font-medium">{formData.owner_email || '—'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Public</span><span className="font-medium">{formData.is_public ? 'Yes' : 'No'}</span></div>
              {isEvent && (
                <>
                  <div className="flex justify-between"><span className="text-gray-500">Event Name</span><span className="font-medium">{formData.event_name || '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Event Dates</span><span className="font-medium">{[formData.event_start_date, formData.event_end_date].filter(Boolean).join(' → ') || '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Order Deadline</span><span className="font-medium">{formData.order_deadline || '—'}</span></div>
                </>
              )}
              {isFundraiser && (
                <>
                  <div className="flex justify-between"><span className="text-gray-500">Fundraiser Goal</span><span className="font-medium">{formData.fundraiser_goal ? `$${formData.fundraiser_goal}` : '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Profit Share</span><span className="font-medium">{formData.fundraiser_profit_percent}%</span></div>
                </>
              )}
              {formData.locked_settings?.shipping_handling_enabled && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Shipping &amp; Handling</span>
                  <span className="font-medium">
                    ${Number(formData.locked_settings.shipping_handling_fee || 0).toFixed(2)} bundled
                  </span>
                </div>
              )}
            </div>

            {recommendedWarnings.length > 0 && (
              <div className="space-y-1.5" data-testid="wizard-recommended-warnings">
                <p className="text-xs font-medium text-amber-700">Recommended (you can still create the store):</p>
                {recommendedWarnings.map((w, i) => <RecommendedFlag key={i} label={w} />)}
              </div>
            )}
          </div>
        )}
      </div>

      <Separator />

      {/* ---------- Footer ---------- */}
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
            <Button
              type="button"
              onClick={goNext}
              disabled={creatingStore}
              data-testid="wizard-next-btn"
            >
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button
              type="button"
              onClick={onSubmit}
              disabled={creatingStore || Object.keys(stepErrors).some((k) => ['type', 'name', 'owner_name'].includes(k))}
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
