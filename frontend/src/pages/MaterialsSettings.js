import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { 
  Loader2, Save, Plus, Trash2, Package, Layers, 
  ArrowLeft, DollarSign, Percent, Edit2, Search
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Material categories
const MATERIAL_CATEGORIES = [
  { value: 'vinyl', label: 'Vinyl & Film' },
  { value: 'print_media', label: 'Print Media' },
  { value: 'laminate', label: 'Laminate' },
  { value: 'substrate', label: 'Substrates & Boards' },
  { value: 'hardware', label: 'Hardware & Mounting' },
  { value: 'supplies', label: 'Supplies & Consumables' },
  { value: 'other', label: 'Other' },
];

// Unit types
const UNIT_TYPES = [
  { value: 'sqft', label: 'per sq ft' },
  { value: 'lnft', label: 'per linear ft' },
  { value: 'each', label: 'each' },
  { value: 'roll', label: 'per roll' },
  { value: 'sheet', label: 'per sheet' },
  { value: 'gallon', label: 'per gallon' },
  { value: 'pack', label: 'per pack' },
];

export default function MaterialsSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [materials, setMaterials] = useState([]);
  const [filteredMaterials, setFilteredMaterials] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showDialog, setShowDialog] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: 'vinyl',
    cost: 0,
    unit: 'sqft',
    markup_percent: 100,
    description: '',
    sku: '',
    supplier: '',
    min_order_qty: 1,
    is_active: true
  });

  const getToken = () => localStorage.getItem('auth_token');

  const fetchMaterials = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pricing/materials/catalog`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setMaterials(data);
        setFilteredMaterials(data);
      }
    } catch (err) {
      console.error('Error fetching materials:', err);
      toast.error('Failed to load materials');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMaterials();
  }, [fetchMaterials]);

  // Filter materials based on search and category
  useEffect(() => {
    let filtered = materials;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m => 
        m.name.toLowerCase().includes(query) ||
        m.description?.toLowerCase().includes(query) ||
        m.sku?.toLowerCase().includes(query)
      );
    }
    
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(m => m.category === categoryFilter);
    }
    
    setFilteredMaterials(filtered);
  }, [materials, searchQuery, categoryFilter]);

  const resetForm = () => {
    setFormData({
      name: '',
      category: 'vinyl',
      cost: 0,
      unit: 'sqft',
      markup_percent: 100,
      description: '',
      sku: '',
      supplier: '',
      min_order_qty: 1,
      is_active: true
    });
    setEditingMaterial(null);
  };

  const handleAdd = () => {
    resetForm();
    setShowDialog(true);
  };

  const handleEdit = (material) => {
    setEditingMaterial(material);
    setFormData({
      name: material.name || '',
      category: material.category || 'vinyl',
      cost: material.cost || 0,
      unit: material.unit || 'sqft',
      markup_percent: material.markup_percent || 100,
      description: material.description || '',
      sku: material.sku || '',
      supplier: material.supplier || '',
      min_order_qty: material.min_order_qty || 1,
      is_active: material.is_active !== false
    });
    setShowDialog(true);
  };

  const handleSave = async () => {
    const token = getToken();
    if (!token) return;

    if (!formData.name.trim()) {
      toast.error('Please enter a material name');
      return;
    }

    setSaving(true);
    try {
      const url = editingMaterial 
        ? `${API_URL}/api/pricing/materials/${editingMaterial.id}`
        : `${API_URL}/api/pricing/materials`;
      
      const method = editingMaterial ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        toast.success(editingMaterial ? 'Material updated!' : 'Material added!');
        setShowDialog(false);
        resetForm();
        fetchMaterials();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to save material');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (materialId) => {
    if (!window.confirm('Are you sure you want to delete this material?')) return;

    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pricing/materials/${materialId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Material deleted');
        fetchMaterials();
      } else {
        toast.error('Failed to delete material');
      }
    } catch (err) {
      toast.error('Network error');
    }
  };

  const handleSeedDefaults = async () => {
    if (!window.confirm('This will add common sign shop materials (vinyl, substrates, hardware, etc.) to get you started. Continue?')) return;

    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/pricing/materials/seed-defaults`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        fetchMaterials();
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to seed materials');
      }
    } catch (err) {
      toast.error('Network error');
    }
  };

  const calculatePrice = (cost, markup) => {
    return (cost * (1 + markup / 100)).toFixed(2);
  };

  const getCategoryLabel = (value) => {
    return MATERIAL_CATEGORIES.find(c => c.value === value)?.label || value;
  };

  const getUnitLabel = (value) => {
    return UNIT_TYPES.find(u => u.value === value)?.label || value;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/settings">
            <Button variant="outline" size="icon" className="border-slate-300 hover:bg-slate-100">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>Materials & Inventory</h1>
            <p className="text-slate-500 mt-1">Manage your materials, supplies, and their costs</p>
          </div>
        </div>
        <Button onClick={handleAdd} className="bg-teal-500 hover:bg-teal-600">
          <Plus className="h-4 w-4 mr-2" />
          Add Material
        </Button>
      </div>

      {/* Filters */}
      <Card className="border border-slate-200">
        <CardContent className="py-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search materials..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {MATERIAL_CATEGORIES.map(cat => (
                  <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Materials List */}
      <div className="grid gap-4">
        {filteredMaterials.length === 0 ? (
          <Card className="border border-slate-200">
            <CardContent className="py-12 text-center">
              <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-600">No materials found</h3>
              <p className="text-slate-400 mt-1">
                {searchQuery || categoryFilter !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'Add your first material to get started'}
              </p>
              {!searchQuery && categoryFilter === 'all' && (
                <div className="flex gap-2 mt-4">
                  <Button onClick={handleAdd} className="bg-teal-500 hover:bg-teal-600">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Material
                  </Button>
                  <Button onClick={handleSeedDefaults} variant="outline">
                    <Package className="h-4 w-4 mr-2" />
                    Load Sign Shop Defaults
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Group by category */}
            {MATERIAL_CATEGORIES.map(category => {
              const categoryMaterials = filteredMaterials.filter(m => m.category === category.value);
              if (categoryMaterials.length === 0) return null;
              
              return (
                <Card key={category.value} className="border border-slate-200">
                  <CardHeader className="py-3 px-4 bg-slate-50">
                    <CardTitle className="text-sm font-medium flex items-center gap-2" style={{ color: '#1A1A1A' }}>
                      <Layers className="h-4 w-4 text-teal-500" />
                      {category.label}
                      <span className="text-slate-400 font-normal">({categoryMaterials.length})</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="divide-y divide-slate-100">
                      {categoryMaterials.map(material => (
                        <div 
                          key={material.id} 
                          className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h4 className="font-medium" style={{ color: '#1A1A1A' }}>{material.name}</h4>
                              {material.sku && (
                                <span className="text-xs px-2 py-0.5 bg-slate-100 rounded text-slate-500">
                                  {material.sku}
                                </span>
                              )}
                              {!material.is_active && (
                                <span className="text-xs px-2 py-0.5 bg-red-100 rounded text-red-600">
                                  Inactive
                                </span>
                              )}
                            </div>
                            {material.description && (
                              <p className="text-sm text-slate-500 mt-1">{material.description}</p>
                            )}
                            {material.supplier && (
                              <p className="text-xs text-slate-400 mt-1">Supplier: {material.supplier}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <p className="text-sm text-slate-500">Cost</p>
                              <p className="font-medium" style={{ color: '#1A1A1A' }}>
                                ${material.cost.toFixed(2)} {getUnitLabel(material.unit)}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-slate-500">Markup</p>
                              <p className="font-medium text-amber-600">
                                {material.markup_percent}%
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-slate-500">Sell Price</p>
                              <p className="font-medium text-green-600">
                                ${calculatePrice(material.cost, material.markup_percent)} {getUnitLabel(material.unit)}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => handleEdit(material)}
                                className="hover:bg-slate-100"
                              >
                                <Edit2 className="h-4 w-4 text-slate-500" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="icon"
                                onClick={() => handleDelete(material.id)}
                                className="hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </>
        )}
      </div>

      {/* Quick Stats */}
      {materials.length > 0 && (
        <Card className="border border-slate-200">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-500">Total Materials</p>
                <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>{materials.length}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-2xl font-bold text-green-600">
                  {materials.filter(m => m.is_active !== false).length}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Categories Used</p>
                <p className="text-2xl font-bold text-teal-600">
                  {new Set(materials.map(m => m.category)).size}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Avg Markup</p>
                <p className="text-2xl font-bold text-amber-600">
                  {materials.length > 0 
                    ? Math.round(materials.reduce((acc, m) => acc + (m.markup_percent || 0), 0) / materials.length)
                    : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingMaterial ? 'Edit Material' : 'Add New Material'}</DialogTitle>
            <DialogDescription>
              {editingMaterial 
                ? 'Update the material details below'
                : 'Add a new material to your inventory with cost and markup information'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label>Material Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., 3M Vinyl 1080"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label>Category</Label>
                <Select 
                  value={formData.category} 
                  onValueChange={(v) => setFormData({ ...formData, category: v })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {MATERIAL_CATEGORIES.map(cat => (
                      <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>SKU / Part #</Label>
                <Input
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  placeholder="Optional"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label>Your Cost *</Label>
                <div className="relative mt-1">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.cost}
                    onChange={(e) => setFormData({ ...formData, cost: parseFloat(e.target.value) || 0 })}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div>
                <Label>Unit</Label>
                <Select 
                  value={formData.unit} 
                  onValueChange={(v) => setFormData({ ...formData, unit: v })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIT_TYPES.map(unit => (
                      <SelectItem key={unit.value} value={unit.value}>{unit.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Markup %</Label>
                <div className="relative mt-1">
                  <Input
                    type="number"
                    value={formData.markup_percent}
                    onChange={(e) => setFormData({ ...formData, markup_percent: parseFloat(e.target.value) || 0 })}
                    className="pr-10"
                  />
                  <Percent className="absolute right-3 top-3 h-4 w-4 text-slate-400" />
                </div>
              </div>
              
              <div>
                <Label>Sell Price</Label>
                <div className="mt-1 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-lg font-semibold text-green-600">
                    ${calculatePrice(formData.cost, formData.markup_percent)} {getUnitLabel(formData.unit)}
                  </p>
                </div>
              </div>
              
              <div className="col-span-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional notes about this material"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label>Supplier</Label>
                <Input
                  value={formData.supplier}
                  onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  placeholder="e.g., Sign Warehouse"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label>Min Order Qty</Label>
                <Input
                  type="number"
                  value={formData.min_order_qty}
                  onChange={(e) => setFormData({ ...formData, min_order_qty: parseInt(e.target.value) || 1 })}
                  className="mt-1"
                  min="1"
                />
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving} className="bg-teal-500 hover:bg-teal-600">
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
              {editingMaterial ? 'Update' : 'Add'} Material
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
