import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth, Permission } from '../context/AuthContext';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { ArrowDown, ArrowUp, Download, Filter, Loader2, Settings2, TrendingDown, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TIME_RANGE_OPTIONS = [
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
  { value: 'this_year', label: 'This Year' },
  { value: 'custom', label: 'Custom Date Range' },
];

const CATEGORY_OPTIONS = [
  { value: 'all', label: 'All Categories' },
  { value: 'vehicle_wraps', label: 'Vehicle Wraps' },
  { value: 'banners', label: 'Banners' },
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'digital_print', label: 'Digital Prints' },
  { value: 'cut_vinyl', label: 'Cut Vinyl' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'services', label: 'Services' },
  { value: 'custom', label: 'Custom / Miscellaneous' },
];

const WIDGET_LABELS = {
  revenue_trend: 'Revenue Trend',
  profit_by_category: 'Profit by Category',
  top_customers: 'Top Customers by Profit',
  low_margin_jobs: 'Low Margin Jobs',
  average_job_value: 'Average Order Value',
};

const formatCurrency = (value) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);

export default function ProfitMarginAnalytics() {
  const { hasPermission, isAdminOrOwner } = useAuth();
  const canView = hasPermission(Permission.FINANCIALS_VIEW) || isAdminOrOwner();

  const [loading, setLoading] = useState(true);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [customRange, setCustomRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [jobSort, setJobSort] = useState({ key: 'profit', direction: 'desc' });
  const [preferences, setPreferences] = useState({
    simple_mode: false,
    widget_order: Object.keys(WIDGET_LABELS),
    enabled_widgets: Object.fromEntries(Object.keys(WIDGET_LABELS).map((key) => [key, true])),
  });

  const getToken = () => getAuthToken();

  const fetchDashboard = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({ range_key: timeRange });
      if (categoryFilter !== 'all') params.set('category', categoryFilter);
      if (timeRange === 'custom') {
        params.set('start_date', customRange.start);
        params.set('end_date', customRange.end);
      }
      const response = await fetch(`${API_URL}/api/profit-analytics/dashboard?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to load analytics');
      const data = await response.json();
      setDashboard(data);
      setPreferences(data.preferences || preferences);
    } catch (error) {
      toast.error('Failed to load profit analytics');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, customRange.end, customRange.start, timeRange]);

  useEffect(() => {
    if (canView) {
      fetchDashboard();
    }
  }, [canView, fetchDashboard]);

  const savePreferences = async () => {
    const token = getToken();
    if (!token) return;
    setSavingPreferences(true);
    try {
      const response = await fetch(`${API_URL}/api/profit-analytics/preferences`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });
      if (!response.ok) throw new Error('Failed to save preferences');
      toast.success('Dashboard settings saved');
      await fetchDashboard();
    } catch (error) {
      toast.error('Failed to save dashboard settings');
    } finally {
      setSavingPreferences(false);
    }
  };

  const downloadReport = async (format) => {
    const token = getToken();
    if (!token) return;
    const params = new URLSearchParams({ format, range_key: timeRange });
    if (categoryFilter !== 'all') params.set('category', categoryFilter);
    if (timeRange === 'custom') {
      params.set('start_date', customRange.start);
      params.set('end_date', customRange.end);
    }

    try {
      const response = await fetch(`${API_URL}/api/profit-analytics/export?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to export');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = format === 'xlsx' ? 'profit-margin-dashboard.xlsx' : `profit-margin-dashboard.${format}`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error(`Failed to export ${format.toUpperCase()}`);
    }
  };

  const sortedJobs = useMemo(() => {
    const rows = [...(dashboard?.job_rows || [])];
    rows.sort((a, b) => {
      const first = a[jobSort.key] || 0;
      const second = b[jobSort.key] || 0;
      return jobSort.direction === 'asc' ? first - second : second - first;
    });
    return rows;
  }, [dashboard?.job_rows, jobSort]);

  const updateWidgetOrder = (widgetKey, direction) => {
    const currentIndex = preferences.widget_order.indexOf(widgetKey);
    if (currentIndex < 0) return;
    const nextIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (nextIndex < 0 || nextIndex >= preferences.widget_order.length) return;
    const nextOrder = [...preferences.widget_order];
    [nextOrder[currentIndex], nextOrder[nextIndex]] = [nextOrder[nextIndex], nextOrder[currentIndex]];
    setPreferences((current) => ({ ...current, widget_order: nextOrder }));
  };

  if (!canView) {
    return (
      <Card data-testid="profit-analytics-access-denied">
        <CardHeader>
          <CardTitle>Access denied</CardTitle>
          <CardDescription>You do not have permission to view Profit & Margin Analytics.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const metrics = dashboard?.metrics || {};
  const categoryRows = dashboard?.category_rows || [];
  const customerRows = dashboard?.customer_rows || [];
  const trendRows = dashboard?.trend_rows || [];
  const lowMarginJobs = dashboard?.low_margin_jobs || [];
  const maxCategoryProfit = Math.max(...categoryRows.map((row) => row.profit), 1);

  return (
    <div className="space-y-6" data-testid="profit-analytics-page">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Profit & Margin Analytics</h1>
          <p className="text-slate-300 mt-1">Use cost snapshots and benchmark data to spot profit drivers and underpriced work.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {['csv', 'xlsx', 'pdf'].map((format) => (
            <Button key={format} variant="outline" onClick={() => downloadReport(format)} data-testid={`profit-analytics-export-${format}`}>
              <Download className="h-4 w-4 mr-2" /> {format.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <Card data-testid="profit-analytics-filters-card">
        <CardContent className="p-4 space-y-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="space-y-2 min-w-[220px]">
              <Label>Time Range</Label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger data-testid="profit-analytics-time-range-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TIME_RANGE_OPTIONS.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2 min-w-[220px]">
              <Label>Category Filter</Label>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger data-testid="profit-analytics-category-filter-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={fetchDashboard} data-testid="profit-analytics-refresh-button"><Filter className="h-4 w-4 mr-2" /> Refresh</Button>
          </div>
          {timeRange === 'custom' && (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Input type="date" value={customRange.start} onChange={(e) => setCustomRange((current) => ({ ...current, start: e.target.value }))} data-testid="profit-analytics-custom-start" />
              </div>
              <div className="space-y-2">
                <Label>End Date</Label>
                <Input type="date" value={customRange.end} onChange={(e) => setCustomRange((current) => ({ ...current, end: e.target.value }))} data-testid="profit-analytics-custom-end" />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card data-testid="profit-analytics-metric-revenue"><CardContent className="p-5"><p className="text-xs uppercase text-slate-400">Revenue This Month</p><p className="text-2xl font-bold text-gray-900 mt-2">{formatCurrency(metrics.revenue_this_month)}</p></CardContent></Card>
        <Card data-testid="profit-analytics-metric-profit"><CardContent className="p-5"><p className="text-xs uppercase text-slate-400">Profit This Month</p><p className="text-2xl font-bold text-emerald-400 mt-2">{formatCurrency(metrics.profit_this_month)}</p></CardContent></Card>
        <Card data-testid="profit-analytics-metric-average-job-value"><CardContent className="p-5"><p className="text-xs uppercase text-slate-400">Average Order Value</p><p className="text-2xl font-bold text-gray-900 mt-2">{formatCurrency(metrics.average_job_value)}</p></CardContent></Card>
        <Card data-testid="profit-analytics-metric-average-margin"><CardContent className="p-5"><p className="text-xs uppercase text-slate-400">Average Profit Margin</p><p className="text-2xl font-bold text-gray-900 mt-2">{metrics.average_profit_margin || 0}%</p></CardContent></Card>
      </div>

      <Card data-testid="profit-analytics-widget-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900"><Settings2 className="h-5 w-5 text-teal-400" /> Dashboard Settings</CardTitle>
          <CardDescription>Keep it simple when needed: toggle simple mode and reorder visible widgets.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-slate-900/40 p-4">
            <div>
              <p className="font-medium text-gray-900">Simple View</p>
              <p className="text-sm text-slate-400">Reduce visual density while keeping the same data source.</p>
            </div>
            <input
              type="checkbox"
              checked={preferences.simple_mode}
              onChange={(e) => setPreferences((current) => ({ ...current, simple_mode: e.target.checked }))}
              data-testid="profit-analytics-simple-mode-toggle"
            />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            {preferences.widget_order.map((widgetKey, index) => (
              <div key={widgetKey} className="flex items-center justify-between rounded-xl border border-gray-200 bg-slate-900/40 p-3" data-testid={`profit-analytics-widget-row-${widgetKey}`}>
                <div>
                  <p className="font-medium text-gray-900">{WIDGET_LABELS[widgetKey]}</p>
                  <p className="text-xs text-slate-400">Position {index + 1}</p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={preferences.enabled_widgets?.[widgetKey] !== false}
                    onChange={(e) => setPreferences((current) => ({
                      ...current,
                      enabled_widgets: { ...current.enabled_widgets, [widgetKey]: e.target.checked },
                    }))}
                    data-testid={`profit-analytics-widget-toggle-${widgetKey}`}
                  />
                  <Button variant="outline" size="icon" onClick={() => updateWidgetOrder(widgetKey, 'up')} data-testid={`profit-analytics-widget-up-${widgetKey}`}><ArrowUp className="h-4 w-4" /></Button>
                  <Button variant="outline" size="icon" onClick={() => updateWidgetOrder(widgetKey, 'down')} data-testid={`profit-analytics-widget-down-${widgetKey}`}><ArrowDown className="h-4 w-4" /></Button>
                </div>
              </div>
            ))}
          </div>
          <Button onClick={savePreferences} disabled={savingPreferences} data-testid="profit-analytics-save-preferences-button">
            {savingPreferences ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Settings2 className="h-4 w-4 mr-2" />}
            Save dashboard settings
          </Button>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-teal-500" /></div>
      ) : (
        <div className="space-y-6">
          {preferences.widget_order.filter((widgetKey) => preferences.enabled_widgets?.[widgetKey] !== false).map((widgetKey) => {
            if (widgetKey === 'profit_by_category') {
              return (
                <Card key={widgetKey} data-testid="profit-analytics-category-chart-card">
                  <CardHeader>
                    <CardTitle className="text-gray-900">Profit by Category</CardTitle>
                    <CardDescription>Revenue, cost, profit, and margin by product category.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {categoryRows.map((row) => (
                      <div key={row.category} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-900">{row.category_label}</span>
                          <span className="text-slate-300">{formatCurrency(row.profit)} · {row.average_margin}% margin</span>
                        </div>
                        <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
                          <div className="h-full rounded-full bg-teal-500" style={{ width: `${Math.max((row.profit / maxCategoryProfit) * 100, 4)}%` }} />
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            }

            if (widgetKey === 'revenue_trend' && !preferences.simple_mode) {
              return (
                <Card key={widgetKey} data-testid="profit-analytics-revenue-trend-card">
                  <CardHeader>
                    <CardTitle className="text-gray-900">Revenue Trend</CardTitle>
                    <CardDescription>Revenue and profit trend for the selected range.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {trendRows.map((row) => (
                        <div key={row.period} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
                          <span className="text-gray-900">{row.period}</span>
                          <div className="text-right">
                            <p className="text-gray-900">{formatCurrency(row.revenue)}</p>
                            <p className="text-xs text-slate-400">Profit {formatCurrency(row.profit)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            }

            if (widgetKey === 'top_customers') {
              return (
                <Card key={widgetKey} data-testid="profit-analytics-top-customers-card">
                  <CardHeader>
                    <CardTitle className="text-gray-900">Top Customers by Profit</CardTitle>
                    <CardDescription>Which customers generate the most profit.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {customerRows.slice(0, preferences.simple_mode ? 5 : 8).map((row) => (
                      <div key={row.customer_id} className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3">
                        <div>
                          <p className="text-gray-900 font-medium">{row.customer_name}</p>
                          <p className="text-xs text-slate-400">{row.total_jobs} jobs · {row.average_margin}% margin</p>
                        </div>
                        <p className="text-emerald-400 font-semibold">{formatCurrency(row.total_profit)}</p>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            }

            if (widgetKey === 'low_margin_jobs') {
              return (
                <Card key={widgetKey} data-testid="profit-analytics-low-margin-card">
                  <CardHeader>
                    <CardTitle className="text-gray-900">Low Margin / Underpriced Jobs</CardTitle>
                    <CardDescription>Orders flagged below benchmark or at unusually low margins.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {(lowMarginJobs.length ? lowMarginJobs : sortedJobs.slice(-5)).slice(0, 8).map((row) => (
                      <div key={row.job_id} className="flex items-center justify-between rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
                        <div>
                          <p className="text-gray-900 font-medium">{row.job_name}</p>
                          <p className="text-xs text-slate-300">{row.customer_name} · {row.category}</p>
                        </div>
                        <Badge className="bg-red-100 text-red-700">{row.profit_margin}% margin</Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            }

            if (widgetKey === 'average_job_value') {
              return (
                <Card key={widgetKey} data-testid="profit-analytics-average-job-value-card">
                  <CardHeader>
                    <CardTitle className="text-gray-900">Average Order Value</CardTitle>
                    <CardDescription>A simple view of average sale size and profitability.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-xl border border-gray-200 bg-slate-900/40 p-5">
                      <p className="text-xs uppercase text-slate-400">Average Job Value</p>
                      <p className="text-3xl font-bold text-gray-900 mt-2">{formatCurrency(metrics.average_job_value)}</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 bg-slate-900/40 p-5">
                      <p className="text-xs uppercase text-slate-400">Average Profit Margin</p>
                      <p className="text-3xl font-bold text-gray-900 mt-2">{metrics.average_profit_margin || 0}%</p>
                    </div>
                  </CardContent>
                </Card>
              );
            }

            return null;
          })}

          <Card data-testid="profit-analytics-job-table-card">
            <CardHeader>
              <CardTitle className="text-gray-900">Order Profitability Table</CardTitle>
              <CardDescription>Sort by profit, margin, or revenue and spot underpriced work.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {['profit', 'profit_margin', 'revenue'].map((key) => (
                  <Button
                    key={key}
                    variant={jobSort.key === key ? 'default' : 'outline'}
                    onClick={() => setJobSort((current) => ({ key, direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc' }))}
                    data-testid={`profit-analytics-sort-${key}`}
                  >
                    Sort by {key === 'profit_margin' ? 'Margin' : key.charAt(0).toUpperCase() + key.slice(1)}
                  </Button>
                ))}
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order Name</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">Total Cost</TableHead>
                    <TableHead className="text-right">Profit</TableHead>
                    <TableHead className="text-right">Profit Margin</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedJobs.map((row) => (
                    <TableRow key={row.job_id} data-testid={`profit-analytics-job-row-${row.job_id}`}>
                      <TableCell className="text-gray-900">{row.job_name}</TableCell>
                      <TableCell>{row.customer_name}</TableCell>
                      <TableCell>{row.category}</TableCell>
                      <TableCell className="text-right">{formatCurrency(row.revenue)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(row.total_cost)}</TableCell>
                      <TableCell className="text-right text-emerald-400">{formatCurrency(row.profit)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <span className={row.underpriced || row.profit_margin < 25 ? 'text-red-400 font-semibold' : 'text-gray-900'}>{row.profit_margin}%</span>
                          {row.underpriced && <Badge className="bg-red-100 text-red-700">Potentially underpriced job</Badge>}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card data-testid="profit-analytics-customer-table-card">
            <CardHeader>
              <CardTitle className="text-gray-900">Customer Profitability Report</CardTitle>
              <CardDescription>See which customers generate the most revenue and profit.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer Name</TableHead>
                    <TableHead className="text-right">Total Revenue</TableHead>
                    <TableHead className="text-right">Total Profit</TableHead>
                    <TableHead className="text-right">Average Margin</TableHead>
                    <TableHead className="text-right">Total Jobs</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customerRows.map((row) => (
                    <TableRow key={row.customer_id} data-testid={`profit-analytics-customer-row-${row.customer_id}`}>
                      <TableCell className="text-gray-900">{row.customer_name}</TableCell>
                      <TableCell className="text-right">{formatCurrency(row.total_revenue)}</TableCell>
                      <TableCell className="text-right text-emerald-400">{formatCurrency(row.total_profit)}</TableCell>
                      <TableCell className="text-right">{row.average_margin}%</TableCell>
                      <TableCell className="text-right">{row.total_jobs}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}