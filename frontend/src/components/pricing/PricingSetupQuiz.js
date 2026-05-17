// Phase 6: Guided Pricing Setup Quiz
// Optional wizard that asks shop owners real-world price questions and converts
// the answers into suggested Pricing Foundation defaults. Nothing is saved
// automatically — the user reviews each suggestion and clicks
// "Apply Selected Defaults" before any settings are mutated.

import { useMemo, useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader,
  DialogTitle, DialogFooter,
} from '../ui/dialog';
import {
  Sparkles, ChevronLeft, ChevronRight, CheckCircle2, AlertCircle, X,
} from 'lucide-react';
import { toast } from 'sonner';

// ─────────── Quiz definition ───────────
// One section per category. Each question has:
//   key      — unique id used to look up the answer
//   label    — what the shop owner reads
//   prefix   — usually '$'; '' for percent/integer fields
//   suffix   — '/each', '%', etc.
//   help     — short helper text
//   type     — 'number' (default) or 'bool'
const SECTIONS = [
  {
    key: 'shop_basics',
    title: 'Shop Basics',
    description: 'Your hourly rates, minimums, and target margin.',
    questions: [
      { key: 'design_hourly_rate',     label: 'Design hourly rate',     prefix: '$', suffix: '/hr', help: 'What you charge per hour of graphic design work.' },
      { key: 'production_hourly_rate', label: 'Production hourly rate', prefix: '$', suffix: '/hr', help: 'Shop floor production labor (printing, weeding, finishing).' },
      { key: 'install_hourly_rate',    label: 'Install hourly rate',    prefix: '$', suffix: '/hr', help: 'Field installation labor.' },
      { key: 'target_profit_margin_percent', label: 'Target profit margin', prefix: '', suffix: '%', help: 'The profit % you want on most jobs.' },
      { key: 'minimum_order',          label: 'Minimum order amount',   prefix: '$', suffix: '/order', help: 'Smallest order you accept.' },
      { key: 'deposit_required',       label: 'Do you require a deposit?', type: 'bool' },
      { key: 'deposit_percentage',     label: 'Deposit %', prefix: '', suffix: '%', help: 'Only if you require a deposit.' },
    ],
  },
  {
    key: 'banners',
    title: 'Banners',
    description: 'Standard 13oz vinyl banners with hems and grommets.',
    questions: [
      { key: 'banner_2x4', label: '2ft × 4ft banner price',  prefix: '$', suffix: '/each', help: '8 sqft, hems + grommets.' },
      { key: 'banner_3x6', label: '3ft × 6ft banner price',  prefix: '$', suffix: '/each', help: '18 sqft.' },
      { key: 'banner_4x8', label: '4ft × 8ft banner price',  prefix: '$', suffix: '/each', help: '32 sqft.' },
      { key: 'banner_finishing_included', label: 'Are hems and grommets usually included?', type: 'bool' },
    ],
  },
  {
    key: 'yard_signs',
    title: 'Yard Signs / Coroplast',
    description: '18in × 24in single-sided coroplast yard signs.',
    questions: [
      { key: 'yard_qty_1',  label: 'Price for 1 yard sign',     prefix: '$', suffix: '/each' },
      { key: 'yard_qty_10', label: 'Price for 10 yard signs',   prefix: '$', suffix: '/each' },
      { key: 'yard_qty_25', label: 'Price for 25 yard signs',   prefix: '$', suffix: '/each' },
      { key: 'yard_qty_50', label: 'Price for 50 yard signs',   prefix: '$', suffix: '/each' },
      { key: 'yard_stakes_included', label: 'Are stakes included?', type: 'bool' },
    ],
  },
  {
    key: 'rigid_signs',
    title: 'Rigid Signs',
    description: 'Standard substrates with direct-print or applied vinyl.',
    questions: [
      { key: 'rigid_coroplast_4x4',  label: '4ft × 4ft coroplast sign',     prefix: '$', suffix: '/each' },
      { key: 'rigid_coroplast_4x8',  label: '4ft × 8ft coroplast sign',     prefix: '$', suffix: '/each' },
      { key: 'rigid_acm_4x8',        label: '4ft × 8ft ACM / composite',    prefix: '$', suffix: '/each' },
      { key: 'rigid_pvc_4x8',        label: '4ft × 8ft PVC sign',           prefix: '$', suffix: '/each' },
    ],
  },
  {
    key: 'cut_vinyl',
    title: 'Cut Vinyl',
    description: 'Plotter-cut decals — one color unless noted.',
    questions: [
      { key: 'cv_12x24_one_color',   label: '12in × 24in one-color decal',  prefix: '$', suffix: '/each' },
      { key: 'cv_24x36_one_color',   label: '24in × 36in one-color decal',  prefix: '$', suffix: '/each' },
      { key: 'cv_24x36_two_color',   label: '24in × 36in two-color decal',  prefix: '$', suffix: '/each' },
      { key: 'cv_minimum_charge',    label: 'Minimum vinyl decal charge',   prefix: '$', suffix: '/order' },
    ],
  },
  {
    key: 'digital_print',
    title: 'Digital Print',
    description: 'Printed adhesive / paper / panels.',
    questions: [
      { key: 'dp_24x36_poster',           label: '24in × 36in poster',                prefix: '$', suffix: '/each' },
      { key: 'dp_24x36_adhesive',         label: '24in × 36in adhesive print',        prefix: '$', suffix: '/each' },
      { key: 'dp_24x36_adhesive_lam',     label: '24in × 36in laminated adhesive',    prefix: '$', suffix: '/each' },
      { key: 'dp_4x8_panel',              label: '4ft × 8ft printed panel',           prefix: '$', suffix: '/each' },
    ],
  },
  {
    key: 'vehicle_graphics',
    title: 'Vehicle Graphics',
    description: 'Door lettering up to full vehicle wraps.',
    questions: [
      { key: 'vg_door_lettering',     label: 'Basic pickup door lettering',     prefix: '$', suffix: '/job' },
      { key: 'vg_spot_van',           label: 'Spot graphics on a van',          prefix: '$', suffix: '/job' },
      { key: 'vg_partial_wrap',       label: 'Partial wrap on a cargo van',     prefix: '$', suffix: '/job' },
      { key: 'vg_full_wrap',          label: 'Full wrap on a cargo van',        prefix: '$', suffix: '/job' },
      { key: 'vg_print_sqft_rate',    label: 'Printed wrap sell rate',          prefix: '$', suffix: '/sqft' },
      { key: 'vg_color_change_sqft',  label: 'Color-change wrap sell rate',     prefix: '$', suffix: '/sqft' },
    ],
  },
  {
    key: 'apparel',
    title: 'Apparel',
    description: 'T-shirts and hoodies with one-color heat transfer.',
    questions: [
      { key: 'ap_tee_qty_12_one_side', label: '12 × one-sided T-shirts (per shirt)',  prefix: '$', suffix: '/each' },
      { key: 'ap_tee_qty_24_one_side', label: '24 × one-sided T-shirts (per shirt)',  prefix: '$', suffix: '/each' },
      { key: 'ap_tee_qty_12_two_side', label: '12 × front-and-back T-shirts (per shirt)', prefix: '$', suffix: '/each' },
      { key: 'ap_blank_cost',          label: 'Average blank shirt cost',             prefix: '$', suffix: '/each' },
      { key: 'ap_decoration_cost',     label: 'Average transfer / decorating cost',   prefix: '$', suffix: '/each' },
      { key: 'ap_hoodie_each',         label: 'Hoodie price (per piece)',             prefix: '$', suffix: '/each' },
    ],
  },
  {
    key: 'services',
    title: 'Services',
    description: 'Hourly rates and minimum service charges.',
    questions: [
      { key: 'svc_design_rate',       label: 'Design rate',                     prefix: '$', suffix: '/hr', help: 'Same as Shop Basics if already answered.' },
      { key: 'svc_production_rate',   label: 'Production rate',                 prefix: '$', suffix: '/hr' },
      { key: 'svc_install_rate',      label: 'Install rate',                    prefix: '$', suffix: '/hr' },
      { key: 'svc_min_design',        label: 'Minimum design charge',           prefix: '$', suffix: '/job' },
      { key: 'svc_min_install',       label: 'Minimum install charge',          prefix: '$', suffix: '/job' },
    ],
  },
  {
    key: 'promotional_custom',
    title: 'Promotional / Custom',
    description: 'Outsourced and vendor work.',
    questions: [
      { key: 'pc_vendor_markup_percent', label: 'Markup on outsourced items', prefix: '', suffix: '%' },
      { key: 'pc_min_setup_fee',         label: 'Minimum setup fee',          prefix: '$', suffix: '/job' },
      { key: 'pc_min_order',             label: 'Minimum order amount',       prefix: '$', suffix: '/order' },
    ],
  },
];

