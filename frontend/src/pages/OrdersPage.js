import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Package, Clock, ChevronRight, Filter, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const token = () => localStorage.getItem('auth_token');

const STATUS_COLORS = {
  new_intake: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  awaiting_review: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  awaiting_quote: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  quote_sent: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  awaiting_approval: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  approved: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
  in_production: 'bg-violet-500/15 text-violet-400 border-violet-500/30',
  partially_complete: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  ready_for_pickup: 'bg-green-500/15 text-green-400 border-green-500/30',
  out_for_delivery: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  completed: 'bg-green-600/15 text-green-300 border-green-600/30',
  on_hold: 'bg-red-500/15 text-red-400 border-red-500/30',
  cancelled: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
};

const PRIORITY_COLORS = {
  rush: 'bg-red-500 text-white',
  urgent: 'bg-orange-500 text-white',
  high: 'bg-amber-500 text-black',
  normal: 'bg-slate-600 text-slate-200',
};

const formatStatus = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function OrdersPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchOrders = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter !== 'all') params.set('status', statusFilter);
      params.set('limit', '50');
      const res = await axios.get(`${API}/orders?${params}`, { headers: { Authorization: `Bearer ${token()}` } });
      setOrders(res.data.orders);
      setTotal(res.data.total);
    } catch {
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOrders(); }, [search, statusFilter]);

  const handleCreateOrder = () => navigate('/orders/new');

  return (
    <div className="space-y-5" data-testid="orders-page">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading">Orders</h1>
          <p className="text-slate-400 text-sm mt-1">{total} order{total !== 1 ? 's' : ''}</p>
        </div>
        <Button onClick={handleCreateOrder} className="bg-violet-600 hover:bg-violet-700 text-white gap-2" data-testid="create-order-btn">
          <Plus className="w-4 h-4" /> New Order
        </Button>
      </div>

      <div className="flex gap-3 items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search orders..."
            className="pl-10 bg-[#0B0F17] border-slate-700 text-white"
            data-testid="orders-search"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48 bg-[#0B0F17] border-slate-700 text-white" data-testid="orders-status-filter">
            <Filter className="w-4 h-4 mr-2 text-slate-400" />
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="new_intake">New Intake</SelectItem>
            <SelectItem value="awaiting_review">Awaiting Review</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="in_production">In Production</SelectItem>
            <SelectItem value="partially_complete">Partially Complete</SelectItem>
            <SelectItem value="ready_for_pickup">Ready for Pickup</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500"></div>
        </div>
      ) : orders.length === 0 ? (
        <Card className="bg-[#111826] border-slate-700">
          <CardContent className="py-16 text-center">
            <Package className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <h3 className="text-lg font-semibold text-white mb-2">No orders yet</h3>
            <p className="text-slate-400 mb-6">Create your first order to start tracking jobs, quotes, and production.</p>
            <Button onClick={handleCreateOrder} className="bg-violet-600 hover:bg-violet-700 text-white gap-2">
              <Plus className="w-4 h-4" /> Create First Order
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Card
              key={order.id}
              className="bg-[#111826] border-slate-700 hover:border-violet-500/40 transition-colors cursor-pointer"
              onClick={() => navigate(`/orders/${order.id}`)}
              data-testid={`order-row-${order.order_number}`}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="w-12 h-12 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-violet-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-white text-sm">{order.order_number}</span>
                        <Badge variant="outline" className={STATUS_COLORS[order.status] || STATUS_COLORS.new_intake}>
                          {formatStatus(order.status)}
                        </Badge>
                      </div>
                      <p className="text-white font-medium mt-0.5 truncate">{order.customer_name || 'No customer'}</p>
                      <p className="text-slate-500 text-xs mt-0.5">{order.company_name}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 flex-shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-slate-500">Total</p>
                      <p className="text-lg font-bold text-white">${(order.order_total || 0).toFixed(2)}</p>
                    </div>
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-slate-500">Tickets</p>
                      <p className="text-lg font-bold text-white">{order.job_ticket_count || 0}</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className="text-xs text-slate-500">Progress</p>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div className="h-full bg-violet-500 rounded-full transition-all" style={{ width: `${order.overall_progress || 0}%` }} />
                        </div>
                        <span className="text-sm text-white font-medium">{Math.round(order.overall_progress || 0)}%</span>
                      </div>
                    </div>
                    <div className="text-right hidden lg:block">
                      <p className="text-xs text-slate-500">Due</p>
                      <p className="text-sm text-white">{order.requested_due_date ? new Date(order.requested_due_date).toLocaleDateString() : '-'}</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
