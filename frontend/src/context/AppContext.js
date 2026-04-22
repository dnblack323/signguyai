import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';
import { useAuth } from './AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API,
});

// Add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
};

export const AppProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchTenantLogo = useCallback(async () => {
    try {
      const res = await api.get('/tenant/logo');
      return res.data?.logo_url || null;
    } catch (err) {
      console.error('Error fetching tenant logo:', err);
      return null;
    }
  }, []);

  const hydrateTenantBranding = useCallback(async (tenantData) => {
    if (!tenantData) return null;
    if (!tenantData.has_logo) {
      return { ...tenantData, logo_url: null };
    }
    const logoUrl = await fetchTenantLogo();
    return { ...tenantData, logo_url: logoUrl };
  }, [fetchTenantLogo]);

  // Customers
  const fetchCustomers = useCallback(async (params = {}) => {
    try {
      const res = await api.get(`/customers`, { params });
      setCustomers(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching customers:', err);
      return [];
    }
  }, []);

  const createCustomer = async (data) => {
    const res = await api.post(`/customers`, data);
    await fetchCustomers();
    return res.data;
  };

  const updateCustomer = async (id, data) => {
    const res = await api.put(`/customers/${id}`, data);
    await fetchCustomers();
    return res.data;
  };

  const deleteCustomer = async (id) => {
    await api.delete(`/customers/${id}`);
    await fetchCustomers();
  };

  // Quotes
  const fetchQuotes = useCallback(async (params = {}) => {
    try {
      const res = await api.get(`/quotes`, { params });
      setQuotes(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching quotes:', err);
      return [];
    }
  }, []);

  const createQuote = async (data) => {
    const res = await api.post(`/quotes`, data);
    await fetchQuotes();
    return res.data;
  };

  const updateQuote = async (id, data) => {
    const res = await api.put(`/quotes/${id}`, data);
    await fetchQuotes();
    return res.data;
  };

  const convertQuoteToJob = async (quoteId) => {
    const res = await api.post(`/quotes/${quoteId}/convert-to-job`);
    await fetchQuotes();
    await fetchJobs();
    return res.data;
  };

  // Jobs
  const fetchJobs = async (params = {}) => {
    try {
      const res = await api.get(`/jobs`, { params });
      setJobs(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching jobs:', err);
      return [];
    }
  };

  const createJob = async (data) => {
    const res = await api.post(`/jobs`, data);
    await fetchJobs();
    return res.data;
  };

  const updateJob = async (id, data) => {
    const res = await api.put(`/jobs/${id}`, data);
    await fetchJobs();
    return res.data;
  };

  const deleteJob = async (id) => {
    await api.delete(`/jobs/${id}`);
    await fetchJobs();
  };

  // Job Details
  const getJobDetails = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/details`);
    return res.data;
  };

  const archiveJob = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/archive`);
    await fetchJobs();
    return res.data;
  };

  const unarchiveJob = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/unarchive`);
    await fetchJobs();
    return res.data;
  };

  const approveJob = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/approve`);
    await fetchJobs();
    return res.data;
  };

  const sendJobQuote = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/send`);
    await fetchJobs();
    return res.data;
  };

  const completeJob = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/complete`);
    await fetchJobs();
    return res.data;
  };

  // Job Notes
  const createJobNote = async (jobId, data) => {
    const res = await api.post(`/jobs/${jobId}/notes`, data);
    return res.data;
  };

  const getJobNotes = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/notes`);
    return res.data;
  };

  const deleteJobNote = async (noteId) => {
    await api.delete(`/job-notes/${noteId}`);
  };

  // Job Activities
  const getJobActivities = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/activities`);
    return res.data;
  };

  // Job Items
  const fetchJobItems = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/items`);
    return res.data;
  };

  const createJobItem = async (jobId, data) => {
    const res = await api.post(`/jobs/${jobId}/items`, data);
    return res.data;
  };

  const updateJobItem = async (itemId, data) => {
    const res = await api.put(`/job-items/${itemId}`, data);
    return res.data;
  };

  const deleteJobItem = async (itemId) => {
    await api.delete(`/job-items/${itemId}`);
  };

  // Invoices
  const fetchInvoices = useCallback(async (params = {}) => {
    try {
      const res = await api.get(`/invoices`, { params });
      setInvoices(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching invoices:', err);
      return [];
    }
  }, []);

  const createInvoice = async (data) => {
    const res = await api.post(`/invoices`, data);
    await fetchInvoices();
    return res.data;
  };

  const createInvoiceFromJob = async (jobId) => {
    const res = await api.post(`/invoices/from-job/${jobId}`);
    await fetchInvoices();
    await fetchJobs();
    return res.data;
  };

  const updateInvoice = async (id, data) => {
    const res = await api.put(`/invoices/${id}`, data);
    await fetchInvoices();
    return res.data;
  };

  const getInvoiceById = async (invoiceId) => {
    const res = await api.get(`/invoices/${invoiceId}`);
    return res.data;
  };

  // Employees
  const fetchEmployees = async (params = {}) => {
    try {
      const res = await api.get(`/employees`, { params });
      setEmployees(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching employees:', err);
      return [];
    }
  };

  const createEmployee = async (data) => {
    const res = await api.post(`/employees`, data);
    await fetchEmployees();
    return res.data;
  };

  const updateEmployee = async (id, data) => {
    const res = await api.put(`/employees/${id}`, data);
    await fetchEmployees();
    return res.data;
  };

  // Tasks
  const fetchTasks = async (params = {}) => {
    try {
      const res = await api.get(`/tasks`, { params });
      setTasks(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching tasks:', err);
      return [];
    }
  };

  const createTask = async (data) => {
    const res = await api.post(`/tasks`, data);
    // Immediately update local state with the new task to ensure UI reflects the change
    setTasks(prev => [res.data, ...prev]);
    return res.data;
  };

  const updateTask = async (id, data) => {
    const res = await api.put(`/tasks/${id}`, data);
    // Immediately update local state to ensure UI reflects the change
    setTasks(prev => prev.map(t => t.id === id ? res.data : t));
    return res.data;
  };

  const deleteTask = async (id) => {
    await api.delete(`/tasks/${id}`);
    // Immediately update local state to ensure UI reflects the change
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  // Dashboard
  const fetchDashboardStats = async () => {
    try {
      const res = await api.get(`/dashboard/stats`);
      setDashboardStats(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      return null;
    }
  };

  // AI Tools
  const generateAIContent = async (tool, inputData) => {
    const res = await api.post(`/ai/generate`, { tool, input_data: inputData });
    return res.data;
  };

  const generateAIImages = async (tool, inputData, count = 3) => {
    const res = await api.post(`/ai/generate-images`, { tool, input_data: inputData, image_count: count });
    return res.data;
  };

  const fetchAIHistory = async (params = {}) => {
    const res = await api.get(`/ai/history`, { params });
    return res.data;
  };

  // Time Clock
  const clockAction = async (employeeId, action) => {
    const res = await api.post(`/timeclock`, { employee_id: employeeId, action });
    return res.data;
  };

  const getClockStatus = async (employeeId) => {
    const res = await api.get(`/timeclock/${employeeId}/status`);
    return res.data;
  };

  const getTodayLogs = async (employeeId) => {
    const res = await api.get(`/timeclock/${employeeId}/today`);
    return res.data;
  };

  const getShiftSummary = async (employeeId, date) => {
    const localDate = date || new Date().toISOString().slice(0, 10);
    const res = await api.get(`/timeclock/${employeeId}/summary`, { params: { date: localDate } });
    return res.data;
  };

  // Payroll
  const createPayrollTransaction = async (data) => {
    const res = await api.post(`/payroll/transactions`, data);
    return res.data;
  };

  const getPayrollTransactions = async (params = {}) => {
    const res = await api.get(`/payroll/transactions`, { params });
    return res.data;
  };

  const getPayrollBalance = async (employeeId) => {
    const res = await api.get(`/payroll/balance/${employeeId}`);
    return res.data;
  };

  const getPayrollReport = async (startDate, endDate) => {
    const res = await api.get(`/payroll/report`, { params: { start_date: startDate, end_date: endDate } });
    return res.data;
  };

  // Job Time Tracking
  const startJobTimer = async (jobId, data = {}) => {
    const res = await api.post(`/jobs/${jobId}/time/start`, data);
    return res.data;
  };

  const stopJobTimer = async (jobId) => {
    const res = await api.post(`/jobs/${jobId}/time/stop`);
    return res.data;
  };

  const getJobTimeEntries = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/time`);
    return res.data;
  };

  const getJobTimeSummary = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/time/summary`);
    return res.data;
  };

  const getJobActiveTimer = async (jobId) => {
    const res = await api.get(`/jobs/${jobId}/time/active`);
    return res.data;
  };

  const deleteJobTimeEntry = async (jobId, entryId) => {
    const res = await api.delete(`/jobs/${jobId}/time/${entryId}`);
    return res.data;
  };

  // Financials
  const createSalesEntry = async (data) => {
    const res = await api.post(`/financials/sales`, data);
    return res.data;
  };

  const getSalesEntries = async (params = {}) => {
    const res = await api.get(`/financials/sales`, { params });
    return res.data;
  };

  const createExpenseEntry = async (data) => {
    const res = await api.post(`/financials/expenses`, data);
    return res.data;
  };

  const getExpenseEntries = async (params = {}) => {
    const res = await api.get(`/financials/expenses`, { params });
    return res.data;
  };

  const getFinancialSummary = async (startDate, endDate) => {
    const res = await api.get(`/financials/summary`, { params: { start_date: startDate, end_date: endDate } });
    return res.data;
  };

  // Webstores (Legacy - keeping for compatibility)
  const createFundraiser = async (data) => {
    const res = await api.post(`/webstores/fundraiser`, data);
    return res.data;
  };

  const getFundraisers = async (params = {}) => {
    const res = await api.get(`/webstores/fundraiser`, { params });
    return res.data;
  };

  const createB2BStore = async (data) => {
    const res = await api.post(`/webstores/b2b`, data);
    return res.data;
  };

  const getB2BStores = async (params = {}) => {
    const res = await api.get(`/webstores/b2b`, { params });
    return res.data;
  };

  const createWebstoreOrder = async (data) => {
    const res = await api.post(`/webstores/orders`, data);
    return res.data;
  };

  const getWebstoreOrders = async (params = {}) => {
    const res = await api.get(`/webstores/orders`, { params });
    return res.data;
  };

  // ============== NEW WEBSTORE SYSTEM ==============
  
  // Products (Master Catalog)
  const createProduct = async (data) => {
    const res = await api.post(`/products`, data);
    return res.data;
  };

  const getProducts = async (params = {}) => {
    const res = await api.get(`/products`, { params });
    return res.data;
  };

  const getProduct = async (productId) => {
    const res = await api.get(`/products/${productId}`);
    return res.data;
  };

  const updateProduct = async (productId, data) => {
    const res = await api.put(`/products/${productId}`, data);
    return res.data;
  };

  const deleteProduct = async (productId) => {
    const res = await api.delete(`/products/${productId}`);
    return res.data;
  };

  // Webstores V2
  const createWebstore = async (data) => {
    const res = await api.post(`/webstores/v2`, data);
    return res.data;
  };

  const getWebstores = async (params = {}) => {
    const res = await api.get(`/webstores/v2`, { params });
    return res.data;
  };

  const getWebstore = async (webstoreId) => {
    const res = await api.get(`/webstores/v2/${webstoreId}`);
    return res.data;
  };

  const updateWebstore = async (webstoreId, data) => {
    const res = await api.put(`/webstores/v2/${webstoreId}`, data);
    return res.data;
  };

  const deleteWebstore = async (webstoreId) => {
    const res = await api.delete(`/webstores/v2/${webstoreId}`);
    return res.data;
  };

  // Webstore Products
  const assignProductToWebstore = async (webstoreId, data) => {
    const res = await api.post(`/webstores/v2/${webstoreId}/products`, data);
    return res.data;
  };

  const getWebstoreProducts = async (webstoreId, includeDisabled = false) => {
    const res = await api.get(`/webstores/v2/${webstoreId}/products`, { 
      params: { include_disabled: includeDisabled } 
    });
    return res.data;
  };

  const removeProductFromWebstore = async (webstoreId, productId) => {
    const res = await api.delete(`/webstores/v2/${webstoreId}/products/${productId}`);
    return res.data;
  };

  const updateWebstoreProductStatus = async (webstoreId, productId, isEnabled) => {
    const res = await api.put(
      `/webstores/v2/${webstoreId}/products/${productId}`,
      { is_enabled: isEnabled }
    );
    return res.data;
  };

  // Webstore Orders V2
  const createWebstoreOrderV2 = async (data) => {
    const res = await api.post(`/webstores/v2/orders`, data);
    return res.data;
  };

  const getWebstoreOrdersV2 = async (params = {}) => {
    const res = await api.get(`/webstores/v2/orders`, { params });
    return res.data;
  };

  const getWebstoreOrderV2 = async (orderId) => {
    const res = await api.get(`/webstores/v2/orders/${orderId}`);
    return res.data;
  };

  const updateOrderStatus = async (orderId, status, jobId = null) => {
    const body = { status };
    if (jobId !== null && jobId !== undefined) body.job_id = jobId;
    const res = await api.put(`/webstores/v2/orders/${orderId}/status`, body);
    return res.data;
  };

  const createJobFromOrder = async (orderId) => {
    const res = await api.post(`/webstores/v2/orders/${orderId}/create-job`);
    return res.data;
  };

  // Payouts
  const recordPayout = async (webstoreId, amount, notes = null) => {
    const body = { amount };
    if (notes) body.notes = notes;
    const res = await api.post(`/webstores/v2/${webstoreId}/record-payout`, body);
    return res.data;
  };

  const getWebstorePayouts = async (webstoreId) => {
    const res = await api.get(`/webstores/v2/${webstoreId}/payouts`);
    return res.data;
  };

  // Webstore Logo Upload
  const uploadWebstoreLogo = async (webstoreId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post(`/webstores/v2/${webstoreId}/upload-logo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  };

  // Webstore Banner Upload
  const uploadWebstoreBanner = async (webstoreId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post(`/webstores/v2/${webstoreId}/upload-banner`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  };

  // Webstore Analytics
  const getWebstoreAnalytics = async (webstoreId) => {
    const res = await api.get(`/webstores/v2/${webstoreId}/analytics`);
    return res.data;
  };

  // Tenant / Company Settings
  const fetchTenant = useCallback(async () => {
    try {
      const res = await api.get(`/tenant`);
      const hydratedTenant = await hydrateTenantBranding(res.data);
      setTenant(hydratedTenant);
      return hydratedTenant;
    } catch (err) {
      console.error('Error fetching tenant:', err);
      return null;
    }
  }, [hydrateTenantBranding]);

  const getTenant = useCallback(async () => {
    const res = await api.get(`/tenant`);
    const hydratedTenant = await hydrateTenantBranding(res.data);
    setTenant(hydratedTenant);
    return hydratedTenant;
  }, [hydrateTenantBranding]);

  const updateTenant = useCallback(async (data) => {
    const res = await api.put(`/tenant`, data);
    const hydratedTenant = await hydrateTenantBranding(res.data);
    setTenant(hydratedTenant);
    return hydratedTenant;
  }, [hydrateTenantBranding]);

  useEffect(() => {
    if (!isAuthenticated || !user?.tenant_id) {
      setTenant(null);
      return;
    }
    fetchTenant();
  }, [fetchTenant, isAuthenticated, user?.tenant_id]);

  // Stripe Connect
  const getStripeConnectStatus = async () => {
    const res = await api.get(`/stripe-connect/status`);
    return res.data;
  };

  const createStripeConnectAccount = async () => {
    const res = await api.post(`/stripe-connect/create-account`);
    return res.data;
  };

  const value = {
    // Raw API instance for custom calls
    api,
    // State
    customers, quotes, jobs, invoices, employees, tasks, dashboardStats, tenant, loading,
    setLoading,
    // Customer actions
    fetchCustomers, createCustomer, updateCustomer, deleteCustomer,
    // Quote actions
    fetchQuotes, createQuote, updateQuote, convertQuoteToJob,
    // Job actions
    fetchJobs, createJob, updateJob, deleteJob,
    getJobDetails, archiveJob, unarchiveJob, approveJob, sendJobQuote, completeJob,
    // Job Notes & Activities
    createJobNote, getJobNotes, deleteJobNote, getJobActivities,
    // Job Item actions
    fetchJobItems, createJobItem, updateJobItem, deleteJobItem,
    // Invoice actions
    fetchInvoices, createInvoice, createInvoiceFromJob, updateInvoice, getInvoiceById,
    // Employee actions
    fetchEmployees, createEmployee, updateEmployee,
    // Task actions
    fetchTasks, createTask, updateTask, deleteTask,
    // Dashboard
    fetchDashboardStats,
    // AI
    generateAIContent, generateAIImages, fetchAIHistory,
    // Time Clock
    clockAction, getClockStatus, getTodayLogs, getShiftSummary,
    // Job Time Tracking
    startJobTimer, stopJobTimer, getJobTimeEntries, getJobTimeSummary, getJobActiveTimer, deleteJobTimeEntry,
    // Payroll
    createPayrollTransaction, getPayrollTransactions, getPayrollBalance, getPayrollReport,
    // Financials
    createSalesEntry, getSalesEntries, createExpenseEntry, getExpenseEntries, getFinancialSummary,
    // Webstores (Legacy)
    createFundraiser, getFundraisers, createB2BStore, getB2BStores, createWebstoreOrder, getWebstoreOrders,
    // Products (Master Catalog)
    createProduct, getProducts, getProduct, updateProduct, deleteProduct,
    // Webstores V2
    createWebstore, getWebstores, getWebstore, updateWebstore, deleteWebstore,
    // Webstore Products
    assignProductToWebstore, getWebstoreProducts, removeProductFromWebstore, updateWebstoreProductStatus,
    // Webstore Orders V2
    createWebstoreOrderV2, getWebstoreOrdersV2, getWebstoreOrderV2, updateOrderStatus, createJobFromOrder,
    // Payouts
    recordPayout, getWebstorePayouts,
    // Webstore Logo & Banner Upload
    uploadWebstoreLogo, uploadWebstoreBanner,
    // Webstore Analytics
    getWebstoreAnalytics,
    // Tenant / Company Settings
    tenant, fetchTenant, getTenant, updateTenant,
    // Stripe Connect
    getStripeConnectStatus, createStripeConnectAccount
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContext;
