import { useState, useEffect, useRef, useMemo } from 'react';
import { Calculator, Loader2, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

/**
 * Live pricing preview for new order form — calls pricing API directly
 * without requiring a saved ticket ID. Shows real-time estimate as fields change.
 */
const getEffectiveQuantity = (category, specs, quantity) => {
  if (category === 'apparel') {
    const sizeKeys = ['size_xs', 'size_s', 'size_m', 'size_l', 'size_xl', 'size_2xl', 'size_3xl', 'size_4xl', 'size_5xl'];
    const total = sizeKeys.reduce((sum, key) => sum + (parseInt(specs?.[key]) || 0), 0);
    if (total > 0) return total;
  }
  return quantity || 1;
};

const normalizeCoverageType = (value) => {
  const raw = String(value || '').toLowerCase();
  if (raw === '25') return 'spot';
  if (raw === '50') return 'half';
  if (raw === '75') return 'partial';
  if (raw === '100' || raw === 'full_wrap') return 'full';
  if (raw === 'partial_50') return 'half';
  if (raw === 'partial_75') return 'partial';
  if (raw === 'spot_graphics') return 'spot';
  if (raw === 'custom') return 'partial';
  return raw || undefined;
};

export default function LivePricingPreview({ category, specs, quantity, onPriceChange, entryMode = 'detailed', manualQuoteOverride = null, onManualOverrideChange }) {
  const [calc, setCalc] = useState(null);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const lastSentPrice = useRef(null);
  const lastError = useRef('');

  // Parse dimensions from specs
  const pricingInput = useMemo(() => {
    const unit = (specs?.unit_of_measure || 'inches').toLowerCase();
    const wRaw = parseFloat(specs?.width) || 0;
    const hRaw = parseFloat(specs?.height) || 0;
    const wIn = unit === 'feet' ? wRaw * 12 : wRaw;
    const hIn = unit === 'feet' ? hRaw * 12 : hRaw;

    const CATEGORY_MAP = {
      banners: 'digital_print', rigid_signs: 'rigid_signs', cut_vinyl: 'cut_vinyl',
      digital_print: 'digital_print', vehicle_wrap: 'vehicle_graphics',
      apparel: 'apparel', services: 'services', promo_misc: 'promotional', custom: 'custom',
    };

    return {
      category: CATEGORY_MAP[category] || 'custom',
      width_inches: wIn || null,
      length_inches: hIn || null,
      unit_of_measure: unit,
      print_media_key: specs?.print_media_key,
      use_type: specs?.use_type,
      print_quality_mode: specs?.print_quality_mode,
      ink_coverage_percent: specs?.ink_coverage_percent,
      laminate: specs?.laminate || false,
      laminate_material_key: specs?.laminate_material_key,
      contour_cut_type: specs?.contour_cut_type,
      trim_finish_type: specs?.trim_finish_type,
      piece_separation_required: specs?.piece_separation_required || false,
      separated_piece_count: parseInt(specs?.separated_piece_count) || 0,
      mounted_to_substrate: specs?.mounted_to_substrate || false,
      substrate_material_key: specs?.substrate_material_key,
      vinyl_type_key: specs?.vinyl_type_key,
      num_colors: parseInt(specs?.num_colors) || 1,
      weeding_complexity: specs?.weeding_complexity,
      masking_required: specs?.masking_required,
      surface_type: specs?.surface_type,
      artwork_ready: specs?.artwork_ready || false,
      artwork_needed: specs?.artwork_needed || false,
      design_complexity: specs?.design_complexity,
      file_cleanup_needed: specs?.file_cleanup_needed || false,
      install_required: specs?.install_required || false,
      install_complexity: specs?.install_complexity,
      rush_order: specs?.rush_order || false,
      substrate_type_key: specs?.substrate_type_key,
      thickness: specs?.thickness,
      graphic_method: specs?.graphic_method,
      protective_finish: specs?.protective_finish || false,
      protective_finish_type: specs?.protective_finish_type,
      sidedness: specs?.sidedness,
      double_sided_art: specs?.double_sided_art,
      shape_type: specs?.shape_type,
      finish_quality: specs?.finish_quality,
      hardware_included: specs?.hardware_included || false,
      hardware_type: specs?.hardware_type,
      drill_prep_required: specs?.drill_prep_required || false,
      apparel_type: specs?.garment_type,
      transfer_type: specs?.decoration_method,
      num_print_locations: (specs?.print_locations || []).length || 1,
      service_type: specs?.service_type,
      estimated_hours: specs?.estimated_hours ? Number(specs.estimated_hours) : null,
      vehicle_type: specs?.vehicle_type,
      coverage_type: normalizeCoverageType(specs?.coverage_type),
      include_setup_fee: specs?.design_needed || specs?.setup_required || false,
      complexity: 1,
    };
  }, [category, JSON.stringify(specs)]);


  const effectiveQuantity = useMemo(() => getEffectiveQuantity(category, specs, quantity), [category, specs, quantity]);

  useEffect(() => {
    if (!category || !pricingInput.category) {
      setCalc(null);
      if (onPriceChange && lastSentPrice.current !== 0) {
        lastSentPrice.current = 0;
        onPriceChange(0, null);
      }
      return;
    }
    // Need at least some input to calculate
    const hasInput = pricingInput.width_inches || pricingInput.apparel_type || pricingInput.vehicle_type || pricingInput.substrate_type || pricingInput.vinyl_type || pricingInput.service_type || pricingInput.estimated_hours;
    if (!hasInput) {
      setCalc(null);
      if (onPriceChange && lastSentPrice.current !== 0) {
        lastSentPrice.current = 0;
        onPriceChange(0, null);
      }
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await axios.post(`${API}/pricing/calculate`, {
          category: pricingInput.category,
          pricing_data: pricingInput,
          quantity: effectiveQuantity,
        }, { headers: hdr() });
        if (res.data?.error) {
          setCalc(res.data);
          if (res.data.error !== lastError.current) {
            lastError.current = res.data.error;
            toast.error(`Pricing needs more setup: ${res.data.error}`);
          }
          if (onPriceChange && lastSentPrice.current !== 0) {
            lastSentPrice.current = 0;
            onPriceChange(0, res.data);
          }
          return;
        }
        setCalc(res.data);
        if (onPriceChange && res.data?.selling_price !== lastSentPrice.current) {
          lastSentPrice.current = res.data?.selling_price ?? 0;
          onPriceChange(res.data?.selling_price ?? 0, res.data);
        }
      } catch {
        setCalc(null);
        if (onPriceChange && lastSentPrice.current !== 0) {
          lastSentPrice.current = 0;
          onPriceChange(0, null);
        }
      } finally {
        setLoading(false);
      }
    }, 600);
  }, [pricingInput, effectiveQuantity, category, onPriceChange]);

  if (!category) return null;
  // Quick-mode items never render the detailed live estimate — they use manual price only.
  if (entryMode === 'quick') return null;

  const breakdown = calc || {};
  const hasCalc = calc && (calc.selling_price > 0 || calc.total_cost > 0);
  const suggestedSell = breakdown.selling_price || 0;
  const manualActive = manualQuoteOverride !== null && manualQuoteOverride !== undefined && Number(manualQuoteOverride) > 0;
  const activePrice = manualActive ? Number(manualQuoteOverride) : suggestedSell;
  const totalCost = breakdown.total_cost || 0;
  const activeProfit = activePrice - totalCost;
  const activeMargin = activePrice > 0 ? (activeProfit / activePrice) * 100 : 0;

  return (
    <Card className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid="live-pricing-preview">
      <CardHeader className="pb-2">
        <CardTitle className="text-gray-900 text-sm flex items-center gap-2">
          <Calculator className="w-4 h-4 text-violet-600" /> Live Estimate
          {loading && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {calc?.error ? (
          <div className="text-center py-3">
            <AlertTriangle className="w-5 h-5 mx-auto text-amber-400 mb-1" />
            <p className="text-xs text-amber-600">Pricing needs more setup</p>
            <p className="text-[11px] text-gray-500 mt-1">{calc.error}</p>
          </div>
        ) : hasCalc ? (
          <div className="space-y-2">
            {[
              { label: 'Material', value: breakdown.material_cost },
              { label: 'Labor', value: breakdown.labor_cost },
              { label: 'Setup', value: breakdown.setup_cost },
              { label: 'Overhead', value: breakdown.overhead_cost },
              { label: 'Additional', value: breakdown.additional_costs },
            ].filter(r => r.value > 0).map(row => (
              <div key={row.label} className="flex justify-between text-xs">
                <span className="text-gray-500">{row.label}</span>
                <span className="text-gray-700">${(row.value || 0).toFixed(2)}</span>
              </div>
            ))}
            <div className="border-t border-gray-200 pt-2 flex justify-between text-xs">
              <span className="text-gray-600">Cost</span>
              <span className="text-gray-900 font-medium">${(breakdown.total_cost || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Markup ({(breakdown.markup_percent || 0).toFixed(0)}%)</span>
              <span className="text-gray-600">${(breakdown.profit_amount || 0).toFixed(2)}</span>
            </div>
            <div className="bg-violet-50 border border-violet-200 rounded-lg p-3 text-center mt-2">
              <p className="text-[10px] text-violet-600 uppercase tracking-wide">Suggested Sell</p>
              <p className="text-xl font-bold text-gray-900">${suggestedSell.toFixed(2)}</p>
              {effectiveQuantity > 1 && <p className="text-[10px] text-gray-500">${(suggestedSell / effectiveQuantity).toFixed(2)} each</p>}
            </div>
            {onManualOverrideChange && (
              <div className="mt-2 space-y-1">
                <label className="text-[10px] text-gray-500 uppercase tracking-wide">Manual Quote Override</label>
                <div className="flex gap-1">
                  <input
                    type="number"
                    step="0.01"
                    value={manualQuoteOverride ?? ''}
                    onChange={(e) => onManualOverrideChange(parseFloat(e.target.value) || null)}
                    className="flex-1 text-xs border rounded px-2 py-1"
                    placeholder="0 = use suggested"
                    data-testid="live-estimate-manual-override"
                  />
                  {manualActive && (
                    <button
                      type="button"
                      onClick={() => onManualOverrideChange(null)}
                      className="text-[10px] text-violet-600 hover:underline"
                      data-testid="live-estimate-manual-reset"
                    >
                      Reset
                    </button>
                  )}
                </div>
                <p className="text-[10px] text-gray-500">
                  Using: <span className="font-medium">{manualActive ? 'Manual' : 'Suggested'}</span>
                  {' '}· Active ${activePrice.toFixed(2)} · Profit ${activeProfit.toFixed(2)} · Margin {activeMargin.toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-3">
            <AlertTriangle className="w-5 h-5 mx-auto text-gray-300 mb-1" />
            <p className="text-xs text-gray-400">Enter dimensions and specs to see estimate</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
