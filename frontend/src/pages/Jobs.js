import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor, cn } from '../lib/utils';
import { Plus, Edit2, Trash2, Receipt, GripVertical, Calendar, ArrowLeft, Package } from 'lucide-react';
import { toast } from 'sonner';

const statusOptions = ['quoted', 'approved', 'in_production', 'installed', 'complete'];
const statusLabels = {
  quoted: 'Quoted',
  approved: 'Approved',
  in_production: 'In Production',
  installed: 'Installed',
  complete: 'Complete'
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

export default function Jobs() {
  const { 
    jobs, customers, fetchJobs, fetchCustomers, 
    createJob, updateJob, deleteJob, createInvoiceFromJob,
    fetchJobItems, createJobItem, updateJobItem, deleteJobItem
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [view, setView] = useState('list');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobItems, setJobItems] = useState([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [isItemDialogOpen, setIsItemDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  const [formData, setFormData] = useState({
    customer_id: '',
    name: '',
    description: '',
    status: 'quoted',
    due_date: ''
  });

  const [itemFormData, setItemFormData] = useState({
    item_type: 'other',
    description: '',
    quantity: 1,
    unit_price: 0,
    status: 'pending',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  useEffect(() => {
    if (selectedJob) {
      loadJobItems(selectedJob.id);
    }
  }, [selectedJob]);

  const loadData = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    await Promise.all([fetchJobs(params), fetchCustomers()]);
    setLoading(false);
  };

  const loadJobItems = async (jobId) => {
    setLoadingItems(true);
    try {
      const items = await fetchJobItems(jobId);
      setJobItems(items);
    } catch (err) {
      console.error('Error loading job items:', err);
      setJobItems([]);
    }
    setLoadingItems(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_id) {
      toast.error('Please select a customer');
      return;
    }
    if (!formData.name.trim()) {
      toast.error('Please enter a job name');
      return;
    }
    try {
      if (editingJob) {
        await updateJob(editingJob.id, {
          name: formData.name,
          description: formData.description,
          status: formData.status,
          due_date: formData.due_date || null
        });
        toast.success('Job updated');
        if (selectedJob && selectedJob.id === editingJob.id) {
          setSelectedJob({ ...selectedJob, ...formData });
        }
      } else {
        const newJob = await createJob(formData);
        toast.success('Job created');
        setSelectedJob(newJob);
      }
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save job');
    }
  };

  const handleItemSubmit = async (e) => {
    e.preventDefault();
    if (!itemFormData.description.trim()) {
      toast.error('Please enter an item description');
      return;
    }
    try {
      if (editingItem) {
        await updateJobItem(editingItem.id, itemFormData);
        toast.success('Item updated');
      } else {
        await createJobItem(selectedJob.id, itemFormData);
        toast.success('Item added');
      }
      await loadJobItems(selectedJob.id);
      await fetchJobs(); // Refresh jobs to update subtotal
      resetItemForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save item');
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('Delete this line item?')) {
      try {
        await deleteJobItem(itemId);
        await loadJobItems(selectedJob.id);
        await fetchJobs(); // Refresh jobs to update subtotal
        toast.success('Item deleted');
      } catch (err) {
        toast.error('Failed to delete item');
      }
    }
  };

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      await updateJob(jobId, { status: newStatus });
      toast.success('Job status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleItemStatusChange = async (itemId, newStatus) => {
    try {
      await updateJobItem(itemId, { status: newStatus });
      await loadJobItems(selectedJob.id);
      toast.success('Item status updated');
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const handleCreateInvoice = async (jobId) => {
    try {
      await createInvoiceFromJob(jobId);
      toast.success('Invoice created from job');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const handleEdit = (job) => {
    setEditingJob(job);
    setFormData({
      customer_id: job.customer_id,
      name: job.name,
      description: job.description || '',
      status: job.status,
      due_date: job.due_date || ''
    });
    setIsDialogOpen(true);
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

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await deleteJob(id);
        if (selectedJob && selectedJob.id === id) {
          setSelectedJob(null);
        }
        toast.success('Job deleted');
      } catch (err) {
        toast.error('Failed to delete job');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      name: '',
      description: '',
      status: 'quoted',
      due_date: ''
    });
    setEditingJob(null);
    setIsDialogOpen(false);
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

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || 'Unknown';
  };

  // Calculate subtotal from items
  const calculateSubtotal = () => {
    return jobItems.reduce((sum, item) => sum + (item.line_total || 0), 0);
  };

  // Group jobs by status for Kanban
  const jobsByStatus = statusOptions.reduce((acc, status) => {
    acc[status] = jobs.filter(j => j.status === status);
    return acc;
  }, {});

  // Job Detail View
  if (selectedJob) {
    const currentJob = jobs.find(j => j.id === selectedJob.id) || selectedJob;
    
    return (
      <div className="space-y-6 animate-fade-in" data-testid="job-detail-page">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            onClick={() => setSelectedJob(null)}
            data-testid="back-to-jobs"
          >
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Jobs
          </Button>
        </div>

        {/* Job Info Card */}
        <Card className="bg-card border-border/50">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h1 className="text-3xl font-bold font-heading uppercase">{currentJob.name}</h1>
                  <Badge className={getStatusColor(currentJob.status)}>
                    {statusLabels[currentJob.status]}
                  </Badge>
                </div>
                <p className="text-muted-foreground">
                  Customer: <span className="text-foreground">{getCustomerName(currentJob.customer_id)}</span>
                </p>
                {currentJob.due_date && (
                  <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1">
                    <Calendar className="h-4 w-4" /> Due: {formatDate(currentJob.due_date)}
                  </p>
                )}
                {currentJob.description && (
                  <p className="text-sm text-muted-foreground mt-3 p-3 bg-muted/30 rounded-lg">
                    <strong>Notes:</strong> {currentJob.description}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <div className="text-right p-4 bg-primary/10 rounded-lg border border-primary/30">
                  <p className="text-sm text-muted-foreground">Subtotal</p>
                  <p className="text-2xl font-bold text-primary">{formatCurrency(calculateSubtotal())}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleEdit(currentJob)}>
                    <Edit2 className="h-4 w-4 mr-1" /> Edit
                  </Button>
                  {!currentJob.invoice_id && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleCreateInvoice(currentJob.id)}
                      data-testid="create-invoice-btn"
                    >
                      <Receipt className="h-4 w-4 mr-1" /> Create Invoice
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card className="bg-card border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="font-heading uppercase flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                Line Items ({jobItems.length})
              </CardTitle>
              <Dialog open={isItemDialogOpen} onOpenChange={setIsItemDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="neon-glow" data-testid="add-line-item-btn" onClick={() => resetItemForm()}>
                    <Plus className="h-4 w-4 mr-2" /> Add Line Item
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
                    <DialogTitle className="font-heading uppercase">
                      {editingItem ? 'Edit Line Item' : 'Add Line Item'}
                    </DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleItemSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Item Type</Label>
                        <Select
                          value={itemFormData.item_type}
                          onValueChange={(val) => setItemFormData({ ...itemFormData, item_type: val })}
                        >
                          <SelectTrigger data-testid="item-type-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {itemTypes.map((t) => (
                              <SelectItem key={t} value={t}>
                                {itemTypeLabels[t]}
                              </SelectItem>
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
                          <SelectTrigger data-testid="item-status-select">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {itemStatusOptions.map((s) => (
                              <SelectItem key={s} value={s}>
                                {itemStatusLabels[s]}
                              </SelectItem>
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
                        placeholder="e.g., 4x8 Banner with grommets"
                        data-testid="item-description-input"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Quantity</Label>
                        <Input
                          type="number"
                          min="1"
                          step="1"
                          value={itemFormData.quantity}
                          onChange={(e) => setItemFormData({ ...itemFormData, quantity: parseFloat(e.target.value) || 1 })}
                          data-testid="item-quantity-input"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Unit Price</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={itemFormData.unit_price}
                          onChange={(e) => setItemFormData({ ...itemFormData, unit_price: parseFloat(e.target.value) || 0 })}
                          data-testid="item-price-input"
                        />
                      </div>
                    </div>
                    <div className="p-3 bg-muted/30 rounded-lg text-right">
                      <span className="text-sm text-muted-foreground">Line Total: </span>
                      <span className="text-lg font-bold text-primary">
                        {formatCurrency(itemFormData.quantity * itemFormData.unit_price)}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <Label>Notes</Label>
                      <Textarea
                        value={itemFormData.notes}
                        onChange={(e) => setItemFormData({ ...itemFormData, notes: e.target.value })}
                        placeholder="Optional notes or file references"
                        rows={2}
                        data-testid="item-notes-input"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" onClick={resetItemForm}>
                        Cancel
                      </Button>
                      <Button type="submit" data-testid="item-submit-btn">
                        {editingItem ? 'Update' : 'Add Item'}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            {loadingItems ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              </div>
            ) : jobItems.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground border-2 border-dashed border-border/50 rounded-lg">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No line items yet</p>
                <Button variant="link" onClick={() => setIsItemDialogOpen(true)}>
                  Add your first line item
                </Button>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center">Qty</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Line Total</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobItems.map((item, idx) => (
                      <TableRow 
                        key={item.id} 
                        className={idx % 2 === 0 ? 'bg-transparent' : 'bg-muted/30'}
                        data-testid={`job-item-row-${item.id}`}
                      >
                        <TableCell>
                          <Badge variant="outline">{itemTypeLabels[item.item_type] || item.item_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{item.description}</p>
                            {item.notes && (
                              <p className="text-xs text-muted-foreground mt-1">{item.notes}</p>
                            )}
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
                                <SelectItem key={s} value={s}>
                                  {itemStatusLabels[s]}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleEditItem(item)}
                              data-testid={`edit-item-${item.id}`}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteItem(item.id)}
                              data-testid={`delete-item-${item.id}`}
                            >
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
                    <span className="text-2xl font-bold text-primary">{formatCurrency(calculateSubtotal())}</span>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Jobs List View
  return (
    <div className="space-y-6 animate-fade-in" data-testid="jobs-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Jobs</h1>
          <p className="text-muted-foreground mt-1">{jobs.length} total jobs</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-job-btn" onClick={() => resetForm()}>
              <Plus className="h-4 w-4 mr-2" /> New Job
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">
                {editingJob ? 'Edit Job' : 'New Job'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select
                  value={formData.customer_id}
                  onValueChange={(val) => setFormData({ ...formData, customer_id: val })}
                  disabled={!!editingJob}
                >
                  <SelectTrigger data-testid="job-customer-select">
                    <SelectValue placeholder="Select customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                      </SelectItem>
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
                    <SelectTrigger data-testid="job-status-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {statusOptions.map((s) => (
                        <SelectItem key={s} value={s}>
                          {statusLabels[s]}
                        </SelectItem>
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
                <Label>Overall Notes</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  placeholder="General job notes (line items hold the actual work)"
                  data-testid="job-description-input"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="job-submit-btn">
                  {editingJob ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* View Tabs */}
      <Tabs value={view} onValueChange={setView}>
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="list" data-testid="jobs-list-view">List</TabsTrigger>
            <TabsTrigger value="kanban" data-testid="jobs-kanban-view">Kanban</TabsTrigger>
          </TabsList>
          {view === 'list' && (
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]" data-testid="job-filter-status">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {statusOptions.map((s) => (
                  <SelectItem key={s} value={s}>
                    {statusLabels[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* List View */}
        <TabsContent value="list" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                </div>
              ) : jobs.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No jobs found</p>
                  <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                    Create your first job
                  </Button>
                </div>
              ) : (
                <div className="divide-y divide-border/50">
                  {jobs.map((job) => (
                    <div 
                      key={job.id} 
                      className="p-4 hover:bg-muted/30 transition-colors cursor-pointer"
                      onClick={() => setSelectedJob(job)}
                      data-testid={`job-row-${job.id}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="font-bold truncate">{job.name}</h3>
                            <Badge className={getStatusColor(job.status)}>
                              {statusLabels[job.status]}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-2">
                            Customer: {getCustomerName(job.customer_id)}
                          </p>
                          <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                            {job.due_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" /> Due: {formatDate(job.due_date)}
                              </span>
                            )}
                            <span>Created: {formatDate(job.created_at)}</span>
                            {job.subtotal > 0 && (
                              <span className="text-primary font-medium">
                                Subtotal: {formatCurrency(job.subtotal)}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          {!job.invoice_id && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCreateInvoice(job.id)}
                              data-testid={`create-invoice-${job.id}`}
                            >
                              <Receipt className="h-4 w-4 mr-1" /> Invoice
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(job)}
                            data-testid={`edit-job-${job.id}`}
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(job.id)}
                            data-testid={`delete-job-${job.id}`}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Kanban View */}
        <TabsContent value="kanban" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 overflow-x-auto">
            {statusOptions.map((status) => (
              <div key={status} className="min-w-[280px]">
                <div className="bg-muted/30 rounded-lg p-3 mb-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-sm uppercase tracking-wide">
                      {statusLabels[status]}
                    </h3>
                    <Badge variant="outline">{jobsByStatus[status].length}</Badge>
                  </div>
                </div>
                <div className="space-y-3">
                  {jobsByStatus[status].map((job) => (
                    <Card 
                      key={job.id} 
                      className="bg-card border-border/50 hover:border-primary/30 transition-all cursor-pointer"
                      onClick={() => setSelectedJob(job)}
                      data-testid={`kanban-job-${job.id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start gap-2">
                          <GripVertical className="h-4 w-4 text-muted-foreground mt-1 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-sm truncate">{job.name}</h4>
                            <p className="text-xs text-muted-foreground mt-1">
                              {getCustomerName(job.customer_id)}
                            </p>
                            {job.due_date && (
                              <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
                                <Calendar className="h-3 w-3" /> {formatDate(job.due_date)}
                              </p>
                            )}
                            {job.subtotal > 0 && (
                              <p className="text-xs text-primary font-medium mt-2">
                                {formatCurrency(job.subtotal)}
                              </p>
                            )}
                            {/* Status Change Dropdown */}
                            <div className="mt-3" onClick={(e) => e.stopPropagation()}>
                              <Select
                                value={job.status}
                                onValueChange={(val) => handleStatusChange(job.id, val)}
                              >
                                <SelectTrigger className="h-8 text-xs">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {statusOptions.map((s) => (
                                    <SelectItem key={s} value={s}>
                                      {statusLabels[s]}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {jobsByStatus[status].length === 0 && (
                    <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed border-border/50 rounded-lg">
                      No jobs
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
