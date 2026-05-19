import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../../context/AppContext';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Separator } from '../../components/ui/separator';
import { Switch } from '../../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { 
  FileText, Upload, Search, Filter, FolderOpen, 
  Download, Trash2, Eye, Link2, Tag, Clock,
  FileImage, FileSpreadsheet, File, Plus, X,
  Archive, MoreVertical, CheckCircle2, HardDrive,
  Sparkles, Wand2, Send, Mail, Globe, ClipboardList
} from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '../../lib/utils';
import { SignatureSection } from '../../components/SignatureSection';

const CATEGORIES = [
  { value: 'contract', label: 'Contract', color: 'bg-blue-500/20 text-blue-400' },
  { value: 'invoice_template', label: 'Invoice Template', color: 'bg-green-500/20 text-green-400' },
  { value: 'work_order', label: 'Work Order', color: 'bg-yellow-500/20 text-yellow-400' },
  { value: 'artwork', label: 'Artwork', color: 'bg-purple-500/20 text-purple-400' },
  { value: 'proof', label: 'Proof', color: 'bg-pink-500/20 text-pink-400' },
  { value: 'permit', label: 'Permit', color: 'bg-orange-500/20 text-orange-400' },
  { value: 'insurance', label: 'Insurance', color: 'bg-cyan-500/20 text-cyan-400' },
  { value: 'warranty', label: 'Warranty', color: 'bg-teal-500/20 text-teal-400' },
  { value: 'quote_template', label: 'Quote Template', color: 'bg-indigo-500/20 text-indigo-400' },
  { value: 'customer_form', label: 'Customer Form', color: 'bg-rose-500/20 text-rose-400' },
  { value: 'internal', label: 'Internal', color: 'bg-slate-500/20 text-slate-400' },
  { value: 'other', label: 'Other', color: 'bg-gray-500/20 text-gray-400' },
];

