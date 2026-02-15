import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Button } from '../components/ui/button';
import { formatCurrency, formatDate } from '../lib/utils';
import { 
  Users, FileText, Briefcase, Receipt, TrendingUp, 
  AlertTriangle, Plus, ArrowRight, Clock 
} from 'lucide-react';
import { Link } from 'react-router-dom';
import InvoicePreviewModal from '../components/InvoicePreviewModal';

const StatCard = ({ title, value, icon: Icon, subtitle, href }) => (
  <div 
    className="rounded-xl p-6 transition-all duration-200 hover:shadow-md"
    style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}
  >
    <div className="flex items-start justify-between">
      <div className="space-y-2">
        <p className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>{title}</p>
        <p className="text-3xl font-bold font-heading tracking-tight" style={{ color: 'var(--text)' }}>{value}</p>
        {subtitle && (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>
        )}
      </div>
      <div className="p-3 rounded-lg" style={{ backgroundColor: 'var(--accent-soft)' }}>
        <Icon className="h-6 w-6" style={{ color: 'var(--accent)' }} />
      </div>
    </div>
    {href && (
      <Link to={href}>
        <button className="mt-4 flex items-center text-sm font-medium hover:opacity-80 transition-opacity" style={{ color: 'var(--accent)' }}>
          View all <ArrowRight className="ml-1 h-4 w-4" />
        </button>
      </Link>
    )}
  </div>
);

const getStatusBadgeStyles = (status) => {
  const styles = {
    quoted: { backgroundColor: 'var(--accent-soft)', color: 'var(--accent)' },
    in_production: { backgroundColor: 'var(--warning-soft)', color: 'var(--warning)' },
    complete: { backgroundColor: 'var(--success-soft)', color: 'var(--success)' },
    delivered: { backgroundColor: 'var(--success-soft)', color: 'var(--success)' },
    overdue: { backgroundColor: 'var(--danger-soft)', color: 'var(--danger)' },
    paid: { backgroundColor: 'var(--success-soft)', color: 'var(--success)' },
    sent: { backgroundColor: 'var(--warning-soft)', color: 'var(--warning)' },
    draft: { backgroundColor: 'var(--surface-2)', color: 'var(--text-muted)' },
  };
  return styles[status] || styles.draft;
};

