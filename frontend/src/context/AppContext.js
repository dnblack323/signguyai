import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API,
});

// Add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
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
  const [customers, setCustomers] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Customers
  const fetchCustomers = async (params = {}) => {
    try {
      const res = await axiosInstanceInstance.get(`/customers`, { params });
      setCustomers(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching customers:', err);
      return [];
    }
  };

  const createCustomer = async (data) => {
    const res = await axiosInstance.post(`${API}/customers`, data);
    await fetchCustomers();
    return res.data;
  };

  const updateCustomer = async (id, data) => {
    const res = await axiosInstance.put(`${API}/customers/${id}`, data);
    await fetchCustomers();
    return res.data;
  };

  const deleteCustomer = async (id) => {
    await axiosInstance.delete(`${API}/customers/${id}`);
    await fetchCustomers();
  };

  // Quotes
  const fetchQuotes = async (params = {}) => {
    try {
      const res = await axiosInstance.get(`${API}/quotes`, { params });
      setQuotes(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching quotes:', err);
      return [];
    }
  };

  const createQuote = async (data) => {
    const res = await axiosInstance.post(`${API}/quotes`, data);
    await fetchQuotes();
    return res.data;
  };

  const updateQuote = async (id, data) => {
    const res = await axiosInstance.put(`${API}/quotes/${id}`, data);
    await fetchQuotes();
    return res.data;
  };

  const convertQuoteToJob = async (quoteId) => {
    const res = await axiosInstance.post(`${API}/quotes/${quoteId}/convert-to-job`);
    await fetchQuotes();
    await fetchJobs();
    return res.data;
  };

  // Jobs
  const fetchJobs = async (params = {}) => {
    try {
      const res = await axiosInstance.get(`${API}/jobs`, { params });
      setJobs(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching jobs:', err);
      return [];
    }
  };

  const createJob = async (data) => {
    const res = await axiosInstance.post(`${API}/jobs`, data);
    await fetchJobs();
    return res.data;
  };

  const updateJob = async (id, data) => {
    const res = await axiosInstance.put(`${API}/jobs/${id}`, data);
    await fetchJobs();
    return res.data;
  };

  const deleteJob = async (id) => {
    await axiosInstance.delete(`${API}/jobs/${id}`);
    await fetchJobs();
  };

  // Job Details
  const getJobDetails = async (jobId) => {
    const res = await axiosInstance.get(`${API}/jobs/${jobId}/details`);
    return res.data;
  };

  const archiveJob = async (jobId) => {
    const res = await axiosInstance.post(`${API}/jobs/${jobId}/archive`);
    await fetchJobs();
    return res.data;
  };

  const unarchiveJob = async (jobId) => {
    const res = await axiosInstance.post(`${API}/jobs/${jobId}/unarchive`);
    await fetchJobs();
    return res.data;
  };

  const completeJob = async (jobId) => {
    const res = await axiosInstance.post(`${API}/jobs/${jobId}/complete`);
    await fetchJobs();
    return res.data;
  };

  // Job Notes
  const createJobNote = async (jobId, data) => {
    const res = await axiosInstance.post(`${API}/jobs/${jobId}/notes`, data);
    return res.data;
  };

  const getJobNotes = async (jobId) => {
    const res = await axiosInstance.get(`${API}/jobs/${jobId}/notes`);
    return res.data;
  };

  const deleteJobNote = async (noteId) => {
    await axiosInstance.delete(`${API}/job-notes/${noteId}`);
  };

  // Job Activities
  const getJobActivities = async (jobId) => {
    const res = await axiosInstance.get(`${API}/jobs/${jobId}/activities`);
    return res.data;
  };

  // Job Items
  const fetchJobItems = async (jobId) => {
    const res = await axiosInstance.get(`${API}/jobs/${jobId}/items`);
    return res.data;
  };

  const createJobItem = async (jobId, data) => {
    const res = await axiosInstance.post(`${API}/jobs/${jobId}/items`, data);
    return res.data;
  };

  const updateJobItem = async (itemId, data) => {
    const res = await axiosInstance.put(`${API}/job-items/${itemId}`, data);
    return res.data;
  };

  const deleteJobItem = async (itemId) => {
    await axiosInstance.delete(`${API}/job-items/${itemId}`);
  };

  // Invoices
  const fetchInvoices = async (params = {}) => {
    try {
      const res = await axiosInstance.get(`${API}/invoices`, { params });
      setInvoices(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching invoices:', err);
      return [];
    }
  };

  const createInvoice = async (data) => {
    const res = await axiosInstance.post(`${API}/invoices`, data);
    await fetchInvoices();
    return res.data;
  };

  const createInvoiceFromJob = async (jobId) => {
    const res = await axiosInstance.post(`${API}/invoices/from-job/${jobId}`);
    await fetchInvoices();
    await fetchJobs();
    return res.data;
  };

  const updateInvoice = async (id, data) => {
    const res = await axiosInstance.put(`${API}/invoices/${id}`, data);
    await fetchInvoices();
    return res.data;
  };

  const getInvoiceById = async (invoiceId) => {
    const res = await axiosInstance.get(`${API}/invoices/${invoiceId}`);
    return res.data;
  };

  // Employees
  const fetchEmployees = async (params = {}) => {
    try {
      const res = await axiosInstance.get(`${API}/employees`, { params });
      setEmployees(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching employees:', err);
      return [];
    }
  };

  const createEmployee = async (data) => {
    const res = await axiosInstance.post(`${API}/employees`, data);
    await fetchEmployees();
    return res.data;
  };

  const updateEmployee = async (id, data) => {
    const res = await axiosInstance.put(`${API}/employees/${id}`, data);
    await fetchEmployees();
    return res.data;
  };

  // Tasks
  const fetchTasks = async (params = {}) => {
    try {
      const res = await axiosInstance.get(`${API}/tasks`, { params });
      setTasks(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching tasks:', err);
      return [];
    }
  };

  const createTask = async (data) => {
    const res = await axiosInstance.post(`${API}/tasks`, data);
    await fetchTasks();
    return res.data;
  };

  const updateTask = async (id, data) => {
    const res = await axiosInstance.put(`${API}/tasks/${id}`, data);
    await fetchTasks();
    return res.data;
  };

  const deleteTask = async (id) => {
    await axiosInstance.delete(`${API}/tasks/${id}`);
    await fetchTasks();
  };

  // Dashboard
  const fetchDashboardStats = async () => {
    try {
      const res = await axiosInstance.get(`${API}/dashboard/stats`);
      setDashboardStats(res.data);
      return res.data;
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      return null;
    }
  };

  // AI Tools
  const generateAIContent = async (tool, inputData) => {
    const res = await axiosInstance.post(`${API}/ai/generate`, { tool, input_data: inputData });
    return res.data;
  };

  const generateAIImages = async (tool, inputData, count = 3) => {
    const res = await axiosInstance.post(`${API}/ai/generate-images`, { tool, input_data: inputData, image_count: count });
    return res.data;
  };

  const fetchAIHistory = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/ai/history`, { params });
    return res.data;
  };

  // Time Clock
  const clockAction = async (employeeId, action) => {
    const res = await axiosInstance.post(`${API}/timeclock`, { employee_id: employeeId, action });
    return res.data;
  };

  const getClockStatus = async (employeeId) => {
    const res = await axiosInstance.get(`${API}/timeclock/${employeeId}/status`);
    return res.data;
  };

  const getTodayLogs = async (employeeId) => {
    const res = await axiosInstance.get(`${API}/timeclock/${employeeId}/today`);
    return res.data;
  };

  const getShiftSummary = async (employeeId, date) => {
    const params = date ? { date } : {};
    const res = await axiosInstance.get(`${API}/timeclock/${employeeId}/summary`, { params });
    return res.data;
  };

  // Payroll
  const createPayrollTransaction = async (data) => {
    const res = await axiosInstance.post(`${API}/payroll/transactions`, data);
    return res.data;
  };

  const getPayrollTransactions = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/payroll/transactions`, { params });
    return res.data;
  };

  const getPayrollBalance = async (employeeId) => {
    const res = await axiosInstance.get(`${API}/payroll/balance/${employeeId}`);
    return res.data;
  };

  const getPayrollReport = async (startDate, endDate) => {
    const res = await axiosInstance.get(`${API}/payroll/report`, { params: { start_date: startDate, end_date: endDate } });
    return res.data;
  };

  // Financials
  const createSalesEntry = async (data) => {
    const res = await axiosInstance.post(`${API}/financials/sales`, data);
    return res.data;
  };

  const getSalesEntries = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/financials/sales`, { params });
    return res.data;
  };

  const createExpenseEntry = async (data) => {
    const res = await axiosInstance.post(`${API}/financials/expenses`, data);
    return res.data;
  };

  const getExpenseEntries = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/financials/expenses`, { params });
    return res.data;
  };

  const getFinancialSummary = async (startDate, endDate) => {
    const res = await axiosInstance.get(`${API}/financials/summary`, { params: { start_date: startDate, end_date: endDate } });
    return res.data;
  };

  // Webstores (Legacy - keeping for compatibility)
  const createFundraiser = async (data) => {
    const res = await axiosInstance.post(`${API}/webstores/fundraiser`, data);
    return res.data;
  };

  const getFundraisers = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/webstores/fundraiser`, { params });
    return res.data;
  };

  const createB2BStore = async (data) => {
    const res = await axiosInstance.post(`${API}/webstores/b2b`, data);
    return res.data;
  };

  const getB2BStores = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/webstores/b2b`, { params });
    return res.data;
  };

  const createWebstoreOrder = async (data) => {
    const res = await axiosInstance.post(`${API}/webstores/orders`, data);
    return res.data;
  };

  const getWebstoreOrders = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/webstores/orders`, { params });
    return res.data;
  };

  // ============== NEW WEBSTORE SYSTEM ==============
  
  // Products (Master Catalog)
  const createProduct = async (data) => {
    const res = await axiosInstance.post(`${API}/products`, data);
    return res.data;
  };

  const getProducts = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/products`, { params });
    return res.data;
  };

  const getProduct = async (productId) => {
    const res = await axiosInstance.get(`${API}/products/${productId}`);
    return res.data;
  };

  const updateProduct = async (productId, data) => {
    const res = await axiosInstance.put(`${API}/products/${productId}`, data);
    return res.data;
  };

  const deleteProduct = async (productId) => {
    const res = await axiosInstance.delete(`${API}/products/${productId}`);
    return res.data;
  };

  // Webstores V2
  const createWebstore = async (data) => {
    const res = await axiosInstance.post(`${API}/webstores/v2`, data);
    return res.data;
  };

  const getWebstores = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/webstores/v2`, { params });
    return res.data;
  };

  const getWebstore = async (webstoreId) => {
    const res = await axiosInstance.get(`${API}/webstores/v2/${webstoreId}`);
    return res.data;
  };

  const updateWebstore = async (webstoreId, data) => {
    const res = await axiosInstance.put(`${API}/webstores/v2/${webstoreId}`, data);
    return res.data;
  };

  const deleteWebstore = async (webstoreId) => {
    const res = await axiosInstance.delete(`${API}/webstores/v2/${webstoreId}`);
    return res.data;
  };

  // Webstore Products
  const assignProductToWebstore = async (webstoreId, data) => {
    const res = await axiosInstance.post(`${API}/webstores/v2/${webstoreId}/products`, data);
    return res.data;
  };

  const getWebstoreProducts = async (webstoreId, includeDisabled = false) => {
    const res = await axiosInstance.get(`${API}/webstores/v2/${webstoreId}/products`, { 
      params: { include_disabled: includeDisabled } 
    });
    return res.data;
  };

  const removeProductFromWebstore = async (webstoreId, productId) => {
    const res = await axiosInstance.delete(`${API}/webstores/v2/${webstoreId}/products/${productId}`);
    return res.data;
  };

  // Webstore Orders V2
  const createWebstoreOrderV2 = async (data) => {
    const res = await axiosInstance.post(`${API}/webstores/v2/orders`, data);
    return res.data;
  };

  const getWebstoreOrdersV2 = async (params = {}) => {
    const res = await axiosInstance.get(`${API}/webstores/v2/orders`, { params });
    return res.data;
  };

  const getWebstoreOrderV2 = async (orderId) => {
    const res = await axiosInstance.get(`${API}/webstores/v2/orders/${orderId}`);
    return res.data;
  };

  const updateOrderStatus = async (orderId, status, jobId = null) => {
    const res = await axiosInstance.put(`${API}/webstores/v2/orders/${orderId}/status`, null, {
      params: { status, job_id: jobId }
    });
    return res.data;
  };

  const createJobFromOrder = async (orderId) => {
    const res = await axiosInstance.post(`${API}/webstores/v2/orders/${orderId}/create-job`);
    return res.data;
  };

  // Payouts
  const recordPayout = async (webstoreId, amount, notes = null) => {
    const res = await axiosInstance.post(`${API}/webstores/v2/${webstoreId}/record-payout`, null, {
      params: { amount, notes }
    });
    return res.data;
  };

  const getWebstorePayouts = async (webstoreId) => {
    const res = await axiosInstance.get(`${API}/webstores/v2/${webstoreId}/payouts`);
    return res.data;
  };

  // Tenant / Company Settings
  const getTenant = async () => {
    const res = await axiosInstance.get(`${API}/tenant/current`);
    return res.data;
  };

  const updateTenant = async (data) => {
    const res = await axiosInstance.put(`${API}/tenant/settings`, data);
    return res.data;
  };

  const value = {
    // State
    customers, quotes, jobs, invoices, employees, tasks, dashboardStats, loading,
    setLoading,
    // Customer actions
    fetchCustomers, createCustomer, updateCustomer, deleteCustomer,
    // Quote actions
    fetchQuotes, createQuote, updateQuote, convertQuoteToJob,
    // Job actions
    fetchJobs, createJob, updateJob, deleteJob,
    getJobDetails, archiveJob, unarchiveJob, completeJob,
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
    assignProductToWebstore, getWebstoreProducts, removeProductFromWebstore,
    // Webstore Orders V2
    createWebstoreOrderV2, getWebstoreOrdersV2, getWebstoreOrderV2, updateOrderStatus, createJobFromOrder,
    // Payouts
    recordPayout, getWebstorePayouts,
    // Tenant / Company Settings
    getTenant, updateTenant
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContext;
