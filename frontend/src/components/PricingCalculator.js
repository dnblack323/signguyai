import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Switch } from '../components/ui/switch';
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
import StandardizedPricingBreakdown from './pricing/StandardizedPricingBreakdown';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Category definitions with icons
const PRICING_CATEGORIES = [
  { id: 'promotional', name: 'Promotional Items', icon: Tag, description: 'Magnets, yard signs, stickers, branded items' },
  { id: 'cut_vinyl', name: 'Cut Vinyl', icon: Scissors, description: 'Decals, lettering, graphics' },
  { id: 'services', name: 'Services', icon: Wrench, description: 'Design, installation, removal, site survey' },
  { id: 'digital_print', name: 'Digital Print', icon: Printer, description: 'Posters, prints, mounted graphics' },
  { id: 'banners', name: 'Banners', icon: Printer, description: 'Indoor/outdoor, event, pole, fabric, step-and-repeat' },
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
  { id: 'oracal_651', name: 'Oracal 651' },
  { id: 'oracal_751', name: 'Oracal 751' },
  { id: 'oracal_951', name: 'Oracal 951' },
  { id: 'avery_hp750', name: 'Avery HP750' },
  { id: 'reflective_vinyl', name: 'Reflective Vinyl' },
  { id: 'metallic_vinyl', name: 'Metallic Vinyl' },
  { id: 'fluorescent_vinyl', name: 'Fluorescent Vinyl' },
  { id: 'etched_frost_vinyl', name: 'Etched / Frost Vinyl' },
  { id: 'wall_vinyl', name: 'Wall Vinyl' },
  { id: 'specialty_custom_vinyl', name: 'Specialty / Custom Vinyl' },
];

// Print materials
const PRINT_MATERIALS = [
  { id: 'banner_13oz', name: '13 oz Banner' },
  { id: 'banner_18oz', name: '18 oz Banner' },
  { id: 'vinyl_adhesive', name: 'Adhesive Vinyl' },
  { id: 'poster_paper', name: 'Poster Paper' },
  { id: 'canvas', name: 'Canvas' },
  { id: 'backlit', name: 'Backlit Film' },
  { id: 'perforated', name: 'Perforated Window Film' },
];

const BANNER_TEMPLATES = [
  {
    key: 'small_pole_banner',
    name: 'Small Pole Banner',
    width: 18,
    height: 36,
    unit: 'inches',
    material_key: '18oz_banner',
    default_addons: ['pole_pockets'],
  },
  {
    key: 'large_pole_banner',
    name: 'Large Pole Banner',
    width: 24,
    height: 48,
    unit: 'inches',
    material_key: '18oz_banner',
    default_addons: ['pole_pockets'],
  },
];

const BANNER_ADDON_DEFAULTS = [
  { key: 'hems', label: 'Hems', pricing_type: 'included', flat_fee: 0, unit_fee: 0, qty: 1, default_labor_minutes: 0, rate_source: 'production_rate' },
  { key: 'grommets', label: 'Grommets', pricing_type: 'each', flat_fee: 0, unit_fee: 1.00, qty: 4, default_labor_minutes: 0, rate_source: 'production_rate' },
  { key: 'brackets', label: 'Brackets', pricing_type: 'each', flat_fee: 0, unit_fee: 20.00, qty: 0, default_labor_minutes: 5, rate_source: 'production_rate' },
  { key: 'other_hardware', label: 'Other Hardware', pricing_type: 'flat_fee', flat_fee: 0, unit_fee: 0, qty: 1, default_labor_minutes: 0, rate_source: 'production_rate' },
  { key: 'pole_pockets', label: 'Pole Pockets', pricing_type: 'flat_fee', flat_fee: 15.00, unit_fee: 0, qty: 1, default_labor_minutes: 5, rate_source: 'production_rate' },
  { key: 'design', label: 'Design', pricing_type: 'flat_fee', flat_fee: 35.00, unit_fee: 0, qty: 1, default_labor_minutes: 30, rate_source: 'design_rate' },
  { key: 'setup_fee', label: 'Setup Fee', pricing_type: 'flat_fee', flat_fee: 15.00, unit_fee: 0, qty: 1, default_labor_minutes: 0, rate_source: 'production_rate' },
  { key: 'install', label: 'Install', pricing_type: 'flat_fee', flat_fee: 0, unit_fee: 0, qty: 1, default_labor_minutes: 0, rate_source: 'install_rate' },
];

const PRINT_QUALITY_MODES = [
  { value: 'draft', label: 'Draft' },
  { value: 'standard', label: 'Standard' },
  { value: 'high', label: 'High' },
  { value: 'photo', label: 'Photo' },
];

const CONTOUR_CUT_TYPES = [
  { value: 'none', label: 'None' },
  { value: 'simple', label: 'Simple Contour' },
  { value: 'complex', label: 'Complex Contour' },
  { value: 'kiss', label: 'Kiss Cut / Sheet Cut' },
];

const TRIM_FINISH_TYPES = [
  { value: 'standard', label: 'Standard Trim' },
  { value: 'premium', label: 'Premium Trim' },
];

const USE_TYPES = [
  { value: 'indoor', label: 'Indoor' },
  { value: 'outdoor', label: 'Outdoor' },
  { value: 'display', label: 'Display' },
  { value: 'floor', label: 'Floor' },
  { value: 'window', label: 'Window' },
  { value: 'wall', label: 'Wall' },
  { value: 'backlit', label: 'Backlit' },
];

const CUT_VINYL_USE_TYPES = [
  { value: 'indoor', label: 'Indoor' },
  { value: 'outdoor', label: 'Outdoor' },
  { value: 'wall', label: 'Wall' },
  { value: 'glass_window', label: 'Glass / Window' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'specialty', label: 'Specialty' },
];

const CUT_VINYL_WEEDING_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];

const CUT_VINYL_SURFACE_TYPES = [
  { value: 'flat_smooth', label: 'Flat Smooth' },
  { value: 'glass_window', label: 'Glass / Window' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'textured_rough', label: 'Textured / Rough' },
  { value: 'curved_awkward', label: 'Curved / Awkward' },
];

const CUT_VINYL_COLOR_OPTIONS = [
  { value: 1, label: '1 Color' },
  { value: 2, label: '2 Colors' },
  { value: 3, label: '3 Colors' },
  { value: 4, label: '4+ Colors' },
];

const DESIGN_COMPLEXITY_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];

const INSTALL_COMPLEXITY_LEVELS = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'difficult', label: 'Difficult' },
  { value: 'extreme', label: 'Extreme' },
];

