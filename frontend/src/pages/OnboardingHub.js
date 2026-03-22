import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Separator } from '../components/ui/separator';
import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, PlayCircle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { useApp } from '../context/AppContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TIERS = [
  {
    id: 'quick_start',
    title: 'Quick Start Setup',
    duration: '10 minutes',
    description: 'Get operational fast so you can create jobs, send proofs, and accept payments.',
    steps: [
      { id: 'quick_company_profile', title: 'Company Profile', type: 'link', route: '/settings', required: true, cta: 'Open Company Profile', lesson: 'Add your company name, business email, phone, address, and logo. This information appears on invoices, quotes, customer portals, and documents.' },
      { id: 'quick_stripe_connect', title: 'Connect Payment Processing', type: 'link', route: '/admin/payments', required: false, cta: 'Open Stripe Setup', lesson: 'Connect Stripe so invoice and webstore payments work. If you skip this step, payment features stay disabled until later.' },
      { id: 'quick_production_workflow', title: 'Set Production Workflow', type: 'workflow', required: false, lesson: 'Choose a simple or detailed workflow. Simple is the fastest path and you can customize by category later.' },
      { id: 'quick_first_employee', title: 'Add First Employee', type: 'employee', required: false, lesson: 'Create at least one employee. Employees can clock in, see assigned jobs, and start production stages in the employee portal.' },
      { id: 'quick_basic_pricing', title: 'Basic Pricing Setup', type: 'pricing', required: false, lesson: 'Enter a few key material and labor values so pricing calculators can produce realistic estimates right away.' },
      { id: 'quick_customer_portal', title: 'Enable Customer Portal', type: 'portal', required: false, lesson: 'Turn on approvals, messaging, document sharing, and invoice payments. Customers must already exist in your database before they can be invited.' },
      { id: 'quick_first_job', title: 'Create First Job', type: 'link', route: '/customers', required: false, cta: 'Create Customer / Job', lesson: 'Create a customer first, then build a test job, upload artwork, send a proof, assign workflow stages, and optionally schedule or assign the job.' },
      { id: 'quick_portal_test', title: 'Quick Test of Customer Portal', type: 'manual', required: false, lesson: 'Send a proof approval request, a message, and a document to confirm customer portal access works end to end.' },
    ]
  },
  {
    id: 'standard_setup',
    title: 'Standard Setup',
    duration: '30 minutes',
    description: 'Move from “working” to “optimized” with better pricing, forms, documents, and workflows.',
    steps: [
      { id: 'standard_historical_invoices', title: 'Import Historical Invoices', type: 'link', route: '/settings/pricing-setup', cta: 'Open Historical Import', lesson: 'Upload past invoices so AI can suggest pricing benchmarks by category, order value, and patterns.' },
      { id: 'standard_detailed_pricing', title: 'Configure Detailed Pricing Settings', type: 'link', route: '/pricing-calculator/settings', cta: 'Open Pricing & Costs', lesson: 'Fill in deeper material costs, labor rates, overhead, and target margins so calculators reflect real shop economics.' },
      { id: 'standard_product_categories', title: 'Configure Product Categories', type: 'manual', lesson: 'Review the product categories that organize jobs, pricing, reports, and invoice analysis. Add or rename as needed.' },
      { id: 'standard_category_workflows', title: 'Configure Workflow by Category', type: 'link', route: '/settings/production', cta: 'Open Production Workflow', lesson: 'Set category-specific workflows so banners, wraps, signs, and apparel each follow the right timeline.' },
      { id: 'standard_document_types', title: 'Configure Document Types', type: 'link', route: '/documents', cta: 'Open Document Library', lesson: 'Organize proofs, contracts, invoices, install instructions, and completion photos for cleaner internal and customer-facing records.' },
      { id: 'standard_questionnaires', title: 'Create Questionnaire Templates', type: 'link', route: '/questionnaires', cta: 'Open Questionnaires', lesson: 'Create reusable intake and measurement forms so the right information gets collected before work begins.' },
      { id: 'standard_notifications', title: 'Configure Notification Preferences', type: 'manual', lesson: 'Choose which approvals, messages, submissions, payments, and status changes should notify your team.' },
      { id: 'standard_ai_access', title: 'Configure AI Tool Access', type: 'manual', lesson: 'Review which roles should be allowed to use different AI tools. Start simple if needed and refine later.' },
      { id: 'standard_job_templates', title: 'Configure Job Templates', type: 'link', route: '/pricing-calculator', cta: 'Open Templates', lesson: 'Save reusable templates for common products so jobs start with consistent defaults and workflow expectations.' },
      { id: 'standard_portal_review', title: 'Review Customer Portal Settings', type: 'manual', lesson: 'Confirm what customers can approve, download, message about, and pay for inside the portal.' },
      { id: 'standard_full_test', title: 'Test Full Workflow', type: 'manual', lesson: 'Run a realistic test: create job, send proof, send questionnaire, send message, create invoice, and test payment flow.' },
    ]
  },
  {
    id: 'full_optimization',
    title: 'Full Optimization',
    duration: '60 minutes',
    description: 'Use analytics, automation, and security review to turn the platform into a full operating system.',
    steps: [
      { id: 'full_production_analytics', title: 'Production Analytics Configuration', type: 'link', route: '/reports/profit-margin', cta: 'Review Analytics', lesson: 'Verify production stage timing and employee-linked production history so the system can measure bottlenecks and durations later.' },
      { id: 'full_labor_cost_integration', title: 'Labor Cost Integration', type: 'link', route: '/pricing-calculator/settings', cta: 'Review Labor Rates', lesson: 'Confirm design, production, and installation rates are configured so labor flows into costing and profitability.' },
      { id: 'full_profit_analytics', title: 'Profit & Margin Analytics', type: 'link', route: '/reports/profit-margin', cta: 'Open Profit Analytics', lesson: 'Use job, category, and customer profitability reports to find underpriced work and top-profit services.' },
      { id: 'full_workflow_automation', title: 'Workflow Automation Rules', type: 'manual', lesson: 'Plan which events should auto-notify staff or customers so approvals and production handoffs require less manual follow-up.' },
      { id: 'full_customer_experience', title: 'Customer Experience Enhancements', type: 'link', route: '/customer-portal', cta: 'Open Customer Portal', lesson: 'Review proof history, documents, forms, and payment visibility from the customer point of view.' },
      { id: 'full_install_scheduling', title: 'Install & Scheduling Optimization', type: 'manual', lesson: 'Review how you want installs, technician assignments, reminders, and checklists organized if installs are part of your process.' },
      { id: 'full_advanced_pricing', title: 'Advanced Pricing Intelligence', type: 'link', route: '/settings/pricing-setup', cta: 'Open Pricing Intelligence', lesson: 'Use historical pricing plus job profitability to spot underpriced patterns and refine future estimates.' },
      { id: 'full_dashboard_customization', title: 'Reporting Dashboard Customization', type: 'link', route: '/reports/profit-margin', cta: 'Customize Reports', lesson: 'Set a simple dashboard that highlights active jobs, approvals, revenue, AI usage, and bottlenecks for your shop.' },
      { id: 'full_security_review', title: 'Security & Permission Review', type: 'link', route: '/settings', cta: 'Review Permissions', lesson: 'Confirm employees only see the right operational sections and cannot access financial or pricing settings unnecessarily.' },
      { id: 'full_backup_safety', title: 'Backup & Data Safety', type: 'link', route: '/settings/backup', cta: 'Open Backup Tools', lesson: 'Review export and backup tools so customer, job, invoice, and document data can be recovered if needed.' },
      { id: 'full_health_check', title: 'Final System Health Check', type: 'manual', lesson: 'Run a final shop-level test of jobs, proofs, forms, messages, documents, invoices, and payments to confirm data sync is solid.' },
      { id: 'full_community_post', title: 'Create First Community Post', type: 'link', route: '/community', cta: 'Open Community Hub', lesson: 'Introduce your shop, ask one question, or share one win so your team starts using the communication hub early.' },
    ]
  }
];