// ─────────── Helpers ───────────
const sqftFromBanner = (W, H) => W * H; // ft × ft
const inToSqft = (W, H) => (W * H) / 144;
const avg = (...xs) => {
  const vals = xs.filter((v) => typeof v === 'number' && Number.isFinite(v) && v > 0);
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
};
const r2 = (n) => Math.round(Number(n) * 100) / 100;
const r1 = (n) => Math.round(Number(n) * 10) / 10;
const num = (v) => {
  const n = parseFloat(v);
  return Number.isFinite(n) && n > 0 ? n : null;
};

// Returns the current value of a path inside the settings object, supporting
// nested paths like ["category_defaults", "banners", "sell_rate_defaults", "base_rate"].
function getPath(obj, path) {
  let cur = obj;
  for (const p of path) {
    if (cur == null) return undefined;
    cur = cur[p];
  }
  return cur;
}

// Applies updates to a fresh deep-cloned settings object.
function applySuggestions(settings, suggestions) {
  const next = JSON.parse(JSON.stringify(settings || {}));
  if (!next.category_defaults) next.category_defaults = {};
  for (const s of suggestions) {
    if (!s.apply) continue;
    let cur = next;
    for (let i = 0; i < s.path.length - 1; i++) {
      const key = s.path[i];
      if (cur[key] == null || typeof cur[key] !== 'object') cur[key] = {};
      cur = cur[key];
    }
    cur[s.path[s.path.length - 1]] = s.suggestedValue;
  }
  return next;
}

