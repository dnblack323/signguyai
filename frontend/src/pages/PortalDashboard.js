import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { getPortalToken, clearPortalToken, clearPortalCustomerId, clearPortalCustomerName, getPortalCustomerName } from '../lib/authStorage';
import { 
  Loader2, LogOut, FileText, Briefcase, Receipt, MessageSquare, 
  Image, Bell, Calendar, User, ChevronRight, Home, Settings,
  ExternalLink, Clock, CheckCircle, AlertCircle, Store
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Portal Layout Wrapper
function PortalLayout({ children, activeNav, customerName }) {
  const navigate = useNavigate();
  const [hasWebstores, setHasWebstores] = useState(false);

  const handleLogout = () => {
    clearPortalToken();
    clearPortalCustomerId();
    clearPortalCustomerName();
    navigate('/customer-portal/login');
  };

  // Single cheap call to know whether to render the Webstores tab.
  // We fetch /api/portal/webstores once per layout mount — list is bounded
  // (max 100) and filtered by tenant + owner_email so it's tiny.
  useEffect(() => {
    let cancelled = false;
    const token = getPortalToken();
    if (!token) return;
    fetch(`${API_URL}/api/portal/webstores`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((rows) => {
        if (!cancelled) setHasWebstores(Array.isArray(rows) && rows.length > 0);
      })
      .catch(() => { /* nav still works if this fails */ });
    return () => { cancelled = true; };
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/customer-portal' },
    { id: 'orders', label: 'Orders', icon: Briefcase, path: '/customer-portal/orders' },
    { id: 'forms', label: 'Forms / Questionnaires', icon: FileText, path: '/customer-portal/forms' },
    { id: 'quotes', label: 'Quotes', icon: FileText, path: '/customer-portal/quotes' },
    { id: 'invoices', label: 'Invoices', icon: Receipt, path: '/customer-portal/invoices' },
    { id: 'documents', label: 'Documents', icon: FileText, path: '/customer-portal/documents' },
    { id: 'messages', label: 'Messages', icon: MessageSquare, path: '/customer-portal/messages' },
    { id: 'proofs', label: 'Artwork Approvals', icon: Image, path: '/customer-portal/proofs' },
    { id: 'appointments', label: 'Appointments', icon: Calendar, path: '/customer-portal/appointments' },
    // Conditionally inserted Webstores tab — appears ONLY when the
    // portal user is the assigned owner of one or more webstores.
    ...(hasWebstores
      ? [{ id: 'webstores', label: 'Webstores', icon: Store, path: '/customer-portal/webstores' }]
      : []),
    { id: 'profile', label: 'Profile', icon: User, path: '/customer-portal/profile' },
  ];

  return (
    <div className="min-h-screen bg-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-teal-500 flex items-center justify-center">
                <span className="text-white font-bold text-lg">S</span>
              </div>
              <div>
                <h1 className="font-semibold text-slate-900">Customer Portal</h1>
                <p className="text-xs text-slate-500">Welcome, {customerName}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={handleLogout}
                className="text-slate-600 hover:text-slate-900"
                data-testid="portal-logout-btn"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 overflow-x-auto py-2">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                  activeNav === item.id
                    ? 'bg-teal-50 text-teal-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                data-testid={`portal-nav-${item.id}`}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-slate-500">
            Powered by SignGuy AI
          </p>
        </div>
      </footer>
    </div>
  );
}

export { PortalLayout };

export default function PortalDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState('');
  const customerName = getPortalCustomerName() || 'Customer';

  const fetchDashboard = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/portal/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDashboard(data);
      } else if (response.status === 401) {
        clearPortalToken();
        navigate('/customer-portal/login');
      } else {
        const err = await response.json();
        setError(err.detail || 'Failed to load dashboard');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: 'bg-slate-100 text-slate-700',
      sent: 'bg-blue-100 text-blue-700',
      approved: 'bg-green-100 text-green-700',
      declined: 'bg-red-100 text-red-700',
      paid: 'bg-green-100 text-green-700',
      overdue: 'bg-red-100 text-red-700',
      quoted: 'bg-purple-100 text-purple-700',
      in_production: 'bg-amber-100 text-amber-700',
      complete: 'bg-green-100 text-green-700',
      pending: 'bg-amber-100 text-amber-700',
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  if (loading) {
    return (
      <PortalLayout activeNav="dashboard" customerName={customerName}>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  if (error) {
    return (
      <PortalLayout activeNav="dashboard" customerName={customerName}>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-700">{error}</p>
            <Button onClick={fetchDashboard} className="mt-4">Try Again</Button>
          </CardContent>
        </Card>
      </PortalLayout>
    );
  }

  const { stats, upcoming_appointments, recent_jobs, recent_invoices, recent_documents, pending_forms, awaiting_approval } = dashboard || {};
  const statCards = [
    {
      key: 'active-orders',
      count: stats?.active_jobs || 0,
      label: 'Active Orders',
      icon: Briefcase,
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      path: '/customer-portal/orders',
    },
    {
      key: 'quotes',
      count: stats?.total_quotes || 0,
      label: 'Quotes',
      icon: FileText,
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
      path: '/customer-portal/quotes',
    },
    {
      key: 'pending-invoices',
      count: stats?.pending_invoices || 0,
      label: 'Pending Invoices',
      icon: Receipt,
      iconBg: 'bg-amber-100',
      iconColor: 'text-amber-600',
      path: '/customer-portal/invoices',
    },
    {
      key: 'proofs-awaiting',
      count: stats?.pending_proofs || 0,
      label: 'Proofs Awaiting',
      icon: Image,
      iconBg: 'bg-teal-100',
      iconColor: 'text-teal-600',
      path: '/customer-portal/proofs',
    },
    {
      key: 'new-messages',
      count: stats?.unread_messages || 0,
      label: 'New Messages',
      icon: MessageSquare,
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      path: '/customer-portal/messages',
    },
    {
      key: 'notifications',
      count: stats?.unread_notifications || 0,
      label: 'Notifications',
      icon: Bell,
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      path: '/customer-portal',
    },
    {
      key: 'pending-forms',
      count: stats?.pending_forms || 0,
      label: 'Pending Forms',
      icon: FileText,
      iconBg: 'bg-cyan-100',
      iconColor: 'text-cyan-600',
      path: '/customer-portal/forms',
    },
    {
      key: 'new-docs',
      count: stats?.recent_documents || 0,
      label: 'New Docs',
      icon: FileText,
      iconBg: 'bg-indigo-100',
      iconColor: 'text-indigo-600',
      path: '/customer-portal/documents',
    },
  ];

  return (
    <PortalLayout activeNav="dashboard" customerName={customerName}>
      <div className="space-y-6">
        {/* Welcome Header */}
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Welcome back, {customerName}!</h2>
          <p className="text-slate-600 mt-1">Here's an overview of your account</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4" data-testid="portal-stats-grid">
          {statCards.map((card) => {
            const Icon = card.icon;
            return (
              <Link key={card.key} to={card.path} data-testid={`portal-stat-card-${card.key}`}>
                <Card className="border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${card.iconBg}`}>
                        <Icon className={`h-5 w-5 ${card.iconColor}`} />
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-slate-900">{card.count}</p>
                        <p className="text-xs text-slate-500">{card.label}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        {/* Quick Actions */}
        {(stats?.pending_proofs > 0 || stats?.unread_messages > 0 || stats?.pending_forms > 0) && (
          <Card className="border-teal-200 bg-teal-50">
            <CardContent className="p-4">
              <h3 className="font-semibold text-teal-800 mb-3">Action Required</h3>
              <div className="flex flex-wrap gap-3">
                {stats?.pending_proofs > 0 && (
                  <Link to="/customer-portal/proofs">
                    <Button variant="outline" className="border-teal-300 text-teal-700 hover:bg-teal-100">
                      <Image className="h-4 w-4 mr-2" />
                      Review {stats.pending_proofs} Artwork Proof{stats.pending_proofs > 1 ? 's' : ''}
                    </Button>
                  </Link>
                )}
                {stats?.unread_messages > 0 && (
                  <Link to="/customer-portal/messages">
                    <Button variant="outline" className="border-teal-300 text-teal-700 hover:bg-teal-100">
                      <MessageSquare className="h-4 w-4 mr-2" />
                      {stats.unread_messages} New Message{stats.unread_messages > 1 ? 's' : ''}
                    </Button>
                  </Link>
                )}
                {stats?.pending_forms > 0 && (
                  <Link to="/customer-portal/forms">
                    <Button variant="outline" className="border-teal-300 text-teal-700 hover:bg-teal-100">
                      <FileText className="h-4 w-4 mr-2" />
                      {stats.pending_forms} Pending Form{stats.pending_forms > 1 ? 's' : ''}
                    </Button>
                  </Link>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Recent Orders */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Recent Orders</CardTitle>
                <Link to="/customer-portal/orders">
                  <Button variant="ghost" size="sm" className="text-teal-600">
                    View All <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {recent_jobs?.length > 0 ? (
                <div className="space-y-3">
                  {recent_jobs.map((job) => (
                    <Link 
                      key={job.id} 
                      to={`/customer-portal/orders/${job.id}`}
                      className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{job.name || `Order #${job.id.slice(0, 8)}`}</p>
                          <p className="text-sm text-slate-500">{formatDate(job.created_at)}</p>
                        </div>
                        <Badge className={getStatusColor(job.status)}>
                          {job.status?.replace('_', ' ')}
                        </Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No recent orders</p>
              )}
            </CardContent>
          </Card>

          {/* Recent Invoices */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Recent Invoices</CardTitle>
                <Link to="/customer-portal/invoices">
                  <Button variant="ghost" size="sm" className="text-teal-600">
                    View All <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {recent_invoices?.length > 0 ? (
                <div className="space-y-3">
                  {recent_invoices.map((invoice) => (
                    <div 
                      key={invoice.id}
                      className="p-3 rounded-lg border border-slate-200"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">Invoice #{invoice.id.slice(0, 8)}</p>
                          <p className="text-sm text-slate-500">{formatDate(invoice.created_at)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-slate-900">{formatCurrency(invoice.total)}</p>
                          <Badge className={getStatusColor(invoice.status)}>
                            {invoice.status}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No invoices yet</p>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Pending Forms</CardTitle>
                <Link to="/customer-portal/forms">
                  <Button variant="ghost" size="sm" className="text-teal-600">
                    View All <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {pending_forms?.length > 0 ? (
                <div className="space-y-3">
                  {pending_forms.map((formRequest) => (
                    <Link key={formRequest.id} to={`/customer-portal/forms/${formRequest.id}`} className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-slate-900">{formRequest.questionnaire_name}</p>
                          <p className="text-sm text-slate-500">Due: {formatDate(formRequest.due_date || formRequest.sent_at)}</p>
                        </div>
                        <Badge className={getStatusColor(formRequest.status)}>{formRequest.status}</Badge>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No pending forms</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Awaiting Approval</CardTitle>
                <Link to="/customer-portal/proofs"><Button variant="ghost" size="sm" className="text-teal-600">View All <ChevronRight className="h-4 w-4 ml-1" /></Button></Link>
              </div>
            </CardHeader>
            <CardContent>
              {awaiting_approval?.length > 0 ? awaiting_approval.map((proof) => (
                <Link key={proof.id} to={`/customer-portal/proofs/${proof.id}`} className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors mb-3 last:mb-0">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">Version {proof.version}</p>
                      <p className="text-sm text-slate-500">{proof.created_at ? formatDate(proof.created_at) : '-'}</p>
                    </div>
                    <Badge className="bg-amber-100 text-amber-700">Pending Review</Badge>
                  </div>
                </Link>
              )) : <p className="text-slate-500 text-center py-8">No approvals waiting</p>}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Recent Documents</CardTitle>
                <Link to="/customer-portal/documents"><Button variant="ghost" size="sm" className="text-teal-600">View All <ChevronRight className="h-4 w-4 ml-1" /></Button></Link>
              </div>
            </CardHeader>
            <CardContent>
              {recent_documents?.length > 0 ? recent_documents.map((doc) => (
                <Link key={doc.id} to="/customer-portal/documents" className="block p-3 rounded-lg border border-slate-200 hover:border-teal-300 hover:bg-slate-50 transition-colors mb-3 last:mb-0">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">{doc.document_name || 'Document'}</p>
                      <p className="text-sm text-slate-500">Shared {formatDate(doc.created_at)}</p>
                    </div>
                    {!doc.viewed_at && <Badge className="bg-teal-100 text-teal-700">New</Badge>}
                  </div>
                </Link>
              )) : <p className="text-slate-500 text-center py-8">No recent documents</p>}
            </CardContent>
          </Card>
        </div>

        {/* Upcoming Appointments */}
        {upcoming_appointments?.length > 0 && (
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Upcoming Appointments</CardTitle>
                <Link to="/customer-portal/appointments">
                  <Button variant="ghost" size="sm" className="text-teal-600">
                    View All <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                {upcoming_appointments.map((apt) => (
                  <div 
                    key={apt.id}
                    className="p-4 rounded-lg border border-slate-200 bg-slate-50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-teal-100 flex items-center justify-center flex-shrink-0">
                        <Calendar className="h-5 w-5 text-teal-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{apt.title}</p>
                        <p className="text-sm text-slate-600">{formatDate(apt.scheduled_date)} at {apt.scheduled_time}</p>
                        {apt.location && (
                          <p className="text-sm text-slate-500 mt-1">{apt.location}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}
