import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Slider } from '../components/ui/slider';
import { Separator } from '../components/ui/separator';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { 
  Calculator, DollarSign, Clock, TrendingUp, Package, 
  Scissors, Printer, Square, Shirt, Car, Wrench, Tag,
  ChevronDown, ChevronUp, AlertCircle, CheckCircle, Loader2,
  Save, Star, Trash2, FolderOpen, Sparkles, Lightbulb, Target
} from 'lucide-react';
import { toast } from 'sonner';
import { useAICreditGuard } from './credits/AICreditConfirmationDialog';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Category definitions with icons
const PRICING_CATEGORIES = [
  { id: 'promotional', name: 'Promotional Items', icon: Tag, description: 'Magnets, yard signs, stickers, branded items' },
  { id: 'cut_vinyl', name: 'Cut Vinyl', icon: Scissors, description: 'Decals, lettering, graphics' },
  { id: 'services', name: 'Services', icon: Wrench, description: 'Design, installation, removal, site survey' },
  { id: 'digital_print', name: 'Digital Print', icon: Printer, description: 'Banners, posters, prints' },
  { id: 'rigid_signs', name: 'Rigid Signs', icon: Square, description: 'Coroplast, aluminum, PVC signs' },
  { id: 'apparel', name: 'Apparel', icon: Shirt, description: 'T-shirts, hoodies, hats' },
  { id: 'vehicle_graphics', name: 'Vehicle Graphics', icon: Car, description: 'Wraps, lettering, partial graphics' },
  { id: 'custom', name: 'Custom / Other', icon: Package, description: 'Manual entry for anything else' },
];

// Service types
const SERVICE_TYPES = [
  { id: 'design', name: 'Design / Artwork' },
  { id: 'installation', name: 'Installation' },
  { id: 'removal', name: 'Removal / Demolition' },
  { id: 'site_survey', name: 'Site Survey' },
  { id: 'consultation', name: 'Consultation' },
  { id: 'travel', name: 'Travel / Mileage' },
  { id: 'other_labor', name: 'Other Labor' },
];

// Vinyl types
const VINYL_TYPES = [
  { id: 'oracal_651', name: 'Oracal 651 (Intermediate)' },
  { id: 'oracal_751', name: 'Oracal 751 (High Performance)' },
  { id: 'oracal_951', name: 'Oracal 951 (Premium Cast)' },
  { id: 'avery_hp750', name: 'Avery HP750' },
  { id: 'reflective', name: 'Reflective Vinyl' },
  { id: 'specialty', name: 'Specialty Vinyl' },
];

// Print materials
const PRINT_MATERIALS = [
  { id: 'banner_13oz', name: '13oz Banner' },
  { id: 'banner_18oz', name: '18oz Banner (Heavy)' },
  { id: 'vinyl_adhesive', name: 'Adhesive Vinyl' },
  { id: 'poster_paper', name: 'Poster Paper' },
  { id: 'canvas', name: 'Canvas' },
  { id: 'backlit', name: 'Backlit Film' },
  { id: 'perforated', name: 'Perforated Window Film' },
];

// Substrate types
const SUBSTRATE_TYPES = [
  { id: 'coroplast_4mm', name: 'Coroplast 4mm' },
  { id: 'coroplast_10mm', name: 'Coroplast 10mm' },
  { id: 'aluminum_040', name: 'Aluminum .040' },
  { id: 'aluminum_063', name: 'Aluminum .063' },
  { id: 'aluminum_080', name: 'Aluminum .080' },
  { id: 'pvc_3mm', name: 'PVC 3mm' },
  { id: 'pvc_6mm', name: 'PVC 6mm' },
  { id: 'acrylic', name: 'Acrylic' },
  { id: 'dibond', name: 'Dibond/ACM' },
  { id: 'mdo', name: 'MDO Plywood' },
];

// Apparel types
const APPAREL_TYPES = [
  { id: 'tshirt', name: 'T-Shirt' },
  { id: 'hoodie', name: 'Hoodie' },
  { id: 'hat', name: 'Hat/Cap' },
  { id: 'polo', name: 'Polo Shirt' },
  { id: 'tank', name: 'Tank Top' },
  { id: 'longsleeve', name: 'Long Sleeve' },
  { id: 'jacket', name: 'Jacket' },
];

// Transfer types
const TRANSFER_TYPES = [
  { id: 'htv', name: 'HTV (Heat Transfer Vinyl)' },
  { id: 'screen_print', name: 'Screen Print' },
  { id: 'dtf', name: 'DTF (Direct to Film)' },
  { id: 'sublimation', name: 'Sublimation' },
  { id: 'embroidery', name: 'Embroidery' },
];

// Vehicle types
const VEHICLE_TYPES = [
  { id: 'car_sedan', name: 'Car (Sedan)' },
  { id: 'car_suv', name: 'Car (SUV)' },
  { id: 'van_mini', name: 'Minivan' },
  { id: 'van_cargo', name: 'Cargo Van' },
  { id: 'van_sprinter', name: 'Sprinter Van' },
  { id: 'box_truck_12ft', name: 'Box Truck (12ft)' },
  { id: 'box_truck_16ft', name: 'Box Truck (16ft)' },
  { id: 'box_truck_24ft', name: 'Box Truck (24ft)' },
  { id: 'trailer', name: 'Trailer' },
  { id: 'semi', name: 'Semi Truck' },
];

