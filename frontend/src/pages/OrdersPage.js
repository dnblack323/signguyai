import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Package, Clock, ChevronRight, Filter, AlertTriangle, Eye, Edit3, Trash2, MoreHorizontal, CheckSquare, Square, Archive, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const token = () => localStorage.getItem('auth_token');

const STATUS_COLORS = {
  draft: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
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
  cancelled: 'bg-slate-500/15 text-gray-500 border-slate-500/30',
};

const PRIORITY_COLORS = {
  rush: 'bg-red-500 text-gray-900',
  urgent: 'bg-orange-500 text-gray-900',
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
  const [selectedOrders, setSelectedOrders] = useState(new Set());
  const [bulkActioning, setBulkActioning] = useState(false);

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

  const handleDeleteOrder = async (e, orderId, orderNumber) => {
    e.stopPropagation();
    if (!window.confirm(`Delete order ${orderNumber}? This will also delete all related tickets and tasks.`)) return;
    try {
      await axios.delete(`${API}/orders/${orderId}`, { headers: { Authorization: `Bearer ${token()}` } });
      toast.success('Order deleted');
      fetchOrders();
    } catch {
      toast.error('Failed to delete order');
    }
  };

  // Bulk selection handlers
  const toggleSelectOrder = (orderId) => {
    setSelectedOrders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(orderId)) {
        newSet.delete(orderId);
      } else {
        newSet.add(orderId);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedOrders.size === orders.length) {
      setSelectedOrders(new Set());
    } else {
      setSelectedOrders(new Set(orders.map(o => o.id)));
    }
  };

  const handleBulkStatusChange = async (newStatus) => {
    if (selectedOrders.size === 0) return;
    setBulkActioning(true);
    try {
      const promises = Array.from(selectedOrders).map(id =>
        axios.put(`${API}/orders/${id}`, { status: newStatus }, { headers: { Authorization: `Bearer ${token()}` } })
      );
      await Promise.all(promises);
      toast.success(`${selectedOrders.size} order(s) updated to ${formatStatus(newStatus)}`);
      setSelectedOrders(new Set());
      fetchOrders();
    } catch {
      toast.error('Failed to update some orders');
    } finally {
      setBulkActioning(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedOrders.size === 0) return;
    if (!window.confirm(`Delete ${selectedOrders.size} order(s)? This cannot be undone.`)) return;
    setBulkActioning(true);
    try {
      const promises = Array.from(selectedOrders).map(id =>
        axios.delete(`${API}/orders/${id}`, { headers: { Authorization: `Bearer ${token()}` } })
      );
      await Promise.all(promises);
      toast.success(`${selectedOrders.size} order(s) deleted`);
      setSelectedOrders(new Set());
      fetchOrders();
    } catch {
      toast.error('Failed to delete some orders');
    } finally {
      setBulkActioning(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="orders-page">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading">Orders</h1>
          <p className="text-slate-400 text-sm mt-1">{total} order{total !== 1 ? 's' : ''}</p>
        </div>
        <Button onClick={handleCreateOrder} className="bg-violet-600 hover:bg-violet-700 text-white gap-2" data-testid="create-order-btn">
          <Plus className="w-4 h-4" /> New Order
        </Button>
      </div>

      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="p-4 flex gap-3 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search orders..."
              className="pl-10 bg-gray-50 border-gray-200 text-gray-900"
              data-testid="orders-search"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48 bg-gray-50 border-gray-200 text-gray-900" data-testid="orders-status-filter">
              <Filter className="w-4 h-4 mr-2 text-gray-400" />
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="draft">Drafts</SelectItem>
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
        </CardContent>
      </Card>

      {/* Bulk Actions Toolbar - appears when orders selected */}
      {selectedOrders.size > 0 && (
        <Card className="bg-violet-600 rounded-xl border border-violet-500 shadow-lg sticky top-20 z-10" data-testid="bulk-actions-toolbar">
          <CardContent className="p-3 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSelectedOrders(new Set())}
                className="text-white hover:bg-violet-500"
              >
                <XCircle className="w-4 h-4 mr-1" /> Clear
              </Button>
              <span className="text-white font-medium">
                {selectedOrders.size} order{selectedOrders.size !== 1 ? 's' : ''} selected
              </span>
            </div>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="secondary" size="sm" disabled={bulkActioning} className="bg-white text-violet-700 hover:bg-violet-50">
                    <CheckSquare className="w-4 h-4 mr-2" /> Change Status
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('approved')}>Mark Approved</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('in_production')}>Start Production</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('ready_for_pickup')}>Mark Ready</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('completed')}>Mark Completed</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('on_hold')}>Put On Hold</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleBulkStatusChange('cancelled')}>Cancel</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={handleBulkDelete}
                disabled={bulkActioning}
                className="bg-red-500 hover:bg-red-600"
              >
                <Trash2 className="w-4 h-4 mr-2" /> Delete
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500"></div>
        </div>
      ) : orders.length === 0 ? (
        <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <CardContent className="py-16 text-center">
            <Package className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No orders yet</h3>
            <p className="text-gray-500 mb-6">Create your first order to start tracking jobs, quotes, and production.</p>
            <Button onClick={handleCreateOrder} className="bg-violet-600 hover:bg-violet-700 text-white gap-2">
              <Plus className="w-4 h-4" /> Create First Order
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {/* Select All row */}
          {orders.length > 0 && (
            <div className="flex items-center gap-3 px-2">
              <Checkbox
                checked={selectedOrders.size === orders.length && orders.length > 0}
                onCheckedChange={toggleSelectAll}
                className="border-gray-400 data-[state=checked]:bg-violet-600"
                data-testid="select-all-orders"
              />
              <span className="text-sm text-gray-400">
                {selectedOrders.size === orders.length ? 'Deselect all' : 'Select all'}
              </span>
            </div>
          )}
          {orders.map((order) => (
            <Card
              key={order.id}
              className={`bg-white rounded-xl border shadow-sm hover:border-violet-500/40 transition-colors cursor-pointer ${
                selectedOrders.has(order.id) ? 'border-violet-500 ring-2 ring-violet-500/20' : 'border-gray-200'
              }`}
              onClick={() => navigate(`/orders/${order.id}`)}
              data-testid={`order-row-${order.order_number}`}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between gap-4">
                  {/* Checkbox */}
                  <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      checked={selectedOrders.has(order.id)}
                      onCheckedChange={() => toggleSelectOrder(order.id)}
                      className="border-gray-300 data-[state=checked]:bg-violet-600"
                      data-testid={`select-order-${order.order_number}`}
                    />
                  </div>
                  
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="w-12 h-12 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                      <Package className="w-6 h-6 text-violet-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-gray-900 text-sm">{order.order_number}</span>
                        <Badge variant="outline" className={STATUS_COLORS[order.status] || STATUS_COLORS.new_intake}>
                          {formatStatus(order.status)}
                        </Badge>
                      </div>
                      <p className="text-gray-900 font-medium mt-0.5 truncate">{order.customer_name || 'No customer'}</p>
                      <p className="text-gray-500 text-xs mt-0.5">{order.company_name}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 flex-shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-gray-500">Total</p>
                      <p className="text-lg font-bold text-gray-900">${(order.order_total || 0).toFixed(2)}</p>
                    </div>
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-gray-500">Tickets</p>
                      <p className="text-lg font-bold text-gray-900">{order.job_ticket_count || 0}</p>
                    </div>
                    <div className="text-right hidden md:block">
                      <p className="text-xs text-gray-500">Progress</p>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-violet-500 rounded-full transition-all" style={{ width: `${order.overall_progress || 0}%` }} />
                        </div>
                        <span className="text-sm text-gray-900 font-medium">{Math.round(order.overall_progress || 0)}%</span>
                      </div>
                    </div>
                    <div className="text-right hidden lg:block">
                      <p className="text-xs text-gray-500">Due</p>
                      <p className="text-sm text-gray-900">{order.requested_due_date ? new Date(order.requested_due_date).toLocaleDateString() : '-'}</p>
                    </div>
                    
                    {/* Action Icons */}
                    <div className="flex items-center gap-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0 text-blue-500 hover:text-blue-600 hover:bg-blue-50"
                        onClick={(e) => { e.stopPropagation(); navigate(`/orders/${order.id}`); }}
                        title="View Order"
                        data-testid={`view-order-${order.order_number}`}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); navigate(`/orders/${order.id}`); }}>
                            <Eye className="w-4 h-4 mr-2" /> View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); navigate(`/orders/${order.id}/add-ticket`); }}>
                            <Plus className="w-4 h-4 mr-2" /> Add Ticket
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            className="text-red-600"
                            onClick={(e) => handleDeleteOrder(e, order.id, order.order_number)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" /> Delete Order
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
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
