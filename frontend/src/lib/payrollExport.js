const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

const dateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
});

const toInputDate = (value) => value.toISOString().split('T')[0];

const shiftDate = (value, days) => {
  const next = new Date(value);
  next.setDate(next.getDate() + days);
  return next;
};

const getWeekStartDate = (reference) => {
  const day = reference.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  return shiftDate(reference, mondayOffset);
};

const formatCurrency = (value) => currencyFormatter.format(Number(value || 0));

const formatHours = (value) => Number(value || 0).toFixed(2);

const formatDateTime = (value) => {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return dateTimeFormatter.format(parsed);
};

const escapeHtml = (value) => String(value ?? '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#39;');

const toCsvValue = (value) => {
  const normalized = String(value ?? '');
  if (/[",\n]/.test(normalized)) {
    return `"${normalized.replaceAll('"', '""')}"`;
  }
  return normalized;
};

const getSourceLabel = (source) => {
  if (source === 'job_timer') return 'Timer';
  if (source === 'time_clock') return 'Time Clock';
  if (source === 'manual') return 'Manual';
  return source || '—';
};

export const getPresetDateRange = (preset, reference = new Date()) => {
  const weekStart = getWeekStartDate(reference);

  if (preset === 'biweekly') {
    const start = shiftDate(weekStart, -7);
    return {
      start: toInputDate(start),
      end: toInputDate(shiftDate(start, 13)),
    };
  }

  return {
    start: toInputDate(weekStart),
    end: toInputDate(shiftDate(weekStart, 6)),
  };
};

export const formatPayrollRangeLabel = ({ start, end }) => {
  if (!start || !end) return 'Custom range';

  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return `${start} to ${end}`;
  }

  return `${dateFormatter.format(startDate)} — ${dateFormatter.format(endDate)}`;
};

