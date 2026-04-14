import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Info, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth, Permission } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { buildPayrollCsv, buildPayrollPrintHtml, downloadTextFile } from '../lib/payrollExport';
import {
  buildAdjustmentRows,
  buildWorksheetRows,
  calculateBreakMinutes,
  getSignedAdjustmentTotal,
  getWeekDates,
  getWeekStart,
  hasAdjustmentContent,
  hasShiftContent,
  inferTransactionType,
  summarizeWorksheet,
  toIsoDateTime,
} from '../lib/payrollWorksheet';
import { formatCurrency } from '../lib/utils';
import { PayrollWorksheetToolbar } from '../components/payroll/PayrollWorksheetToolbar';
import { PayrollAdjustmentsPanel } from '../components/payroll/PayrollAdjustmentsPanel';
import { PayrollWeekTable } from '../components/payroll/PayrollWeekTable';
import { PayrollWorksheetSummary } from '../components/payroll/PayrollWorksheetSummary';

const normalizeEmployeeDraft = (employee) => ({
  id: employee?.id || '',
  name: employee?.name || '',
  title: employee?.title || '',
  manager_name: employee?.manager_name || '',
  hourly_rate: String(employee?.hourly_rate ?? ''),
  overtime_rate: String(employee?.overtime_rate ?? ((Number(employee?.hourly_rate || 0) * 1.5).toFixed(2))),
  role: employee?.role || 'staff',
});

const getDayLabel = (value) => {
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toLocaleDateString('en-US', { weekday: 'long' });
};

