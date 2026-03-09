import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Switch } from '../components/ui/switch';
import {
  Plus, Ticket, Trash2, Edit2, Copy, Check,
  Percent, DollarSign, Clock, Users, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PromoCodes() {
  const [codes, setCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCode, setEditingCode] = useState(null);
  const [copiedCode, setCopiedCode] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    code: '',
    description: '',
    discount_type: 'percent',
    discount_value: 0,
    trial_days: 14,
    max_uses: '',
    expires_at: '',
    is_active: true,
  });

  const fetchCodes = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await axios.get(`${API}/promo-codes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCodes(res.data);
    } catch (err) {
      console.error('Error fetching promo codes:', err);
      toast.error('Failed to load promo codes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCodes();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('auth_token');
    
    try {
      const payload = {
        ...formData,
        code: formData.code.toUpperCase(),
        max_uses: formData.max_uses ? parseInt(formData.max_uses) : null,
        expires_at: formData.expires_at || null,
      };

      if (editingCode) {
        await axios.put(`${API}/promo-codes/${editingCode.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Promo code updated!');
      } else {
        await axios.post(`${API}/promo-codes`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Promo code created!');
      }
      
      setShowModal(false);
      setEditingCode(null);
      resetForm();
      fetchCodes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save promo code');
    }
  };

  const handleDelete = async (codeId) => {
    if (!window.confirm('Are you sure you want to delete this promo code?')) return;
    
    const token = localStorage.getItem('auth_token');
    try {
      await axios.delete(`${API}/promo-codes/${codeId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Promo code deleted');
      fetchCodes();
    } catch (err) {
      toast.error('Failed to delete promo code');
    }
  };

  const handleEdit = (code) => {
    setEditingCode(code);
    setFormData({
      code: code.code,
      description: code.description || '',
      discount_type: code.discount_type,
      discount_value: code.discount_value,
      trial_days: code.trial_days || 14,
      max_uses: code.max_uses || '',
      expires_at: code.expires_at ? code.expires_at.split('T')[0] : '',
      is_active: code.is_active,
    });
    setShowModal(true);
  };

  const resetForm = () => {
    setFormData({
      code: '',
      description: '',
      discount_type: 'percent',
      discount_value: 0,
      trial_days: 14,
      max_uses: '',
      expires_at: '',
      is_active: true,
    });
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast.success('Code copied to clipboard!');
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const getDiscountDisplay = (code) => {
    switch (code.discount_type) {
      case 'percent':
        return `${code.discount_value}% off`;
      case 'fixed':
        return `$${code.discount_value} off`;
      case 'free_trial':
        return `${code.trial_days} days free trial`;
      case 'free_days':
        return `${code.trial_days} days FREE access`;
      default:
        return 'Unknown';
    }
  };

  const getDiscountIcon = (type) => {
    switch (type) {
      case 'percent':
        return <Percent className="h-4 w-4" />;
      case 'fixed':
        return <DollarSign className="h-4 w-4" />;
      case 'free_trial':
        return <Clock className="h-4 w-4" />;
      case 'free_days':
        return <Clock className="h-4 w-4 text-green-500" />;
      default:
        return <Ticket className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }}></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="promo-codes-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-heading text-white">
            Promo Codes
          </h1>
          <p className="text-slate-300">
            Create discount codes for friends and beta testers
          </p>
        </div>
        <Button
          onClick={() => {
            resetForm();
            setEditingCode(null);
            setShowModal(true);
          }}
          className="gap-2"
          style={{ backgroundColor: 'var(--accent)' }}
          data-testid="create-promo-btn"
        >
          <Plus className="h-4 w-4" />
          Create Code
        </Button>
      </div>

      {/* Info Card */}
      <Card style={{ backgroundColor: 'var(--accent-soft)', borderColor: 'var(--accent)' }}>
        <CardContent className="p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 mt-0.5" style={{ color: 'var(--accent)' }} />
          <div>
            <p className="font-medium" style={{ color: 'var(--text)' }}>
              Share these codes with people signing up for SignGuy AI
            </p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Users can enter the code during registration or checkout to receive the discount.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Codes Grid */}
      {codes.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Ticket className="h-12 w-12 mx-auto mb-4" style={{ color: 'var(--text-muted)' }} />
            <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>
              No promo codes yet
            </h3>
            <p style={{ color: 'var(--text-muted)' }}>
              Create your first promo code to share with friends and beta testers.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {codes.map((code) => (
            <Card 
              key={code.id}
              style={{ 
                backgroundColor: 'var(--surface)',
                borderColor: code.is_active ? 'var(--border-light)' : 'var(--text-muted)',
                opacity: code.is_active ? 1 : 0.7
              }}
            >
              <CardContent className="p-5">
                {/* Code Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <div 
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: 'var(--accent-soft)' }}
                    >
                      {getDiscountIcon(code.discount_type)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span 
                          className="font-mono font-bold text-lg"
                          style={{ color: 'var(--text)' }}
                        >
                          {code.code}
                        </span>
                        <button
                          onClick={() => copyCode(code.code)}
                          className="p-1 rounded hover:bg-gray-100 transition-colors"
                          title="Copy code"
                        >
                          {copiedCode === code.code ? (
                            <Check className="h-4 w-4 text-green-500" />
                          ) : (
                            <Copy className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
                          )}
                        </button>
                      </div>
                      <Badge 
                        variant={code.is_active ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {code.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleEdit(code)}
                      className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                      title="Edit"
                    >
                      <Edit2 className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
                    </button>
                    <button
                      onClick={() => handleDelete(code.id)}
                      className="p-2 rounded-lg hover:bg-red-50 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </button>
                  </div>
                </div>

                {/* Discount Display */}
                <div 
                  className="text-2xl font-bold mb-2"
                  style={{ color: 'var(--accent)' }}
                >
                  {getDiscountDisplay(code)}
                </div>

                {code.description && (
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    {code.description}
                  </p>
                )}

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-muted)' }}>
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>
                      {code.times_used}{code.max_uses ? `/${code.max_uses}` : ''} used
                    </span>
                  </div>
                  {code.expires_at && (
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      <span>
                        Expires {new Date(code.expires_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-md" style={{ backgroundColor: 'var(--surface)' }}>
          <DialogHeader>
            <DialogTitle style={{ color: 'var(--text)' }}>
              {editingCode ? 'Edit Promo Code' : 'Create Promo Code'}
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Code */}
            <div>
              <Label style={{ color: 'var(--text)' }}>Code</Label>
              <Input
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                placeholder="FRIEND2024"
                className="font-mono"
                required
                disabled={!!editingCode}
                data-testid="promo-code-input"
              />
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Users will enter this code at checkout
              </p>
            </div>

            {/* Description */}
            <div>
              <Label style={{ color: 'var(--text)' }}>Description (optional)</Label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Special discount for beta testers"
              />
            </div>

            {/* Discount Type */}
            <div>
              <Label style={{ color: 'var(--text)' }}>Discount Type</Label>
              <Select
                value={formData.discount_type}
                onValueChange={(v) => setFormData({ ...formData, discount_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="percent">Percentage Off</SelectItem>
                  <SelectItem value="fixed">Fixed Amount Off</SelectItem>
                  <SelectItem value="free_trial">Free Extended Trial</SelectItem>
                  <SelectItem value="free_days">Free Access (No Payment)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Discount Value */}
            {formData.discount_type !== 'free_trial' && formData.discount_type !== 'free_days' && (
              <div>
                <Label style={{ color: 'var(--text)' }}>
                  {formData.discount_type === 'percent' ? 'Discount Percent' : 'Discount Amount ($)'}
                </Label>
                <Input
                  type="number"
                  value={formData.discount_value}
                  onChange={(e) => setFormData({ ...formData, discount_value: parseFloat(e.target.value) || 0 })}
                  min="0"
                  max={formData.discount_type === 'percent' ? 100 : undefined}
                />
              </div>
            )}

            {/* Trial Days */}
            {formData.discount_type === 'free_trial' && (
              <div>
                <Label style={{ color: 'var(--text)' }}>Free Trial Days</Label>
                <Input
                  type="number"
                  value={formData.trial_days}
                  onChange={(e) => setFormData({ ...formData, trial_days: parseInt(e.target.value) || 14 })}
                  min="1"
                  max="90"
                />
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  Instead of paying $19.99, they get this many days free
                </p>
              </div>
            )}

            {/* Free Days (Full Access) */}
            {formData.discount_type === 'free_days' && (
              <div>
                <Label style={{ color: 'var(--text)' }}>Free Access Days</Label>
                <Input
                  type="number"
                  value={formData.trial_days}
                  onChange={(e) => setFormData({ ...formData, trial_days: parseInt(e.target.value) || 30 })}
                  min="1"
                  max="365"
                />
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  Grants full access for this many days - no payment required. Perfect for friends & family.
                </p>
              </div>
            )}

            {/* Max Uses */}
            <div>
              <Label style={{ color: 'var(--text)' }}>Max Uses (optional)</Label>
              <Input
                type="number"
                value={formData.max_uses}
                onChange={(e) => setFormData({ ...formData, max_uses: e.target.value })}
                placeholder="Unlimited"
                min="1"
              />
            </div>

            {/* Expiration */}
            <div>
              <Label style={{ color: 'var(--text)' }}>Expiration Date (optional)</Label>
              <Input
                type="date"
                value={formData.expires_at}
                onChange={(e) => setFormData({ ...formData, expires_at: e.target.value })}
              />
            </div>

            {/* Active Toggle */}
            <div className="flex items-center justify-between">
              <Label style={{ color: 'var(--text)' }}>Active</Label>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
              <Button type="submit" style={{ backgroundColor: 'var(--accent)' }}>
                {editingCode ? 'Update' : 'Create'} Code
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
