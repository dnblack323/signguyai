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
  getCurrentCycleRange,
  getDateRangeDates,
  getPresetDateRange,
  getSignedAdjustmentTotal,
  hasAdjustmentContent,
  hasShiftContent,
  inferTransactionType,
  summarizeWorksheet,
  toIsoDateTime,
} from '../lib/payrollWorksheet';
import { formatCurrency } from '../lib/utils';
import { PayrollWorksheetToolbar } from '../components/payroll/PayrollWorksheetToolbar';
import { PayrollAdjustmentsPanel } from '../components/payroll/PayrollAdjustmentsPanel';
import { PayrollLegacyEntriesSection } from '../components/payroll/PayrollLegacyEntriesSection';
import { PayrollWeekTable } from '../components/payroll/PayrollWeekTable';
import { PayrollWorksheetSummary } from '../components/payroll/PayrollWorksheetSummary';
import { PayrollSignoffStrip } from '../components/payroll/PayrollSignoffStrip';

const normalizeEmployeeDraft = (employee) => ({
  id: employee?.id || '',
  name: employee?.name || '',
  title: employee?.title || '',
  manager_name: employee?.manager_name || '',
  hourly_rate: String(employee?.hourly_rate ?? ''),
  overtime_rate: String(employee?.overtime_rate ?? ((Number(employee?.hourly_rate || 0) * 1.5).toFixed(2))),
  role: employee?.role || 'staff',
});

const getPayrollSettings = (tenant) => ({
  defaultCycle: tenant?.payroll_settings?.default_cycle || 'weekly',
  payWeekStartDay: tenant?.payroll_settings?.pay_week_start_day || 'monday',
});

const printHtmlDocument = (html) => new Promise((resolve, reject) => {
  const frame = document.createElement('iframe');
  frame.style.position = 'fixed';
  frame.style.right = '0';
  frame.style.bottom = '0';
  frame.style.width = '0';
  frame.style.height = '0';
  frame.style.border = '0';
  frame.setAttribute('aria-hidden', 'true');
  document.body.appendChild(frame);

  const cleanup = () => {
    window.setTimeout(() => {
      frame.remove();
    }, 500);
  };

  try {
    const frameDocument = frame.contentWindow?.document;
    if (!frameDocument || !frame.contentWindow) {
      cleanup();
      reject(new Error('Unable to open print frame'));
      return;
    }

    frameDocument.open();
    frameDocument.write(html);
    frameDocument.close();

    frame.onload = () => {
      frame.contentWindow.focus();
      frame.contentWindow.print();
      cleanup();
      resolve();
    };
  } catch (error) {
    cleanup();
    reject(error);
  }
});