// ─────────── Conversion logic ───────────
// Every suggestion has:
//   - id            (unique)
//   - field         (human-readable target field name)
//   - path          (array path inside the settings object)
//   - sourceAnswer  (human string explaining where this came from)
//   - suggestedValue
//   - confidence    'high' | 'review'  ('review' means "Review recommended" — auto-deselected)
//   - section       (for grouping in the review screen)
function buildSuggestions(answers) {
  const out = [];
  const add = (s) => out.push({ apply: s.confidence === 'high', ...s });

  // ── Shop Basics ──
  const design = num(answers.design_hourly_rate);
  const prod = num(answers.production_hourly_rate);
  const install = num(answers.install_hourly_rate);
  const margin = num(answers.target_profit_margin_percent);
  const minOrder = num(answers.minimum_order);
  const deposit = num(answers.deposit_percentage);
  const depReq = answers.deposit_required;

  if (design) add({
    id: 'shop_design_rate', field: 'Design hourly rate',
    path: ['design_hourly_rate'], suggestedValue: r2(design),
    sourceAnswer: `Design rate: $${design}/hr`,
    confidence: 'high', section: 'Shop Basics',
  });
  if (prod) add({
    id: 'shop_prod_rate', field: 'Production hourly rate',
    path: ['production_hourly_rate'], suggestedValue: r2(prod),
    sourceAnswer: `Production rate: $${prod}/hr`,
    confidence: 'high', section: 'Shop Basics',
  });
  if (install) add({
    id: 'shop_install_rate', field: 'Install hourly rate',
    path: ['install_hourly_rate'], suggestedValue: r2(install),
    sourceAnswer: `Install rate: $${install}/hr`,
    confidence: 'high', section: 'Shop Basics',
  });
  if (margin) add({
    id: 'shop_target_margin', field: 'Target profit margin %',
    path: ['target_profit_margin_percent'], suggestedValue: r1(margin),
    sourceAnswer: `Target margin: ${margin}%`,
    confidence: 'high', section: 'Shop Basics',
  });
  if (minOrder) add({
    id: 'shop_min_order', field: 'Minimum order amount',
    path: ['minimum_order'], suggestedValue: r2(minOrder),
    sourceAnswer: `Minimum order: $${minOrder}`,
    confidence: 'high', section: 'Shop Basics',
  });
  if (depReq === true && deposit) add({
    id: 'shop_deposit_pct', field: 'Deposit %',
    path: ['deposit_percentage'], suggestedValue: r1(deposit),
    sourceAnswer: `Deposit required: ${deposit}%`,
    confidence: 'high', section: 'Shop Basics',
  });

  // ── Banners ──
  // Sell rate per sqft averaged across whatever the shop answered.
  // Conservative: use the AVERAGE rather than the min, but mark 'review' if
  // only one size was answered.
  const b2x4 = num(answers.banner_2x4);
  const b3x6 = num(answers.banner_3x6);
  const b4x8 = num(answers.banner_4x8);
  const bRates = [
    b2x4 ? b2x4 / sqftFromBanner(2, 4) : null,
    b3x6 ? b3x6 / sqftFromBanner(3, 6) : null,
    b4x8 ? b4x8 / sqftFromBanner(4, 8) : null,
  ];
  const bannerRate = avg(...bRates);
  if (bannerRate) {
    const answered = bRates.filter((x) => x != null).length;
    add({
      id: 'banner_sell_rate', field: 'Banners — base sell rate / sqft',
      path: ['category_defaults', 'banners', 'sell_rate_defaults', 'base_rate'],
      suggestedValue: r2(bannerRate),
      sourceAnswer: `Avg of ${answered} banner price answer${answered === 1 ? '' : 's'}: $${r2(bannerRate)}/sqft`,
      confidence: answered >= 2 ? 'high' : 'review',
      section: 'Banners',
    });
  }
  // Smallest banner price → minimum sell price floor
  const minBanner = [b2x4, b3x6, b4x8].filter((x) => x != null).sort((a, b) => a - b)[0];
  if (minBanner) add({
    id: 'banner_min_sell', field: 'Banners — minimum sell price / item',
    path: ['category_defaults', 'banners', 'default_minimum_sell_price'],
    suggestedValue: r2(minBanner),
    sourceAnswer: `Smallest banner answer: $${minBanner}`,
    confidence: 'review',
    section: 'Banners',
  });

  // ── Yard signs / Coroplast (4ft x 4ft coroplast — derived from per-piece prices) ──
  const y1 = num(answers.yard_qty_1);
  const y10 = num(answers.yard_qty_10);
  const y25 = num(answers.yard_qty_25);
  const y50 = num(answers.yard_qty_50);
  // 18 × 24 in = 3 sqft. Take the qty-25 (or 10, or 50) price as a stable sell rate.
  const yMid = y25 || y10 || y50 || y1;
  if (yMid) {
    const rate = yMid / inToSqft(18, 24); // $ / sqft
    add({
      id: 'rigid_yard_rate', field: 'Rigid signs — yard sign sell rate / sqft',
      path: ['category_defaults', 'rigid_signs', 'sell_rate_defaults', 'yard_sign_rate'],
      suggestedValue: r2(rate),
      sourceAnswer: `Yard sign answer ÷ 3 sqft = $${r2(rate)}/sqft (mid-qty)`,
      confidence: 'review',
      section: 'Yard Signs / Coroplast',
    });
  }
  if (y1) add({
    id: 'rigid_yard_single_min', field: 'Rigid signs — minimum sell / item (qty 1 floor)',
    path: ['category_defaults', 'rigid_signs', 'default_minimum_sell_price'],
    suggestedValue: r2(y1),
    sourceAnswer: `Single yard sign answer: $${y1}`,
    confidence: 'review',
    section: 'Yard Signs / Coroplast',
  });
  // Quantity discounts derived from yard-sign tier prices.
  if (y1 && y10 && y10 < y1) {
    const pct = Math.max(0, Math.min(50, Math.round((1 - y10 / y1) * 100)));
    add({
      id: 'rigid_qty_10', field: 'Rigid signs — qty 10 discount %',
      path: ['category_defaults', 'rigid_signs', 'quantity_breaks', 'qty_10_percent'],
      suggestedValue: pct,
      sourceAnswer: `Qty 10 vs qty 1: ${pct}% off`,
      confidence: 'review',
      section: 'Yard Signs / Coroplast',
    });
  }
  if (y1 && y25 && y25 < y1) {
    const pct = Math.max(0, Math.min(60, Math.round((1 - y25 / y1) * 100)));
    add({
      id: 'rigid_qty_25', field: 'Rigid signs — qty 25 discount %',
      path: ['category_defaults', 'rigid_signs', 'quantity_breaks', 'qty_25_percent'],
      suggestedValue: pct,
      sourceAnswer: `Qty 25 vs qty 1: ${pct}% off`,
      confidence: 'review',
      section: 'Yard Signs / Coroplast',
    });
  }

  // ── Rigid Signs ──
  const rc44 = num(answers.rigid_coroplast_4x4);
  const rc48 = num(answers.rigid_coroplast_4x8);
  const ra48 = num(answers.rigid_acm_4x8);
  const rp48 = num(answers.rigid_pvc_4x8);
  // 4x4 = 16 sqft; 4x8 = 32 sqft
  const rRates = [
    rc44 ? rc44 / 16 : null,
    rc48 ? rc48 / 32 : null,
    ra48 ? ra48 / 32 : null,
    rp48 ? rp48 / 32 : null,
  ];
  const rRate = avg(...rRates);
  if (rRate) {
    const answered = rRates.filter((x) => x != null).length;
    add({
      id: 'rigid_sell_rate', field: 'Rigid signs — base sell rate / sqft',
      path: ['category_defaults', 'rigid_signs', 'sell_rate_defaults', 'base_rate'],
      suggestedValue: r2(rRate),
      sourceAnswer: `Avg of ${answered} rigid sign answer${answered === 1 ? '' : 's'}: $${r2(rRate)}/sqft`,
      confidence: answered >= 2 ? 'high' : 'review',
      section: 'Rigid Signs',
    });
  }

  // ── Cut Vinyl ──
  const cv1x = num(answers.cv_12x24_one_color);
  const cv2x = num(answers.cv_24x36_one_color);
  const cv2x2c = num(answers.cv_24x36_two_color);
  const cvMin = num(answers.cv_minimum_charge);
  const cvRates = [
    cv1x ? cv1x / inToSqft(12, 24) : null,
    cv2x ? cv2x / inToSqft(24, 36) : null,
    cv2x2c ? cv2x2c / inToSqft(24, 36) / 2 : null, // half because two-color = 2 layers
  ];
  const cvRate = avg(...cvRates);
  if (cvRate) {
    const answered = cvRates.filter((x) => x != null).length;
    add({
      id: 'cv_sell_rate', field: 'Cut Vinyl — base sell rate / sqft',
      path: ['category_defaults', 'cut_vinyl', 'sell_rate_defaults', 'base_rate'],
      suggestedValue: r2(cvRate),
      sourceAnswer: `Avg of ${answered} cut vinyl answer${answered === 1 ? '' : 's'}: $${r2(cvRate)}/sqft`,
      confidence: answered >= 2 ? 'high' : 'review',
      section: 'Cut Vinyl',
    });
  }
  if (cvMin) add({
    id: 'cv_min_charge', field: 'Cut Vinyl — minimum charge / item',
    path: ['category_defaults', 'cut_vinyl', 'default_minimum_sell_price'],
    suggestedValue: r2(cvMin),
    sourceAnswer: `Minimum vinyl decal charge: $${cvMin}`,
    confidence: 'high',
    section: 'Cut Vinyl',
  });

  // ── Digital Print ──
  const dp_p = num(answers.dp_24x36_poster);
  const dp_a = num(answers.dp_24x36_adhesive);
  const dp_al = num(answers.dp_24x36_adhesive_lam);
  const dp_pn = num(answers.dp_4x8_panel);
  const dpRates = [
    dp_p ? dp_p / inToSqft(24, 36) : null,
    dp_a ? dp_a / inToSqft(24, 36) : null,
    dp_pn ? dp_pn / 32 : null,
  ];
  const dpRate = avg(...dpRates);
  if (dpRate) {
    const answered = dpRates.filter((x) => x != null).length;
    add({
      id: 'dp_sell_rate', field: 'Digital Print — base sell rate / sqft',
      path: ['category_defaults', 'digital_print', 'sell_rate_defaults', 'base_rate'],
      suggestedValue: r2(dpRate),
      sourceAnswer: `Avg of ${answered} digital print answer${answered === 1 ? '' : 's'}: $${r2(dpRate)}/sqft`,
      confidence: answered >= 2 ? 'high' : 'review',
      section: 'Digital Print',
    });
  }
  if (dp_al && dp_a && dp_al > dp_a) {
    const lamPerSqft = (dp_al - dp_a) / inToSqft(24, 36);
    add({
      id: 'dp_lam_addon', field: 'Digital Print — laminate sell add-on / sqft',
      path: ['category_defaults', 'digital_print', 'sell_rate_defaults', 'laminate_addon_per_sqft'],
      suggestedValue: r2(lamPerSqft),
      sourceAnswer: `(Laminated $${dp_al} − adhesive $${dp_a}) ÷ 6 sqft = $${r2(lamPerSqft)}/sqft`,
      confidence: 'review',
      section: 'Digital Print',
    });
  }

  // ── Vehicle Graphics ──
  const vgPrintRate = num(answers.vg_print_sqft_rate);
  const vgColorRate = num(answers.vg_color_change_sqft);
  if (vgPrintRate) add({
    id: 'vg_print_rate', field: 'Vehicle Graphics — printed wrap sell rate / sqft',
    path: ['category_defaults', 'vehicle_graphics', 'sell_rate_defaults', 'printed_wrap_per_sqft'],
    suggestedValue: r2(vgPrintRate),
    sourceAnswer: `Printed wrap rate: $${vgPrintRate}/sqft`,
    confidence: 'high', section: 'Vehicle Graphics',
  });
  if (vgColorRate) add({
    id: 'vg_color_rate', field: 'Vehicle Graphics — color-change wrap sell rate / sqft',
    path: ['category_defaults', 'vehicle_graphics', 'sell_rate_defaults', 'color_change_per_sqft'],
    suggestedValue: r2(vgColorRate),
    sourceAnswer: `Color-change rate: $${vgColorRate}/sqft`,
    confidence: 'high', section: 'Vehicle Graphics',
  });
  // Door lettering / spot / partial / full → benchmark package prices (review only)
  const vgDoor = num(answers.vg_door_lettering);
  const vgSpot = num(answers.vg_spot_van);
  const vgPart = num(answers.vg_partial_wrap);
  const vgFull = num(answers.vg_full_wrap);
  [
    ['vg_door',    vgDoor, 'package_door_lettering', 'Door lettering benchmark'],
    ['vg_spot',    vgSpot, 'package_spot_graphics',  'Spot graphics benchmark'],
    ['vg_partial', vgPart, 'package_partial_wrap',   'Partial wrap benchmark'],
    ['vg_full',    vgFull, 'package_full_wrap',      'Full wrap benchmark'],
  ].forEach(([id, v, key, label]) => {
    if (v) add({
      id, field: `Vehicle Graphics — ${label}`,
      path: ['category_defaults', 'vehicle_graphics', 'benchmarks', key],
      suggestedValue: r2(v),
      sourceAnswer: `${label}: $${v}`,
      confidence: 'review',
      section: 'Vehicle Graphics',
    });
  });

  // ── Apparel — quantity tier suggestions (sell prices per piece) ──
  const ap12_1 = num(answers.ap_tee_qty_12_one_side);
  const ap24_1 = num(answers.ap_tee_qty_24_one_side);
  const apBlank = num(answers.ap_blank_cost);
  const apDeco = num(answers.ap_decoration_cost);
  const apHoodie = num(answers.ap_hoodie_each);
  if (ap12_1) add({
    id: 'apparel_tier_12', field: 'Apparel — tier 12 sell price (1-side tee)',
    path: ['category_defaults', 'apparel', 'shop_pricing_table', 'tee_one_side', 'qty_12'],
    suggestedValue: r2(ap12_1),
    sourceAnswer: `12 one-side tees: $${ap12_1}/each`,
    confidence: 'review', section: 'Apparel',
  });
  if (ap24_1) add({
    id: 'apparel_tier_24', field: 'Apparel — tier 24 sell price (1-side tee)',
    path: ['category_defaults', 'apparel', 'shop_pricing_table', 'tee_one_side', 'qty_24'],
    suggestedValue: r2(ap24_1),
    sourceAnswer: `24 one-side tees: $${ap24_1}/each`,
    confidence: 'review', section: 'Apparel',
  });
  if (apBlank) add({
    id: 'apparel_blank_cost', field: 'Apparel — average blank shirt cost',
    path: ['category_defaults', 'apparel', 'default_blank_cost'],
    suggestedValue: r2(apBlank),
    sourceAnswer: `Average blank cost: $${apBlank}`,
    confidence: 'high', section: 'Apparel',
  });
  if (apDeco) add({
    id: 'apparel_deco_cost', field: 'Apparel — average decoration cost',
    path: ['category_defaults', 'apparel', 'default_decoration_cost'],
    suggestedValue: r2(apDeco),
    sourceAnswer: `Average decoration cost: $${apDeco}`,
    confidence: 'high', section: 'Apparel',
  });
  if (apHoodie) add({
    id: 'apparel_hoodie_each', field: 'Apparel — hoodie sell price (1-side, mid qty)',
    path: ['category_defaults', 'apparel', 'shop_pricing_table', 'hoodie_one_side', 'qty_24'],
    suggestedValue: r2(apHoodie),
    sourceAnswer: `Hoodie price: $${apHoodie}/each`,
    confidence: 'review', section: 'Apparel',
  });

  // ── Services ──
  const sd = num(answers.svc_design_rate);
  const sp = num(answers.svc_production_rate);
  const si = num(answers.svc_install_rate);
  const smd = num(answers.svc_min_design);
  const smi = num(answers.svc_min_install);
  if (sd) add({
    id: 'svc_design_rate', field: 'Services — design rate',
    path: ['category_defaults', 'services', 'labor_rate_overrides', 'design'],
    suggestedValue: r2(sd),
    sourceAnswer: `Service design rate: $${sd}/hr`,
    confidence: 'high', section: 'Services',
  });
  if (sp) add({
    id: 'svc_prod_rate', field: 'Services — production rate',
    path: ['category_defaults', 'services', 'labor_rate_overrides', 'production'],
    suggestedValue: r2(sp),
    sourceAnswer: `Service production rate: $${sp}/hr`,
    confidence: 'high', section: 'Services',
  });
  if (si) add({
    id: 'svc_install_rate', field: 'Services — install rate',
    path: ['category_defaults', 'services', 'labor_rate_overrides', 'install'],
    suggestedValue: r2(si),
    sourceAnswer: `Service install rate: $${si}/hr`,
    confidence: 'high', section: 'Services',
  });
  if (smd) add({
    id: 'svc_min_design', field: 'Services — minimum design charge',
    path: ['category_defaults', 'services', 'minimums', 'design'],
    suggestedValue: r2(smd),
    sourceAnswer: `Minimum design charge: $${smd}`,
    confidence: 'high', section: 'Services',
  });
  if (smi) add({
    id: 'svc_min_install', field: 'Services — minimum install charge',
    path: ['category_defaults', 'services', 'minimums', 'install'],
    suggestedValue: r2(smi),
    sourceAnswer: `Minimum install charge: $${smi}`,
    confidence: 'high', section: 'Services',
  });

  // ── Promotional / Custom ──
  const pcMarkup = num(answers.pc_vendor_markup_percent);
  const pcSetup = num(answers.pc_min_setup_fee);
  const pcMin = num(answers.pc_min_order);
  if (pcMarkup) {
    const mult = 1 + pcMarkup / 100;
    add({
      id: 'pc_markup', field: 'Promotional — default markup multiplier',
      path: ['category_defaults', 'promotional', 'default_markup_multiplier'],
      suggestedValue: r2(mult),
      sourceAnswer: `${pcMarkup}% markup → ×${r2(mult)}`,
      confidence: 'high', section: 'Promotional / Custom',
    });
    add({
      id: 'pc_markup_custom', field: 'Custom — default markup multiplier',
      path: ['category_defaults', 'custom', 'default_markup_multiplier'],
      suggestedValue: r2(mult),
      sourceAnswer: `${pcMarkup}% markup → ×${r2(mult)}`,
      confidence: 'high', section: 'Promotional / Custom',
    });
  }
  if (pcSetup) add({
    id: 'pc_setup', field: 'Promotional — minimum setup fee',
    path: ['category_defaults', 'promotional', 'minimum_setup_fee'],
    suggestedValue: r2(pcSetup),
    sourceAnswer: `Minimum setup fee: $${pcSetup}`,
    confidence: 'high', section: 'Promotional / Custom',
  });
  if (pcMin) add({
    id: 'pc_min', field: 'Promotional / Custom — minimum order',
    path: ['category_defaults', 'promotional', 'minimum_charge'],
    suggestedValue: r2(pcMin),
    sourceAnswer: `Minimum order: $${pcMin}`,
    confidence: 'high', section: 'Promotional / Custom',
  });

  return out;
}

