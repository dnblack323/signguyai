import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { getPortalToken, getPortalCustomerName } from '../lib/authStorage';
import { 
  Loader2, FileText, Receipt, ChevronRight, Calendar, Clock,
  CheckCircle, AlertCircle, DollarSign
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Portal Quotes Page
export function PortalQuotes() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [quotes, setQuotes] = useState([]);
  const [filter, setFilter] = useState('all');
  const customerName = getPortalCustomerName() || 'Customer';

  const fetchQuotes = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const url = filter === 'all'
        ? `${API_URL}/api/portal/quotes`
        : `${API_URL}/api/portal/quotes?status=${filter}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setQuotes(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching quotes:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, filter]);

  useEffect(() => {
    fetchQuotes();
  }, [fetchQuotes]);

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
      draft: { color: 'bg-slate-100 text-slate-700', icon: FileText },
      sent: { color: 'bg-blue-100 text-blue-700', icon: Clock },
      approved: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      declined: { color: 'bg-red-100 text-red-700', icon: AlertCircle },
    };
    return configs[status] || configs.draft;
  };

  const filters = [
    { value: 'all', label: 'All Quotes' },
    { value: 'sent', label: 'Pending' },
    { value: 'approved', label: 'Approved' },
  ];

  return (
    <PortalLayout activeNav="quotes" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Your Quotes</h2>
          <p className="text-slate-600 mt-1">View quotes and estimates</p>
        </div>

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
        ) : quotes.length > 0 ? (
          <div className="space-y-4">
            {quotes.map((quote) => {
              const statusConfig = getStatusConfig(quote.status);
              return (
                <Card key={quote.id} className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-slate-900">
                          Quote #{quote.id.slice(0, 8).toUpperCase()}
                        </h3>
                        <p className="text-sm text-slate-500 mt-1">
                          {quote.line_items?.length || 0} item{(quote.line_items?.length || 0) !== 1 ? 's' : ''}
                        </p>
                        <p className="text-sm text-slate-500">{formatDate(quote.created_at)}</p>
                      </div>
                      <div className="text-right">
                        <Badge className={statusConfig.color}>
                          {quote.status}
                        </Badge>
                        <p className="text-xl font-bold text-slate-900 mt-2">
                          {formatCurrency(quote.total)}
                        </p>
                      </div>
                    </div>
                    {quote.line_items?.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <p className="text-sm text-slate-500 mb-2">Items:</p>
                        <div className="space-y-1">
                          {quote.line_items.slice(0, 3).map((item, idx) => (
                            <div key={idx} className="flex justify-between text-sm">
                              <span className="text-slate-700">{item.description}</span>
                              <span className="text-slate-900 font-medium">{formatCurrency(item.total)}</span>
                            </div>
                          ))}
                          {quote.line_items.length > 3 && (
                            <p className="text-xs text-slate-500">
                              +{quote.line_items.length - 3} more items
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No quotes found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

// Portal Invoices Page
export function PortalInvoices() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState([]);
  const [filter, setFilter] = useState('all');
  const [payingInvoiceId, setPayingInvoiceId] = useState('');
  const customerName = getPortalCustomerName() || 'Customer';

  const fetchInvoices = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const url = filter === 'all'
        ? `${API_URL}/api/portal/invoices`
        : `${API_URL}/api/portal/invoices?status=${filter}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setInvoices(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching invoices:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, filter]);

  useEffect(() => {
    const token = getPortalToken();
    if (token) {
      invoices.forEach((invoice) => {
        fetch(`${API_URL}/api/portal/invoices/${invoice.id}/viewed`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }).catch(() => null);
      });
    }
  }, [invoices]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const handlePayNow = async (invoiceId) => {
    const token = getPortalToken();
    setPayingInvoiceId(invoiceId);
    try {
      const response = await fetch(`${API_URL}/api/portal/invoices/${invoiceId}/pay`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ origin_url: window.location.origin })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to start payment');
      window.location.href = data.url;
    } catch (err) {
      console.error('Error creating invoice payment:', err);
      alert(err.message || 'Unable to start payment');
    } finally {
      setPayingInvoiceId('');
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      draft: { color: 'bg-slate-100 text-slate-700', icon: FileText },
      sent: { color: 'bg-blue-100 text-blue-700', icon: Clock },
      paid: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      overdue: { color: 'bg-red-100 text-red-700', icon: AlertCircle },
    };
    return configs[status] || configs.draft;
  };

  const filters = [
    { value: 'all', label: 'All Invoices' },
    { value: 'sent', label: 'Pending' },
    { value: 'paid', label: 'Paid' },
    { value: 'overdue', label: 'Overdue' },
  ];

  return (
    <PortalLayout activeNav="invoices" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Your Invoices</h2>
          <p className="text-slate-600 mt-1">View and track your invoices</p>
        </div>

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
        ) : invoices.length > 0 ? (
          <div className="space-y-4">
            {invoices.map((invoice) => {
              const statusConfig = getStatusConfig(invoice.status);
              const balanceDue = (invoice.total || 0) - (invoice.amount_paid || 0);
              return (
                <Card key={invoice.id} className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-slate-900">
                          Invoice #{invoice.id.slice(0, 8).toUpperCase()}
                        </h3>
                        <p className="text-sm text-slate-500 mt-1">
                          Issued: {formatDate(invoice.created_at)}
                        </p>
                        {invoice.due_date && (
                          <p className="text-sm text-slate-500">
                            Due: {formatDate(invoice.due_date)}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <Badge className={statusConfig.color}>
                          {invoice.status}
                        </Badge>
                        <p className="text-xl font-bold text-slate-900 mt-2">
                          {formatCurrency(invoice.total)}
                        </p>
                      </div>
                    </div>
                    
                    {invoice.status !== 'paid' && balanceDue > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <div className="flex items-center justify-between bg-amber-50 rounded-lg p-3">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-5 w-5 text-amber-600" />
                            <span className="text-sm font-medium text-amber-800">Balance Due</span>
                          </div>
                          <span className="text-lg font-bold text-amber-900">
                            {formatCurrency(balanceDue)}
                          </span>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <a href={`${API_URL}/api/portal/invoices/${invoice.id}/download`} target="_blank" rel="noopener noreferrer">
                            <Button variant="outline" size="sm">Download PDF</Button>
                          </a>
                          <Button size="sm" className="bg-teal-500 hover:bg-teal-600" onClick={() => handlePayNow(invoice.id)} disabled={payingInvoiceId === invoice.id} data-testid={`portal-pay-invoice-${invoice.id}`}>
                            {payingInvoiceId === invoice.id ? 'Starting...' : 'Pay Now'}
                          </Button>
                        </div>
                      </div>
                    )}

                    {invoice.line_items?.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate-100">
                        <p className="text-sm text-slate-500 mb-2">Items:</p>
                        <div className="space-y-1">
                          {invoice.line_items.slice(0, 3).map((item, idx) => (
                            <div key={idx} className="flex justify-between text-sm">
                              <span className="text-slate-700">{item.description}</span>
                              <span className="text-slate-900 font-medium">{formatCurrency(item.total)}</span>
                            </div>
                          ))}
                          {invoice.line_items.length > 3 && (
                            <p className="text-xs text-slate-500">
                              +{invoice.line_items.length - 3} more items
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <Receipt className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No invoices found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

// Portal Appointments Page
export function PortalAppointments() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState([]);
  const [showPast, setShowPast] = useState(false);
  const customerName = getPortalCustomerName() || 'Customer';

  const fetchAppointments = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const url = showPast
        ? `${API_URL}/api/portal/appointments`
        : `${API_URL}/api/portal/appointments?upcoming_only=true`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAppointments(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching appointments:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, showPast]);

  useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getTypeConfig = (type) => {
    const configs = {
      consultation: { color: 'bg-blue-100 text-blue-700', label: 'Consultation' },
      pickup: { color: 'bg-green-100 text-green-700', label: 'Pickup' },
      installation: { color: 'bg-purple-100 text-purple-700', label: 'Installation' },
      site_survey: { color: 'bg-amber-100 text-amber-700', label: 'Site Survey' },
      other: { color: 'bg-slate-100 text-slate-700', label: 'Other' },
    };
    return configs[type] || configs.other;
  };

  const getStatusConfig = (status) => {
    const configs = {
      scheduled: { color: 'bg-blue-100 text-blue-700' },
      confirmed: { color: 'bg-green-100 text-green-700' },
      completed: { color: 'bg-slate-100 text-slate-700' },
      cancelled: { color: 'bg-red-100 text-red-700' },
      no_show: { color: 'bg-red-100 text-red-700' },
    };
    return configs[status] || configs.scheduled;
  };

  return (
    <PortalLayout activeNav="appointments" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Your Appointments</h2>
          <p className="text-slate-600 mt-1">Scheduled meetings and visits</p>
        </div>

        <div className="flex gap-2">
          <Button
            variant={!showPast ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowPast(false)}
            className={!showPast ? 'bg-teal-500 hover:bg-teal-600' : ''}
          >
            Upcoming
          </Button>
          <Button
            variant={showPast ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowPast(true)}
            className={showPast ? 'bg-teal-500 hover:bg-teal-600' : ''}
          >
            All
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
          </div>
        ) : appointments.length > 0 ? (
          <div className="space-y-4">
            {appointments.map((apt) => {
              const typeConfig = getTypeConfig(apt.appointment_type);
              const statusConfig = getStatusConfig(apt.status);
              return (
                <Card key={apt.id} className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="w-14 h-14 rounded-xl bg-teal-50 flex flex-col items-center justify-center flex-shrink-0">
                        <Calendar className="h-6 w-6 text-teal-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-slate-900">{apt.title}</h3>
                            <p className="text-slate-600 mt-1">{formatDate(apt.scheduled_date)}</p>
                            <div className="flex items-center gap-2 mt-1 text-sm text-slate-500">
                              <Clock className="h-4 w-4" />
                              <span>{apt.scheduled_time}</span>
                              <span>({apt.duration_minutes} min)</span>
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <Badge className={typeConfig.color}>{typeConfig.label}</Badge>
                            <Badge className={statusConfig.color}>{apt.status}</Badge>
                          </div>
                        </div>
                        {apt.location && (
                          <p className="text-sm text-slate-500 mt-2">
                            📍 {apt.location}
                          </p>
                        )}
                        {apt.description && (
                          <p className="text-sm text-slate-600 mt-2">{apt.description}</p>
                        )}
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
              <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">
                {showPast ? 'No appointments found' : 'No upcoming appointments'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

export default PortalQuotes;
