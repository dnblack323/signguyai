import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { formatCurrency, formatDate } from '../lib/utils';
import { 
  Users, FileText, Briefcase, Receipt, TrendingUp, 
  AlertTriangle, Plus, ArrowRight, Clock, MessageSquare,
  CheckCircle, Calendar, UserCheck, Coffee, Sun, Sunset, Moon,
  ChevronRight, Eye, Sparkles, Download, Send, ExternalLink
} from 'lucide-react';
import { Link } from 'react-router-dom';
import InvoicePreviewModal from '../components/InvoicePreviewModal';
import OnboardingChecklist from '../components/OnboardingChecklist';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Get greeting based on time of day
const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return { text: 'Good morning', icon: Sun, color: 'text-amber-500' };
  if (hour < 17) return { text: 'Good afternoon', icon: Sunset, color: 'text-orange-500' };
  return { text: 'Good evening', icon: Moon, color: 'text-indigo-400' };
};

const StatCard = ({ title, value, icon: Icon, subtitle, href, accentColor = 'var(--accent)' }) => (
  <div 
    className="rounded-xl p-4 sm:p-6 transition-all duration-200 hover:shadow-md group"
    style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}
  >
    <div className="flex items-start justify-between">
      <div className="space-y-1 sm:space-y-2 flex-1 min-w-0">
        <p className="text-xs sm:text-sm font-medium truncate" style={{ color: 'var(--text-muted)' }}>{title}</p>
        <p className="text-2xl sm:text-3xl font-bold font-heading tracking-tight" style={{ color: 'var(--text)' }}>{value}</p>
        {subtitle && (
          <p className="text-xs hidden sm:block" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>
        )}
      </div>
      <div className="p-2 sm:p-3 rounded-lg transition-transform group-hover:scale-110 flex-shrink-0 ml-2" style={{ backgroundColor: `${accentColor}15` }}>
        <Icon className="h-5 w-5 sm:h-6 sm:w-6" style={{ color: accentColor }} />
      </div>
    </div>
    {href && (
      <Link to={href}>
        <button className="mt-3 sm:mt-4 flex items-center text-xs sm:text-sm font-medium hover:opacity-80 transition-opacity" style={{ color: accentColor }}>
          View all <ArrowRight className="ml-1 h-3 w-3 sm:h-4 sm:w-4" />
        </button>
      </Link>
    )}
  </div>
);

const getStatusBadgeStyles = (status) => {
  // High-contrast badge styles for readability
  const styles = {
    quoted: { backgroundColor: '#2F8BFB', color: '#FFFFFF' },           // Blue with white text
    in_production: { backgroundColor: '#F59E0B', color: '#000000' },    // Amber with black text for contrast
    complete: { backgroundColor: '#22C55E', color: '#FFFFFF' },         // Green with white text
    delivered: { backgroundColor: '#22C55E', color: '#FFFFFF' },        // Green with white text
    overdue: { backgroundColor: '#EF4444', color: '#FFFFFF' },          // Red with white text
    paid: { backgroundColor: '#22C55E', color: '#FFFFFF' },             // Green with white text
    sent: { backgroundColor: '#8B5CF6', color: '#FFFFFF' },             // Purple with white text
    draft: { backgroundColor: '#6B7280', color: '#FFFFFF' },            // Gray with white text
    working: { backgroundColor: '#22C55E', color: '#FFFFFF' },          // Green with white text
    on_break: { backgroundColor: '#F59E0B', color: '#000000' },         // Amber with black text
    urgent: { backgroundColor: '#EF4444', color: '#FFFFFF' },           // Red with white text
    pending: { backgroundColor: '#F59E0B', color: '#000000' },          // Amber with black text
    approved: { backgroundColor: '#2F8BFB', color: '#FFFFFF' },         // Blue with white text
  };
  return styles[status] || styles.draft;
};