const getFileIcon = (fileType) => {
  if (fileType?.includes('pdf')) return FileText;
  if (fileType?.includes('image')) return FileImage;
  if (fileType?.includes('sheet') || fileType?.includes('excel') || fileType?.includes('csv')) return FileSpreadsheet;
  return File;
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const getCategoryInfo = (category) => {
  return CATEGORIES.find(c => c.value === category) || CATEGORIES[CATEGORIES.length - 1];
};

export default function Documents() {
  const { api, customers, fetchCustomers } = useApp();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showTemplatesOnly, setShowTemplatesOnly] = useState(false);
  
  // Upload dialog
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadForm, setUploadForm] = useState({
    name: '',
    description: '',
    category: 'other',
    is_template: false,
    tags: ''
  });
  const fileInputRef = useRef(null);
  
  // View dialog
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);
  
  // Send dialog
  const [isSendOpen, setIsSendOpen] = useState(false);
  const [sendDoc, setSendDoc] = useState(null);
  const [sendMethod, setSendMethod] = useState('email'); // 'email' or 'portal'
  const [sendCustomerId, setSendCustomerId] = useState('');
  const [sendMessage, setSendMessage] = useState('');
  const [sendIncludeAttachment, setSendIncludeAttachment] = useState(true);
  const [sendNotifyCustomer, setSendNotifyCustomer] = useState(true);
  const [sending, setSending] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (showTemplatesOnly) params.append('is_template', 'true');
      if (searchQuery) params.append('search', searchQuery);
      
      const [docsRes, statsRes] = await Promise.all([
        api.get(`/documents?${params.toString()}`),
        api.get('/documents/stats'),
        fetchCustomers()
      ]);
      
      setDocuments(docsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Error loading documents:', err);
      toast.error('Failed to load documents');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [selectedCategory, showTemplatesOnly, searchQuery]);

  // Handle opening send dialog
  const handleSendDocument = (doc) => {
    setSendDoc(doc);
    setSendMethod('email');
    setSendCustomerId('');
    setSendMessage('');
    setSendIncludeAttachment(true);
    setSendNotifyCustomer(true);
    setIsSendOpen(true);
  };

  // Handle sending document
  const handleSend = async () => {
    if (!sendCustomerId) {
      toast.error('Please select a customer');
      return;
    }
    
    setSending(true);
    try {
      if (sendMethod === 'form') {
        // Navigate to questionnaire creator with document context
        navigate(`/questionnaires?from_doc=${sendDoc.id}&customer=${sendCustomerId}`);
        setIsSendOpen(false);
        toast.success('Redirecting to form creator...');
      } else if (sendMethod === 'email') {
        await api.post(`/documents/${sendDoc.id}/send-email`, {
          customer_id: sendCustomerId,
          message: sendMessage,
          include_attachment: sendIncludeAttachment
        });
        toast.success('Document sent via email');
      } else {
        await api.post(`/documents/${sendDoc.id}/send-to-portal`, {
          customer_id: sendCustomerId,
          message: sendMessage,
          notify_customer: sendNotifyCustomer
        });
        toast.success('Document sent to customer portal');
      }
      if (sendMethod !== 'form') setIsSendOpen(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send document');
    }
    setSending(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Check file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Maximum size is 10MB');
      return;
    }
    
    setUploadFile(file);
    // Auto-fill name from filename
    if (!uploadForm.name) {
      setUploadForm(prev => ({ ...prev, name: file.name.replace(/\.[^/.]+$/, '') }));
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      toast.error('Please select a file');
      return;
    }
    if (!uploadForm.name.trim()) {
      toast.error('Please enter a document name');
      return;
    }
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('name', uploadForm.name);
      formData.append('description', uploadForm.description || '');
      formData.append('category', uploadForm.category);
      formData.append('is_template', uploadForm.is_template.toString());
      formData.append('tags', uploadForm.tags);
      
      await api.post('/documents', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('Document uploaded successfully');
      setIsUploadOpen(false);
      resetUploadForm();
      await loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload document');
    }
    setUploading(false);
  };

  const resetUploadForm = () => {
    setUploadFile(null);
    setUploadForm({
      name: '',
      description: '',
      category: 'other',
      is_template: false,
      tags: ''
    });
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleView = async (doc) => {
    setSelectedDoc(doc);
    setIsViewOpen(true);
  };

  const handleDownload = async (doc) => {
    try {
      const res = await api.get(`/documents/${doc.id}/download`);
      const { file_data, file_type, original_filename } = res.data;
      
      // Create blob and download
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
      
      toast.success('Download started');
    } catch (err) {
      toast.error('Failed to download document');
    }
  };

  const handleDelete = async (doc) => {
    if (!confirm(`Are you sure you want to archive "${doc.name}"?`)) return;
    
    try {
      await api.delete(`/documents/${doc.id}`);
      toast.success('Document archived');
      await loadData();
    } catch (err) {
      toast.error('Failed to archive document');
    }
  };

  const handleToggleTemplate = async (doc) => {
    try {
      await api.put(`/documents/${doc.id}`, { is_template: !doc.is_template });
      toast.success(doc.is_template ? 'Removed from templates' : 'Marked as template');
      await loadData();
    } catch (err) {
      toast.error('Failed to update document');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="documents-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight" style={{ color: 'var(--text)' }}>
            Document Library
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage contracts, templates, and files
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline"
            onClick={() => navigate('/ai-tools?tool=document_composer')}
            data-testid="ai-create-document-btn"
          >
            <Wand2 className="h-4 w-4 mr-2" /> AI Document Creator
          </Button>
          <Button 
            className="neon-glow" 
            onClick={() => { resetUploadForm(); setIsUploadOpen(true); }}
            data-testid="upload-document-btn"
          >
            <Upload className="h-4 w-4 mr-2" /> Upload Document
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FolderOpen className="h-8 w-8 text-primary" />
              <div>
                <p className="text-sm text-muted-foreground">Total Documents</p>
                <p className="text-2xl font-bold">{stats?.total_documents || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-blue-400" />
              <div>
                <p className="text-sm text-muted-foreground">Templates</p>
                <p className="text-2xl font-bold text-blue-400">{stats?.templates || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <HardDrive className="h-8 w-8 text-green-400" />
              <div>
                <p className="text-sm text-muted-foreground">Storage Used</p>
                <p className="text-2xl font-bold text-green-400">{stats?.storage_used_mb || 0} MB</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Tag className="h-8 w-8 text-purple-400" />
              <div>
                <p className="text-sm text-muted-foreground">Categories</p>
                <p className="text-2xl font-bold text-purple-400">
                  {Object.keys(stats?.by_category || {}).length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                  data-testid="search-input"
                />
              </div>
            </div>
            
            {/* Category Filter */}
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[180px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {CATEGORIES.map(cat => (
                  <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {/* Templates Toggle */}
            <div className="flex items-center gap-2">
              <Switch
                checked={showTemplatesOnly}
                onCheckedChange={setShowTemplatesOnly}
                id="templates-only"
              />
              <Label htmlFor="templates-only" className="text-sm cursor-pointer">
                Templates only
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No documents found</p>
              <p className="text-sm mt-1">Upload your first document to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead>Template</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc, idx) => {
                  const FileIcon = getFileIcon(doc.file_type);
                  const catInfo = getCategoryInfo(doc.category);
                  return (
                    <TableRow 
                      key={doc.id} 
                      className={`${idx % 2 === 0 ? '' : 'bg-muted/30'} cursor-pointer hover:bg-muted/50 transition-colors`}
                      onClick={() => handleView(doc)}
                      data-testid={`document-row-${doc.id}`}
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-muted/50 flex items-center justify-center">
                            <FileIcon className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-medium">{doc.name}</p>
                            <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                              {doc.original_filename}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={catInfo.color}>{catInfo.label}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatFileSize(doc.file_size)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(doc.created_at)}
                      </TableCell>
                      <TableCell>
                        {doc.is_template && (
                          <Badge variant="outline" className="border-primary text-primary">
                            <CheckCircle2 className="h-3 w-3 mr-1" /> Template
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleSendDocument(doc)}
                            title="Send to customer"
                            className="text-primary hover:text-primary"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDownload(doc)}
                            title="Download"
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleToggleTemplate(doc)}
                            title={doc.is_template ? "Remove from templates" : "Mark as template"}
                          >
                            <FileText className={`h-4 w-4 ${doc.is_template ? 'text-primary' : ''}`} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(doc)}
                            title="Archive"
                            className="text-destructive hover:text-destructive"
                          >
                            <Archive className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Upload Document</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* File Selection */}
            <div className="space-y-2">
              <Label>Select File *</Label>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileSelect}
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.doc,.docx,.xls,.xlsx,.txt,.csv"
              />
              
              {uploadFile ? (
                <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/30">
                  <FileText className="h-8 w-8 text-primary" />
                  <div className="flex-1">
                    <p className="font-medium text-sm">{uploadFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(uploadFile.size)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setUploadFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="w-full h-24 border-dashed"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="text-center">
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm">Click to select file</p>
                    <p className="text-xs text-muted-foreground">PDF, Images, Word, Excel (max 10MB)</p>
                  </div>
                </Button>
              )}
            </div>
            
            {/* Document Name */}
            <div className="space-y-2">
              <Label>Document Name *</Label>
              <Input
                value={uploadForm.name}
                onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="e.g., Standard Contract Template"
                data-testid="doc-name-input"
              />
            </div>
            
            {/* Category */}
            <div className="space-y-2">
              <Label>Category</Label>
              <Select 
                value={uploadForm.category} 
                onValueChange={(val) => setUploadForm({ ...uploadForm, category: val })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map(cat => (
                    <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Description */}
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={uploadForm.description}
                onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                placeholder="Brief description of this document..."
                rows={2}
              />
            </div>
            
            {/* Tags */}
            <div className="space-y-2">
              <Label>Tags</Label>
              <Input
                value={uploadForm.tags}
                onChange={(e) => setUploadForm({ ...uploadForm, tags: e.target.value })}
                placeholder="Comma-separated tags (e.g., legal, standard, 2024)"
              />
            </div>
            
            {/* Template Toggle */}
            <div className="flex items-center justify-between">
              <div>
                <Label>Mark as Template</Label>
                <p className="text-xs text-muted-foreground">Templates can be reused for jobs</p>
              </div>
              <Switch
                checked={uploadForm.is_template}
                onCheckedChange={(checked) => setUploadForm({ ...uploadForm, is_template: checked })}
              />
            </div>
            
            <Separator />
            
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsUploadOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleUpload} disabled={uploading} data-testid="submit-upload-btn">
                {uploading ? 'Uploading...' : 'Upload'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Document Dialog */}
      <Dialog open={isViewOpen} onOpenChange={setIsViewOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Document Details</DialogTitle>
          </DialogHeader>
          
          {selectedDoc && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-lg bg-muted/50 flex items-center justify-center">
                  {(() => {
                    const FileIcon = getFileIcon(selectedDoc.file_type);
                    return <FileIcon className="h-8 w-8 text-primary" />;
                  })()}
                </div>
                <div>
                  <h3 className="font-bold text-lg">{selectedDoc.name}</h3>
                  <p className="text-sm text-muted-foreground">{selectedDoc.original_filename}</p>
                </div>
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Category</p>
                  <Badge className={getCategoryInfo(selectedDoc.category).color}>
                    {getCategoryInfo(selectedDoc.category).label}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground">File Size</p>
                  <p className="font-medium">{formatFileSize(selectedDoc.file_size)}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">File Type</p>
                  <p className="font-medium">{selectedDoc.file_type}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Uploaded</p>
                  <p className="font-medium">{formatDate(selectedDoc.created_at)}</p>
                </div>
              </div>
              
              {selectedDoc.description && (
                <div>
                  <p className="text-muted-foreground text-sm">Description</p>
                  <p className="text-sm">{selectedDoc.description}</p>
                </div>
              )}
              
              {selectedDoc.tags?.length > 0 && (
                <div>
                  <p className="text-muted-foreground text-sm mb-2">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedDoc.tags.map((tag, i) => (
                      <Badge key={i} variant="outline">{tag}</Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedDoc.is_template && (
                <Badge className="bg-primary/20 text-primary">
                  <CheckCircle2 className="h-3 w-3 mr-1" /> Template
                </Badge>
              )}
              
              <Separator />
              
              {/* Signature Section - Moved to end before actions */}
              <div>
                <SignatureSection
                  parentRecordType={selectedDoc.category === 'customer_form' ? 'form' : 'document'}
                  parentRecordId={selectedDoc.id}
                  orderId={(selectedDoc.linked_jobs || [])[0]}
                  signatureType={selectedDoc.category === 'customer_form' ? 'terms_acknowledgment' : 'terms_acknowledgment'}
                  documentVersion={String(selectedDoc.updated_at || selectedDoc.created_at || '')}
                  title="Document Signature"
                />
              </div>
              
              <Separator />
              
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline" 
                  onClick={async () => {
                    try {
                      const res = await api.get(`/documents/${selectedDoc.id}/download`);
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
                  }}
                >
                  <Eye className="h-4 w-4 mr-2" /> Open in New Tab
                </Button>
                <Button variant="outline" onClick={() => handleDownload(selectedDoc)}>
                  <Download className="h-4 w-4 mr-2" /> Download
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setIsViewOpen(false);
                    handleSendDocument(selectedDoc);
                  }}
                >
                  <Send className="h-4 w-4 mr-2" /> Send
                </Button>
                <Button onClick={() => setIsViewOpen(false)}>Close</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Send Document Dialog */}
      <Dialog open={isSendOpen} onOpenChange={setIsSendOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Send Document</DialogTitle>
          </DialogHeader>
          
          {sendDoc && (
            <div className="space-y-4">
              {/* Document info */}
              <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/30">
                <FileText className="h-8 w-8 text-primary" />
                <div>
                  <p className="font-medium">{sendDoc.name}</p>
                  <p className="text-xs text-muted-foreground">{sendDoc.original_filename}</p>
                </div>
              </div>
              
              {/* Send method selection */}
              <div className="space-y-2">
                <Label>Send Method</Label>
                <Tabs value={sendMethod} onValueChange={setSendMethod}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="email" className="flex items-center gap-1.5 text-xs" data-testid="send-method-email">
                      <Mail className="h-3.5 w-3.5" /> Email PDF
                    </TabsTrigger>
                    <TabsTrigger value="portal" className="flex items-center gap-1.5 text-xs" data-testid="send-method-portal">
                      <Globe className="h-3.5 w-3.5" /> Portal
                    </TabsTrigger>
                    <TabsTrigger value="form" className="flex items-center gap-1.5 text-xs" data-testid="send-method-form">
                      <ClipboardList className="h-3.5 w-3.5" /> As Form
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
                <p className="text-xs text-muted-foreground">
                  {sendMethod === 'email' && 'Send as a PDF attachment — no response needed from customer.'}
                  {sendMethod === 'portal' && 'Add to customer portal for viewing — no response needed.'}
                  {sendMethod === 'form' && 'Send as an interactive form — customer fills it out and submits.'}
                </p>
              </div>
              
              {/* Customer selection */}
              <div className="space-y-2">
                <Label>Select Customer *</Label>
                <Select value={sendCustomerId} onValueChange={setSendCustomerId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a customer..." />
                  </SelectTrigger>
                  <SelectContent>
                    {customers?.map(customer => (
                      <SelectItem key={customer.id} value={customer.id}>
                        {customer.name || customer.contact_name} 
                        {customer.email && ` (${customer.email})`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* Message */}
              <div className="space-y-2">
                <Label>Message (optional)</Label>
                <Textarea
                  value={sendMessage}
                  onChange={(e) => setSendMessage(e.target.value)}
                  placeholder="Add a personal message to the customer..."
                  rows={3}
                />
              </div>
              
              {/* Method-specific options */}
              {sendMethod === 'email' ? (
                <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                  <div>
                    <Label>Include as Attachment</Label>
                    <p className="text-xs text-muted-foreground">Attach the file to the email</p>
                  </div>
                  <Switch
                    checked={sendIncludeAttachment}
                    onCheckedChange={setSendIncludeAttachment}
                  />
                </div>
              ) : sendMethod === 'portal' ? (
                <div className="flex items-center justify-between p-3 rounded-lg border border-border">
                  <div>
                    <Label>Send Email Notification</Label>
                    <p className="text-xs text-muted-foreground">
                      Email customer that a document is ready in their portal
                    </p>
                  </div>
                  <Switch
                    checked={sendNotifyCustomer}
                    onCheckedChange={setSendNotifyCustomer}
                  />
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-sm text-amber-300">
                    <ClipboardList className="h-4 w-4 inline mr-2" />
                    This will open the form creator where you can add questions for the customer to fill out. The customer will receive a link to complete the form.
                  </p>
                </div>
              )}
              
              {/* Info box */}
              <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                <p className="text-sm">
                  {sendMethod === 'email' ? (
                    <>
                      <Mail className="h-4 w-4 inline mr-2" />
                      The document will be sent as a PDF attachment. No response is needed from the customer.
                    </>
                  ) : sendMethod === 'portal' ? (
                    <>
                      <Globe className="h-4 w-4 inline mr-2" />
                      The document will be added to the customer&apos;s portal for viewing only.
                      {sendNotifyCustomer && ' They will receive an email notification.'}
                    </>
                  ) : (
                    <>
                      <ClipboardList className="h-4 w-4 inline mr-2" />
                      The customer will receive a link to fill out the form and submit their response.
                    </>
                  )}
                </p>
              </div>
              
              <Separator />
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsSendOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSend} disabled={sending || !sendCustomerId}>
                  {sending ? 'Sending...' : (
                    <>
                      <Send className="h-4 w-4 mr-2" /> 
                      {sendMethod === 'email' ? 'Send PDF' : sendMethod === 'portal' ? 'Send to Portal' : 'Create Form'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
