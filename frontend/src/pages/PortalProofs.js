import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { 
  Loader2, Image, CheckCircle, XCircle, RefreshCw, ChevronLeft,
  AlertCircle, ZoomIn, Download
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PortalProofs() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [proofs, setProofs] = useState([]);
  const [filter, setFilter] = useState('pending');
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  const fetchProofs = useCallback(async () => {
    const token = localStorage.getItem('portal_token');
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }

    try {
      const url = filter === 'all'
        ? `${API_URL}/api/portal/proofs`
        : `${API_URL}/api/portal/proofs?status=${filter}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProofs(data);
      } else if (response.status === 401) {
        navigate('/customer-portal/login');
      }
    } catch (err) {
      console.error('Error fetching proofs:', err);
    } finally {
      setLoading(false);
    }
  }, [navigate, filter]);

  useEffect(() => {
    fetchProofs();
  }, [fetchProofs]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  const getStatusConfig = (status) => {
    const configs = {
      pending: { color: 'bg-amber-100 text-amber-700', icon: AlertCircle, label: 'Awaiting Review' },
      approved: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: 'Approved' },
      rejected: { color: 'bg-red-100 text-red-700', icon: XCircle, label: 'Rejected' },
      revision_requested: { color: 'bg-blue-100 text-blue-700', icon: RefreshCw, label: 'Revision Requested' },
    };
    return configs[status] || configs.pending;
  };

  const filters = [
    { value: 'pending', label: 'Pending Review' },
    { value: 'all', label: 'All Proofs' },
    { value: 'approved', label: 'Approved' },
  ];

  return (
    <PortalLayout activeNav="proofs" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Artwork Approvals</h2>
          <p className="text-slate-600 mt-1">Review and approve designs for your projects</p>
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
        ) : proofs.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {proofs.map((proof) => {
              const statusConfig = getStatusConfig(proof.status);
              return (
                <Card key={proof.id} className="border-slate-200 overflow-hidden">
                  {/* Image Preview */}
                  <div className="aspect-video bg-slate-100 relative group">
                    {proof.file_url ? (
                      <img 
                        src={proof.file_url} 
                        alt={proof.file_name}
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Image className="h-12 w-12 text-slate-300" />
                      </div>
                    )}
                    {proof.status === 'pending' && (
                      <div className="absolute inset-0 bg-amber-500/90 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link to={`/customer-portal/proofs/${proof.id}`}>
                          <Button className="bg-white text-amber-600 hover:bg-amber-50">
                            Review Now
                          </Button>
                        </Link>
                      </div>
                    )}
                  </div>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-slate-900">
                          {proof.job?.name || `Job #${proof.job_id?.slice(0, 8)}`}
                        </p>
                        <p className="text-sm text-slate-500">Version {proof.version}</p>
                      </div>
                      <Badge className={statusConfig.color}>
                        {statusConfig.label}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-500 mb-3">{formatDate(proof.created_at)}</p>
                    {proof.description && (
                      <p className="text-sm text-slate-600 mb-3">{proof.description}</p>
                    )}
                    <Link to={`/customer-portal/proofs/${proof.id}`}>
                      <Button 
                        variant={proof.status === 'pending' ? 'default' : 'outline'} 
                        size="sm" 
                        className={`w-full ${proof.status === 'pending' ? 'bg-teal-500 hover:bg-teal-600' : ''}`}
                      >
                        {proof.status === 'pending' ? 'Review & Respond' : 'View Details'}
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <Image className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">
                {filter === 'pending' ? 'No proofs awaiting your review' : 'No proofs found'}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

export function PortalProofDetail() {
  const navigate = useNavigate();
  const { proofId } = useParams();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [proof, setProof] = useState(null);
  const [showImageModal, setShowImageModal] = useState(false);
  const [responseModal, setResponseModal] = useState({ open: false, type: null });
  const [comment, setComment] = useState('');
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';

  useEffect(() => {
    const fetchProof = async () => {
      const token = localStorage.getItem('portal_token');
      if (!token) {
        navigate('/customer-portal/login');
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/portal/proofs/${proofId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setProof(data);
        } else if (response.status === 401) {
          navigate('/customer-portal/login');
        }
      } catch (err) {
        console.error('Error fetching proof:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProof();
  }, [navigate, proofId]);

  const handleRespond = async (status) => {
    const token = localStorage.getItem('portal_token');
    setSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/api/portal/proofs/${proofId}/respond`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, comment: comment || null })
      });

      if (response.ok) {
        const updated = await response.json();
        setProof(updated);
        setResponseModal({ open: false, type: null });
        setComment('');
        toast.success(
          status === 'approved' ? 'Proof approved successfully!' : 
          status === 'rejected' ? 'Proof rejected' : 
          'Revision requested'
        );
      } else {
        const err = await response.json();
        toast.error(err.detail || 'Failed to submit response');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusConfig = (status) => {
    const configs = {
      pending: { color: 'bg-amber-100 text-amber-700', label: 'Awaiting Your Review' },
      approved: { color: 'bg-green-100 text-green-700', label: 'Approved' },
      rejected: { color: 'bg-red-100 text-red-700', label: 'Rejected' },
      revision_requested: { color: 'bg-blue-100 text-blue-700', label: 'Revision Requested' },
    };
    return configs[status] || configs.pending;
  };

  if (loading) {
    return (
      <PortalLayout activeNav="proofs" customerName={customerName}>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        </div>
      </PortalLayout>
    );
  }

  if (!proof) {
    return (
      <PortalLayout activeNav="proofs" customerName={customerName}>
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-slate-700">Proof not found</p>
            <Link to="/customer-portal/proofs">
              <Button className="mt-4">Back to Proofs</Button>
            </Link>
          </CardContent>
        </Card>
      </PortalLayout>
    );
  }

  const statusConfig = getStatusConfig(proof.status);

  return (
    <PortalLayout activeNav="proofs" customerName={customerName}>
      <div className="space-y-6">
        {/* Back Button */}
        <Link to="/customer-portal/proofs" className="inline-flex items-center text-sm text-slate-600 hover:text-teal-600">
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back to Proofs
        </Link>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Image Preview */}
          <div className="lg:col-span-2">
            <Card className="border-slate-200 overflow-hidden">
              <div 
                className="bg-slate-100 aspect-video relative cursor-pointer group"
                onClick={() => setShowImageModal(true)}
              >
                {proof.file_url ? (
                  <>
                    <img 
                      src={proof.file_url} 
                      alt={proof.file_name}
                      className="w-full h-full object-contain"
                    />
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <ZoomIn className="h-8 w-8 text-white" />
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Image className="h-16 w-16 text-slate-300" />
                  </div>
                )}
              </div>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-500">{proof.file_name}</p>
                  {proof.file_url && (
                    <a href={proof.file_url} target="_blank" rel="noopener noreferrer">
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    </a>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Details & Actions */}
          <div className="space-y-4">
            <Card className="border-slate-200">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">Proof Details</CardTitle>
                    <CardDescription>Version {proof.version}</CardDescription>
                  </div>
                  <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-slate-500">Project</p>
                  <p className="font-medium text-slate-900">
                    {proof.job?.name || `Job #${proof.job_id?.slice(0, 8)}`}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Uploaded</p>
                  <p className="font-medium text-slate-900">{formatDate(proof.created_at)}</p>
                </div>
                {proof.description && (
                  <div>
                    <p className="text-sm text-slate-500">Description</p>
                    <p className="text-slate-900">{proof.description}</p>
                  </div>
                )}
                {proof.customer_comment && (
                  <div>
                    <p className="text-sm text-slate-500">Your Comment</p>
                    <p className="text-slate-900">{proof.customer_comment}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Action Buttons */}
            {proof.status === 'pending' && (
              <Card className="border-teal-200 bg-teal-50">
                <CardContent className="p-4 space-y-3">
                  <p className="text-sm font-medium text-teal-800">Your Response</p>
                  <Button 
                    className="w-full bg-green-500 hover:bg-green-600"
                    onClick={() => setResponseModal({ open: true, type: 'approved' })}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve Design
                  </Button>
                  <Button 
                    variant="outline"
                    className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
                    onClick={() => setResponseModal({ open: true, type: 'revision_requested' })}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Request Revision
                  </Button>
                  <Button 
                    variant="outline"
                    className="w-full border-red-300 text-red-700 hover:bg-red-50"
                    onClick={() => setResponseModal({ open: true, type: 'rejected' })}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject Design
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Full Image Modal */}
      <Dialog open={showImageModal} onOpenChange={setShowImageModal}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{proof?.file_name}</DialogTitle>
          </DialogHeader>
          <div className="bg-slate-100 rounded-lg overflow-hidden">
            <img 
              src={proof?.file_url} 
              alt={proof?.file_name}
              className="w-full h-auto"
            />
          </div>
        </DialogContent>
      </Dialog>

      {/* Response Modal */}
      <Dialog open={responseModal.open} onOpenChange={(open) => setResponseModal({ open, type: responseModal.type })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {responseModal.type === 'approved' && 'Approve Design'}
              {responseModal.type === 'rejected' && 'Reject Design'}
              {responseModal.type === 'revision_requested' && 'Request Revision'}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <label className="text-sm font-medium text-slate-700">
              {responseModal.type === 'approved' ? 'Additional comments (optional)' : 'Please provide feedback'}
            </label>
            <Textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={
                responseModal.type === 'approved' 
                  ? 'Any final notes...' 
                  : 'Describe the changes needed or reason for rejection...'
              }
              className="mt-2"
              rows={4}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setResponseModal({ open: false, type: null })}>
              Cancel
            </Button>
            <Button 
              onClick={() => handleRespond(responseModal.type)}
              disabled={submitting || (responseModal.type !== 'approved' && !comment.trim())}
              className={
                responseModal.type === 'approved' ? 'bg-green-500 hover:bg-green-600' :
                responseModal.type === 'rejected' ? 'bg-red-500 hover:bg-red-600' :
                'bg-blue-500 hover:bg-blue-600'
              }
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {responseModal.type === 'approved' && 'Confirm Approval'}
              {responseModal.type === 'rejected' && 'Confirm Rejection'}
              {responseModal.type === 'revision_requested' && 'Submit Revision Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PortalLayout>
  );
}

export default PortalProofs;
