import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { formatCurrency, formatDate, getStatusColor } from '../lib/utils';
import { 
  Users, FileText, Briefcase, Receipt, TrendingUp, 
  AlertTriangle, Plus, ArrowRight, Clock 
} from 'lucide-react';
import { Link } from 'react-router-dom';
import InvoicePreviewModal from '../components/InvoicePreviewModal';

const StatCard = ({ title, value, icon: Icon, subtitle, trend, href }) => (
  <Card className="bg-card border-border/50 hover:border-primary/30 transition-all duration-300">
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold font-heading tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        <div className="p-3 rounded-lg bg-primary/10">
          <Icon className="h-6 w-6 text-primary" />
        </div>
      </div>
      {href && (
        <Link to={href}>
          <Button variant="ghost" size="sm" className="mt-4 p-0 h-auto text-primary hover:text-primary/80">
            View all <ArrowRight className="ml-1 h-4 w-4" />
          </Button>
        </Link>
      )}
    </CardContent>
  </Card>
);

const RecentActivity = ({ jobs, invoices, onInvoiceClick }) => {
  const recentJobs = jobs?.slice(0, 5) || [];
  const overdueInvoices = invoices?.filter(i => i.status === 'overdue') || [];

  return (
    <Card className="bg-card border-border/50">
      <CardHeader>
        <CardTitle className="font-heading text-xl uppercase tracking-wide">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {recentJobs.length === 0 && overdueInvoices.length === 0 ? (
          <p className="text-muted-foreground text-sm">No recent activity</p>
        ) : (
          <>
            {recentJobs.map(job => (
              <Link key={job.id} to={`/jobs/${job.id}`} data-testid={`recent-job-${job.id}`}>
                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 hover:border-primary/30 border border-transparent transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <Briefcase className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{job.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Due: {formatDate(job.due_date)}
                      </p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(job.status)}>
                    {job.status.replace('_', ' ')}
                  </Badge>
                </div>
              </Link>
            ))}
            {overdueInvoices.map(inv => (
              <div 
                key={inv.id} 
                onClick={() => onInvoiceClick(inv.id)}
                data-testid={`recent-invoice-${inv.id}`}
                className="flex items-center justify-between p-3 rounded-lg bg-destructive/10 border border-destructive/30 hover:bg-destructive/20 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-4 w-4 text-destructive" />
                  <div>
                    <p className="font-medium text-sm">Invoice Overdue</p>
                    <p className="text-xs text-muted-foreground">{formatCurrency(inv.total)}</p>
                  </div>
                </div>
                <Badge className={getStatusColor('overdue')}>Overdue</Badge>
              </div>
            ))}
          </>
        )}
      </CardContent>
    </Card>
  );
};

const QuickActions = () => (
  <Card className="bg-card border-border/50">
    <CardHeader>
      <CardTitle className="font-heading text-xl uppercase tracking-wide">Quick Actions</CardTitle>
    </CardHeader>
    <CardContent className="grid grid-cols-2 gap-3">
      <Link to="/customers">
        <Button variant="outline" className="w-full justify-start gap-2" data-testid="quick-add-customer">
          <Plus className="h-4 w-4" /> New Customer
        </Button>
      </Link>
      <Link to="/quotes">
        <Button variant="outline" className="w-full justify-start gap-2" data-testid="quick-add-quote">
          <Plus className="h-4 w-4" /> New Quote
        </Button>
      </Link>
      <Link to="/jobs">
        <Button variant="outline" className="w-full justify-start gap-2" data-testid="quick-add-job">
          <Plus className="h-4 w-4" /> New Job
        </Button>
      </Link>
      <Link to="/timeclock">
        <Button variant="outline" className="w-full justify-start gap-2" data-testid="quick-clock-in">
          <Clock className="h-4 w-4" /> Time Clock
        </Button>
      </Link>
    </CardContent>
  </Card>
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">Welcome back to Sign Guy AI</p>
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
        <Card className="bg-destructive/10 border-destructive/30">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <div>
                <p className="font-medium">
                  {dashboardStats.overdue_count} Overdue Invoice{dashboardStats.overdue_count > 1 ? 's' : ''}
                </p>
                <p className="text-sm text-muted-foreground">
                  Total: {formatCurrency(dashboardStats.overdue_total)}
                </p>
              </div>
            </div>
            <Link to="/invoices?status=overdue">
              <Button variant="destructive" size="sm" data-testid="view-overdue">
                View Overdue
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentActivity jobs={jobs} invoices={invoices} />
        </div>
        <div>
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