// ─────────── Subcomponents ───────────
function QuestionRow({ q, value, onChange }) {
  if (q.type === 'bool') {
    return (
      <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg" data-testid={`quiz-q-${q.key}`}>
        <div>
          <Label className="text-sm">{q.label}</Label>
          {q.help && <p className="text-xs text-slate-500 mt-0.5">{q.help}</p>}
        </div>
        <Switch
          checked={!!value}
          onCheckedChange={(v) => onChange(q.key, v)}
          data-testid={`quiz-bool-${q.key}`}
        />
      </div>
    );
  }
  return (
    <div className="p-3 bg-slate-50 rounded-lg" data-testid={`quiz-q-${q.key}`}>
      <Label className="text-sm">{q.label}</Label>
      {q.help && <p className="text-xs text-slate-500 mt-0.5 mb-1.5">{q.help}</p>}
      <div className="mt-1.5 flex items-center gap-2">
        {q.prefix && <span className="text-sm text-slate-500">{q.prefix}</span>}
        <Input
          type="number"
          inputMode="decimal"
          placeholder="Skip if unsure"
          value={value ?? ''}
          onChange={(e) => onChange(q.key, e.target.value === '' ? '' : parseFloat(e.target.value))}
          className="h-9 max-w-[160px]"
          data-testid={`quiz-input-${q.key}`}
        />
        {q.suffix && <span className="text-xs text-slate-500">{q.suffix}</span>}
      </div>
    </div>
  );
}

