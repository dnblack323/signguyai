// Banner Setup Wizard - Configure default banner pricing rules
// Saves to settings.category_defaults.banners

import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Switch } from '../ui/switch';
import { Textarea } from '../ui/textarea';
import { ArrowLeft, ArrowRight, CheckCircle, Info, Package, DollarSign, Clock, Wrench, FileText } from 'lucide-react';
import { toast } from 'sonner';

const n = (v) => Number(v || 0);
const f2 = (v) => n(v).toFixed(2);

const PRICING_METHODS = [
  { value: 'price_per_sqft', label: 'Price Per Square Foot', status: 'basic_setup' },
  { value: 'detailed_material_labor', label: 'Detailed Material + Labor', status: 'detailed_setup' },
  { value: 'compare_methods', label: 'Compare Methods', status: 'compare_ready' },
  { value: 'manual_quote', label: 'Manual Quote', status: 'basic_setup' },
];

const DEFAULT_ADDONS = [
  { key: 'hems', label: 'Hems', active: true, pricing_type: 'included', included_by_default: true, default_flat_fee: 0, default_unit_fee: 0, default_labor_minutes: 0 },
  { key: 'grommets', label: 'Grommets', active: true, pricing_type: 'each', included_by_default: false, default_flat_fee: 0, default_unit_fee: 1.00, default_labor_minutes: 0 },
  { key: 'brackets', label: 'Brackets', active: true, pricing_type: 'each', included_by_default: false, default_flat_fee: 0, default_unit_fee: 20.00, default_labor_minutes: 0 },
  { key: 'other_hardware', label: 'Other Hardware', active: true, pricing_type: 'flat_fee', included_by_default: false, default_flat_fee: 0, default_unit_fee: 0, default_labor_minutes: 0 },
  { key: 'pole_pockets', label: 'Pole Pockets', active: true, pricing_type: 'flat_fee', included_by_default: false, default_flat_fee: 15.00, default_unit_fee: 0, default_labor_minutes: 0 },
  { key: 'design', label: 'Design', active: true, pricing_type: 'flat_fee', included_by_default: false, default_flat_fee: 35.00, default_unit_fee: 0, default_labor_minutes: 30, rate_source: 'design_rate' },
  { key: 'setup_fee', label: 'Setup Fee', active: true, pricing_type: 'flat_fee', included_by_default: false, default_flat_fee: 15.00, default_unit_fee: 0, default_labor_minutes: 0 },
  { key: 'install', label: 'Install', active: true, pricing_type: 'flat_fee', included_by_default: false, default_flat_fee: 0, default_unit_fee: 0, default_labor_minutes: 0, rate_source: 'install_rate' },
];

const PRODUCT_TEMPLATES = [
  {
    key: 'small_pole_banner',
    name: 'Small Pole Banner',
    width: 18,
    height: 36,
    unit: 'inches',
    default_material: '18oz_banner',
    default_addons: ['pole_pockets'],
    show_hardware_option: true,
    suggested_pricing_method: 'compare_methods',
  },
  {
    key: 'large_pole_banner',
    name: 'Large Pole Banner',
    width: 24,
    height: 48,
    unit: 'inches',
    default_material: '18oz_banner',
    default_addons: ['pole_pockets'],
    show_hardware_option: true,
    suggested_pricing_method: 'compare_methods',
  },
];

