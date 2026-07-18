/**
 * WebstoreSetupFlow — consolidated 11-step pre-launch setup tab.
 *
 * Steps: Store Created → Send Questionnaire → Questionnaire Submitted →
 * Staff Review → Branding → Products & Pricing → Fulfillment →
 * Stripe Onboarding → Store Preview → Owner Approval → Open Store
 *
 * This is the single source of truth for store setup. All other tabs
 * (Products, Branding, Payments) are secondary destinations.
 */
import { useState } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Separator } from './ui/separator';
import {
  CheckCircle2, Circle, Clock, AlertCircle, Lock,
  Mail, Eye, Package, Palette, Truck, CreditCard,
  Zap, ExternalLink, Loader2, Copy, Check,
  ChevronRight, ClipboardCheck, ShieldCheck, ArrowRight, Sparkles,
  Store, Paperclip, Download, FileText, FileImage, File,
  ChevronDown, ChevronUp,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../lib/utils';
import { toast } from 'sonner';
import WebstoreOwnerConnectCard from './WebstoreOwnerConnectCard';

// ── Status config ─────────────────────────────────────────────────────────────
const S = {
  complete:       { Icon: CheckCircle2, ring: 'bg-emerald-50',  ic: 'text-emerald-500', badge: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Complete'           },
  needs_action:   { Icon: AlertCircle,  ring: 'bg-amber-50',    ic: 'text-amber-500',   badge: 'bg-amber-100 text-amber-700 border-amber-200',   label: 'Action Needed'      },
  pending_review: { Icon: ClipboardCheck, ring: 'bg-blue-50',   ic: 'text-blue-500',    badge: 'bg-blue-100 text-blue-700 border-blue-200',    label: 'Ready for Review'   },
  waiting:        { Icon: Clock,        ring: 'bg-gray-50',     ic: 'text-gray-400',    badge: 'bg-gray-100 text-gray-500 border-gray-200',    label: 'Waiting on Owner'   },
  not_started:    { Icon: Circle,       ring: 'bg-muted',       ic: 'text-gray-300',    badge: 'bg-gray-50  text-gray-400 border-gray-200',    label: 'Not Started'        },
  blocked:        { Icon: Lock,         ring: 'bg-muted',       ic: 'text-gray-300',    badge: 'bg-gray-50  text-gray-400 border-gray-200',    label: 'Blocked'            },
};

const qLabel = (t) => ({
  event:      'Event Store Setup Questionnaire',
  fundraiser: 'Fundraiser Store Setup Questionnaire',
  creator:    'Team / School Store Setup Questionnaire',
  business:   'Business Store Setup Questionnaire',
}[t] || 'Store Setup Questionnaire');

const qPhase = (qs) => {
  if (!qs?.linked) return 'not_sent';
  const resp = qs.latest_response;
  if (resp?.applied_to_webstore) return 'applied';
  if (resp?.submitted_at)         return 'awaiting_review';
  if (qs.questionnaire?.last_sent_at) return 'sent';
  return 'draft';
};

const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString() : null;

// ── Step row ──────────────────────────────────────────────────────────────────
function StepRow({ step, stepNum, isLast, children }) {
  const cfg = S[step.status] || S.not_started;
  const { Icon } = cfg;
  const isDone = step.status === 'complete';
  return (
    <div className="relative flex gap-3" data-testid={`setup-step-${step.id}`}>
      {!isLast && (
        <div className="absolute left-[15px] top-[34px] bottom-0 w-px bg-border z-0" />
      )}
      <div className={cn('mt-1 shrink-0 h-8 w-8 rounded-full flex items-center justify-center z-10 text-[11px] font-semibold', cfg.ring)}>
        {isDone ? <Icon className={cn('h-4 w-4', cfg.ic)} /> : <span className={cfg.ic}>{stepNum}</span>}
      </div>
      <div className="flex-1 min-w-0 pb-5">
        <div className="flex flex-wrap items-center gap-2 mb-0.5">
          <span className={cn('text-sm font-semibold', isDone ? 'text-muted-foreground' : 'text-foreground')}>
            {step.title}
          </span>
          <Badge className={cn('text-[10px] border shrink-0 px-1.5 py-0', cfg.badge)}>
            {cfg.label}
          </Badge>
          {step.required && !isDone && (
            <Badge variant="outline" className="text-[10px] border-red-200 text-red-500 shrink-0 px-1.5 py-0">Required</Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">{step.description}</p>
        {children && <div className="mt-3 space-y-3">{children}</div>}
      </div>
    </div>
  );
}

// ── Staff Review Panel ────────────────────────────────────────────────────────
function StaffReviewPanel({ webstoreId, questionnaireStatus, onApplyAnswers, applyingAnswers }) {
  const { getWebstoreQuestionnaireReviewDetails } = useApp();
  const [details, setDetails]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [safeOpen, setSafeOpen] = useState(true);
  const [allOpen,  setAllOpen]  = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await getWebstoreQuestionnaireReviewDetails(webstoreId);
      setDetails(d);
    } catch {
      setError('Could not load review details.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground p-2 bg-muted/40 rounded-md" data-testid="staff-review-panel-loading">
      <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading review details…
    </div>
  );

  if (!details) return (
    <div className="flex gap-2 flex-wrap" data-testid="staff-review-panel-trigger">
      <Button size="sm" variant="outline" onClick={load} data-testid="review-panel-view-btn">
        <Eye className="h-3.5 w-3.5 mr-1" /> View Answers & Summary
      </Button>
      <Button
        size="sm"
        onClick={onApplyAnswers}
        disabled={applyingAnswers}
        className="bg-blue-600 hover:bg-blue-700 text-white"
        data-testid="review-panel-apply-btn"
      >
        {applyingAnswers ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5 mr-1" />}
        Apply Safe Answers
      </Button>
    </div>
  );

  if (error) return (
    <div className="text-xs text-destructive p-2 bg-destructive/10 rounded-md" data-testid="staff-review-panel-error">
      {error} <button className="underline ml-1" onClick={load}>Retry</button>
    </div>
  );

  // Backend now returns arrays, not dicts
  const safeList  = Array.isArray(details.safe_fields)          ? details.safe_fields          : [];
  const allList   = Array.isArray(details.all_answers)          ? details.all_answers          : [];
  const aiSummary = details.response?.ai_summary || null;
  const submitter = details.response?.customer_name || details.response?.customer_email || '';

  return (
    <div className="space-y-2 text-xs" data-testid="staff-review-panel">

      {/* ── AI Summary ─────────────────────────────────────────────────── */}
      {aiSummary && (
        <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2.5" data-testid="ai-summary-box">
          <p className="text-[10px] font-semibold text-blue-600 uppercase tracking-wide mb-1 flex items-center gap-1">
            <Sparkles className="h-3 w-3" /> AI Summary
          </p>
          <p className="text-xs text-blue-900 leading-relaxed">{aiSummary}</p>
          {submitter && <p className="text-[10px] text-blue-500 mt-1">Submitted by: {submitter}</p>}
        </div>
      )}
      {!aiSummary && details.response?.submitted_at && (
        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500 text-[10px]">
          AI summary generating… refresh in a moment.
        </div>
      )}

      {/* ── Safe to Apply ──────────────────────────────────────────────── */}
      <div className="border rounded-md overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-medium transition-colors"
          onClick={() => setSafeOpen(!safeOpen)}
          data-testid="review-safe-toggle"
        >
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Safe to apply ({safeList.length} field{safeList.length !== 1 ? 's' : ''})
          </span>
          <ChevronRight className={cn('h-3.5 w-3.5 transition-transform', safeOpen && 'rotate-90')} />
        </button>
        {safeOpen && safeList.length > 0 && (
          <div className="divide-y" data-testid="review-safe-fields">
            {safeList.map((item, i) => (
              <div key={i} className="flex items-start gap-2 px-3 py-1.5">
                <span className="text-muted-foreground w-44 shrink-0 leading-tight">{item.label}</span>
                <span className="font-medium text-foreground break-words">{String(item.value ?? '—')}</span>
              </div>
            ))}
          </div>
        )}
        {safeOpen && safeList.length === 0 && (
          <p className="px-3 py-2 text-muted-foreground italic">No safe fields mapped.</p>
        )}
      </div>

      {/* ── All Answers ─────────────────────────────────────────────────── */}
      <div className="border rounded-md overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium transition-colors"
          onClick={() => setAllOpen(!allOpen)}
          data-testid="review-all-toggle"
        >
          <span>All submitted answers ({allList.length})</span>
          <ChevronRight className={cn('h-3.5 w-3.5 transition-transform', allOpen && 'rotate-90')} />
        </button>
        {allOpen && allList.length > 0 && (
          <div className="divide-y max-h-96 overflow-y-auto" data-testid="review-all-answers">
            {allList.map((item, i) => (
              <div key={i} className="flex items-start gap-2 px-3 py-1.5">
                <span className="text-muted-foreground w-44 shrink-0 leading-tight">{item.label}</span>
                <span className="text-foreground break-words leading-tight">{String(item.answer ?? '—')}</span>
              </div>
            ))}
          </div>
        )}
        {allOpen && allList.length === 0 && (
          <p className="px-3 py-2 text-muted-foreground italic">No answers recorded.</p>
        )}
      </div>

      <div className="flex gap-2 pt-1">
        <Button
          size="sm"
          onClick={onApplyAnswers}
          disabled={applyingAnswers}
          className="bg-blue-600 hover:bg-blue-700 text-white"
          data-testid="review-panel-apply-btn"
        >
          {applyingAnswers ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5 mr-1" />}
          Apply Safe Answers to Store
        </Button>
      </div>
    </div>
  );
}

// ── Customer Uploads Panel ────────────────────────────────────────────────────
function CustomerUploadsPanel({ questionnaireId }) {
  const { getQuestionnaireUploads } = useApp();
  const [uploads, setUploads]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);
  const [open, setOpen]         = useState(false);

  const load = async () => {
    if (!questionnaireId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getQuestionnaireUploads(questionnaireId);
      setUploads(data.uploads || []);
      setOpen(true);
    } catch {
      setError('Could not load uploads.');
    } finally {
      setLoading(false);
    }
  };

  const toggle = () => {
    if (!open && uploads === null) { load(); return; }
    setOpen((v) => !v);
  };

  const fmtSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const FileIcon = (contentType = '') => {
    if (contentType.startsWith('image/')) return <FileImage className="h-4 w-4 text-blue-500 shrink-0" />;
    if (contentType === 'application/pdf') return <FileText className="h-4 w-4 text-red-500 shrink-0" />;
    return <File className="h-4 w-4 text-gray-400 shrink-0" />;
  };

  const count = uploads?.length ?? null;

  return (
    <div className="border rounded-md overflow-hidden text-xs" data-testid="customer-uploads-panel">
      <button
        className="w-full flex items-center justify-between px-3 py-2 bg-muted/40 hover:bg-muted/60 transition-colors"
        onClick={toggle}
        data-testid="customer-uploads-toggle"
      >
        <span className="flex items-center gap-1.5 font-medium text-foreground">
          <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
          Customer Uploaded Files
          {count !== null && (
            <span className="ml-1 bg-primary/10 text-primary rounded-full px-1.5 py-0 font-semibold">
              {count}
            </span>
          )}
        </span>
        {loading
          ? <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
          : open ? <ChevronUp className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        }
      </button>

      {open && (
        <div className="px-3 py-2 space-y-1.5 bg-background">
          {error && (
            <p className="text-destructive text-xs">{error} <button className="underline ml-1" onClick={load}>Retry</button></p>
          )}
          {!error && uploads?.length === 0 && (
            <p className="text-muted-foreground italic">No files uploaded by the customer.</p>
          )}
          {!error && uploads?.map((u) => (
            <div key={u.id} className="flex items-center gap-2 py-1 border-b last:border-0" data-testid={`upload-row-${u.id}`}>
              {FileIcon(u.content_type)}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate text-foreground">{u.original_filename}</p>
                <p className="text-muted-foreground">
                  {fmtSize(u.size_bytes)}
                  {u.uploaded_at && <> · {new Date(u.uploaded_at).toLocaleDateString()}</>}
                  {!u.file_exists && <span className="ml-1 text-amber-600 font-medium">(expired — re-upload needed)</span>}
                </p>
              </div>
              <a
                href={u.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded border text-xs font-medium transition-colors shrink-0',
                  u.file_exists
                    ? 'border-border hover:bg-muted text-foreground'
                    : 'border-amber-200 text-amber-600 cursor-not-allowed pointer-events-none opacity-60'
                )}
                data-testid={`upload-download-${u.id}`}
                title={u.file_exists ? `Download ${u.original_filename}` : 'File no longer on server'}
              >
                <Download className="h-3 w-3" /> Download
              </a>
            </div>
          ))}
          {!error && uploads?.length > 0 && (
            <p className="text-[10px] text-muted-foreground pt-1">
              Files are stored temporarily on the server. Download promptly or ask the customer to re-upload if needed.
            </p>
          )}
        </div>
      )}
    </div>
  );
}


// ── Launch gate ───────────────────────────────────────────────────────────────
function launchReady({ store, storeProducts }) {
  const hasProducts  = (storeProducts || []).length > 0;
  const qSubmitted   = !!store?.questionnaire_submitted_at;
  const qReviewed    = !!store?.questionnaire_reviewed;
  const missing = [];
  if (!hasProducts) missing.push('At least one product must be assigned');
  if (qSubmitted && !qReviewed) missing.push('Questionnaire review must be completed');
  return { ok: missing.length === 0, missing };
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function WebstoreSetupFlow({
  store,
  questionnaireStatus,
  loadingQuestionnaire,
  storeProducts,
  applyingAnswers,
  onApplyAnswers,
  onSendQuestionnaire,     // async (storeId, email) => result
  onShowTab,               // (tab) => void
  onUpdateStore,           // async (payload) => void
  onActivateStore,         // async () => void
  onStampProgress,         // async (flagKey) => void — calls PATCH admin-progress
}) {
  // Questionnaire inline send
  const [sendingQ,       setSendingQ]       = useState(false);
  const [qEmailSent,     setQEmailSent]     = useState(false);
  const [qEmailFail,     setQEmailFail]     = useState(false);
  const [qFallbackLink,  setQFallbackLink]  = useState(null);
  const [qEmail,         setQEmail]         = useState(store?.owner_email || '');
  const [copiedLink,     setCopiedLink]     = useState(false);
  const [showResendInput, setShowResendInput] = useState(false);

  // Activate & stamp state
  const [activating,   setActivating]   = useState(false);
  const [stampingKey,  setStampingKey]  = useState(null);

  const phase      = qPhase(questionnaireStatus);
  const hasProducts = (storeProducts || []).length > 0;
  const hasBranding = !!(store.branding?.logo_url || store.logo_url || store.branding?.banner_url || store.banner_url);
  const hasFulfillment = !!(store.pickup_delivery_instructions || store.pickup_delivery_date || store.order_deadline);
  const { ok: canLaunch, missing } = launchReady({ store, storeProducts });
  const isLive = store.status === 'active';

  const handleSendQ = async () => {
    if (!qEmail.trim()) { toast.error('Enter an email address'); return; }
    setSendingQ(true);
    setQEmailFail(false);
    try {
      const result = await onSendQuestionnaire(store.id, qEmail.trim());
      if (result?.email_sent || result?.success) {
        setQEmailSent(true);
        setShowResendInput(false);
      } else {
        setQEmailFail(true);
        setQFallbackLink(result?.link || result?.invite_url || null);
      }
    } catch {
      setQEmailFail(true);
    } finally {
      setSendingQ(false);
    }
  };

  const copyFallback = () => {
    if (!qFallbackLink) return;
    navigator.clipboard.writeText(qFallbackLink).then(() => {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    });
  };

  const handleActivate = async () => {
    setActivating(true);
    try { await onActivateStore(); }
    finally { setActivating(false); }
  };

  const handleStamp = async (flagKey) => {
    if (stampingKey || !onStampProgress) return;
    setStampingKey(flagKey);
    try { await onStampProgress(flagKey); }
    finally { setStampingKey(null); }
  };

  // ── Per-step status derivation ─────────────────────────────────────────────
  const sendQStatus =
    phase === 'not_sent'               ? 'needs_action' :
    (phase === 'sent' || phase === 'draft') ? 'waiting' :
    'complete';

  const submittedStatus =
    (phase === 'not_sent' || phase === 'draft') ? 'not_started' :
    phase === 'sent'            ? 'waiting' :
    'complete';  // awaiting_review or applied

  const reviewStatus =
    phase === 'awaiting_review' ? 'pending_review' :
    phase === 'applied'         ? 'complete' :
    'not_started';

  const previewStatus =
    store?.preview_ready_at || isLive ? 'complete' : 'needs_action';

  const ownerApprovalStatus =
    store?.owner_approved_at || isLive ? 'complete' :
    store?.preview_ready_at            ? 'needs_action' :
    'not_started';

  // ── Step definitions ────────────────────────────────────────────────────────
  const steps = [
    {
      id: 'record',
      title: 'Store Created',
      status: 'complete',
      required: true,
      description: `${store.name} · ${store.store_type} · Created`,
    },
    {
      id: 'send_questionnaire',
      title: 'Send Setup Questionnaire',
      status: loadingQuestionnaire ? 'not_started' : sendQStatus,
      required: false,
      description:
        phase === 'not_sent'  ? `Send the ${qLabel(store.store_type)} to collect event details, fulfillment, and preferences.` :
        (phase === 'sent' || phase === 'draft') ? 'Questionnaire sent — waiting for owner to complete it.' :
        'Questionnaire sent and owner has answered.',
    },
    {
      id: 'questionnaire_submitted',
      title: 'Questionnaire Submitted',
      status: loadingQuestionnaire ? 'not_started' : submittedStatus,
      required: false,
      description:
        phase === 'sent'           ? 'Questionnaire sent. Waiting for owner to fill it out and submit.' :
        phase === 'awaiting_review'? `Owner submitted answers on ${fmtDate(questionnaireStatus?.latest_response?.submitted_at) || 'recent date'}.` :
        phase === 'applied'        ? 'Owner submitted answers — reviewed and applied.' :
        'Will update when the owner submits the questionnaire.',
    },
    {
      id: 'staff_review',
      title: 'Staff Review Answers',
      status: loadingQuestionnaire ? 'not_started' : reviewStatus,
      required: false,
      description:
        phase === 'awaiting_review' ? 'Owner has submitted. Review the mapped fields and apply safe answers.' :
        phase === 'applied'         ? 'Answers have been reviewed and applied to this store.' :
        'Waiting for the owner to submit the questionnaire.',
    },
    {
      id: 'branding',
      title: 'Branding / Artwork',
      status: hasBranding ? 'complete' : 'not_started',
      required: false,
      description: hasBranding ? 'Logo or banner is set.' : 'Upload a logo, banner, and set a primary color.',
    },
    {
      id: 'products',
      title: 'Products & Pricing',
      status: hasProducts ? 'complete' : 'needs_action',
      required: true,
      description: hasProducts
        ? `${storeProducts.length} product${storeProducts.length !== 1 ? 's' : ''} assigned.`
        : 'Assign at least one product from your catalog and set pricing.',
    },
    {
      id: 'fulfillment',
      title: 'Fulfillment / Shipping / Pickup',
      status: hasFulfillment ? 'complete' : 'not_started',
      required: false,
      description: hasFulfillment
        ? (store.pickup_delivery_instructions || `Pickup date: ${store.pickup_delivery_date}`)
        : 'Set pickup instructions, delivery dates, and any shipping fees.',
    },
    {
      id: 'stripe',
      title: 'Owner Stripe Onboarding',
      status: 'not_started',  // driven by WebstoreOwnerConnectCard internal state
      required: false,
      description: 'Send the store owner a Stripe Connect invite so they can receive payouts.',
    },
    {
      id: 'preview',
      title: 'Store Preview',
      status: previewStatus,
      required: false,
      description: store?.preview_ready_at
        ? `Preview reviewed on ${fmtDate(store.preview_ready_at)}.`
        : 'Preview the storefront before sharing it with the owner.',
    },
    {
      id: 'owner_approval',
      title: 'Owner Approval',
      status: ownerApprovalStatus,
      required: false,
      description: store?.owner_approved_at
        ? `Owner approved on ${fmtDate(store.owner_approved_at)}.`
        : isLive
          ? 'Store is live.'
          : 'Mark that the store owner has reviewed and approved the preview.',
    },
    {
      id: 'launch',
      title: 'Open Store',
      status: isLive ? 'complete' : canLaunch ? 'needs_action' : 'blocked',
      required: true,
      description: isLive
        ? 'Store is live and accepting orders.'
        : canLaunch
          ? 'All required steps complete. Activate the store to go live.'
          : `Required before launch: ${missing.join('; ')}.`,
    },
  ];

  const lastIdx = steps.length - 1;

  return (
    <div className="space-y-1" data-testid="store-setup-flow">
      {/* Header */}
      <div className="flex items-center justify-between pb-2">
        <div>
          <h3 className="text-sm font-semibold">Store Setup</h3>
          <p className="text-xs text-muted-foreground">Complete the steps below to launch this store.</p>
        </div>
        {isLive && (
          <Badge className="bg-emerald-100 text-emerald-700 border border-emerald-200 text-xs">Live</Badge>
        )}
      </div>
      <Separator />

      <div className="pt-3 space-y-0">
        {steps.map((step, idx) => (
          <StepRow key={step.id} step={step} stepNum={idx + 1} isLast={idx === lastIdx}>

            {/* ── Step 2: Send Questionnaire ── */}
            {step.id === 'send_questionnaire' && !loadingQuestionnaire && (
              <>
                {(phase === 'not_sent' || phase === 'draft' || showResendInput) && (
                  qEmailSent ? (
                    <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 rounded p-2">
                      <Check className="h-3.5 w-3.5 shrink-0" />
                      Questionnaire sent to {qEmail}.
                      {qFallbackLink && (
                        <button className="ml-auto underline text-muted-foreground" onClick={copyFallback}>
                          {copiedLink ? 'Copied!' : 'Copy link'}
                        </button>
                      )}
                    </div>
                  ) : qEmailFail ? (
                    <div className="space-y-2">
                      <div className="text-xs text-amber-700 bg-amber-50 rounded p-2">
                        Email delivery failed.
                        {qFallbackLink && (
                          <div className="mt-1 flex items-center gap-2">
                            <span className="font-mono text-[10px] bg-white border rounded px-1 flex-1 truncate">{qFallbackLink}</span>
                            <Button size="sm" variant="outline" className="h-6 text-xs px-2" onClick={copyFallback}>
                              {copiedLink ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-2 items-center">
                      <Input
                        type="email"
                        value={qEmail}
                        onChange={(e) => setQEmail(e.target.value)}
                        placeholder={store?.owner_email || 'Owner email address'}
                        className="h-8 text-xs flex-1 max-w-xs"
                        data-testid="setup-q-email-input"
                      />
                      <Button
                        size="sm"
                        onClick={handleSendQ}
                        disabled={sendingQ}
                        className="bg-blue-600 hover:bg-blue-700 text-white shrink-0"
                        data-testid="setup-send-q-btn"
                      >
                        {sendingQ ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <Mail className="h-3.5 w-3.5 mr-1" />}
                        {showResendInput ? 'Resend' : 'Send'}
                      </Button>
                      {showResendInput && (
                        <button
                          className="text-xs text-muted-foreground underline shrink-0"
                          onClick={() => setShowResendInput(false)}
                          data-testid="setup-cancel-resend-btn"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  )
                )}
                {(phase === 'sent' || phase === 'awaiting_review' || phase === 'applied') && !showResendInput && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setQEmailSent(false);
                        setQEmailFail(false);
                        setQEmail(store?.owner_email || '');
                        setShowResendInput(true);
                      }}
                      data-testid="setup-resend-q-btn"
                    >
                      <Mail className="h-3.5 w-3.5 mr-1" /> Resend
                    </Button>
                    {questionnaireStatus?.questionnaire?.id && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(`/questionnaire/${questionnaireStatus.questionnaire.id}`, '_blank')}
                        data-testid="setup-view-q-btn"
                      >
                        <ExternalLink className="h-3.5 w-3.5 mr-1" /> View Form
                      </Button>
                    )}
                  </div>
                )}
              </>
            )}

            {/* ── Step 4: Staff Review ── */}
            {step.id === 'staff_review' && !loadingQuestionnaire && phase === 'awaiting_review' && (
              <StaffReviewPanel
                webstoreId={store.id}
                questionnaireStatus={questionnaireStatus}
                onApplyAnswers={onApplyAnswers}
                applyingAnswers={applyingAnswers}
              />
            )}

            {/* Customer Uploads — shown on staff review step when questionnaire is submitted or applied */}
            {step.id === 'staff_review' && !loadingQuestionnaire &&
              (phase === 'awaiting_review' || phase === 'applied') &&
              questionnaireStatus?.questionnaire?.id && (
              <CustomerUploadsPanel questionnaireId={questionnaireStatus.questionnaire.id} />
            )}

            {/* ── Step 5: Branding ── */}
            {step.id === 'branding' && !hasBranding && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onShowTab?.('branding')}
                data-testid="setup-goto-branding-btn"
              >
                <Palette className="h-3.5 w-3.5 mr-1" /> Upload in Branding tab
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            )}

            {/* ── Step 6: Products ── */}
            {step.id === 'products' && !hasProducts && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onShowTab?.('products')}
                data-testid="setup-goto-products-btn"
              >
                <Package className="h-3.5 w-3.5 mr-1" /> Assign in Products tab
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            )}

            {/* ── Step 7: Fulfillment ── */}
            {step.id === 'fulfillment' && !hasFulfillment && (
              <div className="text-xs text-muted-foreground bg-muted/40 rounded p-2 flex items-center gap-2">
                <Truck className="h-3.5 w-3.5 shrink-0" />
                Set pickup / delivery details in the <strong>Store Configuration</strong> section below.
              </div>
            )}

            {/* ── Step 8: Stripe ── */}
            {step.id === 'stripe' && (
              <div className="space-y-2">
                <WebstoreOwnerConnectCard webstore={store} />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onShowTab?.('payments')}
                  className="text-xs"
                  data-testid="setup-goto-payments-btn"
                >
                  <CreditCard className="h-3.5 w-3.5 mr-1" /> Full payout details in Payments tab
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            )}

            {/* ── Step 9: Store Preview ── */}
            {step.id === 'preview' && (
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => window.open(`${window.location.origin}/store/${store.id}?admin_preview=1`, '_blank')}
                  data-testid="setup-admin-preview-btn"
                >
                  <Eye className="h-3.5 w-3.5 mr-1" /> Admin Preview
                  <ExternalLink className="h-3 w-3 ml-1" />
                </Button>
                {!store?.preview_ready_at && !isLive && onStampProgress && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStamp('mark_preview_ready')}
                    disabled={!!stampingKey}
                    data-testid="setup-mark-preview-ready-btn"
                  >
                    {stampingKey === 'mark_preview_ready' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5 mr-1" />}
                    Mark Preview Ready
                  </Button>
                )}
              </div>
            )}

            {/* ── Step 10: Owner Approval ── */}
            {step.id === 'owner_approval' && !store?.owner_approved_at && !isLive && (
              <div className="flex flex-wrap gap-2">
                {store?.preview_ready_at && onStampProgress && (
                  <Button
                    size="sm"
                    onClick={() => handleStamp('mark_owner_approved')}
                    disabled={!!stampingKey}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    data-testid="setup-mark-owner-approved-btn"
                  >
                    {stampingKey === 'mark_owner_approved' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5 mr-1" />}
                    Mark Owner Approved
                  </Button>
                )}
                {!store?.preview_ready_at && (
                  <p className="text-xs text-muted-foreground">Complete the Store Preview step first.</p>
                )}
              </div>
            )}

            {/* ── Step 11: Launch ── */}
            {step.id === 'launch' && !isLive && (
              <div className="space-y-2">
                {!canLaunch && (
                  <ul className="text-xs text-muted-foreground space-y-0.5">
                    {missing.map((m) => (
                      <li key={m} className="flex items-center gap-1.5">
                        <Circle className="h-2.5 w-2.5 text-amber-400 shrink-0" />
                        {m}
                      </li>
                    ))}
                  </ul>
                )}
                <Button
                  size="sm"
                  onClick={handleActivate}
                  disabled={activating || !canLaunch}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50"
                  data-testid="setup-flow-launch-btn"
                >
                  {activating ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <Zap className="h-3.5 w-3.5 mr-1" />}
                  {canLaunch ? 'Activate Store' : 'Complete Required Steps First'}
                </Button>
              </div>
            )}

            {step.id === 'launch' && isLive && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => window.open(`${window.location.origin}/store/${store.id}`, '_blank')}
                  data-testid="setup-view-live-btn"
                >
                  <Store className="h-3.5 w-3.5 mr-1" /> View Live Store
                  <ExternalLink className="h-3 w-3 ml-1" />
                </Button>
              </div>
            )}

          </StepRow>
        ))}
      </div>
    </div>
  );
}
