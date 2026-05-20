// Category Pricing Method Setup - Configure pricing methods per category

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import {
  Settings2, CheckCircle, AlertCircle, Calculator, Package, Scissors,
  Printer, Square, Shirt, Car, Wrench, Tag, PenTool, DollarSign,
} from 'lucide-react';
import BannerSetupWizard from './BannerSetupWizard';

const PRICING_METHODS = [
  { value: 'flat_price', label: 'Flat Price' },
  { value: 'price_per_sqft', label: 'Price Per Square Foot' },
  { value: 'quantity_tier', label: 'Quantity Tier' },
  { value: 'detailed_material_labor', label: 'Detailed Material + Labor' },
  { value: 'compare_methods', label: 'Compare Methods' },
  { value: 'manual_quote', label: 'Manual Quote' },
  { value: 'hourly', label: 'Hourly' },
  { value: 'package', label: 'Package Pricing' },
];

const CATEGORIES = [
  {
    id: 'banners',
    name: 'Banners',
    icon: Printer,
    color: 'blue',
    suggestedMethod: 'compare_methods',
    description: '13oz vinyl banners, mesh banners, fabric banners',
  },
  {
    id: 'yard_signs',
    name: 'Yard Signs',
    icon: Square,
    color: 'green',
    suggestedMethod: 'quantity_tier',
    description: '18x24 coroplast signs, H-stakes, volume pricing',
  },
  {
    id: 'rigid_signs',
    name: 'Rigid Signs',
    icon: Square,
    color: 'purple',
    suggestedMethod: 'compare_methods',
    description: 'Coroplast, ACM, PVC, aluminum signs',
  },
  {
    id: 'printed_vinyl',
    name: 'Printed Vinyl / Digital Print',
    icon: Printer,
    color: 'indigo',
    suggestedMethod: 'compare_methods',
    description: 'Adhesive vinyl prints, posters, decals',
  },
  {
    id: 'cut_vinyl',
    name: 'Cut Vinyl',
    icon: Scissors,
    color: 'pink',
    suggestedMethod: 'compare_methods',
    description: 'Plotter-cut decals, lettering, window graphics',
  },
  {
    id: 'vehicle_lettering',
    name: 'Vehicle Lettering / Graphics',
    icon: Car,
    color: 'orange',
    suggestedMethod: 'package',
    description: 'Door lettering, spot graphics, partial graphics',
  },
  {
    id: 'vehicle_wraps',
    name: 'Vehicle Wraps',
    icon: Car,
    color: 'red',
    suggestedMethod: 'compare_methods',
    description: 'Full wraps, partial wraps, color change',
  },
  {
    id: 'apparel',
    name: 'Apparel',
    icon: Shirt,
    color: 'teal',
    suggestedMethod: 'quantity_tier',
    description: 'T-shirts, hoodies, heat transfer vinyl',
  },
  {
    id: 'design',
    name: 'Design',
    icon: PenTool,
    color: 'violet',
    suggestedMethod: 'hourly',
    description: 'Graphic design, artwork, file prep',
  },
  {
    id: 'installation',
    name: 'Installation',
    icon: Wrench,
    color: 'amber',
    suggestedMethod: 'hourly',
    description: 'Field installation, site work',
  },
  {
    id: 'custom_promotional',
    name: 'Custom / Promotional',
    icon: Tag,
    color: 'gray',
    suggestedMethod: 'manual_quote',
    description: 'Outsourced items, custom projects, promo products',
  },
];

const STATUS_OPTIONS = [
  { value: 'not_started', label: 'Not Started', color: 'gray', icon: AlertCircle },
  { value: 'basic_setup', label: 'Basic Setup', color: 'blue', icon: Settings2 },
  { value: 'detailed_setup', label: 'Detailed Setup', color: 'green', icon: CheckCircle },
  { value: 'compare_ready', label: 'Compare Ready', color: 'purple', icon: Calculator },
  { value: 'needs_review', label: 'Needs Review', color: 'amber', icon: AlertCircle },
];

export default function CategoryPricingMethodSetup({ settings, materials, onChange, onSetupCategory, onTestCategory }) {
  const [bannerWizardOpen, setBannerWizardOpen] = useState(false);
  
  const categoryMethods = settings?.category_pricing_methods || {};
  const categoryStatus = settings?.category_setup_status || {};

  const handleMethodChange = (categoryId, method) => {
    const updated = {
      ...categoryMethods,
      [categoryId]: method,
    };
    onChange({
      ...settings,
      category_pricing_methods: updated,
    });
  };

  const handleStatusChange = (categoryId, status) => {
    const updated = {
      ...categoryStatus,
      [categoryId]: status,
    };
    onChange({
      ...settings,
      category_setup_status: updated,
    });
  };

  const handleBannerSetup = () => {
    setBannerWizardOpen(true);
  };

  const handleBannerWizardSave = (updatedSettings) => {
    onChange(updatedSettings);
    setBannerWizardOpen(false);
  };

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <Settings2 className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-blue-900">Category Pricing Method Setup</h3>
            <p className="text-xs text-blue-700 mt-1">
              Choose how you want to price each product category. You can use simple retail rates, detailed cost calculations,
              or compare multiple methods. Setup each category one at a time.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const currentMethod = categoryMethods[cat.id] || cat.suggestedMethod;
          const currentStatus = categoryStatus[cat.id] || 'not_started';
          const statusInfo = STATUS_OPTIONS.find(s => s.value === currentStatus) || STATUS_OPTIONS[0];
          const StatusIcon = statusInfo.icon;

          return (
            <Card key={cat.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg bg-${cat.color}-100`}>
                      <Icon className={`h-5 w-5 text-${cat.color}-600`} />
                    </div>
                    <div>
                      <CardTitle className="text-sm">{cat.name}</CardTitle>
                      <CardDescription className="text-xs mt-1">{cat.description}</CardDescription>
                    </div>
                  </div>
                </div>
                <div className="mt-2">
                  <Badge variant="outline" className={`text-${statusInfo.color}-700 border-${statusInfo.color}-300 bg-${statusInfo.color}-50`}>
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {statusInfo.label}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <label className="text-xs text-gray-600 mb-1 block">Pricing Method</label>
                  <Select value={currentMethod} onValueChange={(v) => handleMethodChange(cat.id, v)}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PRICING_METHODS.map(m => (
                        <SelectItem key={m.value} value={m.value} className="text-xs">
                          {m.label}
                          {m.value === cat.suggestedMethod && <span className="ml-1 text-[10px] text-violet-600">(Suggested)</span>}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-xs text-gray-600 mb-1 block">Setup Status</label>
                  <Select value={currentStatus} onValueChange={(v) => handleStatusChange(cat.id, v)}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUS_OPTIONS.map(s => (
                        <SelectItem key={s.value} value={s.value} className="text-xs">
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1 h-8 text-xs"
                    onClick={() => cat.id === 'banners' ? handleBannerSetup() : (onSetupCategory && onSetupCategory(cat.id))}
                  >
                    <Settings2 className="h-3 w-3 mr-1" />
                    Setup
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="flex-1 h-8 text-xs"
                    onClick={() => onTestCategory && onTestCategory(cat.id)}
                  >
                    <Calculator className="h-3 w-3 mr-1" />
                    Test
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Banner Setup Wizard */}
      <BannerSetupWizard
        open={bannerWizardOpen}
        onClose={() => setBannerWizardOpen(false)}
        settings={settings}
        materials={materials || []}
        onSave={handleBannerWizardSave}
      />
    </div>
  );
}
