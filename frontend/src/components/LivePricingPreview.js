import { useState, useEffect, useRef, useMemo } from 'react';
import { Calculator, DollarSign, Loader2, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/json' });

/**
 * Live pricing preview for new order form — calls pricing API directly
 * without requiring a saved ticket ID. Shows real-time estimate as fields change.
 */
export default function LivePricingPreview({ category, specs, quantity }) {
  const [calc, setCalc] = useState(null);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  // Parse dimensions from specs
  const pricingInput = useMemo(() => {
    const unit = specs?.unit_of_measure || 'inches';
    const wRaw = parseFloat(specs?.width) || 0;
    const hRaw = parseFloat(specs?.height) || 0;
    const wIn = unit === 'feet' ? wRaw * 12 : wRaw;
    const hIn = unit === 'feet' ? hRaw * 12 : hRaw;
    const doubleSided = specs?.double_sided === 'double' || specs?.double_sided === true;
    const hasLam = specs?.lamination && specs.lamination !== 'none';

    const CATEGORY_MAP = {
      banners: 'digital_print', rigid_signs: 'rigid_signs', cut_vinyl: 'cut_vinyl',
      digital_print: 'digital_print', vehicle_wrap: 'vehicle_graphics',
      apparel: 'apparel', promo_misc: 'promotional', custom: 'custom',
    };

    return {
      category: CATEGORY_MAP[category] || 'custom',
      width_inches: wIn || null,
      length_inches: hIn || null,
      double_sided: doubleSided,
      laminate: hasLam,
      laminate_type: specs?.lamination,
      vinyl_type: specs?.vinyl_type || specs?.material,
      substrate_type: specs?.substrate,
      print_material: specs?.material,
      apparel_type: specs?.garment_type,
      transfer_type: specs?.decoration_method,
      num_print_locations: (specs?.print_locations || []).length || 1,
      vehicle_type: specs?.vehicle_type,
      coverage_type: specs?.coverage_type,
      // Finishing options that affect price
      grommets: specs?.grommets === true || (specs?.grommets && specs.grommets !== 'none'),
      hemming: specs?.hemming === true || (specs?.hems && specs.hems !== 'none'),
      include_setup_fee: specs?.design_needed || specs?.setup_required || false,
      // Rigid sign options
      stakes_included: specs?.stakes_included || false,
      install_required: specs?.install_required || false,
      // Cut vinyl
      num_colors: parseInt(specs?.num_colors) || 1,
      complexity: 1,
    };
  }, [category, specs]);

  useEffect(() => {
    if (!category || !pricingInput.category) return;
    // Need at least some input to calculate
    const hasInput = pricingInput.width_inches || pricingInput.apparel_type || pricingInput.vehicle_type || pricingInput.substrate_type || pricingInput.vinyl_type;
    if (!hasInput) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await axios.post(`${API}/pricing/calculate`, {
          category: pricingInput.category,
          pricing_data: pricingInput,
          quantity: quantity || 1,
        }, { headers: hdr() });
        setCalc(res.data);
      } catch {
        setCalc(null);
      } finally {
        setLoading(false);
      }
    }, 600);
  }, [pricingInput, quantity, category]);

  if (!category) return null;

  const breakdown = calc || {};
  const hasCalc = calc && (calc.selling_price > 0 || calc.total_cost > 0);

  return (
    <Card className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid="live-pricing-preview">
      <CardHeader className="pb-2">
        <CardTitle className="text-gray-900 text-sm flex items-center gap-2">
          <Calculator className="w-4 h-4 text-violet-600" /> Live Estimate
          {loading && <Loader2 className="w-3 h-3 animate-spin text-gray-400" />}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasCalc ? (
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
              <p className="text-xs text-violet-600">Estimated Sell Price</p>
              <p className="text-2xl font-bold text-gray-900">${(breakdown.selling_price || 0).toFixed(2)}</p>
              {quantity > 1 && <p className="text-xs text-gray-500">${((breakdown.selling_price || 0) / quantity).toFixed(2)} each</p>}
            </div>
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