// Coverage types
const COVERAGE_TYPES = [
  { id: 'spot', name: 'Spot Graphics (15%)' },
  { id: 'partial', name: 'Partial Wrap (40%)' },
  { id: 'half', name: 'Half Wrap (50%)' },
  { id: 'full', name: 'Full Wrap (100%)' },
];

// Promo product types
const PROMO_PRODUCT_TYPES = [
  { id: 'magnets', name: 'Magnets' },
  { id: 'yard_signs', name: 'Yard Signs' },
  { id: 'license_plates', name: 'License Plates' },
  { id: 'stickers', name: 'Stickers' },
  { id: 'branded_items', name: 'Branded Items' },
  { id: 'custom', name: 'Custom One-Off' },
];

// Print locations
const PRINT_LOCATIONS = [
  { id: 'front', name: 'Front' },
  { id: 'back', name: 'Back' },
  { id: 'left_sleeve', name: 'Left Sleeve' },
  { id: 'right_sleeve', name: 'Right Sleeve' },
  { id: 'left_chest', name: 'Left Chest' },
  { id: 'right_chest', name: 'Right Chest' },
];

const renderSuggestionText = (text) => {
  const lines = String(text || '').split('\n');
  const renderInline = (line) => {
    const parts = line.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={`bold-${index}`}>{part.slice(2, -2)}</strong>;
      }
      return <span key={`text-${index}`}>{part}</span>;
    });
  };

  return lines.map((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return <div key={`line-${index}`} className="h-2" />;
    if (trimmed.startsWith('- ')) {
      return (
        <div key={`line-${index}`} className="flex items-start gap-2">
          <span className="mt-1 text-slate-400">•</span>
          <p>{renderInline(trimmed.slice(2))}</p>
        </div>
      );
    }
    return <p key={`line-${index}`}>{renderInline(line)}</p>;
  });
};

