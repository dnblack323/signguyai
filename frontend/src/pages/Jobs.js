import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate, formatDateTime, getStatusColor, cn } from '../lib/utils';
import { 
  Plus, Edit2, Trash2, Receipt, Calendar, ArrowLeft, Package, Eye, 
  MoreHorizontal, CheckCircle, Archive, ArchiveRestore, Clock,
  FileText, MessageSquare, Activity, DollarSign, User, ExternalLink,
  ChevronRight, Send, CalendarPlus, Calculator
} from 'lucide-react';
import { toast } from 'sonner';
import InvoicePreviewModal from '../components/InvoicePreviewModal';
import PricingCalculatorModal, { PricingCalculatorButton } from '../components/PricingCalculatorModal';

const statusOptions = ['quoted', 'approved', 'in_production', 'installed', 'complete', 'archived'];
const activeStatuses = ['quoted', 'approved', 'in_production', 'installed'];

const statusLabels = {
  quoted: 'Quoted',
  approved: 'Approved',
  in_production: 'In Production',
  installed: 'Installed',
  complete: 'Complete',
  archived: 'Archived'
};

const statusColors = {
  quoted: 'bg-gray-200 text-gray-800 border-gray-300',
  approved: 'bg-green-200 text-green-800 border-green-300',
  in_production: 'bg-yellow-200 text-yellow-800 border-yellow-300',
  installed: 'bg-purple-200 text-purple-800 border-purple-300',
  complete: 'bg-blue-200 text-blue-800 border-blue-300',
  archived: 'bg-slate-200 text-slate-800 border-slate-300'
};

const itemTypes = [
  'banner', 'yard_sign', 'decal', 'wrap', 'install', 'design',
  'vehicle_graphics', 'window_graphics', 'dimensional_letters', 'monument_sign', 'other'
];

const itemTypeLabels = {
  banner: 'Banner',
  yard_sign: 'Yard Sign',
  decal: 'Decal',
  wrap: 'Wrap',
  install: 'Install',
  design: 'Design',
  vehicle_graphics: 'Vehicle Graphics',
  window_graphics: 'Window Graphics',
  dimensional_letters: 'Dimensional Letters',
  monument_sign: 'Monument Sign',
  other: 'Other'
};

const itemStatusOptions = ['pending', 'in_production', 'done'];
const itemStatusLabels = {
  pending: 'Pending',
  in_production: 'In Production',
  done: 'Done'
};

const activityIcons = {
  created: Clock,
  status_changed: Activity,
  quote_converted: FileText,
  invoice_created: Receipt,
  item_added: Plus,
  item_updated: Edit2,
  item_deleted: Trash2,
  note_added: MessageSquare,
  completed: CheckCircle,
  archived: Archive,
  unarchived: ArchiveRestore
};

