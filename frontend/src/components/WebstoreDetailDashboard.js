import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate } from '../lib/utils';
import { 
  TrendingUp, ShoppingCart, DollarSign, Package, Clock, 
  ArrowUpRight, ArrowDownRight, Target, Calendar, Wallet,
  BarChart3, Users
} from 'lucide-react';
import { toast } from 'sonner';
import WebstoreOwnerConnectCard from './WebstoreOwnerConnectCard';

// Simple bar chart component
const SimpleBarChart = ({ data, maxValue }) => {
  if (!data || data.length === 0) return <p className="text-muted-foreground text-sm">No data</p>;
  
  const max = maxValue || Math.max(...data.map(d => d.amount));
  
  return (
    <div className="flex items-end gap-1 h-32">
      {data.slice(-14).map((item, idx) => {
        const height = max > 0 ? (item.amount / max) * 100 : 0;
        return (
          <div key={idx} className="flex-1 flex flex-col items-center group">
            <div className="w-full relative">
              <div 
                className="w-full bg-[#2F8BFB] rounded-t transition-all hover:bg-[#2F8BFB]/80"
                style={{ height: `${Math.max(height, 2)}px` }}
              />
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover border rounded px-2 py-1 text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                {formatCurrency(item.amount)}
                <br />
                <span className="text-muted-foreground">{item.date?.slice(5)}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default function WebstoreDetailDashboard({ store, onClose }) {
  const { getWebstoreAnalytics, getWebstoreOrdersV2, recordPayout, getWebstorePayouts } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [storeOrders, setStoreOrders] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [payoutAmount, setPayoutAmount] = useState('');
  const [payoutNotes, setPayoutNotes] = useState('');
  const [submittingPayout, setSubmittingPayout] = useState(false);

  useEffect(() => {
    if (store?.id) {
      loadAnalytics();
    }
  }, [store?.id]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [analyticsData, ordersData, payoutsData] = await Promise.all([
        getWebstoreAnalytics(store.id),
        getWebstoreOrdersV2({ webstore_id: store.id }),
        getWebstorePayouts(store.id)
      ]);
      setAnalytics(analyticsData);
      setStoreOrders(ordersData);
      setPayouts(payoutsData);
    } catch (err) {
      console.error('Error loading analytics:', err);
      toast.error('Failed to load store analytics');
    }
    setLoading(false);
  };

  const handleRecordPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    
    setSubmittingPayout(true);
    try {
      await recordPayout(store.id, amount, payoutNotes || null);
      toast.success('Payout recorded successfully');
      setPayoutAmount('');
      setPayoutNotes('');
      await loadAnalytics();
    } catch (err) {
      toast.error('Failed to record payout');
    }
    setSubmittingPayout(false);
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      processing: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      production: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
      shipped: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
      completed: 'bg-green-500/20 text-green-400 border-green-500/30',
      cancelled: 'bg-red-500/20 text-red-400 border-red-500/30',
    };
    return colors[status] || 'bg-gray-500/20 text-gray-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#2F8BFB]"></div>
      </div>
    );
  }

  if (!analytics) {
    return <p className="text-center py-8 text-muted-foreground">Failed to load analytics</p>;
  }

  const { summary, payout_info, sales_by_day, top_products, fundraiser_metrics } = analytics;

  return (
    <div className="space-y-6" data-testid="webstore-dashboard">
      {/* Owner Stripe Connect — gate for activating the store */}
      <WebstoreOwnerConnectCard webstore={store} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Total Revenue</p>
                <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>
                  {formatCurrency(summary.total_revenue)}
                </p>
              </div>
              <DollarSign className="h-8 w-8" style={{ color: '#10b981' }} />
            </div>
          </CardContent>
        </Card>
        
        <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Total Orders</p>
                <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>
                  {summary.total_orders}
                </p>
                <p className="text-xs" style={{ color: '#5A5A5A' }}>
                  {summary.pending_orders} pending
                </p>
              </div>
              <ShoppingCart className="h-8 w-8" style={{ color: '#2F8BFB' }} />
            </div>
          </CardContent>
        </Card>
        
        <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Shop Profit</p>
                <p className="text-2xl font-bold" style={{ color: '#10b981' }}>
                  {formatCurrency(summary.shop_profit)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8" style={{ color: '#10b981' }} />
            </div>
          </CardContent>
        </Card>
        
        <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Avg Order Value</p>
                <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>
                  {formatCurrency(summary.avg_order_value)}
                </p>
              </div>
              <BarChart3 className="h-8 w-8" style={{ color: '#2F8BFB' }} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fundraiser Progress (if applicable) */}
      {fundraiser_metrics && (
        <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2" style={{ color: '#1A1A1A' }}>
              <Target className="h-5 w-5" style={{ color: '#2F8BFB' }} />
              Fundraiser Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-3xl font-bold" style={{ color: '#2F8BFB' }}>
                    {formatCurrency(fundraiser_metrics.raised)}
                  </p>
                  <p className="text-sm" style={{ color: '#5A5A5A' }}>
                    raised of {formatCurrency(fundraiser_metrics.goal)} goal
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>
                    {fundraiser_metrics.progress_percent.toFixed(1)}%
                  </p>
                  {fundraiser_metrics.days_remaining !== null && (
                    <p className="text-sm" style={{ color: '#5A5A5A' }}>
                      <Calendar className="h-3 w-3 inline mr-1" />
                      {fundraiser_metrics.days_remaining} days left
                    </p>
                  )}
                </div>
              </div>
              <Progress 
                value={fundraiser_metrics.progress_percent} 
                className="h-4"
              />
              <div className="flex justify-between text-sm" style={{ color: '#5A5A5A' }}>
                <span>Fundraiser gets {fundraiser_metrics.profit_percent}% of profit</span>
                <span>Shop keeps {100 - fundraiser_metrics.profit_percent}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs for different views */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-analytics-overview">
            <BarChart3 className="h-4 w-4 mr-2" /> Analytics
          </TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-analytics-orders">
            <ShoppingCart className="h-4 w-4 mr-2" /> Orders ({storeOrders.length})
          </TabsTrigger>
          <TabsTrigger value="payouts" data-testid="tab-analytics-payouts">
            <Wallet className="h-4 w-4 mr-2" /> Payouts
          </TabsTrigger>
        </TabsList>

        {/* Analytics Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sales Chart */}
            <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg" style={{ color: '#1A1A1A' }}>
                  Sales Trend (Last 14 Days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBarChart 
                  data={sales_by_day} 
                  maxValue={Math.max(...(sales_by_day?.map(d => d.amount) || [0]))}
                />
              </CardContent>
            </Card>

            {/* Top Products */}
            <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg" style={{ color: '#1A1A1A' }}>
                  Top Products
                </CardTitle>
              </CardHeader>
              <CardContent>
                {top_products?.length > 0 ? (
                  <div className="space-y-3">
                    {top_products.slice(0, 5).map((product, idx) => (
                      <div 
                        key={product.product_id} 
                        className="flex items-center justify-between p-2 rounded"
                        style={{ background: '#F5F7FA' }}
                      >
                        <div className="flex items-center gap-3">
                          <span 
                            className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                            style={{ 
                              background: idx === 0 ? '#2F8BFB' : '#D7DCE2',
                              color: idx === 0 ? '#fff' : '#1A1A1A'
                            }}
                          >
                            {idx + 1}
                          </span>
                          <div>
                            <p className="font-medium text-sm" style={{ color: '#1A1A1A' }}>
                              {product.name}
                            </p>
                            <p className="text-xs" style={{ color: '#5A5A5A' }}>
                              {product.quantity} sold
                            </p>
                          </div>
                        </div>
                        <p className="font-bold" style={{ color: '#10b981' }}>
                          {formatCurrency(product.revenue)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center py-4" style={{ color: '#5A5A5A' }}>No products sold yet</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Order Status Breakdown */}
          <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg" style={{ color: '#1A1A1A' }}>
                Order Status Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg text-center" style={{ background: '#fef3c7' }}>
                  <Clock className="h-6 w-6 mx-auto mb-2" style={{ color: '#d97706' }} />
                  <p className="text-2xl font-bold" style={{ color: '#d97706' }}>{summary.pending_orders}</p>
                  <p className="text-sm" style={{ color: '#92400e' }}>Pending</p>
                </div>
                <div className="p-4 rounded-lg text-center" style={{ background: '#dbeafe' }}>
                  <Package className="h-6 w-6 mx-auto mb-2" style={{ color: '#2563eb' }} />
                  <p className="text-2xl font-bold" style={{ color: '#2563eb' }}>{summary.processing_orders}</p>
                  <p className="text-sm" style={{ color: '#1e40af' }}>Processing</p>
                </div>
                <div className="p-4 rounded-lg text-center" style={{ background: '#d1fae5' }}>
                  <TrendingUp className="h-6 w-6 mx-auto mb-2" style={{ color: '#059669' }} />
                  <p className="text-2xl font-bold" style={{ color: '#059669' }}>{summary.completed_orders}</p>
                  <p className="text-sm" style={{ color: '#047857' }}>Completed</p>
                </div>
                <div className="p-4 rounded-lg text-center" style={{ background: '#F5F7FA' }}>
                  <ShoppingCart className="h-6 w-6 mx-auto mb-2" style={{ color: '#1A1A1A' }} />
                  <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>{summary.total_orders}</p>
                  <p className="text-sm" style={{ color: '#5A5A5A' }}>Total</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders" className="mt-4">
          <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
            <CardContent className="p-0">
              {storeOrders.length === 0 ? (
                <div className="text-center py-12" style={{ color: '#5A5A5A' }}>
                  <ShoppingCart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No orders yet for this store</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order #</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {storeOrders.map((order, idx) => (
                      <TableRow 
                        key={order.id} 
                        style={{ background: idx % 2 === 0 ? '#FFFFFF' : '#F5F7FA' }}
                      >
                        <TableCell className="font-mono text-sm">
                          #{order.id.slice(0, 8)}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium" style={{ color: '#1A1A1A' }}>{order.customer_name}</p>
                            <p className="text-xs" style={{ color: '#5A5A5A' }}>{order.customer_email}</p>
                          </div>
                        </TableCell>
                        <TableCell>{order.items?.length || 0} items</TableCell>
                        <TableCell className="text-right font-bold" style={{ color: '#1A1A1A' }}>
                          {formatCurrency(order.total)}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(order.status)}>
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell style={{ color: '#5A5A5A' }}>
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

        {/* Payouts Tab */}
        <TabsContent value="payouts" className="mt-4 space-y-6">
          {/* Payout Summary */}
          <div className="grid grid-cols-3 gap-4">
            <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
              <CardContent className="p-4 text-center">
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Total Earned</p>
                <p className="text-2xl font-bold" style={{ color: '#1A1A1A' }}>
                  {formatCurrency(payout_info.total_earned)}
                </p>
              </CardContent>
            </Card>
            <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
              <CardContent className="p-4 text-center">
                <p className="text-sm" style={{ color: '#5A5A5A' }}>Total Paid Out</p>
                <p className="text-2xl font-bold" style={{ color: '#10b981' }}>
                  {formatCurrency(payout_info.total_paid_out)}
                </p>
              </CardContent>
            </Card>
            <Card style={{ background: payout_info.balance_owed > 0 ? '#fef3c7' : '#d1fae5', borderColor: payout_info.balance_owed > 0 ? '#d97706' : '#059669' }}>
              <CardContent className="p-4 text-center">
                <p className="text-sm" style={{ color: payout_info.balance_owed > 0 ? '#92400e' : '#047857' }}>
                  Balance Owed
                </p>
                <p className="text-2xl font-bold" style={{ color: payout_info.balance_owed > 0 ? '#d97706' : '#059669' }}>
                  {formatCurrency(payout_info.balance_owed)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Record Payout Form */}
          {payout_info.balance_owed > 0 && (
            <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg" style={{ color: '#1A1A1A' }}>
                  Record Payout
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="text-sm mb-1 block" style={{ color: '#5A5A5A' }}>Amount</label>
                    <input
                      type="number"
                      value={payoutAmount}
                      onChange={(e) => setPayoutAmount(e.target.value)}
                      placeholder={`Max: ${formatCurrency(payout_info.balance_owed)}`}
                      className="w-full px-3 py-2 rounded border"
                      style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}
                      data-testid="payout-amount-input"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-sm mb-1 block" style={{ color: '#5A5A5A' }}>Notes (optional)</label>
                    <input
                      type="text"
                      value={payoutNotes}
                      onChange={(e) => setPayoutNotes(e.target.value)}
                      placeholder="e.g., Check #1234"
                      className="w-full px-3 py-2 rounded border"
                      style={{ borderColor: '#D7DCE2', background: '#FFFFFF' }}
                    />
                  </div>
                  <Button 
                    onClick={handleRecordPayout}
                    disabled={submittingPayout}
                    style={{ background: '#2F8BFB' }}
                    className="text-white"
                    data-testid="record-payout-btn"
                  >
                    {submittingPayout ? 'Recording...' : 'Record Payout'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Payout History */}
          <Card style={{ background: '#FFFFFF', borderColor: '#D7DCE2' }}>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg" style={{ color: '#1A1A1A' }}>
                Payout History
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {payouts.length === 0 ? (
                <div className="text-center py-8" style={{ color: '#5A5A5A' }}>
                  <Wallet className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No payouts recorded yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payouts.map((payout, idx) => (
                      <TableRow 
                        key={payout.id || idx}
                        style={{ background: idx % 2 === 0 ? '#FFFFFF' : '#F5F7FA' }}
                      >
                        <TableCell style={{ color: '#5A5A5A' }}>
                          {formatDate(payout.created_at)}
                        </TableCell>
                        <TableCell className="text-right font-bold" style={{ color: '#10b981' }}>
                          {formatCurrency(payout.amount)}
                        </TableCell>
                        <TableCell style={{ color: '#5A5A5A' }}>
                          {payout.notes || '-'}
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
