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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { Store, Heart, Building2, Plus, ShoppingCart } from 'lucide-react';
import { toast } from 'sonner';

export default function Webstores() {
  const { 
    createFundraiser, getFundraisers,
    createB2BStore, getB2BStores,
    getWebstoreOrders
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('fundraiser');
  const [fundraisers, setFundraisers] = useState([]);
  const [b2bStores, setB2bStores] = useState([]);
  const [orders, setOrders] = useState([]);
  const [isFundraiserDialogOpen, setIsFundraiserDialogOpen] = useState(false);
  const [isB2BDialogOpen, setIsB2BDialogOpen] = useState(false);

  const [fundraiserForm, setFundraiserForm] = useState({
    name: '',
    goal: 0,
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    organizer: '',
    payout_rules: '',
    products: []
  });

  const [b2bForm, setB2bForm] = useState({
    company_name: '',
    contact_email: '',
    login_password: '',
    discount_percent: 0,
    allowed_products: []
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [fundraiserData, b2bData, ordersData] = await Promise.all([
        getFundraisers(),
        getB2BStores(),
        getWebstoreOrders()
      ]);
      setFundraisers(fundraiserData);
      setB2bStores(b2bData);
      setOrders(ordersData);
    } catch (err) {
      console.error('Error loading webstore data:', err);
    }
    setLoading(false);
  };

  const handleFundraiserSubmit = async (e) => {
    e.preventDefault();
    if (!fundraiserForm.name.trim() || !fundraiserForm.organizer.trim()) {
      toast.error('Please fill in required fields');
      return;
    }
    try {
      await createFundraiser(fundraiserForm);
      toast.success('Fundraiser created');
      setIsFundraiserDialogOpen(false);
      setFundraiserForm({
        name: '',
        goal: 0,
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        organizer: '',
        payout_rules: '',
        products: []
      });
      await loadData();
    } catch (err) {
      toast.error('Failed to create fundraiser');
    }
  };

  const handleB2BSubmit = async (e) => {
    e.preventDefault();
    if (!b2bForm.company_name.trim() || !b2bForm.contact_email.trim() || !b2bForm.login_password.trim()) {
      toast.error('Please fill in required fields');
      return;
    }
    try {
      await createB2BStore(b2bForm);
      toast.success('B2B store created');
      setIsB2BDialogOpen(false);
      setB2bForm({
        company_name: '',
        contact_email: '',
        login_password: '',
        discount_percent: 0,
        allowed_products: []
      });
      await loadData();
    } catch (err) {
      toast.error('Failed to create B2B store');
    }
  };

  const fundraiserOrders = orders.filter(o => o.store_type === 'fundraiser');
  const b2bOrders = orders.filter(o => o.store_type === 'b2b');

  return (
    <div className="space-y-6 animate-fade-in" data-testid="webstores-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Webstores</h1>
        <p className="text-muted-foreground mt-1">Manage fundraiser campaigns and B2B stores</p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="fundraiser" data-testid="tab-fundraiser">
            <Heart className="h-4 w-4 mr-2" /> Fundraisers
          </TabsTrigger>
          <TabsTrigger value="b2b" data-testid="tab-b2b">
            <Building2 className="h-4 w-4 mr-2" /> B2B Stores
          </TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">
            <ShoppingCart className="h-4 w-4 mr-2" /> Orders ({orders.length})
          </TabsTrigger>
        </TabsList>

        {/* Fundraiser Tab */}
        <TabsContent value="fundraiser" className="mt-4 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold font-heading uppercase">Fundraiser Campaigns</h2>
            <Dialog open={isFundraiserDialogOpen} onOpenChange={setIsFundraiserDialogOpen}>
              <DialogTrigger asChild>
                <Button className="neon-glow" data-testid="add-fundraiser-btn">
                  <Plus className="h-4 w-4 mr-2" /> New Campaign
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle className="font-heading uppercase">New Fundraiser</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleFundraiserSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Campaign Name *</Label>
                    <Input
                      value={fundraiserForm.name}
                      onChange={(e) => setFundraiserForm({ ...fundraiserForm, name: e.target.value })}
                      placeholder="e.g., Spring Sports Fundraiser"
                      data-testid="fundraiser-name-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Goal Amount</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={fundraiserForm.goal}
                        onChange={(e) => setFundraiserForm({ ...fundraiserForm, goal: parseFloat(e.target.value) || 0 })}
                        data-testid="fundraiser-goal-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Organizer *</Label>
                      <Input
                        value={fundraiserForm.organizer}
                        onChange={(e) => setFundraiserForm({ ...fundraiserForm, organizer: e.target.value })}
                        placeholder="Organization name"
                        data-testid="fundraiser-organizer-input"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Start Date</Label>
                      <Input
                        type="date"
                        value={fundraiserForm.start_date}
                        onChange={(e) => setFundraiserForm({ ...fundraiserForm, start_date: e.target.value })}
                        data-testid="fundraiser-start-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>End Date</Label>
                      <Input
                        type="date"
                        value={fundraiserForm.end_date}
                        onChange={(e) => setFundraiserForm({ ...fundraiserForm, end_date: e.target.value })}
                        data-testid="fundraiser-end-input"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Payout Rules</Label>
                    <Textarea
                      value={fundraiserForm.payout_rules}
                      onChange={(e) => setFundraiserForm({ ...fundraiserForm, payout_rules: e.target.value })}
                      placeholder="Describe how proceeds will be distributed"
                      rows={3}
                      data-testid="fundraiser-payout-input"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" onClick={() => setIsFundraiserDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="fundraiser-submit-btn">Create</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : fundraisers.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Heart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No fundraiser campaigns yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Campaign</TableHead>
                      <TableHead>Organizer</TableHead>
                      <TableHead>Goal</TableHead>
                      <TableHead>Raised</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Dates</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fundraisers.map((campaign, idx) => (
                      <TableRow 
                        key={campaign.id} 
                        className={idx % 2 === 0 ? '' : 'bg-muted/30'}
                        data-testid={`fundraiser-row-${campaign.id}`}
                      >
                        <TableCell className="font-medium">{campaign.name}</TableCell>
                        <TableCell>{campaign.organizer}</TableCell>
                        <TableCell>{formatCurrency(campaign.goal)}</TableCell>
                        <TableCell className="text-primary font-bold">
                          {formatCurrency(campaign.total_raised)}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(campaign.status)}>
                            {campaign.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(campaign.start_date)} - {formatDate(campaign.end_date)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* B2B Tab */}
        <TabsContent value="b2b" className="mt-4 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold font-heading uppercase">B2B Custom Stores</h2>
            <Dialog open={isB2BDialogOpen} onOpenChange={setIsB2BDialogOpen}>
              <DialogTrigger asChild>
                <Button className="neon-glow" data-testid="add-b2b-btn">
                  <Plus className="h-4 w-4 mr-2" /> New B2B Store
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle className="font-heading uppercase">New B2B Store</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleB2BSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label>Company Name *</Label>
                    <Input
                      value={b2bForm.company_name}
                      onChange={(e) => setB2bForm({ ...b2bForm, company_name: e.target.value })}
                      placeholder="Client's company name"
                      data-testid="b2b-company-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Contact Email *</Label>
                    <Input
                      type="email"
                      value={b2bForm.contact_email}
                      onChange={(e) => setB2bForm({ ...b2bForm, contact_email: e.target.value })}
                      placeholder="email@company.com"
                      data-testid="b2b-email-input"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Login Password *</Label>
                      <Input
                        type="password"
                        value={b2bForm.login_password}
                        onChange={(e) => setB2bForm({ ...b2bForm, login_password: e.target.value })}
                        placeholder="Store access password"
                        data-testid="b2b-password-input"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Discount %</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={b2bForm.discount_percent}
                        onChange={(e) => setB2bForm({ ...b2bForm, discount_percent: parseFloat(e.target.value) || 0 })}
                        data-testid="b2b-discount-input"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" onClick={() => setIsB2BDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="b2b-submit-btn">Create</Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : b2bStores.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No B2B stores yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Discount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {b2bStores.map((store, idx) => (
                      <TableRow 
                        key={store.id} 
                        className={idx % 2 === 0 ? '' : 'bg-muted/30'}
                        data-testid={`b2b-row-${store.id}`}
                      >
                        <TableCell className="font-medium">{store.company_name}</TableCell>
                        <TableCell>{store.contact_email}</TableCell>
                        <TableCell>{store.discount_percent}%</TableCell>
                        <TableCell>
                          <Badge className={store.is_active ? getStatusColor('active') : getStatusColor('inactive')}>
                            {store.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(store.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders" className="mt-4 space-y-4">
          <h2 className="text-xl font-bold font-heading uppercase">All Orders</h2>
          
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
                      <TableHead>Type</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Job</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order, idx) => (
                      <TableRow 
                        key={order.id} 
                        className={idx % 2 === 0 ? '' : 'bg-muted/30'}
                      >
                        <TableCell className="font-mono text-sm">#{order.id.slice(0, 8)}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {order.store_type}
                          </Badge>
                        </TableCell>
                        <TableCell>{order.items.length} items</TableCell>
                        <TableCell className="font-bold">{formatCurrency(order.total)}</TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(order.status)}>
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {order.job_id ? `#${order.job_id.slice(0, 8)}` : '-'}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(order.created_at)}
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
    </div>
  );
}
