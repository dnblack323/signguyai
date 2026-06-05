/**
 * WebstoreSetupFlow — consolidated pre-launch setup tab.
 *
 * Shows every setup step (questionnaire → branding → products →
 * fulfillment → Stripe → preview → launch) in sequential order with a
 * clear per-step status badge so staff always knows the next action.
 *
 * All pre-launch actions live here. Other tabs (Products, Settings,
 * Dashboard) are secondary and linked-to from each step.
 */
import { useState, useCallback } from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Separator } from './ui/separator';
import {
  CheckCircle2, Circle, Clock, AlertCircle, Lock,
  Mail, Eye, Package, Palette, Truck, CreditCard,
  Zap, ExternalLink, RefreshCw, Loader2, Copy, Check,
  ChevronRight, AlertTriangle, ClipboardCheck,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { cn } from '../lib/utils';
import { toast } from 'sonner';
import WebstoreOwnerConnectCard from './WebstoreOwnerConnectCard';

// ── Status config ────────────────────────────────────────────────────────────
const S = {
  complete:       { Icon: CheckCircle2, ring: 'bg-emerald-50',  ic: 'text-emerald-500', badge: 'bg-emerald-100 text-emerald-700 border-emerald-200', label: 'Complete'           },
  needs_action:   { Icon: AlertCircle,  ring: 'bg-amber-50',    ic: 'text-amber-500',   badge: 'bg-amber-100 text-amber-700 border-amber-200',   label: 'Action Needed'      },
  pending_review: { Icon: Clock,        ring: 'bg-blue-50',     ic: 'text-blue-500',    badge: 'bg-blue-100 text-blue-700 border-blue-200',    label: 'Ready for Review'   },
  waiting:        { Icon: Clock,        ring: 'bg-gray-50',     ic: 'text-gray-400',    badge: 'bg-gray-100 text-gray-500 border-gray-200',    label: 'Waiting on Owner'   },
  not_started:    { Icon: Circle,       ring: 'bg-muted',       ic: 'text-gray-300',    badge: 'bg-gray-50  text-gray-400 border-gray-200',    label: 'Not Started'        },
  blocked:        { Icon: Lock,         ring: 'bg-muted',       ic: 'text-gray-300',    badge: 'bg-gray-50  text-gray-400 border-gray-200',    label: 'Blocked'            },
};

// Questionnaire phase helper (self-contained so component doesn't import from Webstores.js)
const qLabel = (t) => ({
  event: 'Event Store Setup Questionnaire',
  fundraiser: 'Fundraiser Store Setup Questionnaire',
  creator: 'Team / School Store Setup Questionnaire',
  business: 'Business Store Setup Questionnaire',
}[t] || 'Store Setup Questionnaire');

const qPhase = (qs) => {
  if (!qs?.linked) return 'not_sent';
  const resp = qs.latest_response;
  if (resp?.applied_to_webstore) return 'applied';
  if (resp?.submitted_at)         return 'awaiting_review';
  if (qs.questionnaire?.last_sent_at) return 'sent';
  return 'draft';
};

// ── Step row ─────────────────────────────────────────────────────────────────
function StepRow({ step, isLast, children }) {
  const cfg = S[step.status] || S.not_started;
  const { Icon } = cfg;
  return (
    <div className="relative flex gap-3">
      {!isLast && (
        <div className="absolute left-[15px] top-[34px] bottom-0 w-px bg-border z-0" />
      )}
      <div className={cn('mt-1 shrink-0 h-8 w-8 rounded-full flex items-center justify-center z-10', cfg.ring)}>
        <Icon className={cn('h-4 w-4', cfg.ic)} />
      </div>
      <div className="flex-1 min-w-0 pb-5">
        <div className="flex flex-wrap items-center gap-2 mb-0.5">
          <span className={cn('text-sm font-semibold', step.status === 'complete' ? 'text-muted-foreground' : 'text-foreground')}>
            {step.title}
          </span>
          <Badge className={cn('text-[10px] border shrink-0 px-1.5 py-0', cfg.badge)}>
            {cfg.label}
          </Badge>
          {step.required && step.status !== 'complete' && (
            <Badge variant="outline" className="text-[10px] border-red-200 text-red-500 shrink-0 px-1.5 py-0">Required</Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">{step.description}</p>
        {children && <div className="mt-3 space-y-3">{children}</div>}
      </div>
    </div>
  );
}

// ── Launch gate ───────────────────────────────────────────────────────────────
function launchReady({ storeProducts, questionnaireApplied }) {
  const hasProducts = (storeProducts || []).length > 0;
  const missing = [];
  if (!hasProducts) missing.push('At least one product must be assigned');
  return { ok: missing.length === 0, missing };
}

// ── Main component ───────────────────────────────────────────────────────────
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
  onActivateStore,         // async () => void — shorthand for status=active
}) {
  const { getWebstoreOwnerStatus, sendWebstoreOwnerInvite } = useApp();

  // Questionnaire inline send
  const [sendingQ, setSendingQ]   = useState(false);
  const [qEmailSent, setQEmailSent] = useState(false);
  const [qEmailFail, setQEmailFail] = useState(false);
  const [qFallbackLink, setQFallbackLink] = useState(null);
  const [qEmail, setQEmail]       = useState(store?.owner_email || '');
  const [copiedLink, setCopiedLink] = useState(false);

  // Activate store
  const [activating, setActivating] = useState(false);

  const phase = qPhase(questionnaireStatus);
  const hasProducts = (storeProducts || []).length > 0;
  const hasBranding = !!(store.branding?.logo_url || store.logo_url || store.branding?.banner_url || store.banner_url);
  const hasFulfillment = !!(store.pickup_delivery_instructions || store.pickup_delivery_date || store.order_deadline);
  const { ok: canLaunch, missing } = launchReady({ storeProducts, questionnaireApplied: phase === 'applied' });
  const isLive = store.status === 'active';

  const handleSendQ = async () => {
    if (!qEmail.trim()) { toast.error('Enter an email address'); return; }
    setSendingQ(true);
    setQEmailFail(false);
    try {
      const result = await onSendQuestionnaire(store.id, qEmail.trim());
      if (result?.email_sent || result?.success) {
        setQEmailSent(true);
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
    try {
      await onActivateStore();
    } finally {
      setActivating(false);
    }
  };

  // ── Step definitions ────────────────────────────────────────────────────
  const qStatus = phase === 'applied'        ? 'complete'
                : phase === 'awaiting_review'? 'pending_review'
                : (phase === 'sent' || phase === 'draft') ? 'waiting'
                : 'needs_action';

  const steps = [
    {
      id: 'record',
      title: 'Store Created',
      status: 'complete',
      required: true,
      description: `${store.name} · ${store.store_type} store · ${store.status}`,
    },
    {
      id: 'questionnaire',
      title: 'Setup Questionnaire',
      status: loadingQuestionnaire ? 'not_started' : qStatus,
      required: false,
      description: qLabel(store.store_type) + (
        phase === 'applied' ? ' — owner answers applied to this store.' :
        phase === 'awaiting_review' ? ' — owner has submitted answers, ready for staff review.' :
        phase === 'sent' ? ' — questionnaire sent, waiting for owner to submit.' :
        ' — send to the owner to collect event details, fulfillment, and preferences.'
      ),
    },
    {
      id: 'branding',
      title: 'Branding',
      status: hasBranding ? 'complete' : 'not_started',
      required: false,
      description: hasBranding
        ? 'Logo or banner is set.'
        : 'Upload a logo, banner image, and choose a primary color.',
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
      title: 'Fulfillment / Shipping',
      status: hasFulfillment ? 'complete' : 'not_started',
      required: false,
      description: hasFulfillment
        ? (store.pickup_delivery_instructions || `Pickup date: ${store.pickup_delivery_date}`)
        : 'Set pickup instructions, delivery dates, and any shipping fees.',
    },
    {
      id: 'stripe',
      title: 'Owner Stripe Onboarding',
      status: 'not_started', // Driven by WebstoreOwnerConnectCard internal state
      required: false,
      description: 'Send the store owner a Stripe Connect invite so they can receive payouts.',
    },
    {
      id: 'preview',
      title: 'Preview & Approval',
      status: isLive ? 'complete' : 'not_started',
      required: false,
      description: 'Preview the storefront as customers would see it before going live.',
    },
    {
      id: 'launch',
      title: 'Launch Store',
      status: isLive ? 'complete'
              : canLaunch ? 'needs_action'
              : 'blocked',
      required: true,
      description: isLive
        ? 'Store is live and accepting orders.'
        : canLaunch
          ? 'All required steps are done. Activate the store to go live.'
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
          <StepRow key={step.id} step={step} isLast={idx === lastIdx}>

            {/* ── Step-specific actions ── */}

            {step.id === 'questionnaire' && !loadingQuestionnaire && (
              <>
                {phase === 'not_sent' || phase === 'draft' ? (
                  // Not yet sent — show inline send form
                  qEmailSent ? (
                    <div className="flex items-center gap-2 text-xs text-emerald-600 bg-emerald-50 rounded p-2">
                      <Check className="h-3.5 w-3.5 shrink-0" />
                      Questionnaire sent to <strong>{qEmail}</strong>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Input
                          type="email"
                          value={qEmail}
                          onChange={(e) => setQEmail(e.target.value)}
                          placeholder="owner@example.com"
                          className="h-8 text-xs flex-1"
                          data-testid="setup-flow-q-email-input"
                        />
                        <Button
                          size="sm"
                          className="h-8 bg-orange-500 hover:bg-orange-600 text-white shrink-0"
                          onClick={handleSendQ}
                          disabled={sendingQ || !qEmail.trim()}
                          data-testid="setup-flow-send-q-btn"
                        >
                          {sendingQ ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <><Mail className="h-3.5 w-3.5 mr-1" />Send</>}
                        </Button>
                      </div>
                      {qEmailFail && (
                        <div className="space-y-1.5" data-testid="setup-flow-q-link-fallback">
                          <p className="text-xs text-amber-700 flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3 shrink-0" />
                            Email failed. Copy and share this link manually:
                          </p>
                          {qFallbackLink && (
                            <div className="flex gap-1.5">
                              <code className="flex-1 text-[10px] bg-muted rounded px-2 py-1 overflow-hidden text-ellipsis whitespace-nowrap select-all">
                                {qFallbackLink}
                              </code>
                              <Button size="icon" variant="outline" className="h-7 w-7 shrink-0" onClick={copyFallback} data-testid="setup-flow-copy-link-btn">
                                {copiedLink ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
                              </Button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                ) : phase === 'awaiting_review' ? (
                  // Submitted by owner — show review + apply
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      className="h-8 bg-orange-500 hover:bg-orange-600 text-white"
                      onClick={onApplyAnswers}
                      disabled={applyingAnswers}
                      data-testid="setup-flow-apply-btn"
                    >
                      {applyingAnswers ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <><Check className="h-3.5 w-3.5 mr-1" />Apply Answers</>}
                    </Button>
                    {questionnaireStatus?.questionnaire?.id && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8"
                        onClick={() => window.open(`/questionnaire/${questionnaireStatus.questionnaire.id}`, '_blank')}
                        data-testid="setup-flow-view-q-btn"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" /> View Answers
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 text-xs"
                      onClick={() => { setSendingQ(false); setQEmailSent(false); }}
                      data-testid="setup-flow-resend-q-btn"
                    >
                      <Mail className="h-3.5 w-3.5 mr-1" /> Resend
                    </Button>
                  </div>
                ) : phase === 'sent' ? (
                  // Sent, waiting
                  <div className="flex flex-wrap gap-2">
                    <span className="text-xs text-muted-foreground self-center">Waiting for owner to submit.</span>
                    {questionnaireStatus?.questionnaire?.id && (
                      <Button size="sm" variant="outline" className="h-8"
                        onClick={() => window.open(`/questionnaire/${questionnaireStatus.questionnaire.id}`, '_blank')}
                        data-testid="setup-flow-view-q-btn"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" /> View Form
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" className="h-8 text-xs"
                      onClick={() => { setQEmailSent(false); }}
                      data-testid="setup-flow-resend-q-btn"
                    >
                      Resend
                    </Button>
                  </div>
                ) : phase === 'applied' ? (
                  <div className="flex gap-2">
                    {questionnaireStatus?.questionnaire?.id && (
                      <Button size="sm" variant="outline" className="h-8"
                        onClick={() => window.open(`/questionnaire/${questionnaireStatus.questionnaire.id}`, '_blank')}
                        data-testid="setup-flow-view-q-btn"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" /> View Responses
                      </Button>
                    )}
                  </div>
                ) : null}
              </>
            )}

            {step.id === 'branding' && !hasBranding && (
              <Button size="sm" variant="outline" className="h-8" onClick={() => onShowTab('settings')} data-testid="setup-flow-branding-btn">
                <Palette className="h-3.5 w-3.5 mr-1" /> Upload Logo / Banner <ChevronRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}

            {step.id === 'products' && (
              <Button size="sm" variant={hasProducts ? 'outline' : 'default'} className="h-8" onClick={() => onShowTab('products')} data-testid="setup-flow-products-btn">
                <Package className="h-3.5 w-3.5 mr-1" /> {hasProducts ? 'Manage Products' : 'Assign Products'} <ChevronRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}

            {step.id === 'fulfillment' && !hasFulfillment && (
              <Button size="sm" variant="outline" className="h-8" onClick={() => onShowTab('settings')} data-testid="setup-flow-fulfillment-btn">
                <Truck className="h-3.5 w-3.5 mr-1" /> Set Fulfillment Details <ChevronRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}

            {step.id === 'stripe' && (
              <div className="w-full">
                <WebstoreOwnerConnectCard webstore={store} />
              </div>
            )}

            {step.id === 'preview' && !isLive && (
              <Button
                size="sm"
                variant="outline"
                className="h-8"
                onClick={() => window.open(`${window.location.origin}/store/${store.id}?admin_preview=1`, '_blank')}
                data-testid="setup-flow-preview-btn"
              >
                <Eye className="h-3.5 w-3.5 mr-1" /> Admin Preview <ExternalLink className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}

            {step.id === 'launch' && !isLive && (
              <div className="space-y-2">
                {!canLaunch && (
                  <div className="flex items-start gap-1.5 text-xs text-amber-700 bg-amber-50 rounded p-2">
                    <Lock className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                    <span>Complete required steps above before launching.</span>
                  </div>
                )}
                <Button
                  size="sm"
                  className={cn('h-8', canLaunch ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : '')}
                  variant={canLaunch ? 'default' : 'outline'}
                  disabled={!canLaunch || activating}
                  onClick={handleActivate}
                  data-testid="setup-flow-launch-btn"
                >
                  {activating
                    ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    : <><Zap className="h-3.5 w-3.5 mr-1" /> Activate Store</>}
                </Button>
              </div>
            )}

          </StepRow>
        ))}
      </div>
    </div>
  );
}
