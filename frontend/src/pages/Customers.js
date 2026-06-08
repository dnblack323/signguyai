import { useEffect, useState, useRef, useReducer, useCallback } from 'react';
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
  ArrowRight, Package, Store
} from 'lucide-react';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';
import { useSetPageContext } from '../context/PageContext';
import CustomerBrandingTab from '../components/CustomerBrandingTab';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatPhoneInput = (value) => {
  const digits = value.replace(/\D/g, '').slice(0, 10);
  if (digits.length === 0) return '';
  if (digits.length < 4) return `(${digits}`;
  if (digits.length < 7) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
};

const statusOptions = ['lead', 'active', 'inactive'];
const buildCsvHeader = (label, index) => ({ id: `csv-header-${index}-${label}`, index, label });
const buildCsvPreviewRow = (values, rowNumber) => ({ id: `csv-row-${rowNumber}-${values.join('|')}`, values });

export default function Customers() {
  const navigate = useNavigate();
  const { 
    customers, fetchCustomers, createCustomer, updateCustomer, deleteCustomer,
    jobs, fetchJobs, invoices, fetchInvoices, quotes, fetchQuotes
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  // Phase 6 — webstore-tag chip filter. 'all' = no filter, 'webstore_owner' or
  // 'webstore_customer' = client-side narrow on the customer.tags array.
  const [tagFilter, setTagFilter] = useState('all');
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
  const [invitingPortal, setInvitingPortal] = useState(false);

  // Phase 4 follow-up — webstore connections for the selected customer.
  const [webstoreState, dispatchWebstore] = useReducer(
    (s, a) => {
      switch (a.type) {
        case 'LOADING': return { data: { as_owner: [], as_buyer: [], tags: [] }, loading: true, error: false };
        case 'LOADED':  return { data: a.data, loading: false, error: false };
        case 'ERROR':   return { data: { as_owner: [], as_buyer: [], tags: [] }, loading: false, error: true };
        case 'RESET':   return { data: { as_owner: [], as_buyer: [], tags: [] }, loading: false, error: false };
        default:        return s;
      }
    },
    { data: { as_owner: [], as_buyer: [], tags: [] }, loading: false, error: false },
  );
  // Keep a compat alias so downstream JSX doesn't need to change
  const customerWebstores = webstoreState.data;

  const loadWebstores = useCallback((customerId) => {
    dispatchWebstore({ type: 'LOADING' });
    axios.get(`${API_URL}/api/customers/${customerId}/webstores`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
      .then(res => dispatchWebstore({ type: 'LOADED', data: res.data || { as_owner: [], as_buyer: [], tags: [] } }))
      .catch(() => dispatchWebstore({ type: 'ERROR' }));
  }, []);

  useEffect(() => {
    if (!isDetailOpen || !selectedCustomer?.id) {
      dispatchWebstore({ type: 'RESET' });
      return;
    }
    loadWebstores(selectedCustomer.id);
  }, [isDetailOpen, selectedCustomer?.id, loadWebstores]);

  // Phase 3: declare context so "create an order for this customer" works.
  useSetPageContext(
    selectedCustomer && isDetailOpen
      ? {
          page: 'customer_detail',
          recordType: 'customer',
          recordId: selectedCustomer.id,
          recordLabel: selectedCustomer.company || selectedCustomer.name,
        }
      : { page: 'customers_list' },
  );

  // CSV Import state — check for ?import=true URL param on mount
  const [isImportOpen, setIsImportOpen] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('import') === 'true') {
      window.history.replaceState({}, document.title, window.location.pathname);
      return true;
    }
    return false;
  });
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
    { value: 'name', label: 'Name', required: false },
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
  }, []);

  const [loadError, setLoadError] = useState(false);

  const loadCustomers = async () => {
    setLoading(true);
    setLoadError(false);
    const params = {};
    if (statusFilter !== 'all') params.status = statusFilter;
    if (search) params.search = search;
    try {
      await fetchCustomers(params);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleViewCustomer = (customer) => {
    setSelectedCustomer(structuredClone(customer));
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

    // Job status enum value is "completed" (see backend/models/enums.py
    // JobStatus.COMPLETED). The previous filter used the production task
    // value "complete" which never matched any real job — so the
    // "Completed Jobs" stat was always 0 and the "Active Jobs" list
    // double-counted finished work.
    const activeJobs = customerJobs.filter(j => !['completed', 'archived'].includes(j.status));
    const completedJobs = customerJobs.filter(j => j.status === 'completed');
    const totalRevenue = customerInvoices.reduce((sum, i) => sum + (i.total || 0), 0);
    const outstandingBalance = customerInvoices
      .filter(i => i.status !== 'paid')
      .reduce((sum, i) => sum + ((i.total || 0) - (i.amount_paid || 0)), 0);
    
    return { activeJobs, completedJobs, totalRevenue, outstandingBalance, customerJobs, customerInvoices };
  };

  const handleSubmit = async (e, addJobAfter = false) => {
    e.preventDefault();
    if (!formData.name.trim() && !formData.company.trim()) {
      toast.error('Name or Company is required');
      return;
    }
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
          navigate(`/orders/new?customer_id=${newCustomer.id}&customer_name=${encodeURIComponent(newCustomer.name || newCustomer.company)}`);
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

  const handleInviteToPortal = async (customer) => {
    if (!customer?.email) {
      toast.error('Add an email address before inviting this customer to the portal');
      return;
    }
    setInvitingPortal(true);
    try {
      const token = getAuthToken();
      const res = await axios.post(`${API_URL}/api/customers/${customer.id}/invite-portal`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Portal invited. Temporary PIN: ${res.data.temporary_pin}`);
      await loadCustomers();
      const refreshed = await axios.get(`${API_URL}/api/customers/${customer.id}`, { headers: { Authorization: `Bearer ${token}` } });
      setSelectedCustomer(refreshed.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to invite customer to portal');
    }
    setInvitingPortal(false);
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
      const headers = parseCSVLine(lines[0]).map((header, index) => buildCsvHeader(header, index));
      setCsvHeaders(headers);
      
      // Auto-map columns based on header names
      const autoMapping = {};
      headers.forEach((header) => {
        const normalizedHeader = header.label.toLowerCase().trim();
        if (normalizedHeader.includes('name') && !normalizedHeader.includes('company')) {
          autoMapping[header.id] = 'name';
        } else if (normalizedHeader.includes('company') || normalizedHeader.includes('business')) {
          autoMapping[header.id] = 'company';
        } else if (normalizedHeader.includes('email')) {
          autoMapping[header.id] = 'email';
        } else if (normalizedHeader.includes('phone') || normalizedHeader.includes('tel')) {
          autoMapping[header.id] = 'phone';
        } else if (normalizedHeader.includes('status')) {
          autoMapping[header.id] = 'status';
        } else if (normalizedHeader.includes('note')) {
          autoMapping[header.id] = 'notes';
        }
      });
      setColumnMapping(autoMapping);
      
      // Parse data rows (preview first 5)
      const preview = [];
      for (let i = 1; i < Math.min(lines.length, 6); i++) {
        const values = parseCSVLine(lines[i]);
        preview.push(buildCsvPreviewRow(values, i));
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
          
          csvHeaders.forEach((header) => {
            const field = columnMapping[header.id];
            if (field && values[header.index]) {
              let value = values[header.index].replace(/^["']|["']$/g, '').trim();
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
        const token = getAuthToken();
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

  // Phase 6 — apply optional tag filter on top of whatever the backend
  // already filtered (status/search). 'all' is a no-op.
  const filteredCustomers = tagFilter === 'all'
    ? customers
    : customers.filter((c) => Array.isArray(c.tags) && c.tags.includes(tagFilter));

  return (
    <div className="space-y-6 animate-fade-in" data-testid="customers-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight text-gray-900">Customers</h1>
          <p className="text-gray-700 mt-1">{customers.length} total customers</p>
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
                    <Upload className="h-12 w-12 mx-auto mb-4 text-gray-500" />
                    <p className="text-lg font-medium">Click to upload CSV file</p>
                    <p className="text-sm text-gray-500 mt-1">or drag and drop</p>
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
                    <p className="text-sm text-gray-500">
                      Map your CSV columns to customer fields
                    </p>
                    <Badge variant="outline">{csvFile?.name}</Badge>
                  </div>
                  <div className="space-y-3 max-h-[300px] overflow-y-auto">
                    {csvHeaders.map((header) => (
                      <div key={header.id} className="flex items-center gap-3 p-2 rounded bg-gray-50/50">
                        <div className="w-1/3 font-medium truncate text-sm">{header.label}</div>
                        <span className="text-gray-500">→</span>
                        <Select
                          value={columnMapping[header.id] || ''}
                          onValueChange={(val) => setColumnMapping({ ...columnMapping, [header.id]: val })}
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
                            {csvHeaders.map((header) => (
                              <TableHead key={header.id} className="text-xs">
                                {columnMapping[header.id] ? (
                                  <Badge variant="default" className="text-xs">{columnMapping[header.id]}</Badge>
                                ) : (
                                  <span className="text-gray-500">-</span>
                                )}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {csvPreview.map((row) => (
                            <TableRow key={row.id}>
                              {row.values.map((cell, cellIndex) => (
                                <TableCell key={`${row.id}-${csvHeaders[cellIndex]?.id || cellIndex}-${cell}`} className="text-xs py-1 truncate max-w-[100px]">
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
                      <p className="text-sm text-gray-500">Created</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-blue-50">
                      <p className="text-3xl font-bold text-blue-600">{importResult.updated || 0}</p>
                      <p className="text-sm text-gray-500">Updated</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-red-50">
                      <p className="text-3xl font-bold text-red-600">{importResult.errors?.length || 0}</p>
                      <p className="text-sm text-gray-500">Errors</p>
                    </div>
                  </div>
                  {importResult.errors?.length > 0 && (
                    <div className="mt-4 p-3 rounded bg-red-50 border border-red-200">
                      <p className="text-sm font-medium text-red-700 mb-2">Errors:</p>
                      <ul className="text-xs text-red-600 space-y-1">
                        {importResult.errors.slice(0, 5).map((err) => (
                          <li key={err} className="flex items-start gap-2">
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
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      data-testid="customer-name-input"
                    />
                    <p className="text-xs text-gray-500">Name or Company is required.</p>
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
                    onChange={(e) => setFormData({ ...formData, phone: formatPhoneInput(e.target.value) })}
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
                {/* Save & Add Order link - only show for new customers */}
                {!editingCustomer && (
                  <button
                    type="button"
                    onClick={(e) => handleSubmit(e, true)}
                    className="text-sm text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1"
                    data-testid="save-and-add-job-btn"
                  >
                    <Briefcase className="h-3.5 w-3.5" />
                    Save & Add Order
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
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
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
          {/* Phase 6 — webstore-tag filter chips */}
          <div className="flex flex-wrap gap-2 mt-3" data-testid="customer-tag-filters">
            {[
              { v: 'all',                label: 'All customers' },
              { v: 'webstore_owner',     label: 'Webstore owners' },
              { v: 'webstore_customer',  label: 'Webstore buyers' },
            ].map((c) => (
              <button
                key={c.v}
                type="button"
                onClick={() => setTagFilter(c.v)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  tagFilter === c.v
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                }`}
                data-testid={`customer-tag-chip-${c.v}`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          ) : loadError ? (
            <div className="flex flex-col items-center justify-center h-32 gap-2" data-testid="customers-load-error">
              <p className="text-sm text-gray-500">Failed to load customers.</p>
              <Button size="sm" variant="outline" onClick={loadCustomers} data-testid="customers-retry-btn">Retry</Button>
            </div>
          ) : filteredCustomers.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
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
                        className={`cursor-pointer transition-colors ${idx % 2 === 0 ? 'bg-transparent' : 'bg-gray-50'} hover:bg-gray-50/50`}
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
                                <p className="text-xs text-gray-500 flex items-center gap-1 truncate">
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
                                <Mail className="h-3 w-3 text-gray-500 flex-shrink-0" /> {customer.email}
                              </p>
                            )}
                            {customer.phone && (
                              <p className="text-sm flex items-center gap-1">
                                <Phone className="h-3 w-3 text-gray-500 flex-shrink-0" /> {customer.phone}
                              </p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(customer.status)}>
                            {customer.status}
                          </Badge>
                          {/* Phase 6 — webstore tag chips inline on the row */}
                          {Array.isArray(customer.tags) && customer.tags.length > 0 && (
                            <div className="mt-1 flex flex-wrap gap-1" data-testid={`customer-tags-${customer.id}`}>
                              {customer.tags
                                .filter((t) => t === 'webstore_owner' || t === 'webstore_customer')
                                .map((t) => (
                                  <span
                                    key={t}
                                    className="inline-block text-[10px] px-1.5 py-0.5 rounded border bg-blue-50 text-blue-700 border-blue-200"
                                  >
                                    {t === 'webstore_owner' ? 'Webstore Owner' : 'Webstore Buyer'}
                                  </span>
                                ))}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-gray-500 text-sm">
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
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
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
                            <p className="text-xs text-gray-500 truncate">{customer.company}</p>
                          )}
                        </div>
                      </div>
                      <Badge className={`${getStatusColor(customer.status)} flex-shrink-0`}>
                        {customer.status}
                      </Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
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
                      <span className="text-xs text-gray-500">
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
                        <p className="text-gray-500 flex items-center gap-1">
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
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <Briefcase className="h-5 w-5 mx-auto mb-1 text-blue-400" />
                    <p className="text-lg font-bold">{stats.activeJobs.length}</p>
                    <p className="text-xs text-gray-500">Active Orders</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <Clock className="h-5 w-5 mx-auto mb-1 text-green-400" />
                    <p className="text-lg font-bold">{stats.completedJobs.length}</p>
                    <p className="text-xs text-gray-500">Completed</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <DollarSign className="h-5 w-5 mx-auto mb-1 text-primary" />
                    <p className="text-lg font-bold">{formatCurrency(stats.totalRevenue)}</p>
                    <p className="text-xs text-gray-500">Total Revenue</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg text-center">
                    <Receipt className="h-5 w-5 mx-auto mb-1 text-yellow-400" />
                    <p className="text-lg font-bold">{formatCurrency(stats.outstandingBalance)}</p>
                    <p className="text-xs text-gray-500">Outstanding</p>
                  </div>
                </div>

                <Tabs value={detailTab} onValueChange={setDetailTab}>
                  <TabsList className="grid grid-cols-5 w-full">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="jobs">Orders ({stats.customerJobs.length})</TabsTrigger>
                    <TabsTrigger value="invoices">Invoices ({stats.customerInvoices.length})</TabsTrigger>
                    <TabsTrigger value="quotes">Quotes ({customerQuotes.length})</TabsTrigger>
                    <TabsTrigger value="branding" data-testid="customer-branding-tab-trigger">Branding</TabsTrigger>
                  </TabsList>

                  {/* Overview Tab */}
                  <TabsContent value="overview" className="space-y-4 mt-4">
                    {/* Contact Info */}
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <User className="h-4 w-4" /> Contact Information
                      </h4>
                      <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                        <div>
                          <p className="text-xs text-gray-500">Email</p>
                          <p className="font-medium flex items-center gap-2">
                            <Mail className="h-4 w-4 text-gray-500" />
                            {selectedCustomer.email || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Phone</p>
                          <p className="font-medium flex items-center gap-2">
                            <Phone className="h-4 w-4 text-gray-500" />
                            {selectedCustomer.phone || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Company</p>
                          <p className="font-medium flex items-center gap-2">
                            <Building className="h-4 w-4 text-gray-500" />
                            {selectedCustomer.company || 'Not provided'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Customer Since</p>
                          <p className="font-medium flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-gray-500" />
                            {formatDate(selectedCustomer.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <Eye className="h-4 w-4" /> Customer Portal
                      </h4>
                      <div className="p-4 bg-gray-50 rounded-lg flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                          <p className="text-xs text-gray-500">Portal Status</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={selectedCustomer.portal_enabled ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'}>
                              {selectedCustomer.portal_enabled ? 'Invited / Enabled' : 'Not Invited'}
                            </Badge>
                            <p className="text-sm text-gray-500">
                              Customer must exist in the database before they can log in to the portal.
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          onClick={() => handleInviteToPortal(selectedCustomer)}
                          disabled={invitingPortal || !selectedCustomer.email}
                          data-testid="invite-customer-to-portal-btn"
                        >
                          {invitingPortal ? 'Inviting...' : 'Invite to Portal'}
                        </Button>
                      </div>
                    </div>

                    {/* Notes */}
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <FileText className="h-4 w-4" /> Notes
                      </h4>
                      <div className="p-4 bg-gray-50 rounded-lg min-h-[80px]">
                        {selectedCustomer.notes ? (
                          <p className="whitespace-pre-wrap">{selectedCustomer.notes}</p>
                        ) : (
                          <p className="text-gray-500 italic">No notes added</p>
                        )}
                      </div>
                    </div>

                    {/* Recent Activity */}
                    {stats.activeJobs.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-3 flex items-center gap-2">
                          <Briefcase className="h-4 w-4" /> Active Orders
                        </h4>
                        <div className="space-y-2">
                          {stats.activeJobs.slice(0, 3).map(job => (
                            <Link key={job.id} to={`/productivity/legacy-jobs/${job.id}`} onClick={() => setIsDetailOpen(false)}>
                              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-50/50 transition-colors">
                                <div>
                                  <p className="font-medium">{job.name}</p>
                                  <p className="text-xs text-gray-500">Due: {formatDate(job.due_date)}</p>
                                </div>
                                <Badge className={getStatusColor(job.status)}>{job.status.replace('_', ' ')}</Badge>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Phase 4 follow-up — Webstore connections panel.
                        Surfaces every store this customer owns or has shopped
                        on, so a sales rep can jump from a customer record
                        straight to the right store. Only renders when there
                        is at least one connection. */}
                    {((customerWebstores.as_owner?.length || 0) + (customerWebstores.as_buyer?.length || 0)) > 0 && (
                      <div data-testid="customer-webstores-panel">
                        <h4 className="font-medium mb-3 flex items-center gap-2">
                          <Store className="h-4 w-4 text-blue-500" /> Webstore Connections
                          {(customerWebstores.tags || []).length > 0 && (
                            <span className="ml-2 flex gap-1">
                              {(customerWebstores.tags || []).map((t) => (
                                <Badge key={t} variant="outline" className="text-[10px] bg-blue-50 text-blue-700 border-blue-200">
                                  {t.replace('_', ' ')}
                                </Badge>
                              ))}
                            </span>
                          )}
                        </h4>
                        <div className="space-y-2">
                          {(customerWebstores.as_owner || []).map((s) => (
                            <Link
                              key={`owner-${s.id}`}
                              to={`/webstores`}
                              onClick={() => setIsDetailOpen(false)}
                              className="block"
                              data-testid={`webstore-owner-${s.id}`}
                            >
                              <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-100 rounded-lg hover:bg-blue-100/60 transition-colors">
                                <div>
                                  <p className="font-medium text-gray-900">{s.name}</p>
                                  <p className="text-xs text-gray-500">
                                    Owner · {s.store_type || '—'} · {s.order_count || 0} orders · {formatCurrency(s.gross_sales || 0)} gross
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">Owed</p>
                                  <p className={`text-sm font-semibold ${(s.payout_owed || 0) > 0 ? 'text-amber-600' : 'text-gray-700'}`}>
                                    {formatCurrency(s.payout_owed || 0)}
                                  </p>
                                </div>
                              </div>
                            </Link>
                          ))}
                          {(customerWebstores.as_buyer || []).map((s) => (
                            <Link
                              key={`buyer-${s.id}`}
                              to={`/orders?webstore_id=${s.id}`}
                              onClick={() => setIsDetailOpen(false)}
                              className="block"
                              data-testid={`webstore-buyer-${s.id}`}
                            >
                              <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-100 rounded-lg hover:bg-gray-100 transition-colors">
                                <div>
                                  <p className="font-medium text-gray-900">{s.name}</p>
                                  <p className="text-xs text-gray-500">
                                    Buyer · {s.store_type || '—'} · {s.order_count} orders
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-xs text-gray-500">Spent</p>
                                  <p className="text-sm font-semibold text-gray-900">
                                    {formatCurrency(s.gross_sales || 0)}
                                  </p>
                                </div>
                              </div>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  {/* Orders Tab */}
                  <TabsContent value="jobs" className="mt-4">
                    {stats.customerJobs.length === 0 ? (
                      <div className="text-center py-8 text-gray-500">
                        <Briefcase className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No jobs for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {stats.customerJobs.map(job => (
                          <Link key={job.id} to={`/productivity/legacy-jobs/${job.id}`} onClick={() => setIsDetailOpen(false)}>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-50/50 transition-colors">
                              <div className="flex-1">
                                <p className="font-medium">{job.name}</p>
                                <p className="text-xs text-gray-500">
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
                      <div className="text-center py-8 text-gray-500">
                        <Receipt className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No invoices for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {stats.customerInvoices.map(invoice => (
                          <div key={invoice.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <p className="font-medium font-mono">#{invoice.id.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-gray-500">
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
                      <div className="text-center py-8 text-gray-500">
                        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No quotes for this customer</p>
                      </div>
                    ) : (
                      <div className="space-y-2 max-h-[300px] overflow-y-auto">
                        {customerQuotes.map(quote => (
                          <div key={quote.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex-1">
                              <p className="font-medium font-mono">#{quote.id.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-gray-500">
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

                  {/* Branding Tab */}
                  <TabsContent value="branding" className="mt-4">
                    <CustomerBrandingTab customerId={selectedCustomer.id} />
                  </TabsContent>
                </Tabs>

                {/* Actions */}
                <Separator className="my-4" />
                <div className="flex justify-between">
                  <Button variant="outline" onClick={() => { setIsDetailOpen(false); handleEdit(selectedCustomer); }}>
                    <Edit2 className="h-4 w-4 mr-2" /> Edit Customer
                  </Button>
                  <div className="flex gap-2">
                    <Button className="bg-violet-600 hover:bg-violet-700 text-white" onClick={() => { setIsDetailOpen(false); navigate(`/orders/new?customer_id=${selectedCustomer.id}&customer_name=${encodeURIComponent(selectedCustomer.name || '')}&company=${encodeURIComponent(selectedCustomer.company || '')}&email=${encodeURIComponent(selectedCustomer.email || '')}&phone=${encodeURIComponent(selectedCustomer.phone || '')}`); }} data-testid="customer-popup-new-order-btn">
                      <Package className="h-4 w-4 mr-2" /> New Order
                    </Button>
                    <Button variant="outline" onClick={() => { setIsDetailOpen(false); navigate(`/quotes?customer_id=${selectedCustomer.id}`); }} data-testid="customer-popup-view-quotes-btn">
                      <Briefcase className="h-4 w-4 mr-2" /> View Quotes
                    </Button>
                    <Button variant="outline" onClick={() => setIsDetailOpen(false)}>
                      Close
                    </Button>
                  </div>
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>
    </div>
  );
}
