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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor, cn } from '../lib/utils';
import { Plus, Edit2, Trash2, Receipt, GripVertical, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const statusOptions = ['quoted', 'approved', 'in_production', 'installed', 'complete'];
const statusLabels = {
  quoted: 'Quoted',
  approved: 'Approved',
  in_production: 'In Production',
  installed: 'Installed',
  complete: 'Complete'
};

export default function Jobs() {
  const { 
    jobs, customers, fetchJobs, fetchCustomers, 
    createJob, updateJob, deleteJob, createInvoiceFromJob
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [view, setView] = useState('list');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingJob, setEditingJob] = useState(null);
  const [formData, setFormData] = useState({
    customer_id: '',
    name: '',
    description: '',
    status: 'quoted',
    due_date: ''
  });

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    await Promise.all([fetchJobs(params), fetchCustomers()]);
    setLoading(false);
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
      } else {
        await createJob(formData);
        toast.success('Job created');
      }
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save job');
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

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this job?')) {
      try {
        await deleteJob(id);
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

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer?.name || 'Unknown';
  };

  // Group jobs by status for Kanban
  const jobsByStatus = statusOptions.reduce((acc, status) => {
    acc[status] = jobs.filter(j => j.status === status);
    return acc;
  }, {});

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
                <Label>Description</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
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
                      className="p-4 hover:bg-muted/30 transition-colors"
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
                          {job.description && (
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {job.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                            {job.due_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" /> Due: {formatDate(job.due_date)}
                              </span>
                            )}
                            <span>Created: {formatDate(job.created_at)}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
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
                            {/* Status Change Dropdown */}
                            <div className="mt-3">
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
