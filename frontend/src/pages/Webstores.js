import { useEffect, useState, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { ShellCard, ShellCardHeader, ShellCardTitle, PageStack } from '../components/ui/shell-card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { 
  Store, Heart, Building2, User, Plus, ShoppingCart, 
  Eye, Edit2, Trash2, Package, DollarSign, TrendingUp,
  ExternalLink, Check, X, Settings, Copy, Link2, BarChart3,
  Upload, ImageIcon, CreditCard, AlertTriangle, Loader2, Palette,
  QrCode, Download, Shirt, Sticker, Gift, CalendarDays, Search,
  Mail, Lock, ClipboardCheck, Send, ListChecks, CheckCircle2, Wand2
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { toast } from 'sonner';
import WebstoreDetailDashboard from '../components/WebstoreDetailDashboard';
import StoreSetupWizard from '../components/webstores/StoreSetupWizard';
import WebstoreSetupFlow from '../components/WebstoreSetupFlow';
import WebstoreOwnerConnectCard from '../components/WebstoreOwnerConnectCard';

// Product category options
const categoryOptions = [
  { value: 'apparel', label: 'Apparel', icon: Shirt },
  { value: 'signs', label: 'Signs', icon: Package },
  { value: 'decals', label: 'Decals', icon: Sticker },
  { value: 'promotional', label: 'Promotional', icon: Gift },
  { value: 'events', label: 'Events', icon: CalendarDays },
  { value: 'other', label: 'Other', icon: Package },
];

const storeTypes = [
  { value: 'business', label: 'Business (B2B)', icon: Building2, description: 'Employee apparel & company stores' },
  { value: 'fundraiser', label: 'Fundraiser', icon: Heart, description: 'Campaigns with profit sharing' },
  { value: 'creator', label: 'Creator', icon: User, description: 'Individual merch with commission' },
  { value: 'event', label: 'Event Store', icon: CalendarDays, description: 'Event merchandise & order deadlines' },
];

const getStoreTypeIcon = (type) => {
  const st = storeTypes.find(s => s.value === type);
  return st ? st.icon : Store;
};

const getStoreTypeColor = (type) => {
  const colors = {
    business: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    fundraiser: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    creator: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    event: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  };
  return colors[type] || 'bg-gray-500/20 text-gray-400';
};

const getStatusBadge = (status) => {
  const colors = {
    active: 'bg-green-500/20 text-green-400 border-green-500/30',
    disabled: 'bg-red-500/20 text-red-400 border-red-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    completed: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    closed: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return colors[status] || colors.pending;
};

/** Returns the correct questionnaire label for each store type. */
const getQuestionnaireLabel = (storeType) => ({
  event:       'Event Store Setup Questionnaire',
  fundraiser:  'Fundraiser Store Setup Questionnaire',
  creator:     'Team / School Store Setup Questionnaire',
  team:        'Team / School Store Setup Questionnaire',
  team_school: 'Team / School Store Setup Questionnaire',
  business:    'Business Store Setup Questionnaire',
  b2b:         'Business Store Setup Questionnaire',
  company:     'Business Store Setup Questionnaire',
}[storeType] || 'Store Setup Questionnaire');

/** Returns a friendly store-type description for the "not sent" questionnaire state. */
const getQuestionnaireDescription = (storeType) => ({
  event:      'collect event details, fulfillment preferences, fundraiser settings, and Stripe Connect information.',
  fundraiser: 'collect fundraiser details, profit allocation preferences, and Stripe Connect information.',
  creator:    'collect team / school details, product preferences, and Stripe Connect information.',
  business:   'collect business details, product requirements, and Stripe Connect information.',
}[storeType] || 'collect store details and setup preferences.');

/**
 * Derives a display-friendly questionnaire phase from the raw status object.
 * Phases: not_sent | draft | sent | submitted | awaiting_review | applied
 */
const getQStatusPhase = (questionnaireStatus) => {
  if (!questionnaireStatus?.linked) return 'not_sent';
  const q    = questionnaireStatus.questionnaire;
  const resp = questionnaireStatus.latest_response;
  if (resp?.applied_to_webstore) return 'applied';
  if (resp?.submitted_at)         return 'awaiting_review';
  if (q?.last_sent_at)            return 'sent';
  if (q)                          return 'draft';
  return 'not_sent';
};

const Q_PHASE_CONFIG = {
  not_sent:        { label: 'Not Sent',        badge: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  draft:           { label: 'Draft',           badge: 'bg-gray-500/20 text-gray-400 border-gray-500/30' },
  sent:            { label: 'Sent',            badge: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  awaiting_review: { label: 'Awaiting Review', badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  applied:         { label: 'Applied',         badge: 'bg-green-500/20 text-green-400 border-green-500/30' },
};

const normalizeWebstoreList = (payload) => {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.webstores)) return payload.webstores;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
};

const DEV_BYPASS_STRIPE = true;

export default function Webstores() {
  const { 
    getWebstores, createWebstore, updateWebstore, deleteWebstore,
    getWebstoreOrdersV2, getProducts, getWebstoreProducts,
    assignProductToWebstore, removeProductFromWebstore, updateWebstoreProductStatus,
    createJobFromOrder, recordPayout, getWebstorePayouts,
    uploadWebstoreLogo, uploadWebstoreBanner,
    getStripeConnectStatus, createStripeConnectAccount,
    createProduct,
    getWebstoreQuestionnaire, sendWebstoreQuestionnaire, applyWebstoreQuestionnaireAnswers,
    getWebstoreEventChecklist,
    stampWebstoreAdminProgress,
    generateAIContent,
  } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [stripeConnected, setStripeConnected] = useState(null); // null = loading, true/false = status
  const [connectingStripe, setConnectingStripe] = useState(false);
  const [webstores, setWebstores] = useState([]);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [storeSearch, setStoreSearch] = useState('');
  const [activeTab, setActiveTab] = useState('stores');

  // Phase 2 — the Webstores ribbon drives the active tab + create dialog via
  // URL query string (`?tab=stores|orders`, `?new=true`). Sync local state
  // with these params and strip them once consumed so deep links stay clean.
  const location = useLocation();
  const navigate = useNavigate();
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [createdStore, setCreatedStore]             = useState(null); // set after successful creation
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [storeProducts, setStoreProducts] = useState([]);
  const [storePayouts, setStorePayouts] = useState([]);
  const [storeDetailOrders, setStoreDetailOrders] = useState([]);
  const [loadingDetailOrders, setLoadingDetailOrders] = useState(false);
  const [detailPayoutAmount, setDetailPayoutAmount] = useState('');
  const [detailPayoutNotes, setDetailPayoutNotes] = useState('');
  const [submittingDetailPayout, setSubmittingDetailPayout] = useState(false);
  const [detailTab, setDetailTab] = useState('setup');
  const [loadingStoreDetails, setLoadingStoreDetails] = useState(false);
  
  // Create product inline form states
  const [showCreateProduct, setShowCreateProduct] = useState(false);
  const [creatingProduct, setCreatingProduct] = useState(false);
  const [newProductData, setNewProductData] = useState({
    name: '',
    description: '',
    category: 'other',
    base_cost: '',
    retail_price: ''
  });
  const [productImages, setProductImages] = useState([]);
  const [productImagePreviews, setProductImagePreviews] = useState([]);
  const productImageRef = useRef(null);
  
  // Logo upload states
  const [logoPreview, setLogoPreview] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const logoInputRef = useRef(null);
  
  // Banner upload states
  const [bannerPreview, setBannerPreview] = useState(null);
  const [bannerFile, setBannerFile] = useState(null);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const bannerInputRef = useRef(null);

  // Store description editor + AI rewrite
  const [descriptionDraft, setDescriptionDraft] = useState('');
  const [rewritingDesc, setRewritingDesc] = useState(false);
  
  // Create store loading state (prevent double-click)
  const [creatingStore, setCreatingStore] = useState(false);

  // Settings-tab local edit state for event/locked fields
  const [eventEdits, setEventEdits] = useState({});
  const [lockedEdits, setLockedEdits] = useState({});
  const [fundraiserEdits, setFundraiserEdits] = useState({});
  const [savingEvent, setSavingEvent] = useState(false);
  const [savingLocked, setSavingLocked] = useState(false);
  const [savingFundraiser, setSavingFundraiser] = useState(false);

  // Event Store questionnaire state
  const [questionnaireStatus, setQuestionnaireStatus] = useState(null);   // null = not loaded
  const [loadingQuestionnaire, setLoadingQuestionnaire] = useState(false);
  // Event Store setup checklist (admin side)
  const [eventChecklist, setEventChecklist] = useState(null);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [sendingQuestionnaire, setSendingQuestionnaire] = useState(false);
  const [applyingAnswers, setApplyingAnswers] = useState(false);
  const [sendEmailOverride, setSendEmailOverride] = useState('');
  const [sendMessageOverride, setSendMessageOverride] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    store_type: '',
    owner_name: '',
    owner_email: '',
    owner_phone: '',
    description: '',
    is_public: true,
    branding: { primary_color: '#0D9488' },
    fundraiser_goal: 0,
    fundraiser_start_date: '',
    fundraiser_end_date: '',
    fundraiser_profit_percent: 40,
    creator_commission_type: 'percentage',
    creator_commission_value: 20,
    // Event-store fields
    event_name: '',
    event_type: '',
    event_start_date: '',
    event_end_date: '',
    event_location: '',
    order_deadline: '',
    pickup_delivery_date: '',
    pickup_delivery_instructions: '',
    auto_close_after_deadline: false,
    allow_late_orders: false,
    // Event-store fundraiser fields
    fundraiser_enabled: false,
    fundraiser_name: '',
    fundraiser_description: '',
    fundraiser_goal_amount: '',
    show_progress_bar: false,
    allow_checkout_donations: false,
    donation_amount_options: '',
    allow_custom_donation: false,
    profit_allocation_enabled: false,
    profit_allocation_type: '',
    profit_allocation_percentage: '',
    fixed_amount_per_item: '',
    fundraiser_cap_amount: '',
    include_donations_in_progress: true,
    include_profit_allocation_in_progress: true,
    show_total_raised_publicly: false,
    show_supporter_names: '',
    // Tenant-controlled locked settings — only store-level fees here.
    // Per-product pricing (base_item_cost, production_cost, retail_price, etc.)
    // lives at the product assignment level, not the store level.
    locked_settings: {
      shipping_handling_enabled: false,
      shipping_handling_fee: '',
      shipping_handling_label: '',
      shipping_handling_description: '',
    },
  });
  const apiRef = useRef({
    getWebstores,
    getWebstoreOrdersV2,
    getProducts,
    getStripeConnectStatus,
    createStripeConnectAccount,
  });

  useEffect(() => {
    apiRef.current = {
      getWebstores,
      getWebstoreOrdersV2,
      getProducts,
      getStripeConnectStatus,
      createStripeConnectAccount,
    };
  }, [getWebstores, getWebstoreOrdersV2, getProducts, getStripeConnectStatus, createStripeConnectAccount]);

  const loadData = useCallback(async ({ suppressStoreErrorToast = false } = {}) => {
    setLoading(true);
    // Fetch each resource independently. Previously a single failed request
    // (e.g. /products timing out) short-circuited Promise.all and the entire
    // try/catch bailed — leaving `webstores` stale so a just-created store
    // appeared to "not show up in the list" even though the POST succeeded.
    const [storesResult, ordersResult, productsResult] = await Promise.allSettled([
      apiRef.current.getWebstores(),
      apiRef.current.getWebstoreOrdersV2(),
      apiRef.current.getProducts(),
    ]);

    let storesLoaded = false;
    if (storesResult.status === 'fulfilled') {
      setWebstores(normalizeWebstoreList(storesResult.value));
      storesLoaded = true;
    } else {
      console.error('Error loading webstores:', storesResult.reason);
      try {
        // Retry once: the create flow can race with transient API/network hiccups.
        const retryStores = await apiRef.current.getWebstores();
        setWebstores(normalizeWebstoreList(retryStores));
        storesLoaded = true;
      } catch (retryErr) {
        console.error('Webstore retry failed:', retryErr);
        if (!suppressStoreErrorToast) {
          toast.error('Could not refresh webstore list');
        }
      }
    }
    if (ordersResult.status === 'fulfilled') {
      setOrders(ordersResult.value || []);
    } else {
      console.error('Error loading orders:', ordersResult.reason);
    }
    if (productsResult.status === 'fulfilled') {
      setProducts(productsResult.value || []);
    } else {
      console.error('Error loading products:', productsResult.reason);
    }
    setLoading(false);
    return { storesLoaded };
  }, []);
  
  const checkStripeStatus = useCallback(async () => {
    // Bypass Stripe check in dev/test mode
    if (DEV_BYPASS_STRIPE) {
      console.log('DEV MODE: Bypassing Stripe Connect requirement');
      setStripeConnected(true);
      return;
    }
    
    try {
      const status = await apiRef.current.getStripeConnectStatus();
      setStripeConnected(status.connected && status.charges_enabled);
    } catch (err) {
      console.error('Error checking Stripe status:', err);
      setStripeConnected(false);
    }
  }, []);

  const handleConnectStripe = async () => {
    setConnectingStripe(true);
    try {
      const origin = window.location.origin;
      const result = await apiRef.current.createStripeConnectAccount({
        return_url: `${origin}/webstores?stripe_return=true`,
        refresh_url: `${origin}/webstores?stripe_refresh=true`,
      });
      if (result.url) {
        window.location.href = result.url;
      }
    } catch (err) {
      console.error('Error connecting Stripe:', err);
      const detail = err.response?.data?.detail || '';
      if (detail.includes('signed up for Connect')) {
        toast.error('Stripe Connect is not enabled on this platform yet. Contact support.', { duration: 8000 });
      } else {
        toast.error(detail || 'Failed to start Stripe connection. Please try again.');
      }
    }
    setConnectingStripe(false);
  };

  useEffect(() => {
    checkStripeStatus();
    loadData();
  }, [checkStripeStatus, loadData]);

  // Phase 2 ribbon → page sync. The WebstoresRibbon writes `?tab=` and
  // `?new=true` query params; this effect mirrors them into local state and
  // then strips them from the URL so refreshes don't keep re-firing.
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tabParam = params.get('tab');
    const newParam = params.get('new');
    let mutated = false;

    if (tabParam && (tabParam === 'stores' || tabParam === 'orders') && tabParam !== activeTab) {
      setActiveTab(tabParam);
      params.delete('tab');
      mutated = true;
    } else if (tabParam) {
      params.delete('tab');
      mutated = true;
    }

    if (newParam === 'true') {
      resetForm();
      setIsCreateDialogOpen(true);
      params.delete('new');
      mutated = true;
    }

    // After Stripe redirects back, re-check status so the page updates
    const stripeReturn = params.get('stripe_return') || params.get('stripe_refresh');
    if (stripeReturn) {
      checkStripeStatus();
      params.delete('stripe_return');
      params.delete('stripe_refresh');
      mutated = true;
    }

    if (mutated) {
      const nextSearch = params.toString();
      navigate(
        nextSearch ? `${location.pathname}?${nextSearch}` : location.pathname,
        { replace: true },
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search, checkStripeStatus]);

  // Deep-link from dashboard: open a specific store + tab via router state
  useEffect(() => {
    const { openStoreId, openTab } = location.state || {};
    if (!openStoreId || !webstores.length) return;
    const store = webstores.find(s => s.id === openStoreId);
    if (!store) return;
    handleViewStore(store);
    if (openTab) setDetailTab(openTab);
    // Clear the state so navigating back doesn't re-open it
    navigate(location.pathname, { replace: true, state: {} });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state, webstores]);

  const resetForm = () => {
    setFormData({
      name: '',
      store_type: '',
      owner_name: '',
      owner_email: '',
      owner_phone: '',
      description: '',
      is_public: true,
      branding: { primary_color: '#0D9488' },
      fundraiser_goal: 0,
      fundraiser_start_date: '',
      fundraiser_end_date: '',
      fundraiser_profit_percent: 40,
      creator_commission_type: 'percentage',
      creator_commission_value: 20,
      // Event-store fields
      event_name: '',
      event_type: '',
      event_start_date: '',
      event_end_date: '',
      event_location: '',
      order_deadline: '',
      pickup_delivery_date: '',
      pickup_delivery_instructions: '',
      auto_close_after_deadline: false,
      allow_late_orders: false,
      // Event-store fundraiser fields
      fundraiser_enabled: false,
      fundraiser_name: '',
      fundraiser_description: '',
      fundraiser_goal_amount: '',
      show_progress_bar: false,
      allow_checkout_donations: false,
      donation_amount_options: '',
      allow_custom_donation: false,
      profit_allocation_enabled: false,
      profit_allocation_type: '',
      profit_allocation_percentage: '',
      fixed_amount_per_item: '',
      fundraiser_cap_amount: '',
      include_donations_in_progress: true,
      include_profit_allocation_in_progress: true,
      show_total_raised_publicly: false,
      show_supporter_names: '',
      // Locked settings — only store-level shipping/handling
      locked_settings: {
        shipping_handling_enabled: false,
        shipping_handling_fee: '',
        shipping_handling_label: '',
        shipping_handling_description: '',
      },
    });
    setLogoPreview(null);
    setLogoFile(null);
    setBannerPreview(null);
    setBannerFile(null);
    setCreatingStore(false);
  };

  /** Close the create dialog and clear all related state. */
  const handleCloseCreateDialog = () => {
    setIsCreateDialogOpen(false);
    setCreatedStore(null);
    resetForm();
  };

  /** Send the setup questionnaire for a just-created store. Returns the API response. */
  const handleSendQuestionnaireAfterCreate = async (storeId, email) => {
    const origin = window.location.origin;
    const result = await sendWebstoreQuestionnaire(storeId, {
      email: email || undefined,
      public_url: origin,
    });
    // Refresh questionnaire status if this store is the one currently open in the detail dialog
    if (storeId === selectedStore?.id) {
      try {
        const qs = await getWebstoreQuestionnaire(storeId);
        setQuestionnaireStatus(qs);
      } catch {}
    }
    return result; // { email_sent, link, email }
  };

  // Handle logo file selection
  const handleLogoSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please select a valid image file (PNG, JPEG, WebP, or GIF)');
      return;
    }
    
    // Validate file size (2MB max)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Image must be less than 2MB');
      return;
    }
    
    setLogoFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setLogoPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Handle banner file selection
  const handleBannerSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please select a valid image file (PNG, JPEG, WebP, or GIF)');
      return;
    }
    
    // Validate file size (5MB max for banners)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Banner image must be less than 5MB');
      return;
    }
    
    setBannerFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setBannerPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // Upload logo for existing store
  const handleUploadLogo = async (storeId = null) => {
    if (!logoFile) return;
    
    const targetId = storeId || selectedStore?.id;
    if (!targetId) return;
    
    setUploadingLogo(true);
    try {
      const result = await uploadWebstoreLogo(targetId, logoFile);
      toast.success('Logo uploaded successfully');
      
      // Update local state
      if (selectedStore) {
        setSelectedStore({
          ...selectedStore,
          branding: { ...selectedStore.branding, logo_url: result.logo_url }
        });
      }
      
      setLogoFile(null);
      setLogoPreview(null);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload logo');
    }
    setUploadingLogo(false);
  };

  // Upload banner for existing store
  const handleUploadBanner = async (storeId = null) => {
    if (!bannerFile) return;
    
    const targetId = storeId || selectedStore?.id;
    if (!targetId) return;
    
    setUploadingBanner(true);
    try {
      const result = await uploadWebstoreBanner(targetId, bannerFile);
      toast.success('Banner uploaded successfully');
      
      // Update local state
      if (selectedStore) {
        setSelectedStore({
          ...selectedStore,
          branding: { ...selectedStore.branding, banner_url: result.banner_url }
        });
      }
      
      setBannerFile(null);
      setBannerPreview(null);
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload banner');
    }
    setUploadingBanner(false);
  };

  const handleCreateStore = async (e) => {
    if (e && typeof e.preventDefault === 'function') {
      e.preventDefault();
    }
    if (!formData.name.trim() || !formData.owner_name.trim()) {
      toast.error('Store name and owner are required');
      return;
    }
    
    // Prevent double-click
    if (creatingStore) return;
    setCreatingStore(true);
    
    try {
      // Clean empty strings → null for all Optional[float] and Optional[date] fields.
      // Pydantic rejects "" for Optional[float]; sending null is correct.
      const FLOAT_FIELDS = [
        'fundraiser_goal_amount', 'profit_allocation_percentage',
        'fixed_amount_per_item', 'fundraiser_cap_amount', 'fundraiser_goal',
      ];
      const DATE_FIELDS = [
        'fundraiser_start_date', 'fundraiser_end_date',
        'event_start_date', 'event_end_date',
        'order_deadline', 'pickup_delivery_date',
      ];
      const sanitizeTop = (data) => {
        const out = { ...data };
        FLOAT_FIELDS.forEach((k) => { if (out[k] === '' || out[k] === undefined) out[k] = null; });
        DATE_FIELDS.forEach((k) => { if (out[k] === '' || out[k] === undefined) out[k] = null; });
        return out;
      };
      const cleanedLockedSettings = Object.fromEntries(
        Object.entries(formData.locked_settings || {}).map(([k, v]) => [k, v === '' ? null : v])
      );
      const payload = sanitizeTop({ ...formData, locked_settings: cleanedLockedSettings });
      const newStore = await createWebstore(payload);
      
      // If a logo file was selected, upload it to the new store
      if (logoFile && newStore?.id) {
        try {
          await uploadWebstoreLogo(newStore.id, logoFile);
        } catch (uploadErr) {
          console.error('Logo upload failed:', uploadErr);
          toast.warning('Store created but logo upload failed');
        }
      }
      
      // If a banner file was selected, upload it to the new store
      if (bannerFile && newStore?.id) {
        try {
          await uploadWebstoreBanner(newStore.id, bannerFile);
        } catch (uploadErr) {
          console.error('Banner upload failed:', uploadErr);
          toast.warning('Store created but banner upload failed');
        }
      }
      
      toast.success('Webstore created');

      // Optimistic insert so the new store appears immediately even if
      // background refresh has a transient failure.
      if (newStore?.id) {
        setWebstores((current) => {
          const safeCurrent = Array.isArray(current) ? current : [];
          const exists = safeCurrent.some((store) => store.id === newStore.id);
          if (exists) {
            return safeCurrent.map((store) => (store.id === newStore.id ? newStore : store));
          }
          return [newStore, ...safeCurrent];
        });
      }

      // Show the result / questionnaire screen instead of closing immediately.
      setCreatedStore(newStore);

      // Ensure the freshly-created store is visible: clear any filter/search.
      if (newStore?.store_type && newStore.store_type !== selectedType) {
        setSelectedType('all');
      }
      setStoreSearch('');
      // Refresh in background (non-blocking).
      loadData({ suppressStoreErrorToast: true });
    } catch (err) {
      console.error('Failed to create webstore:', err);
      const rawDetail = err.response?.data?.detail;
      const errMsg = !rawDetail ? 'Failed to create webstore'
        : typeof rawDetail === 'string' ? rawDetail
        : Array.isArray(rawDetail) ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
        : 'Failed to create webstore';
      toast.error(errMsg);
    } finally {
      setCreatingStore(false);
    }
  };

  const handleViewStore = async (store) => {
    // Reset store-specific state first to prevent showing stale data
    setStoreProducts([]);
    setStorePayouts([]);
    setLoadingStoreDetails(true);

    setSelectedStore(store);
    // Default to Setup tab for stores that aren't live yet; Dashboard for live/completed stores.
    setDetailTab(store.status === 'active' || store.status === 'completed' ? 'dashboard' : 'setup');

    // Reset branding form state
    setLogoPreview(null);
    setLogoFile(null);
    setBannerPreview(null);
    setBannerFile(null);
    setDescriptionDraft(store.description || '');

    // Initialise event/locked edit state from the store record
    setEventEdits({
      event_name: store.event_name || '',
      event_type: store.event_type || '',
      event_start_date: store.event_start_date || '',
      event_end_date: store.event_end_date || '',
      event_location: store.event_location || '',
      order_deadline: store.order_deadline || '',
      pickup_delivery_date: store.pickup_delivery_date || '',
      pickup_delivery_instructions: store.pickup_delivery_instructions || '',
      auto_close_after_deadline: store.auto_close_after_deadline || false,
      allow_late_orders: store.allow_late_orders || false,
    });
    const ls = store.locked_settings || {};
    // Only store-level shipping/handling fields are editable here.
    // Product-level fields (base_item_cost, production_cost, etc.) belong at product level.
    setLockedEdits({
      // Keep these read if previously stored (backward compat) but don't expose edit UI
      _legacy_base_item_cost: ls.base_item_cost,
      _legacy_production_cost: ls.production_cost,
      _legacy_retail_price: ls.retail_price,
      _legacy_store_owner_profit: ls.store_owner_profit,
      _legacy_profit_split: ls.profit_split,
      _legacy_setup_fee: ls.setup_fee,
      _legacy_shipping_fee: ls.shipping_fee,
      _legacy_handling_fee: ls.handling_fee,
      // Editable store-level fields:
      shipping_handling_enabled: ls.shipping_handling_enabled || false,
      shipping_handling_fee: ls.shipping_handling_fee ?? '',
      shipping_handling_label: ls.shipping_handling_label || '',
      shipping_handling_description: ls.shipping_handling_description || '',
    });

    // Fundraiser edits state
    setFundraiserEdits({
      fundraiser_enabled: store.fundraiser_enabled || false,
      fundraiser_name: store.fundraiser_name || '',
      fundraiser_description: store.fundraiser_description || '',
      fundraiser_goal_amount: store.fundraiser_goal_amount ?? '',
      show_progress_bar: store.show_progress_bar || false,
      allow_checkout_donations: store.allow_checkout_donations || false,
      donation_amount_options: store.donation_amount_options || '',
      allow_custom_donation: store.allow_custom_donation || false,
      profit_allocation_enabled: store.profit_allocation_enabled || false,
      profit_allocation_type: store.profit_allocation_type || '',
      profit_allocation_percentage: store.profit_allocation_percentage ?? '',
      fixed_amount_per_item: store.fixed_amount_per_item ?? '',
      fundraiser_cap_amount: store.fundraiser_cap_amount ?? '',
      include_donations_in_progress: store.include_donations_in_progress ?? true,
      include_profit_allocation_in_progress: store.include_profit_allocation_in_progress ?? true,
      show_total_raised_publicly: store.show_total_raised_publicly || false,
      show_supporter_names: store.show_supporter_names || '',
    });

    // Reset create product form state
    setShowCreateProduct(false);
    setNewProductData({
      name: '',
      description: '',
      category: 'other',
      base_cost: '',
      retail_price: '',
      production_cost: '',
      setup_fee: '',
    });

    // Reset event-specific state immediately so previously-opened store data
    // doesn't bleed through while the new fetches are in flight.
    setQuestionnaireStatus(null);
    setEventChecklist(null);

    // CRITICAL: Open the dialog BEFORE awaiting any network calls. Earlier
    // versions awaited the event-store questionnaire + checklist endpoints
    // here before flipping isDetailDialogOpen, which meant a slow or hung
    // request blocked the dialog from ever opening — the exact black-screen
    // risk Phase 1 had to guard against. Fire-and-forget fetches now so the
    // dialog renders instantly and each card surfaces its own loading state.
    setIsDetailDialogOpen(true);

    // Background: products + payouts for every store type.
    (async () => {
      try {
        const [prods, payouts] = await Promise.all([
          getWebstoreProducts(store.id, true),
          getWebstorePayouts(store.id),
        ]);
        setStoreProducts(prods || []);
        setStorePayouts(payouts || []);
      } catch (err) {
        console.error('Error loading store details:', err);
        setStoreProducts([]);
        setStorePayouts([]);
      } finally {
        setLoadingStoreDetails(false);
      }
    })();

    // Background: questionnaire status — applies to ALL store types.
    // Failures must NOT block the dialog from rendering.
    setLoadingQuestionnaire(true);
    (async () => {
      try {
        const qs = await getWebstoreQuestionnaire(store.id);
        setQuestionnaireStatus(qs);
      } catch (err) {
        console.error('Could not load questionnaire status', err);
        setQuestionnaireStatus({ linked: false, questionnaire: null, latest_response: null });
      } finally {
        setLoadingQuestionnaire(false);
      }
    })();

    // Background: event-specific setup checklist — event stores only.
    if (store.store_type === 'event') {
      (async () => {
        try {
          const ck = await getWebstoreEventChecklist(store.id);
          setEventChecklist(ck);
        } catch (err) {
          console.error('Could not load event setup checklist', err);
        }
      })();
    }
  };

  const getStoreUrl = (storeId) => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/store/${storeId}`;
  };

  const handleCopyLink = (storeId) => {
    const url = getStoreUrl(storeId);
    navigator.clipboard.writeText(url);
    toast.success('Store link copied to clipboard!');
  };

  const handleOpenStore = (storeId) => {
    const url = getStoreUrl(storeId);
    window.open(url, '_blank');
  };

  const handleToggleProduct = async (productId, currentlyEnabled) => {
    if (!selectedStore) return;
    try {
      if (currentlyEnabled) {
        // Update to disabled
        await updateWebstoreProductStatus(selectedStore.id, productId, false);
      } else {
        // Check if product is already assigned but disabled
        const existing = storeProducts.find(sp => sp.id === productId);
        if (existing) {
          // Update to enabled
          await updateWebstoreProductStatus(selectedStore.id, productId, true);
        } else {
          // Assign new product
          await assignProductToWebstore(selectedStore.id, { 
            webstore_id: selectedStore.id,
            product_id: productId, 
            is_enabled: true 
          });
        }
      }
      // Reload all products with their status
      const prods = await getWebstoreProducts(selectedStore.id, true);
      setStoreProducts(prods);
      toast.success(currentlyEnabled ? 'Product disabled' : 'Product enabled');
    } catch (err) {
      toast.error('Failed to update product');
    }
  };

  // Handle product image selection (up to 3)
  const handleProductImageSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    const remaining = 3 - productImages.length;
    if (remaining <= 0) {
      toast.error('Maximum 3 images per product');
      return;
    }
    const validFiles = files.slice(0, remaining).filter(f => {
      if (!['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'].includes(f.type)) {
        toast.error(`${f.name}: Invalid image type`);
        return false;
      }
      if (f.size > 2 * 1024 * 1024) {
        toast.error(`${f.name}: Must be under 2MB`);
        return false;
      }
      return true;
    });
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setProductImages(prev => [...prev, ev.target.result]);
        setProductImagePreviews(prev => [...prev, ev.target.result]);
      };
      reader.readAsDataURL(file);
    });
    if (productImageRef.current) productImageRef.current.value = '';
  };

  const removeProductImage = (idx) => {
    setProductImages(prev => prev.filter((_, i) => i !== idx));
    setProductImagePreviews(prev => prev.filter((_, i) => i !== idx));
  };

  // Create product and auto-assign to current store
  const handleCreateProductForStore = async (e) => {
    e.preventDefault();
    if (!selectedStore) return;
    
    const baseCost = parseFloat(newProductData.base_cost);
    const retailPrice = parseFloat(newProductData.retail_price);
    
    if (!newProductData.name.trim()) {
      toast.error('Product name is required');
      return;
    }
    if (isNaN(baseCost) || isNaN(retailPrice) || baseCost <= 0 || retailPrice <= 0) {
      toast.error('Please enter valid prices');
      return;
    }
    
    setCreatingProduct(true);
    try {
      // Create the product with images
      const productionCost = parseFloat(newProductData.production_cost) || 0;
      const setupFee = parseFloat(newProductData.setup_fee) || 0;
      const newProduct = await createProduct({
        name: newProductData.name,
        description: newProductData.description,
        category: newProductData.category,
        base_cost: baseCost,
        retail_price: retailPrice,
        ...(productionCost > 0 && { production_cost: productionCost }),
        ...(setupFee > 0 && { setup_fee: setupFee }),
        images: productImages
      });
      
      // Assign it to the current store and enable it
      if (newProduct?.id) {
        await assignProductToWebstore(selectedStore.id, {
          webstore_id: selectedStore.id,
          product_id: newProduct.id,
          is_enabled: true
        });
      }
      
      // Reload products for the store and master catalog
      const [prods, allProducts] = await Promise.all([
        getWebstoreProducts(selectedStore.id, true),
        getProducts()
      ]);
      setStoreProducts(prods || []);
      setProducts(allProducts || []);
      
      // Reset form
      setNewProductData({
        name: '',
        description: '',
        category: 'other',
        base_cost: '',
        retail_price: '',
        production_cost: '',
        setup_fee: '',
      });
      setProductImages([]);
      setProductImagePreviews([]);
      setShowCreateProduct(false);
      toast.success('Product created and added to store!');
    } catch (err) {
      console.error('Error creating product:', err);
      toast.error('Failed to create product');
    } finally {
      setCreatingProduct(false);
    }
  };

  const handleDeleteStore = async (storeId) => {
    if (!confirm('Are you sure you want to delete this webstore?')) return;
    try {
      await deleteWebstore(storeId);
      toast.success('Webstore deleted');
      setIsDetailDialogOpen(false);
      await loadData();
    } catch (err) {
      toast.error('Failed to delete webstore');
    }
  };

  const handleCreateJobFromOrder = async (orderId) => {
    try {
      const result = await createJobFromOrder(orderId);
      toast.success('Order created from webstore order');
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create job');
    }
  };

  const handleUpdateBranding = async (field, value) => {
    if (!selectedStore) return;
    try {
      const updatedBranding = {
        ...selectedStore.branding,
        [field]: value
      };
      await updateWebstore(selectedStore.id, { branding: updatedBranding });
      setSelectedStore({ ...selectedStore, branding: updatedBranding });
      toast.success('Branding updated');
      await loadData();
    } catch (err) {
      toast.error('Failed to update branding');
    }
  };

  const handleSaveDescription = async (value) => {
    if (!selectedStore) return;
    try {
      await updateWebstore(selectedStore.id, { description: value });
      setSelectedStore({ ...selectedStore, description: value });
      toast.success('Description saved');
    } catch {
      toast.error('Failed to save description');
    }
  };

  const handleAIRewriteDescription = async () => {
    if (!selectedStore) return;
    setRewritingDesc(true);
    try {
      const products = (storeProducts || [])
        .slice(0, 6)
        .map(p => p.name)
        .join(', ') || 'custom merchandise';
      const result = await generateAIContent('store_description_rewrite', {
        store_name: selectedStore.name || '',
        store_type: selectedStore.store_type || '',
        owner_name: selectedStore.owner_name || selectedStore.owner_email || '',
        existing_description: descriptionDraft.trim() || 'none',
        products,
      });
      const text = (result?.output || result?.content || result || '').trim();
      if (text) {
        setDescriptionDraft(text);
        toast.success('Description rewritten — review and save when ready');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'AI rewrite failed — please try again');
    } finally {
      setRewritingDesc(false);
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    if (!selectedStore) return;
    try {
      await updateWebstore(selectedStore.id, { status: newStatus });
      setSelectedStore({ ...selectedStore, status: newStatus });
      toast.success(`Store ${newStatus === 'active' ? 'activated' : 'disabled'}`);
      await loadData();
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleUpdatePublic = async (isPublic) => {
    if (!selectedStore) return;
    try {
      await updateWebstore(selectedStore.id, { is_public: isPublic });
      setSelectedStore({ ...selectedStore, is_public: isPublic });
      toast.success(`Store is now ${isPublic ? 'public' : 'private'}`);
      await loadData();
    } catch (err) {
      toast.error('Failed to update visibility');
    }
  };

  const handleSaveEventSettings = async () => {
    if (!selectedStore) return;
    setSavingEvent(true);
    // Sanitize empty strings for optional date/string fields
    const cleaned = Object.fromEntries(
      Object.entries(eventEdits).map(([k, v]) => [k, v === '' ? null : v])
    );
    try {
      await updateWebstore(selectedStore.id, cleaned);
      setSelectedStore({ ...selectedStore, ...cleaned });
      toast.success('Event settings saved');
      await loadData();
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      toast.error(typeof rawDetail === 'string' ? rawDetail
        : Array.isArray(rawDetail) ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
        : 'Failed to save event settings');
    } finally {
      setSavingEvent(false);
    }
  };

  const handleSaveFundraiserSettings = async () => {
    if (!selectedStore) return;
    setSavingFundraiser(true);
    // Sanitize: convert empty strings to null for numeric fields
    const cleaned = Object.fromEntries(
      Object.entries(fundraiserEdits).map(([k, v]) => {
        if (v === '') return [k, null];
        return [k, v];
      })
    );
    try {
      await updateWebstore(selectedStore.id, cleaned);
      setSelectedStore({ ...selectedStore, ...cleaned });
      toast.success('Fundraiser settings saved');
      await loadData();
    } catch (err) {
      toast.error('Failed to save fundraiser settings');
    } finally {
      setSavingFundraiser(false);
    }
  };

  const handleSaveLockedSettings = async () => {
    if (!selectedStore) return;
    setSavingLocked(true);
    // Strip legacy read-only fields and convert empty strings to null
    const cleaned = Object.fromEntries(
      Object.entries(lockedEdits)
        .filter(([k]) => !k.startsWith('_legacy_'))
        .map(([k, v]) => [k, v === '' ? null : v])
    );
    try {
      await updateWebstore(selectedStore.id, { locked_settings: cleaned });
      setSelectedStore({ ...selectedStore, locked_settings: cleaned });
      toast.success('Shipping settings saved');
      await loadData();
    } catch (err) {
      toast.error('Failed to save shipping settings');
    } finally {
      setSavingLocked(false);
    }
  };

  const handleSendQuestionnaire = async () => {
    if (!selectedStore) return;
    setSendingQuestionnaire(true);
    try {
      const origin = window.location.origin;
      const result = await sendWebstoreQuestionnaire(selectedStore.id, {
        email: sendEmailOverride || undefined,
        message: sendMessageOverride || undefined,
        public_url: origin,
      });
      if (result.email_sent) {
        toast.success(`Questionnaire sent to ${result.email}`);
      } else {
        toast.warning(`Questionnaire created but email failed. Share this link manually:\n${result.link}`);
      }
      setShowSendDialog(false);
      setSendEmailOverride('');
      setSendMessageOverride('');
      // Refresh questionnaire status
      const qs = await getWebstoreQuestionnaire(selectedStore.id);
      setQuestionnaireStatus(qs);
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      toast.error(typeof rawDetail === 'string' ? rawDetail
        : Array.isArray(rawDetail) ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
        : 'Failed to send questionnaire');
    } finally {
      setSendingQuestionnaire(false);
    }
  };

  const handleApplyQuestionnaireAnswers = async () => {
    if (!selectedStore) return;
    setApplyingAnswers(true);
    try {
      const result = await applyWebstoreQuestionnaireAnswers(selectedStore.id);
      const count = Object.keys(result.applied_fields || {}).length;
      const suggested = (result.suggested_changes || []).length;
      toast.success(
        `Applied ${count} field${count !== 1 ? 's' : ''} to the store.`
        + (suggested ? ` ${suggested} field(s) require admin review.` : '')
      );
      // Refresh store data
      await loadData();
      const qs = await getWebstoreQuestionnaire(selectedStore.id);
      setQuestionnaireStatus(qs);
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      toast.error(typeof rawDetail === 'string' ? rawDetail
        : Array.isArray(rawDetail) ? rawDetail.map((e) => e.msg || JSON.stringify(e)).join('; ')
        : 'Failed to apply answers');
    } finally {
      setApplyingAnswers(false);
    }
  };

  const handleStampAdminProgress = async (flagKey) => {
    if (!selectedStore) return;
    try {
      const result = await stampWebstoreAdminProgress(selectedStore.id, flagKey);
      // Merge stamp timestamps back into selectedStore so the setup flow updates
      setSelectedStore((s) => ({ ...s, ...result }));
      toast.success('Progress updated.');
    } catch (err) {
      const rawDetail = err?.response?.data?.detail;
      toast.error(typeof rawDetail === 'string' ? rawDetail : 'Could not update progress');
    }
  };

  const handleLoadDetailOrders = async () => {
    if (!selectedStore) return;
    setLoadingDetailOrders(true);
    try {
      const ordr = await getWebstoreOrdersV2({ webstore_id: selectedStore.id });
      setStoreDetailOrders(ordr || []);
    } catch {
      setStoreDetailOrders([]);
    } finally {
      setLoadingDetailOrders(false);
    }
  };

  const handleRecordDetailPayout = async () => {
    if (!selectedStore || !detailPayoutAmount) return;
    setSubmittingDetailPayout(true);
    try {
      await recordPayout(selectedStore.id, parseFloat(detailPayoutAmount), detailPayoutNotes);
      toast.success('Payout recorded.');
      setDetailPayoutAmount('');
      setDetailPayoutNotes('');
      const updated = await getWebstorePayouts(selectedStore.id);
      setStorePayouts(updated || []);
    } catch (err) {
      toast.error('Failed to record payout');
    } finally {
      setSubmittingDetailPayout(false);
    }
  };

  const filteredStores = (selectedType === 'all' 
    ? webstores 
    : webstores.filter(s => s.store_type === selectedType)
  ).filter(s => {
    if (!storeSearch.trim()) return true;
    const q = storeSearch.toLowerCase();
    return (
      (s.name || '').toLowerCase().includes(q) ||
      (s.description || '').toLowerCase().includes(q) ||
      (s.store_type || '').toLowerCase().includes(q)
    );
  });

  // Calculate stats
  const totalSales = webstores.reduce((sum, s) => sum + (s.total_sales || 0), 0);
  const totalProfit = webstores.reduce((sum, s) => sum + (s.total_profit || 0), 0);
  const totalOwed = webstores.reduce((sum, s) => sum + (s.payout_owed || 0), 0);
  const pendingOrders = orders.filter(o => o.status === 'pending').length;

  // Show Stripe Connect required message if not connected
  if (stripeConnected === false) {
    return (
      <PageStack gap="24px" data-testid="webstores-page">
        <ShellCard padding="lg">
          <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-full p-6 mb-6">
              <CreditCard className="h-16 w-16 text-amber-500" />
            </div>
            <h1 className="text-3xl font-bold font-heading mb-3 text-gray-900">Connect Stripe to Use Webstores</h1>
            <p className="text-gray-500 max-w-md mb-6">
              Webstores require Stripe payment processing to accept customer orders. 
              Connect your Stripe account to start selling online.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                size="lg" 
                className="bg-blue-600 hover:bg-blue-700"
                onClick={handleConnectStripe}
                disabled={connectingStripe}
              >
                {connectingStripe ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <CreditCard className="h-5 w-5 mr-2" />
                    Connect Stripe Account
                  </>
                )}
              </Button>
            </div>
            <div className="mt-8 p-4 bg-gray-50 rounded-lg max-w-md border border-gray-200">
              <h3 className="font-semibold mb-2 flex items-center gap-2 text-gray-900">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Why is Stripe required?
              </h3>
              <ul className="text-sm text-gray-500 space-y-1 text-left">
                <li>• Accept credit card payments from customers</li>
                <li>• Automatic order processing and confirmation</li>
                <li>• Orders automatically added to your Orders list</li>
                <li>• Secure, PCI-compliant payment handling</li>
              </ul>
            </div>
          </div>
        </ShellCard>
      </PageStack>
    );
  }

  // Show loading while checking Stripe status
  if (stripeConnected === null) {
    return (
      <PageStack gap="24px">
        <ShellCard>
          <div className="flex items-center justify-center min-h-[50vh]">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        </ShellCard>
      </PageStack>
    );
  }

  return (
    <PageStack gap="24px" data-testid="webstores-page">
      {/* Header Card */}
      <ShellCard padding="default">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold font-heading uppercase tracking-tight text-gray-900">Webstore Manager</h1>
            <p className="text-gray-500 text-sm mt-1">Manage all your webstores from one place</p>
          </div>
          {/* Phase 2 — the "Create Webstore" CTA now lives in the Webstores
              ribbon (Create / Setup group). Removed from the page header to
              eliminate the duplicate command surface. */}
        </div>
      </ShellCard>

      {/* Create Dialog — simplified 3-step wizard (type → basics → owner) then questionnaire */}
      <Dialog open={isCreateDialogOpen} onOpenChange={(open) => { if (!open) handleCloseCreateDialog(); }}>
        <DialogContent className="sm:max-w-[720px] max-h-[90vh] overflow-y-auto overflow-x-hidden" data-testid="create-webstore-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Create New Webstore</DialogTitle>
            <DialogDescription className="text-xs text-gray-500">
              {createdStore
                ? 'Store created — send the setup questionnaire to the owner.'
                : 'Select a store type, name your store, and provide the owner contact. Dates, fulfillment, and payments are collected via questionnaire after creation.'}
            </DialogDescription>
          </DialogHeader>
          <StoreSetupWizard
            storeTypes={storeTypes}
            formData={formData}
            setFormData={setFormData}
            creatingStore={creatingStore}
            onSubmit={() => handleCreateStore()}
            onCancel={handleCloseCreateDialog}
            createdStore={createdStore}
            onSendQuestionnaire={handleSendQuestionnaireAfterCreate}
          />
        </DialogContent>
      </Dialog>


      {/* Stats Cards - Individual small cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <ShellCard padding="default">
          <div className="flex items-center gap-3">
            <Store className="h-8 w-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-500">Total Stores</p>
              <p className="text-2xl font-bold text-gray-900">{webstores.length}</p>
            </div>
          </div>
        </ShellCard>
        <ShellCard padding="default">
          <div className="flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div>
              <p className="text-sm text-gray-500">Total Sales</p>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(totalSales)}</p>
            </div>
          </div>
        </ShellCard>
        <ShellCard padding="default">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <div>
              <p className="text-sm text-gray-500">Total Profit</p>
              <p className="text-2xl font-bold text-blue-600">{formatCurrency(totalProfit)}</p>
            </div>
          </div>
        </ShellCard>
        <ShellCard padding="default">
          <div className="flex items-center gap-3">
            <ShoppingCart className="h-8 w-8 text-amber-600" />
            <div>
              <p className="text-sm text-gray-500">Pending Orders</p>
              <p className="text-2xl font-bold text-amber-600">{pendingOrders}</p>
            </div>
          </div>
        </ShellCard>
      </div>

      {/* Main Tabs Card */}
      <ShellCard padding="none">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          {/* Phase 2 — In-page Tabs strip removed. The Webstores ribbon
              (Manage Stores / Orders groups) drives this same activeTab state
              via the `?tab=` query param, so the duplicate command surface is
              gone. Counts now appear in the section sub-header below. */}
          <div className="px-6 pt-5 pb-3 border-b border-gray-100 flex items-center justify-between gap-4 flex-wrap" data-testid="webstores-section-header">
            <div className="flex items-center gap-2 text-sm">
              {activeTab === 'stores' ? (
                <>
                  <Store className="h-4 w-4 text-blue-600" />
                  <span className="font-semibold text-gray-900" data-testid="webstores-section-title">
                    All Stores
                  </span>
                  <span className="text-gray-500" data-testid="webstores-section-count">
                    ({webstores.length})
                  </span>
                </>
              ) : (
                <>
                  <ShoppingCart className="h-4 w-4 text-amber-600" />
                  <span className="font-semibold text-gray-900" data-testid="webstores-section-title">
                    Webstore Orders
                  </span>
                  <span className="text-gray-500" data-testid="webstores-section-count">
                    ({orders.length})
                  </span>
                </>
              )}
            </div>
            {/* Hidden TabsList preserved off-screen so legacy automation that
                queries data-testid='tab-stores' / 'tab-orders' still resolves
                and remains keyboard-accessible. */}
            <TabsList className="sr-only" aria-label="Webstores section">
              <TabsTrigger value="stores" data-testid="tab-stores">All Stores</TabsTrigger>
              <TabsTrigger value="orders" data-testid="tab-orders">Orders</TabsTrigger>
            </TabsList>
          </div>

        {/* Stores Tab */}
        <TabsContent value="stores" className="space-y-0">
          {/* Type Filter + Search */}
          <div className="px-6 py-4 flex gap-2 border-b border-gray-100 flex-wrap items-center">
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                value={storeSearch}
                onChange={(e) => setStoreSearch(e.target.value)}
                placeholder="Search stores..."
                className="pl-9 h-9"
                data-testid="webstores-search-input"
              />
            </div>
            <Button
              variant={selectedType === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedType('all')}
            >
              All
            </Button>
            {storeTypes.map(type => {
              const Icon = type.icon;
              const count = webstores.filter(s => s.store_type === type.value).length;
              return (
                <Button
                  key={type.value}
                  variant={selectedType === type.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedType(type.value)}
                >
                  <Icon className="h-4 w-4 mr-1" /> {type.label} ({count})
                </Button>
              );
            })}
          </div>

          <div>
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            ) : filteredStores.length === 0 ? (
              <div className="text-center py-12 text-gray-500" data-testid="webstores-empty-state">
                <Store className="h-12 w-12 mx-auto mb-4 opacity-50" />
                {webstores.length === 0 ? (
                  <>
                    <p>No webstores yet</p>
                    <p className="text-sm mt-1">Create your first webstore to get started</p>
                  </>
                ) : (
                  <>
                    <p>No stores match this filter</p>
                    <p className="text-sm mt-1">
                      You have {webstores.length} store{webstores.length === 1 ? '' : 's'} —{' '}
                      <button
                        type="button"
                        className="underline text-blue-600 hover:text-blue-800"
                        onClick={() => { setSelectedType('all'); setStoreSearch(''); }}
                        data-testid="webstores-clear-filter"
                      >
                        clear filters
                      </button>
                      {' '}to see them all.
                    </p>
                  </>
                )}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Store</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Owner</TableHead>
                    <TableHead className="text-right">Sales</TableHead>
                    <TableHead className="text-right">Profit</TableHead>
                    <TableHead className="text-right">Owed</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredStores.map((store, idx) => {
                    const Icon = getStoreTypeIcon(store.store_type);
                    return (
                      <TableRow 
                        key={store.id} 
                        className={idx % 2 === 0 ? '' : 'bg-gray-50'}
                        data-testid={`store-row-${store.id}`}
                      >
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                              <Icon className="h-5 w-5 text-gray-600" />
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{store.name}</p>
                              <p className="text-xs text-gray-500">
                                {store.total_orders || 0} orders
                              </p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStoreTypeColor(store.store_type)}>
                            {store.store_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-700">{store.owner_name}</TableCell>
                        <TableCell className="text-right font-medium text-gray-900">
                          {formatCurrency(store.total_sales || 0)}
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          {formatCurrency(store.total_profit || 0)}
                        </TableCell>
                        <TableCell className="text-right text-amber-600">
                          {formatCurrency(store.payout_owed || 0)}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(store.status)}>
                            {store.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleCopyLink(store.id)}
                                title="Copy store link"
                                data-testid={`copy-link-${store.id}`}
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleOpenStore(store.id)}
                                title="Open storefront"
                                data-testid={`open-store-${store.id}`}
                              >
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleViewStore(store)}
                                title="Manage store"
                                data-testid={`view-store-${store.id}`}
                              >
                                <Settings className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDeleteStore(store.id)}
                                title="Delete store"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </div>
          </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders" className="space-y-0">
          <div>
            {orders.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <ShoppingCart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No orders yet</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                      <TableHead>Order #</TableHead>
                      <TableHead>Store</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Profit</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Order</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order, idx) => (
                      <TableRow key={order.id} className={idx % 2 === 0 ? '' : 'bg-gray-50'}>
                        <TableCell className="font-mono text-sm">#{order.id.slice(0, 8)}</TableCell>
                        <TableCell>
                          <Badge className={getStoreTypeColor(order.store_type)}>
                            {order.webstore_name || order.store_type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium text-gray-900">{order.customer_name}</p>
                            <p className="text-xs text-gray-500">{order.customer_email}</p>
                          </div>
                        </TableCell>
                        <TableCell>{order.items?.length || 0} items</TableCell>
                        <TableCell className="text-right font-bold text-gray-900">{formatCurrency(order.total)}</TableCell>
                        <TableCell className="text-right text-green-600">
                          {formatCurrency(order.total_profit || 0)}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(order.status)}>
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {order.job_id ? (
                            <Badge variant="outline">#{order.job_id.slice(0, 8)}</Badge>
                          ) : (
                            <span className="text-gray-500">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {!order.job_id && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCreateJobFromOrder(order.id)}
                            >
                              Create Order
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </ShellCard>

      {/* Store Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={(open) => {
        setIsDetailDialogOpen(open);
        if (!open) {
          // Reset store products when closing to prevent state leakage
          setStoreProducts([]);
          setLoadingStoreDetails(false);
          // Reset questionnaire overlay so it never persists to next opened store
          setShowSendDialog(false);
          setSendEmailOverride('');
          setSendMessageOverride('');
        }
      }}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto overflow-x-hidden" data-testid="store-detail-dialog">
          {selectedStore && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3 pr-8">
                  {(() => {
                    const Icon = getStoreTypeIcon(selectedStore.store_type);
                    return <Icon className="h-6 w-6 shrink-0" />;
                  })()}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <DialogTitle className="font-heading uppercase truncate">{selectedStore.name}</DialogTitle>
                      <Badge className={`${getStoreTypeColor(selectedStore.store_type)} shrink-0`}>
                        {selectedStore.store_type}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{selectedStore.owner_name}</p>
                  </div>
                </div>
              </DialogHeader>

              <Tabs value={detailTab} onValueChange={(t) => {
                setDetailTab(t);
                if (t === 'orders' && storeDetailOrders.length === 0) handleLoadDetailOrders();
              }}>
                {/* Tab bar — 6 tabs, no horizontal scroll */}
                <TabsList className="flex w-full bg-muted rounded-lg p-1 gap-0 h-auto flex-wrap">
                  <TabsTrigger value="setup" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-setup">
                    Store Setup
                  </TabsTrigger>
                  <TabsTrigger value="products" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-products">
                    Products
                  </TabsTrigger>
                  <TabsTrigger value="branding" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-branding">
                    Branding
                  </TabsTrigger>
                  <TabsTrigger value="payments" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-payments">
                    Payments
                  </TabsTrigger>
                  <TabsTrigger value="orders" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-orders">
                    Orders
                  </TabsTrigger>
                  <TabsTrigger value="analytics" className="shrink-0 flex-1 min-w-[72px] text-xs sm:text-sm" data-testid="tab-analytics">
                    Analytics
                  </TabsTrigger>
                </TabsList>

                {/* ── Store Setup tab ─────────────────────────────────────── */}
                <TabsContent value="setup" className="mt-4" data-testid="tab-content-setup">
                  <WebstoreSetupFlow
                    store={selectedStore}
                    questionnaireStatus={questionnaireStatus}
                    loadingQuestionnaire={loadingQuestionnaire}
                    storeProducts={storeProducts}
                    applyingAnswers={applyingAnswers}
                    onApplyAnswers={handleApplyQuestionnaireAnswers}
                    onSendQuestionnaire={handleSendQuestionnaireAfterCreate}
                    onShowTab={setDetailTab}
                    onUpdateStore={async (payload) => {
                      await updateWebstore(selectedStore.id, payload);
                      setSelectedStore((s) => ({ ...s, ...payload }));
                    }}
                    onActivateStore={async () => {
                      try {
                        const updated = await updateWebstore(selectedStore.id, { status: 'active' });
                        setSelectedStore((s) => ({ ...s, status: 'active', ...updated }));
                        toast.success('Store is now live!');
                      } catch (err) {
                        const detail = err?.response?.data?.detail;
                        toast.error(typeof detail === 'string' ? detail : 'Could not activate store');
                      }
                    }}
                    onStampProgress={handleStampAdminProgress}
                  />

                  {/* Store Access — always visible below the setup flow */}
                  <Card className="mt-4">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        Store Access
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label className="text-sm">Store Active</Label>
                          <p className="text-xs text-muted-foreground">Enable or disable this storefront</p>
                        </div>
                        <Switch
                          checked={selectedStore.status === 'active'}
                          onCheckedChange={(checked) => handleUpdateStatus(checked ? 'active' : 'disabled')}
                          data-testid="store-active-switch"
                        />
                      </div>
                      <Separator />
                      <div className="flex items-center justify-between">
                        <div>
                          <Label className="text-sm">Public Access</Label>
                          <p className="text-xs text-muted-foreground">Allow anyone to view and order</p>
                        </div>
                        <Switch
                          checked={selectedStore.is_public}
                          onCheckedChange={(checked) => handleUpdatePublic(checked)}
                          data-testid="store-public-switch"
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Event Settings — event stores only */}
                  {selectedStore.store_type === 'event' && (
                    <Card className="mt-4">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <CalendarDays className="h-4 w-4 text-orange-400" />
                          Event Settings
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-1 col-span-2">
                            <Label className="text-xs">Event Name</Label>
                            <Input
                              value={eventEdits.event_name || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, event_name: e.target.value })}
                              placeholder="e.g., Johnson Benefit Dinner 2026"
                              data-testid="edit-event-name-input"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Event Date</Label>
                            <Input type="date"
                              value={eventEdits.event_start_date || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, event_start_date: e.target.value })}
                              data-testid="edit-event-date-input"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Event Location</Label>
                            <Input
                              value={eventEdits.event_location || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, event_location: e.target.value })}
                              placeholder="Venue or city"
                              data-testid="edit-event-location-input"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Store Opens</Label>
                            <Input type="date"
                              value={eventEdits.store_open_date || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, store_open_date: e.target.value })}
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Order Deadline</Label>
                            <Input type="date"
                              value={eventEdits.order_deadline || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, order_deadline: e.target.value })}
                            />
                          </div>
                          <div className="space-y-1 col-span-2">
                            <Label className="text-xs">Pickup / Delivery Instructions</Label>
                            <Textarea
                              value={eventEdits.pickup_delivery_instructions || ''}
                              onChange={(e) => setEventEdits({ ...eventEdits, pickup_delivery_instructions: e.target.value })}
                              placeholder="e.g., Pick up at check-in table the night of the event"
                              rows={2}
                              data-testid="edit-pickup-instructions"
                            />
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <Button size="sm" onClick={handleSaveEventSettings} disabled={savingEvent} data-testid="save-event-settings-btn">
                            {savingEvent ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                            Save Event Settings
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Fundraiser Settings */}
                  {(selectedStore.fundraiser_enabled || fundraiserEdits.fundraiser_enabled) && (
                    <Card className="mt-4">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Fundraiser Settings</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-1 col-span-2">
                            <Label className="text-xs">Fundraiser Name</Label>
                            <Input
                              value={fundraiserEdits.fundraiser_name || ''}
                              onChange={(e) => setFundraiserEdits({ ...fundraiserEdits, fundraiser_name: e.target.value })}
                              placeholder="Fundraiser name"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Goal Amount ($)</Label>
                            <Input type="number" min="0" step="0.01"
                              value={fundraiserEdits.fundraiser_goal_amount ?? ''}
                              onChange={(e) => setFundraiserEdits({ ...fundraiserEdits, fundraiser_goal_amount: e.target.value })}
                            />
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <Button size="sm" onClick={handleSaveFundraiserSettings} disabled={savingFundraiser} data-testid="save-fundraiser-settings-btn">
                            {savingFundraiser ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                            Save Fundraiser Settings
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Shipping & Handling Fee */}
                  <Card className="mt-4">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        Shipping &amp; Handling Fee
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm">Shipping &amp; Handling Bundle</Label>
                        <Switch
                          checked={lockedEdits.shipping_handling_enabled || false}
                          onCheckedChange={(checked) => setLockedEdits({ ...lockedEdits, shipping_handling_enabled: checked })}
                          data-testid="edit-sh-enabled-switch"
                        />
                      </div>
                      {lockedEdits.shipping_handling_enabled && (
                        <div className="grid grid-cols-2 gap-3">
                          <div className="space-y-1">
                            <Label className="text-xs">Bundle Fee ($)</Label>
                            <Input type="number" min="0" step="0.01"
                              value={lockedEdits.shipping_handling_fee ?? ''}
                              onChange={(e) => setLockedEdits({ ...lockedEdits, shipping_handling_fee: e.target.value })}
                              className="h-8 text-sm"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Label</Label>
                            <Input
                              value={lockedEdits.shipping_handling_label || ''}
                              onChange={(e) => setLockedEdits({ ...lockedEdits, shipping_handling_label: e.target.value })}
                              placeholder="Shipping & Handling"
                              className="h-8 text-sm"
                            />
                          </div>
                        </div>
                      )}
                      <div className="flex justify-end">
                        <Button size="sm" onClick={handleSaveLockedSettings} disabled={savingLocked} data-testid="save-locked-settings-btn">
                          {savingLocked ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                          Save Shipping Settings
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                </TabsContent>

                <TabsContent value="products" className="space-y-4">
                  {/* Header with Create Button */}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Enable products from your catalog for this store
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowCreateProduct(!showCreateProduct)}
                      data-testid="create-product-btn"
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      {showCreateProduct ? 'Cancel' : 'Create Product'}
                    </Button>
                  </div>

                  {/* Create Product Form */}
                  {showCreateProduct && (
                    <Card className="border-primary/30 bg-primary/5">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                          <Plus className="h-4 w-4" />
                          Create New Product
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleCreateProductForStore} className="space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2 space-y-1">
                              <Label className="text-xs">Product Name *</Label>
                              <Input
                                value={newProductData.name}
                                onChange={(e) => setNewProductData({ ...newProductData, name: e.target.value })}
                                placeholder="e.g., Custom T-Shirt"
                                className="h-9"
                                data-testid="new-product-name"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Category</Label>
                              <Select
                                value={newProductData.category}
                                onValueChange={(val) => setNewProductData({ ...newProductData, category: val })}
                              >
                                <SelectTrigger className="h-9" data-testid="new-product-category">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {categoryOptions.map(cat => (
                                    <SelectItem key={cat.value} value={cat.value}>
                                      {cat.label}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Description</Label>
                              <Input
                                value={newProductData.description}
                                onChange={(e) => setNewProductData({ ...newProductData, description: e.target.value })}
                                placeholder="Optional"
                                className="h-9"
                                data-testid="new-product-description"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Base Cost *</Label>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                value={newProductData.base_cost}
                                onChange={(e) => setNewProductData({ ...newProductData, base_cost: e.target.value })}
                                placeholder="0.00"
                                className="h-9"
                                data-testid="new-product-cost"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Retail Price *</Label>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                value={newProductData.retail_price}
                                onChange={(e) => setNewProductData({ ...newProductData, retail_price: e.target.value })}
                                placeholder="0.00"
                                className="h-9"
                                data-testid="new-product-price"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Production Cost</Label>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                value={newProductData.production_cost}
                                onChange={(e) => setNewProductData({ ...newProductData, production_cost: e.target.value })}
                                placeholder="0.00"
                                className="h-9"
                                data-testid="new-product-production-cost"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-xs">Setup Fee</Label>
                              <Input
                                type="number"
                                step="0.01"
                                min="0"
                                value={newProductData.setup_fee}
                                onChange={(e) => setNewProductData({ ...newProductData, setup_fee: e.target.value })}
                                placeholder="0.00"
                                className="h-9"
                                data-testid="new-product-setup-fee"
                              />
                            </div>
                            {/* Product Images (up to 3) */}
                            <div className="col-span-2 space-y-2">
                              <Label className="text-xs">Product Images (up to 3)</Label>
                              <div className="flex items-center gap-2 flex-wrap">
                                {productImagePreviews.map((img, idx) => (
                                  <div key={idx} className="relative group w-16 h-16 rounded border overflow-hidden">
                                    <img src={img} alt={`Product ${idx + 1}`} className="w-full h-full object-cover" />
                                    <button
                                      type="button"
                                      onClick={() => removeProductImage(idx)}
                                      className="absolute top-0 right-0 bg-red-500 text-white rounded-bl p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                                      data-testid={`remove-product-image-${idx}`}
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </div>
                                ))}
                                {productImages.length < 3 && (
                                  <button
                                    type="button"
                                    onClick={() => productImageRef.current?.click()}
                                    className="w-16 h-16 rounded border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-gray-400 hover:border-primary hover:text-primary transition-colors"
                                    data-testid="add-product-image-btn"
                                  >
                                    <ImageIcon className="h-5 w-5" />
                                    <span className="text-[10px]">Add</span>
                                  </button>
                                )}
                                <input
                                  ref={productImageRef}
                                  type="file"
                                  accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                                  multiple
                                  onChange={handleProductImageSelect}
                                  className="hidden"
                                  data-testid="product-image-input"
                                />
                              </div>
                            </div>
                          </div>
                          <div className="flex justify-end gap-2 pt-2">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setShowCreateProduct(false);
                                setNewProductData({
                                  name: '',
                                  description: '',
                                  category: 'other',
                                  base_cost: '',
                                  retail_price: ''
                                });
                                setProductImages([]);
                                setProductImagePreviews([]);
                              }}
                            >
                              Cancel
                            </Button>
                            <Button
                              type="submit"
                              size="sm"
                              disabled={creatingProduct}
                              data-testid="save-new-product-btn"
                            >
                              {creatingProduct ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                  Creating...
                                </>
                              ) : (
                                <>
                                  <Check className="h-4 w-4 mr-1" />
                                  Create & Add to Store
                                </>
                              )}
                            </Button>
                          </div>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  {/* Existing Products List */}
                  {loadingStoreDetails ? (
                    <div className="flex items-center justify-center h-32">
                      <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                  ) : products.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Package className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>No products in catalog yet</p>
                      <p className="text-sm mt-1">Click "Create Product" above to add your first product</p>
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-[300px] overflow-y-auto">
                      {products.map(product => {
                        const assigned = storeProducts.find(sp => sp.id === product.id);
                        const isEnabled = assigned?.is_enabled ?? false;
                        return (
                          <div 
                            key={`${selectedStore?.id}-${product.id}`}
                            className={`flex items-center justify-between p-3 rounded-lg border ${
                              isEnabled ? 'border-primary/30 bg-primary/5' : 'border-border'
                            }`}
                            data-testid={`product-toggle-${product.id}`}
                          >
                            <div className="flex items-center gap-3">
                              {product.images?.length > 0 || product.image_url ? (
                                <img 
                                  src={product.images?.[0] || product.image_url} 
                                  alt={product.name}
                                  className="h-10 w-10 rounded object-cover border"
                                />
                              ) : (
                                <Package className="h-5 w-5 text-muted-foreground" />
                              )}
                              <div>
                                <p className="font-medium">{product.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {formatCurrency(product.retail_price)} • {product.category}
                                </p>
                              </div>
                            </div>
                            <Switch
                              checked={isEnabled}
                              onCheckedChange={() => handleToggleProduct(product.id, isEnabled)}
                              data-testid={`product-switch-${product.id}`}
                            />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="branding" className="space-y-6" data-testid="tab-content-branding">
                  {/* ── Store Description ── */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Edit2 className="h-4 w-4" />
                        Store Description
                      </CardTitle>
                      <p className="text-xs text-muted-foreground">
                        Appears on your public storefront. Keep it concise and welcoming.
                      </p>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="relative">
                        <Textarea
                          value={descriptionDraft}
                          onChange={(e) => setDescriptionDraft(e.target.value)}
                          onBlur={(e) => {
                            const val = e.target.value.trim();
                            if (val !== (selectedStore.description || '').trim()) {
                              handleSaveDescription(val);
                            }
                          }}
                          placeholder="Describe your store — who it's for, what you offer, and why customers will love it..."
                          rows={4}
                          className="resize-none pr-3 text-sm"
                          data-testid="store-description-textarea"
                        />
                        <p className="text-[10px] text-muted-foreground text-right mt-1">
                          {descriptionDraft.length} chars · auto-saves on blur
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={handleAIRewriteDescription}
                          disabled={rewritingDesc}
                          className="gap-1.5 border-violet-300 text-violet-700 hover:bg-violet-50 dark:border-violet-700 dark:text-violet-300 dark:hover:bg-violet-950"
                          data-testid="ai-rewrite-description-btn"
                        >
                          {rewritingDesc
                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            : <Wand2 className="h-3.5 w-3.5" />}
                          {rewritingDesc ? 'Rewriting…' : 'AI Rewrite'}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => handleSaveDescription(descriptionDraft.trim())}
                          disabled={descriptionDraft.trim() === (selectedStore.description || '').trim()}
                          data-testid="save-description-btn"
                        >
                          Save
                        </Button>
                        {descriptionDraft.trim() !== (selectedStore.description || '').trim() && (
                          <span className="text-xs text-amber-600">Unsaved changes</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  <Separator />

                  {/* Branding Section */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Palette className="h-4 w-4" />
                        Store Branding
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      {/* Logo Upload */}
                      <div className="space-y-3">
                        <Label className="text-sm font-medium">Company Logo</Label>
                        
                        {(logoPreview || selectedStore.branding?.logo_url) && (
                          <div className="flex items-center gap-4 p-3 rounded-lg border border-border bg-muted/30">
                            <img 
                              src={logoPreview || selectedStore.branding?.logo_url} 
                              alt="Logo preview" 
                              className="h-14 w-auto object-contain rounded"
                            />
                            <div className="flex-1">
                              <p className="text-sm font-medium">
                                {logoFile ? 'New Logo' : 'Current Logo'}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {logoFile ? logoFile.name : 'Uploaded logo'}
                              </p>
                            </div>
                            {logoPreview && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setLogoPreview(null);
                                  setLogoFile(null);
                                }}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        )}
                        
                        <div className="flex gap-2">
                          <input
                            type="file"
                            accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                            onChange={handleLogoSelect}
                            className="hidden"
                            id="edit-logo-file-input"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => document.getElementById('edit-logo-file-input')?.click()}
                            disabled={uploadingLogo}
                            data-testid="upload-logo-btn"
                          >
                            <Upload className="h-4 w-4 mr-2" />
                            {logoPreview ? 'Change' : 'Upload'}
                          </Button>
                          {logoFile && (
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => handleUploadLogo()}
                              disabled={uploadingLogo}
                              data-testid="save-logo-btn"
                            >
                              {uploadingLogo ? 'Saving...' : 'Save Logo'}
                            </Button>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-px bg-border" />
                          <span className="text-xs text-muted-foreground">or URL</span>
                          <div className="flex-1 h-px bg-border" />
                        </div>
                        
                        <Input
                          value={selectedStore.branding?.logo_url || ''}
                          onChange={(e) => handleUpdateBranding('logo_url', e.target.value)}
                          placeholder="https://example.com/logo.png"
                          className="text-sm"
                          data-testid="edit-logo-url-input"
                        />
                      </div>

                      <Separator />

                      {/* Banner Upload */}
                      <div className="space-y-3">
                        <div>
                          <Label className="text-sm font-medium">Store Banner</Label>
                          <p className="text-xs text-muted-foreground mt-1">
                            Recommended size: 1200x300px
                          </p>
                        </div>
                        
                        {(bannerPreview || selectedStore.branding?.banner_url) && (
                          <div className="relative rounded-lg border border-border overflow-hidden">
                            <img 
                              src={bannerPreview || selectedStore.branding?.banner_url} 
                              alt="Banner preview" 
                              className="w-full h-28 object-cover"
                            />
                            {bannerPreview && (
                              <Button
                                type="button"
                                variant="secondary"
                                size="sm"
                                className="absolute top-2 right-2"
                                onClick={() => {
                                  setBannerPreview(null);
                                  setBannerFile(null);
                                }}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        )}
                        
                        <div className="flex gap-2">
                          <input
                            type="file"
                            accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                            onChange={handleBannerSelect}
                            className="hidden"
                            id="edit-banner-file-input"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => document.getElementById('edit-banner-file-input')?.click()}
                            disabled={uploadingBanner}
                            data-testid="upload-banner-btn"
                          >
                            <Upload className="h-4 w-4 mr-2" />
                            {bannerPreview ? 'Change' : 'Upload'}
                          </Button>
                          {bannerFile && (
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => handleUploadBanner()}
                              disabled={uploadingBanner}
                              data-testid="save-banner-btn"
                            >
                              {uploadingBanner ? 'Saving...' : 'Save Banner'}
                            </Button>
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-px bg-border" />
                          <span className="text-xs text-muted-foreground">or URL</span>
                          <div className="flex-1 h-px bg-border" />
                        </div>
                        
                        <Input
                          value={selectedStore.branding?.banner_url || ''}
                          onChange={(e) => handleUpdateBranding('banner_url', e.target.value)}
                          placeholder="https://example.com/banner.jpg"
                          className="text-sm"
                          data-testid="edit-banner-url-input"
                        />
                      </div>

                      <Separator />

                      {/* Accent Color */}
                      <div className="space-y-3">
                        <Label className="text-sm font-medium">Accent Color</Label>
                        <div className="flex gap-3 items-center">
                          <div className="relative w-12 h-10 rounded border border-border overflow-hidden cursor-pointer">
                            <input
                              type="color"
                              value={selectedStore.branding?.primary_color || '#0D9488'}
                              onChange={(e) => handleUpdateBranding('primary_color', e.target.value)}
                              className="absolute inset-0 w-full h-full cursor-pointer border-0 p-0"
                              style={{ 
                                WebkitAppearance: 'none',
                                MozAppearance: 'none',
                                appearance: 'none',
                                backgroundColor: 'transparent'
                              }}
                              data-testid="edit-color-picker"
                            />
                            <div 
                              className="absolute inset-0 pointer-events-none"
                              style={{ backgroundColor: selectedStore.branding?.primary_color || '#0D9488' }}
                            />
                          </div>
                          <Input
                            value={selectedStore.branding?.primary_color || '#0D9488'}
                            onChange={(e) => handleUpdateBranding('primary_color', e.target.value)}
                            placeholder="#0D9488"
                            className="w-28 font-mono text-sm"
                            data-testid="edit-color-input"
                          />
                          <div 
                            className="flex-1 h-10 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                            style={{ backgroundColor: selectedStore.branding?.primary_color || '#0D9488' }}
                          >
                            Button Preview
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Store Details (Read-only info) */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
                        Store Details
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground text-xs">Owner/Organization</p>
                          <p className="font-medium">{selectedStore.owner_name || '-'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Store Type</p>
                          <Badge className={getStoreTypeColor(selectedStore.store_type)}>
                            {selectedStore.store_type}
                          </Badge>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Contact Email</p>
                          <p className="font-medium">{selectedStore.owner_email || '-'}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-xs">Contact Phone</p>
                          <p className="font-medium">{selectedStore.owner_phone || '-'}</p>
                        </div>
                        <div className="col-span-2">
                          <p className="text-muted-foreground text-xs">Description</p>
                          <p className="font-medium">{selectedStore.description || '-'}</p>
                        </div>
                        {selectedStore.store_slug && (
                          <div className="col-span-2">
                            <p className="text-muted-foreground text-xs">Store Slug</p>
                            <p className="font-mono text-sm">{selectedStore.store_slug}</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="payments" className="space-y-4" data-testid="tab-content-payments">
                  <WebstoreOwnerConnectCard webstore={selectedStore} />

                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Record Payout</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs">Amount ($)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={detailPayoutAmount}
                            onChange={(e) => setDetailPayoutAmount(e.target.value)}
                            placeholder="0.00"
                            className="h-8 text-sm"
                            data-testid="payout-amount-input"
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Notes (optional)</Label>
                          <Input
                            value={detailPayoutNotes}
                            onChange={(e) => setDetailPayoutNotes(e.target.value)}
                            placeholder="e.g., Check #1234"
                            className="h-8 text-sm"
                            data-testid="payout-notes-input"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <Button
                          size="sm"
                          onClick={handleRecordDetailPayout}
                          disabled={submittingDetailPayout || !detailPayoutAmount}
                          data-testid="record-payout-btn"
                        >
                          {submittingDetailPayout ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : null}
                          Record Payout
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  {storePayouts.length > 0 && (
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm">Payout History</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {storePayouts.map((p) => (
                            <div key={p.id} className="flex justify-between items-center text-sm border-b pb-2">
                              <div>
                                <p className="font-medium">${p.amount?.toFixed?.(2) ?? p.amount}</p>
                                {p.notes && <p className="text-xs text-muted-foreground">{p.notes}</p>}
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                              </span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </TabsContent>

                <TabsContent value="orders" className="space-y-4" data-testid="tab-content-orders">
                  {loadingDetailOrders ? (
                    <div className="flex items-center justify-center py-8 text-muted-foreground text-sm gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" /> Loading orders…
                    </div>
                  ) : storeDetailOrders.length === 0 ? (
                    <div className="text-center py-10 text-muted-foreground text-sm">
                      No orders for this store yet.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {storeDetailOrders.map((order) => (
                        <div key={order.id} className="border rounded-lg p-3 flex items-center justify-between gap-3" data-testid={`store-order-${order.id}`}>
                          <div className="min-w-0">
                            <p className="font-medium text-sm truncate">{order.customer_name || order.buyer_name || 'Unknown Customer'}</p>
                            <p className="text-xs text-muted-foreground">{order.created_at ? new Date(order.created_at).toLocaleDateString() : ''}</p>
                          </div>
                          <div className="text-right shrink-0">
                            <p className="font-semibold text-sm">${(order.total_amount || 0).toFixed(2)}</p>
                            <Badge variant="outline" className="text-[10px]">{order.status}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="analytics" className="mt-4" data-testid="tab-content-analytics">
                  <WebstoreDetailDashboard
                    store={selectedStore}
                    onClose={() => setIsDetailDialogOpen(false)}
                  />
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </PageStack>
  );
}
