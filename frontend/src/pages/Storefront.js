import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { formatCurrency } from '../lib/utils';
import { 
  ShoppingCart, Plus, Minus, Trash2, Package, CheckCircle,
  Store, Heart, Building2, User, ArrowLeft, X
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Storefront() {
  const { storeId } = useParams();
  const [searchParams] = useSearchParams();
  const embedded = searchParams.get('embedded') === 'true';
  
  const [loading, setLoading] = useState(true);
  const [store, setStore] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
  const [orderPlaced, setOrderPlaced] = useState(false);
  const [processingCheckout, setProcessingCheckout] = useState(false);
  const [verifyingPayment, setVerifyingPayment] = useState(false);
  const [supporters, setSupporters] = useState([]);
  
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    shipping_address: '',
    notes: ''
  });

  // Part 4: donation selection state ($amount + custom mode).
  // null = no donation selected.
  const [donationAmount, setDonationAmount] = useState(0);
  const [donationMode, setDonationMode] = useState('none'); // 'none' | 'preset' | 'custom'
  const [customDonation, setCustomDonation] = useState('');
  // Polish: donor consent toggle — only relevant when store has
  // show_supporter_names="yes_with_permission" AND user is donating.
  const [donorConsent, setDonorConsent] = useState(false);

  useEffect(() => {
    loadStore();
    
    // Handle payment success/cancel from URL params.
    // IMPORTANT: never trust URL flag alone; verify with backend Stripe status.
    const urlParams = new URLSearchParams(window.location.search);
    const paymentResult = urlParams.get('payment');
    const sessionId = urlParams.get('session_id');

    const verifyPayment = async () => {
      if (paymentResult !== 'success') return;

      if (!sessionId) {
        toast.error('Payment session missing. Please contact support if you were charged.');
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
      }

      setVerifyingPayment(true);
      const maxAttempts = 6;

      try {
        for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
          const statusRes = await fetch(`${API}/api/stripe-connect/payment-status/${sessionId}`);
          const statusData = await statusRes.json();

          if (!statusRes.ok) {
            throw new Error(statusData?.detail || 'Unable to verify payment');
          }

          if (statusData.payment_status === 'paid') {
            setOrderPlaced(true);
            setCart([]);
            toast.success('Payment successful! Thank you for your order.');
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }

          const finalFailure = ['expired', 'canceled'].includes(statusData.status)
            || ['failed', 'unpaid'].includes(statusData.payment_status);

          if (finalFailure) {
            toast.error('Payment was not completed. Please try checkout again.');
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
          }

          // Poll briefly while Stripe/webhook settles.
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }

        toast.error('Payment confirmation is taking longer than expected. Please refresh in a moment.');
      } catch (err) {
        toast.error(err.message || 'Failed to verify payment status');
      } finally {
        setVerifyingPayment(false);
      }
    };

    if (paymentResult === 'cancelled') {
      toast.info('Payment cancelled. Your cart is still saved.');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      verifyPayment();
    }
  }, [storeId]);

  const loadStore = async () => {
    setLoading(true);
    try {
      // Fetch store details using public storefront endpoint
      const storeRes = await fetch(`${API}/api/storefront/${storeId}`);
      if (!storeRes.ok) throw new Error('Store not found');
      const storeData = await storeRes.json();
      setStore(storeData);
      
      // Fetch store products using public storefront endpoint
      const productsRes = await fetch(`${API}/api/storefront/${storeId}/products`);
      const productsData = await productsRes.json();
      setProducts(productsData);

      // Fetch recent supporters (Event Store fundraisers only — endpoint
      // returns [] for non-event/non-fundraiser stores or when names are
      // hidden, so we can safely call it unconditionally).
      try {
        const supRes = await fetch(`${API}/api/storefront/${storeId}/supporters?limit=5`);
        if (supRes.ok) {
          const sup = await supRes.json();
          setSupporters(Array.isArray(sup) ? sup : []);
        }
      } catch (_) { /* non-critical */ }
    } catch (err) {
      console.error('Error loading store:', err);
      toast.error('Store not found');
    }
    setLoading(false);
  };

  const addToCart = (product, variant = null) => {
    const cartItemId = variant ? `${product.product_id}-${variant.id}` : product.product_id;
    const existingItem = cart.find(item => item.cartItemId === cartItemId);
    
    if (existingItem) {
      setCart(cart.map(item => 
        item.cartItemId === cartItemId 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      const price = product.effective_price + (variant?.additional_cost || 0);
      setCart([...cart, {
        cartItemId,
        product_id: product.product_id,
        variant_id: variant?.id || null,
        name: product.product.name,
        variant_name: variant?.name || null,
        price,
        quantity: 1
      }]);
    }
    toast.success('Added to cart');
  };

  const updateQuantity = (cartItemId, delta) => {
    setCart(cart.map(item => {
      if (item.cartItemId === cartItemId) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty } : item;
      }
      return item;
    }).filter(item => item.quantity > 0));
  };

  const removeFromCart = (cartItemId) => {
    setCart(cart.filter(item => item.cartItemId !== cartItemId));
  };

  const cartTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const checkoutEnabled = store?.checkout_enabled !== false;

  // Part 4: Event Store fundraiser + checkout extras (all sourced from the
  // public store payload; locked_settings is a pre-sanitized subset that
  // only contains shipping/handling info — no cost or profit data).
  const lockedSettings = store?.locked_settings || {};
  const shippingHandlingEnabled = !!lockedSettings.shipping_handling_enabled;
  const shippingHandlingFee = Number(
    shippingHandlingEnabled
      ? (lockedSettings.shipping_handling_fee || 0)
      : (Number(lockedSettings.shipping_fee || 0) + Number(lockedSettings.handling_fee || 0))
  ) || 0;
  const shippingHandlingLabel = shippingHandlingEnabled
    ? (lockedSettings.shipping_handling_label || 'Shipping & Handling')
    : 'Shipping & Handling';

  // Effective donation amount based on the current selection mode.
  let effectiveDonation = 0;
  if (donationMode === 'preset') {
    effectiveDonation = Number(donationAmount) || 0;
  } else if (donationMode === 'custom') {
    const v = parseFloat(customDonation);
    effectiveDonation = Number.isFinite(v) && v > 0 ? v : 0;
  }
  effectiveDonation = Math.max(0, Math.round(effectiveDonation * 100) / 100);

  const donationsEnabled = !!store?.allow_checkout_donations;
  const donationPresets = Array.isArray(store?.donation_presets) ? store.donation_presets : [];
  const allowCustomDonation = !!store?.allow_custom_donation;

  const grandTotal = Math.round((cartTotal + shippingHandlingFee + effectiveDonation) * 100) / 100;

  // Fundraiser progress bar conditions:
  //  - fundraiser_enabled MUST be true
  //  - show_progress_bar MUST be true
  //  - fundraiser_goal_amount > 0
  const fundraiserGoal = Number(store?.fundraiser_goal_amount || 0);
  const showFundraiserProgress = !!store?.fundraiser_enabled
    && !!store?.show_progress_bar
    && fundraiserGoal > 0;
  const totalRaised = Number(store?.total_raised || 0);
  const progressPct = fundraiserGoal > 0
    ? Math.min(100, (totalRaised / fundraiserGoal) * 100)
    : 0;

  // Polish: supporters strip — Event Stores only, when allowed AND there
  // are supporters. The backend already enforces all the gates; the UI
  // just needs to know whether to render the section.
  const showSupporters = store?.store_type === 'event'
    && !!store?.fundraiser_enabled
    && ((store?.show_supporter_names || 'no').toLowerCase() !== 'no')
    && Array.isArray(supporters)
    && supporters.length > 0;
  const supporterNameMode = (store?.show_supporter_names || 'no').toLowerCase();
  const supportersRequireConsent = supporterNameMode === 'yes_with_permission';

  const handleCheckout = async (e) => {
    e.preventDefault();
    if (processingCheckout) return;
    if (!customerInfo.name || !customerInfo.email) {
      toast.error('Name and email are required');
      return;
    }
    if (cart.length === 0) {
      toast.error('Cart is empty');
      return;
    }

    setProcessingCheckout(true);
    try {
      // Validate donation: if user selected 'custom', must have a positive value
      if (donationMode === 'custom') {
        const cv = parseFloat(customDonation);
        if (!Number.isFinite(cv) || cv <= 0) {
          setProcessingCheckout(false);
          toast.error('Please enter a valid donation amount or choose No donation.');
          return;
        }
      }

      // Create Stripe checkout session
      const checkoutPayload = {
        items: cart.map(item => ({
          product_id: item.product_id,
          variant_id: item.variant_id,
          variant_name: item.variant_name,
          quantity: item.quantity,
          price: item.price
        })),
        customer_info: {
          name: customerInfo.name,
          email: customerInfo.email,
          phone: customerInfo.phone,
          shipping_address: customerInfo.shipping_address,
          notes: customerInfo.notes
        },
        donation_amount: donationsEnabled ? effectiveDonation : 0,
        donor_consent: donationsEnabled && effectiveDonation > 0
          ? (supportersRequireConsent ? donorConsent : (supporterNameMode === 'yes_all'))
          : false,
      };

      // Use clean origin URL (without query params)
      const originUrl = `${window.location.origin}`;
      
      const paymentRes = await fetch(`${API}/api/stripe-connect/webstore/${storeId}/checkout?origin_url=${encodeURIComponent(originUrl)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(checkoutPayload)
      });

      const paymentData = await paymentRes.json();
      
      if (paymentRes.ok && paymentData.url) {
        // Redirect to Stripe checkout
        window.location.href = paymentData.url;
        return;
      }

      // Show specific error message based on response
      if (paymentData.detail === "Store cannot accept payments at this time") {
        throw new Error(store?.checkout_message || "This store is not yet set up to accept payments. Please contact the store owner.");
      } else if (paymentData.detail === "Store payment setup incomplete") {
        throw new Error(store?.checkout_message || "The store's payment system is still being configured. Please try again later.");
      }
      throw new Error(paymentData.detail || 'Unable to process payment');
    } catch (err) {
      console.error('Checkout error:', err);
      toast.error(err.message || 'Failed to process checkout. Please try again.');
    } finally {
      setProcessingCheckout(false);
    }
  };

  const getStoreTypeIcon = (type) => {
    switch (type) {
      case 'business': return Building2;
      case 'fundraiser': return Heart;
      case 'creator': return User;
      case 'event': return Heart;
      default: return Store;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!store) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <Store className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-xl font-bold mb-2">Store Not Found</h2>
            <p className="text-muted-foreground">This store doesn't exist or has been disabled.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (store.status !== 'active') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <Store className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h2 className="text-xl font-bold mb-2">Store Unavailable</h2>
            <p className="text-muted-foreground">This store is currently not accepting orders.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (orderPlaced) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="max-w-md w-full">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Order Placed!</h2>
            <p className="text-muted-foreground mb-6">
              Thank you for your order. We'll send a confirmation to your email shortly.
            </p>
            <Button onClick={() => { setOrderPlaced(false); setCustomerInfo({ name: '', email: '', phone: '', shipping_address: '', notes: '' }); }}>
              Continue Shopping
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const StoreIcon = getStoreTypeIcon(store.store_type);
  const primaryColor = store.branding?.primary_color || '#0D9488';
  const bannerUrl = store.branding?.banner_url
    || store.banner_url
    || store.banner_image_url
    || store.banner_image_data;
  const logoUrl = store.branding?.logo_url
    || store.logo_url
    || store.logo_image_url
    || store.logo_image_data;

  return (
    <div className="min-h-screen bg-background">
      {/* Banner Image */}
      {bannerUrl && (
        <div className="w-full h-48 sm:h-64 overflow-hidden">
          <img 
            src={bannerUrl} 
            alt={`${store.name} banner`} 
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Header */}
      <header 
        className="border-b border-border sticky top-0 z-40 bg-card"
        style={{ borderBottomColor: primaryColor + '40' }}
      >
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {logoUrl ? (
              <img src={logoUrl} alt={store.name} className="h-10 w-auto rounded" />
            ) : (
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: primaryColor + '20' }}
              >
                <StoreIcon className="h-5 w-5" style={{ color: primaryColor }} />
              </div>
            )}
            <div>
              <h1 className="font-bold text-lg">{store.name}</h1>
              <p className="text-xs text-muted-foreground">{store.owner_name}</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            className="relative"
            onClick={() => setIsCartOpen(true)}
            data-testid="cart-button"
          >
            <ShoppingCart className="h-5 w-5 mr-2" />
            Cart
            {cartCount > 0 && (
              <span 
                className="absolute -top-2 -right-2 w-5 h-5 rounded-full text-xs flex items-center justify-center text-white"
                style={{ backgroundColor: primaryColor }}
              >
                {cartCount}
              </span>
            )}
          </Button>
        </div>
      </header>

      {/* Banner / Description */}
      {(store.description || store.store_type === 'fundraiser' || showFundraiserProgress) && (
        <div 
          className="border-b border-border"
          style={{ backgroundColor: primaryColor + '10' }}
        >
          <div className="max-w-6xl mx-auto px-4 py-6">
            {store.description && (
              <p className="text-muted-foreground">{store.description}</p>
            )}
            {store.store_type === 'fundraiser' && store.fundraiser_goal > 0 && (
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-2">
                  <span>Fundraiser Progress</span>
                  <span className="font-bold">
                    {formatCurrency(store.total_sales || 0)} / {formatCurrency(store.fundraiser_goal)}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-3">
                  <div 
                    className="h-3 rounded-full transition-all"
                    style={{ 
                      width: `${Math.min(100, ((store.total_sales || 0) / store.fundraiser_goal) * 100)}%`,
                      backgroundColor: primaryColor
                    }}
                  />
                </div>
              </div>
            )}
            {/* Event Store fundraiser progress bar (Part 4). */}
            {showFundraiserProgress && (
              <div className="mt-4" data-testid="fundraiser-progress-bar">
                <div className="flex justify-between text-sm mb-2">
                  <span>
                    {store.fundraiser_name
                      ? `${store.fundraiser_name} — Progress`
                      : 'Fundraiser Progress'}
                  </span>
                  <span className="font-bold" data-testid="fundraiser-progress-amount">
                    {formatCurrency(totalRaised)} / {formatCurrency(fundraiserGoal)}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-3 overflow-hidden">
                  <div
                    className="h-3 rounded-full transition-all"
                    style={{ width: `${progressPct}%`, backgroundColor: primaryColor }}
                  />
                </div>
                {store.fundraiser_description && (
                  <p className="text-xs text-muted-foreground mt-2" data-testid="fundraiser-description">
                    {store.fundraiser_description}
                  </p>
                )}
              </div>
            )}

            {/* Recent supporters strip (Event Store fundraiser only). */}
            {showSupporters && (
              <div className="mt-4" data-testid="supporters-strip">
                <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Recent Supporters
                </p>
                <div className="flex flex-wrap gap-2">
                  {supporters.map((s, idx) => (
                    <div
                      key={`${s.created_at || idx}-${idx}`}
                      className="flex items-center gap-2 rounded-full border bg-white/60 px-3 py-1.5 text-xs shadow-sm"
                      data-testid={`supporter-chip-${idx}`}
                    >
                      <Heart className="h-3 w-3" style={{ color: primaryColor }} />
                      <span className="font-medium text-foreground">{s.name}</span>
                      <span className="text-muted-foreground">{formatCurrency(s.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {!checkoutEnabled && (
        <div className="border-b border-border bg-amber-50" data-testid="store-checkout-inactive-banner">
          <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-1 text-sm text-amber-900">
            <p className="font-semibold">Checkout inactive</p>
            <p>{store.checkout_message || 'Checkout is inactive until this shop connects Stripe through SignGuy AI.'}</p>
          </div>
        </div>
      )}

      {verifyingPayment && (
        <div className="border-b border-border bg-blue-50" data-testid="store-payment-verifying-banner">
          <div className="max-w-6xl mx-auto px-4 py-3 text-sm font-medium text-blue-800">
            Verifying payment… please wait.
          </div>
        </div>
      )}

      {/* Products Grid */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {products.length === 0 ? (
          <div className="text-center py-16">
            <Package className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h2 className="text-xl font-bold mb-2">No Products Available</h2>
            <p className="text-muted-foreground">Check back soon for new products!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((item) => (
              <ProductCard 
                key={item.product_id} 
                item={item} 
                onAddToCart={addToCart}
                primaryColor={primaryColor}
              />
            ))}
          </div>
        )}
      </main>

      {/* Cart Drawer */}
      <Dialog open={isCartOpen} onOpenChange={setIsCartOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              Your Cart ({cartCount} items)
            </DialogTitle>
          </DialogHeader>
          
          {cart.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <ShoppingCart className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Your cart is empty</p>
            </div>
          ) : (
            <>
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {cart.map((item) => (
                  <div key={item.cartItemId} className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{item.name}</p>
                      {item.variant_name && (
                        <p className="text-xs text-muted-foreground">{item.variant_name}</p>
                      )}
                      <p className="text-sm font-bold" style={{ color: primaryColor }}>
                        {formatCurrency(item.price)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button 
                        variant="outline" 
                        size="icon" 
                        className="h-8 w-8"
                        onClick={() => updateQuantity(item.cartItemId, -1)}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      <span className="w-8 text-center font-medium">{item.quantity}</span>
                      <Button 
                        variant="outline" 
                        size="icon" 
                        className="h-8 w-8"
                        onClick={() => updateQuantity(item.cartItemId, 1)}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 text-destructive"
                        onClick={() => removeFromCart(item.cartItemId)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <Separator />
              <div className="flex justify-between items-center font-bold text-lg">
                <span>Total:</span>
                <span style={{ color: primaryColor }}>{formatCurrency(cartTotal)}</span>
              </div>
              <Button 
                className="w-full" 
                onClick={() => { setIsCartOpen(false); setIsCheckoutOpen(true); }}
                style={{ backgroundColor: primaryColor }}
                data-testid="checkout-button"
              >
                Proceed to Checkout
              </Button>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Checkout Dialog */}
      <Dialog open={isCheckoutOpen} onOpenChange={setIsCheckoutOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Checkout</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCheckout} className="space-y-4">
            {!checkoutEnabled && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" data-testid="checkout-disabled-message">
                {store.checkout_message || 'Checkout is inactive until this shop connects Stripe through SignGuy AI.'}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2 col-span-2">
                <Label>Full Name *</Label>
                <Input
                  value={customerInfo.name}
                  onChange={(e) => setCustomerInfo({ ...customerInfo, name: e.target.value })}
                  placeholder="John Smith"
                  data-testid="checkout-name"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Email *</Label>
                <Input
                  type="email"
                  value={customerInfo.email}
                  onChange={(e) => setCustomerInfo({ ...customerInfo, email: e.target.value })}
                  placeholder="john@example.com"
                  data-testid="checkout-email"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input
                  value={customerInfo.phone}
                  onChange={(e) => setCustomerInfo({ ...customerInfo, phone: e.target.value })}
                  placeholder="(555) 123-4567"
                  data-testid="checkout-phone"
                />
              </div>
              <div className="space-y-2 col-span-2">
                <Label>Shipping Address</Label>
                <Textarea
                  value={customerInfo.shipping_address}
                  onChange={(e) => setCustomerInfo({ ...customerInfo, shipping_address: e.target.value })}
                  placeholder="123 Main St, City, State ZIP"
                  rows={2}
                  data-testid="checkout-address"
                />
              </div>
              <div className="space-y-2 col-span-2">
                <Label>Order Notes</Label>
                <Textarea
                  value={customerInfo.notes}
                  onChange={(e) => setCustomerInfo({ ...customerInfo, notes: e.target.value })}
                  placeholder="Special instructions..."
                  rows={2}
                />
              </div>
            </div>

            {/* Donation block (Event Store fundraiser, optional) */}
            {donationsEnabled && (
              <div className="rounded-lg border bg-card p-4 space-y-3" data-testid="checkout-donation-block">
                <div className="flex items-center gap-2">
                  <Heart className="h-4 w-4" style={{ color: primaryColor }} />
                  <p className="font-medium text-sm">Add a donation (optional)</p>
                </div>
                {store.fundraiser_description && (
                  <p className="text-xs text-muted-foreground">{store.fundraiser_description}</p>
                )}
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={donationMode === 'none' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => { setDonationMode('none'); setDonationAmount(0); setCustomDonation(''); }}
                    style={donationMode === 'none' ? { backgroundColor: primaryColor } : undefined}
                    data-testid="donation-none-button"
                  >
                    No thanks
                  </Button>
                  {donationPresets.map((amt) => (
                    <Button
                      key={amt}
                      type="button"
                      variant={donationMode === 'preset' && donationAmount === amt ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => { setDonationMode('preset'); setDonationAmount(amt); setCustomDonation(''); }}
                      style={donationMode === 'preset' && donationAmount === amt ? { backgroundColor: primaryColor } : undefined}
                      data-testid={`donation-preset-${amt}`}
                    >
                      {formatCurrency(amt)}
                    </Button>
                  ))}
                  {allowCustomDonation && (
                    <Button
                      type="button"
                      variant={donationMode === 'custom' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => { setDonationMode('custom'); setDonationAmount(0); }}
                      style={donationMode === 'custom' ? { backgroundColor: primaryColor } : undefined}
                      data-testid="donation-custom-toggle"
                    >
                      Custom
                    </Button>
                  )}
                </div>
                {donationMode === 'custom' && allowCustomDonation && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">$</span>
                    <Input
                      type="number"
                      min="1"
                      step="0.01"
                      value={customDonation}
                      onChange={(e) => setCustomDonation(e.target.value)}
                      placeholder="Enter amount"
                      className="max-w-[140px]"
                      data-testid="donation-custom-input"
                    />
                  </div>
                )}
                {/* Donor consent (only when names require permission). */}
                {effectiveDonation > 0 && supportersRequireConsent && (
                  <label className="flex items-start gap-2 text-xs text-muted-foreground cursor-pointer" data-testid="donor-consent-label">
                    <input
                      type="checkbox"
                      className="mt-0.5"
                      checked={donorConsent}
                      onChange={(e) => setDonorConsent(e.target.checked)}
                      data-testid="donor-consent-checkbox"
                    />
                    <span>
                      Show my name as a supporter on this fundraiser. If unchecked, your donation appears as <em>Anonymous Supporter</em>.
                    </span>
                  </label>
                )}
              </div>
            )}

            {/* Order Summary */}
            <div className="p-4 bg-muted/30 rounded-lg" data-testid="checkout-order-summary">
              <h4 className="font-medium mb-2">Order Summary</h4>
              <div className="space-y-1 text-sm">
                {cart.map(item => (
                  <div key={item.cartItemId} className="flex justify-between">
                    <span>{item.name} {item.variant_name && `(${item.variant_name})`} x{item.quantity}</span>
                    <span>{formatCurrency(item.price * item.quantity)}</span>
                  </div>
                ))}
                <div className="flex justify-between text-muted-foreground">
                  <span>Subtotal</span>
                  <span>{formatCurrency(cartTotal)}</span>
                </div>
                {shippingHandlingFee > 0 && (
                  <div className="flex justify-between text-muted-foreground" data-testid="checkout-shipping-handling-row">
                    <span>{shippingHandlingLabel}</span>
                    <span>{formatCurrency(shippingHandlingFee)}</span>
                  </div>
                )}
                {effectiveDonation > 0 && (
                  <div className="flex justify-between text-muted-foreground" data-testid="checkout-donation-row">
                    <span>Donation</span>
                    <span>{formatCurrency(effectiveDonation)}</span>
                  </div>
                )}
              </div>
              <Separator className="my-2" />
              <div className="flex justify-between font-bold">
                <span>Total</span>
                <span style={{ color: primaryColor }} data-testid="checkout-grand-total">
                  {formatCurrency(grandTotal)}
                </span>
              </div>
            </div>

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setIsCheckoutOpen(false)} className="flex-1">
                Back to Cart
              </Button>
              <Button 
                type="submit" 
                className="flex-1"
                style={{ backgroundColor: primaryColor }}
                disabled={!checkoutEnabled || processingCheckout}
                data-testid="place-order-button"
              >
                {!checkoutEnabled
                  ? 'Checkout Inactive'
                  : (processingCheckout ? 'Redirecting to Stripe…' : 'Continue to Secure Payment')}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center text-sm text-muted-foreground">
        <p>Powered by SignGuy AI</p>
      </footer>
    </div>
  );
}

// Product Card Component
function ProductCard({ item, onAddToCart, primaryColor }) {
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const product = item.product;
  const hasVariants = product.has_variants && product.variants?.length > 0;
  
  // Get images array (fallback to image_url for backwards compatibility)
  const images = product.images?.length > 0 ? product.images : (product.image_url ? [product.image_url] : []);
  
  const effectivePrice = item.effective_price + (selectedVariant?.additional_cost || 0);

  return (
    <Card className="overflow-hidden group hover:border-primary/30 transition-colors">
      {/* Product Image */}
      <div className="aspect-square bg-muted/30 flex items-center justify-center overflow-hidden relative">
        {images.length > 0 ? (
          <>
            <img 
              src={images[currentImageIndex]} 
              alt={product.name} 
              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
            />
            {/* Image Navigation Dots */}
            {images.length > 1 && (
              <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                {images.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(idx); }}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      idx === currentImageIndex ? 'bg-white' : 'bg-white/50'
                    }`}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <Package className="h-16 w-16 text-muted-foreground/50" />
        )}
      </div>
      
      <CardContent className="p-4">
        <h3 className="font-bold mb-1">{product.name}</h3>
        {product.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{product.description}</p>
        )}
        
        <div className="flex items-center justify-between mb-3">
          <span className="text-xl font-bold" style={{ color: primaryColor }}>
            {formatCurrency(effectivePrice)}
          </span>
          <Badge variant="outline" className="text-xs">
            {product.category}
          </Badge>
        </div>

        {/* Variant Selection */}
        {hasVariants && (
          <div className="mb-3">
            <Select
              value={selectedVariant?.id || ''}
              onValueChange={(val) => {
                const variant = product.variants.find(v => v.id === val);
                setSelectedVariant(variant);
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select option" />
              </SelectTrigger>
              <SelectContent>
                {product.variants.filter(v => v.is_available !== false).map((variant) => (
                  <SelectItem key={variant.id} value={variant.id}>
                    {variant.name}
                    {variant.tier && ` (${variant.tier})`}
                    {variant.additional_cost > 0 && ` (+${formatCurrency(variant.additional_cost)})`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <Button 
          className="w-full"
          onClick={() => onAddToCart(item, selectedVariant)}
          disabled={hasVariants && !selectedVariant}
          style={{ backgroundColor: primaryColor }}
          data-testid={`add-to-cart-${product.id}`}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add to Cart
        </Button>
      </CardContent>
    </Card>
  );
}