const UNIT_OF_MEASURE_OPTIONS = [
  { value: 'inches', label: 'Inches' },
  { value: 'feet', label: 'Feet' },
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

// Vehicle types (labels match Foundation material keys)
const VEHICLE_TYPES = [
  { id: 'car_sedan', name: 'Sedan' },
  { id: 'car_suv', name: 'SUV' },
  { id: 'pickup', name: 'Pickup' },
  { id: 'van_mini', name: 'Mini Van' },
  { id: 'van_cargo', name: 'Cargo Van' },
  { id: 'van_sprinter', name: 'Sprinter Van' },
  { id: 'box_truck_12ft', name: '12 ft Box Truck' },
  { id: 'box_truck_16ft', name: '16 ft Box Truck' },
  { id: 'box_truck_24ft', name: '24 ft Box Truck' },
  { id: 'trailer', name: 'Trailer' },
  { id: 'semi', name: 'Semi Truck' },
  { id: 'other', name: 'Custom / Other' },
];

// Coverage types
const COVERAGE_TYPES = [
  { id: 'spot', name: 'Spot Graphics' },
  { id: 'partial', name: 'Partial Wrap' },
  { id: 'half', name: 'Half Wrap' },
  { id: 'full', name: 'Full Wrap' },
  { id: 'custom', name: 'Custom %' },
];

const WRAP_MATERIAL_DEFAULTS = [
  { id: 'wrap_standard_calendered', name: 'Standard Calendered Vinyl' },
  { id: 'wrap_premium_cast', name: 'Premium Cast Vinyl' },
  { id: 'wrap_cast_film', name: 'Wrap Cast Film' },
  { id: 'wrap_reflective', name: 'Reflective Vinyl' },
  { id: 'wrap_etched_frost', name: 'Etched / Frost Film' },
  { id: 'wrap_specialty_media', name: 'Specialty / Custom Vehicle Media' },
];

const WRAP_LAMINATE_DEFAULTS = [
  { id: 'wrap_laminate_gloss', name: 'Gloss Laminate' },
  { id: 'wrap_laminate_matte', name: 'Matte Laminate' },
  { id: 'wrap_laminate_satin', name: 'Satin Laminate' },
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
  const [digitalPrintSources, setDigitalPrintSources] = useState({});
  const [cutVinylSources, setCutVinylSources] = useState({});
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
  const [bannerBreakdownExpanded, setBannerBreakdownExpanded] = useState(false);
  const [description, setDescription] = useState('');
  const [orderItemName, setOrderItemName] = useState('');
  const [notes, setNotes] = useState('');

  // Manual override / final selling price for the line item. The standardized
  // breakdown component derives profit/margin from this; the save payload
  // builder below also reuses the same fallback chain in its own scope.
  const finalPrice = overrideEnabled && overridePrice
    ? parseFloat(overridePrice)
    : calculation?.selling_price || calculation?.suggested_price || 0;
  
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

  const getDigitalPrintCategoryDefaults = () => (
    foundationDefaults?.category_defaults?.digital_print || {}
  );

  const getDigitalPrintMediaOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const options = materials.filter((m) => m.category === 'print_media');
    if (options.length) return options;
    return PRINT_MATERIALS.map((item) => ({ key: item.id, name: item.name }));
  };

  const getDigitalPrintLaminateOptions = () => {
    const materials = foundationDefaults?.materials || [];
    return materials.filter((m) => m.category === 'laminate');
  };

  const getDigitalPrintSubstrateOptions = () => {
    const materials = foundationDefaults?.materials || [];
    return materials.filter((m) => m.category === 'substrate' || ['coroplast', 'aluminum_composite', 'foam_board', 'acrylic_sheet', 'rigid_sign_board'].includes(m.key));
  };

  const updateDigitalPrintField = (field, value) => {
    setPricingData((prev) => ({ ...prev, [field]: value }));
    setDigitalPrintSources((prev) => ({ ...prev, [field]: 'user' }));
  };

  const resolveDigitalPrintDefaults = () => {
    const catDefaults = getDigitalPrintCategoryDefaults();
    return {
      unit_of_measure: catDefaults.default_unit_of_measure || 'inches',
      use_type: catDefaults.default_use_type || 'indoor',
      print_media_key: catDefaults.default_print_media_key || 'printable_adhesive_vinyl',
      print_quality_mode: catDefaults.default_print_quality_mode || 'standard',
      ink_coverage_percent: catDefaults.default_ink_coverage_percent ?? 35,
      laminate: catDefaults.default_laminate_required ?? false,
      laminate_material_key: catDefaults.default_laminate_key || 'laminate_gloss',
      contour_cut_type: catDefaults.default_contour_cut_type || 'none',
      trim_finish_type: catDefaults.default_trim_finish_type || 'standard',
      design_complexity: catDefaults.default_design_complexity || 'simple',
      install_required: catDefaults.default_install_included ?? false,
      install_complexity: catDefaults.default_install_complexity || 'easy',
    };
  };

  const resolveDigitalPrintAiSuggestions = (baseDefaults) => {
    if (!foundationDefaults?.ai_estimation_rules?.fill_missing_only) return {};
    const text = `${orderItemName || ''} ${description || ''}`.toLowerCase();
    const useType = pricingData.use_type || baseDefaults.use_type || 'indoor';
    const suggestions = {};

    if (!pricingData.print_media_key) {
      if (useType === 'floor' || text.includes('floor')) suggestions.print_media_key = 'floor_graphic_media';
      else if (useType === 'window' || text.includes('window') || text.includes('perf')) suggestions.print_media_key = 'perforated_window_film';
      else if (useType === 'backlit' || text.includes('backlit')) suggestions.print_media_key = 'backlit_film';
      else if (useType === 'wall' || text.includes('wall')) suggestions.print_media_key = 'wall_graphic_media';
      else if (useType === 'display' || text.includes('poster')) suggestions.print_media_key = 'poster_paper';
      else if (text.includes('canvas')) suggestions.print_media_key = 'canvas';
      else suggestions.print_media_key = baseDefaults.print_media_key;
    }

    if (pricingData.laminate === undefined) {
      suggestions.laminate = ['floor', 'outdoor'].includes(useType) || text.includes('laminate');
    }

    if (!pricingData.laminate_material_key && (suggestions.laminate || pricingData.laminate)) {
      if (useType === 'floor') suggestions.laminate_material_key = 'laminate_floor';
      else if (useType === 'outdoor') suggestions.laminate_material_key = 'laminate_heavy_duty';
      else suggestions.laminate_material_key = baseDefaults.laminate_material_key;
    }

    if (!pricingData.print_quality_mode) {
      if (text.includes('photo')) suggestions.print_quality_mode = 'photo';
      else if (text.includes('high')) suggestions.print_quality_mode = 'high';
      else if (text.includes('draft')) suggestions.print_quality_mode = 'draft';
      else suggestions.print_quality_mode = baseDefaults.print_quality_mode;
    }

    if (pricingData.ink_coverage_percent === undefined) {
      suggestions.ink_coverage_percent = baseDefaults.ink_coverage_percent;
    }

    if (!pricingData.contour_cut_type) {
      if (text.includes('kiss cut')) suggestions.contour_cut_type = 'kiss';
      else if (text.includes('complex contour')) suggestions.contour_cut_type = 'complex';
      else if (text.includes('contour')) suggestions.contour_cut_type = 'simple';
    }

    if (!pricingData.trim_finish_type) {
      if (text.includes('premium trim')) suggestions.trim_finish_type = 'premium';
      else suggestions.trim_finish_type = baseDefaults.trim_finish_type;
    }

    if (pricingData.mounted_to_substrate === undefined && (text.includes('mounted') || text.includes('mount')))
      suggestions.mounted_to_substrate = true;

    if (pricingData.install_required === undefined && text.includes('install'))
      suggestions.install_required = true;

    if (!pricingData.install_complexity) suggestions.install_complexity = baseDefaults.install_complexity;
    if (!pricingData.design_complexity) suggestions.design_complexity = baseDefaults.design_complexity;

    if (pricingData.artwork_needed === undefined) {
      if (text.includes('artwork needed') || text.includes('design needed')) suggestions.artwork_needed = true;
    }

    return suggestions;
  };

  useEffect(() => {
    if (category !== 'digital_print' || !foundationDefaults) return;
    const defaults = resolveDigitalPrintDefaults();
    const aiSuggestions = resolveDigitalPrintAiSuggestions(defaults);
    const nextData = { ...pricingData };
    const nextSources = { ...digitalPrintSources };
    let changed = false;

    const applyValues = (values, source) => {
      Object.entries(values).forEach(([key, value]) => {
        if (nextData[key] === undefined || nextData[key] === null || nextData[key] === '') {
          nextData[key] = value;
          if (!nextSources[key]) nextSources[key] = source;
          changed = true;
        }
      });
    };

    applyValues(aiSuggestions, 'ai');
    applyValues(defaults, 'default');

    if (changed) {
      setPricingData(nextData);
      setDigitalPrintSources(nextSources);
    }
  }, [category, foundationDefaults, orderItemName, description, pricingData.use_type]);

  const getCutVinylCategoryDefaults = () => (
    foundationDefaults?.category_defaults?.cut_vinyl || {}
  );

  const getCutVinylOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const options = materials.filter((m) => m.category === 'cut_vinyl');
    if (options.length) return options;
    return VINYL_TYPES.map((item) => ({ key: item.id, name: item.name }));
  };

  const updateCutVinylField = (field, value) => {
    setPricingData((prev) => ({ ...prev, [field]: value }));
    setCutVinylSources((prev) => ({ ...prev, [field]: 'user' }));
  };

  const resolveCutVinylDefaults = () => {
    const catDefaults = getCutVinylCategoryDefaults();
    return {
      unit_of_measure: catDefaults.default_unit_of_measure || 'inches',
      use_type: catDefaults.default_use_type || 'indoor',
      vinyl_type_key: catDefaults.default_vinyl_type_key || 'oracal_651',
      num_colors: catDefaults.default_number_of_colors ?? 1,
      weeding_complexity: catDefaults.default_weeding_complexity || 'simple',
      masking_required: catDefaults.default_masking_required ?? true,
      install_required: catDefaults.default_install_included ?? false,
      install_complexity: catDefaults.default_install_complexity || 'easy',
      surface_type: catDefaults.default_surface_type || 'flat_smooth',
      design_complexity: catDefaults.default_design_complexity || 'simple',
    };
  };

  const resolveCutVinylAiSuggestions = (baseDefaults) => {
    if (!foundationDefaults?.ai_estimation_rules?.fill_missing_only) return {};
    const text = `${orderItemName || ''} ${description || ''}`.toLowerCase();
    const useType = pricingData.use_type || baseDefaults.use_type || 'indoor';
    const suggestions = {};

    if (!pricingData.use_type) suggestions.use_type = baseDefaults.use_type;

    if (!pricingData.vinyl_type_key) {
      if (text.includes('reflective')) suggestions.vinyl_type_key = 'reflective_vinyl';
      else if (text.includes('metallic')) suggestions.vinyl_type_key = 'metallic_vinyl';
      else if (text.includes('fluorescent')) suggestions.vinyl_type_key = 'fluorescent_vinyl';
      else if (useType === 'glass_window' || text.includes('window') || text.includes('glass')) suggestions.vinyl_type_key = 'etched_frost_vinyl';
      else if (useType === 'wall' || text.includes('wall')) suggestions.vinyl_type_key = 'wall_vinyl';
      else if (useType === 'vehicle' || text.includes('vehicle')) suggestions.vinyl_type_key = 'oracal_951';
      else if (useType === 'outdoor') suggestions.vinyl_type_key = 'oracal_751';
      else suggestions.vinyl_type_key = baseDefaults.vinyl_type_key;
    }

    if (pricingData.masking_required === undefined) suggestions.masking_required = baseDefaults.masking_required;

    if (!pricingData.weeding_complexity) {
      if (text.includes('intricate') || text.includes('detailed')) suggestions.weeding_complexity = 'complex';
      else suggestions.weeding_complexity = baseDefaults.weeding_complexity;
    }

    if (!pricingData.num_colors) {
      if (text.includes('two color')) suggestions.num_colors = 2;
      else if (text.includes('three color')) suggestions.num_colors = 3;
      else suggestions.num_colors = baseDefaults.num_colors;
    }

    if (pricingData.install_required === undefined && text.includes('install')) suggestions.install_required = true;
    if (!pricingData.install_complexity) suggestions.install_complexity = baseDefaults.install_complexity;

    if (!pricingData.surface_type) {
      if (useType === 'glass_window') suggestions.surface_type = 'glass_window';
      else if (useType === 'vehicle') suggestions.surface_type = 'vehicle';
      else if (useType === 'wall') suggestions.surface_type = 'flat_smooth';
      else suggestions.surface_type = baseDefaults.surface_type;
    }

    if (!pricingData.design_complexity) suggestions.design_complexity = baseDefaults.design_complexity;

    if (pricingData.artwork_needed === undefined && (text.includes('design') || text.includes('artwork needed')))
      suggestions.artwork_needed = true;

    return suggestions;
  };

  useEffect(() => {
    if (category !== 'cut_vinyl' || !foundationDefaults) return;
    const defaults = resolveCutVinylDefaults();
    const aiSuggestions = resolveCutVinylAiSuggestions(defaults);
    const nextData = { ...pricingData };
    const nextSources = { ...cutVinylSources };
    let changed = false;

    const applyValues = (values, source) => {
      Object.entries(values).forEach(([key, value]) => {
        if (nextData[key] === undefined || nextData[key] === null || nextData[key] === '') {
          nextData[key] = value;
          if (!nextSources[key]) nextSources[key] = source;
          changed = true;
        }
      });
    };

    applyValues(aiSuggestions, 'ai');
    applyValues(defaults, 'default');

    if (changed) {
      setPricingData(nextData);
      setCutVinylSources(nextSources);
    }
  }, [category, foundationDefaults, orderItemName, description, pricingData.use_type]);

  const getRigidSignCategoryDefaults = () => (
    foundationDefaults?.category_defaults?.rigid_signs || {}
  );

  const getRigidSignSubstrateOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const options = materials.filter((m) => m.category === 'substrate');
    if (options.length) return options;
    return SUBSTRATE_TYPES.map((item) => ({ key: item.id, name: item.name }));
  };

  const getRigidSignFinishOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const options = materials.filter((m) => m.category === 'rigid_finish' || m.category === 'finish');
    if (options.length) return options;
    return [{ key: 'rigid_finish_standard', name: 'Standard Protective Finish' }];
  };

  const getRigidSignHardwareOptions = () => {
    const hardware = foundationDefaults?.hardware_accessories || [];
    const options = hardware.filter((item) => {
      if (item.is_active === false) return false;
      if (!item.compatible_categories || item.compatible_categories.length === 0) return true;
      return item.compatible_categories.includes('rigid_signs');
    });
    return options;
  };

  const updateRigidSignField = (field, value) => {
    setPricingData((prev) => ({ ...prev, [field]: value }));
  };

  const resolveRigidSignDefaults = () => {
    const catDefaults = getRigidSignCategoryDefaults();
    return {
      unit_of_measure: catDefaults.default_unit_of_measure || 'inches',
      substrate_type_key: catDefaults.default_substrate_key || '',
      graphic_method: catDefaults.default_graphic_method || 'direct_print',
      protective_finish: catDefaults.default_finish_required ?? false,
      protective_finish_type: catDefaults.default_finish_key || '',
      sidedness: catDefaults.default_sidedness || 'single',
      double_sided_art: catDefaults.default_double_sided_art || 'same',
      shape_type: catDefaults.default_shape_type || 'rectangle',
      finish_quality: catDefaults.default_finish_quality || 'standard',
      install_required: catDefaults.default_install_included ?? false,
      install_complexity: catDefaults.default_install_complexity || 'easy',
      design_complexity: catDefaults.default_design_complexity || 'simple',
    };
  };

  useEffect(() => {
    if (category !== 'rigid_signs' || !foundationDefaults) return;
    const defaults = resolveRigidSignDefaults();
    const nextData = { ...pricingData };
    let changed = false;

    Object.entries(defaults).forEach(([key, value]) => {
      if (nextData[key] === undefined || nextData[key] === null || nextData[key] === '') {
        nextData[key] = value;
        changed = true;
      }
    });

    if (changed) setPricingData(nextData);
  }, [category, foundationDefaults]);

  /* ───────── BANNERS helpers ───────── */
  const getBannersCategoryDefaults = () => (
    foundationDefaults?.category_defaults?.banners || {}
  );

  const getBannerMaterialOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const cat = getBannersCategoryDefaults();
    const availableKeys = cat.available_banner_material_keys || [];
    const filtered = materials.filter((m) =>
      m.category === 'banner_material'
      && m.is_active !== false
      && (availableKeys.length === 0 || availableKeys.includes(m.key || m.id))
    );
    if (filtered.length) return filtered;
    return [
      { key: '13oz_banner', name: '13 oz Banner' },
      { key: '18oz_banner', name: '18 oz Banner' },
      { key: 'mesh_banner', name: 'Standard Mesh Banner' },
      { key: 'fabric_banner', name: 'Standard Fabric Banner' },
    ];
  };

  const getBannerCoatingOptions = () => {
    const materials = foundationDefaults?.materials || [];
    const options = materials.filter((m) =>
      (m.category === 'banner_coating' || m.category === 'laminate')
      && m.is_active !== false
    );
    if (options.length) return options;
    return [{ key: 'banner_laminate_coating', name: 'Optional Laminate / Coating' }];
  };

  const getBannerHardwareOptions = () => {
    const hardware = foundationDefaults?.hardware_accessories || [];
    return hardware.filter((item) => {
      if (item.is_active === false) return false;
      return (item.compatible_categories || []).includes('banners');
    });
  };

  const updateBannerField = (field, value) => {
    setPricingData((prev) => ({ ...prev, [field]: value }));
  };

  const applyBannerTemplate = (templateKey) => {
    const template = BANNER_TEMPLATES.find((t) => t.key === templateKey);
    if (!template) return;
    const materialOptions = getBannerMaterialOptions();
    const matched = materialOptions.find(
      (m) => (m.key || m.id) === template.material_key || m.name?.toLowerCase().includes('18 oz')
    );
    const existingAddons = pricingData.banner_addons || [];
    const newAddons = [...existingAddons];
    template.default_addons.forEach((addonKey) => {
      if (!newAddons.some((a) => a.key === addonKey)) {
        const def = BANNER_ADDON_DEFAULTS.find((d) => d.key === addonKey);
        if (def) newAddons.push({ ...def, active: true });
      }
    });
    setPricingData((prev) => ({
      ...prev,
      width_inches: template.width,
      length_inches: template.height,
      unit_of_measure: template.unit,
      banner_material_key: matched ? (matched.key || matched.id) : template.material_key,
      product_type: template.name,
      banner_addons: newAddons,
    }));
    toast.success(`${template.name} template applied`);
  };

  // ===== BANNER COMPARE METHODS =====
  const computeBannerCompareMethods = () => {
    if (!foundationDefaults) return null;
    const catDefaults = getBannersCategoryDefaults();

    // Area
    const unit = (pricingData.unit_of_measure || 'feet').toLowerCase();
    const w = Number(pricingData.width_inches || 0);
    const h = Number(pricingData.length_inches || 0);
    const sqftPerPiece = unit === 'feet' ? w * h : (w * h) / 144;
    const qty = Number(quantity || 1);
    const totalSqft = sqftPerPiece * qty;
    if (sqftPerPiece <= 0) return null;

    // Material
    const matOptions = getBannerMaterialOptions();
    const matKey = pricingData.banner_material_key || '';
    const mat = matOptions.find((m) => (m.key || m.id) === matKey);

    // Shop cost & waste
    const costPerSqft = Number(mat?.cost_per_sqft || mat?.shop_cost_per_sqft || 0);
    const wastePercent = Number(mat?.waste_percent || catDefaults.waste_percentage || 8);
    const wasteAdjCostPerSqft = costPerSqft * (1 + wastePercent / 100);

    // Retail rate — priority chain
    const materialRetailRates = catDefaults.material_retail_rates || [];
    const matRetailEntry = materialRetailRates.find((r) =>
      r.material_id === matKey
      || (r.material_name && mat?.name && r.material_name.toLowerCase() === mat.name.toLowerCase())
    );
    const retailRatePerSqft = Number(
      matRetailEntry?.default_retail_rate_per_sqft
      || mat?.sell_rate_per_sqft
      || mat?.suggested_material_charge_per_sqft
      || catDefaults.default_retail_rate_per_sqft
      || 8.00
    );

    // Add-on fees and labor
    const addons = pricingData.banner_addons || [];
    const addonFees = addons.reduce((sum, a) => {
      if (a.pricing_type === 'flat_fee') return sum + Number(a.flat_fee || 0);
      if (a.pricing_type === 'each') return sum + Number(a.unit_fee || 0) * Number(a.qty || 1);
      return sum;
    }, 0);

    // Separate add-on labor by rate source
    let generalAddonLaborMin = 0;
    let designAddonLaborMin = 0;
    let installAddonLaborMin = 0;
    addons.forEach((addon) => {
      const def = BANNER_ADDON_DEFAULTS.find((d) => d.key === addon.key);
      const lm = Number(def?.default_labor_minutes || 0);
      if (def?.rate_source === 'design_rate') designAddonLaborMin += lm;
      else if (def?.rate_source === 'install_rate') installAddonLaborMin += lm;
      else generalAddonLaborMin += lm;
    });

    // Labor rates
    const laborRates = foundationDefaults.labor_rates || {};
    const prodRate = Number(laborRates.production?.hourly_rate || foundationDefaults.production_hourly_rate || foundationDefaults.hourly_rate || 75);
    const designRate = Number(laborRates.design?.hourly_rate || foundationDefaults.design_hourly_rate || 85);
    const installRate = Number(laborRates.installation?.hourly_rate || foundationDefaults.install_hourly_rate || 95);

    // Base labor minutes from wizard/category settings
    const setupMin = Number(catDefaults.setup_minutes || 10);
    const productionMin = Number(catDefaults.production_minutes || 15);
    const minPerSqft = Number(catDefaults.minutes_per_sqft || 0);
    const baseLaborMin = (setupMin + productionMin + minPerSqft * sqftPerPiece) * qty;
    const totalGeneralLaborMin = baseLaborMin + generalAddonLaborMin;

    // Labor costs
    const generalLaborCost = (totalGeneralLaborMin / 60) * prodRate;
    const designLaborCost = (designAddonLaborMin / 60) * designRate;
    const installLaborCost = (installAddonLaborMin / 60) * installRate;
    const totalLaborCost = generalLaborCost + designLaborCost + installLaborCost;
    const totalLaborMin = totalGeneralLaborMin + designAddonLaborMin + installAddonLaborMin;

    // Minimum charge
    const minimumCharge = Number(
      catDefaults.minimum_charge || catDefaults.default_minimum_sell_price || 35
    ) * qty;

    // Price Per Sq Ft method
    const retailBase = retailRatePerSqft * totalSqft;
    const ppsqftRaw = retailBase + addonFees;
    const pricePerSqftTotal = Math.max(ppsqftRaw, minimumCharge);
    const ppsqftMinApplied = ppsqftRaw < minimumCharge;

    // Detailed Material + Labor method
    const materialCost = wasteAdjCostPerSqft * totalSqft;
    const detailedRaw = materialCost + totalLaborCost + addonFees;
    const detailedTotal = Math.max(detailedRaw, minimumCharge);
    const detailedMinApplied = detailedRaw < minimumCharge;

    // Recommendation: higher of the two
    const recommendedPrice = Math.max(pricePerSqftTotal, detailedTotal);
    const recommendedMethod = pricePerSqftTotal >= detailedTotal ? 'price_per_sqft' : 'detailed';
    const diff = Math.abs(pricePerSqftTotal - detailedTotal);

    return {
      sqftPerPiece, totalSqft, qty,
      matName: mat?.name || matKey,
      costPerSqft, wastePercent, wasteAdjCostPerSqft,
      retailRatePerSqft, retailBase,
      addonFees,
      setupMin, productionMin, minPerSqft,
      baseLaborMin, totalGeneralLaborMin, designAddonLaborMin, installAddonLaborMin,
      totalLaborMin, prodRate, designRate, installRate,
      generalLaborCost, designLaborCost, installLaborCost, totalLaborCost,
      materialCost,
      minimumCharge,
      pricePerSqftTotal, ppsqftMinApplied,
      detailedTotal, detailedMinApplied,
      recommendedPrice, recommendedMethod, diff,
    };
  };

  const resolveBannerDefaults = () => {
    const catDefaults = getBannersCategoryDefaults();
    return {
      unit_of_measure: catDefaults.default_unit_of_measure || 'feet',
      banner_material_key: catDefaults.default_banner_material_key || 'banner_13oz',
      banner_use_type: catDefaults.default_use_type || 'outdoor',
      banner_hems: catDefaults.default_hems || 'standard',
      banner_grommets: catDefaults.default_grommets || 'corners',
      banner_pole_pockets: catDefaults.default_pole_pockets || 'none',
      banner_double_sided: catDefaults.default_double_sided || 'no',
      banner_reinforced_corners: catDefaults.default_reinforced_corners ?? false,
      banner_wind_slits: catDefaults.default_wind_slits ?? false,
      banner_specialty_sewing: catDefaults.default_specialty_sewing ?? false,
      banner_event_premium: catDefaults.default_event_premium ?? false,
      banner_laminate: catDefaults.default_laminate_required ?? false,
      banner_laminate_type_key: catDefaults.default_laminate_key || 'banner_laminate_coating',
      install_required: catDefaults.default_install_included ?? false,
      install_complexity: catDefaults.default_install_complexity || 'easy',
      design_complexity: catDefaults.default_design_complexity || 'simple',
    };
  };

  useEffect(() => {
    if (category !== 'banners' || !foundationDefaults) return;
    const defaults = resolveBannerDefaults();
    const nextData = { ...pricingData };
    let changed = false;
    Object.entries(defaults).forEach(([key, value]) => {
      if (nextData[key] === undefined || nextData[key] === null || nextData[key] === '') {
        nextData[key] = value;
        changed = true;
      }
    });
    if (changed) setPricingData(nextData);
  }, [category, foundationDefaults]);

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

    let finalPrice = overrideEnabled && overridePrice 
      ? parseFloat(overridePrice) 
      : calculation?.selling_price || calculation?.suggested_price || 0;

    // Banner add-ons: safely add to total when not using manual override
    let bannerAddonTotal = 0;
    if (category === 'banners' && !overrideEnabled) {
      bannerAddonTotal = (pricingData.banner_addons || []).reduce((sum, a) => {
        if (a.pricing_type === 'flat_fee') return sum + Number(a.flat_fee || 0);
        if (a.pricing_type === 'each') return sum + Number(a.unit_fee || 0) * Number(a.qty || 1);
        return sum;
      }, 0);
      finalPrice += bannerAddonTotal;
    }

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
      order_item_name: orderItemName,
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

  const renderDigitalPrintSource = (field) => {
    const source = digitalPrintSources[field] || 'default';
    const label = source === 'ai' ? 'AI Estimated' : source === 'user' ? 'User Entered' : 'Shop Default';
    return (
      <Badge variant="outline" className="text-[10px]" data-testid={`digital-print-source-${field}`}>
        {label}
      </Badge>
    );
  };

  const renderCutVinylSource = (field) => {
    const source = cutVinylSources[field] || 'default';
    const label = source === 'ai' ? 'AI Estimated' : source === 'user' ? 'User Entered' : 'Shop Default';
    return (
      <Badge variant="outline" className="text-[10px]" data-testid={`cut-vinyl-source-${field}`}>
        {label}
      </Badge>
    );
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

      case 'cut_vinyl': {
        const vinylOptions = getCutVinylOptions();
        const unit = pricingData.unit_of_measure || 'inches';
        const widthValue = Number(pricingData.width_inches || 0);
        const heightValue = Number(pricingData.length_inches || 0);
        const areaPerPiece = unit === 'feet' ? (widthValue * heightValue) : ((widthValue * heightValue) / 144);
        const selectedVinyl = vinylOptions.find((m) => (m.key || m.id) === pricingData.vinyl_type_key);
        return (
          <div className="space-y-4" data-testid="cut-vinyl-fields">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label className="flex items-center justify-between">Order Item Name {renderCutVinylSource('item_name')}</Label>
                <Input
                  value={orderItemName}
                  onChange={(e) => {
                    setOrderItemName(e.target.value);
                    setCutVinylSources((prev) => ({ ...prev, item_name: 'user' }));
                  }}
                  placeholder="e.g., Door Lettering"
                  data-testid="cut-vinyl-item-name"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label className="flex items-center justify-between">Width {renderCutVinylSource('width_inches')}</Label>
                <Input
                  type="number"
                  value={pricingData.width_inches || ''}
                  onChange={(e) => updateCutVinylField('width_inches', parseFloat(e.target.value) || 0)}
                  data-testid="cut-vinyl-width"
                />
              </div>
              <div>
                <Label className="flex items-center justify-between">Height {renderCutVinylSource('length_inches')}</Label>
                <Input
                  type="number"
                  value={pricingData.length_inches || ''}
                  onChange={(e) => updateCutVinylField('length_inches', parseFloat(e.target.value) || 0)}
                  data-testid="cut-vinyl-height"
                />
              </div>
              <div>
                <Label className="flex items-center justify-between">Unit {renderCutVinylSource('unit_of_measure')}</Label>
                <Select
                  value={pricingData.unit_of_measure || 'inches'}
                  onValueChange={(v) => updateCutVinylField('unit_of_measure', v)}
                >
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-unit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIT_OF_MEASURE_OPTIONS.map((u) => (
                      <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Area / Piece</Label>
                <Input value={areaPerPiece.toFixed(2)} disabled className="bg-slate-100" data-testid="cut-vinyl-area" />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <Label className="flex items-center justify-between">Vinyl Type {renderCutVinylSource('vinyl_type_key')}</Label>
                <Select value={pricingData.vinyl_type_key || ''} onValueChange={(v) => updateCutVinylField('vinyl_type_key', v)}>
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-type">
                    <SelectValue placeholder="Select vinyl" />
                  </SelectTrigger>
                  <SelectContent>
                    {vinylOptions.map((t) => (
                      <SelectItem key={t.key || t.id} value={t.key || t.id}>{t.name || t.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.vinyl_type_key && !selectedVinyl && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="cut-vinyl-type-warning">
                    Missing vinyl type.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="cut-vinyl-type-add-new">Add New</Link>
                  </p>
                )}
              </div>
              <div>
                <Label className="flex items-center justify-between">Number of Colors {renderCutVinylSource('num_colors')}</Label>
                <Select value={String(pricingData.num_colors || 1)} onValueChange={(v) => updateCutVinylField('num_colors', parseInt(v, 10))}>
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-colors">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CUT_VINYL_COLOR_OPTIONS.map((t) => (
                      <SelectItem key={t.value} value={String(t.value)}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="flex items-center justify-between">Weeding Complexity {renderCutVinylSource('weeding_complexity')}</Label>
                <Select value={pricingData.weeding_complexity || 'simple'} onValueChange={(v) => updateCutVinylField('weeding_complexity', v)}>
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-weeding">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CUT_VINYL_WEEDING_LEVELS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.masking_required ?? false}
                  onCheckedChange={(c) => updateCutVinylField('masking_required', Boolean(c))}
                  data-testid="cut-vinyl-masking"
                />
                <Label className="cursor-pointer">Masking Required</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Application / Use Type {renderCutVinylSource('use_type')}</Label>
                <Select value={pricingData.use_type || 'indoor'} onValueChange={(v) => updateCutVinylField('use_type', v)}>
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-use-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CUT_VINYL_USE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_ready || false}
                  onCheckedChange={(c) => updateCutVinylField('artwork_ready', Boolean(c))}
                  data-testid="cut-vinyl-artwork-ready"
                />
                <Label className="cursor-pointer">Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_needed || false}
                  onCheckedChange={(c) => updateCutVinylField('artwork_needed', Boolean(c))}
                  data-testid="cut-vinyl-artwork-needed"
                />
                <Label className="cursor-pointer">Artwork Needed</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Design Complexity {renderCutVinylSource('design_complexity')}</Label>
                <Select value={pricingData.design_complexity || 'simple'} onValueChange={(v) => updateCutVinylField('design_complexity', v)}>
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-design-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DESIGN_COMPLEXITY_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>{level.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.file_cleanup_needed || false}
                  onCheckedChange={(c) => updateCutVinylField('file_cleanup_needed', Boolean(c))}
                  data-testid="cut-vinyl-file-cleanup"
                />
                <Label className="cursor-pointer">File Cleanup Needed</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.install_required || false}
                  onCheckedChange={(c) => updateCutVinylField('install_required', Boolean(c))}
                  data-testid="cut-vinyl-install-required"
                />
                <Label className="cursor-pointer">Install Required</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Install Complexity {renderCutVinylSource('install_complexity')}</Label>
                <Select
                  value={pricingData.install_complexity || 'easy'}
                  onValueChange={(v) => updateCutVinylField('install_complexity', v)}
                  disabled={!pricingData.install_required}
                >
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-install-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INSTALL_COMPLEXITY_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>{level.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="flex items-center justify-between">Surface Type {renderCutVinylSource('surface_type')}</Label>
                <Select
                  value={pricingData.surface_type || 'flat_smooth'}
                  onValueChange={(v) => updateCutVinylField('surface_type', v)}
                  disabled={!pricingData.install_required}
                >
                  <SelectTrigger className="h-9" data-testid="cut-vinyl-surface-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CUT_VINYL_SURFACE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.rush_order || false}
                  onCheckedChange={(c) => updateCutVinylField('rush_order', Boolean(c))}
                  data-testid="cut-vinyl-rush"
                />
                <Label className="cursor-pointer">Rush</Label>
              </div>
            </div>
          </div>
        );
      }

      case 'services': {
        const svcCat = (foundationDefaults?.category_defaults || {}).services || {};
        const serviceTypes = svcCat.available_service_types || [];
        const billingUnits = (svcCat.available_billing_units && svcCat.available_billing_units.length > 0)
          ? svcCat.available_billing_units
          : ['hour','flat','piece','sqft','linear_foot','mile','trip','day','custom']; // last-resort fallback — Foundation should provide these
        const laborRolesMap = svcCat.labor_roles || {};
        const equipmentLibrary = svcCat.equipment_library || [];
        const selectedSt = pricingData.service_type || svcCat.default_service_type || 'general_labor';
        const selectedStInfo = serviceTypes.find((s) => s.key === selectedSt) || {};
        const billingUnit = pricingData.services_billing_unit || selectedStInfo.default_billing_unit || 'hour';
        const laborRole = pricingData.services_labor_role || selectedStInfo.default_labor_role || svcCat.default_labor_role || 'production';
        const showFlat = billingUnit === 'flat';
        const showUnitRate = ['piece','sqft','linear_foot','mile','trip','day','custom'].includes(billingUnit);
        const buLabels = { hour: 'Hour', flat: 'Flat Fee', piece: 'Piece', sqft: 'Sq Ft', linear_foot: 'Linear Ft', mile: 'Mile', trip: 'Trip', day: 'Day', custom: 'Custom Unit' };
        const aiFieldSet = new Set(pricingData.ai_prefilled_fields || []);
        const srcBadge = (fieldName, userSetCheck) => {
          if (aiFieldSet.has(fieldName)) return <Badge variant="outline" className="ml-2 text-[9px] bg-violet-50 text-violet-700 border-violet-300">AI</Badge>;
          if (userSetCheck) return <Badge variant="outline" className="ml-2 text-[9px] bg-slate-100 text-slate-600 border-slate-300">Edited</Badge>;
          return <Badge variant="outline" className="ml-2 text-[9px] bg-emerald-50 text-emerald-700 border-emerald-300">Default</Badge>;
        };
        const runAiPrefill = async () => {
          const desc = (pricingData.ai_description || '').trim();
          if (desc.length < 3) { toast.error('Describe the service in a few words first'); return; }
          try {
            setPricingData((prev) => ({ ...prev, _ai_prefilling: true }));
            const existing = { ...pricingData };
            delete existing.ai_description;
            delete existing._ai_prefilling;
            delete existing.ai_prefilled_fields;
            const { data } = await (await import('axios')).default.post(
              `${API_URL}/api/ai/services-prefill`,
              { description: desc, existing_inputs: existing },
              { headers: { Authorization: `Bearer ${getAuthToken()}` } }
            );
            const filled = data?.prefilled || {};
            const aiKeys = data?.ai_prefilled_fields || [];
            const aiSignature = data?.ai_prefill_signature || null;
            // L-3: backend validators already drop unknown enum values, but
            // double-check service_type on the client in case the library was
            // updated in another tab between prefill and render.
            if (filled.service_type && !serviceTypes.some((s) => s.key === filled.service_type)) {
              toast.warning(`AI proposed unknown service type "${filled.service_type}" — ignoring.`);
              delete filled.service_type;
            }
            if (Object.keys(filled).length === 0) {
              toast.info('AI had nothing new to add — all fields were already set.');
            } else {
              toast.success(`AI prefilled ${Object.keys(filled).length} field(s)`);
            }
            setPricingData((prev) => ({
              ...prev,
              ...filled,
              ai_prefilled_fields: [...new Set([...(prev.ai_prefilled_fields || []), ...aiKeys])],
              ai_prefill_signature: aiSignature,
              _ai_prefilling: false,
            }));
          } catch (err) {
            setPricingData((prev) => ({ ...prev, _ai_prefilling: false }));
            toast.error(err?.response?.data?.detail || 'AI prefill failed');
          }
        };
        return (
          <div className="space-y-4">
            {/* AI Prefill panel */}
            <div className="rounded-lg border border-violet-200 bg-violet-50/60 p-3" data-testid="services-ai-prefill-panel">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-violet-600" />
                <p className="text-xs font-semibold text-violet-900">AI Prefill (Services) — optional, fills missing fields only</p>
              </div>
              <div className="flex gap-2">
                <Textarea
                  value={pricingData.ai_description || ''}
                  onChange={(e) => setPricingData({ ...pricingData, ai_description: e.target.value })}
                  placeholder="e.g. Install 4 aluminum signs at a new retail site, 15 miles away, needs a lift…"
                  rows={2}
                  className="text-sm flex-1"
                  data-testid="svc-ai-description"
                />
                <Button
                  type="button"
                  onClick={runAiPrefill}
                  disabled={pricingData._ai_prefilling}
                  className="bg-violet-600 hover:bg-violet-700 text-white self-stretch"
                  data-testid="svc-ai-prefill-btn"
                >
                  {pricingData._ai_prefilling ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Prefill'}
                </Button>
              </div>
              <p className="text-[10px] text-violet-700/80 mt-1">Badges next to each field: <span className="font-semibold">Default</span> = shop default, <span className="font-semibold">AI</span> = AI estimated, <span className="font-semibold">Edited</span> = user entered.</p>
            </div>

            {/* Service Type + Billing Unit */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="flex items-center">Service Type *{srcBadge('service_type', !!pricingData.service_type)}</Label>
                <Select value={selectedSt} onValueChange={(v) => {
                  const info = serviceTypes.find((s) => s.key === v) || {};
                  setPricingData({ ...pricingData, service_type: v, services_billing_unit: info.default_billing_unit || 'hour', services_labor_role: info.default_labor_role || 'production', services_travel_required: !!info.requires_travel, services_equipment_required: !!info.uses_equipment, services_subcontracted: !!info.typically_subcontracted });
                }}>
                  <SelectTrigger data-testid="svc-service-type"><SelectValue placeholder="Select service" /></SelectTrigger>
                  <SelectContent>
                    {serviceTypes.map((s) => (<SelectItem key={s.key} value={s.key}>{s.label}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Billing Unit *</Label>
                <Select value={billingUnit} onValueChange={(v) => setPricingData({ ...pricingData, services_billing_unit: v })}>
                  <SelectTrigger data-testid="svc-billing-unit"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {billingUnits.map((u) => (<SelectItem key={u} value={u}>{buLabels[u] || u}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Labor Role + Complexity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Labor Role</Label>
                <Select value={laborRole} onValueChange={(v) => setPricingData({ ...pricingData, services_labor_role: v })}>
                  <SelectTrigger data-testid="svc-labor-role"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(laborRolesMap).map(([k, v]) => (<SelectItem key={k} value={k}>{v.label || k}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Complexity</Label>
                <Select value={pricingData.services_complexity || 'medium'} onValueChange={(v) => setPricingData({ ...pricingData, services_complexity: v })}>
                  <SelectTrigger data-testid="svc-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy (1.0x)</SelectItem>
                    <SelectItem value="medium">Medium (1.25x)</SelectItem>
                    <SelectItem value="difficult">Difficult (1.5x)</SelectItem>
                    <SelectItem value="extreme">Extreme (2.0x)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Labor params */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Estimated Hours</Label>
                <Input type="number" step="0.25" value={pricingData.estimated_hours ?? ''} onChange={(e) => setPricingData({ ...pricingData, estimated_hours: parseFloat(e.target.value) || 0 })} data-testid="svc-estimated-hours" />
              </div>
              <div>
                <Label>Number of Workers</Label>
                <Input
                  type="number"
                  min="1"
                  value={pricingData.num_workers ?? 1}
                  onChange={(e) => setPricingData({ ...pricingData, num_workers: parseInt(e.target.value) || 1 })}
                  disabled={showFlat}
                  data-testid="svc-num-workers"
                />
                {showFlat && (
                  <p className="text-[10px] text-amber-700 mt-1">
                    Flat-fee pricing ignores worker count on the sell side. Use hourly billing if workers should scale the price.
                  </p>
                )}
              </div>
              {showFlat && (
                <div>
                  <Label>Flat Fee ($)</Label>
                  <Input type="number" step="0.01" value={pricingData.services_flat_fee ?? ''} onChange={(e) => setPricingData({ ...pricingData, services_flat_fee: parseFloat(e.target.value) || 0 })} data-testid="svc-flat-fee" />
                </div>
              )}
              {showUnitRate && (
                <div>
                  <Label>Unit Rate Override ($)</Label>
                  <Input type="number" step="0.01" value={pricingData.services_unit_rate_override ?? ''} onChange={(e) => setPricingData({ ...pricingData, services_unit_rate_override: parseFloat(e.target.value) || 0 })} data-testid="svc-unit-rate-override" />
                </div>
              )}
              <div>
                <Label>Hourly Rate Override ($)</Label>
                <Input type="number" step="0.01" value={pricingData.hourly_rate_override ?? ''} onChange={(e) => setPricingData({ ...pricingData, hourly_rate_override: parseFloat(e.target.value) || null })} placeholder="Leave blank for default" data-testid="svc-hourly-override" />
              </div>
            </div>

            {/* Minimums */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={pricingData.services_minimum_applies !== false} onCheckedChange={(v) => setPricingData({ ...pricingData, services_minimum_applies: v })} data-testid="svc-min-applies" />
                <Label>Apply Minimum Charge</Label>
              </div>
              <div>
                <Label>Minimum Charge Override ($)</Label>
                <Input type="number" step="0.01" value={pricingData.services_minimum_override ?? ''} onChange={(e) => setPricingData({ ...pricingData, services_minimum_override: parseFloat(e.target.value) || 0 })} placeholder="0 = use service default" data-testid="svc-min-override" />
              </div>
            </div>

            {/* Travel */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.services_travel_required} onCheckedChange={(v) => setPricingData({ ...pricingData, services_travel_required: v })} data-testid="svc-travel-required" />
                <Label>Travel Required</Label>
              </div>
              <div>
                <Label>Travel Miles</Label>
                <Input type="number" value={pricingData.services_travel_miles ?? ''} onChange={(e) => setPricingData({ ...pricingData, services_travel_miles: parseFloat(e.target.value) || 0 })} disabled={!pricingData.services_travel_required && billingUnit !== 'mile'} data-testid="svc-travel-miles" />
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch
                  checked={!!pricingData.services_trip_charge_applies && !['mile','trip'].includes(billingUnit)}
                  onCheckedChange={(v) => setPricingData({ ...pricingData, services_trip_charge_applies: v })}
                  disabled={['mile','trip'].includes(billingUnit)}
                  data-testid="svc-trip-applies"
                />
                <Label className={['mile','trip'].includes(billingUnit) ? 'text-slate-400' : ''}>
                  Trip Charge {['mile','trip'].includes(billingUnit) && '(included in unit rate)'}
                </Label>
              </div>
              <div>
                <Label>Trip Count</Label>
                <Input type="number" min="1" value={pricingData.services_trip_count ?? 1} onChange={(e) => setPricingData({ ...pricingData, services_trip_count: parseInt(e.target.value) || 1 })} disabled={['mile'].includes(billingUnit)} data-testid="svc-trip-count" />
              </div>
            </div>

            {/* Equipment */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.services_equipment_required} onCheckedChange={(v) => setPricingData({ ...pricingData, services_equipment_required: v })} data-testid="svc-equip-required" />
                <Label>Equipment Required</Label>
              </div>
              <div>
                <Label>Equipment Type</Label>
                <Select value={pricingData.services_equipment_type || ''} onValueChange={(v) => setPricingData({ ...pricingData, services_equipment_type: v })} disabled={!pricingData.services_equipment_required}>
                  <SelectTrigger data-testid="svc-equip-type"><SelectValue placeholder="Select equipment" /></SelectTrigger>
                  <SelectContent>
                    {equipmentLibrary.map((e) => (<SelectItem key={e.key} value={e.key}>{e.label}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Equipment Days</Label>
                <Input type="number" step="0.25" min="0" value={pricingData.services_equipment_days ?? 0} onChange={(e) => setPricingData({ ...pricingData, services_equipment_days: parseFloat(e.target.value) || 0 })} disabled={!pricingData.services_equipment_required} data-testid="svc-equip-days" />
              </div>
              <div>
                <Label>Partial-Day Hours <span className="text-[10px] text-slate-500 font-normal">(added on top of days)</span></Label>
                <Input
                  type="number"
                  step="0.25"
                  min="0"
                  value={pricingData.services_equipment_hours ?? 0}
                  onChange={(e) => setPricingData({ ...pricingData, services_equipment_hours: parseFloat(e.target.value) || 0 })}
                  readOnly={!pricingData.services_equipment_required}
                  className={!pricingData.services_equipment_required ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}
                  data-testid="svc-equip-hours"
                />
              </div>
            </div>

            {/* Subcontract */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.services_subcontracted} onCheckedChange={(v) => setPricingData({ ...pricingData, services_subcontracted: v })} data-testid="svc-subcontracted" />
                <Label>Subcontracted / Outsourced</Label>
              </div>
              <div>
                <Label>Subcontract Cost ($)</Label>
                <Input type="number" step="0.01" value={pricingData.services_subcontract_cost ?? 0} onChange={(e) => setPricingData({ ...pricingData, services_subcontract_cost: parseFloat(e.target.value) || 0 })} disabled={!pricingData.services_subcontracted} data-testid="svc-sub-cost" />
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={pricingData.services_subcontract_markup_applies !== false} onCheckedChange={(v) => setPricingData({ ...pricingData, services_subcontract_markup_applies: v })} disabled={!pricingData.services_subcontracted} data-testid="svc-sub-markup" />
                <Label>Apply Markup</Label>
              </div>
              <div>
                <Label>Permit / External Fee ($)</Label>
                <Input type="number" step="0.01" value={pricingData.services_permit_external_fee ?? 0} onChange={(e) => setPricingData({ ...pricingData, services_permit_external_fee: parseFloat(e.target.value) || 0 })} data-testid="svc-permit-fee" />
              </div>
            </div>

            {/* Rush + Manual Override */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.rush_order} onCheckedChange={(v) => setPricingData({ ...pricingData, rush_order: v })} data-testid="svc-rush" />
                <Label>Rush</Label>
              </div>
              <div>
                <Label>Manual Quote Override ($ total)</Label>
                <Input type="number" step="0.01" value={pricingData.services_manual_quote_override ?? 0} onChange={(e) => setPricingData({ ...pricingData, services_manual_quote_override: parseFloat(e.target.value) || 0 })} placeholder="0 = use suggested" data-testid="svc-manual-override" />
              </div>
            </div>
          </div>
        );
      }

      case 'digital_print': {
        const mediaOptions = getDigitalPrintMediaOptions();
        const laminateOptions = getDigitalPrintLaminateOptions();
        const substrateOptions = getDigitalPrintSubstrateOptions();
        const unit = pricingData.unit_of_measure || 'inches';
        const widthValue = Number(pricingData.width_inches || 0);
        const heightValue = Number(pricingData.length_inches || 0);
        const areaPerPiece = unit === 'feet' ? (widthValue * heightValue) : ((widthValue * heightValue) / 144);
        const selectedMedia = mediaOptions.find((m) => (m.key || m.id) === pricingData.print_media_key);
        const selectedLaminate = laminateOptions.find((m) => (m.key || m.id) === pricingData.laminate_material_key);
        const selectedSubstrate = substrateOptions.find((m) => (m.key || m.id) === pricingData.substrate_material_key);
        return (
          <div className="space-y-4" data-testid="digital-print-fields">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label className="flex items-center justify-between">Order Item Name {renderDigitalPrintSource('item_name')}</Label>
                <Input
                  value={orderItemName}
                  onChange={(e) => {
                    setOrderItemName(e.target.value);
                    setDigitalPrintSources((prev) => ({ ...prev, item_name: 'user' }));
                  }}
                  placeholder="e.g., Window Graphics"
                  data-testid="digital-print-item-name"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label className="flex items-center justify-between">Width {renderDigitalPrintSource('width_inches')}</Label>
                <Input
                  type="number"
                  value={pricingData.width_inches || ''}
                  onChange={(e) => updateDigitalPrintField('width_inches', parseFloat(e.target.value) || 0)}
                  data-testid="digital-print-width"
                />
              </div>
              <div>
                <Label className="flex items-center justify-between">Height {renderDigitalPrintSource('length_inches')}</Label>
                <Input
                  type="number"
                  value={pricingData.length_inches || ''}
                  onChange={(e) => updateDigitalPrintField('length_inches', parseFloat(e.target.value) || 0)}
                  data-testid="digital-print-height"
                />
              </div>
              <div>
                <Label className="flex items-center justify-between">Unit {renderDigitalPrintSource('unit_of_measure')}</Label>
                <Select
                  value={pricingData.unit_of_measure || 'inches'}
                  onValueChange={(v) => updateDigitalPrintField('unit_of_measure', v)}
                >
                  <SelectTrigger className="h-9" data-testid="digital-print-unit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIT_OF_MEASURE_OPTIONS.map((u) => (
                      <SelectItem key={u.value} value={u.value}>{u.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Area / Piece</Label>
                <Input value={areaPerPiece.toFixed(2)} disabled className="bg-slate-100" data-testid="digital-print-area" />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <Label className="flex items-center justify-between">Print Media Type {renderDigitalPrintSource('print_media_key')}</Label>
                <Select
                  value={pricingData.print_media_key || ''}
                  onValueChange={(v) => updateDigitalPrintField('print_media_key', v)}
                >
                  <SelectTrigger className="h-9" data-testid="digital-print-media">
                    <SelectValue placeholder="Select media" />
                  </SelectTrigger>
                  <SelectContent>
                    {mediaOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.print_media_key && !selectedMedia && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="digital-print-media-warning">
                    Missing media type. 
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="digital-print-media-add-new">Add New</Link>
                  </p>
                )}
              </div>
              <div>
                <Label className="flex items-center justify-between">Use Type / Finish Use {renderDigitalPrintSource('use_type')}</Label>
                <Select value={pricingData.use_type || 'indoor'} onValueChange={(v) => updateDigitalPrintField('use_type', v)}>
                  <SelectTrigger className="h-9" data-testid="digital-print-use-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {USE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="flex items-center justify-between">Print Quality Mode {renderDigitalPrintSource('print_quality_mode')}</Label>
                <Select value={pricingData.print_quality_mode || 'standard'} onValueChange={(v) => updateDigitalPrintField('print_quality_mode', v)}>
                  <SelectTrigger className="h-9" data-testid="digital-print-quality">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRINT_QUALITY_MODES.map((mode) => (
                      <SelectItem key={mode.value} value={mode.value}>{mode.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="flex items-center justify-between">Ink Coverage % {renderDigitalPrintSource('ink_coverage_percent')}</Label>
                <Input
                  type="number"
                  value={pricingData.ink_coverage_percent ?? ''}
                  onChange={(e) => updateDigitalPrintField('ink_coverage_percent', parseFloat(e.target.value) || 0)}
                  data-testid="digital-print-ink-coverage"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.laminate || false}
                  onCheckedChange={(c) => updateDigitalPrintField('laminate', Boolean(c))}
                  data-testid="digital-print-laminate-toggle"
                />
                <Label className="cursor-pointer">Laminate Required</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Laminate Type {renderDigitalPrintSource('laminate_material_key')}</Label>
                <Select
                  value={pricingData.laminate_material_key || ''}
                  onValueChange={(v) => updateDigitalPrintField('laminate_material_key', v)}
                  disabled={!pricingData.laminate}
                >
                  <SelectTrigger className="h-9" data-testid="digital-print-laminate-type">
                    <SelectValue placeholder="Select laminate" />
                  </SelectTrigger>
                  <SelectContent>
                    {laminateOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.laminate && pricingData.laminate_material_key && !selectedLaminate && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="digital-print-laminate-warning">
                    Missing laminate type.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="digital-print-laminate-add-new">Add New</Link>
                  </p>
                )}
              </div>
              <div>
                <Label className="flex items-center justify-between">Contour Cut Type {renderDigitalPrintSource('contour_cut_type')}</Label>
                <Select value={pricingData.contour_cut_type || 'none'} onValueChange={(v) => updateDigitalPrintField('contour_cut_type', v)}>
                  <SelectTrigger className="h-9" data-testid="digital-print-contour-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTOUR_CUT_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="flex items-center justify-between">Trim Finish Type {renderDigitalPrintSource('trim_finish_type')}</Label>
                <Select value={pricingData.trim_finish_type || 'standard'} onValueChange={(v) => updateDigitalPrintField('trim_finish_type', v)}>
                  <SelectTrigger className="h-9" data-testid="digital-print-trim-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRIM_FINISH_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.piece_separation_required || false}
                  onCheckedChange={(c) => updateDigitalPrintField('piece_separation_required', Boolean(c))}
                  data-testid="digital-print-piece-separation"
                />
                <Label className="cursor-pointer">Piece Separation Required</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Separated Piece Count {renderDigitalPrintSource('separated_piece_count')}</Label>
                <Input
                  type="number"
                  value={pricingData.separated_piece_count || ''}
                  onChange={(e) => updateDigitalPrintField('separated_piece_count', parseInt(e.target.value, 10) || 0)}
                  disabled={!pricingData.piece_separation_required}
                  data-testid="digital-print-piece-count"
                />
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_ready || false}
                  onCheckedChange={(c) => updateDigitalPrintField('artwork_ready', Boolean(c))}
                  data-testid="digital-print-artwork-ready"
                />
                <Label className="cursor-pointer">Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_needed || false}
                  onCheckedChange={(c) => updateDigitalPrintField('artwork_needed', Boolean(c))}
                  data-testid="digital-print-artwork-needed"
                />
                <Label className="cursor-pointer">Artwork Needed</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Design Complexity {renderDigitalPrintSource('design_complexity')}</Label>
                <Select value={pricingData.design_complexity || 'simple'} onValueChange={(v) => updateDigitalPrintField('design_complexity', v)}>
                  <SelectTrigger className="h-9" data-testid="digital-print-design-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DESIGN_COMPLEXITY_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>{level.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.file_cleanup_needed || false}
                  onCheckedChange={(c) => updateDigitalPrintField('file_cleanup_needed', Boolean(c))}
                  data-testid="digital-print-file-cleanup"
                />
                <Label className="cursor-pointer">File Cleanup Needed</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.mounted_to_substrate || false}
                  onCheckedChange={(c) => updateDigitalPrintField('mounted_to_substrate', Boolean(c))}
                  data-testid="digital-print-mounted"
                />
                <Label className="cursor-pointer">Mounted to Substrate</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Substrate Type {renderDigitalPrintSource('substrate_material_key')}</Label>
                <Select
                  value={pricingData.substrate_material_key || ''}
                  onValueChange={(v) => updateDigitalPrintField('substrate_material_key', v)}
                  disabled={!pricingData.mounted_to_substrate}
                >
                  <SelectTrigger className="h-9" data-testid="digital-print-substrate-type">
                    <SelectValue placeholder="Select substrate" />
                  </SelectTrigger>
                  <SelectContent>
                    {substrateOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.mounted_to_substrate && pricingData.substrate_material_key && !selectedSubstrate && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="digital-print-substrate-warning">
                    Missing substrate type.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="digital-print-substrate-add-new">Add New</Link>
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.install_required || false}
                  onCheckedChange={(c) => updateDigitalPrintField('install_required', Boolean(c))}
                  data-testid="digital-print-install-required"
                />
                <Label className="cursor-pointer">Install Required</Label>
              </div>
              <div>
                <Label className="flex items-center justify-between">Install Complexity {renderDigitalPrintSource('install_complexity')}</Label>
                <Select
                  value={pricingData.install_complexity || 'easy'}
                  onValueChange={(v) => updateDigitalPrintField('install_complexity', v)}
                  disabled={!pricingData.install_required}
                >
                  <SelectTrigger className="h-9" data-testid="digital-print-install-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INSTALL_COMPLEXITY_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>{level.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.rush_order || false}
                  onCheckedChange={(c) => updateDigitalPrintField('rush_order', Boolean(c))}
                  data-testid="digital-print-rush"
                />
                <Label className="cursor-pointer">Rush</Label>
              </div>
            </div>
          </div>
        );
      }

      case 'rigid_signs': {
        const substrateOptions = getRigidSignSubstrateOptions();
        const finishOptions = getRigidSignFinishOptions();
        const hardwareOptions = getRigidSignHardwareOptions();
        const selectedSubstrate = substrateOptions.find((m) => (m.key || m.id) === pricingData.substrate_type_key);
        const selectedFinish = finishOptions.find((m) => (m.key || m.id) === pricingData.protective_finish_type);
        const selectedHardware = hardwareOptions.find((m) => (m.id || m.key) === pricingData.hardware_type);
        const unit = pricingData.unit_of_measure || 'inches';
        const widthVal = Number(pricingData.width_inches || 0);
        const heightVal = Number(pricingData.length_inches || 0);
        const area = unit === 'feet' ? widthVal * heightVal : (widthVal * heightVal) / 144;

        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label>Width</Label>
                <Input
                  type="number"
                  value={pricingData.width_inches || ''}
                  onChange={(e) => updateRigidSignField('width_inches', parseFloat(e.target.value) || 0)}
                  data-testid="rigid-signs-width"
                />
              </div>
              <div>
                <Label>Height</Label>
                <Input
                  type="number"
                  value={pricingData.length_inches || ''}
                  onChange={(e) => updateRigidSignField('length_inches', parseFloat(e.target.value) || 0)}
                  data-testid="rigid-signs-height"
                />
              </div>
              <div>
                <Label>Unit</Label>
                <Select value={unit} onValueChange={(v) => updateRigidSignField('unit_of_measure', v)}>
                  <SelectTrigger className="h-9" data-testid="rigid-signs-unit">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIT_OF_MEASURE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Area (sqft)</Label>
                <Input
                  value={area.toFixed(2)}
                  disabled
                  className="bg-slate-100"
                  data-testid="rigid-signs-area"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label>Substrate</Label>
                <Select
                  value={pricingData.substrate_type_key || ''}
                  onValueChange={(v) => updateRigidSignField('substrate_type_key', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-substrate">
                    <SelectValue placeholder="Select substrate" />
                  </SelectTrigger>
                  <SelectContent>
                    {substrateOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.substrate_type_key && !selectedSubstrate && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="rigid-signs-substrate-warning">
                    Missing substrate in Pricing Foundation.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="rigid-signs-substrate-add">Add New</Link>
                  </p>
                )}
              </div>
              <div>
                <Label>Thickness</Label>
                <Select
                  value={pricingData.thickness || ''}
                  onValueChange={(v) => updateRigidSignField('thickness', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-thickness">
                    <SelectValue placeholder="Select thickness" />
                  </SelectTrigger>
                  <SelectContent>
                    {[
                      { value: '3mm', label: '3mm' },
                      { value: '4mm', label: '4mm' },
                      { value: '6mm', label: '6mm' },
                      { value: '10mm', label: '10mm' },
                      { value: '0.040', label: '0.040"' },
                      { value: '0.063', label: '0.063"' },
                      { value: '0.080', label: '0.080"' },
                      { value: '1/8', label: '1/8"' },
                      { value: '3/16', label: '3/16"' },
                      { value: '1/4', label: '1/4"' },
                      { value: '1/2', label: '1/2"' },
                      { value: 'custom', label: 'Custom' },
                    ].map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Graphic Method</Label>
                <Select
                  value={pricingData.graphic_method || 'direct_print'}
                  onValueChange={(v) => updateRigidSignField('graphic_method', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-graphic-method">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="direct_print">Direct Print</SelectItem>
                    <SelectItem value="mounted_print">Mounted Print</SelectItem>
                    <SelectItem value="cut_vinyl_applied">Cut Vinyl Applied</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Finish Quality</Label>
                <Select
                  value={pricingData.finish_quality || 'standard'}
                  onValueChange={(v) => updateRigidSignField('finish_quality', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-finish-quality">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                    <SelectItem value="presentation">Presentation</SelectItem>
                    <SelectItem value="architectural">Architectural</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.protective_finish || false}
                  onCheckedChange={(c) => updateRigidSignField('protective_finish', Boolean(c))}
                  data-testid="rigid-signs-protective-finish"
                />
                <Label className="cursor-pointer">Protective Finish</Label>
              </div>
              <div>
                <Label>Finish Type</Label>
                <Select
                  value={pricingData.protective_finish_type || ''}
                  onValueChange={(v) => updateRigidSignField('protective_finish_type', v)}
                  disabled={!pricingData.protective_finish}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-finish-type">
                    <SelectValue placeholder="Select finish" />
                  </SelectTrigger>
                  <SelectContent>
                    {finishOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name || m.key}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.protective_finish && pricingData.protective_finish_type && !selectedFinish && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="rigid-signs-finish-warning">
                    Missing finish in Pricing Foundation.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="rigid-signs-finish-add">Add New</Link>
                  </p>
                )}
              </div>
              <div>
                <Label>Sidedness</Label>
                <Select
                  value={pricingData.sidedness || 'single'}
                  onValueChange={(v) => updateRigidSignField('sidedness', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-sidedness">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single">Single</SelectItem>
                    <SelectItem value="double">Double</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Double-Sided Art</Label>
                <Select
                  value={pricingData.double_sided_art || 'same'}
                  onValueChange={(v) => updateRigidSignField('double_sided_art', v)}
                  disabled={pricingData.sidedness !== 'double'}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-double-art">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="same">Same Art</SelectItem>
                    <SelectItem value="different">Different Art</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label>Shape Type</Label>
                <Select
                  value={pricingData.shape_type || 'rectangle'}
                  onValueChange={(v) => updateRigidSignField('shape_type', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-shape">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="rectangle">Rectangle</SelectItem>
                    <SelectItem value="rounded_corners">Rounded Corners</SelectItem>
                    <SelectItem value="simple_contour">Simple Contour</SelectItem>
                    <SelectItem value="complex_contour">Complex Contour</SelectItem>
                    <SelectItem value="specialty_routed">Specialty Routed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.hardware_included || false}
                  onCheckedChange={(c) => updateRigidSignField('hardware_included', Boolean(c))}
                  data-testid="rigid-signs-hardware-included"
                />
                <Label className="cursor-pointer">Hardware Included</Label>
              </div>
              <div>
                <Label>Hardware Type</Label>
                <Select
                  value={pricingData.hardware_type || ''}
                  onValueChange={(v) => updateRigidSignField('hardware_type', v)}
                  disabled={!pricingData.hardware_included}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-hardware-type">
                    <SelectValue placeholder="Select hardware" />
                  </SelectTrigger>
                  <SelectContent>
                    {hardwareOptions.map((h) => (
                      <SelectItem key={h.id || h.key} value={h.id || h.key}>{h.name || h.id}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {pricingData.hardware_included && pricingData.hardware_type && !selectedHardware && (
                  <p className="text-xs text-amber-600 mt-1" data-testid="rigid-signs-hardware-warning">
                    Missing hardware in Pricing Foundation.
                    <Link to="/pricing-foundation" className="text-amber-700 underline ml-1" data-testid="rigid-signs-hardware-add">Add New</Link>
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.drill_prep_required || false}
                  onCheckedChange={(c) => updateRigidSignField('drill_prep_required', Boolean(c))}
                  data-testid="rigid-signs-drill-prep"
                />
                <Label className="cursor-pointer">Drill / Prep Required</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_ready || false}
                  onCheckedChange={(c) => updateRigidSignField('artwork_ready', Boolean(c))}
                  data-testid="rigid-signs-artwork-ready"
                />
                <Label className="cursor-pointer">Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.artwork_needed || false}
                  onCheckedChange={(c) => updateRigidSignField('artwork_needed', Boolean(c))}
                  data-testid="rigid-signs-artwork-needed"
                />
                <Label className="cursor-pointer">Design Needed</Label>
              </div>
              <div>
                <Label>Design Complexity</Label>
                <Select
                  value={pricingData.design_complexity || 'simple'}
                  onValueChange={(v) => updateRigidSignField('design_complexity', v)}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-design-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="simple">Simple</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="complex">Complex</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.rush_order || false}
                  onCheckedChange={(c) => updateRigidSignField('rush_order', Boolean(c))}
                  data-testid="rigid-signs-rush"
                />
                <Label className="cursor-pointer">Rush</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={pricingData.install_required || false}
                  onCheckedChange={(c) => updateRigidSignField('install_required', Boolean(c))}
                  data-testid="rigid-signs-install-required"
                />
                <Label className="cursor-pointer">Install Required</Label>
              </div>
              <div>
                <Label>Install Complexity</Label>
                <Select
                  value={pricingData.install_complexity || 'easy'}
                  onValueChange={(v) => updateRigidSignField('install_complexity', v)}
                  disabled={!pricingData.install_required}
                >
                  <SelectTrigger className="h-9" data-testid="rigid-signs-install-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="difficult">Difficult</SelectItem>
                    <SelectItem value="high_risk">High-Risk</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        );
      }

      case 'banners': {
        const materialOptions = getBannerMaterialOptions();
        const coatingOptions = getBannerCoatingOptions();
        const hardwareOptions = getBannerHardwareOptions();
        const selectedMaterial = materialOptions.find((m) => (m.key || m.id) === pricingData.banner_material_key);
        const selectedCoating = coatingOptions.find((m) => (m.key || m.id) === pricingData.banner_laminate_type_key);
        const unit = pricingData.unit_of_measure || 'feet';
        const widthVal = Number(pricingData.width_inches || 0);
        const heightVal = Number(pricingData.length_inches || 0);
        const areaPerPiece = unit === 'feet' ? widthVal * heightVal : (widthVal * heightVal) / 144;

        return (
          <div className="space-y-4" data-testid="banners-fields">
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label>Order Item Name</Label>
                <Input
                  value={orderItemName}
                  onChange={(e) => setOrderItemName(e.target.value)}
                  placeholder="e.g., Grand Opening Banner"
                  data-testid="banners-item-name"
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Describe the banner (indoor/outdoor, event context, etc.)"
                  data-testid="banners-description"
                />
              </div>
            </div>

            {/* Quick Templates */}
            <div>
              <Label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Quick Templates</Label>
              <div className="flex gap-2 flex-wrap mt-2">
                {BANNER_TEMPLATES.map((t) => (
                  <Button
                    key={t.key}
                    variant="outline"
                    size="sm"
                    type="button"
                    onClick={() => applyBannerTemplate(t.key)}
                    className="text-xs h-8"
                    data-testid={`banner-template-${t.key}`}
                  >
                    {t.name}
                  </Button>
                ))}
              </div>
            </div>

            {/* Product Type */}
            <div>
              <Label>Product Type</Label>
              <Input
                value={pricingData.product_type || ''}
                onChange={(e) => updateBannerField('product_type', e.target.value)}
                placeholder="e.g., Pole Banner, Step-and-Repeat, Event Banner"
                data-testid="banners-product-type"
              />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label>Width</Label>
                <Input
                  type="number"
                  value={pricingData.width_inches || ''}
                  onChange={(e) => updateBannerField('width_inches', parseFloat(e.target.value) || 0)}
                  data-testid="banners-width"
                />
              </div>
              <div>
                <Label>Height</Label>
                <Input
                  type="number"
                  value={pricingData.length_inches || ''}
                  onChange={(e) => updateBannerField('length_inches', parseFloat(e.target.value) || 0)}
                  data-testid="banners-height"
                />
              </div>
              <div>
                <Label>Unit of Measure</Label>
                <Select value={unit} onValueChange={(v) => updateBannerField('unit_of_measure', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-unit"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="feet">Feet</SelectItem>
                    <SelectItem value="inches">Inches</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Area / piece</Label>
                <div className="h-9 flex items-center text-sm text-gray-600" data-testid="banners-area-per-piece">
                  {areaPerPiece.toFixed(2)} sq ft
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div>
                <Label>Banner Material Type</Label>
                <Select
                  value={pricingData.banner_material_key || ''}
                  onValueChange={(v) => updateBannerField('banner_material_key', v)}
                >
                  <SelectTrigger className="h-9" data-testid="banners-material"><SelectValue placeholder="Select material" /></SelectTrigger>
                  <SelectContent>
                    {materialOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedMaterial && (
                  <div className="text-xs text-gray-500 mt-1">
                    Cost ${Number(selectedMaterial.cost_per_sqft || 0).toFixed(2)}/sqft · Sell ${Number(selectedMaterial.sell_rate_per_sqft || 0).toFixed(2)}/sqft
                  </div>
                )}
              </div>
              <div>
                <Label>Use Type</Label>
                <Select value={pricingData.banner_use_type || 'outdoor'} onValueChange={(v) => updateBannerField('banner_use_type', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-use-type"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="indoor">Indoor</SelectItem>
                    <SelectItem value="outdoor">Outdoor</SelectItem>
                    <SelectItem value="event_display">Event / Display</SelectItem>
                    <SelectItem value="fence">Fence</SelectItem>
                    <SelectItem value="pole_banner">Pole Banner</SelectItem>
                    <SelectItem value="backwall_step_repeat">Backwall / Step-and-Repeat</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Double-Sided?</Label>
                <Select value={pricingData.banner_double_sided || 'no'} onValueChange={(v) => updateBannerField('banner_double_sided', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-double-sided"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="no">No</SelectItem>
                    <SelectItem value="same">Same art both sides</SelectItem>
                    <SelectItem value="different">Different art both sides</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.banner_laminate}
                  onCheckedChange={(c) => updateBannerField('banner_laminate', Boolean(c))}
                  data-testid="banners-laminate-toggle"
                />
                <Label className="cursor-pointer">Laminate / Coating?</Label>
              </div>
              <div>
                <Label>Laminate / Coating Type</Label>
                <Select
                  value={pricingData.banner_laminate_type_key || ''}
                  onValueChange={(v) => updateBannerField('banner_laminate_type_key', v)}
                  disabled={!pricingData.banner_laminate}
                >
                  <SelectTrigger className="h-9" data-testid="banners-laminate-type"><SelectValue placeholder="Select coating" /></SelectTrigger>
                  <SelectContent>
                    {coatingOptions.map((m) => (
                      <SelectItem key={m.key || m.id} value={m.key || m.id}>{m.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedCoating && pricingData.banner_laminate && (
                  <div className="text-xs text-gray-500 mt-1">Cost ${Number(selectedCoating.cost_per_sqft || 0).toFixed(2)}/sqft</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <Label>Hems</Label>
                <Select value={pricingData.banner_hems || 'standard'} onValueChange={(v) => updateBannerField('banner_hems', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-hems"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="standard">Standard Hem</SelectItem>
                    <SelectItem value="reinforced">Reinforced Hem</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Grommets</Label>
                <Select value={pricingData.banner_grommets || 'corners'} onValueChange={(v) => updateBannerField('banner_grommets', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-grommets"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="corners">Corners Only</SelectItem>
                    <SelectItem value="every_2ft">Every 2 ft</SelectItem>
                    <SelectItem value="every_3ft">Every 3 ft</SelectItem>
                    <SelectItem value="custom">Custom Count</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Grommet Count (custom)</Label>
                <Input
                  type="number"
                  value={pricingData.banner_grommet_count || ''}
                  onChange={(e) => updateBannerField('banner_grommet_count', parseInt(e.target.value) || 0)}
                  disabled={pricingData.banner_grommets !== 'custom'}
                  data-testid="banners-grommet-count"
                />
              </div>
              <div>
                <Label>Pole Pockets</Label>
                <Select value={pricingData.banner_pole_pockets || 'none'} onValueChange={(v) => updateBannerField('banner_pole_pockets', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-pole-pockets"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="top">Top Only</SelectItem>
                    <SelectItem value="top_and_bottom">Top and Bottom</SelectItem>
                    <SelectItem value="side_pockets">Side Pockets</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.banner_reinforced_corners}
                  onCheckedChange={(c) => updateBannerField('banner_reinforced_corners', Boolean(c))}
                  data-testid="banners-reinforced-corners"
                />
                <Label className="cursor-pointer">Reinforced Corners</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.banner_wind_slits}
                  onCheckedChange={(c) => updateBannerField('banner_wind_slits', Boolean(c))}
                  data-testid="banners-wind-slits"
                />
                <Label className="cursor-pointer">Wind Slits</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.banner_specialty_sewing}
                  onCheckedChange={(c) => updateBannerField('banner_specialty_sewing', Boolean(c))}
                  data-testid="banners-specialty-sewing"
                />
                <Label className="cursor-pointer">Specialty Sewing</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.banner_event_premium}
                  onCheckedChange={(c) => updateBannerField('banner_event_premium', Boolean(c))}
                  data-testid="banners-event-premium"
                />
                <Label className="cursor-pointer">Event / Step-and-Repeat Premium</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.artwork_ready}
                  onCheckedChange={(c) => updateBannerField('artwork_ready', Boolean(c))}
                  data-testid="banners-artwork-ready"
                />
                <Label className="cursor-pointer">Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.artwork_needed}
                  onCheckedChange={(c) => updateBannerField('artwork_needed', Boolean(c))}
                  data-testid="banners-artwork-needed"
                />
                <Label className="cursor-pointer">Artwork Needed</Label>
              </div>
              <div>
                <Label>Design Complexity</Label>
                <Select value={pricingData.design_complexity || 'simple'} onValueChange={(v) => updateBannerField('design_complexity', v)}>
                  <SelectTrigger className="h-9" data-testid="banners-design-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="simple">Simple</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="complex">Complex</SelectItem>
                    <SelectItem value="extreme">Extreme</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.rush_order}
                  onCheckedChange={(c) => updateBannerField('rush_order', Boolean(c))}
                  data-testid="banners-rush"
                />
                <Label className="cursor-pointer">Rush</Label>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-2 pt-6">
                <Checkbox
                  checked={!!pricingData.install_required}
                  onCheckedChange={(c) => updateBannerField('install_required', Boolean(c))}
                  data-testid="banners-install-required"
                />
                <Label className="cursor-pointer">Install Required</Label>
              </div>
              <div>
                <Label>Install Complexity</Label>
                <Select
                  value={pricingData.install_complexity || 'easy'}
                  onValueChange={(v) => updateBannerField('install_complexity', v)}
                  disabled={!pricingData.install_required}
                >
                  <SelectTrigger className="h-9" data-testid="banners-install-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="difficult">Difficult</SelectItem>
                    <SelectItem value="high_access">High-Access</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {hardwareOptions.length > 0 && (
              <div>
                <Label>Hardware / Accessories</Label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2">
                  {hardwareOptions.map((hw) => {
                    const currentKeys = pricingData.banner_hardware_keys || [];
                    const checked = currentKeys.includes(hw.id || hw.key);
                    return (
                      <div key={hw.id || hw.key} className="flex items-center gap-2">
                        <Checkbox
                          checked={checked}
                          onCheckedChange={(c) => {
                            const next = c
                              ? [...currentKeys, hw.id || hw.key]
                              : currentKeys.filter((k) => k !== (hw.id || hw.key));
                            updateBannerField('banner_hardware_keys', next);
                          }}
                          data-testid={`banners-hw-${hw.id || hw.key}`}
                        />
                        <Label className="cursor-pointer text-sm">{hw.name}</Label>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Banner Add-ons */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="font-medium">Add-ons</Label>
                <Select
                  value=""
                  onValueChange={(key) => {
                    if (!key) return;
                    const existing = pricingData.banner_addons || [];
                    if (existing.some((a) => a.key === key)) return;
                    const def = BANNER_ADDON_DEFAULTS.find((d) => d.key === key);
                    if (def) updateBannerField('banner_addons', [...existing, { ...def, active: true }]);
                  }}
                >
                  <SelectTrigger className="h-8 w-44 text-xs" data-testid="banners-add-addon-select">
                    <SelectValue placeholder="+ Add add-on" />
                  </SelectTrigger>
                  <SelectContent>
                    {BANNER_ADDON_DEFAULTS.filter(
                      (d) => !(pricingData.banner_addons || []).some((a) => a.key === d.key)
                    ).map((d) => (
                      <SelectItem key={d.key} value={d.key}>{d.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {(pricingData.banner_addons || []).length > 0 && (
                <div className="space-y-2" data-testid="banners-addons-list">
                  {(pricingData.banner_addons || []).map((addon, idx) => {
                    const lineTotal = addon.pricing_type === 'each'
                      ? Number(addon.unit_fee || 0) * Number(addon.qty || 1)
                      : addon.pricing_type === 'flat_fee'
                      ? Number(addon.flat_fee || 0)
                      : 0;
                    return (
                      <div key={addon.key} className="grid grid-cols-12 gap-1 items-center p-2 bg-gray-50 rounded text-sm" data-testid={`banner-addon-row-${addon.key}`}>
                        <div className="col-span-3 text-sm font-medium truncate">{addon.label}</div>
                        {addon.pricing_type === 'flat_fee' && (
                          <>
                            <div className="col-span-3">
                              <Input
                                type="number"
                                value={addon.flat_fee}
                                onChange={(e) => {
                                  const updated = [...(pricingData.banner_addons || [])];
                                  updated[idx] = { ...updated[idx], flat_fee: Number(e.target.value) || 0 };
                                  updateBannerField('banner_addons', updated);
                                }}
                                className="h-7 text-xs"
                                data-testid={`banner-addon-flat-fee-${addon.key}`}
                              />
                            </div>
                            <div className="col-span-3 text-xs text-gray-500">flat fee</div>
                            <div className="col-span-2 text-right font-medium">${lineTotal.toFixed(2)}</div>
                            <div className="col-span-1 text-right">
                              <button type="button" onClick={() => updateBannerField('banner_addons', (pricingData.banner_addons || []).filter((_, i) => i !== idx))} className="text-gray-400 hover:text-red-500 text-sm leading-none" data-testid={`banner-addon-remove-${addon.key}`}>×</button>
                            </div>
                          </>
                        )}
                        {addon.pricing_type === 'each' && (
                          <>
                            <div className="col-span-2">
                              <Input type="number" value={addon.qty} onChange={(e) => { const u = [...(pricingData.banner_addons || [])]; u[idx] = { ...u[idx], qty: Number(e.target.value) || 0 }; updateBannerField('banner_addons', u); }} className="h-7 text-xs" data-testid={`banner-addon-qty-${addon.key}`} />
                            </div>
                            <div className="col-span-2">
                              <Input type="number" value={addon.unit_fee} onChange={(e) => { const u = [...(pricingData.banner_addons || [])]; u[idx] = { ...u[idx], unit_fee: Number(e.target.value) || 0 }; updateBannerField('banner_addons', u); }} className="h-7 text-xs" data-testid={`banner-addon-unit-fee-${addon.key}`} />
                            </div>
                            <div className="col-span-2 text-xs text-gray-500">each</div>
                            <div className="col-span-2 text-right font-medium">${lineTotal.toFixed(2)}</div>
                            <div className="col-span-1 text-right">
                              <button type="button" onClick={() => updateBannerField('banner_addons', (pricingData.banner_addons || []).filter((_, i) => i !== idx))} className="text-gray-400 hover:text-red-500 text-sm leading-none" data-testid={`banner-addon-remove-${addon.key}`}>×</button>
                            </div>
                          </>
                        )}
                        {addon.pricing_type === 'included' && (
                          <>
                            <div className="col-span-6 text-xs text-gray-500 italic">Included in price</div>
                            <div className="col-span-2 text-right text-gray-400">$0.00</div>
                            <div className="col-span-1 text-right">
                              <button type="button" onClick={() => updateBannerField('banner_addons', (pricingData.banner_addons || []).filter((_, i) => i !== idx))} className="text-gray-400 hover:text-red-500 text-sm leading-none" data-testid={`banner-addon-remove-${addon.key}`}>×</button>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                  <div className="flex justify-end text-sm font-semibold pt-1 border-t" data-testid="banners-addons-total">
                    Add-ons Total: ${(pricingData.banner_addons || []).reduce((sum, a) => {
                      if (a.pricing_type === 'flat_fee') return sum + Number(a.flat_fee || 0);
                      if (a.pricing_type === 'each') return sum + Number(a.unit_fee || 0) * Number(a.qty || 1);
                      return sum;
                    }, 0).toFixed(2)}
                  </div>
                </div>
              )}
            </div>

            {/* Banner Compare Methods */}
            {(() => {
              const c = computeBannerCompareMethods();
              if (!c) return null;
              return (
                <div className="border rounded-lg overflow-hidden" data-testid="banner-compare-methods">
                  {/* Header */}
                  <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-gray-800 text-sm">Compare Pricing Methods</p>
                      <p className="text-xs text-gray-500">{c.totalSqft.toFixed(2)} sq ft · {c.matName} · Qty {c.qty}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setBannerBreakdownExpanded((v) => !v)}
                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                      data-testid="banner-compare-toggle-breakdown"
                    >
                      {bannerBreakdownExpanded ? 'Hide Details' : 'Show Details'}
                    </button>
                  </div>

                  {/* Two-column method comparison */}
                  <div className="grid grid-cols-2 divide-x">
                    {/* Price Per Sq Ft */}
                    <div className="p-4 space-y-2" data-testid="banner-compare-ppsqft">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Price Per Sq Ft</p>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div className="flex justify-between">
                          <span>{c.totalSqft.toFixed(2)} sqft × ${c.retailRatePerSqft.toFixed(2)}</span>
                          <span>${c.retailBase.toFixed(2)}</span>
                        </div>
                        {c.addonFees > 0 && (
                          <div className="flex justify-between">
                            <span>Add-ons</span>
                            <span>${c.addonFees.toFixed(2)}</span>
                          </div>
                        )}
                        {c.ppsqftMinApplied && (
                          <div className="text-amber-600 text-xs">Min applied: ${c.minimumCharge.toFixed(2)}</div>
                        )}
                      </div>
                      <div className="pt-2 border-t flex items-center justify-between">
                        <span className="font-bold text-base" data-testid="banner-compare-ppsqft-total">
                          ${c.pricePerSqftTotal.toFixed(2)}
                        </span>
                        <button
                          type="button"
                          onClick={() => { setOverrideEnabled(true); setOverridePrice(c.pricePerSqftTotal.toFixed(2)); }}
                          className="text-xs px-2 py-1 border rounded hover:bg-gray-50"
                          data-testid="banner-compare-use-ppsqft"
                        >
                          Use
                        </button>
                      </div>
                    </div>

                    {/* Detailed M+L */}
                    <div className="p-4 space-y-2" data-testid="banner-compare-detailed">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Detailed Material + Labor</p>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div className="flex justify-between">
                          <span>Material ({c.wastePercent}% waste adj.)</span>
                          <span>${c.materialCost.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Labor ({c.totalLaborMin.toFixed(0)} min)</span>
                          <span>${c.totalLaborCost.toFixed(2)}</span>
                        </div>
                        {c.addonFees > 0 && (
                          <div className="flex justify-between">
                            <span>Add-ons</span>
                            <span>${c.addonFees.toFixed(2)}</span>
                          </div>
                        )}
                        {c.detailedMinApplied && (
                          <div className="text-amber-600 text-xs">Min applied: ${c.minimumCharge.toFixed(2)}</div>
                        )}
                      </div>
                      <div className="pt-2 border-t flex items-center justify-between">
                        <span className="font-bold text-base" data-testid="banner-compare-detailed-total">
                          ${c.detailedTotal.toFixed(2)}
                        </span>
                        <button
                          type="button"
                          onClick={() => { setOverrideEnabled(true); setOverridePrice(c.detailedTotal.toFixed(2)); }}
                          className="text-xs px-2 py-1 border rounded hover:bg-gray-50"
                          data-testid="banner-compare-use-detailed"
                        >
                          Use
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Expandable breakdown */}
                  {bannerBreakdownExpanded && (
                    <div className="border-t bg-gray-50 p-4 text-xs text-gray-700 space-y-3" data-testid="banner-compare-breakdown">
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">Area</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                          <span className="text-gray-500">Sq ft / piece:</span><span>{c.sqftPerPiece.toFixed(2)} sqft</span>
                          <span className="text-gray-500">Total sq ft (×{c.qty}):</span><span>{c.totalSqft.toFixed(2)} sqft</span>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">Material</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                          <span className="text-gray-500">Selected material:</span><span>{c.matName}</span>
                          <span className="text-gray-500">Shop cost/sqft:</span><span>${c.costPerSqft.toFixed(2)}</span>
                          <span className="text-gray-500">Waste:</span><span>{c.wastePercent}%</span>
                          <span className="text-gray-500">Waste-adj cost/sqft:</span><span>${c.wasteAdjCostPerSqft.toFixed(4)}</span>
                          <span className="text-gray-500">Total material cost:</span><span>${c.materialCost.toFixed(2)}</span>
                          <span className="text-gray-500">Retail rate/sqft:</span><span>${c.retailRatePerSqft.toFixed(2)}</span>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">Labor</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                          <span className="text-gray-500">Setup:</span><span>{c.setupMin} min</span>
                          <span className="text-gray-500">Production:</span><span>{c.productionMin} min{c.minPerSqft > 0 ? ` + ${c.minPerSqft}/sqft` : ''}</span>
                          <span className="text-gray-500">Add-on labor (production):</span><span>{(c.totalGeneralLaborMin - c.baseLaborMin).toFixed(0)} min</span>
                          {c.designAddonLaborMin > 0 && <><span className="text-gray-500">Add-on labor (design):</span><span>{c.designAddonLaborMin} min @ ${c.designRate}/hr</span></>}
                          {c.installAddonLaborMin > 0 && <><span className="text-gray-500">Add-on labor (install):</span><span>{c.installAddonLaborMin} min @ ${c.installRate}/hr</span></>}
                          <span className="text-gray-500">Production rate:</span><span>${c.prodRate}/hr</span>
                          <span className="text-gray-500">Total labor cost:</span><span>${c.totalLaborCost.toFixed(2)}</span>
                        </div>
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700 mb-1">Pricing</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                          <span className="text-gray-500">Price/sqft method total:</span><span>${c.pricePerSqftTotal.toFixed(2)}{c.ppsqftMinApplied ? ' (min)' : ''}</span>
                          <span className="text-gray-500">Detailed method total:</span><span>${c.detailedTotal.toFixed(2)}{c.detailedMinApplied ? ' (min)' : ''}</span>
                          <span className="text-gray-500">Difference:</span><span>${c.diff.toFixed(2)}</span>
                          <span className="text-gray-500">Minimum charge:</span><span>${c.minimumCharge.toFixed(2)}</span>
                          <span className="text-gray-500">Recommended:</span><span className="font-semibold">${c.recommendedPrice.toFixed(2)} ({c.recommendedMethod === 'price_per_sqft' ? 'Price/SqFt' : 'Detailed'})</span>
                          {overrideEnabled && overridePrice && <><span className="text-gray-500">Manual override:</span><span className="font-semibold text-blue-700">${parseFloat(overridePrice || 0).toFixed(2)}</span></>}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Recommended price + override row */}
                  <div className="border-t p-4 bg-teal-50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-medium text-teal-700 uppercase tracking-wide">
                        Recommended · {c.recommendedMethod === 'price_per_sqft' ? 'Price Per Sq Ft' : 'Detailed M+L'}
                        {' '}is ${c.diff.toFixed(2)} higher
                      </p>
                      <p className="text-2xl font-bold text-teal-800" data-testid="banner-compare-recommended">
                        ${c.recommendedPrice.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex gap-2 items-center flex-wrap">
                      <button
                        type="button"
                        onClick={() => { setOverrideEnabled(true); setOverridePrice(c.recommendedPrice.toFixed(2)); }}
                        className="px-3 py-1.5 bg-teal-600 text-white text-sm rounded hover:bg-teal-700 font-medium"
                        data-testid="banner-compare-use-recommended"
                      >
                        Use Recommended
                      </button>
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-gray-500">Override:</span>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="Manual price"
                          className="border rounded px-2 py-1 text-sm w-28 h-8"
                          value={overrideEnabled ? overridePrice : ''}
                          onChange={(e) => { setOverrideEnabled(true); setOverridePrice(e.target.value); }}
                          data-testid="banner-compare-manual-override"
                        />
                        {overrideEnabled && (
                          <button
                            type="button"
                            onClick={() => { setOverrideEnabled(false); setOverridePrice(''); }}
                            className="text-xs text-gray-400 hover:text-red-500"
                            data-testid="banner-compare-clear-override"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        );
      }

      case 'apparel': {
        const apCat = (foundationDefaults?.category_defaults || {}).apparel || {};
        const productTypes = apCat.available_product_types || [];
        const brandStylesMap = apCat.available_brand_styles || {};
        const placementSets = apCat.placement_sets || {};
        const methodCfg = apCat.method_config || {};
        const availMethods = apCat.available_decoration_methods || [];
        const selectedProduct = pricingData.apparel_product_type || (productTypes[0]?.key || 'short_sleeve_tee');
        const productInfo = productTypes.find((p) => p.key === selectedProduct) || {};
        const isHat = !!productInfo.is_hat;
        const placementKind = productInfo.allowed_placement_set || 'garment';
        const brandOptions = brandStylesMap[selectedProduct] || [];
        const placementOptions = placementSets[placementKind] || [];
        const selectedMethodCfg = methodCfg[pricingData.apparel_decoration_method || apCat.default_decoration_method || 'htv'] || {};
        const usesShopTable = !!selectedMethodCfg.uses_shop_table;
        return (
          <div className="space-y-4">
            {/* Product + Brand */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Product Type *</Label>
                <Select value={selectedProduct} onValueChange={(v) => setPricingData({ ...pricingData, apparel_product_type: v, apparel_brand_style_key: (brandStylesMap[v] || [])[0]?.key || '', apparel_placement_set: 'front' })}>
                  <SelectTrigger data-testid="ap-product-type"><SelectValue placeholder="Select product" /></SelectTrigger>
                  <SelectContent>
                    {productTypes.map((p) => (<SelectItem key={p.key} value={p.key}>{p.label}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Brand / Style *</Label>
                <Select value={pricingData.apparel_brand_style_key || ''} onValueChange={(v) => setPricingData({ ...pricingData, apparel_brand_style_key: v })}>
                  <SelectTrigger data-testid="ap-brand-style"><SelectValue placeholder="Select brand" /></SelectTrigger>
                  <SelectContent>
                    {brandOptions.map((b) => (<SelectItem key={b.key} value={b.key}>{b.label}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Garment color */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Garment / Hat Color</Label>
                <Input value={pricingData.apparel_garment_color || ''} onChange={(e) => setPricingData({ ...pricingData, apparel_garment_color: e.target.value })} placeholder="Black, White, Navy" data-testid="ap-color" />
              </div>
              <div>
                <Label>Blank Cost Override ($)</Label>
                <Input type="number" step="0.01" value={pricingData.blank_cost_override ?? ''} onChange={(e) => setPricingData({ ...pricingData, blank_cost_override: parseFloat(e.target.value) || null })} placeholder="Auto from brand" data-testid="ap-blank-override" />
              </div>
            </div>

            {/* Placement + Decoration Method */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Placement Set *</Label>
                <Select value={pricingData.apparel_placement_set || 'front'} onValueChange={(v) => setPricingData({ ...pricingData, apparel_placement_set: v })}>
                  <SelectTrigger data-testid="ap-placement"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {placementOptions.map((p) => (<SelectItem key={p.key} value={p.key}>{p.label}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Decoration Method *</Label>
                <Select value={pricingData.apparel_decoration_method || apCat.default_decoration_method || 'htv'} onValueChange={(v) => setPricingData({ ...pricingData, apparel_decoration_method: v })}>
                  <SelectTrigger data-testid="ap-decoration-method"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {availMethods.map((m) => (<SelectItem key={m} value={m}>{(methodCfg[m] || {}).label || m.replace(/_/g, ' ')}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="text-[11px] text-slate-500" data-testid="ap-method-source">
              {usesShopTable ? 'Pricing baseline: shop quantity-table (uploaded)' : 'Pricing baseline: cost-plus (method-specific)'}
            </div>

            {/* Method-specific details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Number of Colors</Label>
                <Input type="number" min="1" value={pricingData.apparel_num_colors ?? 1} onChange={(e) => setPricingData({ ...pricingData, apparel_num_colors: parseInt(e.target.value) || 1 })} data-testid="ap-num-colors" />
              </div>
              <div>
                <Label>Stitch Count (embroidery)</Label>
                <Input type="number" value={pricingData.apparel_stitch_count ?? ''} onChange={(e) => setPricingData({ ...pricingData, apparel_stitch_count: parseInt(e.target.value) || 0 })} placeholder="6000" data-testid="ap-stitch-count" />
              </div>
            </div>

            {/* Quantity / Plus size */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Plus Size Count (2XL–5XL, weighted)</Label>
                <Input type="number" value={pricingData.apparel_plus_size_count ?? 0} onChange={(e) => setPricingData({ ...pricingData, apparel_plus_size_count: parseInt(e.target.value) || 0 })} data-testid="ap-plus-size-count" disabled={isHat} />
                {isHat && <p className="text-[10px] text-slate-400">Not applicable to hats</p>}
              </div>
              <div>
                <Label>Manual Quote Override ($ total)</Label>
                <Input type="number" value={pricingData.apparel_manual_quote_override ?? 0} onChange={(e) => setPricingData({ ...pricingData, apparel_manual_quote_override: parseFloat(e.target.value) || 0 })} placeholder="0 = use suggested" data-testid="ap-manual-override" />
              </div>
            </div>

            {/* Artwork / Design */}
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.artwork_ready} onCheckedChange={(v) => setPricingData({ ...pricingData, artwork_ready: v })} data-testid="ap-artwork-ready" />
                <Label>Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.artwork_needed} onCheckedChange={(v) => setPricingData({ ...pricingData, artwork_needed: v })} data-testid="ap-artwork-needed" />
                <Label>Artwork Needed</Label>
              </div>
              <div>
                <Label>Design Complexity</Label>
                <Select value={pricingData.design_complexity || 'simple'} onValueChange={(v) => setPricingData({ ...pricingData, design_complexity: v })}>
                  <SelectTrigger data-testid="ap-design-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="simple">Simple</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="complex">Complex</SelectItem>
                    <SelectItem value="extreme">Extreme</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Add-ons */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.apparel_custom_name_number} onCheckedChange={(v) => setPricingData({ ...pricingData, apparel_custom_name_number: v })} data-testid="ap-custom-nn" />
                <Label>Custom Name / Number</Label>
              </div>
              <div>
                <Label>Name/Number Count</Label>
                <Input type="number" value={pricingData.apparel_custom_name_number_count ?? 0} onChange={(e) => setPricingData({ ...pricingData, apparel_custom_name_number_count: parseInt(e.target.value) || 0 })} disabled={!pricingData.apparel_custom_name_number} data-testid="ap-nn-count" />
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.apparel_specialty_finish} onCheckedChange={(v) => setPricingData({ ...pricingData, apparel_specialty_finish: v })} data-testid="ap-specialty-finish" />
                <Label>Specialty Finish / Vinyl</Label>
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.apparel_bag_and_fold} onCheckedChange={(v) => setPricingData({ ...pricingData, apparel_bag_and_fold: v })} data-testid="ap-bag-fold" />
                <Label>Bag & Fold</Label>
              </div>
              {isHat && (
                <>
                  <div className="flex items-center gap-2 h-10">
                    <Switch checked={!!pricingData.apparel_two_tone_hat_finish} onCheckedChange={(v) => setPricingData({ ...pricingData, apparel_two_tone_hat_finish: v })} data-testid="ap-two-tone" />
                    <Label>Two-Tone / Specialty Hat Finish</Label>
                  </div>
                  <div className="flex items-center gap-2 h-10">
                    <Switch checked={!!pricingData.apparel_leather_patch} onCheckedChange={(v) => setPricingData({ ...pricingData, apparel_leather_patch: v })} data-testid="ap-leather-patch" />
                    <Label>Leather / Faux Patch</Label>
                  </div>
                </>
              )}
            </div>

            {/* Rush */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.rush_order} onCheckedChange={(v) => setPricingData({ ...pricingData, rush_order: v })} data-testid="ap-rush" />
                <Label>Rush</Label>
              </div>
              <div>
                <Label>Rush % (override)</Label>
                <Input type="number" step="0.5" value={pricingData.apparel_rush_percent ?? (apCat.default_rush_percent || 17.5)} onChange={(e) => setPricingData({ ...pricingData, apparel_rush_percent: parseFloat(e.target.value) || 0 })} disabled={!pricingData.rush_order} data-testid="ap-rush-percent" />
              </div>
            </div>
          </div>
        );
      }

      case 'vehicle_graphics': {
        const vwCat = (foundationDefaults?.category_defaults || {}).vehicle_wraps || {};
        const matsAll = foundationDefaults?.materials || [];
        const allowedMatKeys = vwCat.available_wrap_material_keys || [];
        const wrapMaterials = allowedMatKeys.length
          ? matsAll.filter((m) => allowedMatKeys.includes(m.key || m.id)).map((m) => ({ id: m.key || m.id, name: m.name }))
          : WRAP_MATERIAL_DEFAULTS;
        const allowedLamKeys = vwCat.available_wrap_laminate_keys || [];
        const wrapLaminates = allowedLamKeys.length
          ? matsAll.filter((m) => allowedLamKeys.includes(m.key || m.id)).map((m) => ({ id: m.key || m.id, name: m.name }))
          : WRAP_LAMINATE_DEFAULTS;
        return (
          <div className="space-y-4">
            {/* Vehicle + Coverage */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Vehicle Type *</Label>
                <Select value={pricingData.vehicle_type || ''} onValueChange={(v) => setPricingData({ ...pricingData, vehicle_type: v })}>
                  <SelectTrigger data-testid="vw-vehicle-type"><SelectValue placeholder="Select vehicle" /></SelectTrigger>
                  <SelectContent>
                    {VEHICLE_TYPES.map((t) => (<SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Coverage Type *</Label>
                <Select value={pricingData.coverage_type || 'spot'} onValueChange={(v) => setPricingData({ ...pricingData, coverage_type: v })}>
                  <SelectTrigger data-testid="vw-coverage-type"><SelectValue placeholder="Select coverage" /></SelectTrigger>
                  <SelectContent>
                    {COVERAGE_TYPES.map((t) => (<SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            {pricingData.coverage_type === 'custom' && (
              <div>
                <Label>Custom Coverage %</Label>
                <Input type="number" placeholder="e.g. 65" value={pricingData.custom_coverage_percent ?? ''}
                  onChange={(e) => setPricingData({ ...pricingData, custom_coverage_percent: parseFloat(e.target.value) || 0 })}
                  data-testid="vw-custom-percent" />
              </div>
            )}

            {/* Vehicle Details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Make</Label>
                <Input value={pricingData.vehicle_make || ''} onChange={(e) => setPricingData({ ...pricingData, vehicle_make: e.target.value })} placeholder="Ford" data-testid="vw-make" />
              </div>
              <div>
                <Label>Model</Label>
                <Input value={pricingData.vehicle_model || ''} onChange={(e) => setPricingData({ ...pricingData, vehicle_model: e.target.value })} placeholder="Transit" data-testid="vw-model" />
              </div>
            </div>

            {/* Material + Laminate */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Wrap Material *</Label>
                <Select value={pricingData.wrap_material_key || ''} onValueChange={(v) => setPricingData({ ...pricingData, wrap_material_key: v })}>
                  <SelectTrigger data-testid="vw-wrap-material"><SelectValue placeholder="Select material" /></SelectTrigger>
                  <SelectContent>
                    {wrapMaterials.map((m) => (<SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end gap-2">
                <div className="flex items-center gap-2 h-10">
                  <Switch checked={!!pricingData.wrap_laminate_required} onCheckedChange={(v) => setPricingData({ ...pricingData, wrap_laminate_required: v })} data-testid="vw-laminate-required" />
                  <Label>Laminate Required</Label>
                </div>
              </div>
            </div>
            {pricingData.wrap_laminate_required && (
              <div>
                <Label>Laminate Type</Label>
                <Select value={pricingData.wrap_laminate_type_key || ''} onValueChange={(v) => setPricingData({ ...pricingData, wrap_laminate_type_key: v })}>
                  <SelectTrigger data-testid="vw-laminate-type"><SelectValue placeholder="Select laminate" /></SelectTrigger>
                  <SelectContent>
                    {wrapLaminates.map((m) => (<SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Window Perf */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.window_perf_included} onCheckedChange={(v) => setPricingData({ ...pricingData, window_perf_included: v })} data-testid="vw-perf-included" />
                <Label>Window Perf Included</Label>
              </div>
              {pricingData.window_perf_included && (
                <div>
                  <Label>Perf Scope</Label>
                  <Select value={pricingData.window_perf_scope || 'rear'} onValueChange={(v) => setPricingData({ ...pricingData, window_perf_scope: v })}>
                    <SelectTrigger data-testid="vw-perf-scope"><SelectValue placeholder="Select scope" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rear">Rear Only</SelectItem>
                      <SelectItem value="side">Side Windows</SelectItem>
                      <SelectItem value="full">Full Window Package</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            {/* Design */}
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.artwork_ready} onCheckedChange={(v) => setPricingData({ ...pricingData, artwork_ready: v })} data-testid="vw-artwork-ready" />
                <Label>Artwork Ready</Label>
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={pricingData.artwork_needed !== false} onCheckedChange={(v) => setPricingData({ ...pricingData, artwork_needed: v })} data-testid="vw-artwork-needed" />
                <Label>Artwork Needed</Label>
              </div>
              <div>
                <Label>Design Complexity</Label>
                <Select value={pricingData.design_complexity || 'medium'} onValueChange={(v) => setPricingData({ ...pricingData, design_complexity: v })}>
                  <SelectTrigger data-testid="vw-design-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="simple">Simple</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="complex">Complex</SelectItem>
                    <SelectItem value="extreme">Extreme</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Surface Prep / Removal */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Surface Prep</Label>
                <Select value={pricingData.surface_prep_level || 'none'} onValueChange={(v) => setPricingData({ ...pricingData, surface_prep_level: v })}>
                  <SelectTrigger data-testid="vw-prep-level"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="basic">Basic (+0.25h)</SelectItem>
                    <SelectItem value="moderate">Moderate (+0.75h)</SelectItem>
                    <SelectItem value="heavy">Heavy (+1.5h)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Removal</Label>
                <Select value={pricingData.removal_scope || 'none'} onValueChange={(v) => setPricingData({ ...pricingData, removal_scope: v })}>
                  <SelectTrigger data-testid="vw-removal-scope"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="small">Small (+0.5h)</SelectItem>
                    <SelectItem value="partial">Partial (+2h)</SelectItem>
                    <SelectItem value="full">Full (+4h+)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Install */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={pricingData.install_required !== false} onCheckedChange={(v) => setPricingData({ ...pricingData, install_required: v })} data-testid="vw-install-required" />
                <Label>Install Required</Label>
              </div>
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.second_installer_required} onCheckedChange={(v) => setPricingData({ ...pricingData, second_installer_required: v })} data-testid="vw-second-installer" />
                <Label>Second Installer (Helper)</Label>
              </div>
              <div>
                <Label>Install Difficulty</Label>
                <Select value={pricingData.install_difficulty_level || 'medium'} onValueChange={(v) => setPricingData({ ...pricingData, install_difficulty_level: v })}>
                  <SelectTrigger data-testid="vw-install-difficulty"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy (1.0x)</SelectItem>
                    <SelectItem value="medium">Medium (1.25x)</SelectItem>
                    <SelectItem value="difficult">Difficult (1.5x)</SelectItem>
                    <SelectItem value="extreme">Extreme (2.0x)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Panel / Seam Complexity</Label>
                <Select value={pricingData.seam_complexity || 'basic'} onValueChange={(v) => setPricingData({ ...pricingData, seam_complexity: v })}>
                  <SelectTrigger data-testid="vw-seam-complexity"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic (1.0x)</SelectItem>
                    <SelectItem value="moderate">Moderate (1.15x)</SelectItem>
                    <SelectItem value="advanced">Advanced (1.3x)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Rush + Optional Override */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2 h-10">
                <Switch checked={!!pricingData.rush_order} onCheckedChange={(v) => setPricingData({ ...pricingData, rush_order: v })} data-testid="vw-rush" />
                <Label>Rush</Label>
              </div>
              <div>
                <Label>Override Estimated Sq Ft (optional)</Label>
                <Input type="number" value={pricingData.estimated_vehicle_sqft ?? ''}
                  onChange={(e) => setPricingData({ ...pricingData, estimated_vehicle_sqft: parseFloat(e.target.value) || 0 })}
                  placeholder="Auto from vehicle type" data-testid="vw-sqft-override" />
              </div>
            </div>
          </div>
        );
      }

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
                  onChange={(e) => {
                    setDescription(e.target.value);
                    if (category === 'digital_print') {
                      setDigitalPrintSources((prev) => ({ ...prev, description: 'user' }));
                    }
                    if (category === 'cut_vinyl') {
                      setCutVinylSources((prev) => ({ ...prev, description: 'user' }));
                    }
                  }}
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
                  {/* ============== PHASE 3: STANDARDIZED BREAKDOWN DISPLAY ============== */}
                  <StandardizedPricingBreakdown
                    calculation={calculation}
                    formatCurrency={formatCurrency}
                    finalPrice={finalPrice}
                  />

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

                  {/* Banner Add-ons Summary in Results */}
                  {category === 'banners' && !overrideEnabled && (pricingData.banner_addons || []).length > 0 && (() => {
                    const addonTotal = (pricingData.banner_addons || []).reduce((sum, a) => {
                      if (a.pricing_type === 'flat_fee') return sum + Number(a.flat_fee || 0);
                      if (a.pricing_type === 'each') return sum + Number(a.unit_fee || 0) * Number(a.qty || 1);
                      return sum;
                    }, 0);
                    return addonTotal > 0 ? (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm" data-testid="banners-addon-results-summary">
                        <div className="flex justify-between text-gray-700">
                          <span>Base price</span>
                          <span>{formatCurrency(calculation.selling_price || calculation.suggested_price)}</span>
                        </div>
                        <div className="flex justify-between text-blue-700 font-medium">
                          <span>Add-ons</span>
                          <span>+{formatCurrency(addonTotal)}</span>
                        </div>
                        <div className="flex justify-between font-bold text-gray-900 border-t border-blue-200 mt-1 pt-1">
                          <span>Total with add-ons</span>
                          <span>{formatCurrency((calculation.selling_price || calculation.suggested_price) + addonTotal)}</span>
                        </div>
                      </div>
                    ) : null;
                  })()}

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
                  {(() => {
                    const bannerAddonAmt = (category === 'banners' && !overrideEnabled)
                      ? (pricingData.banner_addons || []).reduce((sum, a) => {
                          if (a.pricing_type === 'flat_fee') return sum + Number(a.flat_fee || 0);
                          if (a.pricing_type === 'each') return sum + Number(a.unit_fee || 0) * Number(a.qty || 1);
                          return sum;
                        }, 0)
                      : 0;
                    const displayPrice = (overrideEnabled && overridePrice)
                      ? parseFloat(overridePrice)
                      : (calculation.selling_price || calculation.suggested_price) + bannerAddonAmt;
                    return (
                      <div className="flex items-center justify-between p-4 bg-teal-500 rounded-lg">
                        <div className="text-white">
                          <p className="text-sm opacity-80">Final Price</p>
                          <p className="text-3xl font-bold">{formatCurrency(displayPrice)}</p>
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
                    );
                  })()}
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