export default function Payroll() {
  const { hasPermission, isAdminOrOwner } = useAuth();
  const { api, employees, fetchEmployees, tenant } = useApp();
  const canViewPayroll = hasPermission(Permission.PAYROLL_VIEW);
  const canEditPayroll = isAdminOrOwner() || hasPermission(Permission.PAYROLL_EDIT);
  const payrollSettings = useMemo(() => getPayrollSettings(tenant), [tenant]);

  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [employeeDraft, setEmployeeDraft] = useState(normalizeEmployeeDraft(null));
  const [worksheetRows, setWorksheetRows] = useState([]);
  const [adjustmentRows, setAdjustmentRows] = useState(buildAdjustmentRows([]));
  const [legacyEntries, setLegacyEntries] = useState([]);
  const [report, setReport] = useState(null);
  const [timesheet, setTimesheet] = useState(null);
  const [signoff, setSignoff] = useState({ reviewed_by: '', review_date: '', approved_by: '', approval_date: '', payroll_notes: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState('');

  useEffect(() => {
    if (!canViewPayroll) return;
    fetchEmployees();
  }, [canViewPayroll, fetchEmployees]);

  useEffect(() => {
    if (!startDate || !endDate) {
      const range = getCurrentCycleRange({ cycle: payrollSettings.defaultCycle, payWeekStartDay: payrollSettings.payWeekStartDay });
      setStartDate(range.startDate);
      setEndDate(range.endDate);
    }
  }, [endDate, payrollSettings.defaultCycle, payrollSettings.payWeekStartDay, startDate]);

  useEffect(() => {
    if (!employees.length || selectedEmployeeId) return;
    setSelectedEmployeeId(employees[0].id);
  }, [employees, selectedEmployeeId]);

  const dateRange = useMemo(() => getDateRangeDates(startDate, endDate), [startDate, endDate]);

  const loadWorksheet = useCallback(async () => {
    if (!selectedEmployeeId || !canViewPayroll || !startDate || !endDate) return;
    setLoading(true);
    try {
      const params = { employee_id: selectedEmployeeId, start_date: startDate, end_date: endDate };
      const [employeeRes, shiftsRes, transactionsRes, reportRes, timesheetRes, signoffRes, legacyRes] = await Promise.all([
        api.get(`/employees/${selectedEmployeeId}`),
        api.get('/payroll/timeclock-shifts', { params }),
        api.get('/payroll/transactions', { params }),
        api.get('/payroll/report', { params }),
        api.get('/payroll/timesheet', { params }),
        api.get('/payroll/signoff', { params: { employee_id: selectedEmployeeId, week_start: startDate, period_end: endDate } }),
        api.get('/payroll/legacy-manual-entries', { params }),
      ]);

      setEmployeeDraft(normalizeEmployeeDraft(employeeRes.data));
      setWorksheetRows(buildWorksheetRows(startDate, endDate, shiftsRes.data || []));
      setAdjustmentRows(buildAdjustmentRows(transactionsRes.data || []));
      setReport(reportRes.data);
      setTimesheet(timesheetRes.data);
      setLegacyEntries(legacyRes.data || []);
      setSignoff({
        reviewed_by: signoffRes.data.reviewed_by || '',
        review_date: signoffRes.data.review_date || '',
        approved_by: signoffRes.data.approved_by || '',
        approval_date: signoffRes.data.approval_date || '',
        payroll_notes: signoffRes.data.payroll_notes || '',
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to load payroll worksheet');
    } finally {
      setLoading(false);
    }
  }, [api, canViewPayroll, endDate, selectedEmployeeId, startDate]);

  useEffect(() => {
    loadWorksheet();
  }, [loadWorksheet]);

  const worksheetSummary = useMemo(
    () => summarizeWorksheet(worksheetRows, Number(employeeDraft.hourly_rate || 0), Number(employeeDraft.overtime_rate || 0), payrollSettings.payWeekStartDay),
    [employeeDraft.hourly_rate, employeeDraft.overtime_rate, payrollSettings.payWeekStartDay, worksheetRows],
  );

  const adjustmentTotal = useMemo(() => getSignedAdjustmentTotal(adjustmentRows), [adjustmentRows]);
  const selectedTimesheetEmployee = timesheet?.employees?.[0];
  const carryoverBalance = selectedTimesheetEmployee?.carryover_balance || report?.employees?.[0]?.carryover_balance || 0;
  const legacyReview = useMemo(() => {
    const entries = selectedTimesheetEmployee?.entries || [];
    const timeClockByDate = entries
      .filter((entry) => entry.source === 'time_clock')
      .reduce((accumulator, entry) => {
        const dateKey = entry.date || entry.clock_in?.slice(0, 10) || 'unknown';
        accumulator[dateKey] = (accumulator[dateKey] || 0) + 1;
        return accumulator;
      }, {});
    const extraSameDayShiftCount = Object.values(timeClockByDate).reduce((sum, count) => sum + Math.max(count - 1, 0), 0);
    const unresolvedCount = legacyEntries.filter((entry) => !entry.resolution_saved).length;
    const unmappedHours = legacyEntries.reduce((sum, entry) => sum + Number(entry.current_effect_hours || 0), 0);
    const unmappedPay = legacyEntries.reduce((sum, entry) => sum + Number(entry.current_effect_pay || 0), 0);
    return {
      manualCount: legacyEntries.length,
      extraSameDayShiftCount,
      unresolvedCount,
      unmappedHours: Number(unmappedHours.toFixed(2)),
      unmappedPay: Number(unmappedPay.toFixed(2)),
      needsMigration: legacyEntries.length > 0 || extraSameDayShiftCount > 0,
    };
  }, [legacyEntries, selectedTimesheetEmployee]);

  const readOnlyLocked = !canEditPayroll;

  const handlePresetChange = (preset) => {
    const nextRange = getPresetDateRange(preset, payrollSettings);
    setStartDate(nextRange.startDate);
    setEndDate(nextRange.endDate);
  };

  const handleRowChange = (index, field, value) => {
    setWorksheetRows((currentRows) => currentRows.map((row, rowIndex) => {
      if (rowIndex !== index) return row;
      const nextRow = { ...row, [field]: value };
      if (field === 'date') {
        const matched = getDateRangeDates(value, value)[0];
        nextRow.dayLabel = matched?.dayLabel || row.dayLabel;
      }
      return nextRow;
    }));
  };

  const handleAdjustmentChange = (index, field, value) => {
    setAdjustmentRows((currentRows) => currentRows.map((row, rowIndex) => (
      rowIndex === index ? { ...row, [field]: value } : row
    )));
  };

  const handleLegacyEntryChange = (index, field, value) => {
    setLegacyEntries((currentEntries) => currentEntries.map((entry, entryIndex) => (
      entryIndex === index ? { ...entry, [field]: value } : entry
    )));
  };

  const fetchExportPayload = useCallback(async () => {
    const params = { employee_id: selectedEmployeeId, start_date: startDate, end_date: endDate };
    const [reportRes, timesheetRes] = await Promise.all([
      api.get('/payroll/report', { params }),
      api.get('/payroll/timesheet', { params }),
    ]);
    return { report: reportRes.data, timesheet: timesheetRes.data };
  }, [api, endDate, selectedEmployeeId, startDate]);

  const handleExportCsv = async () => {
    setExporting('csv');
    try {
      const payload = await fetchExportPayload();
      const csv = buildPayrollCsv({
        ...payload,
        selectedEmployeeLabel: employeeDraft.name || 'Selected employee',
        rangeLabel: `${startDate} — ${endDate}`,
      });
      downloadTextFile(`payroll-worksheet-${selectedEmployeeId}-${startDate}-${endDate}.csv`, csv, 'text/csv;charset=utf-8');
      toast.success('Payroll worksheet CSV exported');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to export worksheet');
    } finally {
      setExporting('');
    }
  };

  const handlePrint = async () => {
    setExporting('print');
    try {
      const payload = await fetchExportPayload();
      const html = buildPayrollPrintHtml({
        ...payload,
        selectedEmployeeLabel: employeeDraft.name || 'Selected employee',
        rangeLabel: `${startDate} — ${endDate}`,
      });
      await printHtmlDocument(html);
      toast.success('Printable payroll worksheet opened');
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to print worksheet');
    } finally {
      setExporting('');
    }
  };

  const validateRows = () => {
    if (!startDate || !endDate || endDate < startDate) {
      return 'Choose a valid payroll date range.';
    }
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
    if (!canEditPayroll) {
      toast.error('You do not have permission to edit payroll');
      return;
    }

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
          date: row.date || startDate,
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

      for (const entry of legacyEntries) {
        await api.put(`/payroll/legacy-manual-entries/${entry.id}/resolution`, {
          employee_id: selectedEmployeeId,
          week_start: startDate,
          period_end: endDate,
          handling_mode: entry.handling_mode,
          target_date: entry.target_date,
          admin_note: entry.admin_note,
        });
      }

      await api.put('/payroll/signoff', {
        employee_id: selectedEmployeeId,
        week_start: startDate,
        period_end: endDate,
        reviewed_by: signoff.reviewed_by,
        review_date: signoff.review_date || null,
        approved_by: signoff.approved_by,
        approval_date: signoff.approval_date || null,
        payroll_notes: signoff.payroll_notes,
      });

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
        <h1 className="text-4xl font-bold tracking-tight text-slate-900" data-testid="payroll-page-title">One practical payroll worksheet</h1>
        <p className="max-w-3xl text-sm text-slate-600" data-testid="payroll-page-subtitle">Choose any payroll date range, keep everything inline, and use weekly or biweekly presets only when they help.</p>
      </div>

      <div className="overflow-hidden rounded-[34px] border border-slate-300 bg-white shadow-[0_22px_55px_rgba(15,23,42,0.08)]" data-testid="payroll-worksheet-layout">
        <PayrollWorksheetToolbar
          employees={employees}
          employeeId={selectedEmployeeId}
          endDate={endDate}
          exporting={exporting}
          onEmployeeChange={setSelectedEmployeeId}
          onEndDateChange={setEndDate}
          onExportCsv={handleExportCsv}
          onPresetChange={handlePresetChange}
          onPrint={handlePrint}
          onSave={handleSaveWorksheet}
          onStartDateChange={setStartDate}
          saveDisabled={!canEditPayroll || saving || loading || !startDate || !endDate}
          saving={saving}
          startDate={startDate}
        />

        <div className="grid min-h-[880px] lg:grid-cols-[320px_1fr]">
          <PayrollAdjustmentsPanel rows={adjustmentRows} onChange={handleAdjustmentChange} readOnlyLocked={readOnlyLocked} total={adjustmentTotal} />

          <section className="bg-[#f8fbfb] p-5 lg:p-7" data-testid="payroll-worksheet-main">
            <div className="space-y-5 rounded-[30px] border border-slate-300 bg-white p-5 shadow-[inset_0_0_0_1px_rgba(148,163,184,0.16)] lg:p-7">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="payroll-meta-grid">
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-employee-name">Employee Name</Label>
                  <Input disabled={readOnlyLocked} id="payroll-meta-employee-name" value={employeeDraft.name} onChange={(event) => setEmployeeDraft((current) => ({ ...current, name: event.target.value }))} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid="payroll-meta-employee-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-title">Title</Label>
                  <Input disabled={readOnlyLocked} id="payroll-meta-title" value={employeeDraft.title} onChange={(event) => setEmployeeDraft((current) => ({ ...current, title: event.target.value }))} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid="payroll-meta-title-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-manager-name">Manager Name</Label>
                  <Input disabled={readOnlyLocked} id="payroll-meta-manager-name" value={employeeDraft.manager_name} onChange={(event) => setEmployeeDraft((current) => ({ ...current, manager_name: event.target.value }))} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid="payroll-meta-manager-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-start-date">Pay Period Start</Label>
                  <Input id="payroll-meta-start-date" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} data-testid="payroll-meta-start-date-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-end-date">Pay Period End</Label>
                  <Input id="payroll-meta-end-date" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} data-testid="payroll-meta-end-date-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-hourly-rate">Hourly Rate</Label>
                  <Input disabled={readOnlyLocked} id="payroll-meta-hourly-rate" type="number" step="0.01" value={employeeDraft.hourly_rate} onChange={(event) => setEmployeeDraft((current) => ({ ...current, hourly_rate: event.target.value }))} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid="payroll-meta-hourly-rate-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll-meta-overtime-rate">Overtime Rate</Label>
                  <Input disabled={readOnlyLocked} id="payroll-meta-overtime-rate" type="number" step="0.01" value={employeeDraft.overtime_rate} onChange={(event) => setEmployeeDraft((current) => ({ ...current, overtime_rate: event.target.value }))} className="disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500" data-testid="payroll-meta-overtime-rate-input" />
                </div>
              </div>

              {legacyReview.needsMigration ? (
                <PayrollLegacyEntriesSection
                  entries={legacyEntries}
                  readOnlyLocked={readOnlyLocked}
                  unresolvedCount={legacyReview.unresolvedCount}
                  totalHours={legacyReview.unmappedHours}
                  totalPay={legacyReview.unmappedPay}
                  weekDates={dateRange}
                  onEntryChange={handleLegacyEntryChange}
                />
              ) : (
                <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3" data-testid="payroll-legacy-review-clean">
                  <Info className="h-4 w-4 text-emerald-600" />
                  <p className="text-sm text-emerald-800">Current payroll records for this employee and selected date range map cleanly into the worksheet rows.</p>
                </div>
              )}

              <PayrollWeekTable rows={worksheetSummary.rows} onRowChange={handleRowChange} readOnlyLocked={readOnlyLocked} />

              <PayrollSignoffStrip
                readOnlyLocked={readOnlyLocked}
                signoff={signoff}
                onChange={(field, value) => setSignoff((current) => ({ ...current, [field]: value }))}
              />

              <div className="flex flex-wrap items-center gap-3" data-testid="payroll-worksheet-status-strip">
                <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700" data-testid="payroll-status-badge">{canEditPayroll ? 'Inline editing enabled' : 'Read only — worksheet locked'}</Badge>
                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700" data-testid="payroll-export-ready-badge">Export + print use the selected date range exactly as shown</Badge>
                <p className="text-sm text-slate-500" data-testid="payroll-week-range-label">{startDate} — {endDate}</p>
              </div>

              <PayrollWorksheetSummary
                adjustmentsTotal={adjustmentTotal}
                carryoverBalance={carryoverBalance}
                legacyManualHours={legacyReview.unmappedHours}
                legacyManualPay={legacyReview.unmappedPay}
                summary={worksheetSummary}
              />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}