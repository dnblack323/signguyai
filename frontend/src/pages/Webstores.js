import { useEffect, useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
  Upload, ImageIcon, CreditCard, AlertTriangle, Loader2, Palette
} from 'lucide-react';
import { toast } from 'sonner';
import WebstoreDetailDashboard from '../components/WebstoreDetailDashboard';

const storeTypes = [
  { value: 'business', label: 'Business (B2B)', icon: Building2, description: 'Employee apparel & company stores' },
  { value: 'fundraiser', label: 'Fundraiser', icon: Heart, description: 'Campaigns with profit sharing' },
  { value: 'creator', label: 'Creator', icon: User, description: 'Individual merch with commission' },
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
  };
  return colors[type] || 'bg-gray-500/20 text-gray-400';
};

const getStatusBadge = (status) => {
  const colors = {
    active: 'bg-green-500/20 text-green-400 border-green-500/30',
    disabled: 'bg-red-500/20 text-red-400 border-red-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };
  return colors[status] || colors.pending;
};

export default function Webstores() {
  const { 
    getWebstores, createWebstore, updateWebstore, deleteWebstore,
    getWebstoreOrdersV2, getProducts, getWebstoreProducts,
    assignProductToWebstore, removeProductFromWebstore, updateWebstoreProductStatus,
    createJobFromOrder, recordPayout, getWebstorePayouts,
    uploadWebstoreLogo, uploadWebstoreBanner,
    getStripeConnectStatus, createStripeConnectAccount
  } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [stripeConnected, setStripeConnected] = useState(null); // null = loading, true/false = status
  const [connectingStripe, setConnectingStripe] = useState(false);
  const [webstores, setWebstores] = useState([]);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [activeTab, setActiveTab] = useState('stores');
  
  // Dialog states
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [storeProducts, setStoreProducts] = useState([]);
  const [storePayouts, setStorePayouts] = useState([]);
  const [detailTab, setDetailTab] = useState('dashboard');
  
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
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    store_type: 'business',
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
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [storesData, ordersData, productsData] = await Promise.all([
        getWebstores(),
        getWebstoreOrdersV2(),
        getProducts()
      ]);
      setWebstores(storesData);
      setOrders(ordersData);
      setProducts(productsData);
    } catch (err) {
      console.error('Error loading data:', err);
    }
    setLoading(false);
  };

  // Check Stripe Connect status first
  const checkStripeStatus = async () => {
    try {
      const status = await getStripeConnectStatus();
      setStripeConnected(status.connected && status.charges_enabled);
    } catch (err) {
      console.error('Error checking Stripe status:', err);
      setStripeConnected(false);
    }
  };

  const handleConnectStripe = async () => {
    setConnectingStripe(true);
    try {
      const result = await createStripeConnectAccount();
      if (result.url) {
        window.location.href = result.url;
      }
    } catch (err) {
      console.error('Error connecting Stripe:', err);
      toast.error('Failed to start Stripe connection');
    }
    setConnectingStripe(false);
  };

  useEffect(() => {
    checkStripeStatus();
    loadData();
  }, []);

  const resetForm = () => {
    setFormData({
      name: '',
      store_type: 'business',
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
    });
    setLogoPreview(null);
    setLogoFile(null);
    setBannerPreview(null);
    setBannerFile(null);
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
    e.preventDefault();
    if (!formData.name.trim() || !formData.owner_name.trim()) {
      toast.error('Store name and owner are required');
      return;
    }
    try {
      const newStore = await createWebstore(formData);
      
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
      setIsCreateDialogOpen(false);
      resetForm();
      await loadData();
    } catch (err) {
      toast.error('Failed to create webstore');
    }
  };

  const handleViewStore = async (store) => {
    setSelectedStore(store);
    setDetailTab('dashboard');
    try {
      const [prods, payouts] = await Promise.all([
        getWebstoreProducts(store.id, true),
        getWebstorePayouts(store.id)
      ]);
      setStoreProducts(prods);
      setStorePayouts(payouts);
    } catch (err) {
      console.error('Error loading store details:', err);
    }
    setIsDetailDialogOpen(true);
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
      toast.success('Job created from order');
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

  const filteredStores = selectedType === 'all' 
    ? webstores 
    : webstores.filter(s => s.store_type === selectedType);

  // Calculate stats
  const totalSales = webstores.reduce((sum, s) => sum + (s.total_sales || 0), 0);
  const totalProfit = webstores.reduce((sum, s) => sum + (s.total_profit || 0), 0);
  const totalOwed = webstores.reduce((sum, s) => sum + (s.payout_owed || 0), 0);
  const pendingOrders = orders.filter(o => o.status === 'pending').length;

  // Show Stripe Connect required message if not connected
  if (stripeConnected === false) {
    return (
      <div className="space-y-6 animate-fade-in" data-testid="webstores-page">
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-full p-6 mb-6">
            <CreditCard className="h-16 w-16 text-amber-500" />
          </div>
          <h1 className="text-3xl font-bold font-heading mb-3">Connect Stripe to Use Webstores</h1>
          <p className="text-muted-foreground max-w-md mb-6">
            Webstores require Stripe payment processing to accept customer orders. 
            Connect your Stripe account to start selling online.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              size="lg" 
              className="neon-glow"
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
          <div className="mt-8 p-4 bg-[var(--surface-2)] rounded-lg max-w-md">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Why is Stripe required?
            </h3>
            <ul className="text-sm text-muted-foreground space-y-1 text-left">
              <li>• Accept credit card payments from customers</li>
              <li>• Automatic order processing and confirmation</li>
              <li>• Orders automatically added to your Jobs list</li>
              <li>• Secure, PCI-compliant payment handling</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // Show loading while checking Stripe status
  if (stripeConnected === null) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="webstores-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight" style={{ color: 'var(--text)' }}>Webstore Manager</h1>
          <p className="text-muted-foreground mt-1">Manage all your webstores from one place</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="create-store-btn" onClick={() => resetForm()}>
              <Plus className="h-4 w-4 mr-2" /> Create Webstore
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">Create New Webstore</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateStore} className="space-y-4">
              {/* Store Type Selection */}
              <div className="space-y-2">
                <Label>Store Type *</Label>
                <div className="grid grid-cols-3 gap-3">
                  {storeTypes.map(type => {
                    const Icon = type.icon;
                    return (
                      <button
                        key={type.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, store_type: type.value })}
                        className={`p-4 rounded-lg border-2 transition-all text-left ${
                          formData.store_type === type.value
                            ? 'border-primary bg-primary/10'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <Icon className="h-6 w-6 mb-2" />
                        <p className="font-medium text-sm">{type.label}</p>
                        <p className="text-xs text-muted-foreground">{type.description}</p>
                      </button>
                    );
                  })}
                </div>
              </div>

              <Separator />

              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2 col-span-2">
                  <Label>Store Name *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., ABC Company Store"
                    data-testid="store-name-input"
                  />
                </div>
                <div className="space-y-2 col-span-2">
                  <Label>Owner/Organization Name *</Label>
                  <Input
                    value={formData.owner_name}
                    onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                    placeholder="Company or individual name"
                    data-testid="store-owner-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contact Email</Label>
                  <Input
                    type="email"
                    value={formData.owner_email}
                    onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                    placeholder="email@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Contact Phone</Label>
                  <Input
                    value={formData.owner_phone}
                    onChange={(e) => setFormData({ ...formData, owner_phone: e.target.value })}
                    placeholder="(555) 123-4567"
                  />
                </div>
                <div className="space-y-2 col-span-2">
                  <Label>Description</Label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Store description..."
                    rows={2}
                  />
                </div>
              </div>

              {/* Type-specific fields */}
              {formData.store_type === 'fundraiser' && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    <h4 className="font-medium">Fundraiser Settings</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label>Goal Amount</Label>
                        <Input
                          type="number"
                          value={formData.fundraiser_goal}
                          onChange={(e) => setFormData({ ...formData, fundraiser_goal: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Start Date</Label>
                        <Input
                          type="date"
                          value={formData.fundraiser_start_date}
                          onChange={(e) => setFormData({ ...formData, fundraiser_start_date: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>End Date</Label>
                        <Input
                          type="date"
                          value={formData.fundraiser_end_date}
                          onChange={(e) => setFormData({ ...formData, fundraiser_end_date: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Fundraiser Profit Share (%)</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={formData.fundraiser_profit_percent}
                        onChange={(e) => setFormData({ ...formData, fundraiser_profit_percent: parseFloat(e.target.value) || 0 })}
                      />
                      <p className="text-xs text-muted-foreground">
                        Percentage of profit that goes to the fundraiser (you keep the rest)
                      </p>
                    </div>
                  </div>
                </>
              )}

              {formData.store_type === 'creator' && (
                <>
                  <Separator />
                  <div className="space-y-4">
                    <h4 className="font-medium">Creator Commission Settings</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Commission Type</Label>
                        <Select
                          value={formData.creator_commission_type}
                          onValueChange={(val) => setFormData({ ...formData, creator_commission_type: val })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percentage">Percentage of Profit</SelectItem>
                            <SelectItem value="fixed">Fixed Amount per Item</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>
                          {formData.creator_commission_type === 'percentage' ? 'Commission %' : 'Amount per Item ($)'}
                        </Label>
                        <Input
                          type="number"
                          min="0"
                          value={formData.creator_commission_value}
                          onChange={(e) => setFormData({ ...formData, creator_commission_value: parseFloat(e.target.value) || 0 })}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Branding / Customization */}
              <Separator />
              <div className="space-y-4">
                <h4 className="font-medium">Store Branding</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3 col-span-2">
                    <Label>Company Logo</Label>
                    
                    {/* Logo Preview */}
                    {(logoPreview || formData.branding?.logo_url) && (
                      <div className="flex items-center gap-4 p-3 rounded-lg border border-border bg-muted/30">
                        <img 
                          src={logoPreview || formData.branding?.logo_url} 
                          alt="Logo preview" 
                          className="h-16 w-auto object-contain rounded"
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Logo Preview</p>
                          <p className="text-xs text-muted-foreground">
                            {logoFile ? logoFile.name : 'Current logo'}
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
                              if (logoInputRef.current) logoInputRef.current.value = '';
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    )}
                    
                    {/* Upload Button */}
                    <div className="flex gap-2">
                      <input
                        ref={logoInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                        onChange={handleLogoSelect}
                        className="hidden"
                        data-testid="store-logo-file-input"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => logoInputRef.current?.click()}
                        className="flex-1"
                        data-testid="store-logo-upload-btn"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        {logoPreview ? 'Change Logo' : 'Upload Logo'}
                      </Button>
                    </div>
                    
                    {/* Or use URL */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-border" />
                      <span className="text-xs text-muted-foreground">or enter URL</span>
                      <div className="flex-1 h-px bg-border" />
                    </div>
                    
                    <Input
                      value={formData.branding?.logo_url || ''}
                      onChange={(e) => {
                        setFormData({ 
                          ...formData, 
                          branding: { ...formData.branding, logo_url: e.target.value } 
                        });
                        // Clear file upload if URL is entered
                        if (e.target.value) {
                          setLogoPreview(null);
                          setLogoFile(null);
                        }
                      }}
                      placeholder="https://example.com/logo.png"
                      data-testid="store-logo-input"
                    />
                    <p className="text-xs text-muted-foreground">
                      Upload an image or enter a URL. Max file size: 2MB
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label>Accent Color</Label>
                    <div className="flex gap-2 items-center">
                      <div className="relative w-12 h-10 rounded border border-border overflow-hidden cursor-pointer">
                        <input
                          type="color"
                          value={formData.branding?.primary_color || '#0D9488'}
                          onChange={(e) => setFormData({ 
                            ...formData, 
                            branding: { ...formData.branding, primary_color: e.target.value } 
                          })}
                          className="absolute inset-0 w-full h-full cursor-pointer border-0 p-0"
                          style={{ 
                            WebkitAppearance: 'none',
                            MozAppearance: 'none',
                            appearance: 'none',
                            backgroundColor: 'transparent'
                          }}
                          data-testid="store-color-input"
                        />
                        <div 
                          className="absolute inset-0 pointer-events-none"
                          style={{ backgroundColor: formData.branding?.primary_color || '#0D9488' }}
                        />
                      </div>
                      <Input
                        value={formData.branding?.primary_color || '#0D9488'}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          branding: { ...formData.branding, primary_color: e.target.value } 
                        })}
                        placeholder="#0D9488"
                        className="w-28 font-mono"
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Customize the storefront theme color
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label>Preview</Label>
                    <div 
                      className="w-full h-10 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                      style={{ backgroundColor: formData.branding?.primary_color || '#0D9488' }}
                    >
                      Button Preview
                    </div>
                  </div>
                  
                  {/* Banner Image Upload */}
                  <div className="space-y-3 col-span-2">
                    <Label>Store Banner</Label>
                    <p className="text-xs text-muted-foreground">
                      Add a custom banner image to personalize the storefront header
                    </p>
                    
                    {/* Banner Preview */}
                    {(bannerPreview || formData.branding?.banner_url) && (
                      <div className="relative rounded-lg border border-border overflow-hidden">
                        <img 
                          src={bannerPreview || formData.branding?.banner_url} 
                          alt="Banner preview" 
                          className="w-full h-32 object-cover"
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
                              if (bannerInputRef.current) bannerInputRef.current.value = '';
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    )}
                    
                    {/* Upload Button */}
                    <div className="flex gap-2">
                      <input
                        ref={bannerInputRef}
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                        onChange={handleBannerSelect}
                        className="hidden"
                        data-testid="store-banner-file-input"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => bannerInputRef.current?.click()}
                        className="flex-1"
                        data-testid="store-banner-upload-btn"
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        {bannerPreview ? 'Change Banner' : 'Upload Banner'}
                      </Button>
                    </div>
                    
                    {/* Or use URL */}
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-px bg-border" />
                      <span className="text-xs text-muted-foreground">or enter URL</span>
                      <div className="flex-1 h-px bg-border" />
                    </div>
                    
                    <Input
                      value={formData.branding?.banner_url || ''}
                      onChange={(e) => {
                        setFormData({ 
                          ...formData, 
                          branding: { ...formData.branding, banner_url: e.target.value } 
                        });
                        // Clear file upload if URL is entered
                        if (e.target.value) {
                          setBannerPreview(null);
                          setBannerFile(null);
                        }
                      }}
                      placeholder="https://example.com/banner.jpg"
                      data-testid="store-banner-input"
                    />
                    <p className="text-xs text-muted-foreground">
                      Recommended size: 1200x300px. Max file size: 5MB
                    </p>
                  </div>
                </div>
              </div>

              {/* Visibility */}
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Public Store</Label>
                  <p className="text-xs text-muted-foreground">Allow anyone to view and order</p>
                </div>
                <Switch
                  checked={formData.is_public}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_public: checked })}
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="store-submit-btn">Create Store</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Store className="h-8 w-8 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Total Stores</p>
                <p className="text-2xl font-bold">{webstores.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <DollarSign className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-sm text-muted-foreground">Total Sales</p>
                <p className="text-2xl font-bold text-green-400">{formatCurrency(totalSales)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-8 w-8 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Total Profit</p>
                <p className="text-2xl font-bold text-primary">{formatCurrency(totalProfit)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <ShoppingCart className="h-8 w-8 text-yellow-400" />
              <div>
                <p className="text-sm text-muted-foreground">Pending Orders</p>
                <p className="text-2xl font-bold text-yellow-400">{pendingOrders}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="stores" data-testid="tab-stores">
            <Store className="h-4 w-4 mr-2" /> All Stores ({webstores.length})
          </TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">
            <ShoppingCart className="h-4 w-4 mr-2" /> Orders ({orders.length})
          </TabsTrigger>
        </TabsList>

        {/* Stores Tab */}
        <TabsContent value="stores" className="mt-4 space-y-4">
          {/* Type Filter */}
          <div className="flex gap-2">
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

          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : filteredStores.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Store className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No webstores yet</p>
                  <p className="text-sm mt-1">Create your first webstore to get started</p>
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
                          className={idx % 2 === 0 ? '' : 'bg-muted/30'}
                          data-testid={`store-row-${store.id}`}
                        >
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center">
                                <Icon className="h-5 w-5" />
                              </div>
                              <div>
                                <p className="font-medium">{store.name}</p>
                                <p className="text-xs text-muted-foreground">
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
                          <TableCell>{store.owner_name}</TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(store.total_sales || 0)}
                          </TableCell>
                          <TableCell className="text-right text-green-400">
                            {formatCurrency(store.total_profit || 0)}
                          </TableCell>
                          <TableCell className="text-right text-yellow-400">
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {orders.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
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
                      <TableHead>Job</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order, idx) => (
                      <TableRow key={order.id} className={idx % 2 === 0 ? '' : 'bg-muted/30'}>
                        <TableCell className="font-mono text-sm">#{order.id.slice(0, 8)}</TableCell>
                        <TableCell>
                          <Badge className={getStoreTypeColor(order.store_type)}>
                            {order.webstore_name || order.store_type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{order.customer_name}</p>
                            <p className="text-xs text-muted-foreground">{order.customer_email}</p>
                          </div>
                        </TableCell>
                        <TableCell>{order.items?.length || 0} items</TableCell>
                        <TableCell className="text-right font-bold">{formatCurrency(order.total)}</TableCell>
                        <TableCell className="text-right text-green-400">
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
                            <span className="text-muted-foreground">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {!order.job_id && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCreateJobFromOrder(order.id)}
                            >
                              Create Job
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Store Detail Dialog */}
      <Dialog open={isDetailDialogOpen} onOpenChange={setIsDetailDialogOpen}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
          {selectedStore && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {(() => {
                      const Icon = getStoreTypeIcon(selectedStore.store_type);
                      return <Icon className="h-6 w-6" />;
                    })()}
                    <div>
                      <DialogTitle className="font-heading uppercase">{selectedStore.name}</DialogTitle>
                      <p className="text-sm text-muted-foreground">{selectedStore.owner_name}</p>
                    </div>
                  </div>
                  <Badge className={getStoreTypeColor(selectedStore.store_type)}>
                    {selectedStore.store_type}
                  </Badge>
                </div>
              </DialogHeader>

              <Tabs value={detailTab} onValueChange={setDetailTab}>
                <TabsList className="grid grid-cols-3 w-full">
                  <TabsTrigger value="dashboard">
                    <BarChart3 className="h-4 w-4 mr-2" /> Dashboard
                  </TabsTrigger>
                  <TabsTrigger value="products">Products</TabsTrigger>
                  <TabsTrigger value="settings">Settings & Branding</TabsTrigger>
                </TabsList>

                <TabsContent value="dashboard" className="mt-4">
                  <WebstoreDetailDashboard 
                    store={selectedStore} 
                    onClose={() => setIsDetailDialogOpen(false)}
                  />
                </TabsContent>

                <TabsContent value="products" className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Enable products from your catalog for this store
                  </p>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {products.map(product => {
                      const assigned = storeProducts.find(sp => sp.id === product.id);
                      const isEnabled = assigned?.is_enabled ?? false;
                      return (
                        <div 
                          key={product.id}
                          className={`flex items-center justify-between p-3 rounded-lg border ${
                            isEnabled ? 'border-primary/30 bg-primary/5' : 'border-border'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <Package className="h-5 w-5 text-muted-foreground" />
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
                          />
                        </div>
                      );
                    })}
                  </div>
                </TabsContent>

                <TabsContent value="settings" className="space-y-6">
                  {/* Store Link Section - Prominent at top */}
                  <div className="p-4 rounded-lg bg-gradient-to-r from-[#2F8BFB]/10 to-[#2F8BFB]/5 border border-[#2F8BFB]/20">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#2F8BFB]/20 rounded-lg">
                          <Link2 className="h-5 w-5 text-[#2F8BFB]" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">Public Store Link</p>
                          <p className="text-xs font-mono text-muted-foreground truncate max-w-[350px]">
                            {getStoreUrl(selectedStore.id)}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleCopyLink(selectedStore.id)}
                          data-testid="copy-store-link-btn"
                        >
                          <Copy className="h-4 w-4 mr-1" /> Copy
                        </Button>
                        <Button 
                          size="sm"
                          onClick={() => handleOpenStore(selectedStore.id)}
                          className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90 text-white"
                          data-testid="open-store-btn"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" /> Open
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Store Status Controls */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        Store Status
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Store Active</Label>
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
                          <Label>Public Access</Label>
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
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
