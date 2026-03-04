import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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
  DialogDescription,
  DialogFooter,
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
  DollarSign, Clock, Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Download,
  ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const statusOptions = ['lead', 'active', 'inactive'];

export default function Customers() {
  const navigate = useNavigate();
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

  // CSV Import state
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [csvFile, setCsvFile] = useState(null);
  const [csvPreview, setCsvPreview] = useState([]);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [columnMapping, setColumnMapping] = useState({});
  const [importing, setImporting] = useState(false);
  const [importStep, setImportStep] = useState('upload'); // 'upload', 'map', 'preview', 'result'
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = useRef(null);

  // Available fields for mapping
  const availableFields = [
    { value: '', label: 'Skip this column' },
    { value: 'name', label: 'Name *', required: true },
    { value: 'company', label: 'Company' },
    { value: 'email', label: 'Email' },
    { value: 'phone', label: 'Phone' },
    { value: 'status', label: 'Status (lead/active/inactive)' },
    { value: 'notes', label: 'Notes' },
  ];

  useEffect(() => {
    loadCustomers();
  }, [statusFilter, search]);

  useEffect(() => {
    // Load related data for customer details
    fetchJobs();
    fetchInvoices();
    fetchQuotes();
    
    // Check URL params for auto-open import dialog
    const params = new URLSearchParams(window.location.search);
    if (params.get('import') === 'true') {
      setIsImportOpen(true);
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
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

  const handleSubmit = async (e, addJobAfter = false) => {
    e.preventDefault();
    try {
      if (editingCustomer) {
        await updateCustomer(editingCustomer.id, formData);
        toast.success('Customer updated');
        resetForm();
      } else {
        const newCustomer = await createCustomer(formData);
        toast.success('Customer created');
        resetForm();
        
        // If "Save & Add Job" was clicked, navigate to jobs page with customer pre-selected
        if (addJobAfter && newCustomer) {
          navigate(`/jobs?new=true&customer_id=${newCustomer.id}&customer_name=${encodeURIComponent(newCustomer.name)}`);
        }
      }
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

  // CSV Import Functions
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.csv')) {
      toast.error('Please select a CSV file');
      return;
    }
    
    setCsvFile(file);
    parseCSV(file);
  };

  const parseCSV = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length < 2) {
        toast.error('CSV file must have headers and at least one row of data');
        return;
      }
      
      // Parse headers (first row)
      const headers = parseCSVLine(lines[0]);
      setCsvHeaders(headers);
      
      // Auto-map columns based on header names
      const autoMapping = {};
      headers.forEach((header, index) => {
        const normalizedHeader = header.toLowerCase().trim();
        if (normalizedHeader.includes('name') && !normalizedHeader.includes('company')) {
          autoMapping[index] = 'name';
        } else if (normalizedHeader.includes('company') || normalizedHeader.includes('business')) {
          autoMapping[index] = 'company';
        } else if (normalizedHeader.includes('email')) {
          autoMapping[index] = 'email';
        } else if (normalizedHeader.includes('phone') || normalizedHeader.includes('tel')) {
          autoMapping[index] = 'phone';
        } else if (normalizedHeader.includes('status')) {
          autoMapping[index] = 'status';
        } else if (normalizedHeader.includes('note')) {
          autoMapping[index] = 'notes';
        }
      });
      setColumnMapping(autoMapping);
      
      // Parse data rows (preview first 5)
      const preview = [];
      for (let i = 1; i < Math.min(lines.length, 6); i++) {
        const values = parseCSVLine(lines[i]);
        preview.push(values);
      }
      setCsvPreview(preview);
      setImportStep('map');
    };
    reader.readAsText(file);
  };

  const parseCSVLine = (line) => {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());
    return values;
  };

  const handleImport = async () => {
    // Validate name column is mapped
    if (!Object.values(columnMapping).includes('name')) {
      toast.error('You must map the "Name" column');
      return;
    }
    
    setImporting(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        const lines = text.split('\n').filter(line => line.trim());
        
        // Skip header, process all data rows
        const customers = [];
        for (let i = 1; i < lines.length; i++) {
          const values = parseCSVLine(lines[i]);
          const customer = { status: 'lead' }; // Default status
          
          Object.entries(columnMapping).forEach(([colIndex, field]) => {
            if (field && values[parseInt(colIndex)]) {
              let value = values[parseInt(colIndex)].replace(/^["']|["']$/g, '').trim();
              // Normalize status values
              if (field === 'status') {
                value = value.toLowerCase();
                if (!['lead', 'active', 'inactive'].includes(value)) {
                  value = 'lead';
                }
              }
              customer[field] = value;
            }
          });
          
          // Only add if name is present
          if (customer.name) {
            customers.push(customer);
          }
        }
        
        if (customers.length === 0) {
          toast.error('No valid customers found in CSV');
          setImporting(false);
          return;
        }
        
        // Send to backend
        const token = localStorage.getItem('token');
        const response = await axios.post(
          `${API_URL}/api/customers/import`,
          { customers },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setImportResult(response.data);
        setImportStep('result');
        toast.success(`Successfully imported ${response.data.created} customers`);
        loadCustomers();
      };
      reader.readAsText(csvFile);
    } catch (err) {
      console.error('Import error:', err);
      toast.error(err.response?.data?.detail || 'Failed to import customers');
    }
    setImporting(false);
  };

  const resetImport = () => {
    setCsvFile(null);
    setCsvPreview([]);
    setCsvHeaders([]);
    setColumnMapping({});
    setImportStep('upload');
    setImportResult(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const downloadTemplate = () => {
    const template = 'Name,Company,Email,Phone,Status,Notes\nJohn Doe,Acme Inc,john@acme.com,555-1234,active,VIP customer\nJane Smith,,,555-5678,lead,New lead from website';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'customer_import_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredCustomers = customers;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="customers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight text-white">Customers</h1>
          <p className="text-slate-300 mt-1">{customers.length} total customers</p>
        </div>
        <div className="flex gap-2">
          {/* Import CSV Button */}
          <Dialog open={isImportOpen} onOpenChange={(open) => { setIsImportOpen(open); if (!open) resetImport(); }}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="import-csv-btn">
                <Upload className="h-4 w-4 mr-2" /> Import CSV
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle className="font-heading uppercase flex items-center gap-2">
                  <FileSpreadsheet className="h-5 w-5" />
                  Import Customers from CSV
                </DialogTitle>
                <DialogDescription>
                  Upload a CSV file to bulk import customers
                </DialogDescription>
              </DialogHeader>

              {/* Step 1: Upload */}
              {importStep === 'upload' && (
                <div className="space-y-4 py-4">
                  <div 
                    className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-lg font-medium">Click to upload CSV file</p>
                    <p className="text-sm text-muted-foreground mt-1">or drag and drop</p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                  </div>
                  <div className="flex items-center justify-center">
                    <Button variant="link" onClick={downloadTemplate}>
                      <Download className="h-4 w-4 mr-2" /> Download Template
                    </Button>
                  </div>
                </div>
              )}

              {/* Step 2: Map Columns */}
              {importStep === 'map' && (
                <div className="space-y-4 py-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Map your CSV columns to customer fields
                    </p>
                    <Badge variant="outline">{csvFile?.name}</Badge>
                  </div>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {csvHeaders.map((header, index) => (
                      <div key={index} className="flex items-center gap-3 p-2 rounded bg-muted/50">
                        <div className="w-1/3 font-medium truncate text-sm">{header}</div>
                        <span className="text-muted-foreground">→</span>
                        <Select
                          value={columnMapping[index] || ''}
                          onValueChange={(val) => setColumnMapping({ ...columnMapping, [index]: val })}
                        >
                          <SelectTrigger className="w-1/2">
                            <SelectValue placeholder="Select field" />
                          </SelectTrigger>
                          <SelectContent>
                            {availableFields.map((field) => (
                              <SelectItem key={field.value} value={field.value}>
                                {field.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>

                  {/* Preview */}
                  <div className="mt-4">
                    <p className="text-sm font-medium mb-2">Preview (first 5 rows):</p>
                    <div className="border rounded-lg overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {csvHeaders.map((header, index) => (
                              <TableHead key={index} className="text-xs">
                                {columnMapping[index] ? (
                                  <Badge variant="default" className="text-xs">{columnMapping[index]}</Badge>
                                ) : (
                                  <span className="text-muted-foreground">-</span>
                                )}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {csvPreview.map((row, rowIndex) => (
                            <TableRow key={rowIndex}>
                              {row.map((cell, cellIndex) => (
                                <TableCell key={cellIndex} className="text-xs py-1 truncate max-w-[100px]">
                                  {cell || '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>

                  <DialogFooter className="flex gap-2">
                    <Button variant="outline" onClick={resetImport}>Cancel</Button>
                    <Button onClick={handleImport} disabled={importing || !Object.values(columnMapping).includes('name')}>
                      {importing ? 'Importing...' : 'Import Customers'}
                    </Button>
                  </DialogFooter>
                </div>
              )}

              {/* Step 3: Results */}
              {importStep === 'result' && importResult && (
                <div className="space-y-4 py-4">
                  <div className="text-center py-4">
                    <CheckCircle2 className="h-16 w-16 mx-auto text-green-500 mb-4" />
                    <h3 className="text-xl font-bold">Import Complete!</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 rounded-lg bg-green-50">
                      <p className="text-3xl font-bold text-green-600">{importResult.created}</p>
                      <p className="text-sm text-muted-foreground">Created</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-blue-50">
                      <p className="text-3xl font-bold text-blue-600">{importResult.updated || 0}</p>
                      <p className="text-sm text-muted-foreground">Updated</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-red-50">
                      <p className="text-3xl font-bold text-red-600">{importResult.errors?.length || 0}</p>
                      <p className="text-sm text-muted-foreground">Errors</p>
                    </div>
                  </div>
                  {importResult.errors?.length > 0 && (
                    <div className="mt-4 p-3 rounded bg-red-50 border border-red-200">
                      <p className="text-sm font-medium text-red-700 mb-2">Errors:</p>
                      <ul className="text-xs text-red-600 space-y-1">
                        {importResult.errors.slice(0, 5).map((err, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                            {err}
                          </li>
                        ))}
                        {importResult.errors.length > 5 && (
                          <li>...and {importResult.errors.length - 5} more errors</li>
                        )}
                      </ul>
                    </div>
                  )}
                  <DialogFooter>
                    <Button onClick={() => { setIsImportOpen(false); resetImport(); }}>
                      Done
                    </Button>
                  </DialogFooter>
                </div>
              )}
            </DialogContent>
          </Dialog>

          {/* Add Customer Button */}
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
              
              {/* Action Buttons */}
              <div className="flex justify-between items-center pt-2">
                {/* Save & Add Job link - only show for new customers */}
                {!editingCustomer && (
                  <button
                    type="button"
                    onClick={(e) => handleSubmit(e, true)}
                    className="text-sm text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1"
                    data-testid="save-and-add-job-btn"
                  >
                    <Briefcase className="h-3.5 w-3.5" />
                    Save & Add Job
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
                {editingCustomer && <div />}
                
                <div className="flex gap-2">
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                  <Button type="submit" data-testid="customer-submit-btn">
                    {editingCustomer ? 'Update' : 'Create'}
                  </Button>
                </div>
              </div>
            </form>
          </DialogContent>
        </Dialog>
        </div>
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
            <>
              {/* Desktop Table View */}
              <div className="hidden md:block overflow-x-auto">
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
                            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                              <span className="text-primary font-bold text-sm">
                                {getInitials(customer.name)}
                              </span>
                            </div>
                            <div className="min-w-0">
                              <p className="font-medium truncate">{customer.name}</p>
                              {customer.company && (
                                <p className="text-xs text-muted-foreground flex items-center gap-1 truncate">
                                  <Building className="h-3 w-3 flex-shrink-0" /> {customer.company}
                                </p>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            {customer.email && (
                              <p className="text-sm flex items-center gap-1 truncate max-w-[200px]">
                                <Mail className="h-3 w-3 text-muted-foreground flex-shrink-0" /> {customer.email}
                              </p>
                            )}
                            {customer.phone && (
                              <p className="text-sm flex items-center gap-1">
                                <Phone className="h-3 w-3 text-muted-foreground flex-shrink-0" /> {customer.phone}
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
              </div>

              {/* Mobile Card View */}
              <div className="md:hidden divide-y divide-border">
                {filteredCustomers.map((customer) => (
                  <div 
                    key={customer.id}
                    className="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
                    onClick={() => handleViewCustomer(customer)}
                    data-testid={`customer-card-${customer.id}`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-primary font-bold text-sm">
                            {getInitials(customer.name)}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="font-medium truncate">{customer.name}</p>
                          {customer.company && (
                            <p className="text-xs text-muted-foreground truncate">{customer.company}</p>
                          )}
                        </div>
                      </div>
                      <Badge className={`${getStatusColor(customer.status)} flex-shrink-0`}>
                        {customer.status}
                      </Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                      {customer.email && (
                        <span className="flex items-center gap-1 truncate max-w-full">
                          <Mail className="h-3 w-3 flex-shrink-0" /> 
                          <span className="truncate">{customer.email}</span>
                        </span>
                      )}
                      {customer.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="h-3 w-3 flex-shrink-0" /> {customer.phone}
                        </span>
                      )}
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">
                        {formatDate(customer.created_at)}
                      </span>
                      <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(customer)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(customer.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
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
