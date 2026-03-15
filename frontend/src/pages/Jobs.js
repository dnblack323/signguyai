import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate, useParams, Link, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { ShellCard, ShellCardHeader, ShellCardTitle, PageStack } from '../components/ui/shell-card';
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
  ChevronRight, Send, CalendarPlus, Calculator, Play, Square, Timer, Loader2,
  GitBranch, ArrowRight, ArrowRightCircle, Filter
} from 'lucide-react';
import { TimelineToggle } from '../components/ProductionTimeline';
import { JobHistoryPanel } from '../components/JobHistoryPanel';
import { toast } from 'sonner';
import InvoicePreviewModal from '../components/InvoicePreviewModal';
import PricingCalculatorModal, { PricingCalculatorButton } from '../components/PricingCalculatorModal';

// Updated status options for unified system
const statusOptions = ['quote', 'approved', 'in_progress', 'completed', 'invoiced', 'archived'];
const activeStatuses = ['approved', 'in_progress'];  // Only these count as "active" production
const quoteStatuses = ['quote'];  // Pipeline stage
const taskTypes = [
  { value: 'design', label: 'Design' },
  { value: 'production', label: 'Production' },
  { value: 'installation', label: 'Installation' },
  { value: 'admin', label: 'Admin/Other' }
];

const statusLabels = {
  quote: 'Quote',
  approved: 'Approved',
  in_progress: 'In Progress',
  completed: 'Completed',
  invoiced: 'Invoiced',
  archived: 'Archived'
};

const statusColors = {
  quote: 'bg-amber-200 text-amber-800 border-amber-300',
  approved: 'bg-green-200 text-green-800 border-green-300',
  in_progress: 'bg-yellow-200 text-yellow-800 border-yellow-300',
  completed: 'bg-blue-200 text-blue-800 border-blue-300',
  invoiced: 'bg-purple-200 text-purple-800 border-purple-300',
  archived: 'bg-slate-200 text-slate-800 border-slate-300'
};