// ============ JOBS LIST COMPONENT ============
export function JobsList() {
  const navigate = useNavigate();
  const { 
    jobs, customers, fetchJobs, fetchCustomers, 
    createJob, updateJob, deleteJob, completeJob, archiveJob
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('active');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    customer_id: '',
    name: '',
    description: '',
    status: 'quoted',
    due_date: ''
  });

  useEffect(() => {
    loadData();
  }, [filterType]);

  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      fetchJobs({ filter_type: filterType }), 
      fetchCustomers()
    ]);
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id || !formData.name.trim()) {
      toast.error('Please fill in required fields');
      return;
    }
    try {
      const newJob = await createJob(formData);
      toast.success('Job created');
      setIsDialogOpen(false);
      setFormData({ customer_id: '', name: '', description: '', status: 'quoted', due_date: '' });
      navigate(`/jobs/${newJob.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create job');
    }
  };

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      await updateJob(jobId, { status: newStatus });
      toast.success('Status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleComplete = async (jobId) => {
    try {
      await completeJob(jobId);
      toast.success('Job marked as complete');
    } catch (err) {
      toast.error('Failed to complete job');
    }
  };

  const handleArchive = async (jobId) => {
    try {
      await archiveJob(jobId);
      toast.success('Job archived');
    } catch (err) {
      toast.error('Failed to archive job');
    }
  };

  const handleDelete = async (jobId) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await deleteJob(jobId);
        toast.success('Job deleted');
      } catch (err) {
        toast.error('Failed to delete job');
      }
    }
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || 'Unknown';
  };

  const filterCounts = {
    active: jobs.filter(j => activeStatuses.includes(j.status) && !j.is_archived).length,
    completed: jobs.filter(j => j.status === 'complete' && !j.is_archived).length,
    archived: jobs.filter(j => j.is_archived || j.status === 'archived').length
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="jobs-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight" style={{ color: 'var(--text)' }}>Jobs</h1>
          <p className="text-muted-foreground mt-1">{jobs.length} jobs</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-job-btn">
              <Plus className="h-4 w-4 mr-2" /> New Job
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">New Job</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select
                  value={formData.customer_id}
                  onValueChange={(val) => setFormData({ ...formData, customer_id: val })}
                >
                  <SelectTrigger data-testid="job-customer-select">
                    <SelectValue placeholder="Select customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Job Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Storefront Sign Installation"
                  data-testid="job-name-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(val) => setFormData({ ...formData, status: val })}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {activeStatuses.map((s) => (
                        <SelectItem key={s} value={s}>{statusLabels[s]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button type="submit" data-testid="job-submit-btn">Create Job</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['active', 'completed', 'archived'].map((filter) => (
          <Button
            key={filter}
            variant={filterType === filter ? "default" : "outline"}
            size="sm"
            onClick={() => setFilterType(filter)}
            data-testid={`filter-${filter}`}
            className={filterType === filter ? "neon-glow" : ""}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
            <Badge variant="secondary" className="ml-2 h-5 min-w-[20px]">
              {filter === 'active' ? filterCounts.active : filter === 'completed' ? filterCounts.completed : filterCounts.archived}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Jobs List */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No {filterType} jobs</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {jobs.map((job) => (
                <div 
                  key={job.id} 
                  className="p-4 hover:bg-muted/30 transition-colors group"
                  data-testid={`job-row-${job.id}`}
                >
                  <div className="flex items-center gap-4">
                    {/* Job Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1">
                        <Link 
                          to={`/jobs/${job.id}`}
                          className="font-bold text-lg hover:text-primary transition-colors truncate"
                        >
                          {job.name}
                        </Link>
                        {/* Interactive Status Badge */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button className="focus:outline-none">
                              <Badge 
                                className={cn(
                                  statusColors[job.status], 
                                  "cursor-pointer hover:opacity-80 transition-opacity"
                                )}
                              >
                                {statusLabels[job.status]}
                              </Badge>
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="start">
                            {statusOptions.filter(s => s !== 'archived').map((status) => (
                              <DropdownMenuItem
                                key={status}
                                onClick={() => handleStatusChange(job.id, status)}
                                disabled={status === job.status}
                              >
                                <Badge className={cn(statusColors[status], "mr-2")} />
                                {statusLabels[status]}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{getCustomerName(job.customer_id)}</span>
                        {job.due_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" /> {formatDate(job.due_date)}
                          </span>
                        )}
                        {job.subtotal > 0 && (
                          <span className="text-primary font-medium">
                            {formatCurrency(job.subtotal)}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => navigate(`/jobs/${job.id}`)}
                        data-testid={`view-job-${job.id}`}
                      >
                        <Eye className="h-4 w-4 mr-1" /> View
                      </Button>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/jobs/${job.id}`)}>
                            <Eye className="h-4 w-4 mr-2" /> View Details
                          </DropdownMenuItem>
                          {job.status !== 'complete' && job.status !== 'archived' && (
                            <DropdownMenuItem onClick={() => handleComplete(job.id)}>
                              <CheckCircle className="h-4 w-4 mr-2" /> Mark Complete
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {job.status !== 'archived' && !job.is_archived ? (
                            <DropdownMenuItem onClick={() => handleArchive(job.id)}>
                              <Archive className="h-4 w-4 mr-2" /> Archive
                            </DropdownMenuItem>
                          ) : null}
                          <DropdownMenuItem 
                            onClick={() => handleDelete(job.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ============ JOB DETAILS COMPONENT ============
export function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { 
    customers, fetchCustomers,
    getJobDetails, updateJob, completeJob, archiveJob, unarchiveJob,
    createInvoiceFromJob, fetchJobs,
    fetchJobItems, createJobItem, updateJobItem, deleteJobItem,
    createJobNote, deleteJobNote,
    createTask
  } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [jobData, setJobData] = useState(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isItemDialogOpen, setIsItemDialogOpen] = useState(false);
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = useState(false);
  const [isCalculatorOpen, setIsCalculatorOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [newNote, setNewNote] = useState('');
  const [activeTab, setActiveTab] = useState('items');
  
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    status: '',
    due_date: ''
  });
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  
  // Schedule task form
  const [scheduleFormData, setScheduleFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    due_time: '09:00'
  });
  
  const [itemFormData, setItemFormData] = useState({
    item_type: 'other',
    description: '',
    quantity: 1,
    unit_price: 0,
    status: 'pending',
    notes: ''
  });

  // Handle calculated item from pricing calculator
  const handleCalculatedItem = (calculatedData) => {
    // Map the calculator output to the item form format
    const itemTypeMap = {
      'rigid_signs': 'yard_sign',
      'cut_vinyl': 'decal',
      'digital_print': 'banner',
      'vehicle_graphics': 'vehicle_graphics',
      'apparel': 'other',
      'services': 'design',
      'promotional': 'other',
      'custom': 'other'
    };
    
    setItemFormData({
      item_type: itemTypeMap[calculatedData.category] || 'other',
      description: calculatedData.description || `${calculatedData.category} - Qty ${calculatedData.quantity}`,
      quantity: calculatedData.quantity || 1,
      unit_price: calculatedData.unit_price || calculatedData.suggested_price || 0,
      status: 'pending',
      notes: calculatedData.pricing_breakdown ? 
        `Cost: $${calculatedData.production_cost?.toFixed(2)} | Profit: $${calculatedData.profit_amount?.toFixed(2)} (${calculatedData.profit_margin_percent?.toFixed(0)}%)` : ''
    });
    
    setIsCalculatorOpen(false);
    setIsItemDialogOpen(true);
    toast.success('Item calculated! Review and save.');
  };

  useEffect(() => {
    loadJobDetails();
    fetchCustomers();
  }, [id]);

  const loadJobDetails = async () => {
    setLoading(true);
    try {
      const data = await getJobDetails(id);
      setJobData(data);
      setEditFormData({
        name: data.job.name,
        description: data.job.description || '',
        status: data.job.status,
        due_date: data.job.due_date || ''
      });
    } catch (err) {
      toast.error('Failed to load job details');
      navigate('/jobs');
    }
    setLoading(false);
  };

  const handleUpdateJob = async (e) => {
    e.preventDefault();
    try {
      await updateJob(id, editFormData);
      await loadJobDetails();
      await fetchJobs();
      setIsEditDialogOpen(false);
      toast.success('Job updated');
    } catch (err) {
      toast.error('Failed to update job');
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await updateJob(id, { status: newStatus });
      await loadJobDetails();
      await fetchJobs();
      toast.success('Status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleComplete = async () => {
    try {
      await completeJob(id);
      await loadJobDetails();
      toast.success('Job marked as complete');
    } catch (err) {
      toast.error('Failed to complete job');
    }
  };

  const handleArchive = async () => {
    try {
      await archiveJob(id);
      await loadJobDetails();
      toast.success('Job archived');
    } catch (err) {
      toast.error('Failed to archive job');
    }
  };

  const handleUnarchive = async () => {
    try {
      await unarchiveJob(id);
      await loadJobDetails();
      toast.success('Job unarchived');
    } catch (err) {
      toast.error('Failed to unarchive job');
    }
  };

  const handleCreateInvoice = async () => {
    try {
      await createInvoiceFromJob(id);
      await loadJobDetails();
      await fetchJobs();
      toast.success('Invoice created');
    } catch (err) {
      toast.error('Failed to create invoice');
    }
  };

  const handleOpenSchedule = () => {
    const job = jobData?.job;
    setScheduleFormData({
      title: job?.name || '',
      description: job?.description || '',
      due_date: job?.due_date || new Date().toISOString().split('T')[0],
      due_time: '09:00'
    });
    setIsScheduleDialogOpen(true);
  };

  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    if (!scheduleFormData.title.trim()) {
      toast.error('Task title is required');
      return;
    }
    try {
      await createTask({
        title: scheduleFormData.title,
        description: scheduleFormData.description,
        job_id: id,
        due_date: scheduleFormData.due_date,
        status: 'pending'
      });
      setIsScheduleDialogOpen(false);
      toast.success('Task added to calendar!');
    } catch (err) {
      toast.error('Failed to schedule task');
    }
  };

  // Item handlers
  const handleItemSubmit = async (e) => {
    e.preventDefault();
    if (!itemFormData.description.trim()) {
      toast.error('Please enter item description');
      return;
    }
    try {
      if (editingItem) {
        await updateJobItem(editingItem.id, itemFormData);
        toast.success('Item updated');
      } else {
        await createJobItem(id, itemFormData);
        toast.success('Item added');
      }
      await loadJobDetails();
      await fetchJobs();
      resetItemForm();
    } catch (err) {
      toast.error('Failed to save item');
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setItemFormData({
      item_type: item.item_type,
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unit_price,
      status: item.status,
      notes: item.notes || ''
    });
    setIsItemDialogOpen(true);
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('Delete this line item?')) {
      try {
        await deleteJobItem(itemId);
        await loadJobDetails();
        await fetchJobs();
        toast.success('Item deleted');
      } catch (err) {
        toast.error('Failed to delete item');
      }
    }
  };

  const handleItemStatusChange = async (itemId, newStatus) => {
    try {
      await updateJobItem(itemId, { status: newStatus });
      await loadJobDetails();
      toast.success('Item status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const resetItemForm = () => {
    setItemFormData({
      item_type: 'other',
      description: '',
      quantity: 1,
      unit_price: 0,
      status: 'pending',
      notes: ''
    });
    setEditingItem(null);
    setIsItemDialogOpen(false);
  };

  // Note handlers
  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    try {
      await createJobNote(id, { content: newNote });
      await loadJobDetails();
      setNewNote('');
      toast.success('Note added');
    } catch (err) {
      toast.error('Failed to add note');
    }
  };

  const handleDeleteNote = async (noteId) => {
    try {
      await deleteJobNote(noteId);
      await loadJobDetails();
      toast.success('Note deleted');
    } catch (err) {
      toast.error('Failed to delete note');
    }
  };

  if (loading || !jobData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const { job, customer, quote, invoice, job_items, notes, activities, financial_snapshot } = jobData;
  const isArchived = job.is_archived || job.status === 'archived';

  return (
    <div className="space-y-6 animate-fade-in" data-testid="job-details-page">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => navigate('/jobs')} data-testid="back-to-jobs">
        <ArrowLeft className="h-4 w-4 mr-2" /> Back to Jobs
      </Button>

      {/* Header Card */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            {/* Job Info */}
            <div className="flex-1">
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-3xl font-bold font-heading uppercase" style={{ color: 'var(--text)' }}>{job.name}</h1>
                    {/* Editable Status Dropdown */}
                    <Select value={job.status} onValueChange={handleStatusChange}>
                      <SelectTrigger className="w-[160px]" data-testid="job-status-dropdown">
                        <Badge className={statusColors[job.status]}>
                          {statusLabels[job.status]}
                        </Badge>
                      </SelectTrigger>
                      <SelectContent>
                        {statusOptions.map((s) => (
                          <SelectItem key={s} value={s}>
                            <Badge className={statusColors[s]}>{statusLabels[s]}</Badge>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Customer Link */}
                  <Link 
                    to="/customers" 
                    className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
                  >
                    <User className="h-4 w-4" />
                    <span className="font-medium">{customer?.name || 'Unknown Customer'}</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
                
                <Button variant="outline" size="sm" onClick={() => setIsEditDialogOpen(true)}>
                  <Edit2 className="h-4 w-4 mr-1" /> Edit
                </Button>
              </div>

              {/* Meta Info */}
              <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                {job.due_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" /> Due: {formatDate(job.due_date)}
                  </span>
                )}
                <span>Created: {formatDate(job.created_at)}</span>
                {quote && (
                  <span className="flex items-center gap-1">
                    <FileText className="h-4 w-4" /> From Quote #{quote.id.slice(0, 8)}
                  </span>
                )}
              </div>

              {/* Job Notes */}
              {job.description && (
                <p className="mt-4 p-3 bg-muted/30 rounded-lg text-sm">
                  <strong>Notes:</strong> {job.description}
                </p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col gap-2">
              <Button variant="outline" onClick={handleOpenSchedule} data-testid="schedule-job-btn">
                <CalendarPlus className="h-4 w-4 mr-2" /> Schedule
              </Button>
              {!invoice && (
                <Button onClick={handleCreateInvoice} data-testid="create-invoice-btn">
                  <Receipt className="h-4 w-4 mr-2" /> Create Invoice
                </Button>
              )}
              {invoice && (
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => {
                    setPreviewInvoiceId(invoice.id);
                    setIsInvoiceModalOpen(true);
                  }}
                  data-testid="view-invoice-btn"
                >
                  <Receipt className="h-4 w-4 mr-2" /> View Invoice
                </Button>
              )}
              {job.status !== 'complete' && !isArchived && (
                <Button variant="outline" onClick={handleComplete}>
                  <CheckCircle className="h-4 w-4 mr-2" /> Mark Complete
                </Button>
              )}
              {!isArchived ? (
                <Button variant="outline" onClick={handleArchive}>
                  <Archive className="h-4 w-4 mr-2" /> Archive
                </Button>
              ) : (
                <Button variant="outline" onClick={handleUnarchive}>
                  <ArchiveRestore className="h-4 w-4 mr-2" /> Unarchive
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Financial Snapshot */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-card border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground mb-1">Quote Total</p>
            <p className="text-xl font-bold">{formatCurrency(financial_snapshot.quote_total)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground mb-1">Job Subtotal</p>
            <p className="text-xl font-bold text-primary">{formatCurrency(job.subtotal)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground mb-1">Invoiced</p>
            <p className="text-xl font-bold">{formatCurrency(financial_snapshot.invoice_total)}</p>
            {financial_snapshot.invoice_status && (
              <Badge className={cn(getStatusColor(financial_snapshot.invoice_status), "mt-1 text-xs")}>
                {financial_snapshot.invoice_status}
              </Badge>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground mb-1">Paid</p>
            <p className="text-xl font-bold text-green-400">{formatCurrency(financial_snapshot.amount_paid)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground mb-1">Balance Due</p>
            <p className={cn("text-xl font-bold", financial_snapshot.balance_due > 0 ? "text-red-400" : "text-green-400")}>
              {formatCurrency(financial_snapshot.balance_due)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs: Line Items, Notes, Activity */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="items">
            <Package className="h-4 w-4 mr-2" /> Line Items ({job_items.length})
          </TabsTrigger>
          <TabsTrigger value="notes">
            <MessageSquare className="h-4 w-4 mr-2" /> Notes ({notes.length})
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Activity className="h-4 w-4 mr-2" /> Activity ({activities.length})
          </TabsTrigger>
        </TabsList>

        {/* Line Items Tab */}
        <TabsContent value="items" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="font-heading uppercase">Line Items</CardTitle>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    className="border-teal-500/50 text-teal-500 hover:bg-teal-500/10"
                    onClick={() => { resetItemForm(); setIsCalculatorOpen(true); }}
                    data-testid="open-calculator-btn"
                  >
                    <Calculator className="h-4 w-4 mr-2" /> Use Calculator
                  </Button>
                  <Dialog open={isItemDialogOpen} onOpenChange={setIsItemDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="neon-glow" data-testid="add-line-item-btn" onClick={resetItemForm}>
                        <Plus className="h-4 w-4 mr-2" /> Add Item
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                      <DialogHeader>
                        <DialogTitle className="font-heading uppercase">
                          {editingItem ? 'Edit Item' : 'Add Item'}
                        </DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleItemSubmit} className="space-y-4">
                        {/* Calculator shortcut */}
                        {!editingItem && (
                          <div className="p-3 bg-teal-500/10 border border-teal-500/30 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div className="text-sm">
                                <p className="text-teal-400 font-medium">Need to calculate pricing?</p>
                                <p className="text-muted-foreground text-xs mt-0.5">Use the calculator for accurate pricing</p>
                              </div>
                              <Button 
                                type="button"
                                variant="outline" 
                                size="sm"
                                className="border-teal-500/50 text-teal-500 hover:bg-teal-500/10"
                                onClick={() => { setIsItemDialogOpen(false); setIsCalculatorOpen(true); }}
                              >
                                <Calculator className="h-4 w-4 mr-1" /> Calculate
                              </Button>
                            </div>
                          </div>
                        )}
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Type</Label>
                            <Select
                              value={itemFormData.item_type}
                              onValueChange={(val) => setItemFormData({ ...itemFormData, item_type: val })}
                            >
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {itemTypes.map((t) => (
                                  <SelectItem key={t} value={t}>{itemTypeLabels[t]}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Status</Label>
                            <Select
                              value={itemFormData.status}
                              onValueChange={(val) => setItemFormData({ ...itemFormData, status: val })}
                            >
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {itemStatusOptions.map((s) => (
                                  <SelectItem key={s} value={s}>{itemStatusLabels[s]}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Description *</Label>
                          <Input
                            value={itemFormData.description}
                            onChange={(e) => setItemFormData({ ...itemFormData, description: e.target.value })}
                            placeholder="e.g., 4x8 Vinyl Banner"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Quantity</Label>
                            <Input
                              type="number"
                              min="1"
                              value={itemFormData.quantity || ''}
                              onChange={(e) => setItemFormData({ ...itemFormData, quantity: e.target.value === '' ? '' : parseFloat(e.target.value) || 1 })}
                              onBlur={(e) => {
                                if (e.target.value === '' || parseFloat(e.target.value) < 1) {
                                  setItemFormData({ ...itemFormData, quantity: 1 });
                                }
                              }}
                              placeholder="1"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Unit Price</Label>
                            <Input
                              type="number"
                              step="0.01"
                              value={itemFormData.unit_price === 0 ? '' : itemFormData.unit_price}
                              onChange={(e) => setItemFormData({ ...itemFormData, unit_price: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                              onBlur={(e) => {
                                if (e.target.value === '') {
                                  setItemFormData({ ...itemFormData, unit_price: 0 });
                                }
                              }}
                              placeholder="0.00"
                            />
                          </div>
                        </div>
                        <div className="p-3 bg-muted/30 rounded-lg text-right">
                          <span className="text-muted-foreground">Line Total: </span>
                          <span className="text-lg font-bold text-primary">
                            {formatCurrency(itemFormData.quantity * itemFormData.unit_price)}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <Label>Notes</Label>
                          <Textarea
                            value={itemFormData.notes}
                            onChange={(e) => setItemFormData({ ...itemFormData, notes: e.target.value })}
                            rows={2}
                          />
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button type="button" variant="outline" onClick={resetItemForm}>Cancel</Button>
                          <Button type="submit">{editingItem ? 'Update' : 'Add'}</Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {job_items.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No line items</p>
                </div>
              ) : (
                <>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-center">Qty</TableHead>
                        <TableHead className="text-right">Unit Price</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {job_items.map((item, idx) => (
                        <TableRow key={item.id} className={idx % 2 === 1 ? 'bg-muted/30' : ''}>
                          <TableCell>
                            <Badge variant="outline">{itemTypeLabels[item.item_type]}</Badge>
                          </TableCell>
                          <TableCell>
                            <div>
                              <p className="font-medium">{item.description}</p>
                              {item.notes && <p className="text-xs text-muted-foreground">{item.notes}</p>}
                            </div>
                          </TableCell>
                          <TableCell className="text-center">{item.quantity}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                          <TableCell className="text-right font-bold">{formatCurrency(item.line_total)}</TableCell>
                          <TableCell>
                            <Select
                              value={item.status}
                              onValueChange={(val) => handleItemStatusChange(item.id, val)}
                            >
                              <SelectTrigger className="w-[130px] h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {itemStatusOptions.map((s) => (
                                  <SelectItem key={s} value={s}>{itemStatusLabels[s]}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="icon" onClick={() => handleEditItem(item)}>
                                <Edit2 className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="icon" onClick={() => handleDeleteItem(item.id)}>
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <div className="flex justify-end mt-4 p-4 bg-muted/30 rounded-lg">
                    <div className="text-right">
                      <span className="text-muted-foreground mr-4">Subtotal:</span>
                      <span className="text-2xl font-bold text-primary">{formatCurrency(job.subtotal)}</span>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notes Tab */}
        <TabsContent value="notes" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle className="font-heading uppercase">Internal Notes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Add Note */}
              <div className="flex gap-2">
                <Textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Add a note..."
                  rows={2}
                  className="flex-1"
                  data-testid="new-note-input"
                />
                <Button onClick={handleAddNote} disabled={!newNote.trim()} data-testid="add-note-btn">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              
              <Separator />

              {notes.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No notes yet</p>
              ) : (
                <div className="space-y-3">
                  {notes.map((note) => (
                    <div key={note.id} className="p-4 bg-muted/30 rounded-lg group">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="whitespace-pre-wrap">{note.content}</p>
                          <p className="text-xs text-muted-foreground mt-2">
                            {note.author && <span>{note.author} • </span>}
                            {formatDateTime(note.created_at)}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteNote(note.id)}
                          className="opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle className="font-heading uppercase">Activity Log</CardTitle>
            </CardHeader>
            <CardContent>
              {activities.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No activity recorded</p>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {activities.map((activity) => {
                      const Icon = activityIcons[activity.activity_type] || Activity;
                      return (
                        <div key={activity.id} className="flex items-start gap-3">
                          <div className="p-2 rounded-full bg-muted/50">
                            <Icon className="h-4 w-4 text-muted-foreground" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm">{activity.description}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {formatDateTime(activity.created_at)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Invoice Preview Modal */}
      <InvoicePreviewModal
        invoiceId={previewInvoiceId}
        isOpen={isInvoiceModalOpen}
        onClose={() => {
          setIsInvoiceModalOpen(false);
          setPreviewInvoiceId(null);
        }}
      />

      {/* Schedule Task Dialog */}
      <Dialog open={isScheduleDialogOpen} onOpenChange={setIsScheduleDialogOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase flex items-center gap-2">
              <CalendarPlus className="h-5 w-5" />
              Schedule Task
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground -mt-2">
            Add this job to your calendar/to-do list
          </p>
          <form onSubmit={handleScheduleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Task Title *</Label>
              <Input
                value={scheduleFormData.title}
                onChange={(e) => setScheduleFormData({ ...scheduleFormData, title: e.target.value })}
                placeholder="e.g., Banner design for Smith Co."
                data-testid="schedule-title-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={scheduleFormData.due_date}
                  onChange={(e) => setScheduleFormData({ ...scheduleFormData, due_date: e.target.value })}
                  data-testid="schedule-date-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Time</Label>
                <Input
                  type="time"
                  value={scheduleFormData.due_time}
                  onChange={(e) => setScheduleFormData({ ...scheduleFormData, due_time: e.target.value })}
                  data-testid="schedule-time-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={scheduleFormData.description}
                onChange={(e) => setScheduleFormData({ ...scheduleFormData, description: e.target.value })}
                placeholder="Task details..."
                rows={3}
                data-testid="schedule-description-input"
              />
            </div>
            <div className="p-3 bg-muted/30 rounded-lg text-sm">
              <p className="text-muted-foreground">
                This task will be linked to: <span className="font-medium text-foreground">{job?.name}</span>
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setIsScheduleDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" data-testid="schedule-submit-btn">
                <CalendarPlus className="h-4 w-4 mr-2" /> Add to Calendar
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Job Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Edit Job</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleUpdateJob} className="space-y-4">
            <div className="space-y-2">
              <Label>Job Name</Label>
              <Input
                value={editFormData.name}
                onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Status</Label>
                <Select
                  value={editFormData.status}
                  onValueChange={(val) => setEditFormData({ ...editFormData, status: val })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((s) => (
                      <SelectItem key={s} value={s}>{statusLabels[s]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={editFormData.due_date}
                  onChange={(e) => setEditFormData({ ...editFormData, due_date: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={editFormData.description}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
              <Button type="submit">Save Changes</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Pricing Calculator Modal */}
      <PricingCalculatorModal
        isOpen={isCalculatorOpen}
        onClose={() => setIsCalculatorOpen(false)}
        onItemCalculated={handleCalculatedItem}
      />
    </div>
  );
}

// Default export for router
export default function Jobs() {
  return <JobsList />;
}
