import { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { 
  Loader2, LogOut, FileText, Briefcase, Receipt, MessageSquare, 
  Image, Calendar, User, Home, Download, Eye, Clock, FileIcon,
  FileImage, FileSpreadsheet, File, ExternalLink, FolderOpen
} from 'lucide-react';
import { toast } from 'sonner';
import { getPortalToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Portal Layout Wrapper (same as other portal pages)
function PortalLayout({ children, activeNav, customerName }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('portal_token');
    localStorage.removeItem('portal_customer_id');
    localStorage.removeItem('portal_customer_name');
    navigate('/customer-portal/login');
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/customer-portal' },
    { id: 'orders', label: 'Orders', icon: Briefcase, path: '/customer-portal/orders' },
    { id: 'forms', label: 'Forms / Questionnaires', icon: FileText, path: '/customer-portal/forms' },
    { id: 'quotes', label: 'Quotes', icon: FileText, path: '/customer-portal/quotes' },
    { id: 'invoices', label: 'Invoices', icon: Receipt, path: '/customer-portal/invoices' },
    { id: 'documents', label: 'Documents', icon: FolderOpen, path: '/customer-portal/documents' },
    { id: 'messages', label: 'Messages', icon: MessageSquare, path: '/customer-portal/messages' },
    { id: 'proofs', label: 'Artwork Approvals', icon: Image, path: '/customer-portal/proofs' },
    { id: 'appointments', label: 'Appointments', icon: Calendar, path: '/customer-portal/appointments' },
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

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}

const getFileIcon = (fileType) => {
  if (fileType?.includes('pdf')) return FileText;
  if (fileType?.includes('image')) return FileImage;
  if (fileType?.includes('sheet') || fileType?.includes('excel') || fileType?.includes('csv')) return FileSpreadsheet;
  return File;
};

const formatFileSize = (bytes) => {
  if (!bytes) return 'N/A';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const CATEGORY_LABELS = {
  'contract': 'Contract',
  'invoice_template': 'Invoice',
  'work_order': 'Work Order',
  'artwork': 'Artwork',
  'proof': 'Proof',
  'permit': 'Permit',
  'insurance': 'Insurance',
  'warranty': 'Warranty',
  'quote_template': 'Quote',
  'customer_form': 'Form',
  'internal': 'Internal',
  'other': 'Document'
};

export default function PortalDocuments() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [customerName, setCustomerName] = useState('');

  const fetchDocuments = useCallback(async () => {
    const token = getPortalToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/api/portal/documents`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDocuments(response.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      if (err.response?.status === 401) {
        navigate('/customer-portal/login');
      } else {
        toast.error('Failed to load documents');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    const name = localStorage.getItem('portal_customer_name');
    if (name) setCustomerName(name);
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDownload = async (doc) => {
    const fileUrl = doc.document?.file_url;
    if (fileUrl) {
      window.open(fileUrl, '_blank');
      toast.success('Document download started');
    } else {
      toast.error('Document file not available');
    }
  };

  const handleView = async (doc) => {
    const fileUrl = doc.document?.file_url;
    if (fileUrl) {
      window.open(fileUrl, '_blank');
      
      // Mark as viewed
      const token = getPortalToken();
      try {
        await axios.get(`${API_URL}/api/portal/documents/${doc.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        // Refresh to update viewed status
        fetchDocuments();
      } catch (err) {
        console.error('Error marking document as viewed:', err);
      }
    } else {
      toast.error('Document file not available');
    }
  };

  if (loading) {
    return (
      <PortalLayout activeNav="documents" customerName={customerName}>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  return (
    <PortalLayout activeNav="documents" customerName={customerName}>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-slate-900" data-testid="portal-documents-title">Documents</h2>
          <p className="text-slate-600 mt-1">View and download documents shared with you</p>
        </div>

        {/* Documents List */}
        {documents.length === 0 ? (
          <Card className="border-slate-200 bg-white">
            <CardContent className="py-12 text-center">
              <FolderOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No Documents Yet</h3>
              <p className="text-slate-500">
                Documents shared by your sign shop will appear here.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {documents.map((doc) => {
              const FileIconComponent = getFileIcon(doc.document?.file_type);
              const isViewed = !!doc.viewed_at;
              
              return (
                <Card 
                  key={doc.id} 
                  className={`border-slate-200 bg-white hover:shadow-md transition-shadow ${!isViewed ? 'border-l-4 border-l-teal-500' : ''}`}
                  data-testid={`portal-document-${doc.id}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      {/* File Icon */}
                      <div className="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                        <FileIconComponent className="h-6 w-6 text-slate-500" />
                      </div>
                      
                      {/* Document Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <h3 className="font-medium text-slate-900 truncate">
                              {doc.document?.name || 'Untitled Document'}
                            </h3>
                            <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
                              <span>{formatFileSize(doc.document?.file_size)}</span>
                              <span>•</span>
                              <span>{CATEGORY_LABELS[doc.document?.category] || 'Document'}</span>
                            </div>
                            {doc.message && (
                              <p className="mt-2 text-sm text-slate-600 italic">"{doc.message}"</p>
                            )}
                          </div>
                          
                          {/* Status Badge */}
                          {!isViewed && (
                            <Badge className="bg-teal-100 text-teal-700 flex-shrink-0">New</Badge>
                          )}
                        </div>
                        
                        {/* Metadata */}
                        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Shared {formatDate(doc.created_at)}
                          </span>
                          {isViewed && (
                            <span className="flex items-center gap-1">
                              <Eye className="h-3 w-3" />
                              Viewed {formatDate(doc.viewed_at)}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Actions */}
                      <div className="flex gap-2 flex-shrink-0">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleView(doc)}
                          className="text-slate-600"
                          data-testid={`view-doc-${doc.id}`}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          View
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleDownload(doc)}
                          className="bg-teal-500 hover:bg-teal-600"
                          data-testid={`download-doc-${doc.id}`}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </PortalLayout>
  );
}
