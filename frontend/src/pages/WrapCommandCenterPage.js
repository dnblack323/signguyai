// Phase 2A: Wrap Command Center page.
// Phase 1 layout untouched. Phase 2A adds:
//   • fetch /api/wrap/items/{ticketId} and pass wrapData + setters to tabs
//   • track save status (idle | saving | saved | error) and surface it in the header subtitle
//   • Vehicle Info tab + Measurements tab now save real data via the new
//     endpoints; other tabs continue to use placeholders.

import { useEffect, useMemo, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import WrapCommandHeader from '../components/wrap/WrapCommandHeader';
import WrapStatusBar from '../components/wrap/WrapStatusBar';
import WrapTabNavigation from '../components/wrap/WrapTabNavigation';
import WrapSidebar from '../components/wrap/WrapSidebar';

import OverviewTab from '../components/wrap/tabs/OverviewTab';
import VehicleInfoTab from '../components/wrap/tabs/VehicleInfoTab';
import MeasurementsTab from '../components/wrap/tabs/MeasurementsTab';
import PricingTab from '../components/wrap/tabs/PricingTab';
import DesignTab from '../components/wrap/tabs/DesignTab';
import ContractTab from '../components/wrap/tabs/ContractTab';
import InspectionTab from '../components/wrap/tabs/InspectionTab';
import ProductionTab from '../components/wrap/tabs/ProductionTab';
import InstallTab from '../components/wrap/tabs/InstallTab';
import PhotosFilesTab from '../components/wrap/tabs/PhotosFilesTab';
import AftercareTab from '../components/wrap/tabs/AftercareTab';
import AIAssistantTab from '../components/wrap/tabs/AIAssistantTab';
import QuoteDraftModal from '../components/wrap/QuoteDraftModal';

import { PLACEHOLDER_HEADER, isWrapCategory } from '../components/wrap/constants';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

function deriveHeader(order, item, customer, wrapData) {
  if (!order && !item) return PLACEHOLDER_HEADER;
  const snapshot = item?.pricing_snapshot;
  const quoted = snapshot?.active_price || item?.estimated_price || PLACEHOLDER_HEADER.quoted_price;
  const specs = item?.specs || {};
  const v = wrapData?.vehicle_info || {};
  const vehicleParts = [v.year, v.make, v.model].filter(Boolean);
  const vehicle = vehicleParts.length
    ? vehicleParts.join(' ')
    : [specs.vehicle_year, specs.vehicle_make, specs.vehicle_model].filter(Boolean).join(' ') || PLACEHOLDER_HEADER.vehicle;
  return {
    order_number: order?.order_number ? `Order #${order.order_number}` : PLACEHOLDER_HEADER.order_number,
    customer_name: customer?.name || order?.customer_name || PLACEHOLDER_HEADER.customer_name,
    business_name: customer?.company || order?.customer_company || '',
    item_name: item?.item_name || PLACEHOLDER_HEADER.item_name,
    vehicle,
    wrap_type: specs.wrap_type || item?.item_category?.replace(/_/g, ' ') || PLACEHOLDER_HEADER.wrap_type,
    status: PLACEHOLDER_HEADER.status,
    quoted_price: quoted,
    deposit_status: PLACEHOLDER_HEADER.deposit_status,
    balance_due: quoted,
  };
}

export default function WrapCommandCenterPage() {
  const { orderId, itemId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const [item, setItem] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [wrapData, setWrapData] = useState(null);
  const [saveStatus, setSaveStatus] = useState('idle'); // idle | saving | saved | error
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const res = await axios.get(`${API}/orders/${orderId}`, { headers: hdr() });
        if (cancelled) return;
        const o = res.data || null;
        setOrder(o);
        const tickets = o?.job_tickets || [];
        const matched = tickets.find((t) => t.id === itemId) || null;
        setItem(matched);
        // Pull customer (best-effort) and wrap data in parallel
        const tasks = [];
        if (o?.customer_id) {
          tasks.push(axios.get(`${API}/customers/${o.customer_id}`, { headers: hdr() })
            .then((cr) => { if (!cancelled) setCustomer(cr.data || null); })
            .catch(() => {}));
        }
        if (matched && isWrapCategory(matched.item_category)) {
          tasks.push(axios.get(`${API}/wrap/items/${itemId}`, { headers: hdr() })
            .then((wr) => { if (!cancelled) setWrapData(wr.data || null); })
            .catch(() => { /* keep wrapData null on failure */ }));
        }
        await Promise.all(tasks);
      } catch (_) {
        // network/auth failure — fall back to placeholder UI so users still see structure
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (orderId) load();
    return () => { cancelled = true; };
  }, [orderId, itemId]);

  const header = useMemo(() => deriveHeader(order, item, customer, wrapData), [order, item, customer, wrapData]);

  // If item is loaded but not wrap, gently redirect (preserve Phase 1 guard)
  useEffect(() => {
    if (!loading && item && !isWrapCategory(item.item_category)) {
      navigate(`/orders/${orderId}`, { replace: true });
    }
  }, [loading, item, orderId, navigate]);

  // ─── Save helpers (used by Vehicle Info + Measurements tabs) ───
  const flashSaved = useCallback(() => {
    setSaveStatus('saved');
    setSaveError('');
    setTimeout(() => {
      setSaveStatus((s) => (s === 'saved' ? 'idle' : s));
    }, 2000);
  }, []);

  const handleSaveVehicle = useCallback(async (vehiclePayload) => {
    setSaveStatus('saving');
    setSaveError('');
    try {
      const res = await axios.put(`${API}/wrap/items/${itemId}/vehicle`, vehiclePayload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Vehicle info saved');
      return { ok: true };
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed to save';
      setSaveError(msg);
      toast.error('Failed to save vehicle info', { description: msg });
      return { ok: false, error: msg };
    }
  }, [itemId, flashSaved]);

  const handleAddArea = useCallback(async (areaPayload) => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}/areas`, areaPayload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Area added');
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to add area', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleUpdateArea = useCallback(async (areaId, areaPayload) => {
    setSaveStatus('saving');
    try {
      const res = await axios.put(`${API}/wrap/items/${itemId}/areas/${areaId}`, areaPayload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to update area', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleDeleteArea = useCallback(async (areaId) => {
    setSaveStatus('saving');
    try {
      const res = await axios.delete(`${API}/wrap/items/${itemId}/areas/${areaId}`, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Area deleted');
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to delete area', { description: msg });
    }
  }, [itemId, flashSaved]);

  // ─── Pricing & Materials (Phase 2B) ───
  const handleSavePricing = useCallback(async (pricingPayload) => {
    setSaveStatus('saving');
    try {
      const res = await axios.put(`${API}/wrap/items/${itemId}/pricing`, pricingPayload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Pricing saved');
      return true;
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to save pricing', { description: msg });
      return false;
    }
  }, [itemId, flashSaved]);

  const handleRecalculate = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}/recalculate`, {}, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Pricing recalculated');
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to recalculate', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleApplyPrice = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}/apply-price-to-order`, {}, { headers: hdr() });
      setWrapData(res.data || null);
      // also refresh the parent order so the header's quoted/balance update
      try {
        const o = await axios.get(`${API}/orders/${orderId}`, { headers: hdr() });
        setOrder(o.data || null);
        const tickets = o.data?.job_tickets || [];
        setItem(tickets.find((t) => t.id === itemId) || null);
      } catch (_) { /* non-fatal */ }
      flashSaved();
      const applied = res.data?.applied_to_ticket;
      toast.success('Price applied to order', {
        description: applied ? `Order item updated to $${(applied.estimated_price || 0).toFixed(2)}` : undefined,
      });
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to apply price', { description: msg });
    }
  }, [itemId, orderId, flashSaved]);

  const handleAddMaterial = useCallback(async (payload) => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}/materials`, payload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Material added');
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to add material', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleUpdateMaterial = useCallback(async (materialId, payload) => {
    setSaveStatus('saving');
    try {
      const res = await axios.put(`${API}/wrap/items/${itemId}/materials/${materialId}`, payload, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to update material', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleDeleteMaterial = useCallback(async (materialId) => {
    setSaveStatus('saving');
    try {
      const res = await axios.delete(`${API}/wrap/items/${itemId}/materials/${materialId}`, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      toast.success('Material deleted');
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Failed to delete material', { description: msg });
    }
  }, [itemId, flashSaved]);

  // ─── Phase 2C: Design / Contract / Approvals / Quote Draft ───
  const doWrapPut = useCallback(async (path, body, successMsg) => {
    setSaveStatus('saving');
    try {
      const res = await axios.put(`${API}/wrap/items/${itemId}${path}`, body, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      if (successMsg) toast.success(successMsg);
      return true;
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Save failed', { description: msg });
      return false;
    }
  }, [itemId, flashSaved]);

  const doWrapPost = useCallback(async (path, body, successMsg) => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}${path}`, body || {}, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      if (successMsg) toast.success(successMsg);
      return res.data;
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Action failed', { description: msg });
      return null;
    }
  }, [itemId, flashSaved]);

  const doWrapDelete = useCallback(async (path, successMsg) => {
    setSaveStatus('saving');
    try {
      const res = await axios.delete(`${API}/wrap/items/${itemId}${path}`, { headers: hdr() });
      setWrapData(res.data || null);
      flashSaved();
      if (successMsg) toast.success(successMsg);
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Delete failed', { description: msg });
    }
  }, [itemId, flashSaved]);

  const handleSaveDesign = useCallback((body) => doWrapPut('/design', body, 'Design saved'), [doWrapPut]);
  const handleSendQuestionnaire = useCallback(() => doWrapPost('/design/send-questionnaire', {}, 'Design questionnaire marked as sent. Customer delivery will be connected in a later phase.'), [doWrapPost]);
  const handleAddProof = useCallback((p) => doWrapPost('/design/proofs', p, 'Proof added'), [doWrapPost]);
  const handleUpdateProof = useCallback((proofId, body) => doWrapPut(`/design/proofs/${proofId}`, body, 'Proof updated'), [doWrapPut]);
  const handleDeleteProof = useCallback((proofId) => doWrapDelete(`/design/proofs/${proofId}`, 'Proof deleted'), [doWrapDelete]);

  const handleSaveContract = useCallback((body) => doWrapPut('/contract', body, 'Contract saved'), [doWrapPut]);
  const handleContractAction = useCallback((action, extra) => doWrapPost('/contract/action', { action, ...(extra || {}) }, `Contract: ${action.replace(/_/g, ' ')}`), [doWrapPost]);

  const handleUpdateApprovals = useCallback((body) => doWrapPut('/approvals', body), [doWrapPut]);

  // ─── Phase 2D: Production / Install ───
  const handleSaveProduction = useCallback((body) => doWrapPut('/production', body, 'Production saved'), [doWrapPut]);
  const handleToggleProductionChecklist = useCallback((key, value) => doWrapPut('/production', { [key]: value }), [doWrapPut]);
  const handleLoadDefaultTasks = useCallback(() => doWrapPost('/production/tasks/load-defaults', {}, 'Default wrap tasks loaded'), [doWrapPost]);
  const handleAddProductionTask = useCallback((p) => doWrapPost('/production/tasks', p, 'Task added'), [doWrapPost]);
  const handleUpdateProductionTask = useCallback((id, p) => doWrapPut(`/production/tasks/${id}`, p), [doWrapPut]);
  const handleDeleteProductionTask = useCallback((id) => doWrapDelete(`/production/tasks/${id}`, 'Task deleted'), [doWrapDelete]);

  const handleSaveInstall = useCallback((body) => doWrapPut('/install', body, 'Install saved'), [doWrapPut]);
  const handleInstallSignoffToggle = useCallback((v) => doWrapPut('/install', { customer_signoff: v }), [doWrapPut]);
  const handleInstallChecklistToggle = useCallback((key, v) => doWrapPut('/install', { checklist: { [key]: v } }), [doWrapPut]);
  const handleAddInstallIssue = useCallback((p) => doWrapPost('/install/issues', p, 'Issue logged'), [doWrapPost]);
  const handleUpdateInstallIssue = useCallback((id, p) => doWrapPut(`/install/issues/${id}`, p), [doWrapPut]);
  const handleDeleteInstallIssue = useCallback((id) => doWrapDelete(`/install/issues/${id}`, 'Issue deleted'), [doWrapDelete]);

  // ─── Phase 2E: Inspection / Aftercare ───
  const handleSaveInspection = useCallback((body) => doWrapPut('/inspection', body, 'Inspection saved'), [doWrapPut]);
  const handleInspectionAckToggle = useCallback((v) => doWrapPut('/inspection', { customer_acknowledged: v }), [doWrapPut]);
  const handleAddDamageMarker = useCallback((p) => doWrapPost('/inspection/damage-markers', p, 'Damage marker added'), [doWrapPost]);
  const handleUpdateDamageMarker = useCallback((id, p) => doWrapPut(`/inspection/damage-markers/${id}`, p), [doWrapPut]);
  const handleDeleteDamageMarker = useCallback((id) => doWrapDelete(`/inspection/damage-markers/${id}`, 'Marker deleted'), [doWrapDelete]);

  const handleSaveAftercare = useCallback((body) => doWrapPut('/aftercare', body, 'Aftercare saved'), [doWrapPut]);
  const handleAftercareToggle = useCallback((key, v) => doWrapPut('/aftercare', { [key]: v }), [doWrapPut]);

  const [quoteDraft, setQuoteDraft] = useState(null);
  const [quoteOpen, setQuoteOpen] = useState(false);
  const handleDraftQuoteMessage = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const res = await axios.post(`${API}/wrap/items/${itemId}/draft-updated-quote-message`, {}, { headers: hdr() });
      if (res.data && res.data.subject) {
        setQuoteDraft(res.data);
        setQuoteOpen(true);
      }
      flashSaved();
    } catch (e) {
      setSaveStatus('error');
      const msg = e?.response?.data?.detail || e?.message || 'Failed';
      setSaveError(msg);
      toast.error('Could not generate quote draft', { description: msg });
    }
  }, [itemId, flashSaved]);

  const renderTab = () => {
    switch (tab) {
      case 'overview':     return <OverviewTab wrapData={wrapData} header={header} onJumpToTab={setTab} />;
      case 'vehicle':      return <VehicleInfoTab wrapData={wrapData} onSave={handleSaveVehicle} saveStatus={saveStatus} />;
      case 'measurements': return <MeasurementsTab wrapData={wrapData} onAddArea={handleAddArea} onUpdateArea={handleUpdateArea} onDeleteArea={handleDeleteArea} saveStatus={saveStatus} />;
      case 'pricing':      return <PricingTab
                                      header={header}
                                      wrapData={wrapData}
                                      onSavePricing={handleSavePricing}
                                      onRecalculate={handleRecalculate}
                                      onApplyPrice={handleApplyPrice}
                                      onAddMaterial={handleAddMaterial}
                                      onUpdateMaterial={handleUpdateMaterial}
                                      onDeleteMaterial={handleDeleteMaterial}
                                      onDraftQuoteMessage={handleDraftQuoteMessage}
                                      saveStatus={saveStatus}
                                    />;
      case 'design':       return <DesignTab
                                      wrapData={wrapData}
                                      onSaveDesign={handleSaveDesign}
                                      onSendQuestionnaire={handleSendQuestionnaire}
                                      onAddProof={handleAddProof}
                                      onUpdateProof={handleUpdateProof}
                                      onDeleteProof={handleDeleteProof}
                                      saveStatus={saveStatus}
                                    />;
      case 'contract':     return <ContractTab
                                      wrapData={wrapData}
                                      onSaveContract={handleSaveContract}
                                      onContractAction={handleContractAction}
                                      onUpdateApprovals={handleUpdateApprovals}
                                      onDraftQuoteMessage={handleDraftQuoteMessage}
                                      saveStatus={saveStatus}
                                    />;
      case 'inspection':   return <InspectionTab
                                      wrapData={wrapData}
                                      onSaveInspection={handleSaveInspection}
                                      onAckToggle={handleInspectionAckToggle}
                                      onAddMarker={handleAddDamageMarker}
                                      onUpdateMarker={handleUpdateDamageMarker}
                                      onDeleteMarker={handleDeleteDamageMarker}
                                      saveStatus={saveStatus}
                                    />;
      case 'production':   return <ProductionTab
                                      wrapData={wrapData}
                                      onSaveProduction={handleSaveProduction}
                                      onToggleChecklist={handleToggleProductionChecklist}
                                      onLoadDefaults={handleLoadDefaultTasks}
                                      onAddTask={handleAddProductionTask}
                                      onUpdateTask={handleUpdateProductionTask}
                                      onDeleteTask={handleDeleteProductionTask}
                                      saveStatus={saveStatus}
                                    />;
      case 'install':      return <InstallTab
                                      wrapData={wrapData}
                                      onSaveInstall={handleSaveInstall}
                                      onSignoffToggle={handleInstallSignoffToggle}
                                      onChecklistToggle={handleInstallChecklistToggle}
                                      onAddIssue={handleAddInstallIssue}
                                      onUpdateIssue={handleUpdateInstallIssue}
                                      onDeleteIssue={handleDeleteInstallIssue}
                                      saveStatus={saveStatus}
                                    />;
      case 'photos':       return <PhotosFilesTab />;
      case 'aftercare':    return <AftercareTab
                                      wrapData={wrapData}
                                      onSaveAftercare={handleSaveAftercare}
                                      onToggleField={handleAftercareToggle}
                                      saveStatus={saveStatus}
                                    />;
      case 'ai':           return <AIAssistantTab wrapData={wrapData} onJumpToTab={setTab} />;
      default:             return <OverviewTab header={header} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20" data-testid="wrap-cc-loading">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="wrap-command-center-page">
      <WrapCommandHeader orderId={orderId} header={header} saveStatus={saveStatus} saveError={saveError} />
      <div className="px-4 sm:px-6 pt-3">
        <WrapStatusBar currentStatus={header.status} pipelineState={wrapData?.pipeline_state} testId="wrap-cc-status-bar" />
      </div>
      <WrapTabNavigation activeTab={tab} onChange={setTab} />
      <div className="px-4 sm:px-6 py-4">
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
          <div data-testid="wrap-cc-tab-content">
            {renderTab()}
          </div>
          <div className="hidden xl:block">
            <WrapSidebar header={header} />
          </div>
        </div>
      </div>
      <QuoteDraftModal open={quoteOpen} onClose={() => setQuoteOpen(false)} draft={quoteDraft} />
    </div>
  );
}