// Filter options for the job board
const filterOptions = [
  { value: 'all', label: 'All Jobs' },
  { value: 'quotes', label: 'Quotes (Pipeline)' },
  { value: 'active', label: 'Active (Production)' },
  { value: 'completed', label: 'Completed' },
  { value: 'invoiced', label: 'Invoiced' },
  { value: 'archived', label: 'Archived' }
];

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
  const [searchParams, setSearchParams] = useSearchParams();
  const { 
    jobs, customers, fetchJobs, fetchCustomers, 
    createJob, updateJob, deleteJob, completeJob, archiveJob, approveJob
  } = useApp();
  const [loading, setLoading] = useState(true);
  // Get filter from URL params, default to 'all'
  const filterType = searchParams.get('filter') || 'all';
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showPricingCalculator, setShowPricingCalculator] = useState(false);
  const [createMode, setCreateMode] = useState('quote'); // 'quote' or 'job'
  const [formData, setFormData] = useState({
    customer_id: '',
    name: '',
    description: '',
    notes: '',
    status: 'quote',
    due_date: '',
    line_items: [{ description: '', quantity: 1, unit_price: '' }]
  });

  useEffect(() => {
    loadData();
  }, [filterType]);

  // Handle URL params for opening new job dialog with pre-selected customer
  useEffect(() => {
    const isNew = searchParams.get('new') === 'true';
    const customerId = searchParams.get('customer_id');
    const customerName = searchParams.get('customer_name');
    const jobType = searchParams.get('type'); // 'quote' or 'job'
    
    if (isNew) {
      // Set the create mode - default to 'job' if coming from customer page, otherwise check URL param
      const mode = jobType === 'quote' ? 'quote' : 'job';
      setCreateMode(mode);
      
      // Pre-fill customer if provided
      if (customerId) {
        setFormData(prev => ({
          ...prev,
          customer_id: customerId,
          status: mode === 'job' ? 'approved' : 'quote'
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          status: mode === 'job' ? 'approved' : 'quote'
        }));
      }
      
      // Open the dialog
      setIsDialogOpen(true);
      
      // Clear the URL params after opening
      setSearchParams({});
      
      if (customerName) {
        toast.info(`Creating ${mode} for ${decodeURIComponent(customerName)}`);
      }
    }
  }, [searchParams]);

  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      fetchJobs({ filter_type: filterType }), 
      fetchCustomers()
    ]);
    setLoading(false);
  };

  const setFilterType = (newFilter) => {
    setSearchParams({ filter: newFilter });
  };

  // Calculate total from line items
  const calculateTotal = () => {
    return formData.line_items.reduce((sum, item) => {
      const qty = parseFloat(item.quantity) || 0;
      const price = parseFloat(item.unit_price) || 0;
      return sum + (qty * price);
    }, 0);
  };

  const addLineItem = () => {
    setFormData({
      ...formData,
      line_items: [...formData.line_items, { description: '', quantity: 1, unit_price: '' }]
    });
  };

  const updateLineItem = (index, field, value) => {
    const newItems = [...formData.line_items];
    newItems[index][field] = value;
    setFormData({ ...formData, line_items: newItems });
  };

  const removeLineItem = (index) => {
    if (formData.line_items.length > 1) {
      const newItems = formData.line_items.filter((_, i) => i !== index);
      setFormData({ ...formData, line_items: newItems });
    }
  };

  // Handle item calculated from pricing calculator
  const handlePricingCalculatorItem = (itemData) => {
    const newLineItem = {
      description: itemData.description || 'Calculated Item',
      quantity: itemData.quantity || 1,
      unit_price: itemData.unit_price || itemData.line_total || 0,
      pricing_category: itemData.pricing_category || itemData.category,
      pricing_data: itemData.pricing_data,
      cost_snapshot: itemData.cost_snapshot
    };
    
    // Add the calculated item to line items
    setFormData({
      ...formData,
      line_items: [...formData.line_items.filter(item => item.description.trim()), newLineItem]
    });
    
    setShowPricingCalculator(false);
    toast.success('Item added from calculator');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id || !formData.name.trim()) {
      toast.error('Please fill in required fields');
      return;
    }
    
    // Clean line items - convert strings to numbers
    const cleanedLineItems = formData.line_items
      .filter(item => item.description.trim()) // Only include items with descriptions
      .map(item => ({
        ...item,
        quantity: parseFloat(item.quantity) || 1,
        unit_price: parseFloat(item.unit_price) || 0
      }));
    
    try {
      const jobData = {
        ...formData,
        line_items: cleanedLineItems,
        status: createMode === 'job' ? 'approved' : 'quote'
      };
      const newJob = await createJob(jobData);
      toast.success(createMode === 'job' ? 'Job created' : 'Quote created');
      setIsDialogOpen(false);
      resetForm();
      navigate(`/jobs/${newJob.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create');
    }
  };

  const resetForm = (mode = 'quote') => {
    setFormData({
      customer_id: '',
      name: '',
      description: '',
      notes: '',
      status: mode === 'job' ? 'approved' : 'quote',
      due_date: '',
      line_items: [{ description: '', quantity: 1, unit_price: '' }]
    });
    setCreateMode(mode);
  };

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      await updateJob(jobId, { status: newStatus });
      toast.success('Status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleApprove = async (jobId) => {
    try {
      await approveJob(jobId);
      toast.success('Quote approved - ready for production!');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve');
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

  // Count jobs by filter type for display
  const getFilterLabel = (filter) => {
    const option = filterOptions.find(f => f.value === filter);
    return option?.label || 'All Jobs';
  };

  return (
    <PageStack gap="24px" data-testid="jobs-page">
      {/* Header Card */}
      <ShellCard padding="default">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold font-heading uppercase tracking-tight text-gray-900">Jobs</h1>
            <p className="text-gray-500 text-sm mt-1">{jobs.length} {getFilterLabel(filterType).toLowerCase()}</p>
          </div>
          <div className="flex gap-2">
            {/* New Quote / New Job dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button className="bg-blue-600 hover:bg-blue-700" data-testid="add-job-btn">
                  <Plus className="h-4 w-4 mr-2" /> Create New
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem 
                  onClick={() => { resetForm('quote'); setIsDialogOpen(true); }}
                  data-testid="new-quote-option"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  New Quote
                  <span className="text-xs text-muted-foreground ml-2">(Pipeline)</span>
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={() => { resetForm('job'); setIsDialogOpen(true); }}
                  data-testid="new-job-option"
                >
                  <Package className="h-4 w-4 mr-2" />
                  New Job
                  <span className="text-xs text-muted-foreground ml-2">(Ready for production)</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </ShellCard>

      {/* Filters Card */}
      <ShellCard padding="default">
        <div className="flex items-center gap-3 flex-wrap">
          <Filter className="h-4 w-4 text-gray-400" />
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-[200px]" data-testid="job-filter-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {filterOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {/* Quick filter badges */}
          <div className="hidden md:flex gap-2 ml-4">
            {filterOptions.slice(1).map((opt) => (
              <Badge 
                key={opt.value}
                variant={filterType === opt.value ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setFilterType(opt.value)}
              >
                {opt.label}
              </Badge>
            ))}
          </div>
        </div>
      </ShellCard>

      {/* Jobs List Card */}
      <ShellCard padding="none">
        <div className="p-4 lg:p-6 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">
            {getFilterLabel(filterType)}
          </h2>
        </div>

      {/* Create Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase flex items-center gap-2">
              {createMode === 'quote' ? (
                <><FileText className="h-5 w-5" /> New Quote</>
              ) : (
                <><Package className="h-5 w-5" /> New Job</>
              )}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Mode indicator */}
            <div className={cn(
              "p-3 rounded-lg border text-sm",
              createMode === 'quote' 
                ? "bg-amber-50 border-amber-200 text-amber-800"
                : "bg-green-50 border-green-200 text-green-800"
            )}>
              {createMode === 'quote' ? (
                <p><strong>Quote Mode:</strong> This will create a job in the pipeline (quote stage). Approve it later to move to production.</p>
              ) : (
                <p><strong>Job Mode:</strong> This will create a job ready for production (approved status).</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
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
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  data-testid="job-due-date-input"
                />
              </div>
            </div>
              
            <div className="space-y-2">
              <Label>Job Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Main Street Banner Project"
                data-testid="job-name-input"
              />
            </div>

            {/* Line Items - shown for both Quote and Job modes */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Line Items</Label>
                <div className="flex gap-2">
                  <PricingCalculatorButton 
                    onClick={() => setShowPricingCalculator(true)} 
                    variant="outline"
                    size="sm"
                  />
                  <Button type="button" variant="outline" size="sm" onClick={addLineItem}>
                    <Plus className="h-3 w-3 mr-1" /> Add Item
                  </Button>
                </div>
              </div>
              {formData.line_items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 items-end">
                  <div className="col-span-6">
                    <Input
                      placeholder="Description"
                      value={item.description}
                      onChange={(e) => updateLineItem(idx, 'description', e.target.value)}
                      data-testid={`line-item-desc-${idx}`}
                    />
                  </div>
                  <div className="col-span-2">
                    <Input
                      type="number"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={(e) => updateLineItem(idx, 'quantity', e.target.value)}
                      data-testid={`line-item-qty-${idx}`}
                    />
                  </div>
                  <div className="col-span-3">
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="Price"
                      value={item.unit_price}
                      onChange={(e) => updateLineItem(idx, 'unit_price', e.target.value)}
                      data-testid={`line-item-price-${idx}`}
                    />
                  </div>
                  <div className="col-span-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeLineItem(idx)}
                      disabled={formData.line_items.length === 1}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
              <div className="text-right font-bold text-lg">
                Total: {formatCurrency(calculateTotal())}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={formData.notes || formData.description}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value, description: e.target.value })}
                rows={2}
                placeholder="Additional notes..."
              />
            </div>
            
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button type="submit" data-testid="job-submit-btn">
                {createMode === 'quote' ? 'Create Quote' : 'Create Job'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Pricing Calculator Modal for Line Items */}
      <PricingCalculatorModal
        isOpen={showPricingCalculator}
        onClose={() => setShowPricingCalculator(false)}
        onItemCalculated={handlePricingCalculatorItem}
      />

        {/* Jobs Table Content */}
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No jobs found</p>
            <Button variant="link" onClick={() => { setCreateMode('quote'); setIsDialogOpen(true); }}>
              Create your first quote
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {jobs.map((job) => (
              <div 
                key={job.id} 
                className="p-4 hover:bg-gray-50 transition-colors group cursor-pointer"
                data-testid={`job-row-${job.id}`}
                onClick={(e) => {
                  // Don't navigate if clicking on interactive elements
                  if (e.target.closest('button') || e.target.closest('[role="menu"]') || e.target.closest('a')) return;
                  navigate(`/jobs/${job.id}`);
                }}
              >
                <div className="flex items-center gap-4">
                  {/* Job Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span 
                        className="font-bold text-lg hover:text-blue-600 transition-colors truncate cursor-pointer text-gray-900"
                      >
                        {job.name}
                      </span>
                      {/* Interactive Status Badge */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="focus:outline-none" onClick={(e) => e.stopPropagation()}>
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
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{getCustomerName(job.customer_id)}</span>
                      {job.due_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" /> {formatDate(job.due_date)}
                        </span>
                      )}
                      {job.subtotal > 0 && (
                        <span className="text-blue-600 font-medium">
                          {formatCurrency(job.subtotal)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Show Approve button for quotes */}
                    {job.status === 'quote' && (
                        <Button
                          variant="default"
                          size="sm"
                          className="bg-green-600 hover:bg-green-700"
                          onClick={(e) => { e.stopPropagation(); handleApprove(job.id); }}
                          data-testid={`approve-job-${job.id}`}
                        >
                          <ArrowRightCircle className="h-4 w-4 mr-1" /> Approve
                        </Button>
                      )}
                      <Button
                        variant="default"
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); navigate(`/jobs/${job.id}`); }}
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
                          {/* Approve option for quotes */}
                          {job.status === 'quote' && (
                            <DropdownMenuItem onClick={() => handleApprove(job.id)}>
                              <ArrowRightCircle className="h-4 w-4 mr-2 text-green-600" /> Approve Quote
                            </DropdownMenuItem>
                          )}
                          {job.status !== 'completed' && job.status !== 'archived' && job.status !== 'quote' && (
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
      </ShellCard>
    </PageStack>
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
    createTask,
    startJobTimer, stopJobTimer, getJobTimeEntries, getJobTimeSummary, getJobActiveTimer, deleteJobTimeEntry
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
  
  // Time tracking state
  const [timeEntries, setTimeEntries] = useState([]);
  const [timeSummary, setTimeSummary] = useState(null);
  const [activeTimer, setActiveTimer] = useState(null);
  const [isTimerLoading, setIsTimerLoading] = useState(false);
  const [timerTaskType, setTimerTaskType] = useState('production');
  const [timerDescription, setTimerDescription] = useState('');
  const [runningTime, setRunningTime] = useState(0);
  
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    status: '',
    due_date: ''
  });
  
  // Invoice preview modal state
  const [previewInvoiceId, setPreviewInvoiceId] = useState(null);
  const [isInvoiceModalOpen, setIsInvoiceModalOpen] = useState(false);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  
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
    unit_price: '',
    status: 'pending',
    notes: '',
    pricing_category: null,
    pricing_data: null,
    cost_snapshot: null,
    production_cost: 0,
    profit_amount: 0,
    profit_margin_percent: 0,
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
      unit_price: calculatedData.unit_price || calculatedData.selling_price || calculatedData.suggested_price || 0,
      status: 'pending',
      notes: calculatedData.cost_snapshot ? 
        `Cost: $${calculatedData.cost_snapshot.total_cost?.toFixed(2)} | Profit: $${calculatedData.cost_snapshot.profit_amount?.toFixed(2)} (${calculatedData.cost_snapshot.profit_margin_percent?.toFixed(0)}%)` : '',
      pricing_category: calculatedData.pricing_category || calculatedData.category,
      pricing_data: calculatedData.pricing_data,
      cost_snapshot: calculatedData.cost_snapshot,
      production_cost: calculatedData.production_cost || calculatedData.cost_snapshot?.total_cost || 0,
      profit_amount: calculatedData.profit_amount || calculatedData.cost_snapshot?.profit_amount || 0,
      profit_margin_percent: calculatedData.profit_margin_percent || calculatedData.cost_snapshot?.profit_margin_percent || 0,
    });
    
    setIsCalculatorOpen(false);
    setIsItemDialogOpen(true);
    toast.success('Item calculated! Review and save.');
  };

  useEffect(() => {
    loadJobDetails();
    fetchCustomers();
    loadTimeTracking();
  }, [id]);

  // Update running time every second when timer is active
  useEffect(() => {
    let interval;
    if (activeTimer) {
      interval = setInterval(() => {
        const start = new Date(activeTimer.start_time);
        const now = new Date();
        const diffSeconds = Math.floor((now - start) / 1000);
        setRunningTime(diffSeconds);
      }, 1000);
    } else {
      setRunningTime(0);
    }
    return () => clearInterval(interval);
  }, [activeTimer]);

  const loadTimeTracking = async () => {
    try {
      const [entriesData, summaryData, activeData] = await Promise.all([
        getJobTimeEntries(id),
        getJobTimeSummary(id),
        getJobActiveTimer(id)
      ]);
      setTimeEntries(entriesData || []);
      setTimeSummary(summaryData);
      if (activeData?.has_active_timer) {
        setActiveTimer(activeData.entry);
      } else {
        setActiveTimer(null);
      }
    } catch (err) {
      console.error('Failed to load time tracking:', err);
    }
  };

  const handleStartTimer = async () => {
    setIsTimerLoading(true);
    try {
      const result = await startJobTimer(id, {
        description: timerDescription || undefined,
        task_type: timerTaskType
      });
      setActiveTimer(result);
      setTimerDescription('');
      await loadTimeTracking();
      toast.success('Timer started!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start timer');
    }
    setIsTimerLoading(false);
  };

  const handleStopTimer = async () => {
    setIsTimerLoading(true);
    try {
      await stopJobTimer(id);
      setActiveTimer(null);
      await loadTimeTracking();
      toast.success('Timer stopped!');
    } catch (err) {
      toast.error('Failed to stop timer');
    }
    setIsTimerLoading(false);
  };

  const handleDeleteTimeEntry = async (entryId) => {
    try {
      await deleteJobTimeEntry(id, entryId);
      await loadTimeTracking();
      toast.success('Time entry deleted');
    } catch (err) {
      toast.error('Failed to delete time entry');
    }
  };

  const formatTimeDisplay = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

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
      notes: item.notes || '',
      pricing_category: item.pricing_category,
      pricing_data: item.pricing_data,
      cost_snapshot: item.cost_snapshot,
      production_cost: item.production_cost || item.cost_snapshot?.total_cost || 0,
      profit_amount: item.profit_amount || item.cost_snapshot?.profit_amount || 0,
      profit_margin_percent: item.profit_margin_percent || item.cost_snapshot?.profit_margin_percent || 0,
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
      unit_price: '',
      status: 'pending',
      notes: '',
      pricing_category: null,
      pricing_data: null,
      cost_snapshot: null,
      production_cost: 0,
      profit_amount: 0,
      profit_margin_percent: 0,
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
                    <h1 className="text-3xl font-bold font-heading uppercase text-white">{job.name}</h1>
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
              <Button variant="outline" onClick={() => setShowHistoryPanel(true)} data-testid="view-job-history-btn">
                <GitBranch className="h-4 w-4 mr-2" /> View Timeline
              </Button>
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

      {/* Tabs: Line Items, Notes, Activity, Time Tracking */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="items">
            <Package className="h-4 w-4 mr-2" /> Line Items ({job_items.length})
          </TabsTrigger>
          <TabsTrigger value="time">
            <Timer className="h-4 w-4 mr-2" /> Time {timeSummary && timeSummary.total_hours > 0 ? `(${timeSummary.total_hours.toFixed(1)}h)` : ''}
          </TabsTrigger>
          <TabsTrigger value="notes">
            <MessageSquare className="h-4 w-4 mr-2" /> Notes ({notes.length})
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Activity className="h-4 w-4 mr-2" /> Activity ({activities.length})
          </TabsTrigger>
          <TabsTrigger value="timeline">
            <GitBranch className="h-4 w-4 mr-2" /> Timeline
          </TabsTrigger>
        </TabsList>

        {/* Time Tracking Tab */}
        <TabsContent value="time" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Timer Control Panel */}
            <Card className="bg-card border-border/50 lg:col-span-1">
              <CardHeader className="pb-3">
                <CardTitle className="font-heading uppercase text-sm flex items-center gap-2">
                  <Timer className="h-4 w-4" /> Job Timer
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {activeTimer ? (
                  /* Active Timer Display */
                  <div className="space-y-4">
                    <div className="text-center p-6 bg-green-500/10 border border-green-500/30 rounded-xl">
                      <div className="text-4xl font-mono font-bold text-green-400" data-testid="active-timer-display">
                        {formatTimeDisplay(runningTime)}
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        {activeTimer.task_type && <Badge variant="outline" className="mr-2">{activeTimer.task_type}</Badge>}
                        {activeTimer.description || 'Working...'}
                      </p>
                    </div>
                    <Button 
                      onClick={handleStopTimer}
                      disabled={isTimerLoading}
                      className="w-full bg-red-600 hover:bg-red-700"
                      data-testid="stop-timer-btn"
                    >
                      {isTimerLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Square className="h-4 w-4 mr-2" />
                      )}
                      Stop Timer
                    </Button>
                  </div>
                ) : (
                  /* Start Timer Form */
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Task Type</Label>
                      <Select value={timerTaskType} onValueChange={setTimerTaskType}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {taskTypes.map((t) => (
                            <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Description (optional)</Label>
                      <Input
                        placeholder="What are you working on?"
                        value={timerDescription}
                        onChange={(e) => setTimerDescription(e.target.value)}
                      />
                    </div>
                    <Button 
                      onClick={handleStartTimer}
                      disabled={isTimerLoading}
                      className="w-full bg-green-600 hover:bg-green-700"
                      data-testid="start-timer-btn"
                    >
                      {isTimerLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4 mr-2" />
                      )}
                      Start Timer
                    </Button>
                  </div>
                )}

                {/* Summary Stats */}
                {timeSummary && timeSummary.entries_count > 0 && (
                  <div className="pt-4 border-t border-border/50 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Time:</span>
                      <span className="font-medium">{timeSummary.total_hours.toFixed(2)} hours</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Labor Cost:</span>
                      <span className="font-medium">{formatCurrency(timeSummary.total_labor_cost)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Entries:</span>
                      <span className="font-medium">{timeSummary.entries_count}</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Time Entries List */}
            <Card className="bg-card border-border/50 lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="font-heading uppercase text-sm">Time Log</CardTitle>
              </CardHeader>
              <CardContent>
                {timeEntries.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No time entries yet</p>
                    <p className="text-sm">Start the timer to track time on this job</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {timeEntries.map((entry) => (
                      <div 
                        key={entry.id} 
                        className={cn(
                          "flex items-center justify-between p-3 rounded-lg border",
                          entry.is_active ? "bg-green-500/10 border-green-500/30" : "bg-muted/30 border-border/50"
                        )}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">{entry.task_type}</Badge>
                            <span className="text-sm font-medium">{entry.employee_name}</span>
                            {entry.is_active && (
                              <Badge className="bg-green-500 text-white animate-pulse">Active</Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            {entry.description || 'No description'}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatDateTime(entry.start_time)}
                            {entry.end_time && ` - ${formatDateTime(entry.end_time)}`}
                          </p>
                        </div>
                        <div className="text-right flex items-center gap-3">
                          <div>
                            <p className="font-mono font-medium">
                              {entry.is_active ? formatTimeDisplay(runningTime) : `${entry.duration_minutes?.toFixed(0) || 0} min`}
                            </p>
                            {entry.labor_cost > 0 && (
                              <p className="text-xs text-muted-foreground">{formatCurrency(entry.labor_cost)}</p>
                            )}
                          </div>
                          {!entry.is_active && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteTimeEntry(entry.id)}
                              className="text-destructive hover:bg-destructive/10"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

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
                        <TableHead>Timeline</TableHead>
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
                          <TableCell>
                            <TimelineToggle
                              jobId={job.id}
                              lineItemId={item.id}
                              lineItemName={item.description}
                              timelineEnabled={item.timeline_enabled}
                              onTimelineChange={(enabled) => {
                                // Update local state to show timeline status
                                loadJobDetails();
                              }}
                            />
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

        {/* Timeline Tab - Visual Status Flow */}
        <TabsContent value="timeline" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle className="font-heading uppercase flex items-center gap-2">
                <GitBranch className="h-5 w-5" /> Job Status Timeline
              </CardTitle>
              <CardDescription>Visual progression through production stages</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Status Flow Diagram */}
              <div className="mb-8">
                <div className="flex items-center justify-between max-w-4xl mx-auto">
                  {statusOptions.filter(s => s !== 'archived').map((status, index, arr) => {
                    const isCurrentStatus = job?.status === status;
                    const isPastStatus = statusOptions.indexOf(job?.status) > statusOptions.indexOf(status);
                    const statusActivity = activities.find(a => 
                      a.activity_type === 'status_changed' && a.new_status === status
                    );
                    
                    return (
                      <div key={status} className="flex items-center flex-1">
                        <div className="flex flex-col items-center">
                          <div 
                            className={cn(
                              "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all",
                              isCurrentStatus 
                                ? "bg-primary border-primary text-primary-foreground scale-110 shadow-lg" 
                                : isPastStatus 
                                  ? "bg-green-500 border-green-500 text-white"
                                  : "bg-muted border-muted-foreground/30 text-muted-foreground"
                            )}
                          >
                            {isPastStatus ? (
                              <CheckCircle className="h-5 w-5" />
                            ) : (
                              <span className="text-xs font-bold">{index + 1}</span>
                            )}
                          </div>
                          <span 
                            className={cn(
                              "text-xs mt-2 font-medium text-center",
                              isCurrentStatus ? "text-primary" : isPastStatus ? "text-green-600" : "text-muted-foreground"
                            )}
                          >
                            {statusLabels[status]}
                          </span>
                          {statusActivity && (
                            <span className="text-[10px] text-muted-foreground mt-1">
                              {new Date(statusActivity.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        {index < arr.length - 1 && (
                          <div 
                            className={cn(
                              "flex-1 h-1 mx-2",
                              isPastStatus ? "bg-green-500" : "bg-muted"
                            )}
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Status Change History */}
              <div className="border-t border-border/50 pt-6">
                <h4 className="text-sm font-medium uppercase tracking-wider text-muted-foreground mb-4">
                  Status Change History
                </h4>
                {(() => {
                  const statusChanges = activities.filter(a => 
                    a.activity_type === 'status_changed' || 
                    a.activity_type === 'created' ||
                    a.activity_type === 'completed' ||
                    a.activity_type === 'archived' ||
                    a.activity_type === 'unarchived'
                  );
                  
                  if (statusChanges.length === 0) {
                    return (
                      <p className="text-center text-muted-foreground py-4">No status changes recorded</p>
                    );
                  }
                  
                  return (
                    <div className="space-y-3">
                      {statusChanges.map((activity, index) => {
                        const prevActivity = statusChanges[index + 1];
                        let timeInStatus = null;
                        
                        if (prevActivity) {
                          const current = new Date(activity.created_at);
                          const prev = new Date(prevActivity.created_at);
                          const diffMs = current - prev;
                          const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                          const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                          
                          if (diffHours > 24) {
                            const diffDays = Math.floor(diffHours / 24);
                            timeInStatus = `${diffDays} day${diffDays > 1 ? 's' : ''}`;
                          } else if (diffHours > 0) {
                            timeInStatus = `${diffHours}h ${diffMins}m`;
                          } else {
                            timeInStatus = `${diffMins} min`;
                          }
                        }
                        
                        return (
                          <div 
                            key={activity.id}
                            className="flex items-center gap-4 p-3 rounded-lg bg-muted/30 border border-border/50"
                          >
                            <div className="flex-shrink-0">
                              {activity.old_status && activity.new_status ? (
                                <div className="flex items-center gap-2">
                                  <Badge variant="outline" className={cn(statusColors[activity.old_status], "text-xs")}>
                                    {statusLabels[activity.old_status] || activity.old_status}
                                  </Badge>
                                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                                  <Badge className={cn(statusColors[activity.new_status])}>
                                    {statusLabels[activity.new_status] || activity.new_status}
                                  </Badge>
                                </div>
                              ) : (
                                <Badge variant="outline">{activity.activity_type.replace('_', ' ')}</Badge>
                              )}
                            </div>
                            <div className="flex-1">
                              <p className="text-sm">{activity.description}</p>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <p className="text-xs text-muted-foreground">
                                {formatDateTime(activity.created_at)}
                              </p>
                              {timeInStatus && (
                                <p className="text-xs text-primary font-medium mt-1">
                                  <Clock className="h-3 w-3 inline mr-1" />
                                  {timeInStatus} in previous status
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
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

      <JobHistoryPanel
        isOpen={showHistoryPanel}
        onClose={() => setShowHistoryPanel(false)}
        jobId={job.id}
        jobName={job.name}
        onOpenInvoice={(invoiceId) => {
          setPreviewInvoiceId(invoiceId);
          setIsInvoiceModalOpen(true);
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