export default function Payroll() {
  const { hasPermission, isAdminOrOwner } = useAuth();
  const { api, employees, fetchEmployees } = useApp();
  const canViewPayroll = hasPermission(Permission.PAYROLL_VIEW);
  const canEditPayroll = isAdminOrOwner() || hasPermission(Permission.PAYROLL_EDIT);

  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [weekStart, setWeekStart] = useState(getWeekStart());
  const [employeeDraft, setEmployeeDraft] = useState(normalizeEmployeeDraft(null));
  const [worksheetRows, setWorksheetRows] = useState(buildWorksheetRows(getWeekStart(), []));
  const [adjustmentRows, setAdjustmentRows] = useState(buildAdjustmentRows([]));
  const [report, setReport] = useState(null);
  const [timesheet, setTimesheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState('');

  useEffect(() => {
    if (!canViewPayroll) return;
    fetchEmployees();
  }, [canViewPayroll, fetchEmployees]);

  useEffect(() => {
    if (!employees.length || selectedEmployeeId) return;
    setSelectedEmployeeId(employees[0].id);
  }, [employees, selectedEmployeeId]);

  const weekDates = useMemo(() => getWeekDates(weekStart), [weekStart]);
  const weekEnd = weekDates[6]?.date || weekStart;

  const loadWorksheet = useCallback(async () => {
    if (!selectedEmployeeId || !canViewPayroll) return;
    setLoading(true);
    try {
      const [employeeRes, shiftsRes, transactionsRes, reportRes, timesheetRes] = await Promise.all([
        api.get(`/employees/${selectedEmployeeId}`),
        api.get('/payroll/timeclock-shifts', { params: { employee_id: selectedEmployeeId, start_date: weekStart, end_date: weekEnd } }),
        api.get('/payroll/transactions', { params: { employee_id: selectedEmployeeId, start_date: weekStart, end_date: weekEnd } }),
        api.get('/payroll/report', { params: { employee_id: selectedEmployeeId, start_date: weekStart, end_date: weekEnd } }),
        api.get('/payroll/timesheet', { params: { employee_id: selectedEmployeeId, start_date: weekStart, end_date: weekEnd } }),
      ]);
      setEmployeeDraft(normalizeEmployeeDraft(employeeRes.data));
      setWorksheetRows(buildWorksheetRows(weekStart, shiftsRes.data || []));
      setAdjustmentRows(buildAdjustmentRows(transactionsRes.data || []));
      setReport(reportRes.data);
      setTimesheet(timesheetRes.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load payroll worksheet');
    } finally {
      setLoading(false);
    }
  }, [api, canViewPayroll, selectedEmployeeId, weekEnd, weekStart]);

  useEffect(() => {
    loadWorksheet();
  }, [loadWorksheet]);

  const worksheetSummary = useMemo(
    () => summarizeWorksheet(worksheetRows, Number(employeeDraft.hourly_rate || 0), Number(employeeDraft.overtime_rate || 0)),
    [employeeDraft.hourly_rate, employeeDraft.overtime_rate, worksheetRows],
  );

  const adjustmentTotal = useMemo(() => getSignedAdjustmentTotal(adjustmentRows), [adjustmentRows]);
  const selectedTimesheetEmployee = timesheet?.employees?.[0];
  const carryoverBalance = selectedTimesheetEmployee?.carryover_balance || report?.employees?.[0]?.carryover_balance || 0;
  const hiddenLegacyEntryCount = useMemo(
    () => (selectedTimesheetEmployee?.entries || []).filter((entry) => entry.source !== 'time_clock').length,
    [selectedTimesheetEmployee],
  );

  const handleRowChange = (index, field, value) => {
    setWorksheetRows((currentRows) => currentRows.map((row, rowIndex) => {
      if (rowIndex !== index) return row;
      const nextRow = { ...row, [field]: value };
      if (field === 'date') nextRow.dayLabel = getDayLabel(value);
      return nextRow;
    }));
  };

  const handleAdjustmentChange = (index, field, value) => {
    setAdjustmentRows((currentRows) => currentRows.map((row, rowIndex) => (
      rowIndex === index ? { ...row, [field]: value } : row
    )));
  };

  const fetchExportPayload = useCallback(async () => {
    const params = { employee_id: selectedEmployeeId, start_date: weekStart, end_date: weekEnd };
    const [reportRes, timesheetRes] = await Promise.all([
      api.get('/payroll/report', { params }),
      api.get('/payroll/timesheet', { params }),
    ]);
    return { report: reportRes.data, timesheet: timesheetRes.data };
  }, [api, selectedEmployeeId, weekEnd, weekStart]);

  const handleExportCsv = async () => {
    setExporting('csv');
    try {
      const payload = await fetchExportPayload();
      const csv = buildPayrollCsv({
        ...payload,
        selectedEmployeeLabel: employeeDraft.name || 'Selected employee',
        rangeLabel: `${weekStart} — ${weekEnd}`,
      });
      downloadTextFile(`payroll-worksheet-${selectedEmployeeId}-${weekStart}.csv`, csv, 'text/csv;charset=utf-8');
      toast.success('Payroll worksheet CSV exported');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to export worksheet');
    } finally {
      setExporting('');
    }
  };

  const handlePrint = async () => {
    const printWindow = window.open('', '_blank', 'noopener,noreferrer,width=1200,height=900');
    if (!printWindow) {
      toast.error('Please allow pop-ups to print the payroll worksheet');
      return;
    }
    setExporting('print');
    try {
      const payload = await fetchExportPayload();
      const html = buildPayrollPrintHtml({
        ...payload,
        selectedEmployeeLabel: employeeDraft.name || 'Selected employee',
        rangeLabel: `${weekStart} — ${weekEnd}`,
      });
      printWindow.document.open();
      printWindow.document.write(html);
      printWindow.document.close();
      printWindow.focus();
      window.setTimeout(() => printWindow.print(), 300);
      toast.success('Printable worksheet opened');
    } catch (error) {
      printWindow.close();
      toast.error(error.response?.data?.detail || 'Failed to print worksheet');
    } finally {
      setExporting('');
    }
  };

  const validateRows = () => {
    for (const row of worksheetRows) {
      const rowHasValues = hasShiftContent(row);
      if (!rowHasValues) continue;
      if (!row.startTime || !row.endTime) {
        return `Add both start and end time for ${row.dayLabel}.`;
      }
      if ((row.lunchStart && !row.lunchEnd) || (!row.lunchStart && row.lunchEnd)) {
        return `Complete both lunch fields for ${row.dayLabel}.`;
      }
      if (row.lunchStart && row.lunchEnd && calculateBreakMinutes(row.lunchStart, row.lunchEnd) <= 0) {
        return `Lunch end must be after lunch start for ${row.dayLabel}.`;
      }
    }
    return null;
  };

  const handleSaveWorksheet = async () => {
    const validationError = validateRows();
    if (validationError) {
      toast.error(validationError);
      return;
    }

    setSaving(true);
    try {
      await api.put(`/employees/${selectedEmployeeId}`, {
        name: employeeDraft.name,
        title: employeeDraft.title,
        manager_name: employeeDraft.manager_name,
        hourly_rate: Number(employeeDraft.hourly_rate || 0),
        overtime_rate: Number(employeeDraft.overtime_rate || 0),
      });

      for (const row of worksheetRows) {
        const rowHasValues = hasShiftContent(row);
        if (!rowHasValues && row.id) {
          await api.delete(`/payroll/timeclock-shifts/${row.id}`);
          continue;
        }
        if (!rowHasValues) continue;

        const payload = {
          employee_id: selectedEmployeeId,
          date: row.date,
          clock_in: toIsoDateTime(row.date, row.startTime),
          clock_out: toIsoDateTime(row.date, row.endTime),
          lunch_start: toIsoDateTime(row.date, row.lunchStart),
          lunch_end: toIsoDateTime(row.date, row.lunchEnd),
          break_minutes: calculateBreakMinutes(row.lunchStart, row.lunchEnd),
          notes: row.notes,
        };

        if (row.id) {
          await api.put(`/payroll/timeclock-shifts/${row.id}`, payload);
        } else {
          await api.post('/payroll/timeclock-shifts', payload);
        }
      }

      for (const row of adjustmentRows) {
        const rowHasValues = hasAdjustmentContent(row);
        if (!rowHasValues && row.id) {
          await api.delete(`/payroll/transactions/${row.id}`);
          continue;
        }
        if (!rowHasValues) continue;

        const numericAmount = Number(row.amount || 0);
        if (!numericAmount) continue;
        const payload = {
          employee_id: selectedEmployeeId,
          date: row.date || weekStart,
          description: row.notes,
          amount: Math.abs(numericAmount),
          type: inferTransactionType(numericAmount, row.type),
        };

        if (row.id) {
          await api.put(`/payroll/transactions/${row.id}`, payload);
        } else {
          await api.post('/payroll/transactions', payload);
        }
      }

      await fetchEmployees();
      await loadWorksheet();
      toast.success('Payroll worksheet saved');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save payroll worksheet');
    } finally {
      setSaving(false);
    }
  };

  if (!canViewPayroll) {
    return (
      <div className="flex h-64 flex-col items-center justify-center text-center">
        <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
        <h2 className="text-xl font-semibold text-gray-900" data-testid="payroll-access-denied-title">Access Denied</h2>
        <p className="mt-2 text-gray-500">You do not have permission to view payroll.</p>
      </div>
    );
  }

  if (!employees.length && loading) {
    return (
      <div className="flex h-64 items-center justify-center" data-testid="payroll-loading-state">
        <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
      </div>
    );
  }

  if (!employees.length) {
    return (
      <div className="rounded-[28px] border border-slate-200 bg-white p-8" data-testid="payroll-empty-state">
        <p className="text-lg font-semibold text-slate-900">No employees found.</p>
        <p className="mt-2 text-sm text-slate-500">Add an employee first to use the payroll worksheet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-8" data-testid="payroll-page">
      <div className="space-y-2 px-1">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500" data-testid="payroll-page-kicker">Admin Payroll Worksheet</p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900" data-testid="payroll-page-title">One practical worksheet screen</h1>
        <p className="max-w-3xl text-sm text-slate-600" data-testid="payroll-page-subtitle">Inline payroll editing for one employee and one week — no stacked dashboards, duplicate cards, or modal-heavy busywork.</p>
      </div>

      <div className="overflow-hidden rounded-[34px] border border-slate-300 bg-white shadow-[0_22px_55px_rgba(15,23,42,0.08)]" data-testid="payroll-worksheet-layout">
        <PayrollWorksheetToolbar
          employees={employees}
          employeeId={selectedEmployeeId}
          exporting={exporting}
          onEmployeeChange={setSelectedEmployeeId}
          onExportCsv={handleExportCsv}
          onPrint={handlePrint}
          onSave={handleSaveWorksheet}
          saveDisabled={!canEditPayroll || saving || loading}
          saving={saving}
          weekStart={weekStart}
          onWeekChange={setWeekStart}
        />

        <div className="grid min-h-[880px] lg:grid-cols-[320px_1fr]">
          <PayrollAdjustmentsPanel rows={adjustmentRows} onChange={handleAdjustmentChange} total={adjustmentTotal} />

          <section className="bg-[#f8fbfb] p-5 lg:p-7" data-testid="payroll-worksheet-main">
            <div className="space-y-5 rounded-[30px] border border-slate-300 bg-white p-5 shadow-[inset_0_0_0_1px_rgba(148,163,184,0.16)] lg:p-7">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="payroll-meta-grid">
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-employee-name">Employee Name</Label>
                  <Input id="payroll-meta-employee-name" value={employeeDraft.name} onChange={(event) => setEmployeeDraft((current) => ({ ...current, name: event.target.value }))} data-testid="payroll-meta-employee-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-title">Title</Label>
                  <Input id="payroll-meta-title" value={employeeDraft.title} onChange={(event) => setEmployeeDraft((current) => ({ ...current, title: event.target.value }))} data-testid="payroll-meta-title-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-manager-name">Manager Name</Label>
                  <Input id="payroll-meta-manager-name" value={employeeDraft.manager_name} onChange={(event) => setEmployeeDraft((current) => ({ ...current, manager_name: event.target.value }))} data-testid="payroll-meta-manager-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-week">Week Of</Label>
                  <Input id="payroll-meta-week" type="date" value={weekStart} onChange={(event) => setWeekStart(event.target.value)} data-testid="payroll-meta-week-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-hourly-rate">Hourly Rate</Label>
                  <Input id="payroll-meta-hourly-rate" type="number" step="0.01" value={employeeDraft.hourly_rate} onChange={(event) => setEmployeeDraft((current) => ({ ...current, hourly_rate: event.target.value }))} data-testid="payroll-meta-hourly-rate-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-overtime-rate">Overtime Rate</Label>
                  <Input id="payroll-meta-overtime-rate" type="number" step="0.01" value={employeeDraft.overtime_rate} onChange={(event) => setEmployeeDraft((current) => ({ ...current, overtime_rate: event.target.value }))} data-testid="payroll-meta-overtime-rate-input" />
                </div>
              </div>

              {hiddenLegacyEntryCount > 0 && (
                <div className="flex flex-wrap items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3" data-testid="payroll-legacy-entry-warning">
                  <Info className="mt-0.5 h-4 w-4 text-amber-600" />
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-amber-900">Legacy off-grid entries are still included in exports and payroll totals.</p>
                    <p className="text-sm text-amber-800">{hiddenLegacyEntryCount} manual or timer entry{hiddenLegacyEntryCount === 1 ? '' : 'ies'} exist in this week and are preserved even though the worksheet grid focuses on time-clock rows.</p>
                  </div>
                </div>
              )}

              <PayrollWeekTable rows={worksheetSummary.rows} onRowChange={handleRowChange} />

              <div className="flex flex-wrap items-center gap-3" data-testid="payroll-worksheet-status-strip">
                <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700" data-testid="payroll-status-badge">{canEditPayroll ? 'Inline editing enabled' : 'Read only'}</Badge>
                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700" data-testid="payroll-export-ready-badge">Export + print wired to current payroll endpoints</Badge>
                <p className="text-sm text-slate-500" data-testid="payroll-week-range-label">{weekStart} — {weekEnd}</p>
              </div>

              <PayrollWorksheetSummary adjustmentsTotal={adjustmentTotal} carryoverBalance={carryoverBalance} summary={worksheetSummary} />
            </div>
          </section>
        </div>
      </div>

      <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500" data-testid="payroll-footer-summary">
        <span>Report gross for selected week: <strong className="text-slate-900" data-testid="payroll-report-gross-value">{formatCurrency(report?.employees?.[0]?.gross_pay || 0)}</strong></span>
        <span>Current final owed from backend: <strong className="text-slate-900" data-testid="payroll-report-final-owed-value">{formatCurrency(report?.employees?.[0]?.final_owed || 0)}</strong></span>
      </div>
    </div>
  );
}