import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { formatCurrency } from '../lib/utils';
import { TrendingUp, ShoppingCart, DollarSign, Package, BarChart3 } from 'lucide-react';

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
  const { getWebstoreAnalytics } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (store?.id) {
      loadAnalytics();
    }
  }, [store?.id]);

  const loadAnalytics = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await getWebstoreAnalytics(store.id);
      setAnalytics(data || null);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setAnalytics(null);
      const detail = err?.response?.data?.detail;
      setLoadError(typeof detail === 'string' ? detail : 'Failed to load store analytics');
    } finally {
      setLoading(false);
    }
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
    // Surface an explicit, retry-able error instead of a generic empty state.
    // Previously this rendered a single "Failed to load analytics" line which
    // looked indistinguishable from a healthy empty-store state.
    return (
      <div
        className="rounded-md border p-6 text-center space-y-3"
        style={{ background: '#FEF2F2', borderColor: '#FCA5A5' }}
        data-testid="webstore-analytics-error"
      >
        <p className="text-sm font-semibold" style={{ color: '#991B1B' }}>
          Couldn't load analytics for this store
        </p>
        <p className="text-xs" style={{ color: '#7F1D1D' }}>
          {loadError || 'The analytics request failed. Other store data may be unavailable until this loads.'}
        </p>
        <Button
          size="sm"
          onClick={loadAnalytics}
          style={{ background: '#2F8BFB' }}
          className="text-white"
          data-testid="webstore-analytics-retry-btn"
        >
          Retry
        </Button>
      </div>
    );
  }

  // Defensive defaults — the analytics endpoint normally returns all of
  // these fields, but if a future schema change drops one we want the
  // dashboard to render an empty card instead of crashing on
  // `undefined.toFixed` / `undefined.total_revenue` etc.
  const summary = analytics.summary || {};
  const payout_info = analytics.payout_info || {};
  const sales_by_day = Array.isArray(analytics.sales_by_day) ? analytics.sales_by_day : [];
  const top_products = Array.isArray(analytics.top_products) ? analytics.top_products : [];
  const fundraiser_metrics = analytics.fundraiser_metrics || null;

  // Backend currently returns payout_info as
  //   { total_owed, total_paid, pending_payout, commission_rate }
  // Older UI code expected { total_earned, total_paid_out, balance_owed }
  // which silently rendered $0 everywhere — a classic hidden-failure
  // state. Map both shapes so the cards always reflect real numbers.
  const payout_total_paid = Number(payout_info.total_paid_out ?? payout_info.total_paid ?? 0);
  const payout_balance_owed = Number(payout_info.balance_owed ?? payout_info.total_owed ?? 0);
  const payout_total_earned = Number(
    payout_info.total_earned ?? (payout_total_paid + payout_balance_owed),
  );

  return (
    <div className="space-y-6" data-testid="webstore-dashboard">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-2xl font-bold">{formatCurrency(summary.total_revenue)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Orders</p>
                <p className="text-2xl font-bold">{summary.total_orders}</p>
                <p className="text-xs text-muted-foreground">{summary.pending_orders} pending</p>
              </div>
              <ShoppingCart className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg. Order Value</p>
                <p className="text-2xl font-bold">{formatCurrency(summary.average_order_value)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Products Sold</p>
                <p className="text-2xl font-bold">{summary.total_items_sold}</p>
              </div>
              <Package className="h-8 w-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sales Chart + Top Products */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Sales Trend (Last 14 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleBarChart
              data={sales_by_day}
              maxValue={Math.max(...(sales_by_day?.map(d => d.amount) || [0]))}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Top Products</CardTitle>
          </CardHeader>
          <CardContent>
            {top_products?.length > 0 ? (
              <div className="space-y-3">
                {top_products.slice(0, 5).map((product, idx) => (
                  <div key={product.product_id} className="flex items-center justify-between p-2 rounded bg-muted/40">
                    <div className="flex items-center gap-3">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${idx === 0 ? 'bg-blue-500 text-white' : 'bg-muted text-foreground'}`}>
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-sm">{product.name}</p>
                        <p className="text-xs text-muted-foreground">{product.quantity} sold</p>
                      </div>
                    </div>
                    <p className="font-bold text-emerald-600">{formatCurrency(product.revenue)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center py-4 text-muted-foreground text-sm">No products sold yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Order Status Breakdown */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-blue-500" />
            Order Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg text-center bg-amber-50">
              <p className="text-2xl font-bold text-amber-600">{summary.pending_orders}</p>
              <p className="text-xs text-amber-800">Pending</p>
            </div>
            <div className="p-3 rounded-lg text-center bg-blue-50">
              <p className="text-2xl font-bold text-blue-600">{summary.processing_orders}</p>
              <p className="text-xs text-blue-800">Processing</p>
            </div>
            <div className="p-3 rounded-lg text-center bg-emerald-50">
              <p className="text-2xl font-bold text-emerald-600">{summary.completed_orders}</p>
              <p className="text-xs text-emerald-800">Completed</p>
            </div>
            <div className="p-3 rounded-lg text-center bg-muted/40">
              <p className="text-2xl font-bold">{summary.total_orders}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Fundraiser Metrics */}
      {fundraiser_metrics && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Fundraiser Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-3xl font-bold text-blue-600">{formatCurrency(fundraiser_metrics.raised)}</p>
                <p className="text-sm text-muted-foreground">raised of {formatCurrency(fundraiser_metrics.goal)} goal</p>
              </div>
              <p className="text-2xl font-bold">{(Number(fundraiser_metrics.progress_percent) || 0).toFixed(1)}%</p>
            </div>
            <Progress value={fundraiser_metrics.progress_percent} className="h-3" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
