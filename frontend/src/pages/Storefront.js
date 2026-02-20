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
  
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: '',
    shipping_address: '',
    notes: ''
  });

  useEffect(() => {
    loadStore();
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

  const handleCheckout = async (e) => {
    e.preventDefault();
    if (!customerInfo.name || !customerInfo.email) {
      toast.error('Name and email are required');
      return;
    }
    if (cart.length === 0) {
      toast.error('Cart is empty');
      return;
    }

    try {
      const orderData = {
        webstore_id: storeId,
        customer_name: customerInfo.name,
        customer_email: customerInfo.email,
        customer_phone: customerInfo.phone,
        shipping_address: customerInfo.shipping_address,
        items: cart.map(item => ({
          product_id: item.product_id,
          variant_id: item.variant_id,
          quantity: item.quantity
        })),
        tax: 0,
        shipping: 0,
        notes: customerInfo.notes
      };

      const res = await fetch(`${API}/api/webstores/v2/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      if (!res.ok) throw new Error('Failed to place order');
      
      setOrderPlaced(true);
      setCart([]);
      setIsCheckoutOpen(false);
      toast.success('Order placed successfully!');
    } catch (err) {
      toast.error('Failed to place order');
    }
  };

  const getStoreTypeIcon = (type) => {
    switch (type) {
      case 'business': return Building2;
      case 'fundraiser': return Heart;
      case 'creator': return User;
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
  const bannerUrl = store.branding?.banner_url || store.banner_image_data;
  const logoUrl = store.branding?.logo_url || store.logo_image_data;

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
      {(store.description || store.store_type === 'fundraiser') && (
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

            {/* Order Summary */}
            <div className="p-4 bg-muted/30 rounded-lg">
              <h4 className="font-medium mb-2">Order Summary</h4>
              <div className="space-y-1 text-sm">
                {cart.map(item => (
                  <div key={item.cartItemId} className="flex justify-between">
                    <span>{item.name} {item.variant_name && `(${item.variant_name})`} x{item.quantity}</span>
                    <span>{formatCurrency(item.price * item.quantity)}</span>
                  </div>
                ))}
              </div>
              <Separator className="my-2" />
              <div className="flex justify-between font-bold">
                <span>Total</span>
                <span style={{ color: primaryColor }}>{formatCurrency(cartTotal)}</span>
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
                data-testid="place-order-button"
              >
                Place Order
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