function SuggestionRow({ s, currentValue, onToggle }) {
  const same = currentValue != null && Number(currentValue) === Number(s.suggestedValue);
  return (
    <div
      className={`grid grid-cols-12 gap-2 items-center p-2 rounded ${s.apply ? 'bg-violet-50' : 'bg-slate-50'}`}
      data-testid={`quiz-suggestion-${s.id}`}
    >
      <div className="col-span-4">
        <p className="text-sm font-medium text-slate-800">{s.field}</p>
        <p className="text-xs text-slate-500">{s.sourceAnswer}</p>
      </div>
      <div className="col-span-2 text-xs text-slate-600">
        <span className="text-slate-500">Current: </span>
        {currentValue != null && currentValue !== '' ? String(currentValue) : '—'}
      </div>
      <div className="col-span-2 text-xs">
        <span className="text-slate-500">Suggested: </span>
        <span className="font-medium text-slate-800">{s.suggestedValue}</span>
      </div>
      <div className="col-span-2">
        {s.confidence === 'review' ? (
          <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
            <AlertCircle className="h-3 w-3" /> Review recommended
          </span>
        ) : same ? (
          <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
            Already set
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-800">
            <CheckCircle2 className="h-3 w-3" /> Recommended
          </span>
        )}
      </div>
      <div className="col-span-2 flex justify-end">
        <Switch
          checked={s.apply}
          onCheckedChange={(v) => onToggle(s.id, v)}
          data-testid={`quiz-suggestion-toggle-${s.id}`}
        />
      </div>
    </div>
  );
}