export const downloadTextFile = (filename, text, mimeType = 'text/plain;charset=utf-8') => {
  const blob = new Blob([text], { type: mimeType });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

export const buildPayrollCsv = ({ report, timesheet, selectedEmployeeLabel, rangeLabel }) => {
  const rows = [
    ['Payroll Report'],
    ['Employee Scope', selectedEmployeeLabel, 'Date Range', rangeLabel],
    [],
    ['Summary'],
    ['Employee', 'Hourly Rate', 'Total Hours', 'Regular Hours', 'Overtime Hours', 'Gross Pay', 'Advances', 'Payments', 'Balance'],
  ];

  (report?.employees || []).forEach((employee) => {
    rows.push([
      employee.employee_name,
      formatCurrency(employee.hourly_rate),
      formatHours(employee.hours),
      formatHours(employee.regular_hours),
      formatHours(employee.overtime_hours),
      formatCurrency(employee.gross_pay ?? employee.earnings),
      formatCurrency(employee.advances),
      formatCurrency(employee.payments),
      formatCurrency(employee.balance),
    ]);
  });

  rows.push([]);
  rows.push(['Entry Details']);
  rows.push(['Employee', 'Date', 'Source', 'Task', 'Job', 'Description', 'Hours', 'Pay', 'Clock In', 'Clock Out', 'Break Minutes']);

  let hasEntries = false;
  (timesheet?.employees || []).forEach((employee) => {
    (employee.entries || []).forEach((entry) => {
      hasEntries = true;
      rows.push([
        employee.employee_name,
        entry.date || '',
        getSourceLabel(entry.source),
        entry.task_type || '',
        entry.job_name || '',
        entry.description || '',
        formatHours(entry.hours),
        formatCurrency(entry.pay),
        formatDateTime(entry.clock_in),
        formatDateTime(entry.clock_out),
        entry.break_minutes || 0,
      ]);
    });
  });

  if (!hasEntries) {
    rows.push(['No entries found for the selected range']);
  }

  return rows.map((row) => row.map(toCsvValue).join(',')).join('\n');
};

export const buildPayrollPrintHtml = ({ report, timesheet, selectedEmployeeLabel, rangeLabel }) => {
  const summaryRows = (report?.employees || []).map((employee) => `
    <tr>
      <td>${escapeHtml(employee.employee_name)}</td>
      <td>${escapeHtml(formatCurrency(employee.hourly_rate))}</td>
      <td>${escapeHtml(formatHours(employee.hours))}</td>
      <td>${escapeHtml(formatHours(employee.regular_hours))}</td>
      <td>${escapeHtml(formatHours(employee.overtime_hours))}</td>
      <td>${escapeHtml(formatCurrency(employee.gross_pay ?? employee.earnings))}</td>
      <td>${escapeHtml(formatCurrency(employee.advances))}</td>
      <td>${escapeHtml(formatCurrency(employee.payments))}</td>
      <td>${escapeHtml(formatCurrency(employee.balance))}</td>
    </tr>
  `).join('');

  const employeeSections = (timesheet?.employees || []).map((employee) => {
    const entryRows = (employee.entries || []).map((entry) => `
      <tr>
        <td>${escapeHtml(entry.date || '—')}</td>
        <td>${escapeHtml(getSourceLabel(entry.source))}</td>
        <td>${escapeHtml(entry.task_type || '—')}</td>
        <td>${escapeHtml(entry.job_name || '—')}</td>
        <td>${escapeHtml(entry.description || '—')}</td>
        <td>${escapeHtml(formatHours(entry.hours))}</td>
        <td>${escapeHtml(formatCurrency(entry.pay))}</td>
      </tr>
    `).join('');

    return `
      <section class="employee-section">
        <div class="employee-header">
          <div>
            <h3>${escapeHtml(employee.employee_name)}</h3>
            <p>${escapeHtml(formatCurrency(employee.hourly_rate))}/hr</p>
          </div>
          <div class="employee-totals">
            <span><strong>${escapeHtml(formatHours(employee.total_hours))}</strong> hrs</span>
            <span><strong>${escapeHtml(formatCurrency(employee.total_pay))}</strong> pay</span>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Source</th>
              <th>Task</th>
              <th>Job</th>
              <th>Description</th>
              <th>Hours</th>
              <th>Pay</th>
            </tr>
          </thead>
          <tbody>
            ${entryRows || '<tr><td colspan="7">No entries found for this employee.</td></tr>'}
          </tbody>
        </table>
      </section>
    `;
  }).join('');

  return `<!doctype html>
  <html>
    <head>
      <meta charset="utf-8" />
      <title>Payroll Report</title>
      <style>
        body { font-family: "Helvetica Neue", Arial, sans-serif; margin: 32px; color: #0f172a; }
        h1, h2, h3, p { margin: 0; }
        .page-header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 24px; }
        .meta { color: #475569; font-size: 13px; display: grid; gap: 6px; }
        .summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }
        .summary-card { border: 1px solid #cbd5e1; border-radius: 14px; padding: 14px 16px; background: #f8fafc; }
        .summary-card span { display: block; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
        .summary-card strong { font-size: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-size: 13px; vertical-align: top; }
        thead th { background: #eff6ff; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; }
        .employee-section { margin-top: 28px; page-break-inside: avoid; }
        .employee-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 8px; }
        .employee-header p { color: #64748b; margin-top: 4px; }
        .employee-totals { display: flex; gap: 16px; color: #0f172a; font-size: 13px; }
        @media print {
          body { margin: 20px; }
          .summary-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
      </style>
    </head>
    <body>
      <header class="page-header">
        <div>
          <p style="color:#2563eb; font-size:12px; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">Payroll export</p>
          <h1>Payroll Report</h1>
        </div>
        <div class="meta">
          <div><strong>Scope:</strong> ${escapeHtml(selectedEmployeeLabel)}</div>
          <div><strong>Range:</strong> ${escapeHtml(rangeLabel)}</div>
          <div><strong>Generated:</strong> ${escapeHtml(dateTimeFormatter.format(new Date()))}</div>
        </div>
      </header>

      <section class="summary-grid">
        <div class="summary-card"><span>Total Hours</span><strong>${escapeHtml(formatHours(report?.totals?.hours))}</strong></div>
        <div class="summary-card"><span>Gross Pay</span><strong>${escapeHtml(formatCurrency(report?.totals?.earnings))}</strong></div>
        <div class="summary-card"><span>Advances</span><strong>${escapeHtml(formatCurrency(report?.totals?.advances))}</strong></div>
        <div class="summary-card"><span>Balance</span><strong>${escapeHtml(formatCurrency(report?.totals?.balance))}</strong></div>
      </section>

      <section>
        <h2>Payroll Summary</h2>
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Rate</th>
              <th>Total Hours</th>
              <th>Regular</th>
              <th>OT</th>
              <th>Gross Pay</th>
              <th>Advances</th>
              <th>Payments</th>
              <th>Balance</th>
            </tr>
          </thead>
          <tbody>
            ${summaryRows || '<tr><td colspan="9">No payroll data found for the selected range.</td></tr>'}
          </tbody>
        </table>
      </section>

      ${employeeSections || '<section class="employee-section"><h2>Time Details</h2><p>No entries found for the selected range.</p></section>'}
    </body>
  </html>`;
};