// Phase 1: Wrap Command Center — shared constants
// Single source of truth for the wrap-category detection, status pipeline,
// tab list, and the seed placeholder data used until backend wiring lands.

// Order-item categories that should open the Wrap Command Center workflow.
// Matches existing PricingCategory enum values and a few user-facing labels.
export const WRAP_CATEGORIES = new Set([
  'vehicle_wrap',
  'vehicle_wraps',
  'wraps',
  'vehicle_graphics',
  'fleet_graphics',
  'trailer_wraps',
  'box_truck_wraps',
  'commercial_wraps',
  'vehicle_wraps_graphics',
]);

export const isWrapCategory = (category) => {
  if (!category) return false;
  const c = String(category).toLowerCase().replace(/\s+/g, '_').replace(/&/g, '_');
  return WRAP_CATEGORIES.has(c) || c.includes('wrap');
};

// Wrap workflow status pipeline — used by the status chips bar.
export const WRAP_PIPELINE = [
  'Lead', 'Estimate', 'Measurements', 'Quote Sent', 'Contract Sent',
  'Contract Signed', 'Deposit Paid', 'Design', 'Proof Sent', 'Approved',
  'Production', 'Inspection', 'Install', 'Aftercare', 'Complete',
];

// Tab definitions (id, label, icon imported in the navigation component)
export const WRAP_TABS = [
  { id: 'overview',     label: 'Overview' },
  { id: 'vehicle',      label: 'Vehicle Info' },
  { id: 'measurements', label: 'Measurements & Coverage' },
  { id: 'pricing',      label: 'Pricing & Materials' },
  { id: 'design',       label: 'Design & Mockups' },
  { id: 'contract',     label: 'Contract & Approvals' },
  { id: 'inspection',   label: 'Inspection' },
  { id: 'production',   label: 'Production' },
  { id: 'install',      label: 'Install' },
  { id: 'photos',       label: 'Photos & Files' },
  { id: 'aftercare',    label: 'Aftercare' },
  { id: 'ai',           label: 'AI Assistant' },
];

// Placeholder data used when backend fields aren't yet populated.
// Kept in one place so future phases can simply delete it and lean on the
// real order/item/customer values that already exist in scope.
export const PLACEHOLDER_HEADER = {
  order_number: 'Order #1048',
  customer_name: 'Keith Johnson',
  business_name: "Keith's Landscaping",
  item_name: '2022 Ford Transit Partial Commercial Wrap',
  vehicle: '2022 Ford Transit 250 High Roof',
  wrap_type: 'Partial Commercial Wrap',
  status: 'Design Pending',
  quoted_price: 3850,
  deposit_status: 'Pending',
  balance_due: 3850,
};

export const TOAST_PHASE1 = 'This feature will be completed in a later phase.';
export const TOAST_AI_PHASE1 = 'AI feature will be connected in a later phase.';
