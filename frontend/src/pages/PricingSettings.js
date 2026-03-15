import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import {
  ArrowLeft,
  BarChart3,
  Factory,
  Layers3,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth, Permission } from '../context/AuthContext';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MATERIAL_PRESETS = [
  { key: 'vinyl', name: 'Vinyl Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'laminate', name: 'Laminate Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'banner_material', name: 'Banner Material Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'coroplast', name: 'Coroplast Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'aluminum_composite', name: 'Aluminum Composite Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'foam_board', name: 'Foam Board Cost Per Sq Ft', category: 'material', unit_type: 'sqft' },
  { key: 'ink', name: 'Ink Cost Per Sq Ft', category: 'optional', unit_type: 'sqft' },
  { key: 'transfer_tape', name: 'Transfer Tape Cost Per Sq Ft', category: 'optional', unit_type: 'sqft' },
];

const CATEGORY_ORDER = [
  { key: 'vehicle_wraps', label: 'Vehicle Wraps' },
  { key: 'banners', label: 'Banners' },
  { key: 'rigid_signs', label: 'Rigid Signs' },
];

const createMaterial = (seed = {}) => ({
  id: seed.id || `${seed.key || 'material'}-${Math.random().toString(36).slice(2, 10)}`,
  key: seed.key || '',
  name: seed.name || '',
  category: seed.category || 'material',
  cost_per_unit: seed.cost_per_unit ?? 0,
  unit_type: seed.unit_type || 'sqft',
  is_active: seed.is_active ?? true,
});

const defaultCategoryDefaults = {
  vehicle_wraps: {
    label: 'Vehicle Wraps',
    default_labor_hours_per_sqft: 0.12,
    default_markup_multiplier: 2.4,
    target_profit_margin_percent: 42,
    minimum_charge: 850,
    default_material_keys: ['vinyl', 'laminate', 'ink'],
  },
  banners: {
    label: 'Banners',
    default_labor_hours_per_sqft: 0.06,
    default_markup_multiplier: 2.35,
    target_profit_margin_percent: 40,
    minimum_charge: 35,
    default_material_keys: ['banner_material', 'ink'],
  },
  rigid_signs: {
    label: 'Rigid Signs',
    default_labor_hours_per_sqft: 0.08,
    default_markup_multiplier: 2.45,
    target_profit_margin_percent: 41,
    minimum_charge: 55,
    default_material_keys: ['coroplast', 'aluminum_composite', 'foam_board', 'ink'],
  },
};

const defaultBenchmarks = {
  vehicle_wraps: { label: 'Vehicle Wraps', average_sell_price_per_sqft: 18.75, average_order_total: 2850, minimum_charge: 950 },
  banners: { label: 'Banners', average_sell_price_per_sqft: 8.25, average_order_total: 245, minimum_charge: 45 },
  rigid_signs: { label: 'Rigid Signs', average_sell_price_per_sqft: 12.4, average_order_total: 310, minimum_charge: 65 },
};

export default function PricingSettings() {
  const { hasPermission, isOwner, isAdminOrOwner } = useAuth();
  const canView = hasPermission(Permission.SETTINGS_VIEW) || isAdminOrOwner();
  const canEdit = hasPermission(Permission.SETTINGS_EDIT) || isOwner();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [settings, setSettings] = useState(null);

  const getToken = () => localStorage.getItem('auth_token');

  const fetchSettings = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/pricing/defaults`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Failed to load settings');

      const data = await response.json();
      setSettings({
        ...data,
        materials: (data.materials || MATERIAL_PRESETS).map(createMaterial),
        category_defaults: { ...defaultCategoryDefaults, ...(data.category_defaults || {}) },
        selling_price_benchmarks: { ...defaultBenchmarks, ...(data.selling_price_benchmarks || {}) },
      });
      setHasChanges(false);
    } catch (error) {
      toast.error('Failed to load pricing settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const updateSettings = (updater) => {
    setSettings((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      return next;
    });
    setHasChanges(true);
  };

  const updateMaterial = (id, field, value) => {
    updateSettings((current) => ({
      ...current,
      materials: current.materials.map((material) =>
        material.id === id ? { ...material, [field]: value } : material
      ),
    }));
  };

  const addMaterial = (preset = null) => {
    const seed = preset || { key: '', name: 'Custom Material', category: 'material', unit_type: 'sqft' };
    updateSettings((current) => ({
      ...current,
      materials: [...current.materials, createMaterial(seed)],
    }));
  };

  const removeMaterial = (id) => {
    updateSettings((current) => ({
      ...current,
      materials: current.materials.filter((material) => material.id !== id),
    }));
  };

  const updateCategory = (categoryKey, field, value) => {
    updateSettings((current) => ({
      ...current,
      category_defaults: {
        ...current.category_defaults,
        [categoryKey]: {
          ...current.category_defaults[categoryKey],
          [field]: value,
        },
      },
    }));
  };

  const toggleCategoryMaterial = (categoryKey, materialKey, checked) => {
    const existing = settings.category_defaults[categoryKey]?.default_material_keys || [];
    const nextKeys = checked
      ? [...new Set([...existing, materialKey])]
      : existing.filter((key) => key !== materialKey);

    updateCategory(categoryKey, 'default_material_keys', nextKeys);
  };

  const updateBenchmark = (categoryKey, field, value) => {
    updateSettings((current) => ({
      ...current,
      selling_price_benchmarks: {
        ...current.selling_price_benchmarks,
        [categoryKey]: {
          ...current.selling_price_benchmarks[categoryKey],
          [field]: value,
        },
      },
    }));
  };

  const handleSave = async () => {
    const token = getToken();
    if (!token || !settings) return;

    setSaving(true);
    try {
      const payload = {
        ...settings,
        hourly_rate: Number(settings.production_hourly_rate || 0),
        design_hourly_rate: Number(settings.design_hourly_rate || 0),
        install_hourly_rate: Number(settings.installer_hourly_rate || 0),
        default_markup_percent: Math.max(0, (Number(settings.default_markup_multiplier || 1) - 1) * 100),
      };

      const response = await fetch(`${API_URL}/api/pricing/defaults`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save settings');
      }

      toast.success('Pricing & cost settings saved');
      await fetchSettings();
    } catch (error) {
      toast.error(error.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (!canView) {
    return (
      <div className="max-w-3xl mx-auto">
        <Card data-testid="pricing-settings-access-denied">
          <CardHeader>
            <CardTitle>Access denied</CardTitle>
            <CardDescription>You do not have permission to view pricing settings.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (loading || !settings) {
    return (
      <div className="flex items-center justify-center py-24" data-testid="pricing-settings-loading-state">
        <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6" data-testid="pricing-settings-page">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Link to="/pricing-calculator">
            <Button variant="outline" data-testid="pricing-settings-back-button">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to calculator
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white">Pricing & Cost Settings</h1>
            <p className="text-slate-300 mt-1 max-w-3xl">
              Set your real material costs, labor rates, overhead, category defaults, and selling benchmarks.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Badge className="bg-emerald-100 text-emerald-800" data-testid="pricing-settings-tenant-badge">
            <ShieldCheck className="h-3 w-3 mr-1" /> Tenant-isolated settings
          </Badge>
          {hasChanges && (
            <Button variant="outline" onClick={fetchSettings} data-testid="pricing-settings-reset-button">
              <RefreshCw className="h-4 w-4 mr-2" /> Reset
            </Button>
          )}
          <Button onClick={handleSave} disabled={!canEdit || saving || !hasChanges} data-testid="pricing-settings-save-button">
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
            Save changes
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card data-testid="pricing-settings-materials-summary-card">
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Tracked materials</p>
            <p className="text-2xl font-bold text-white mt-2">{settings.materials.length}</p>
          </CardContent>
        </Card>
        <Card data-testid="pricing-settings-production-rate-card">
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Production rate</p>
            <p className="text-2xl font-bold text-white mt-2">${Number(settings.production_hourly_rate || 0).toFixed(2)}</p>
          </CardContent>
        </Card>
        <Card data-testid="pricing-settings-target-margin-card">
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Target margin</p>
            <p className="text-2xl font-bold text-white mt-2">{Number(settings.target_profit_margin_percent || 0).toFixed(1)}%</p>
          </CardContent>
        </Card>
        <Card data-testid="pricing-settings-benchmarks-summary-card">
          <CardContent className="p-5">
            <p className="text-xs uppercase text-slate-400">Reference benchmarks</p>
            <p className="text-2xl font-bold text-white mt-2">{Object.keys(settings.selling_price_benchmarks || {}).length}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="materials" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4" data-testid="pricing-settings-tabs">
          <TabsTrigger value="materials" data-testid="pricing-settings-tab-materials">Material Costs</TabsTrigger>
          <TabsTrigger value="labor" data-testid="pricing-settings-tab-labor">Labor & Overhead</TabsTrigger>
          <TabsTrigger value="categories" data-testid="pricing-settings-tab-categories">Category Defaults</TabsTrigger>
          <TabsTrigger value="benchmarks" data-testid="pricing-settings-tab-benchmarks">Selling Benchmarks</TabsTrigger>
        </TabsList>

        <TabsContent value="materials" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Layers3 className="h-5 w-5 text-teal-400" /> Material cost settings
              </CardTitle>
              <CardDescription>
                Add, edit, and remove tenant-specific material costs used by your calculators.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {MATERIAL_PRESETS.map((preset) => (
                  <Button
                    key={preset.key}
                    type="button"
                    variant="outline"
                    onClick={() => addMaterial(preset)}
                    disabled={!canEdit}
                    data-testid={`pricing-add-preset-${preset.key}`}
                  >
                    <Plus className="h-4 w-4 mr-2" /> {preset.name}
                  </Button>
                ))}
              </div>

              <div className="space-y-3">
                {settings.materials.map((material, index) => (
                  <div
                    key={material.id}
                    className="grid gap-3 rounded-xl border border-slate-700 bg-slate-900/40 p-4 md:grid-cols-[1.6fr_1fr_0.8fr_0.8fr_auto]"
                    data-testid={`pricing-material-row-${index}`}
                  >
                    <div className="space-y-2">
                      <Label htmlFor={`material-name-${material.id}`}>Material name</Label>
                      <Input
                        id={`material-name-${material.id}`}
                        value={material.name}
                        onChange={(event) => updateMaterial(material.id, 'name', event.target.value)}
                        disabled={!canEdit}
                        data-testid={`pricing-material-name-${index}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`material-key-${material.id}`}>Key</Label>
                      <Input
                        id={`material-key-${material.id}`}
                        value={material.key}
                        onChange={(event) => updateMaterial(material.id, 'key', event.target.value)}
                        disabled={!canEdit}
                        data-testid={`pricing-material-key-${index}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`material-unit-${material.id}`}>Unit</Label>
                      <Input
                        id={`material-unit-${material.id}`}
                        value={material.unit_type}
                        onChange={(event) => updateMaterial(material.id, 'unit_type', event.target.value)}
                        disabled={!canEdit}
                        data-testid={`pricing-material-unit-${index}`}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`material-cost-${material.id}`}>Cost</Label>
                      <Input
                        id={`material-cost-${material.id}`}
                        type="number"
                        step="0.01"
                        value={material.cost_per_unit}
                        onChange={(event) => updateMaterial(material.id, 'cost_per_unit', Number(event.target.value || 0))}
                        disabled={!canEdit}
                        data-testid={`pricing-material-cost-${index}`}
                      />
                    </div>
                    <div className="flex items-end justify-end gap-2">
                      <div className="flex items-center gap-2 px-3 py-2 border border-slate-700 rounded-md">
                        <Label htmlFor={`material-active-${material.id}`} className="text-sm">Active</Label>
                        <Switch
                          id={`material-active-${material.id}`}
                          checked={material.is_active}
                          onCheckedChange={(checked) => updateMaterial(material.id, 'is_active', checked)}
                          disabled={!canEdit}
                          data-testid={`pricing-material-active-${index}`}
                        />
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => removeMaterial(material.id)}
                        disabled={!canEdit}
                        data-testid={`pricing-material-remove-${index}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="labor" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Factory className="h-5 w-5 text-teal-400" /> Labor, overhead, and pricing targets
              </CardTitle>
              <CardDescription>
                These values drive labor cost, total cost, and target sell price suggestions.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {[
                ['design_hourly_rate', 'Designer Hourly Rate'],
                ['production_hourly_rate', 'Production Hourly Rate'],
                ['installer_hourly_rate', 'Installer Hourly Rate'],
                ['overhead_percentage', 'Overhead Percentage'],
                ['shop_overhead_per_hour', 'Shop Overhead Per Hour'],
                ['target_profit_margin_percent', 'Target Profit Margin %'],
                ['default_markup_multiplier', 'Default Markup Multiplier'],
              ].map(([field, label]) => (
                <div key={field} className="space-y-2" data-testid={`pricing-field-${field}`}>
                  <Label htmlFor={field}>{label}</Label>
                  <Input
                    id={field}
                    type="number"
                    step="0.01"
                    value={settings[field] ?? 0}
                    onChange={(event) => updateSettings((current) => ({ ...current, [field]: Number(event.target.value || 0) }))}
                    disabled={!canEdit}
                    data-testid={`pricing-input-${field}`}
                  />
                </div>
              ))}

              <div className="rounded-xl border border-slate-700 bg-slate-900/40 p-4 space-y-3" data-testid="pricing-overhead-toggle-card">
                <div>
                  <p className="font-medium text-white">Apply overhead automatically</p>
                  <p className="text-sm text-slate-400">Adds overhead into total cost before sell price is suggested.</p>
                </div>
                <Switch
                  checked={settings.apply_overhead_to_jobs}
                  onCheckedChange={(checked) => updateSettings((current) => ({ ...current, apply_overhead_to_jobs: checked }))}
                  disabled={!canEdit}
                  data-testid="pricing-input-apply-overhead"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="categories" className="space-y-4">
          <div className="grid gap-4 xl:grid-cols-3">
            {CATEGORY_ORDER.map((category) => {
              const values = settings.category_defaults[category.key] || defaultCategoryDefaults[category.key];
              return (
                <Card key={category.key} data-testid={`pricing-category-card-${category.key}`}>
                  <CardHeader>
                    <CardTitle className="text-white">{category.label}</CardTitle>
                    <CardDescription>Defaults used when this calculator category loads.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      ['default_labor_hours_per_sqft', 'Labor Hours Per Sq Ft'],
                      ['default_markup_multiplier', 'Default Markup'],
                      ['target_profit_margin_percent', 'Target Margin %'],
                      ['minimum_charge', 'Minimum Charge'],
                    ].map(([field, label]) => (
                      <div key={field} className="space-y-2">
                        <Label htmlFor={`${category.key}-${field}`}>{label}</Label>
                        <Input
                          id={`${category.key}-${field}`}
                          type="number"
                          step="0.01"
                          value={values[field] ?? 0}
                          onChange={(event) => updateCategory(category.key, field, Number(event.target.value || 0))}
                          disabled={!canEdit}
                          data-testid={`pricing-category-${category.key}-${field}`}
                        />
                      </div>
                    ))}

                    <div className="space-y-3">
                      <Label>Default Materials Used</Label>
                      <div className="space-y-2">
                        {settings.materials.filter((material) => material.is_active).map((material) => (
                          <div key={`${category.key}-${material.id}`} className="flex items-center justify-between rounded-lg border border-slate-700 px-3 py-2">
                            <span className="text-sm text-slate-200">{material.name}</span>
                            <Switch
                              checked={(values.default_material_keys || []).includes(material.key)}
                              onCheckedChange={(checked) => toggleCategoryMaterial(category.key, material.key, checked)}
                              disabled={!canEdit}
                              data-testid={`pricing-category-${category.key}-material-${material.key}`}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="benchmarks" className="space-y-4">
          <Card data-testid="pricing-benchmark-info-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <BarChart3 className="h-5 w-5 text-teal-400" /> Selling Price Benchmarks
              </CardTitle>
              <CardDescription>
                Reference-only benchmarks. Keep these separate from actual costs so profit math stays real.
              </CardDescription>
            </CardHeader>
          </Card>

          <div className="grid gap-4 xl:grid-cols-3">
            {CATEGORY_ORDER.map((category) => {
              const values = settings.selling_price_benchmarks[category.key] || defaultBenchmarks[category.key];
              return (
                <Card key={category.key} data-testid={`pricing-benchmark-card-${category.key}`}>
                  <CardHeader>
                    <CardTitle className="text-white">{category.label}</CardTitle>
                    <CardDescription>Historical or target selling-price references.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      ['average_sell_price_per_sqft', 'Average Sell Price / Sq Ft'],
                      ['average_order_total', 'Average Order Total'],
                      ['minimum_charge', 'Reference Minimum Charge'],
                    ].map(([field, label]) => (
                      <div key={field} className="space-y-2">
                        <Label htmlFor={`${category.key}-benchmark-${field}`}>{label}</Label>
                        <Input
                          id={`${category.key}-benchmark-${field}`}
                          type="number"
                          step="0.01"
                          value={values[field] ?? 0}
                          onChange={(event) => updateBenchmark(category.key, field, Number(event.target.value || 0))}
                          disabled={!canEdit}
                          data-testid={`pricing-benchmark-${category.key}-${field}`}
                        />
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}