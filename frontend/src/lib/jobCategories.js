/**
 * Single source of truth for Job Ticket / Order Item categories.
 * Values MUST match backend `JobTicketCategory` enum in `models/orders.py`.
 * M7: consolidates what used to live in NewOrderForm.js and CloneItemDialog.js.
 */

export const JOB_CATEGORIES = [
  { value: 'banners', label: 'Banners' },
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'cut_vinyl', label: 'Cut Vinyl / Lettering' },
  { value: 'digital_print', label: 'Digital Print' },
  { value: 'vehicle_wrap', label: 'Vehicle Wrap' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'services', label: 'Services' },
  { value: 'promo_misc', label: 'Promotional / Misc' },
  { value: 'custom', label: 'Custom' },
];

export const JOB_CATEGORY_VALUES = JOB_CATEGORIES.map((c) => c.value);

export const JOB_CATEGORY_LABEL_BY_VALUE = JOB_CATEGORIES.reduce((acc, c) => {
  acc[c.value] = c.label;
  return acc;
}, {});