// Pending Approvals Widget
const PendingApprovalsWidget = ({ approvals }) => {
  if (!approvals || approvals.length === 0) {
    return (
      <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
        <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-500" />
            <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
              Pending Approvals
            </h2>
          </div>
          <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-500">All clear</span>
        </div>
        <div className="p-6 text-center">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No proofs awaiting approval</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <Eye className="h-5 w-5 text-amber-500" />
          <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
            Pending Approvals
          </h2>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-amber-500/10 text-amber-500 font-medium">
          {approvals.length} pending
        </span>
      </div>
      <div className="p-4 space-y-2">
        {approvals.slice(0, 3).map(approval => (
          <Link key={approval.id} to={`/jobs/${approval.job_id}`}>
            <div 
              className="flex items-center justify-between p-3 rounded-lg transition-all duration-150 hover:shadow-sm cursor-pointer"
              style={{ backgroundColor: 'var(--surface-2)', border: '1px solid transparent' }}
            >
              <div>
                <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>{approval.job_name}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{approval.customer_name}</p>
              </div>
              <ChevronRight className="h-4 w-4" style={{ color: 'var(--text-muted)' }} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

// Unread Messages Widget
const MessagesWidget = ({ messages }) => {
  if (!messages || messages.length === 0) {
    return (
      <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
        <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-blue-500" />
            <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
              Messages
            </h2>
          </div>
          <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-500">Inbox zero</span>
        </div>
        <div className="p-6 text-center">
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No unread messages</p>
        </div>
      </div>
    );
  }

  const totalUnread = messages.reduce((sum, m) => sum + m.unread_count, 0);

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-blue-500" />
          <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
            Messages
          </h2>
        </div>
        <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-500 font-medium">
          {totalUnread} unread
        </span>
      </div>
      <div className="p-4 space-y-2">
        {messages.slice(0, 3).map(msg => (
          <div 
            key={msg.conversation_id}
            className="flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-150 hover:shadow-sm"
            style={{ backgroundColor: 'var(--surface-2)' }}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{msg.customer_name}</p>
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
                  {msg.unread_count}
                </span>
              </div>
              <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{msg.last_message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Clocked In Employees Widget
const ClockedInWidget = ({ employees }) => {
  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <UserCheck className="h-5 w-5 text-emerald-500" />
          <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
            Clocked In
          </h2>
        </div>
        <Link to="/timeclock">
          <span className="text-xs text-blue-500 hover:underline">View all</span>
        </Link>
      </div>
      <div className="p-4">
        {(!employees || employees.length === 0) ? (
          <div className="text-center py-4">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No employees clocked in</p>
          </div>
        ) : (
          <div className="space-y-2">
            {employees.map(emp => (
              <div 
                key={emp.employee_id}
                className="flex items-center justify-between p-3 rounded-lg"
                style={{ backgroundColor: 'var(--surface-2)' }}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    {emp.status === 'on_break' ? (
                      <Coffee className="h-4 w-4 text-amber-500" />
                    ) : (
                      <UserCheck className="h-4 w-4 text-emerald-500" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm" style={{ color: 'var(--text)' }}>{emp.employee_name}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      Since {new Date(emp.clocked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
                <span 
                  className="px-2 py-0.5 rounded-full text-xs font-medium"
                  style={getStatusBadgeStyles(emp.status)}
                >
                  {emp.status === 'on_break' ? 'Break' : 'Working'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Today's Schedule Widget
const ScheduleWidget = ({ schedule }) => {
  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-purple-500" />
          <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
            Today's Schedule
          </h2>
        </div>
        <Link to="/jobs">
          <span className="text-xs text-blue-500 hover:underline">View all jobs</span>
        </Link>
      </div>
      <div className="p-4">
        {(!schedule || schedule.length === 0) ? (
          <div className="text-center py-4">
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No jobs due today</p>
          </div>
        ) : (
          <div className="space-y-2">
            {schedule.slice(0, 4).map(item => (
              <Link key={item.id} to={`/jobs/${item.id}`}>
                <div 
                  className="flex items-center justify-between p-3 rounded-lg transition-all duration-150 hover:shadow-sm cursor-pointer"
                  style={{ 
                    backgroundColor: item.priority === 'overdue' ? 'var(--danger-soft)' : 'var(--surface-2)',
                    border: item.priority === 'overdue' ? '1px solid var(--danger)' : '1px solid transparent'
                  }}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{item.name}</p>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{item.customer_name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.priority === 'overdue' && (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    )}
                    <span 
                      className="px-2 py-0.5 rounded-full text-xs font-medium"
                      style={getStatusBadgeStyles(item.status)}
                    >
                      {item.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Recent AI Documents Widget
const RecentAIDocumentsWidget = ({ documents }) => {
  const handleDownload = async (doc) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await axios.get(`${API}/documents/${doc.id}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const { file_data, file_type, original_filename } = res.data;
      
      const byteCharacters = atob(file_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: file_type });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Document downloaded');
    } catch (err) {
      toast.error('Failed to download');
    }
  };

  const handleView = async (doc) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await axios.get(`${API}/documents/${doc.id}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const { file_data, file_type } = res.data;
      
      const byteCharacters = atob(file_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: file_type });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (err) {
      toast.error('Failed to open document');
    }
  };

  const getToolName = (tags) => {
    const toolTag = tags?.find(t => t !== 'ai-generated');
    const toolNames = {
      'document_composer': 'Document Composer',
      'business_copywriter': 'Business Copywriter',
      'blog_creator': 'Blog Creator',
      'email_template': 'Email Generator',
      'job_post_creator': 'Job Post Creator',
      'social_media_creator': 'Social Media Creator'
    };
    return toolNames[toolTag] || 'AI Tool';
  };

  return (
    <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
      <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border-light)' }}>
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          <h2 className="font-heading text-base font-semibold" style={{ color: 'var(--text)' }}>
            Recent AI Documents
          </h2>
        </div>
        <Link to="/ai-tools">
          <span className="text-xs text-purple-500 hover:underline flex items-center gap-1">
            Create new <ArrowRight className="h-3 w-3" />
          </span>
        </Link>
      </div>
      <div className="p-4">
        {(!documents || documents.length === 0) ? (
          <div className="text-center py-6">
            <Sparkles className="h-8 w-8 mx-auto mb-2 text-purple-500/30" />
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No AI documents yet</p>
            <Link to="/ai-tools">
              <Button size="sm" variant="outline" className="mt-3 text-purple-500 border-purple-500/30">
                <Plus className="h-3 w-3 mr-1" /> Create Document
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map(doc => (
              <div 
                key={doc.id}
                className="flex items-center justify-between p-3 rounded-lg transition-all duration-150 hover:shadow-sm"
                style={{ backgroundColor: 'var(--surface-2)', border: '1px solid transparent' }}
              >
                <div className="flex-1 min-w-0 mr-3">
                  <p className="font-medium text-sm truncate" style={{ color: 'var(--text)' }}>{doc.name}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {getToolName(doc.tags)} • {formatDate(doc.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <button 
                    onClick={() => handleView(doc)}
                    className="p-1.5 rounded-md hover:bg-purple-500/10 transition-colors"
                    title="View"
                  >
                    <Eye className="h-4 w-4 text-purple-500" />
                  </button>
                  <button 
                    onClick={() => handleDownload(doc)}
                    className="p-1.5 rounded-md hover:bg-purple-500/10 transition-colors"
                    title="Download"
                  >
                    <Download className="h-4 w-4 text-purple-500" />
                  </button>
                  <Link to="/documents">
                    <button 
                      className="p-1.5 rounded-md hover:bg-purple-500/10 transition-colors"
                      title="Send to customer"
                    >
                      <Send className="h-4 w-4 text-purple-500" />
                    </button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const QuickActions = () => (
  <div className="rounded-xl" style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-light)' }}>
    <div className="px-4 sm:px-6 py-3 sm:py-4" style={{ borderBottom: '1px solid var(--border-light)' }}>
      <h2 className="font-heading text-sm sm:text-base font-semibold" style={{ color: 'var(--text)' }}>
        Quick Actions
      </h2>
    </div>
    <div className="p-3 sm:p-4 grid grid-cols-2 gap-2 sm:gap-3">
      <Link to="/customers">
        <button 
          className="w-full flex items-center justify-start gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-xs sm:text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-customer"
        >
          <Plus className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" style={{ color: 'var(--accent)' }} /> 
          <span className="truncate">New Customer</span>
        </button>
      </Link>
      <Link to="/jobs?filter=quotes">
        <button 
          className="w-full flex items-center justify-start gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-xs sm:text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-quote"
        >
          <Plus className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" style={{ color: 'var(--accent)' }} /> 
          <span className="truncate">New Quote</span>
        </button>
      </Link>
      <Link to="/jobs?filter=active">
        <button 
          className="w-full flex items-center justify-start gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-xs sm:text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-add-job"
        >
          <Plus className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" style={{ color: 'var(--accent)' }} /> 
          <span className="truncate">New Job</span>
        </button>
      </Link>
      <Link to="/timeclock">
        <button 
          className="w-full flex items-center justify-start gap-2 px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg text-xs sm:text-sm font-medium transition-all duration-150 hover:shadow-sm"
          style={{ backgroundColor: 'var(--surface-2)', color: 'var(--text)', border: '1px solid var(--border-light)' }}
          data-testid="quick-clock-in"
        >
          <Clock className="h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" style={{ color: 'var(--accent)' }} /> 
          <span className="truncate">Time Clock</span>
        </button>
      </Link>
    </div>
  </div>
);

export default function Dashboard() {
  const { user } = useAuth();
  const { 
    fetchDashboardStats, fetchCustomers, fetchJobs, fetchInvoices,
    dashboardStats, customers, jobs, invoices 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [unreadMessages, setUnreadMessages] = useState([]);
  const [clockedInEmployees, setClockedInEmployees] = useState([]);
  const [todaysSchedule, setTodaysSchedule] = useState([]);
  const [recentAIDocs, setRecentAIDocs] = useState([]);
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  
  const greeting = getGreeting();
  const GreetingIcon = greeting.icon;

  const handleInvoiceClick = (invoiceId) => {
    setPreviewInvoiceId(invoiceId);
    setIsInvoiceModalOpen(true);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      try {
        // Fetch all dashboard data in parallel
        await Promise.all([
          fetchDashboardStats(),
          fetchCustomers(),
          fetchJobs(),
          fetchInvoices(),
          // Fetch new widget data
          axios.get(`${API}/dashboard/pending-approvals`, { headers }).then(res => setPendingApprovals(res.data)).catch(() => {}),
          axios.get(`${API}/dashboard/unread-messages`, { headers }).then(res => setUnreadMessages(res.data)).catch(() => {}),
          axios.get(`${API}/dashboard/clocked-in`, { headers }).then(res => setClockedInEmployees(res.data)).catch(() => {}),
          axios.get(`${API}/dashboard/todays-schedule`, { headers }).then(res => setTodaysSchedule(res.data)).catch(() => {}),
          axios.get(`${API}/dashboard/recent-ai-documents`, { headers }).then(res => setRecentAIDocs(res.data)).catch(() => {}),
        ]);
      } catch (err) {
        console.error('Error loading dashboard:', err);
      }
      setLoading(false);
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }}></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in" data-testid="dashboard">
      {/* Personalized Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 sm:gap-3 mb-1">
            <GreetingIcon className={`h-6 w-6 sm:h-7 sm:w-7 ${greeting.color}`} />
            <h1 className="text-2xl sm:text-3xl font-bold font-heading tracking-tight" style={{ color: 'var(--text)' }}>
              {greeting.text}, {user?.full_name?.split(' ')[0] || 'there'}!
            </h1>
          </div>
          <p className="ml-8 sm:ml-10 text-sm sm:text-base" style={{ color: 'var(--text-muted)' }}>
            Here's what's happening at {user?.company_name || 'your shop'} today
          </p>
        </div>
        <div className="text-left sm:text-right ml-8 sm:ml-0">
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <StatCard
          title="Total Customers"
          value={dashboardStats?.total_customers || 0}
          icon={Users}
          href="/customers"
          accentColor="#2F8BFB"
        />
        <StatCard
          title="Active Jobs"
          value={dashboardStats?.active_jobs || 0}
          icon={Briefcase}
          href="/jobs"
          accentColor="#10B981"
        />
        <StatCard
          title="Pending Invoices"
          value={dashboardStats?.pending_invoices || 0}
          icon={Receipt}
          href="/invoices"
          accentColor="#F59E0B"
        />
        <StatCard
          title="Today's Revenue"
          value={formatCurrency(dashboardStats?.today_revenue || 0)}
          icon={TrendingUp}
          href="/financials"
          accentColor="#8B5CF6"
        />
      </div>

      {/* Overdue Alert */}
      {dashboardStats?.overdue_count > 0 && (
        <div 
          className="rounded-xl p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          style={{ backgroundColor: 'var(--danger-soft)', border: '1px solid var(--danger)' }}
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" style={{ color: 'var(--danger)' }} />
            <div>
              <p className="font-medium text-sm sm:text-base" style={{ color: 'var(--text)' }}>
                {dashboardStats.overdue_count} Overdue Invoice{dashboardStats.overdue_count > 1 ? 's' : ''}
              </p>
              <p className="text-xs sm:text-sm" style={{ color: 'var(--text-muted)' }}>
                Total: {formatCurrency(dashboardStats.overdue_total)}
              </p>
            </div>
          </div>
          <Link to="/invoices?status=overdue">
            <Button 
              size="sm" 
              data-testid="view-overdue"
              className="text-white w-full sm:w-auto"
              style={{ backgroundColor: 'var(--danger)' }}
            >
              View Overdue
            </Button>
          </Link>
        </div>
      )}

      {/* Main Content Grid - responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Left Column - Schedule & Approvals */}
        <div className="space-y-4 sm:space-y-6">
          <ScheduleWidget schedule={todaysSchedule} />
          <PendingApprovalsWidget approvals={pendingApprovals} />
        </div>
        
        {/* Middle Column - Messages & Clocked In */}
        <div className="space-y-4 sm:space-y-6">
          <MessagesWidget messages={unreadMessages} />
          <ClockedInWidget employees={clockedInEmployees} />
        </div>
        
        {/* Right Column - Quick Actions & Recent AI Docs */}
        <div className="space-y-4 sm:space-y-6">
          <QuickActions />
          <RecentAIDocumentsWidget documents={recentAIDocs} />
        </div>
      </div>

      {/* Onboarding Checklist - Shows for new users */}
      <OnboardingChecklist />

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