export default function PricingCalculator({ 
  onCalculationComplete, 
  initialCategory = null,
  initialData = null,
  embedded = false 
}) {
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const [category, setCategory] = useState(initialCategory || '');
  const [quantity, setQuantity] = useState(1);
  const [complexity, setComplexity] = useState(1);  // Default to 1 (simple) - was 5
  const [pricingData, setPricingData] = useState(initialData || {});
  const [foundationDefaults, setFoundationDefaults] = useState(null);
  const [includeSetupFee, setIncludeSetupFee] = useState(false);  // Setup fee is opt-in
  // Initialize calculation with zeros instead of null
  const [calculation, setCalculation] = useState({
    material_cost: 0,
    labor_cost: 0,
    setup_cost: 0,
    additional_costs: 0,
    overhead_cost: 0,
    production_cost: 0,
    total_cost: 0,
    suggested_price: 0,
    selling_price: 0,
    markup_percent: 0,
    profit_margin_percent: 0,
    profit_amount: 0,
    estimated_labor_minutes: 0,
    breakdown: {}
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [overrideEnabled, setOverrideEnabled] = useState(false);
  const [overridePrice, setOverridePrice] = useState('');
  const [showBreakdown, setShowBreakdown] = useState(true);
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  
  // AI Suggestions state
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [loadingAiSuggestions, setLoadingAiSuggestions] = useState(false);
  const [showAiSuggestions, setShowAiSuggestions] = useState(false);
  
  // Template state
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDesc, setTemplateDesc] = useState('');
  const [savingTemplate, setSavingTemplate] = useState(false);

  // Get auth token
  const getToken = () => getAuthToken();

  useEffect(() => {
    const loadDefaults = async () => {
      const token = getToken();
      if (!token) return;
      try {
        const response = await fetch(`${API_URL}/api/pricing/defaults`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) return;
        const data = await response.json();
        setFoundationDefaults(data);
      } catch {
        // Ignore defaults load failures
      }
    };
    loadDefaults();
  }, []);

  // Fetch AI-powered pricing suggestions
  const fetchAiSuggestions = async () => {
    if (!category || !calculation) return;
    
    const token = getToken();
    if (!token) return;
    
    await runGuardedAction({
      actionType: 'pricing_advisor',
      featureName: 'AI Pricing Advisor',
      execute: async () => {
        setLoadingAiSuggestions(true);
        try {
          const response = await fetch(`${API_URL}/api/ai/generate`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              tool: 'pricing_advisor',
              input_data: {
                category: category,
                quantity: quantity,
                current_price: calculation?.selling_price || calculation?.suggested_price || 0,
                production_cost: calculation?.production_cost || 0,
                profit_margin: calculation?.profit_margin_percent || 0,
                complexity: complexity,
                pricing_data: pricingData,
                breakdown: calculation?.breakdown || {}
              }
            })
          });
          
          if (response.ok) {
            const data = await response.json();
            setAiSuggestions(data.content);
            setShowAiSuggestions(true);
            toast.success('AI suggestions generated!');
            return data;
          }
          toast.error('Failed to get AI suggestions');
          throw new Error('Failed to get AI suggestions');
        } catch (err) {
          console.error('Error fetching AI suggestions:', err);
          toast.error(err.message || 'Failed to connect to AI service');
          throw err;
        } finally {
          setLoadingAiSuggestions(false);
        }
      }
    });
  };

  // Fetch templates
  const fetchTemplates = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pricing/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // Save template
  const handleSaveTemplate = async () => {
    if (!templateName.trim() || !category) {
      toast.error('Please enter a template name');
      return;
    }

    const token = getToken();
    setSavingTemplate(true);

    try {
      const response = await fetch(`${API_URL}/api/pricing/templates`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: templateName,
          description: templateDesc,
          category,
          pricing_data: { ...pricingData, complexity },
          quantity
        })
      });

      if (response.ok) {
        toast.success('Template saved!');
        setShowSaveDialog(false);
        setTemplateName('');
        setTemplateDesc('');
        fetchTemplates();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to save template');
      }
    } catch (err) {
      toast.error('Network error');
    } finally {
      setSavingTemplate(false);
    }
  };

  // Load template
  const handleLoadTemplate = (template) => {
    setCategory(template.category);
    setPricingData(template.pricing_data || {});
    setQuantity(template.quantity || 1);
    setComplexity(template.pricing_data?.complexity || 1);
    setDescription(template.name);
    setShowTemplates(false);
    toast.success(`Loaded: ${template.name}`);
  };

  // Delete template
  const handleDeleteTemplate = async (templateId, e) => {
    e.stopPropagation();
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/api/pricing/templates/${templateId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Template deleted');
        fetchTemplates();
      }
    } catch (err) {
      toast.error('Failed to delete template');
    }
  };

  // Toggle favorite
  const handleToggleFavorite = async (templateId, e) => {
    e.stopPropagation();
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/api/pricing/templates/${templateId}/favorite`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        fetchTemplates();
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  // Calculate pricing
  const calculatePrice = useCallback(async () => {
    if (!category) return;
    
    const token = getToken();
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/pricing/calculate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          category,
          pricing_data: {
            ...pricingData,
            category,
            complexity,
            include_setup_fee: includeSetupFee  // Pass the setup fee toggle
          },
          quantity
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCalculation(data);
      } else {
        const err = await response.json();
        setError(err.detail || 'Calculation failed');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  }, [category, pricingData, quantity, complexity, includeSetupFee]);

  // Auto-calculate when inputs change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (category) {
        calculatePrice();
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [category, pricingData, quantity, complexity, includeSetupFee, calculatePrice]);

  // Handle adding item
  const handleAddItem = () => {
    if (!calculation && !overrideEnabled) return;

    const finalPrice = overrideEnabled && overridePrice 
      ? parseFloat(overridePrice) 
      : calculation?.selling_price || calculation?.suggested_price || 0;

    const totalCost = calculation?.total_cost || calculation?.production_cost || 0;
    const profitAmount = finalPrice - totalCost;
    const profitMarginPercent = finalPrice > 0 ? Number(((profitAmount / finalPrice) * 100).toFixed(1)) : 0;

    const costSnapshot = {
      material_cost: calculation?.material_cost || 0,
      labor_cost: calculation?.labor_cost || 0,
      setup_cost: calculation?.setup_cost || 0,
      additional_costs: calculation?.additional_costs || 0,
      overhead_cost: calculation?.overhead_cost || 0,
      total_cost: totalCost,
      selling_price: finalPrice,
      profit: profitAmount,
      profit_margin: profitMarginPercent,
      profit_amount: profitAmount,
      profit_margin_percent: profitMarginPercent,
      estimated_labor_minutes: calculation?.estimated_labor_minutes || 0,
      breakdown: calculation?.breakdown || {}
    };

    const itemData = {
      category,
      description: description || getCategoryName(category),
      quantity,
      unit_price: finalPrice / quantity,
      line_total: finalPrice,
      pricing_category: category,
      pricing_data: {
        ...pricingData,
        category,
        complexity,
        price_override: overrideEnabled ? parseFloat(overridePrice) : null,
        override_enabled: overrideEnabled
      },
      pricing_calculation: calculation,
      cost_snapshot: costSnapshot,
      production_cost: totalCost,
      profit_amount: profitAmount,
      profit_margin_percent: profitMarginPercent,
      notes
    };

    if (onCalculationComplete) {
      onCalculationComplete(itemData);
    }
  };

  const getCategoryName = (catId) => {
    return PRICING_CATEGORIES.find(c => c.id === catId)?.name || 'Item';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  // Render category-specific fields
  const renderCategoryFields = () => {
    switch (category) {
      case 'promotional':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Product Type</Label>
                <Select 
                  value={pricingData.promo_product_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, promo_product_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    {PROMO_PRODUCT_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Unit Cost ($)</Label>
                <Input 
                  type="number" 
                  step="0.01"
                  value={pricingData.unit_cost || ''} 
                  onChange={(e) => setPricingData({...pricingData, unit_cost: parseFloat(e.target.value) || 0})}
                  placeholder="Your cost per item"
                />
              </div>
            </div>
            <div>
              <Label>Markup %</Label>
              <Input 
                type="number" 
                value={pricingData.markup_percent ?? 100} 
                onChange={(e) => setPricingData({...pricingData, markup_percent: parseFloat(e.target.value) || 0})}
                placeholder="100 = 2x markup"
              />
              <p className="text-xs text-slate-400 mt-1">100% markup doubles the price</p>
            </div>
          </div>
        );

      case 'cut_vinyl':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Width (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.width_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, width_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Length (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.length_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, length_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Sq Ft (auto)</Label>
                <Input 
                  type="number" 
                  value={((pricingData.width_inches || 0) * (pricingData.length_inches || 0) / 144).toFixed(2)} 
                  disabled
                  className="bg-slate-100"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vinyl Type</Label>
                <Select 
                  value={pricingData.vinyl_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, vinyl_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select vinyl" /></SelectTrigger>
                  <SelectContent>
                    {VINYL_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Number of Colors</Label>
                <Input 
                  type="number" 
                  min="1"
                  value={pricingData.num_colors || 1} 
                  onChange={(e) => setPricingData({...pricingData, num_colors: parseInt(e.target.value) || 1})}
                />
              </div>
            </div>
          </div>
        );

      case 'services':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Service Type</Label>
                <Select 
                  value={pricingData.service_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, service_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select service" /></SelectTrigger>
                  <SelectContent>
                    {SERVICE_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Estimated Hours</Label>
                <Input 
                  type="number" 
                  step="0.5"
                  value={pricingData.estimated_hours || ''} 
                  onChange={(e) => setPricingData({...pricingData, estimated_hours: parseFloat(e.target.value) || 0})}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Number of Workers</Label>
                <Input 
                  type="number" 
                  min="1"
                  value={pricingData.num_workers || 1} 
                  onChange={(e) => setPricingData({...pricingData, num_workers: parseInt(e.target.value) || 1})}
                />
              </div>
              <div>
                <Label>Distance (miles)</Label>
                <Input 
                  type="number" 
                  value={pricingData.distance_miles || ''} 
                  onChange={(e) => setPricingData({...pricingData, distance_miles: parseFloat(e.target.value) || 0})}
                  placeholder="For travel cost"
                />
              </div>
            </div>
            <div>
              <Label>Hourly Rate Override ($)</Label>
              <Input 
                type="number" 
                step="0.01"
                value={pricingData.hourly_rate_override || ''} 
                onChange={(e) => setPricingData({...pricingData, hourly_rate_override: parseFloat(e.target.value) || null})}
                placeholder="Leave blank for default"
              />
            </div>
          </div>
        );

      case 'digital_print':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Width (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.width_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, width_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Length (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.length_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, length_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Sq Ft</Label>
                <Input 
                  value={((pricingData.width_inches || 0) * (pricingData.length_inches || 0) / 144).toFixed(2)} 
                  disabled
                  className="bg-slate-100"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Material</Label>
                <Select 
                  value={pricingData.print_material || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, print_material: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select material" /></SelectTrigger>
                  <SelectContent>
                    {PRINT_MATERIALS.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <div className="flex items-center gap-2">
                  <Checkbox 
                    id="laminate"
                    checked={pricingData.laminate || false}
                    onCheckedChange={(c) => setPricingData({...pricingData, laminate: c})}
                  />
                  <Label htmlFor="laminate" className="cursor-pointer">Add Laminate</Label>
                </div>
              </div>
            </div>
          </div>
        );

      case 'rigid_signs':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Width (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.width_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, width_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Length (inches)</Label>
                <Input 
                  type="number" 
                  value={pricingData.length_inches || ''} 
                  onChange={(e) => setPricingData({...pricingData, length_inches: parseFloat(e.target.value) || 0})}
                />
              </div>
              <div>
                <Label>Sq Ft</Label>
                <Input 
                  value={((pricingData.width_inches || 0) * (pricingData.length_inches || 0) / 144).toFixed(2)} 
                  disabled
                  className="bg-slate-100"
                />
              </div>
            </div>
            <div>
              <Label>Substrate</Label>
              <Select 
                value={pricingData.substrate_type || ''} 
                onValueChange={(v) => setPricingData({...pricingData, substrate_type: v})}
              >
                <SelectTrigger><SelectValue placeholder="Select substrate" /></SelectTrigger>
                <SelectContent>
                  {SUBSTRATE_TYPES.map(t => (
                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-6">
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="double_sided"
                  checked={pricingData.double_sided || false}
                  onCheckedChange={(c) => setPricingData({...pricingData, double_sided: c})}
                />
                <Label htmlFor="double_sided" className="cursor-pointer">Double-Sided</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="laminate_sign"
                  checked={pricingData.laminate || false}
                  onCheckedChange={(c) => setPricingData({...pricingData, laminate: c})}
                />
                <Label htmlFor="laminate_sign" className="cursor-pointer">Laminate</Label>
              </div>
            </div>
          </div>
        );

      case 'apparel':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Apparel Type</Label>
                <Select 
                  value={pricingData.apparel_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, apparel_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    {APPAREL_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Transfer Type</Label>
                <Select 
                  value={pricingData.transfer_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, transfer_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select transfer" /></SelectTrigger>
                  <SelectContent>
                    {TRANSFER_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Number of Colors</Label>
                <Input 
                  type="number" 
                  min="1"
                  value={pricingData.num_colors || 1} 
                  onChange={(e) => setPricingData({...pricingData, num_colors: parseInt(e.target.value) || 1})}
                />
              </div>
              <div>
                <Label>Blank Cost Override ($)</Label>
                <Input 
                  type="number" 
                  step="0.01"
                  value={pricingData.blank_cost_override || ''} 
                  onChange={(e) => setPricingData({...pricingData, blank_cost_override: parseFloat(e.target.value) || null})}
                  placeholder="Leave blank for default"
                />
              </div>
            </div>
            <div>
              <Label>Print Locations</Label>
              <div className="flex flex-wrap gap-3 mt-2">
                {PRINT_LOCATIONS.map(loc => (
                  <div key={loc.id} className="flex items-center gap-2">
                    <Checkbox 
                      id={`loc_${loc.id}`}
                      checked={(pricingData.print_locations || []).includes(loc.id)}
                      onCheckedChange={(c) => {
                        const current = pricingData.print_locations || [];
                        const updated = c 
                          ? [...current, loc.id]
                          : current.filter(l => l !== loc.id);
                        setPricingData({
                          ...pricingData, 
                          print_locations: updated,
                          num_print_locations: updated.length || 1
                        });
                      }}
                    />
                    <Label htmlFor={`loc_${loc.id}`} className="cursor-pointer text-sm">{loc.name}</Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'vehicle_graphics':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vehicle Type</Label>
                <Select 
                  value={pricingData.vehicle_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, vehicle_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select vehicle" /></SelectTrigger>
                  <SelectContent>
                    {VEHICLE_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Coverage</Label>
                <Select 
                  value={pricingData.coverage_type || ''} 
                  onValueChange={(v) => setPricingData({...pricingData, coverage_type: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select coverage" /></SelectTrigger>
                  <SelectContent>
                    {COVERAGE_TYPES.map(t => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vehicle Make</Label>
                <Input 
                  value={pricingData.vehicle_make || ''} 
                  onChange={(e) => setPricingData({...pricingData, vehicle_make: e.target.value})}
                  placeholder="e.g., Ford"
                />
              </div>
              <div>
                <Label>Vehicle Model</Label>
                <Input 
                  value={pricingData.vehicle_model || ''} 
                  onChange={(e) => setPricingData({...pricingData, vehicle_model: e.target.value})}
                  placeholder="e.g., Transit"
                />
              </div>
            </div>
            <div>
              <Label>Install Difficulty (1-10)</Label>
              <div className="flex items-center gap-4 mt-2">
                <Slider
                  value={[pricingData.install_difficulty || 5]}
                  onValueChange={(v) => setPricingData({...pricingData, install_difficulty: v[0]})}
                  min={1}
                  max={10}
                  step={1}
                  className="flex-1"
                />
                <span className="w-8 text-center font-medium">{pricingData.install_difficulty || 5}</span>
              </div>
            </div>
          </div>
        );

      case 'custom':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Unit Cost ($)</Label>
                <Input 
                  type="number" 
                  step="0.01"
                  value={pricingData.unit_cost || ''} 
                  onChange={(e) => setPricingData({...pricingData, unit_cost: parseFloat(e.target.value) || 0})}
                  placeholder="Your cost per item"
                />
              </div>
              <div>
                <Label>Markup %</Label>
                <Input 
                  type="number" 
                  value={pricingData.markup_percent ?? 100} 
                  onChange={(e) => setPricingData({...pricingData, markup_percent: parseFloat(e.target.value) || 0})}
                />
              </div>
            </div>
            <p className="text-sm text-slate-500">
              Use this for any item not covered by other categories. Enter your cost and desired markup.
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={embedded ? '' : 'max-w-4xl mx-auto'}>
      {creditDialog}
      <Card className="border-slate-200">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-teal-100 flex items-center justify-center">
                <Calculator className="h-5 w-5 text-teal-600" />
              </div>
              <div>
                <CardTitle>Pricing Calculator</CardTitle>
                <CardDescription>Calculate pricing for order items</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowTemplates(true)}
                className="border-slate-300"
                data-testid="pricing-templates-button"
              >
                <FolderOpen className="h-4 w-4 mr-2" />
                Templates ({templates.length})
              </Button>
              {category && calculation && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setShowSaveDialog(true)}
                  className="border-teal-300 text-teal-600 hover:bg-teal-50"
                  data-testid="pricing-save-template-button"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save as Template
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Category Selection */}
          <div>
            <Label className="text-base font-medium">Item Category</Label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
              {PRICING_CATEGORIES.map((cat) => {
                const Icon = cat.icon;
                return (
                  <button
                    key={cat.id}
                    onClick={() => {
                      setCategory(cat.id);
                      setPricingData({});
                      setCalculation(null);
                    }}
                    data-testid={`pricing-category-${cat.id}`}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      category === cat.id
                        ? 'border-teal-500 bg-teal-50 ring-1 ring-teal-500'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className={`h-5 w-5 mb-1 ${category === cat.id ? 'text-teal-600' : 'text-slate-400'}`} />
                    <p className={`text-sm font-medium ${category === cat.id ? 'text-teal-700' : 'text-slate-700'}`}>
                      {cat.name}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {foundationDefaults && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600" data-testid="pricing-foundation-defaults-summary">
              <p className="text-xs font-medium text-slate-700">Pricing Foundation Defaults</p>
              <div className="flex flex-wrap gap-4 mt-1">
                <span>Markup: {foundationDefaults.default_markup_multiplier}x</span>
                <span>Target Margin: {foundationDefaults.target_profit_margin_percent}%</span>
                <span>Overhead: {foundationDefaults.overhead_percentage}%</span>
              </div>
            </div>
          )}

          {category && (
            <>
              <Separator />

              {/* Description */}
              <div>
                <Label>Item Description</Label>
                <Input 
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={`e.g., ${getCategoryName(category)} for customer`}
                  className="mt-1"
                  data-testid="pricing-description-input"
                />
              </div>

              {/* Category-specific fields */}
              <div className="p-4 bg-slate-50 rounded-lg">
                {renderCategoryFields()}
              </div>

              {/* Quantity, Complexity, and Setup Fee */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <Label>Quantity</Label>
                  <Input 
                    type="number" 
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    className="mt-1"
                    data-testid="pricing-quantity-input"
                  />
                </div>
                <div>
                  <Label>Complexity (1-10)</Label>
                  <div className="flex items-center gap-4 mt-1">
                    <Slider
                      value={[complexity]}
                      onValueChange={(v) => setComplexity(v[0])}
                      min={1}
                      max={10}
                      step={1}
                      className="flex-1"
                    />
                    <Badge variant="outline" className="w-8 justify-center">{complexity}</Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">1=Simple, 10=Very Complex</p>
                </div>
                <div>
                  <Label>Setup Fee</Label>
                  <div className="flex items-center gap-3 mt-2 p-3 border rounded-lg bg-white">
                    <Checkbox 
                      id="include_setup"
                      checked={includeSetupFee}
                      onCheckedChange={setIncludeSetupFee}
                      data-testid="pricing-setup-fee-checkbox"
                    />
                    <div className="flex-1">
                      <Label htmlFor="include_setup" className="cursor-pointer font-normal">
                        Include Setup Fee
                      </Label>
                      <p className="text-xs text-slate-400">One-time fee per order</p>
                    </div>
                    {includeSetupFee && (
                      <Input 
                        type="number" 
                        step="0.01"
                        value={pricingData.setup_fee || ''}
                        onChange={(e) => setPricingData({...pricingData, setup_fee: parseFloat(e.target.value) || 0})}
                        placeholder="$15"
                        className="w-20"
                      />
                    )}
                  </div>
                </div>
              </div>

              <Separator />

              {/* Pricing Results */}
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-teal-500" />
                  <span className="ml-2 text-slate-500">Calculating...</span>
                </div>
              ) : error ? (
                <div className="flex items-center gap-2 text-red-600 py-4">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              ) : calculation ? (
                <div className="space-y-4">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
                    <div className="p-4 bg-slate-100 rounded-lg" data-testid="pricing-material-cost-card">
                      <p className="text-xs text-slate-500 uppercase">Material</p>
                      <p className="text-xl font-bold text-slate-700">{formatCurrency(calculation.material_cost)}</p>
                    </div>
                    <div className="p-4 bg-amber-100 rounded-lg" data-testid="pricing-labor-cost-card">
                      <p className="text-xs text-amber-700 uppercase">Labor</p>
                      <p className="text-xl font-bold text-amber-800">{formatCurrency(calculation.labor_cost)}</p>
                    </div>
                    <div className="p-4 bg-violet-100 rounded-lg" data-testid="pricing-overhead-cost-card">
                      <p className="text-xs text-violet-700 uppercase">Overhead</p>
                      <p className="text-xl font-bold text-violet-800">{formatCurrency(calculation.overhead_cost || 0)}</p>
                    </div>
                    <div className="p-4 bg-slate-100 rounded-lg" data-testid="pricing-total-cost-card">
                      <p className="text-xs text-slate-500 uppercase">Total Cost</p>
                      <p className="text-xl font-bold text-slate-700">{formatCurrency(calculation.total_cost || calculation.production_cost)}</p>
                    </div>
                    <div className="p-4 bg-teal-100 rounded-lg" data-testid="pricing-selling-price-card">
                      <p className="text-xs text-teal-600 uppercase">Selling Price</p>
                      <p className="text-xl font-bold text-teal-700">{formatCurrency(calculation.selling_price || calculation.suggested_price)}</p>
                    </div>
                    <div className="p-4 bg-green-100 rounded-lg" data-testid="pricing-profit-card">
                      <p className="text-xs text-green-600 uppercase">Profit</p>
                      <p className="text-xl font-bold text-green-700">{formatCurrency(calculation.profit_amount)}</p>
                      <p className="text-xs text-green-700 mt-1">{calculation.profit_margin_percent}% margin</p>
                    </div>
                  </div>

                  {/* Breakdown Toggle */}
                  <button
                    onClick={() => setShowBreakdown(!showBreakdown)}
                    className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800"
                    data-testid="pricing-breakdown-toggle"
                  >
                    {showBreakdown ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    {showBreakdown ? 'Hide' : 'Show'} Pricing Breakdown
                  </button>

                  {showBreakdown && (
                    <div className="p-4 bg-slate-50 rounded-lg space-y-2 text-sm">
                      <div className="flex justify-between" data-testid="pricing-breakdown-material-cost">
                        <span className="text-slate-600">Material Cost:</span>
                        <span className="font-medium">{formatCurrency(calculation.material_cost)}</span>
                      </div>
                      <div className="flex justify-between" data-testid="pricing-breakdown-labor-cost">
                        <span className="text-slate-600">Labor Cost:</span>
                        <span className="font-medium">{formatCurrency(calculation.labor_cost)}</span>
                      </div>
                      <div className="flex justify-between" data-testid="pricing-breakdown-overhead-cost">
                        <span className="text-slate-600">Overhead:</span>
                        <span className="font-medium">{formatCurrency(calculation.overhead_cost || 0)}</span>
                      </div>
                      {calculation.setup_cost > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600">Setup Cost:</span>
                          <span className="font-medium">{formatCurrency(calculation.setup_cost)}</span>
                        </div>
                      )}
                      {calculation.additional_costs > 0 && (
                        <div className="flex justify-between">
                          <span className="text-slate-600">Additional Costs:</span>
                          <span className="font-medium">{formatCurrency(calculation.additional_costs)}</span>
                        </div>
                      )}
                      <div className="flex justify-between pt-2 border-t border-slate-200" data-testid="pricing-breakdown-total-cost">
                        <span className="text-slate-700 font-medium">Total Cost:</span>
                        <span className="font-semibold">{formatCurrency(calculation.total_cost || calculation.production_cost)}</span>
                      </div>
                      <div className="flex justify-between" data-testid="pricing-breakdown-selling-price">
                        <span className="text-slate-700 font-medium">Selling Price:</span>
                        <span className="font-semibold text-teal-700">{formatCurrency(calculation.selling_price || calculation.suggested_price)}</span>
                      </div>
                      <div className="flex justify-between" data-testid="pricing-breakdown-profit">
                        <span className="text-slate-700 font-medium">Profit:</span>
                        <span className="font-semibold text-green-700">{formatCurrency(calculation.profit_amount)}</span>
                      </div>
                      {calculation.estimated_labor_minutes > 0 && (
                        <div className="flex justify-between pt-2 border-t border-slate-200">
                          <span className="text-slate-600">Estimated Labor:</span>
                          <span className="font-medium flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {Math.round(calculation.estimated_labor_minutes)} min
                          </span>
                        </div>
                      )}
                      {calculation.breakdown && Object.keys(calculation.breakdown).length > 0 && (
                        <div className="pt-2 border-t border-slate-200">
                          <p className="text-xs text-slate-500 uppercase mb-2">Details</p>
                          {Object.entries(calculation.breakdown).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-xs">
                              <span className="text-slate-500">{key.replace(/_/g, ' ')}:</span>
                              <span className="text-slate-700">
                                {typeof value === 'number' ? 
                                  (key.includes('cost') || key.includes('price') ? formatCurrency(value) : value) 
                                  : Array.isArray(value) ? value.join(', ') : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* AI Pricing Suggestions */}
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                          <Sparkles className="h-4 w-4 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium text-purple-900">AI Pricing Advisor</p>
                          <p className="text-xs text-purple-600">Get smart pricing recommendations</p>
                        </div>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={fetchAiSuggestions}
                        disabled={loadingAiSuggestions}
                        className="border-purple-300 text-purple-700 hover:bg-purple-100"
                        data-testid="pricing-ai-suggestions-button"
                      >
                        {loadingAiSuggestions ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Lightbulb className="h-4 w-4 mr-2" />
                            Get Suggestions
                          </>
                        )}
                      </Button>
                    </div>
                    
                    {showAiSuggestions && aiSuggestions && (
                      <div className="mt-4 p-4 bg-white rounded-lg border border-purple-100">
                        <div className="flex items-center gap-2 mb-3">
                          <Target className="h-4 w-4 text-purple-600" />
                          <span className="text-sm font-medium text-purple-800">AI Recommendations</span>
                        </div>
                        <div className="prose prose-sm prose-purple max-w-none">
                          <div className="text-sm text-slate-700 space-y-2">
                            {/* Render AI suggestions as safe JSX instead of raw HTML to prevent XSS. */}
                            {renderSuggestionText(aiSuggestions)}
                          </div>
                        </div>
                        <button
                          onClick={() => setShowAiSuggestions(false)}
                          className="mt-3 text-xs text-purple-600 hover:text-purple-800"
                        >
                          Hide suggestions
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Price Override */}
                  <div className="p-4 border-2 border-dashed border-slate-300 rounded-lg">
                    <div className="flex items-center gap-2 mb-3">
                      <Checkbox 
                        id="override"
                        checked={overrideEnabled}
                        onCheckedChange={setOverrideEnabled}
                        data-testid="pricing-override-checkbox"
                      />
                      <Label htmlFor="override" className="cursor-pointer font-medium">Override Price</Label>
                    </div>
                    {overrideEnabled && (
                      <div className="flex items-center gap-3">
                        <DollarSign className="h-5 w-5 text-slate-400" />
                        <Input 
                          type="number"
                          step="0.01"
                          value={overridePrice}
                          onChange={(e) => setOverridePrice(e.target.value)}
                          placeholder={(calculation.selling_price || calculation.suggested_price).toFixed(2)}
                          className="text-lg font-bold"
                          data-testid="pricing-override-input"
                        />
                      </div>
                    )}
                  </div>

                  {/* Notes */}
                  <div>
                    <Label>Notes (optional)</Label>
                    <Textarea 
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Any special instructions or notes..."
                      className="mt-1"
                      rows={2}
                    />
                  </div>

                  {/* Final Price & Add Button */}
                  <div className="flex items-center justify-between p-4 bg-teal-500 rounded-lg">
                    <div className="text-white">
                      <p className="text-sm opacity-80">Final Price</p>
                      <p className="text-3xl font-bold">
                        {formatCurrency(
                          overrideEnabled && overridePrice 
                            ? parseFloat(overridePrice) 
                            : (calculation.selling_price || calculation.suggested_price)
                        )}
                      </p>
                    </div>
                    <Button 
                      size="lg"
                      onClick={handleAddItem}
                      className="bg-white text-teal-600 hover:bg-teal-50"
                      data-testid="pricing-add-item-button"
                    >
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Add Item
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Calculator className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Fill in the details above to calculate pricing</p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Templates Browser Dialog */}
      <Dialog open={showTemplates} onOpenChange={setShowTemplates}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-teal-500" />
              Saved Templates
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {templates.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No saved templates yet</p>
                <p className="text-sm mt-1">Save your first template after configuring a pricing calculation</p>
              </div>
            ) : (
              <>
                {templates.filter(t => t.is_favorite).length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs uppercase text-slate-500 mb-2 flex items-center gap-1">
                      <Star className="h-3 w-3" /> Favorites
                    </p>
                    {templates.filter(t => t.is_favorite).map(template => (
                      <div
                        key={template.id}
                        onClick={() => handleLoadTemplate(template)}
                        className="p-3 border border-teal-200 rounded-lg cursor-pointer hover:bg-teal-50 transition-colors mb-2 flex items-center justify-between"
                      >
                        <div>
                          <p className="font-medium text-slate-800">{template.name}</p>
                          <p className="text-xs text-slate-500">
                            {PRICING_CATEGORIES.find(c => c.id === template.category)?.name} • Qty: {template.quantity}
                          </p>
                          {template.description && (
                            <p className="text-xs text-slate-400 mt-1">{template.description}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={(e) => handleToggleFavorite(template.id, e)}
                            className="p-1.5 hover:bg-amber-100 rounded"
                          >
                            <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                          </button>
                          <button
                            onClick={(e) => handleDeleteTemplate(template.id, e)}
                            className="p-1.5 hover:bg-red-100 rounded"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div>
                  {templates.filter(t => t.is_favorite).length > 0 && templates.filter(t => !t.is_favorite).length > 0 && (
                    <p className="text-xs uppercase text-slate-500 mb-2">All Templates</p>
                  )}
                  {templates.filter(t => !t.is_favorite).map(template => (
                    <div
                      key={template.id}
                      onClick={() => handleLoadTemplate(template)}
                      className="p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors mb-2 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-medium text-slate-800">{template.name}</p>
                        <p className="text-xs text-slate-500">
                          {PRICING_CATEGORIES.find(c => c.id === template.category)?.name} • Qty: {template.quantity}
                        </p>
                        {template.description && (
                          <p className="text-xs text-slate-400 mt-1">{template.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => handleToggleFavorite(template.id, e)}
                          className="p-1.5 hover:bg-slate-200 rounded"
                        >
                          <Star className="h-4 w-4 text-slate-400" />
                        </button>
                        <button
                          onClick={(e) => handleDeleteTemplate(template.id, e)}
                          className="p-1.5 hover:bg-red-100 rounded"
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Save Template Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Save className="h-5 w-5 text-teal-500" />
              Save as Template
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Template Name *</Label>
              <Input
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                placeholder="e.g., Standard Yard Sign 18x24"
                className="mt-1"
              />
            </div>
            <div>
              <Label>Description (optional)</Label>
              <Textarea
                value={templateDesc}
                onChange={(e) => setTemplateDesc(e.target.value)}
                placeholder="Notes about this template..."
                className="mt-1"
                rows={2}
              />
            </div>
            <div className="p-3 bg-slate-50 rounded-lg text-sm">
              <p className="text-slate-600">This will save:</p>
              <ul className="mt-1 text-slate-500 space-y-1">
                <li>• Category: <span className="font-medium text-slate-700">{getCategoryName(category)}</span></li>
                <li>• Quantity: <span className="font-medium text-slate-700">{quantity}</span></li>
                <li>• Complexity: <span className="font-medium text-slate-700">{complexity}</span></li>
                <li>• All current settings and field values</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveTemplate}
              disabled={savingTemplate || !templateName.trim()}
              className="bg-teal-500 hover:bg-teal-600"
            >
              {savingTemplate ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Save Template
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