// ─────────── Main quiz component ───────────
export default function PricingSetupQuiz({ open, onClose, settings, onApply }) {
  const [step, setStep] = useState(0); // 0..SECTIONS.length-1 = question pages; SECTIONS.length = review
  const [answers, setAnswers] = useState({});
  const [suggestions, setSuggestions] = useState([]);

  const onReview = step === SECTIONS.length;
  const total = SECTIONS.length;

  const updateAnswer = (key, value) => setAnswers((a) => ({ ...a, [key]: value }));
  const toggleSuggestion = (id, value) =>
    setSuggestions((arr) => arr.map((s) => (s.id === id ? { ...s, apply: value } : s)));

  const goNext = () => {
    if (step < total - 1) {
      setStep(step + 1);
    } else {
      // moving from last question into review — compute suggestions
      setSuggestions(buildSuggestions(answers));
      setStep(total);
    }
  };
  const goPrev = () => {
    if (step > 0) setStep(step - 1);
  };

  const applySelected = () => {
    const selected = suggestions.filter((s) => s.apply);
    if (selected.length === 0) {
      toast.message('No defaults selected to apply.');
      return;
    }
    const next = applySuggestions(settings, suggestions);
    onApply(next, selected);
    toast.success(`Applied ${selected.length} suggested default${selected.length === 1 ? '' : 's'}. Remember to click "Save All".`);
    onClose();
    // reset for next session
    setStep(0);
    setAnswers({});
    setSuggestions([]);
  };

  const resetAndClose = () => {
    setStep(0);
    setAnswers({});
    setSuggestions([]);
    onClose();
  };

  const groupedSuggestions = useMemo(() => {
    const grouped = {};
    for (const s of suggestions) {
      if (!grouped[s.section]) grouped[s.section] = [];
      grouped[s.section].push(s);
    }
    return grouped;
  }, [suggestions]);

  const currentSection = SECTIONS[step];

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) resetAndClose(); }}>
      <DialogContent
        className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        data-testid="pricing-setup-quiz-dialog"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-600" />
            Pricing Setup Quiz
            <span className="text-xs font-normal text-slate-500 ml-auto">
              {onReview ? 'Review' : `Step ${step + 1} of ${total}`}
            </span>
          </DialogTitle>
          <DialogDescription>
            {onReview
              ? 'Review the suggested defaults below. Toggle off any you do not want. Nothing changes until you click "Apply Selected Defaults".'
              : 'Answer the prices you would charge — skip any question you are unsure about.'}
          </DialogDescription>
        </DialogHeader>

        {/* Progress dots */}
        <div className="flex items-center gap-1 mb-2">
          {SECTIONS.map((s, i) => (
            <div
              key={s.key}
              className={`h-1.5 flex-1 rounded ${
                i < step ? 'bg-violet-500' : i === step ? 'bg-violet-300' : 'bg-slate-200'
              }`}
            />
          ))}
          <div className={`h-1.5 w-4 rounded ${onReview ? 'bg-violet-500' : 'bg-slate-200'}`} title="Review" />
        </div>

        <div className="flex-1 overflow-y-auto pr-1">
          {!onReview && currentSection && (
            <div className="space-y-3" data-testid={`quiz-section-${currentSection.key}`}>
              <div>
                <h3 className="text-base font-semibold text-slate-800">{currentSection.title}</h3>
                <p className="text-xs text-slate-500">{currentSection.description}</p>
              </div>
              <div className="space-y-2">
                {currentSection.questions.map((q) => (
                  <QuestionRow key={q.key} q={q} value={answers[q.key]} onChange={updateAnswer} />
                ))}
              </div>
            </div>
          )}

          {onReview && (
            <div className="space-y-4" data-testid="quiz-review-screen">
              {suggestions.length === 0 ? (
                <div className="p-6 text-center text-slate-500" data-testid="quiz-review-empty">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                  No suggestions to apply — looks like all questions were skipped.
                  Go back and answer the ones you want to use, or close the quiz.
                </div>
              ) : (
                Object.entries(groupedSuggestions).map(([section, items]) => (
                  <div key={section} data-testid={`quiz-review-section-${section.replace(/\W+/g, '_').toLowerCase()}`}>
                    <h4 className="text-sm font-semibold text-slate-700 mb-1.5">{section}</h4>
                    <div className="grid grid-cols-12 gap-2 px-2 py-1 text-[11px] text-slate-500 uppercase">
                      <div className="col-span-4">Field</div>
                      <div className="col-span-2">Current</div>
                      <div className="col-span-2">Suggested</div>
                      <div className="col-span-2">Status</div>
                      <div className="col-span-2 text-right">Apply</div>
                    </div>
                    <div className="space-y-1">
                      {items.map((s) => (
                        <SuggestionRow
                          key={s.id}
                          s={s}
                          currentValue={getPath(settings, s.path)}
                          onToggle={toggleSuggestion}
                        />
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <DialogFooter className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-2">
            {step > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={goPrev}
                data-testid="quiz-prev-btn"
              >
                <ChevronLeft className="h-4 w-4 mr-1" /> Back
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={resetAndClose}
              data-testid="quiz-close-btn"
            >
              <X className="h-4 w-4 mr-1" /> Cancel
            </Button>
          </div>
          <div className="flex items-center gap-2">
            {!onReview && step < total - 1 && (
              <Button variant="outline" size="sm" onClick={goNext} data-testid="quiz-skip-btn">
                Skip section
              </Button>
            )}
            {!onReview && (
              <Button size="sm" onClick={goNext} data-testid="quiz-next-btn">
                {step === total - 1 ? 'Review suggestions' : 'Next'}
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
            {onReview && (
              <Button
                size="sm"
                onClick={applySelected}
                disabled={suggestions.filter((s) => s.apply).length === 0}
                className="bg-violet-600 hover:bg-violet-700"
                data-testid="quiz-apply-btn"
              >
                Apply Selected Defaults
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
