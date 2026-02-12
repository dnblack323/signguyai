import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Loader2, Save, DollarSign, Clock, Percent, Package,
  RefreshCw, AlertCircle, ArrowLeft
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PricingSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [defaults, setDefaults] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  const getToken = () => localStorage.getItem('token');

  const fetchDefaults = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pricing/defaults`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDefaults(data);
      }
    } catch (err) {
      console.error('Error fetching pricing defaults:', err);
      toast.error('Failed to load pricing settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDefaults();
  }, [fetchDefaults]);

  const handleChange = (field, value) => {
    setDefaults(prev => ({
      ...prev,
      [field]: value
    }));
    setHasChanges(true);
  };

  const handleQuantityBreakChange = (breakKey, field, value) => {
    setDefaults(prev => ({
      ...prev,
      quantity_breaks: {
        ...prev.quantity_breaks,
        [breakKey]: {
          ...prev.quantity_breaks[breakKey],
          [field]: value
        }
      }
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    const token = getToken();
    if (!token) return;

    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/pricing/defaults`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(defaults)
      });

      if (response.ok) {
        toast.success('Pricing settings saved successfully!');
        setHasChanges(false);
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to save settings');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    fetchDefaults();
    setHasChanges(false);
    toast.info('Settings reset to saved values');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/pricing">
            <Button variant="outline" size="icon" className="border-slate-600 text-slate-300 hover:bg-slate-700">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">Pricing Settings</h1>
            <p className="text-slate-400 mt-1">Configure default rates, markups, and pricing rules</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {hasChanges && (
            <Button variant="outline" onClick={handleReset} className="border-slate-600">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset
              </Button>
            )}
            <Button 
              onClick={handleSave} 
              disabled={saving || !hasChanges}
              className="bg-teal-500 hover:bg-teal-600"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
              Save Changes
            </Button>
          </div>
        </div>

        {hasChanges && (
          <div className="flex items-center gap-2 p-3 bg-amber-500/20 border border-amber-500/50 rounded-lg">
            <AlertCircle className="h-5 w-5 text-amber-400" />
            <span className="text-amber-200 text-sm">You have unsaved changes</span>
          </div>
        )}

        <Tabs defaultValue="rates" className="space-y-6">
          <TabsList className="bg-slate-800">
            <TabsTrigger value="rates">Labor Rates</TabsTrigger>
            <TabsTrigger value="markups">Markups</TabsTrigger>
            <TabsTrigger value="minimums">Minimums</TabsTrigger>
            <TabsTrigger value="complexity">Complexity</TabsTrigger>
            <TabsTrigger value="quantity">Quantity Breaks</TabsTrigger>
            <TabsTrigger value="setup">Setup Fees</TabsTrigger>
          </TabsList>

          {/* Labor Rates Tab */}
          <TabsContent value="rates">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-teal-400" />
                  Hourly Labor Rates
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Set your default hourly rates for different types of work
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <Label className="text-slate-300">General Hourly Rate</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.hourly_rate || 75}
                        onChange={(e) => handleChange('hourly_rate', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Used for general production work</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Design Hourly Rate</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.design_hourly_rate || 85}
                        onChange={(e) => handleChange('design_hourly_rate', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Used for design/artwork services</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Install Hourly Rate</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.install_hourly_rate || 95}
                        onChange={(e) => handleChange('install_hourly_rate', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Used for installation services</p>
                  </div>
                </div>

                <Separator className="bg-slate-700" />

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-slate-300">Mileage Rate (per mile)</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.mileage_rate || 0.67}
                        onChange={(e) => handleChange('mileage_rate', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">IRS standard rate: $0.67/mile (2024)</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Minimum Travel Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_travel_charge || 50}
                        onChange={(e) => handleChange('minimum_travel_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Minimum charge for any travel</p>
                  </div>
                </div>

                <Separator className="bg-slate-700" />

                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-3">Time Estimates (minutes per sq ft)</h4>
                  <div className="grid md:grid-cols-4 gap-4">
                    <div>
                      <Label className="text-slate-400 text-xs">Weeding Time</Label>
                      <Input
                        type="number"
                        step="0.5"
                        value={defaults?.weeding_time_per_sqft || 5}
                        onChange={(e) => handleChange('weeding_time_per_sqft', parseFloat(e.target.value) || 0)}
                        className="mt-1 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-slate-400 text-xs">Application Time</Label>
                      <Input
                        type="number"
                        step="0.5"
                        value={defaults?.application_time_per_sqft || 3}
                        onChange={(e) => handleChange('application_time_per_sqft', parseFloat(e.target.value) || 0)}
                        className="mt-1 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-slate-400 text-xs">Print Time</Label>
                      <Input
                        type="number"
                        step="0.5"
                        value={defaults?.print_time_per_sqft || 1}
                        onChange={(e) => handleChange('print_time_per_sqft', parseFloat(e.target.value) || 0)}
                        className="mt-1 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <div>
                      <Label className="text-slate-400 text-xs">Laminate Time</Label>
                      <Input
                        type="number"
                        step="0.5"
                        value={defaults?.laminate_time_per_sqft || 1.5}
                        onChange={(e) => handleChange('laminate_time_per_sqft', parseFloat(e.target.value) || 0)}
                        className="mt-1 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Markups Tab */}
          <TabsContent value="markups">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Percent className="h-5 w-5 text-teal-400" />
                  Default Markups
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Set default markup percentages applied to production costs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-slate-300">Default Markup %</Label>
                    <div className="relative mt-1">
                      <Input
                        type="number"
                        value={defaults?.default_markup_percent || 100}
                        onChange={(e) => handleChange('default_markup_percent', parseFloat(e.target.value) || 0)}
                        className="pr-10 bg-slate-900 border-slate-600 text-white"
                      />
                      <Percent className="absolute right-3 top-3 h-4 w-4 text-slate-500" />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">100% markup = 50% profit margin</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Material Markup %</Label>
                    <div className="relative mt-1">
                      <Input
                        type="number"
                        value={defaults?.material_markup_percent || 50}
                        onChange={(e) => handleChange('material_markup_percent', parseFloat(e.target.value) || 0)}
                        className="pr-10 bg-slate-900 border-slate-600 text-white"
                      />
                      <Percent className="absolute right-3 top-3 h-4 w-4 text-slate-500" />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Applied specifically to material costs</p>
                  </div>
                </div>

                <div className="p-4 bg-slate-900/50 rounded-lg">
                  <h4 className="text-sm font-medium text-slate-300 mb-2">Markup Calculator</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Markup %</p>
                      <p className="text-white font-medium">{defaults?.default_markup_percent || 100}%</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Profit Margin</p>
                      <p className="text-teal-400 font-medium">
                        {((defaults?.default_markup_percent || 100) / (100 + (defaults?.default_markup_percent || 100)) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Example: $100 cost</p>
                      <p className="text-green-400 font-medium">
                        Sells for ${(100 * (1 + (defaults?.default_markup_percent || 100) / 100)).toFixed(0)}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Minimums Tab */}
          <TabsContent value="minimums">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-teal-400" />
                  Minimum Charges
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Set minimum charges for different types of work
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <Label className="text-slate-300">Minimum Order</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_order || 50}
                        onChange={(e) => handleChange('minimum_order', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Min Vinyl Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_vinyl_charge || 25}
                        onChange={(e) => handleChange('minimum_vinyl_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Min Print Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_print_charge || 35}
                        onChange={(e) => handleChange('minimum_print_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Min Sign Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_sign_charge || 50}
                        onChange={(e) => handleChange('minimum_sign_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Min Service Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_service_charge || 75}
                        onChange={(e) => handleChange('minimum_service_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Min Wrap Charge</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.minimum_wrap_charge || 500}
                        onChange={(e) => handleChange('minimum_wrap_charge', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Complexity Tab */}
          <TabsContent value="complexity">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Package className="h-5 w-5 text-teal-400" />
                  Complexity Multipliers
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Configure how complexity (1-10) affects pricing
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-slate-300">Base Multiplier (Complexity 1)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={defaults?.complexity_multiplier_base || 1.0}
                      onChange={(e) => handleChange('complexity_multiplier_base', parseFloat(e.target.value) || 1)}
                      className="mt-1 bg-slate-900 border-slate-600 text-white"
                    />
                    <p className="text-xs text-slate-500 mt-1">Multiplier at lowest complexity</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Max Multiplier (Complexity 10)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={defaults?.complexity_multiplier_max || 2.0}
                      onChange={(e) => handleChange('complexity_multiplier_max', parseFloat(e.target.value) || 2)}
                      className="mt-1 bg-slate-900 border-slate-600 text-white"
                    />
                    <p className="text-xs text-slate-500 mt-1">Multiplier at highest complexity</p>
                  </div>
                </div>

                <div className="p-4 bg-slate-900/50 rounded-lg">
                  <h4 className="text-sm font-medium text-slate-300 mb-3">Multiplier Preview</h4>
                  <div className="grid grid-cols-5 gap-2 text-center text-sm">
                    {[1, 3, 5, 7, 10].map(level => {
                      const base = defaults?.complexity_multiplier_base || 1;
                      const max = defaults?.complexity_multiplier_max || 2;
                      const mult = base + (max - base) * (level - 1) / 9;
                      return (
                        <div key={level} className="p-2 bg-slate-800 rounded">
                          <p className="text-slate-500">Level {level}</p>
                          <p className="text-teal-400 font-medium">{mult.toFixed(2)}x</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Quantity Breaks Tab */}
          <TabsContent value="quantity">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Package className="h-5 w-5 text-teal-400" />
                  Quantity Discount Breaks
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Configure automatic discounts based on order quantity
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['break_1', 'break_2', 'break_3', 'break_4'].map((breakKey, index) => (
                    <div key={breakKey} className="flex items-center gap-4 p-4 bg-slate-900/50 rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-teal-500/20 flex items-center justify-center text-teal-400 font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1 grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-slate-400 text-xs">Minimum Quantity</Label>
                          <Input
                            type="number"
                            value={defaults?.quantity_breaks?.[breakKey]?.min_qty || 0}
                            onChange={(e) => handleQuantityBreakChange(breakKey, 'min_qty', parseInt(e.target.value) || 0)}
                            className="mt-1 bg-slate-900 border-slate-600 text-white"
                          />
                        </div>
                        <div>
                          <Label className="text-slate-400 text-xs">Discount %</Label>
                          <Input
                            type="number"
                            value={defaults?.quantity_breaks?.[breakKey]?.discount_percent || 0}
                            onChange={(e) => handleQuantityBreakChange(breakKey, 'discount_percent', parseInt(e.target.value) || 0)}
                            className="mt-1 bg-slate-900 border-slate-600 text-white"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-500 mt-4">
                  Discounts are cumulative - the highest applicable discount is used
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Setup Fees Tab */}
          <TabsContent value="setup">
            <Card className="border-slate-700 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-teal-400" />
                  Setup Fees
                </CardTitle>
                <CardDescription className="text-slate-400">
                  One-time setup fees added to jobs by category
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <Label className="text-slate-300">Vinyl Setup Fee</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.setup_fee_vinyl || 15}
                        onChange={(e) => handleChange('setup_fee_vinyl', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Print Setup Fee</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.setup_fee_print || 25}
                        onChange={(e) => handleChange('setup_fee_print', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Screen Print Setup (per color)</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.setup_fee_apparel_screen || 35}
                        onChange={(e) => handleChange('setup_fee_apparel_screen', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Multiplied by number of colors</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">DTF/HTV Setup Fee</Label>
                    <div className="relative mt-1">
                      <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <Input
                        type="number"
                        step="0.01"
                        value={defaults?.setup_fee_apparel_dtf || 20}
                        onChange={(e) => handleChange('setup_fee_apparel_dtf', parseFloat(e.target.value) || 0)}
                        className="pl-10 bg-slate-900 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
  );
}
