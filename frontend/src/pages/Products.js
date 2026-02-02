import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
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
import { formatCurrency } from '../lib/utils';
import { 
  Plus, Package, Shirt, SignpostBig, Sticker, Gift, 
  Edit2, Trash2, X, ChevronDown, ChevronUp 
} from 'lucide-react';
import { toast } from 'sonner';

const categoryOptions = [
  { value: 'apparel', label: 'Apparel', icon: Shirt },
  { value: 'signs', label: 'Signs', icon: SignpostBig },
  { value: 'decals', label: 'Decals', icon: Sticker },
  { value: 'promotional', label: 'Promotional', icon: Gift },
  { value: 'other', label: 'Other', icon: Package },
];

const getCategoryIcon = (category) => {
  const cat = categoryOptions.find(c => c.value === category);
  return cat ? cat.icon : Package;
};

const getCategoryColor = (category) => {
  const colors = {
    apparel: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    signs: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    decals: 'bg-green-500/20 text-green-400 border-green-500/30',
    promotional: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    other: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  };
  return colors[category] || colors.other;
};

export default function Products() {
  const { getProducts, createProduct, updateProduct, deleteProduct } = useApp();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [expandedProduct, setExpandedProduct] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'other',
    base_cost: 0,
    retail_price: 0,
    image_url: '',
    has_variants: false,
    variants: []
  });

  const [newVariant, setNewVariant] = useState({ name: '', size: '', color: '', additional_cost: 0 });

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const data = await getProducts();
      setProducts(data);
    } catch (err) {
      toast.error('Failed to load products');
    }
    setLoading(false);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'other',
      base_cost: 0,
      retail_price: 0,
      image_url: '',
      has_variants: false,
      variants: []
    });
    setNewVariant({ name: '', size: '', color: '', additional_cost: 0 });
    setEditingProduct(null);
  };

  const handleOpenDialog = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name,
        description: product.description || '',
        category: product.category,
        base_cost: product.base_cost,
        retail_price: product.retail_price,
        image_url: product.image_url || '',
        has_variants: product.has_variants,
        variants: product.variants || []
      });
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleAddVariant = () => {
    if (!newVariant.name.trim()) {
      toast.error('Variant name is required');
      return;
    }
    setFormData({
      ...formData,
      variants: [...formData.variants, { ...newVariant, id: `temp-${Date.now()}` }]
    });
    setNewVariant({ name: '', size: '', color: '', additional_cost: 0 });
  };

  const handleRemoveVariant = (index) => {
    const updated = formData.variants.filter((_, i) => i !== index);
    setFormData({ ...formData, variants: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Product name is required');
      return;
    }
    if (formData.base_cost <= 0 || formData.retail_price <= 0) {
      toast.error('Costs must be greater than 0');
      return;
    }

    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, formData);
        toast.success('Product updated');
      } else {
        await createProduct(formData);
        toast.success('Product created');
      }
      setIsDialogOpen(false);
      resetForm();
      await loadProducts();
    } catch (err) {
      toast.error('Failed to save product');
    }
  };

  const handleDelete = async (productId) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await deleteProduct(productId);
      toast.success('Product deleted');
      await loadProducts();
    } catch (err) {
      toast.error('Failed to delete product');
    }
  };

  const filteredProducts = selectedCategory === 'all' 
    ? products 
    : products.filter(p => p.category === selectedCategory);

  const profitMargin = (retail, cost) => {
    if (cost === 0) return 0;
    return ((retail - cost) / retail * 100).toFixed(1);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Product Catalog</h1>
          <p className="text-muted-foreground mt-1">Master catalog of products for all webstores</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={(open) => { if (!open) resetForm(); setIsDialogOpen(open); }}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-product-btn" onClick={() => handleOpenDialog()}>
              <Plus className="h-4 w-4 mr-2" /> Add Product
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">
                {editingProduct ? 'Edit Product' : 'New Product'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2 col-span-2">
                  <Label>Product Name *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Custom Yard Sign 18x24"
                    data-testid="product-name-input"
                  />
                </div>
                <div className="space-y-2 col-span-2">
                  <Label>Description</Label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Product description..."
                    rows={2}
                    data-testid="product-description-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Category *</Label>
                  <Select 
                    value={formData.category} 
                    onValueChange={(val) => setFormData({ ...formData, category: val })}
                  >
                    <SelectTrigger data-testid="product-category-select">
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
                <div className="space-y-2">
                  <Label>Image URL</Label>
                  <Input
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    placeholder="https://..."
                    data-testid="product-image-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Base Cost (Your Cost) *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.base_cost}
                    onChange={(e) => setFormData({ ...formData, base_cost: parseFloat(e.target.value) || 0 })}
                    data-testid="product-cost-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Retail Price *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.retail_price}
                    onChange={(e) => setFormData({ ...formData, retail_price: parseFloat(e.target.value) || 0 })}
                    data-testid="product-price-input"
                  />
                </div>
              </div>

              {/* Profit Preview */}
              {formData.base_cost > 0 && formData.retail_price > 0 && (
                <div className="p-3 bg-muted/30 rounded-lg flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Profit per unit:</span>
                  <span className="font-bold text-green-400">
                    {formatCurrency(formData.retail_price - formData.base_cost)} ({profitMargin(formData.retail_price, formData.base_cost)}%)
                  </span>
                </div>
              )}

              {/* Variants Section */}
              <div className="space-y-3 border-t border-border pt-4">
                <div className="flex items-center justify-between">
                  <Label className="text-base">Product Variants (Size/Color)</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setFormData({ ...formData, has_variants: !formData.has_variants })}
                  >
                    {formData.has_variants ? 'Disable Variants' : 'Enable Variants'}
                  </Button>
                </div>

                {formData.has_variants && (
                  <>
                    {/* Current Variants */}
                    {formData.variants.length > 0 && (
                      <div className="space-y-2">
                        {formData.variants.map((v, idx) => (
                          <div key={v.id || idx} className="flex items-center gap-2 p-2 bg-muted/30 rounded-lg">
                            <span className="flex-1 text-sm">{v.name}</span>
                            {v.size && <Badge variant="outline">{v.size}</Badge>}
                            {v.color && <Badge variant="outline">{v.color}</Badge>}
                            {v.additional_cost > 0 && (
                              <span className="text-xs text-yellow-400">+{formatCurrency(v.additional_cost)}</span>
                            )}
                            <Button 
                              type="button" 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleRemoveVariant(idx)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Add Variant Form */}
                    <div className="grid grid-cols-4 gap-2">
                      <Input
                        placeholder="Variant name"
                        value={newVariant.name}
                        onChange={(e) => setNewVariant({ ...newVariant, name: e.target.value })}
                      />
                      <Input
                        placeholder="Size"
                        value={newVariant.size}
                        onChange={(e) => setNewVariant({ ...newVariant, size: e.target.value })}
                      />
                      <Input
                        placeholder="Color"
                        value={newVariant.color}
                        onChange={(e) => setNewVariant({ ...newVariant, color: e.target.value })}
                      />
                      <div className="flex gap-1">
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="+$"
                          value={newVariant.additional_cost || ''}
                          onChange={(e) => setNewVariant({ ...newVariant, additional_cost: parseFloat(e.target.value) || 0 })}
                          className="w-20"
                        />
                        <Button type="button" size="icon" onClick={handleAddVariant}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => { resetForm(); setIsDialogOpen(false); }}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="product-submit-btn">
                  {editingProduct ? 'Update' : 'Create'} Product
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Category Filter */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList>
          <TabsTrigger value="all" data-testid="filter-all">
            <Package className="h-4 w-4 mr-2" /> All ({products.length})
          </TabsTrigger>
          {categoryOptions.map(cat => {
            const count = products.filter(p => p.category === cat.value).length;
            const Icon = cat.icon;
            return (
              <TabsTrigger key={cat.value} value={cat.value} data-testid={`filter-${cat.value}`}>
                <Icon className="h-4 w-4 mr-2" /> {cat.label} ({count})
              </TabsTrigger>
            );
          })}
        </TabsList>
      </Tabs>

      {/* Products List */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No products yet</p>
              <p className="text-sm mt-1">Add products to your master catalog</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10"></TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Base Cost</TableHead>
                  <TableHead className="text-right">Retail Price</TableHead>
                  <TableHead className="text-right">Profit</TableHead>
                  <TableHead>Variants</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.map((product, idx) => {
                  const Icon = getCategoryIcon(product.category);
                  const isExpanded = expandedProduct === product.id;
                  return (
                    <>
                      <TableRow 
                        key={product.id} 
                        className={idx % 2 === 0 ? '' : 'bg-muted/30'}
                        data-testid={`product-row-${product.id}`}
                      >
                        <TableCell>
                          {product.has_variants && product.variants?.length > 0 && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setExpandedProduct(isExpanded ? null : product.id)}
                            >
                              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </Button>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            {product.image_url ? (
                              <img src={product.image_url} alt={product.name} className="w-10 h-10 rounded object-cover" />
                            ) : (
                              <div className="w-10 h-10 rounded bg-muted/50 flex items-center justify-center">
                                <Icon className="h-5 w-5 text-muted-foreground" />
                              </div>
                            )}
                            <div>
                              <p className="font-medium">{product.name}</p>
                              {product.description && (
                                <p className="text-xs text-muted-foreground line-clamp-1">{product.description}</p>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getCategoryColor(product.category)}>
                            {product.category}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          {formatCurrency(product.base_cost)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(product.retail_price)}
                        </TableCell>
                        <TableCell className="text-right text-green-400 font-bold">
                          {formatCurrency(product.retail_price - product.base_cost)}
                        </TableCell>
                        <TableCell>
                          {product.has_variants && product.variants?.length > 0 ? (
                            <Badge variant="outline">{product.variants.length} variants</Badge>
                          ) : (
                            <span className="text-muted-foreground text-sm">-</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleOpenDialog(product)}
                              data-testid={`edit-product-${product.id}`}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(product.id)}
                              className="text-destructive hover:text-destructive"
                              data-testid={`delete-product-${product.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                      {/* Expanded Variants */}
                      {isExpanded && product.variants?.map((v, vIdx) => (
                        <TableRow key={`${product.id}-${v.id}`} className="bg-muted/10">
                          <TableCell></TableCell>
                          <TableCell className="pl-16">
                            <span className="text-sm text-muted-foreground">↳ {v.name}</span>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              {v.size && <Badge variant="outline" className="text-xs">{v.size}</Badge>}
                              {v.color && <Badge variant="outline" className="text-xs">{v.color}</Badge>}
                            </div>
                          </TableCell>
                          <TableCell className="text-right text-muted-foreground text-sm">
                            {v.additional_cost > 0 ? `+${formatCurrency(v.additional_cost)}` : '-'}
                          </TableCell>
                          <TableCell className="text-right text-sm">
                            {formatCurrency(product.retail_price + (v.additional_cost || 0))}
                          </TableCell>
                          <TableCell></TableCell>
                          <TableCell>
                            <Badge variant={v.is_available !== false ? 'outline' : 'secondary'} className="text-xs">
                              {v.is_available !== false ? 'Available' : 'Unavailable'}
                            </Badge>
                          </TableCell>
                          <TableCell></TableCell>
                        </TableRow>
                      ))}
                    </>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
