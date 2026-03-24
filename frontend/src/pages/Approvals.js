import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../components/ui/table';
import {
  Image, Upload, Clock, CheckCircle, AlertTriangle, RefreshCw, Send,
  Eye, Trash2, Plus, Filter, X
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Approvals() {
  const { user } = useApp();
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, revisions: 0 });
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [customers, setCustomers] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [previewProof, setPreviewProof] = useState(null);
  
  // Form state
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedJob, setSelectedJob] = useState('');
  const [description, setDescription] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [watermarkedUrl, setWatermarkedUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadApprovals();
  }, [filter]);

  useEffect(() => {
    if (selectedCustomer) {
      loadJobs(selectedCustomer);
    }
  }, [selectedCustomer]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setLoading(false);
        return;
      }
      
      // Load stats
      const statsRes = await fetch(`${API}/api/approvals/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      
      // Load customers
      const customersRes = await fetch(`${API}/api/approvals/customers/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (customersRes.ok) {
        const customersData = await customersRes.json();
        setCustomers(customersData);
      }
      
      await loadApprovals();
    } catch (err) {
      console.error('Error loading data:', err);
    }
    setLoading(false);
  };

  const loadApprovals = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;
      
      let url = `${API}/api/approvals`;
      
      if (filter !== 'all') {
        url += `?status=${filter}`;
      }
      
      const res = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setApprovals(data);
      }
    } catch (err) {
      console.error('Error loading approvals:', err);
    }
  };

  const loadJobs = async (customerId) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API}/api/approvals/jobs/list?customer_id=${customerId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      console.error('Error loading jobs:', err);
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }
    
    setUploadedFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewUrl(event.target.result);
      // Apply watermark after image loads
      applyWatermark(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const applyWatermark = (imageUrl) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const img = new window.Image();
    
    img.onload = () => {
      // Set canvas size to image size
      canvas.width = img.width;
      canvas.height = img.height;
      
      // Draw the original image
      ctx.drawImage(img, 0, 0);
      
      // Apply semi-transparent overlay
      ctx.fillStyle = 'rgba(0, 0, 0, 0.03)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Watermark settings
      const fontSize = Math.max(20, canvas.width / 30);
      ctx.font = `bold ${fontSize}px Arial`;
      ctx.fillStyle = 'rgba(128, 128, 128, 0.4)';
      ctx.textAlign = 'center';
      
      // Company name (from user context or tenant)
      const companyName = user?.company_name || 'SIGN SHOP';
      
      // Draw diagonal watermarks
      ctx.save();
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate(-Math.PI / 6); // -30 degrees
      
      // Draw multiple watermarks
      for (let y = -canvas.height; y < canvas.height; y += fontSize * 4) {
        for (let x = -canvas.width; x < canvas.width; x += fontSize * 12) {
          ctx.fillText(companyName, x, y);
        }
      }
      ctx.restore();
      
      // Add bottom disclaimer
      const disclaimerFontSize = Math.max(14, canvas.width / 50);
      ctx.font = `${disclaimerFontSize}px Arial`;
      ctx.fillStyle = 'rgba(50, 50, 50, 0.8)';
      ctx.textAlign = 'center';
      
      // Background for disclaimer
      const disclaimerText = `PROOF ONLY - Artwork remains property of ${companyName} until final payment is received`;
      const textWidth = ctx.measureText(disclaimerText).width;
      const padding = 10;
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(
        (canvas.width - textWidth) / 2 - padding,
        canvas.height - disclaimerFontSize - padding * 3,
        textWidth + padding * 2,
        disclaimerFontSize + padding * 2
      );
      
      ctx.fillStyle = 'rgba(50, 50, 50, 0.9)';
      ctx.fillText(disclaimerText, canvas.width / 2, canvas.height - padding * 2);
      
      // Get watermarked image URL
      const watermarked = canvas.toDataURL('image/jpeg', 0.9);
      setWatermarkedUrl(watermarked);
    };
    
    img.src = imageUrl;
  };

  const handleSubmit = async () => {
    if (!selectedCustomer || !selectedJob || !uploadedFile) {
      toast.error('Please select customer, job, and upload artwork');
      return;
    }
    
    setUploading(true);
    
    try {
      const token = localStorage.getItem('auth_token');
      
      // Create the approval with base64 image
      const approvalRes = await fetch(`${API}/api/approvals`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: selectedCustomer,
          job_id: selectedJob,
          file_url: watermarkedUrl, // Store watermarked version
          file_name: uploadedFile.name,
          description: description
        })
      });
      
      if (!approvalRes.ok) {
        const errData = await approvalRes.json();
        throw new Error(errData.detail || 'Failed to create approval');
      }
      
      toast.success('Artwork sent for approval!');
      setIsDialogOpen(false);
      resetForm();
      loadData();
    } catch (err) {
      console.error('Error:', err);
      toast.error(err.message || 'Failed to send artwork for approval');
    }
    
    setUploading(false);
  };

  const resetForm = () => {
    setSelectedCustomer('');
    setSelectedJob('');
    setDescription('');
    setUploadedFile(null);
    setPreviewUrl('');
    setWatermarkedUrl('');
    setJobs([]);
  };

  const handleResend = async (proofId) => {
    try {
      const token = localStorage.getItem('auth_token');
      await fetch(`${API}/api/approvals/${proofId}/resend`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      toast.success('Reminder sent to customer');
    } catch (err) {
      toast.error('Failed to send reminder');
    }
  };

  const handleDelete = async (proofId) => {
    if (!window.confirm('Are you sure you want to delete this proof?')) return;
    
    try {
      const token = localStorage.getItem('auth_token');
      await fetch(`${API}/api/approvals/${proofId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      toast.success('Proof deleted');
      loadData();
    } catch (err) {
      toast.error('Failed to delete proof');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      approved: 'bg-green-500/20 text-green-400 border-green-500/30',
      revision_requested: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      rejected: 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    const labels = {
      pending: 'Awaiting Approval',
      approved: 'Approved',
      revision_requested: 'Revisions Needed',
      rejected: 'Rejected'
    };
    return (
      <Badge className={`${styles[status] || styles.pending} border`}>
        {labels[status] || status}
      </Badge>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const StatCard = ({ title, value, icon: Icon, color, filterKey, isActive }) => (
    <Card 
      className={`cursor-pointer transition-all hover:scale-105 ${isActive ? 'ring-2 ring-primary' : ''}`}
      onClick={() => setFilter(filterKey)}
      data-testid={`stat-${filterKey}`}
    >
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">{title}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
          </div>
          <div className={`p-3 rounded-full ${color.replace('text-', 'bg-').replace('-400', '-500/20')}`}>
            <Icon className={`h-6 w-6 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Artwork Approvals</h1>
          <p className="text-slate-300">Manage and track artwork proofs for customer approval</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="new-approval-btn">
              <Plus className="h-4 w-4 mr-2" />
              New Approval Request
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Send Artwork for Approval</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              {/* Customer Selection */}
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select value={selectedCustomer} onValueChange={setSelectedCustomer}>
                  <SelectTrigger data-testid="customer-select">
                    <SelectValue placeholder="Select a customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map(c => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* Job Selection */}
              <div className="space-y-2">
                <Label>Job *</Label>
                <Select 
                  value={selectedJob} 
                  onValueChange={setSelectedJob}
                  disabled={!selectedCustomer || jobs.length === 0}
                >
                  <SelectTrigger data-testid="job-select">
                    <SelectValue placeholder={!selectedCustomer ? "Select customer first" : jobs.length === 0 ? "No active jobs" : "Select a job"} />
                  </SelectTrigger>
                  <SelectContent>
                    {jobs.map(j => (
                      <SelectItem key={j.id} value={j.id}>{j.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* File Upload */}
              <div className="space-y-2">
                <Label>Artwork File *</Label>
                <div 
                  className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  {!previewUrl ? (
                    <>
                      <Upload className="h-10 w-10 mx-auto mb-2 text-gray-500" />
                      <p className="text-gray-500">Click to upload artwork</p>
                      <p className="text-xs text-gray-500 mt-1">PNG, JPG up to 10MB</p>
                    </>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-green-400">Preview with Watermark:</p>
                      <img 
                        src={watermarkedUrl || previewUrl} 
                        alt="Preview" 
                        className="max-h-48 mx-auto rounded-lg"
                      />
                      <p className="text-xs text-gray-500">{uploadedFile?.name}</p>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleFileChange}
                    data-testid="file-input"
                  />
                </div>
              </div>
              
              {/* Description */}
              <div className="space-y-2">
                <Label>Notes for Customer (optional)</Label>
                <Textarea
                  placeholder="Add any notes or instructions for the customer..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  data-testid="description-input"
                />
              </div>
              
              {/* Hidden canvas for watermarking */}
              <canvas ref={canvasRef} className="hidden" />
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => { setIsDialogOpen(false); resetForm(); }}>
                Cancel
              </Button>
              <Button 
                onClick={handleSubmit} 
                disabled={uploading || !selectedCustomer || !selectedJob || !uploadedFile}
                data-testid="submit-approval-btn"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Send for Approval
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Proofs"
          value={stats.total}
          icon={Image}
          color="text-blue-400"
          filterKey="all"
          isActive={filter === 'all'}
        />
        <StatCard
          title="Awaiting Approval"
          value={stats.pending}
          icon={Clock}
          color="text-yellow-400"
          filterKey="pending"
          isActive={filter === 'pending'}
        />
        <StatCard
          title="Approved"
          value={stats.approved}
          icon={CheckCircle}
          color="text-green-400"
          filterKey="approved"
          isActive={filter === 'approved'}
        />
        <StatCard
          title="Needs Revisions"
          value={stats.revisions}
          icon={AlertTriangle}
          color="text-orange-400"
          filterKey="revision_requested"
          isActive={filter === 'revision_requested'}
        />
      </div>

      {/* Filter indicator */}
      {filter !== 'all' && (
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-500">
            Showing: {filter === 'pending' ? 'Awaiting Approval' : filter === 'approved' ? 'Approved' : 'Needs Revisions'}
          </span>
          <Button variant="ghost" size="sm" onClick={() => setFilter('all')}>
            <X className="h-4 w-4 mr-1" />
            Clear filter
          </Button>
        </div>
      )}

      {/* Approvals Table */}
      <Card>
        <CardHeader>
          <CardTitle>Approval Requests</CardTitle>
        </CardHeader>
        <CardContent>
          {approvals.length === 0 ? (
            <div className="text-center py-12">
              <Image className="h-12 w-12 mx-auto mb-4 text-gray-500" />
              <p className="text-gray-500">No approval requests found</p>
              <p className="text-sm text-gray-500 mt-1">
                Click "New Approval Request" to send artwork to a customer
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Preview</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Job</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Sent</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {approvals.map(proof => (
                  <TableRow key={proof.id} data-testid={`proof-row-${proof.id}`}>
                    <TableCell>
                      <div 
                        className="w-16 h-16 rounded-lg overflow-hidden bg-gray-50 cursor-pointer hover:opacity-80 transition-opacity"
                        onClick={() => setPreviewProof(proof)}
                      >
                        {proof.file_url ? (
                          <img 
                            src={proof.thumbnail_url || proof.file_url} 
                            alt="Proof" 
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Image className="h-6 w-6 text-gray-500" />
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{proof.customer_name}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm">{proof.job_name}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">v{proof.version}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(proof.status)}</TableCell>
                    <TableCell>
                      <p className="text-sm text-gray-500">{formatDate(proof.created_at)}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => setPreviewProof(proof)}
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {proof.status === 'pending' && (
                          <Button 
                            variant="ghost" 
                            size="icon"
                            onClick={() => handleResend(proof.id)}
                            title="Send Reminder"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                        )}
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => handleDelete(proof.id)}
                          title="Delete"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Preview Dialog */}
      <Dialog open={!!previewProof} onOpenChange={() => setPreviewProof(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              Proof Preview - {previewProof?.job_name} (Version {previewProof?.version})
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-lg overflow-hidden bg-gray-50">
              {previewProof?.file_url && (
                <img 
                  src={previewProof.file_url} 
                  alt="Proof" 
                  className="w-full max-h-[60vh] object-contain"
                />
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Customer</p>
                <p className="font-medium">{previewProof?.customer_name}</p>
              </div>
              <div>
                <p className="text-gray-500">Status</p>
                {previewProof && getStatusBadge(previewProof.status)}
              </div>
              {previewProof?.description && (
                <div className="col-span-2">
                  <p className="text-gray-500">Notes</p>
                  <p>{previewProof.description}</p>
                </div>
              )}
              {previewProof?.customer_comment && (
                <div className="col-span-2">
                  <p className="text-gray-500">Customer Feedback</p>
                  <p className="p-3 bg-gray-50 rounded-lg">{previewProof.customer_comment}</p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
