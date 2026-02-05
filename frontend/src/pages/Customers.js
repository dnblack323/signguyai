import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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
import { formatDate, formatCurrency, getStatusColor, getInitials } from '../lib/utils';
import { 
  Plus, Search, Edit2, Trash2, Mail, Phone, Building, 
  User, Briefcase, Receipt, FileText, Calendar, Eye,
  DollarSign, Clock
} from 'lucide-react';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

const statusOptions = ['lead', 'active', 'inactive'];

export default function Customers() {
  const { 
    customers, fetchCustomers, createCustomer, updateCustomer, deleteCustomer,
    jobs, fetchJobs, invoices, fetchInvoices, quotes, fetchQuotes
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    phone: '',
    email: '',
    status: 'lead',
    notes: ''
  });
  
  // Customer detail modal state
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [detailTab, setDetailTab] = useState('overview');

  useEffect(() => {
    loadCustomers();
  }, [statusFilter, search]);

  useEffect(() => {
    // Load related data for customer details
    fetchJobs();
    fetchInvoices();
    fetchQuotes();
  }, []);

  const loadCustomers = async () => {
    setLoading(true);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (search) params.search = search;
    await fetchCustomers(params);
    setLoading(false);
  };

  const handleViewCustomer = (customer) => {
    setSelectedCustomer(customer);
    setDetailTab('overview');
    setIsDetailOpen(true);
  };

  // Get customer-related data
  const getCustomerJobs = (customerId) => {
    return jobs.filter(j => j.customer_id === customerId);
  };

  const getCustomerInvoices = (customerId) => {
    return invoices.filter(i => i.customer_id === customerId);
  };

  const getCustomerQuotes = (customerId) => {
    return quotes.filter(q => q.customer_id === customerId);
  };

  const getCustomerStats = (customerId) => {
    const customerJobs = getCustomerJobs(customerId);
    const customerInvoices = getCustomerInvoices(customerId);
    
    const activeJobs = customerJobs.filter(j => !['complete', 'archived'].includes(j.status));
    const completedJobs = customerJobs.filter(j => j.status === 'complete');
    const totalRevenue = customerInvoices.reduce((sum, i) => sum + (i.total || 0), 0);
    const outstandingBalance = customerInvoices
      .filter(i => i.status !== 'paid')
      .reduce((sum, i) => sum + ((i.total || 0) - (i.amount_paid || 0)), 0);
    
    return { activeJobs, completedJobs, totalRevenue, outstandingBalance, customerJobs, customerInvoices };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCustomer) {
        await updateCustomer(editingCustomer.id, formData);
        toast.success('Customer updated');
      } else {
        await createCustomer(formData);
        toast.success('Customer created');
      }
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save customer');
    }
  };

  const handleEdit = (customer) => {
    setEditingCustomer(customer);
    setFormData({
      name: customer.name,
      company: customer.company || '',
      phone: customer.phone || '',
      email: customer.email || '',
      status: customer.status,
      notes: customer.notes || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this customer?')) {
      try {
        await deleteCustomer(id);
        toast.success('Customer deleted');
      } catch (err) {
        toast.error('Failed to delete customer');
      }
    }
  };

  const resetForm = () => {
    setFormData({ name: '', company: '', phone: '', email: '', status: 'lead', notes: '' });
    setEditingCustomer(null);
    setIsDialogOpen(false);
  };

  const filteredCustomers = customers;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="customers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Customers</h1>
          <p className="text-muted-foreground mt-1">{customers.length} total customers</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-customer-btn" onClick={() => resetForm()}>
              <Plus className="h-4 w-4 mr-2" /> Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">
                {editingCustomer ? 'Edit Customer' : 'New Customer'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    data-testid="customer-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    data-testid="customer-company-input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    data-testid="customer-email-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    data-testid="customer-phone-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(val) => setFormData({ ...formData, status: val })}
                >
                  <SelectTrigger data-testid="customer-status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  data-testid="customer-notes-input"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="customer-submit-btn">
                  {editingCustomer ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search customers..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
                data-testid="customer-search-input"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]" data-testid="customer-filter-status">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {statusOptions.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : filteredCustomers.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No customers found</p>
              <Button variant="link" onClick={() => setIsDialogOpen(true)}>
                Add your first customer
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Customer</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map((customer, idx) => (
                  <TableRow 
                    key={customer.id} 
                    className={`cursor-pointer transition-colors ${idx % 2 === 0 ? 'bg-transparent' : 'bg-muted/30'} hover:bg-muted/50`}
                    data-testid={`customer-row-${customer.id}`}
                    onClick={() => handleViewCustomer(customer)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                          <span className="text-primary font-bold text-sm">
                            {getInitials(customer.name)}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium">{customer.name}</p>
                          {customer.company && (
                            <p className="text-xs text-muted-foreground flex items-center gap-1">
                              <Building className="h-3 w-3" /> {customer.company}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {customer.email && (
                          <p className="text-sm flex items-center gap-1">
                            <Mail className="h-3 w-3 text-muted-foreground" /> {customer.email}
                          </p>
                        )}
                        {customer.phone && (
                          <p className="text-sm flex items-center gap-1">
                            <Phone className="h-3 w-3 text-muted-foreground" /> {customer.phone}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(customer.status)}>
                        {customer.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(customer.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(customer)}
                          data-testid={`edit-customer-${customer.id}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(customer.id)}
                          data-testid={`delete-customer-${customer.id}`}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
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

      {/* Customer Detail Modal */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto" data-testid="customer-detail-modal">
          {selectedCustomer && (() => {
            const stats = getCustomerStats(selectedCustomer.id);
            const customerQuotes = getCustomerQuotes(selectedCustomer.id);
            return (
              <>
                <DialogHeader>
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                      <span className="text-primary font-bold text-2xl">
                        {getInitials(selectedCustomer.name)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <DialogTitle className="text-2xl font-heading">{selectedCustomer.name}</DialogTitle>
                      {selectedCustomer.company && (
                        <p className="text-muted-foreground flex items-center gap-1">
                          <Building className="h-4 w-4" /> {selectedCustomer.company}
                        </p>
                      )}
                    </div>
                    <Badge className={getStatusColor(selectedCustomer.status)} data-testid="customer-status">
                      {selectedCustomer.status}
                    </Badge>
                  </div>
                </DialogHeader>

                {/* Quick Stats */}
                <div className="grid grid-cols-4 gap-3 my-4">
                  <div className="p-3 bg-muted/30 rounded-lg text-center">
                    <Briefcase className="h-5 w-5 mx-auto mb-1 text-blue-400" />
                    <p className="text-lg font-bold">{stats.activeJobs.length}</p>
                    <p className="text-xs text-muted-foreground">Active Jobs</p>
                  </div>
                  <div className="p-3 bg-muted/30 rounded-lg text-center">
                    <Clock className="h-5 w-5 mx-auto mb-1 text-green-400" />
                    <p className="text-lg font-bold">{stats.completedJobs.length}</p>
                    <p className="text-xs text-muted-foreground">Completed</p>
                  </div>
                  <div className="p-3 bg-muted/30 rounded-lg text-center">
                    <DollarSign className="h-5 w-5 mx-auto mb-1 text-primary" />
                    <p className="text-lg font-bold">{formatCurrency(stats.totalRevenue)}</p>
                    <p className="text-xs text-muted-foreground">Total Revenue</p>
                  </div>
                  <div className="p-3 bg-muted/30 rounded-lg text-center">
                    <Receipt className="h-5 w-5 mx-auto mb-1 text-yellow-400" />
                    <p className="text-lg font-bold">{formatCurrency(stats.outstandingBalance)}</p>
                    <p className="text-xs text-muted-foreground">Outstanding</p>
                  </div>
                </div>

                <Tabs value={detailTab} onValueChange={setDetailTab}>
                  <TabsList className="grid grid-cols-4 w-full">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="jobs">Jobs ({stats.customerJobs.length})</TabsTrigger>
                    <TabsTrigger value="invoices">Invoices ({stats.customerInvoices.length})</TabsTrigger>
                    <TabsTrigger value="quotes">Quotes ({customerQuotes.length})</TabsTrigger>
                  </TabsList>

                  {/* Overview Tab */}
                  <TabsContent value="overview" className="space-y-4 mt-4">
                    {/* Contact Info */}
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <User className="h-4 w-4" /> Contact Information
                      </h4>
                      <div className="grid grid-cols-2 gap-4 p-4 bg-muted/30 rounded-lg">
                        <div>
                          <p className="text-xs text-muted-foreground">Email</p>
                          <p className="font-medium flex items-center gap-2">
                            <Mail className="h-4 w-4 text-muted-foreground" />
                            {selectedCustomer.email || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Phone</p>
                          <p className="font-medium flex items-center gap-2">
                            <Phone className="h-4 w-4 text-muted-foreground" />
                            {selectedCustomer.phone || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Company</p>
                          <p className="font-medium flex items-center gap-2">
                            <Building className="h-4 w-4 text-muted-foreground" />
                            {selectedCustomer.company || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Customer Since</p>
                          <p className="font-medium flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            {formatDate(selectedCustomer.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Notes */}
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <FileText className="h-4 w-4" /> Notes
                      </h4>
                      <div className="p-4 bg-muted/30 rounded-lg min-h-[80px]">
                        {selectedCustomer.notes ? (
                          <p className="whitespace-pre-wrap">{selectedCustomer.notes}</p>
                        ) : (
                          <p className="text-muted-foreground italic">No notes added</p>
                        )}
                      </div>
                    </div>

                    {/* Recent Activity */}
                    {stats.activeJobs.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-3 flex items-center gap-2">
                          <Briefcase className="h-4 w-4" /> Active Jobs
                        </h4>
                        <div className="space-y-2">
                          {stats.activeJobs.slice(0, 3).map(job => (
                            <Link key={job.id} to={`/jobs/${job.id}`} onClick={() => setIsDetailOpen(false)}>
                              <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
                                <div>
                                  <p className="font-medium">{job.name}</p>
                                  <p className="text-xs text-muted-foreground">Due: {formatDate(job.due_date)}</p>
                                </div>
                                <Badge className={getStatusColor(job.status)}>{job.status.replace('_', ' ')}</Badge>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  {/* Jobs Tab */}
                  <TabsContent value="jobs" className="mt-4">
                    {stats.customerJobs.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No jobs for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {stats.customerJobs.map(job => (
                          <Link key={job.id} to={`/jobs/${job.id}`} onClick={() => setIsDetailOpen(false)}>
                            <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors">
                              <div className="flex-1">
                                <p className="font-medium">{job.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  Created: {formatDate(job.created_at)} • Due: {formatDate(job.due_date)}
                                </p>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="font-bold">{formatCurrency(job.subtotal || 0)}</span>
                                <Badge className={getStatusColor(job.status)}>{job.status.replace('_', ' ')}</Badge>
                              </div>
                            </div>
                          </Link>
                        ))}
                      </div>
                    )}
                  </TabsContent>

                  {/* Invoices Tab */}
                  <TabsContent value="invoices" className="mt-4">
                    {stats.customerInvoices.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Receipt className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No invoices for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {stats.customerInvoices.map(invoice => (
                          <div key={invoice.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                            <div className="flex-1">
                              <p className="font-medium font-mono">#{invoice.id.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-muted-foreground">
                                Created: {formatDate(invoice.created_at)}
                                {invoice.due_date && ` • Due: ${formatDate(invoice.due_date)}`}
                              </p>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className="text-right">
                                <p className="font-bold">{formatCurrency(invoice.total || 0)}</p>
                                {invoice.status !== 'paid' && invoice.amount_paid > 0 && (
                                  <p className="text-xs text-green-400">Paid: {formatCurrency(invoice.amount_paid)}</p>
                                )}
                              </div>
                              <Badge className={getStatusColor(invoice.status)}>{invoice.status}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>

                  {/* Quotes Tab */}
                  <TabsContent value="quotes" className="mt-4">
                    {customerQuotes.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No quotes for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {customerQuotes.map(quote => (
                          <div key={quote.id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                            <div className="flex-1">
                              <p className="font-medium font-mono">#{quote.id.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-muted-foreground">
                                Created: {formatDate(quote.created_at)}
                              </p>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="font-bold">{formatCurrency(quote.total || 0)}</span>
                              <Badge className={getStatusColor(quote.status)}>{quote.status}</Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>

                {/* Actions */}
                <Separator className="my-4" />
                <div className="flex justify-between">
                  <Button variant="outline" onClick={() => { setIsDetailOpen(false); handleEdit(selectedCustomer); }}>
                    <Edit2 className="h-4 w-4 mr-2" /> Edit Customer
                  </Button>
                  <Button variant="outline" onClick={() => setIsDetailOpen(false)}>
                    Close
                  </Button>
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}
