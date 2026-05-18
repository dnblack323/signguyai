// Phase 2E: Deterministic wrap-summary helpers shared by OverviewTab and AIAssistantTab.
// No AI calls — pure rule-based derivation from wrap_data + order + customer.

export const PROFIT_MARGIN_WARNING_THRESHOLD = 30;

export function isVehicleComplete(v) {
  if (!v) return false;
  return !!(v.year && v.make && v.model);
}

export function getNextBestAction(wrapData) {
  if (!wrapData) return { label: 'Open Wrap Command Center', tab: 'overview' };
  const vehicle = wrapData.vehicle_info || {};
  const coverage = wrapData.coverage_summary || {};
  const snapshot = wrapData.pricing_snapshot;
  const contract = wrapData.contract || {};
  const design = wrapData.design || {};
  const approvals = wrapData.approvals || {};
  const inspection = wrapData.inspection || {};
  const production = wrapData.production || {};
  const install = wrapData.install || {};
  const aftercare = wrapData.aftercare || {};

  if (!isVehicleComplete(vehicle)) return { label: 'Complete Vehicle Info', tab: 'vehicle' };
  if ((coverage.included_count || 0) === 0) return { label: 'Add Measurements', tab: 'measurements' };
  if (!snapshot || !snapshot.quoted_price) return { label: 'Calculate Pricing', tab: 'pricing' };
  if (!(approvals.contract_signed || ['signed', 'stored'].includes(contract.contract_status))) {
    return { label: 'Send or Sign Contract', tab: 'contract' };
  }
  if (!(design.proof_status === 'approved' || approvals.proof_approved)) {
    return { label: 'Complete Design Proof Approval', tab: 'design' };
  }
  if (!(inspection.inspection_status === 'acknowledged' || approvals.inspection_acknowledged)) {
    return { label: 'Complete Vehicle Inspection', tab: 'inspection' };
  }
  if (!['ready_for_install', 'complete'].includes(production.production_status)) {
    return { label: 'Finish Production', tab: 'production' };
  }
  if (install.install_status !== 'complete' || !approvals.final_signoff_completed) {
    return { label: 'Complete Install', tab: 'install' };
  }
  if (!(aftercare.aftercare_sent || approvals.aftercare_sent)) {
    return { label: 'Send Aftercare', tab: 'aftercare' };
  }
  return { label: 'Wrap workflow complete', tab: 'overview' };
}

export function getMissingItems(wrapData) {
  if (!wrapData) return [];
  const out = [];
  const v = wrapData.vehicle_info || {};
  const coverage = wrapData.coverage_summary || {};
  const snapshot = wrapData.pricing_snapshot;
  const contract = wrapData.contract || {};
  const design = wrapData.design || {};
  const approvals = wrapData.approvals || {};
  const inspection = wrapData.inspection || {};
  const production = wrapData.production || {};
  const install = wrapData.install || {};
  const aftercare = wrapData.aftercare || {};

  if (!isVehicleComplete(v)) out.push('Vehicle info incomplete');
  if ((coverage.included_count || 0) === 0) out.push('No measurements');
  if (!snapshot || !snapshot.quoted_price) out.push('No pricing snapshot');
  if (!(contract.contract_status && contract.contract_status !== 'not_created' && contract.contract_status !== 'draft')) out.push('No contract sent');
  if (!(approvals.contract_signed || ['signed', 'stored'].includes(contract.contract_status))) out.push('Contract not signed');
  if (!(design.proof_status === 'approved' || approvals.proof_approved)) out.push('Proof not approved');
  if (!(inspection.inspection_status === 'acknowledged' || approvals.inspection_acknowledged)) out.push('Inspection not acknowledged');
  if (!['ready_for_install', 'complete'].includes(production.production_status)) out.push('Production not ready');
  if (install.install_status !== 'complete') out.push('Install not complete');
  if (!(aftercare.aftercare_sent || approvals.aftercare_sent)) out.push('Aftercare not sent');
  return out;
}

export function getProfitRisk(wrapData) {
  const snapshot = wrapData?.pricing_snapshot;
  if (!snapshot) return { level: 'unknown', message: 'No pricing snapshot available yet.' };
  const margin = Number(snapshot.estimated_margin_percent || 0);
  if (margin < PROFIT_MARGIN_WARNING_THRESHOLD) {
    return {
      level: 'warning',
      message: `Estimated margin appears low (${margin.toFixed(1)}%). Target ≥ ${PROFIT_MARGIN_WARNING_THRESHOLD}%.`,
      margin,
    };
  }
  return { level: 'ok', message: `Estimated margin healthy (${margin.toFixed(1)}%).`, margin };
}

export function getCommunicationSuggestions(wrapData) {
  if (!wrapData) return [];
  const out = [];
  const snapshot = wrapData.pricing_snapshot;
  const design = wrapData.design || {};
  const contract = wrapData.contract || {};
  const install = wrapData.install || {};
  const aftercare = wrapData.aftercare || {};

  if (snapshot && snapshot.quoted_price) out.push({ key: 'updated_quote', label: 'Send updated quote' });
  if (design.questionnaire_status === 'sent') out.push({ key: 'questionnaire_reminder', label: 'Send design questionnaire reminder' });
  if (contract.contract_status === 'sent') out.push({ key: 'contract_reminder', label: 'Send contract reminder' });
  if (install.install_date && install.install_status === 'scheduled') out.push({ key: 'install_reminder', label: 'Send install reminder' });
  if (aftercare.aftercare_sent && !aftercare.customer_acknowledged) out.push({ key: 'aftercare_followup', label: 'Send aftercare follow-up' });
  return out;
}
