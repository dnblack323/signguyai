import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { getPortalToken } from '../lib/authStorage';
import { 
  Loader2, Briefcase, ChevronLeft, ChevronRight, FileText, 
  Clock, CheckCircle, Truck, Package, AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PortalOrders() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('all');
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  const fetchOrders = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const url = filter === 'all' 
        ? `${API_URL}/api/portal/orders`
        : `${API_URL}/api/portal/orders?status=${filter}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching orders:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, filter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const getStatusConfig = (status) => {
    const configs = {
      quoted: { color: 'bg-purple-100 text-purple-700', icon: FileText },
      approved: { color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
      in_production: { color: 'bg-amber-100 text-amber-700', icon: Package },
      installed: { color: 'bg-teal-100 text-teal-700', icon: Truck },
      complete: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      archived: { color: 'bg-slate-100 text-slate-700', icon: FileText },
    };
    return configs[status] || { color: 'bg-slate-100 text-slate-700', icon: Clock };
  };

  const filters = [
    { value: 'all', label: 'All Orders' },
    { value: 'in_production', label: 'In Production' },
    { value: 'complete', label: 'Completed' },
  ];

  return (
    <PortalLayout activeNav="orders" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Your Orders</h2>
          <p className="text-slate-600 mt-1">Track the status of your sign projects</p>
        </div>

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {filters.map((f) => (
            <Button
              key={f.value}
              variant={filter === f.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(f.value)}
              className={filter === f.value ? 'bg-teal-500 hover:bg-teal-600' : ''}
            >
              {f.label}
            </Button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
          </div>
        ) : orders.length > 0 ? (
          <div className="space-y-4">
            {orders.map((order) => {
              const statusConfig = getStatusConfig(order.status);
              const StatusIcon = statusConfig.icon;
              return (
                <Card key={order.id} className="border-slate-200 hover:border-teal-300 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${statusConfig.color.split(' ')[0]}`}>
                          <StatusIcon className={`h-6 w-6 ${statusConfig.color.split(' ')[1]}`} />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">
                            {order.name || `Order #${order.id.slice(0, 8)}`}
                          </h3>
                          <p className="text-sm text-slate-500 mt-1">{order.description || 'No description'}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                            <span>Created: {formatDate(order.created_at)}</span>
                            {order.due_date && <span>Due: {formatDate(order.due_date)}</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <Badge className={statusConfig.color}>
                          {order.status?.replace('_', ' ')}
                        </Badge>
                        <p className="text-lg font-semibold text-slate-900">
                          {formatCurrency(order.subtotal)}
                        </p>
                        <Link to={`/customer-portal/orders/${order.id}`}>
                          <Button variant="ghost" size="sm" className="text-teal-600">
                            View Details <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <Briefcase className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No orders found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

export function PortalOrderDetail() {
  const navigate = useNavigate();
  const { orderId } = useParams();
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  useEffect(() => {
    const fetchOrder = async () => {
      const token = getPortalToken();
      if (!token) {
        navigate('/customer-portal/login');
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/portal/orders/${orderId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setOrder(data);
        } else if (response.status === 401) {
          navigate('/customer-portal/login');
        }
      } catch (err) {
        console.error('Error fetching order:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchOrder();
  }, [navigate, orderId]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-amber-100 text-amber-700',
      in_production: 'bg-blue-100 text-blue-700',
      done: 'bg-green-100 text-green-700',
      complete: 'bg-green-100 text-green-700',
      approved: 'bg-teal-100 text-teal-700',
      rejected: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  if (loading) {
    return (
      <PortalLayout activeNav="orders" customerName={customerName}>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  if (!order) {
    return (
      <PortalLayout activeNav="orders" customerName={customerName}>
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-700">Order not found</p>
            <Link to="/customer-portal/orders">
              <Button className="mt-4">Back to Orders</Button>
            </Link>
          </CardContent>
        </Card>
      </PortalLayout>
    );
  }

  return (
    <PortalLayout activeNav="orders" customerName={customerName}>
      <div className="space-y-6">
        {/* Back Button */}
        <Link to="/customer-portal/orders" className="inline-flex items-center text-sm text-slate-600 hover:text-teal-600">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Orders
        </Link>

        {/* Order Header */}
        <Card className="border-slate-200">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-xl">
                  {order.name || `Order #${order.id.slice(0, 8)}`}
                </CardTitle>
                <CardDescription className="mt-1">
                  Created on {formatDate(order.created_at)}
                </CardDescription>
              </div>
              <Badge className={getStatusColor(order.status)}>
                {order.status?.replace('_', ' ')}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {order.description && (
              <p className="text-slate-600 mb-4">{order.description}</p>
            )}
            <div className="flex flex-wrap gap-6 text-sm">
              <div>
                <span className="text-slate-500">Job Number:</span>
                <span className="ml-2 font-medium text-slate-900">{order.id.slice(0, 8).toUpperCase()}</span>
              </div>
              {order.due_date && (
                <div>
                  <span className="text-slate-500">Due Date:</span>
                  <span className="ml-2 font-medium text-slate-900">{formatDate(order.due_date)}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {order.customer_status_timeline?.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Status Timeline</CardTitle>
              <CardDescription>Customer-facing progress updates only.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
                {order.customer_status_timeline.map((item, index) => (
                  <div key={`${item.label}-${index}`} className="rounded-lg border border-slate-200 p-4" data-testid={`portal-order-status-${index}`}>
                    <p className="font-medium text-slate-900">{item.label}</p>
                    <Badge className={item.status === 'complete' ? 'bg-green-100 text-green-700 mt-2' : item.status === 'current' ? 'bg-amber-100 text-amber-700 mt-2' : 'bg-slate-100 text-slate-700 mt-2'}>{item.status}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Line Items */}
        {order.items?.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Order Items</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Item</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Type</th>
                      <th className="text-center py-3 px-4 text-sm font-medium text-slate-500">Status</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Qty</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Price</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.items.map((item, idx) => (
                      <tr key={item.id || idx} className="border-b border-slate-100">
                        <td className="py-3 px-4">
                          <p className="font-medium text-slate-900">{item.description}</p>
                          {item.notes && <p className="text-sm text-slate-500 mt-1">{item.notes}</p>}
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-600">
                          {item.item_type?.replace('_', ' ')}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge className={getStatusColor(item.status)}>
                            {item.status?.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right text-slate-600">{item.quantity}</td>
                        <td className="py-3 px-4 text-right text-slate-600">{formatCurrency(item.unit_price)}</td>
                        <td className="py-3 px-4 text-right font-medium text-slate-900">
                          {formatCurrency(item.line_total || item.quantity * item.unit_price)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan="5" className="py-3 px-4 text-right font-semibold text-slate-900">
                        Total
                      </td>
                      <td className="py-3 px-4 text-right text-lg font-bold text-teal-600">
                        {formatCurrency(order.subtotal)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Artwork Proofs */}
        {order.proofs?.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Artwork Proofs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {order.proofs.map((proof) => (
                  <div key={proof.id} className="border border-slate-200 rounded-lg overflow-hidden">
                    {proof.file_url && (
                      <img 
                        src={proof.file_url} 
                        alt={proof.file_name}
                        className="w-full h-40 object-cover bg-slate-100"
                      />
                    )}
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-slate-900">Version {proof.version}</span>
                        <Badge className={getStatusColor(proof.status)}>{proof.status}</Badge>
                      </div>
                      <p className="text-xs text-slate-500">{formatDate(proof.created_at)}</p>
                      {proof.status === 'pending' && (
                        <Link to={`/customer-portal/proofs/${proof.id}`}>
                          <Button size="sm" className="w-full mt-2 bg-teal-500 hover:bg-teal-600">
                            Review & Approve
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Forms / Questionnaires</CardTitle>
            </CardHeader>
            <CardContent>
              {order.forms?.length > 0 ? order.forms.map((form) => (
                <Link key={form.id} to={`/customer-portal/forms/${form.id}`} className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors mb-3 last:mb-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{form.questionnaire_name}</p>
                      <p className="text-sm text-slate-500">{form.instructions || 'Complete the requested form'}</p>
                    </div>
                    <Badge className={form.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}>{form.status.replace('_', ' ')}</Badge>
                  </div>
                </Link>
              )) : <p className="text-slate-500">No forms linked to this job.</p>}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Messages</CardTitle>
            </CardHeader>
            <CardContent>
              {order.conversations?.length > 0 ? order.conversations.map((conversation) => (
                <Link key={conversation.id} to={`/customer-portal/messages/${conversation.id}`} className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors mb-3 last:mb-0">
                  <p className="font-medium text-slate-900">{conversation.subject}</p>
                  <p className="text-sm text-slate-500">{conversation.last_message_preview}</p>
                </Link>
              )) : <p className="text-slate-500">No job-specific messages yet.</p>}
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {order.documents?.length > 0 ? order.documents.map((doc) => (
                <Link key={doc.id} to="/customer-portal/documents" className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors mb-3 last:mb-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{doc.document_name || 'Document'}</p>
                      <p className="text-sm text-slate-500">Shared {formatDate(doc.created_at)}</p>
                    </div>
                    {!doc.viewed_at && <Badge className="bg-teal-100 text-teal-700">New</Badge>}
                  </div>
                </Link>
              )) : <p className="text-slate-500">No customer-visible documents linked to this job.</p>}
            </CardContent>
          </Card>

          {order.invoice && (
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Invoice</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Status</span>
                  <Badge className={getStatusColor(order.invoice.status)}>{order.invoice.status}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Total</span>
                  <span className="font-semibold text-slate-900">{formatCurrency(order.invoice.total)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Balance Due</span>
                  <span className="font-semibold text-slate-900">{formatCurrency((order.invoice.total || 0) - (order.invoice.amount_paid || 0))}</span>
                </div>
                <div className="flex gap-2 pt-2">
                  <a href={`${API_URL}/api/portal/invoices/${order.invoice.id}/download`} target="_blank" rel="noopener noreferrer">
                    <Button variant="outline">Download PDF</Button>
                  </a>
                  <Link to="/customer-portal/invoices"><Button className="bg-teal-500 hover:bg-teal-600">Open Invoices</Button></Link>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </PortalLayout>
  );
}

export default PortalOrders;