const statusColor = {
  completed: 'bg-green-100 text-green-700 border-green-200',
  finish_later: 'bg-amber-100 text-amber-700 border-amber-200',
  incomplete: 'bg-slate-100 text-slate-700 border-slate-200',
};

export default function OnboardingHub() {
  const navigate = useNavigate();
  const { updateTenant, createEmployee } = useApp();
  const [program, setProgram] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTierId, setSelectedTierId] = useState('quick_start');
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [saving, setSaving] = useState(false);
  const [workflowMode, setWorkflowMode] = useState('simple');
  const [employeeForm, setEmployeeForm] = useState({ name: '', email: '', role: 'production' });
  const [pricingForm, setPricingForm] = useState({ vinyl: '', banner_material: '', coroplast: '', production_hourly_rate: '' });
  const [portalSettings, setPortalSettings] = useState({
    enable_artwork_approvals: true,
    enable_customer_messaging: true,
    enable_document_sharing: true,
    enable_invoice_payments: true,
  });

  const loadProgram = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/onboarding/status`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      setProgram(data);

      const savedTier = data.progress?.current_tier;
      const savedStepId = data.progress?.current_step_id;
      const savedTierConfig = TIERS.find((tier) => tier.id === savedTier);
      if (savedTierConfig && savedStepId) {
        const savedStepIndex = savedTierConfig.steps.findIndex((step) => step.id === savedStepId);
        if (savedStepIndex >= 0) {
          setSelectedTierId(savedTierConfig.id);
          setCurrentStepIndex(savedStepIndex);
          setLoading(false);
          return;
        }
      }

      const firstIncompleteTier = TIERS.find((tier) => tier.steps.some((step) => (data.step_statuses?.[step.id] || 'incomplete') !== 'completed'));
      if (firstIncompleteTier) {
        setSelectedTierId(firstIncompleteTier.id);
        const firstIncompleteStep = firstIncompleteTier.steps.findIndex((step) => (data.step_statuses?.[step.id] || 'incomplete') !== 'completed');
        setCurrentStepIndex(Math.max(firstIncompleteStep, 0));
      }
    } catch (err) {
      toast.error('Failed to load onboarding program');
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadProgram(); }, [loadProgram]);

  const selectedTier = useMemo(() => TIERS.find((tier) => tier.id === selectedTierId) || TIERS[0], [selectedTierId]);
  const selectedStep = selectedTier.steps[currentStepIndex];
  const analytics = program?.analytics || {};
  const finishLaterSteps = Object.entries(program?.step_statuses || {}).filter(([, status]) => status === 'finish_later');

  useEffect(() => {
    const saveSession = async () => {
      if (!selectedTierId || !selectedTier?.steps?.[currentStepIndex]) return;
      const token = localStorage.getItem('auth_token');
      await fetch(`${API}/onboarding/session`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_tier: selectedTierId,
          current_step_id: selectedTier.steps[currentStepIndex].id,
        }),
      });
    };

    saveSession();
  }, [selectedTierId, currentStepIndex, selectedTier]);

  const getStepStatus = (stepId) => program?.step_statuses?.[stepId] || 'incomplete';
  const selectedTierCompleteCount = selectedTier.steps.filter((step) => getStepStatus(step.id) === 'completed').length;

  const updateStepStatus = async (stepId, status) => {
    const token = localStorage.getItem('auth_token');
    await fetch(`${API}/onboarding/steps/${stepId}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ status }),
    });
    await loadProgram();
  };

  const saveWorkflowMode = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('auth_token');
      await fetch(`${API}/production-timeline/settings`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow_mode: workflowMode, category_template_map: {} }),
      });
      toast.success('Workflow mode saved');
      await updateStepStatus('quick_production_workflow', 'completed');
    } catch {
      toast.error('Failed to save workflow mode');
    }
    setSaving(false);
  };

  const saveEmployee = async () => {
    if (!employeeForm.name.trim()) {
      toast.error('Employee name is required');
      return;
    }
    setSaving(true);
    try {
      await createEmployee({ ...employeeForm, hourly_rate: 0 });
      toast.success('Employee added');
      setEmployeeForm({ name: '', email: '', role: 'production' });
      await updateStepStatus('quick_first_employee', 'completed');
    } catch {
      toast.error('Failed to create employee');
    }
    setSaving(false);
  };

  const saveBasicPricing = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('auth_token');
      await fetch(`${API}/pricing/defaults`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          materials: [
            { id: 'vinyl-cost', key: 'vinyl', name: 'Vinyl Cost Per Sq Ft', category: 'material', cost_per_unit: Number(pricingForm.vinyl || 0), unit_type: 'sqft', is_active: true },
            { id: 'banner-material-cost', key: 'banner_material', name: 'Banner Material Cost Per Sq Ft', category: 'material', cost_per_unit: Number(pricingForm.banner_material || 0), unit_type: 'sqft', is_active: true },
            { id: 'coroplast-cost', key: 'coroplast', name: 'Coroplast Cost Per Sq Ft', category: 'material', cost_per_unit: Number(pricingForm.coroplast || 0), unit_type: 'sqft', is_active: true },
          ],
          production_hourly_rate: Number(pricingForm.production_hourly_rate || 0),
        }),
      });
      toast.success('Basic pricing saved');
      await updateStepStatus('quick_basic_pricing', 'completed');
    } catch {
      toast.error('Failed to save pricing settings');
    }
    setSaving(false);
  };

  const savePortalSettings = async () => {
    setSaving(true);
    try {
      await updateTenant({ customer_portal_settings: portalSettings });
      toast.success('Customer portal settings saved');
      await updateStepStatus('quick_customer_portal', 'completed');
    } catch {
      toast.error('Failed to save customer portal settings');
    }
    setSaving(false);
  };

  const renderQuickAction = (step) => {
    if (step.type === 'workflow') {
      return (
        <div className="space-y-3">
          <Label>Workflow Mode</Label>
          <Select value={workflowMode} onValueChange={setWorkflowMode}>
            <SelectTrigger data-testid="onboarding-workflow-mode-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="simple">Simple Workflow</SelectItem>
              <SelectItem value="detailed">Detailed Workflow</SelectItem>
              <SelectItem value="custom">Custom Workflow</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={saveWorkflowMode} disabled={saving} data-testid="onboarding-save-workflow-button">Save Workflow Choice</Button>
        </div>
      );
    }

    if (step.type === 'employee') {
      return (
        <div className="grid gap-3 md:grid-cols-3">
          <Input placeholder="Employee Name" value={employeeForm.name} onChange={(e) => setEmployeeForm({ ...employeeForm, name: e.target.value })} data-testid="onboarding-employee-name" />
          <Input placeholder="Email Address" value={employeeForm.email} onChange={(e) => setEmployeeForm({ ...employeeForm, email: e.target.value })} data-testid="onboarding-employee-email" />
          <Select value={employeeForm.role} onValueChange={(value) => setEmployeeForm({ ...employeeForm, role: value })}>
            <SelectTrigger data-testid="onboarding-employee-role"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="designer">Designer</SelectItem>
              <SelectItem value="production">Production</SelectItem>
              <SelectItem value="installer">Installer</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={saveEmployee} disabled={saving} className="md:col-span-3" data-testid="onboarding-save-employee-button">Add First Employee</Button>
        </div>
      );
    }

    if (step.type === 'pricing') {
      return (
        <div className="grid gap-3 md:grid-cols-2">
          <Input placeholder="Vinyl Cost / Sq Ft" value={pricingForm.vinyl} onChange={(e) => setPricingForm({ ...pricingForm, vinyl: e.target.value })} data-testid="onboarding-pricing-vinyl" />
          <Input placeholder="Banner Material Cost / Sq Ft" value={pricingForm.banner_material} onChange={(e) => setPricingForm({ ...pricingForm, banner_material: e.target.value })} data-testid="onboarding-pricing-banner" />
          <Input placeholder="Coroplast Cost / Sq Ft" value={pricingForm.coroplast} onChange={(e) => setPricingForm({ ...pricingForm, coroplast: e.target.value })} data-testid="onboarding-pricing-coroplast" />
          <Input placeholder="Production Hourly Rate" value={pricingForm.production_hourly_rate} onChange={(e) => setPricingForm({ ...pricingForm, production_hourly_rate: e.target.value })} data-testid="onboarding-pricing-production-rate" />
          <Button onClick={saveBasicPricing} disabled={saving} className="md:col-span-2" data-testid="onboarding-save-pricing-button">Save Basic Pricing</Button>
        </div>
      );
    }

    if (step.type === 'portal') {
      return (
        <div className="space-y-3">
          {[
            ['enable_artwork_approvals', 'Enable Artwork Approvals'],
            ['enable_customer_messaging', 'Enable Customer Messaging'],
            ['enable_document_sharing', 'Enable Document Sharing'],
            ['enable_invoice_payments', 'Enable Invoice Payments'],
          ].map(([key, label]) => (
            <div key={key} className="flex items-center justify-between rounded-lg border p-3">
              <Label>{label}</Label>
              <Switch checked={portalSettings[key]} onCheckedChange={(checked) => setPortalSettings({ ...portalSettings, [key]: checked })} />
            </div>
          ))}
          <p className="text-sm text-slate-500">After this step, invite customers from the customer record using the new <strong>Invite to Portal</strong> button.</p>
          <Button onClick={savePortalSettings} disabled={saving} data-testid="onboarding-save-portal-settings-button">Save Customer Portal Settings</Button>
        </div>
      );
    }

    return null;
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Clock3 className="h-8 w-8 animate-spin text-teal-500" /></div>;
  }

  return (
    <div className="space-y-6" data-testid="onboarding-hub-page">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">SignGuy AI OS Onboarding</h1>
          <p className="text-slate-300 mt-1">Checklist + guided walkthrough so new tenants can learn one part at a time without getting overwhelmed.</p>
        </div>
        <Link to="/dashboard"><Button variant="outline"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard</Button></Link>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {TIERS.map((tier) => {
          const completeCount = tier.steps.filter((step) => getStepStatus(step.id) === 'completed').length;
          return (
            <Card key={tier.id} className={`border ${selectedTierId === tier.id ? 'border-teal-400' : 'border-slate-700'}`} data-testid={`onboarding-tier-${tier.id}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-slate-900">{tier.title}</CardTitle>
                  <Badge>{tier.duration}</Badge>
                </div>
                <CardDescription className="text-slate-600">{tier.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm text-slate-400">
                  <span>{completeCount} / {tier.steps.length} complete</span>
                  <span>{Math.round((completeCount / tier.steps.length) * 100)}%</span>
                </div>
                <Button variant={selectedTierId === tier.id ? 'default' : 'outline'} className="w-full" onClick={() => { setSelectedTierId(tier.id); setCurrentStepIndex(0); setTimeout(() => document.getElementById('onboarding-steps')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100); }}>
                  {selectedTierId === tier.id ? 'Current Tier' : 'Open Tier'}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-4">
        <Card>
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Overall Completed</p>
            <p className="text-2xl font-bold text-slate-900 mt-2">{Object.values(program?.step_statuses || {}).filter((value) => value === 'completed').length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Finish Later</p>
            <p className="text-2xl font-bold text-slate-900 mt-2">{finishLaterSteps.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Last Activity</p>
            <p className="text-sm font-semibold text-slate-900 mt-2">{program?.progress?.last_opened_at ? new Date(program.progress.last_opened_at).toLocaleString() : 'Not started yet'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Resume Step</p>
            <p className="text-sm font-semibold text-slate-900 mt-2">{selectedStep.title}</p>
          </CardContent>
        </Card>
      </div>

      <div id="onboarding-steps" className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-900">{selectedTier.title} Checklist</CardTitle>
            <CardDescription className="text-slate-600">{selectedTierCompleteCount} of {selectedTier.steps.length} completed</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {selectedTier.steps.map((step, index) => {
              const status = getStepStatus(step.id);
              return (
                <button
                  key={step.id}
                  type="button"
                  onClick={() => setCurrentStepIndex(index)}
                  className={`w-full rounded-xl border p-3 text-left ${currentStepIndex === index ? 'border-teal-400 bg-teal-500/10' : 'border-slate-700 bg-slate-900/40'}`}
                  data-testid={`onboarding-step-${step.id}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{step.title}</p>
                      <p className="text-xs text-slate-400 mt-1">{step.required ? 'Required' : 'Recommended / Optional'}</p>
                    </div>
                    <Badge className={statusColor[status]}>{status === 'finish_later' ? 'Finish Later' : status}</Badge>
                  </div>
                </button>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2 text-slate-900"><PlayCircle className="h-5 w-5 text-teal-400" /> Guided Walkthrough</CardTitle>
                <CardDescription className="text-slate-600">Short class-style walkthrough for the selected step.</CardDescription>
              </div>
              <Badge className={statusColor[getStepStatus(selectedStep.id)]}>{getStepStatus(selectedStep.id) === 'finish_later' ? 'Finish Later' : getStepStatus(selectedStep.id)}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <p className="text-sm uppercase tracking-wider text-slate-400">{selectedTier.title}</p>
              <h2 className="text-2xl font-semibold text-slate-900">{selectedStep.title}</h2>
              <p className="text-slate-600">{selectedStep.lesson}</p>
            </div>

            {renderQuickAction(selectedStep)}

            {selectedStep.type === 'link' && selectedStep.route && (
              <div className="rounded-xl border border-slate-700 bg-slate-900/40 p-4">
                <p className="text-sm text-slate-300 mb-3">Open the matching setup page, make the changes, then come back here and continue.</p>
                <Link to={selectedStep.route}><Button data-testid={`onboarding-open-${selectedStep.id}`}>{selectedStep.cta || 'Open Step'} <ArrowRight className="h-4 w-4 ml-2" /></Button></Link>
              </div>
            )}

            {selectedStep.type === 'manual' && (
              <div className="rounded-xl border border-slate-700 bg-slate-900/40 p-4">
                <p className="text-sm text-slate-300">This step is currently checklist-guided. Complete it in the linked area of the app, or mark it for later if you want to keep moving.</p>
              </div>
            )}

            <Separator />

            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setCurrentStepIndex((value) => Math.max(value - 1, 0))} disabled={currentStepIndex === 0}>Back</Button>
                <Button variant="outline" onClick={() => setCurrentStepIndex((value) => Math.min(value + 1, selectedTier.steps.length - 1))} disabled={currentStepIndex === selectedTier.steps.length - 1}>Next</Button>
              </div>
              <div className="flex gap-2">
                {!selectedStep.required && getStepStatus(selectedStep.id) !== 'completed' && (
                  <Button variant="outline" onClick={() => updateStepStatus(selectedStep.id, 'finish_later')} data-testid={`onboarding-finish-later-${selectedStep.id}`}>Finish Later</Button>
                )}
                {getStepStatus(selectedStep.id) !== 'completed' && (
                  <Button onClick={() => updateStepStatus(selectedStep.id, 'completed')} data-testid={`onboarding-mark-complete-${selectedStep.id}`}>
                    <CheckCircle2 className="h-4 w-4 mr-2" /> Mark Complete
                  </Button>
                )}
              </div>
            </div>

            {selectedTierCompleteCount === selectedTier.steps.length && (
              <div className="rounded-xl border border-green-400/40 bg-green-500/10 p-4 text-green-200" data-testid={`onboarding-tier-complete-${selectedTier.id}`}>
                <div className="flex items-center gap-2 font-medium"><Sparkles className="h-4 w-4" /> {selectedTier.title} Complete</div>
                <p className="text-sm mt-2">Great — this tier is complete. You can continue into the next tier or revisit any step later.</p>
              </div>
            )}

            {finishLaterSteps.length > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900" data-testid="onboarding-finish-later-summary">
                <p className="font-medium">Finish Later Queue</p>
                <p className="text-sm mt-1">You currently have {finishLaterSteps.length} step(s) marked to finish later. Resume them anytime from this hub.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}