const RecentActivity = ({ jobs, invoices, onInvoiceClick }) => {
  const recentJobs = jobs?.slice(0, 5) || [];
  const overdueInvoices = invoices?.filter(i => i.status === 'overdue') || [];

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <h2 className="font-heading text-lg font-semibold uppercase tracking-wide" style={{ color: 'var(--text)' }}>
          Recent Activity
        </h2>
      </div>
      <div className="p-4 space-y-3">
        {recentJobs.length === 0 && overdueInvoices.length === 0 ? (
          <p className="text-sm py-4 text-center" style={{ color: 'var(--text-muted)' }}>No recent activity</p>
        ) : (
          <>
            {recentJobs.map(job => (
              <Link key={job.id} to={`/jobs/${job.id}`} data-testid={`recent-job-${job.id}`}>
                <div 
                  className="flex items-center justify-between p-3 rounded-lg transition-all duration-150 hover:shadow-sm"
                  style={{ backgroundColor: 'var(--surface-2)', border: '1px solid transparent' }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent)'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
                >
                  <div className="flex items-center gap-3">
                    <Briefcase className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>{job.name}</p>
                      <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        Due: {formatDate(job.due_date)}
                      </p>
                    </div>
                  </div>
                  <span 
                    className="px-2.5 py-0.5 rounded-full text-xs font-medium"
                    style={getStatusBadgeStyles(job.status)}
                  >
                    {job.status.replace('_', ' ')}
                  </span>
                </div>
              </Link>
            ))}
            {overdueInvoices.map(inv => (
              <div 
                key={inv.id} 
                onClick={() => onInvoiceClick(inv.id)}
                data-testid={`recent-invoice-${inv.id}`}
                className="flex items-center justify-between p-3 rounded-lg transition-colors cursor-pointer"
                style={{ backgroundColor: 'var(--danger-soft)', border: '1px solid var(--danger)' }}
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-4 w-4" style={{ color: 'var(--danger)' }} />
                  <div>
                    <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>Invoice Overdue</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{formatCurrency(inv.total)}</p>
                  </div>
                </div>
                <span 
                  className="px-2.5 py-0.5 rounded-full text-xs font-medium"
                  style={getStatusBadgeStyles('overdue')}
                >
                  Overdue
                </span>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
};

const QuickActions = () => (
  <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
    <div className="px-6 py-4" style={{ borderBottom: '1px solid var(--border-light)' }}>
      <h2 className="font-heading text-lg font-semibold uppercase tracking-wide" style={{ color: 'var(--text)' }}>
        Quick Actions
      </h2>
    </div>
    <div className="p-4 grid grid-cols-2 gap-3">
      <Link to="/customers">
        <button 
          className="w-full flex items-center justify-start gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-customer"
        >
          <Plus className="h-4 w-4" style={{ color: 'var(--accent)' }} /> New Customer
        </button>
      </Link>
      <Link to="/quotes">
        <button 
          className="w-full flex items-center justify-start gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-quote"
        >
          <Plus className="h-4 w-4" style={{ color: 'var(--accent)' }} /> New Quote
        </button>
      </Link>
      <Link to="/jobs">
        <button 
          className="w-full flex items-center justify-start gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-job"
        >
          <Plus className="h-4 w-4" style={{ color: 'var(--accent)' }} /> New Job
        </button>
      </Link>
      <Link to="/timeclock">
        <button 
          className="w-full flex items-center justify-start gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-clock-in"
        >
          <Clock className="h-4 w-4" style={{ color: 'var(--accent)' }} /> Time Clock
        </button>
      </Link>
    </div>
  </div>
);

export default function Dashboard() {
  const { 
    fetchDashboardStats, fetchCustomers, fetchJobs, fetchInvoices,
    dashboardStats, customers, jobs, invoices 
  } = useApp();
  const [loading, setLoading] = useState(true);
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  
  const handleInvoiceClick = (invoiceId) => {
    setPreviewInvoiceId(invoiceId);
    setIsInvoiceModalOpen(true);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchDashboardStats(),
        fetchCustomers(),
        fetchJobs(),
        fetchInvoices()
      ]);
      setLoading(false);
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: '#2F8BFB' }}></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight" style={{ color: '#1A1A1A' }}>
          Dashboard
        </h1>
        <p className="mt-1" style={{ color: '#5A5A5A' }}>Welcome back to SignGuy AI</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Customers"
          value={dashboardStats?.total_customers || 0}
          icon={Users}
          href="/customers"
        />
        <StatCard
          title="Active Jobs"
          value={dashboardStats?.active_jobs || 0}
          icon={Briefcase}
          href="/jobs"
        />
        <StatCard
          title="Pending Invoices"
          value={dashboardStats?.pending_invoices || 0}
          icon={Receipt}
          href="/invoices"
        />
        <StatCard
          title="Today's Revenue"
          value={formatCurrency(dashboardStats?.today_revenue || 0)}
          icon={TrendingUp}
          href="/financials"
        />
      </div>

      {/* Overdue Alert */}
      {dashboardStats?.overdue_count > 0 && (
        <div 
          className="rounded-xl p-4 flex items-center justify-between"
          style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <div>
              <p className="font-medium" style={{ color: '#1A1A1A' }}>
                {dashboardStats.overdue_count} Overdue Invoice{dashboardStats.overdue_count > 1 ? 's' : ''}
              </p>
              <p className="text-sm" style={{ color: '#5A5A5A' }}>
                Total: {formatCurrency(dashboardStats.overdue_total)}
              </p>
            </div>
          </div>
          <Link to="/invoices?status=overdue">
            <Button 
              size="sm" 
              data-testid="view-overdue"
              className="text-white"
              style={{ backgroundColor: '#dc2626' }}
            >
              View Overdue
            </Button>
          </Link>
        </div>
      )}

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentActivity jobs={jobs} invoices={invoices} onInvoiceClick={handleInvoiceClick} />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>

      {/* Invoice Preview Modal */}
      <InvoicePreviewModal
        invoiceId={previewInvoiceId}
        isOpen={isInvoiceModalOpen}
        onClose={() => {
          setIsInvoiceModalOpen(false);
          setPreviewInvoiceId(null);
        }}
      />
    </div>
  );
}