export default function BannerSetupWizard({ open, onClose, settings, materials, onSave }) {
  const [step, setStep] = useState(1);
  const [wizardData, setWizardData] = useState({});

  useEffect(() => {
    if (open) {
      // Load existing banner settings
      const bannerSettings = settings?.category_defaults?.banners || {};
      setWizardData({
        pricing_method: bannerSettings.pricing_method || 'compare_methods',
        default_material: bannerSettings.default_material || '13oz_banner',
        material_retail_rates: bannerSettings.material_retail_rates || [
          { material_id: '13oz_banner', material_name: '13 oz Banner', default_retail_rate_per_sqft: 8.00 },
          { material_id: '18oz_banner', material_name: '18 oz Banner', default_retail_rate_per_sqft: 10.00 },
          { material_id: 'mesh_banner', material_name: 'Standard Mesh Banner', default_retail_rate_per_sqft: 11.00 },
          { material_id: 'fabric_banner', material_name: 'Standard Fabric Banner', default_retail_rate_per_sqft: 12.00 },
        ],
        minimum_charge: bannerSettings.default_minimum_sell_price || 75,
        setup_minutes: bannerSettings.setup_minutes || 10,
        production_minutes: bannerSettings.production_minutes || 15,
        minutes_per_sqft: bannerSettings.minutes_per_sqft || 0,
        addon_defaults: bannerSettings.addon_defaults || DEFAULT_ADDONS,
        product_templates: bannerSettings.product_templates || PRODUCT_TEMPLATES,
      });
    }
  }, [open, settings]);

  const handleNext = () => {
    if (step < 7) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleSave = () => {
    const selectedMethod = PRICING_METHODS.find(m => m.value === wizardData.pricing_method);
    
    const updatedSettings = {
      ...settings,
      category_defaults: {
        ...settings.category_defaults,
        banners: {
          ...(settings.category_defaults?.banners || {}),
          ...wizardData,
        },
      },
      category_pricing_methods: {
        ...(settings.category_pricing_methods || {}),
        banners: wizardData.pricing_method,
      },
      category_setup_status: {
        ...(settings.category_setup_status || {}),
        banners: selectedMethod?.status || 'basic_setup',
      },
    };

    onSave(updatedSettings);
    toast.success('Banner setup saved successfully');
    onClose();
  };

  const updateWizardData = (field, value) => {
    setWizardData({ ...wizardData, [field]: value });
  };

  const bannerMaterials = materials.filter(m => m.category === 'banner_material' && m.is_active);

  const renderStep = () => {
    if (step === 1) {
      // Step 1: Pricing Method
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">How do you normally want to price banners?</h3>
            <p className="text-sm text-gray-600 mb-4">
              You can change this later or use different methods per quote.
            </p>
          </div>
          <div className="space-y-3">
            {PRICING_METHODS.map(method => (
              <Card
                key={method.value}
                className={`cursor-pointer transition-all ${wizardData.pricing_method === method.value ? 'ring-2 ring-violet-500 bg-violet-50' : 'hover:bg-gray-50'}`}
                onClick={() => updateWizardData('pricing_method', method.value)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{method.label}</CardTitle>
                  <CardDescription className="text-xs">
                    {method.value === 'price_per_sqft' && 'Simple retail rate per square foot. Fast and easy.'}
                    {method.value === 'detailed_material_labor' && 'Calculate from actual material cost + labor time. Most accurate.'}
                    {method.value === 'compare_methods' && 'Show both retail and detailed pricing. Recommend the better option.'}
                    {method.value === 'manual_quote' && 'Enter price manually. No automatic calculation.'}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      );
    }

    if (step === 2) {
      // Step 2: Materials & Retail Rates
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Banner Materials & Retail Rates</h3>
            <p className="text-sm text-gray-600 mb-4">
              Set default retail rates per square foot for each banner material. Material shop costs are managed in the Materials Library.
            </p>
          </div>
          
          <div>
            <Label className="text-sm">Default Banner Material</Label>
            <Select value={wizardData.default_material} onValueChange={(v) => updateWizardData('default_material', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {bannerMaterials.map(m => (
                  <SelectItem key={m.id} value={m.key || m.id}>{m.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium">Material Retail Rates</Label>
            {(wizardData.material_retail_rates || []).map((rate, idx) => (
              <div key={idx} className="grid grid-cols-3 gap-2 items-center p-2 bg-gray-50 rounded">
                <div className="text-sm font-medium">{rate.material_name}</div>
                <div>
                  <Input
                    type="number"
                    value={rate.default_retail_rate_per_sqft}
                    onChange={(e) => {
                      const updated = [...(wizardData.material_retail_rates || [])];
                      updated[idx].default_retail_rate_per_sqft = n(e.target.value);
                      updateWizardData('material_retail_rates', updated);
                    }}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="text-xs text-gray-500">$/sq ft retail</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (step === 3) {
      // Step 3: Minimum Charge
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Minimum Banner Charge</h3>
            <p className="text-sm text-gray-600 mb-4">
              Set the minimum price for any banner, regardless of size.
            </p>
          </div>
          <div>
            <Label className="text-sm">Minimum Charge</Label>
            <Input
              type="number"
              value={wizardData.minimum_charge}
              onChange={(e) => updateWizardData('minimum_charge', n(e.target.value))}
              className="h-10"
              prefix="$"
            />
            <p className="text-xs text-gray-500 mt-1">Suggested: $75</p>
          </div>
        </div>
      );
    }

    if (step === 4) {
      // Step 4: Labor Defaults
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Labor Time Defaults</h3>
            <p className="text-sm text-gray-600 mb-4">
              How much time does a normal banner take to produce and finish?
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-sm">Setup Minutes (per order)</Label>
              <Input
                type="number"
                value={wizardData.setup_minutes}
                onChange={(e) => updateWizardData('setup_minutes', n(e.target.value))}
                className="h-8"
              />
            </div>
            <div>
              <Label className="text-sm">Production/Finishing Minutes</Label>
              <Input
                type="number"
                value={wizardData.production_minutes}
                onChange={(e) => updateWizardData('production_minutes', n(e.target.value))}
                className="h-8"
              />
            </div>
            <div className="col-span-2">
              <Label className="text-sm">Minutes Per Sq Ft (optional)</Label>
              <Input
                type="number"
                value={wizardData.minutes_per_sqft}
                onChange={(e) => updateWizardData('minutes_per_sqft', n(e.target.value))}
                className="h-8"
              />
              <p className="text-xs text-gray-500 mt-1">Leave at 0 if you don't calculate labor by square foot</p>
            </div>
          </div>
        </div>
      );
    }

    if (step === 5) {
      // Step 5: Add-on Defaults
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Add-on Defaults</h3>
            <p className="text-sm text-gray-600 mb-4">
              Configure common banner add-ons and their default pricing.
            </p>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {(wizardData.addon_defaults || []).map((addon, idx) => (
              <Card key={addon.key} className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={addon.active}
                      onCheckedChange={(checked) => {
                        const updated = [...(wizardData.addon_defaults || [])];
                        updated[idx].active = checked;
                        updateWizardData('addon_defaults', updated);
                      }}
                    />
                    <Label className="text-sm font-medium">{addon.label}</Label>
                  </div>
                  <Select
                    value={addon.pricing_type}
                    onValueChange={(v) => {
                      const updated = [...(wizardData.addon_defaults || [])];
                      updated[idx].pricing_type = v;
                      updateWizardData('addon_defaults', updated);
                    }}
                  >
                    <SelectTrigger className="w-40 h-7 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="included">Included</SelectItem>
                      <SelectItem value="flat_fee">Flat Fee</SelectItem>
                      <SelectItem value="each">Per Each</SelectItem>
                      <SelectItem value="labor_minutes">Labor Minutes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {addon.active && addon.pricing_type !== 'included' && (
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {addon.pricing_type === 'flat_fee' && (
                      <div>
                        <Label className="text-xs">Flat Fee</Label>
                        <Input
                          type="number"
                          value={addon.default_flat_fee}
                          onChange={(e) => {
                            const updated = [...(wizardData.addon_defaults || [])];
                            updated[idx].default_flat_fee = n(e.target.value);
                            updateWizardData('addon_defaults', updated);
                          }}
                          className="h-7 text-xs"
                        />
                      </div>
                    )}
                    {addon.pricing_type === 'each' && (
                      <div>
                        <Label className="text-xs">Price Each</Label>
                        <Input
                          type="number"
                          value={addon.default_unit_fee}
                          onChange={(e) => {
                            const updated = [...(wizardData.addon_defaults || [])];
                            updated[idx].default_unit_fee = n(e.target.value);
                            updateWizardData('addon_defaults', updated);
                          }}
                          className="h-7 text-xs"
                        />
                      </div>
                    )}
                    {addon.pricing_type === 'labor_minutes' && (
                      <div>
                        <Label className="text-xs">Labor Minutes</Label>
                        <Input
                          type="number"
                          value={addon.default_labor_minutes}
                          onChange={(e) => {
                            const updated = [...(wizardData.addon_defaults || [])];
                            updated[idx].default_labor_minutes = n(e.target.value);
                            updateWizardData('addon_defaults', updated);
                          }}
                          className="h-7 text-xs"
                        />
                      </div>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      );
    }

    if (step === 6) {
      // Step 6: Product Templates
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Product Templates</h3>
            <p className="text-sm text-gray-600 mb-4">
              Quick-fill templates for common banner sizes and configurations.
            </p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
            <p className="font-medium text-blue-900">Default Templates Included:</p>
            <ul className="list-disc ml-4 mt-2 space-y-1 text-blue-800">
              <li><strong>Small Pole Banner:</strong> 18" × 36" with pole pockets</li>
              <li><strong>Large Pole Banner:</strong> 24" × 48" with pole pockets</li>
            </ul>
          </div>
          <p className="text-xs text-gray-500">
            Both templates default to 18 oz Banner material and Compare Methods pricing. You can add more templates later.
          </p>
        </div>
      );
    }

    if (step === 7) {
      // Step 7: Review & Save
      return (
        <div className="space-y-4">
          <h3 className="text-base font-semibold mb-2">Review Banner Setup</h3>
          <div className="space-y-3">
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Pricing Method</p>
              <p className="text-sm font-medium">
                {PRICING_METHODS.find(m => m.value === wizardData.pricing_method)?.label}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Default Material</p>
              <p className="text-sm font-medium">
                {bannerMaterials.find(m => (m.key || m.id) === wizardData.default_material)?.name || wizardData.default_material}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Minimum Charge</p>
              <p className="text-sm font-medium">${f2(wizardData.minimum_charge)}</p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Labor Defaults</p>
              <p className="text-sm">
                Setup: {wizardData.setup_minutes} min, Production: {wizardData.production_minutes} min
                {wizardData.minutes_per_sqft > 0 && `, ${wizardData.minutes_per_sqft} min/sq ft`}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Active Add-ons</p>
              <p className="text-sm">
                {(wizardData.addon_defaults || []).filter(a => a.active).map(a => a.label).join(', ')}
              </p>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <p className="text-xs text-gray-500">Product Templates</p>
              <p className="text-sm">Small Pole Banner, Large Pole Banner</p>
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="h-5 w-5 text-violet-600" />
            Banner Setup Wizard - Step {step} of 7
          </DialogTitle>
          <DialogDescription>
            Configure default banner pricing rules. All settings save to Category Rules → Banners.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {/* Progress */}
          <div className="mb-4 flex items-center gap-2">
            {[1, 2, 3, 4, 5, 6, 7].map(s => (
              <div key={s} className={`h-1.5 flex-1 rounded-full ${s <= step ? 'bg-violet-600' : 'bg-gray-200'}`} />
            ))}
          </div>

          {renderStep()}
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div>
            {step > 1 && (
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {step === 7 ? (
              <Button onClick={handleSave} className="bg-violet-600 hover:bg-violet-700">
                <CheckCircle className="h-4 w-4 mr-1" /> Save Banner Setup
              </Button>
            ) : (
              <Button onClick={handleNext}>
                Next <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
