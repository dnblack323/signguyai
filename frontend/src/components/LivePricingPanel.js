import { useState, useEffect, useCallback, useRef } from 'react';
import { Calculator, DollarSign, Loader2, RefreshCw, Edit3, Lock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

/**
 * Live Pricing Panel — connects to existing /api/pricing/calculate via job ticket bridge.
 * Reads all values from tenant pricing settings. No hardcoded pricing.
 */
export default function LivePricingPanel({ ticketId, ticketData, onPriceSaved }) {
  const [calc, setCalc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pricingMode, setPricingMode] = useState('calculator');
  const [manualPrice, setManualPrice] = useState(0);
  const [saving, setSaving] = useState(false);
  const [pricingInputs, setPricingInputs] = useState({});
  const debounceRef = useRef(null);

  const runCalculation = useCallback(async (extraInputs = {}) => {
    if (!ticketId) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API}/job-tickets/${ticketId}/calculate-pricing`, 
        { ...pricingInputs, ...extraInputs }, 
        { headers: hdr() }
      );
      if (res.data.calculation) {
        setCalc(res.data);
      }
    } catch {
      // Silent fail — pricing preview is optional
    } finally {
      setLoading(false);
    }
  }, [ticketId, pricingInputs]);

  // Auto-calculate on mount and when ticket data changes
  useEffect(() => {
    if (ticketId) {
      runCalculation();
    }
  }, [ticketId]);

  // Debounced recalc when inputs change
  const handleInputChange = (key, value) => {
    const updated = { ...pricingInputs, [key]: value };
    setPricingInputs(updated);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runCalculation(updated), 500);
  };

  const handleSavePricing = async () => {
    if (!ticketId) return;
    setSaving(true);
    try {
      const body = {
        pricing_mode: pricingMode,
        calculated_price: calc?.active_price || 0,
        manual_price: manualPrice,
        calculation_breakdown: calc?.calculation || {},
      };
      const res = await axios.post(`${API}/job-tickets/${ticketId}/save-pricing`, body, { headers: hdr() });
      toast.success(`Price saved: $${res.data.active_price?.toFixed(2)} (${res.data.pricing_mode})`);
      onPriceSaved?.(res.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to save pricing');
    } finally {
      setSaving(false);
    }
  };

  const breakdown = calc?.calculation || {};
  const activePrice = pricingMode === 'manual' ? manualPrice : (calc?.active_price || 0);

  return (
    <Card className="bg-white rounded-xl border border-gray-200 shadow-sm" data-testid="live-pricing-panel">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-gray-900 text-base flex items-center gap-2">
            <Calculator className="w-5 h-5 text-violet-400" /> Pricing
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={pricingMode === 'calculator' ? 'bg-violet-500/15 text-violet-400 border-violet-500/30' : 'bg-amber-500/15 text-amber-400 border-amber-500/30'}>
              {pricingMode === 'calculator' ? 'Calculator' : 'Manual'}
            </Badge>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-gray-500" onClick={() => runCalculation()} disabled={loading} title="Recalculate">
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Switch */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
          <Label className="text-gray-700 text-sm">Pricing Mode</Label>
          <div className="flex items-center gap-2">
            <span className={`text-xs ${pricingMode === 'calculator' ? 'text-violet-400' : 'text-gray-500'}`}>Calculator</span>
            <Switch checked={pricingMode === 'manual'} onCheckedChange={(v) => setPricingMode(v ? 'manual' : 'calculator')} />
            <span className={`text-xs ${pricingMode === 'manual' ? 'text-amber-400' : 'text-gray-500'}`}>Manual</span>
          </div>
        </div>

        {/* Calculator Breakdown */}
        {pricingMode === 'calculator' && calc?.calculation && (
          <div className="space-y-2">
            {[
              { label: 'Material Cost', value: breakdown.material_cost, color: 'text-blue-400' },
              { label: 'Labor Cost', value: breakdown.labor_cost, color: 'text-green-400' },
              { label: 'Setup Cost', value: breakdown.setup_cost, color: 'text-purple-400' },
              { label: 'Overhead', value: breakdown.overhead_cost, color: 'text-gray-500' },
              { label: 'Additional', value: breakdown.additional_costs, color: 'text-orange-400' },
            ].filter(r => r.value > 0).map(row => (
              <div key={row.label} className="flex justify-between text-sm">
                <span className="text-gray-500">{row.label}</span>
                <span className={row.color}>${(row.value || 0).toFixed(2)}</span>
              </div>
            ))}
            <div className="border-t border-gray-200 pt-2 flex justify-between text-sm">
              <span className="text-gray-700">Production Cost</span>
              <span className="text-gray-900 font-medium">${(breakdown.production_cost || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Markup ({(breakdown.markup_percent || 0).toFixed(0)}%)</span>
              <span className="text-gray-700">${(breakdown.profit_amount || 0).toFixed(2)}</span>
            </div>
          </div>
        )}

        {pricingMode === 'calculator' && !calc?.calculation && !loading && (
          <p className="text-xs text-gray-500 text-center py-3">Enter dimensions and specs to see pricing</p>
        )}

        {/* Manual Override */}
        {pricingMode === 'manual' && (
          <div>
            <Label className="text-gray-700 text-sm">Override Price</Label>
            <div className="relative mt-1">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                type="number" min={0} step={0.01}
                value={manualPrice}
                onChange={(e) => setManualPrice(parseFloat(e.target.value) || 0)}
                className="pl-8 bg-gray-50 border-gray-300 text-gray-900"
                data-testid="manual-price-input"
              />
            </div>
            {calc?.active_price > 0 && (
              <p className="text-xs text-gray-500 mt-1">Calculator estimate: ${calc.active_price.toFixed(2)}</p>
            )}
          </div>
        )}

        {/* Active Price */}
        <div className="bg-violet-50 border border-violet-200 rounded-lg p-4 text-center">
          <p className="text-xs text-violet-600 uppercase">Active Price</p>
          <p className="text-3xl font-bold text-gray-900 mt-1" data-testid="active-price">${activePrice.toFixed(2)}</p>
          <p className="text-xs text-gray-500 mt-1">
            {pricingMode === 'calculator' ? 'From settings-based calculator' : 'Manual override'}
            {calc?.pricing_category && ` | ${calc.pricing_category}`}
          </p>
        </div>

        {/* Complexity Input (for calculator mode) */}
        {pricingMode === 'calculator' && (
          <div className="flex items-center justify-between">
            <Label className="text-gray-500 text-xs">Complexity (1-5)</Label>
            <Input
              type="number" min={1} max={5}
              value={pricingInputs.complexity || 1}
              onChange={(e) => handleInputChange('complexity', parseInt(e.target.value) || 1)}
              className="w-16 h-7 text-center bg-gray-50 border-gray-300 text-gray-900 text-sm"
            />
          </div>
        )}

        {/* Save */}
        <Button onClick={handleSavePricing} disabled={saving} className="w-full bg-violet-600 hover:bg-violet-700 text-white" data-testid="save-pricing-btn">
          {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <DollarSign className="w-4 h-4 mr-2" />}
          Save Pricing to Ticket
        </Button>
      </CardContent>
    </Card>
  );
}
