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

const formatSignedCurrency = (value) => {
  const amount = Number(value || 0);
  return `${amount >= 0 ? '+' : '-'}${currencyFormatter.format(Math.abs(amount))}`;
};

const formatHours = (value) => Number(value || 0).toFixed(2);

const formatHoursLabel = (minutes, fallback) => {
  if (typeof minutes === 'number') {
    const wholeMinutes = Math.round(minutes);
    const hours = Math.floor(wholeMinutes / 60);
    const remainingMinutes = wholeMinutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  }
  return fallback || '0h 0m';
};

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

const formatTimeOnly = (value) => {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(parsed);
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
    ['Employee', 'Hourly Rate', 'Total Time', 'Regular Time', 'Overtime Time', 'Carryover', 'Gross Pay', 'Earnings Adj.', 'Advances', 'Payments', 'Adjustments', 'Final Owed'],
  ];

  (report?.employees || []).forEach((employee) => {
    rows.push([
      employee.employee_name,
      formatCurrency(employee.hourly_rate),
      employee.total_hours_label || formatHoursLabel(employee.total_minutes, employee.total_hours_label),
      employee.regular_hours_label || formatHoursLabel(employee.regular_minutes, employee.regular_hours_label),
      employee.overtime_hours_label || formatHoursLabel(employee.overtime_minutes, employee.overtime_hours_label),
      formatCurrency(employee.carryover_balance),
      formatCurrency(employee.gross_pay ?? employee.earnings),
      formatCurrency(employee.earnings_adjustments),
      formatCurrency(employee.advances),
      formatCurrency(employee.payments),
      formatSignedCurrency(employee.adjustments_total),
      formatCurrency(employee.final_owed ?? employee.balance),
    ]);
  });

  rows.push([]);
  rows.push(['Daily Breakdown']);
  rows.push(['Employee', 'Day', 'Date', 'Worked Time', 'Break Time', 'Daily Pay', 'Daily Adjustments', 'Daily Final']);

  (timesheet?.employees || []).forEach((employee) => {
    (employee.daily_breakdown || []).forEach((day) => {
      rows.push([
        employee.employee_name,
        day.day_name,
        day.date,
        day.total_hours_label || formatHoursLabel(day.total_minutes, day.total_hours_label),
        day.break_label || formatHoursLabel(day.break_minutes, day.break_label),
        formatCurrency(day.daily_pay),
        formatSignedCurrency(day.daily_adjustments),
        formatCurrency(day.daily_final),
      ]);
    });
  });

  rows.push([]);
  rows.push(['Entry Details']);
  rows.push(['Employee', 'Day', 'Date', 'Source', 'Task', 'Order', 'Description', 'Worked Time', 'Clock In', 'Clock Out', 'Break Time', 'Pay']);

  let hasEntries = false;
  (timesheet?.employees || []).forEach((employee) => {
    (employee.entries || []).forEach((entry) => {
      hasEntries = true;
      rows.push([
        employee.employee_name,
        entry.date ? new Date(`${entry.date}T00:00:00`).toLocaleDateString('en-US', { weekday: 'long' }) : '',
        entry.date || '',
        getSourceLabel(entry.source),
        entry.task_type || '',
        entry.job_name || '',
        entry.description || '',
        entry.hours_minutes_label || formatHoursLabel(entry.minutes, entry.hours_minutes_label),
        formatTimeOnly(entry.clock_in),
        formatTimeOnly(entry.clock_out),
        entry.break_label || formatHoursLabel(entry.break_minutes, entry.break_label),
        formatCurrency(entry.pay),
      ]);
    });
  });

  if (!hasEntries) {
    rows.push(['No entries found for the selected range']);
  }

  rows.push([]);
  rows.push(['Transactions']);
  rows.push(['Employee', 'Date', 'Type', 'Description', 'Amount', 'Signed Impact']);

  (report?.employees || []).forEach((employee) => {
    (employee.transactions || []).forEach((transaction) => {
      rows.push([
        employee.employee_name,
        transaction.date || '',
        transaction.type || '',
        transaction.description || '',
        formatCurrency(transaction.amount),
        formatSignedCurrency(transaction.signed_amount),
      ]);
    });
  });

  return rows.map((row) => row.map(toCsvValue).join(',')).join('\n');
};

export const buildPayrollPrintHtml = ({ report, timesheet, selectedEmployeeLabel, rangeLabel }) => {
  const summaryRows = (report?.employees || []).map((employee) => `
    <tr>
      <td>${escapeHtml(employee.employee_name)}</td>
      <td>${escapeHtml(formatCurrency(employee.hourly_rate))}</td>
      <td>${escapeHtml(employee.total_hours_label || formatHoursLabel(employee.total_minutes, employee.total_hours_label))}</td>
      <td>${escapeHtml(employee.regular_hours_label || formatHoursLabel(employee.regular_minutes, employee.regular_hours_label))}</td>
      <td>${escapeHtml(employee.overtime_hours_label || formatHoursLabel(employee.overtime_minutes, employee.overtime_hours_label))}</td>
      <td>${escapeHtml(formatCurrency(employee.carryover_balance))}</td>
      <td>${escapeHtml(formatCurrency(employee.gross_pay ?? employee.earnings))}</td>
      <td>${escapeHtml(formatCurrency(employee.earnings_adjustments))}</td>
      <td>${escapeHtml(formatCurrency(employee.advances))}</td>
      <td>${escapeHtml(formatCurrency(employee.payments))}</td>
      <td>${escapeHtml(formatSignedCurrency(employee.adjustments_total))}</td>
      <td>${escapeHtml(formatCurrency(employee.final_owed ?? employee.balance))}</td>
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
        <td>${escapeHtml(entry.hours_minutes_label || formatHoursLabel(entry.minutes, entry.hours_minutes_label))}</td>
        <td>${escapeHtml(formatTimeOnly(entry.clock_in))}</td>
        <td>${escapeHtml(formatTimeOnly(entry.clock_out))}</td>
        <td>${escapeHtml(entry.break_label || formatHoursLabel(entry.break_minutes, entry.break_label))}</td>
        <td>${escapeHtml(formatCurrency(entry.pay))}</td>
      </tr>
    `).join('');

    const dailyRows = (employee.daily_breakdown || []).map((day) => `
      <tr>
        <td>${escapeHtml(day.day_name)}</td>
        <td>${escapeHtml(day.date || '—')}</td>
        <td>${escapeHtml(day.total_hours_label || formatHoursLabel(day.total_minutes, day.total_hours_label))}</td>
        <td>${escapeHtml(day.break_label || formatHoursLabel(day.break_minutes, day.break_label))}</td>
        <td>${escapeHtml(formatCurrency(day.daily_pay))}</td>
        <td>${escapeHtml(formatSignedCurrency(day.daily_adjustments))}</td>
        <td>${escapeHtml(formatCurrency(day.daily_final))}</td>
      </tr>
    `).join('');

    const transactionRows = ((employee.transaction_summary?.transactions) || []).map((transaction) => `
      <tr>
        <td>${escapeHtml(transaction.date || '—')}</td>
        <td>${escapeHtml(transaction.type || '—')}</td>
        <td>${escapeHtml(transaction.description || '—')}</td>
        <td>${escapeHtml(formatCurrency(transaction.amount))}</td>
        <td>${escapeHtml(formatSignedCurrency(transaction.signed_amount))}</td>
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
            <span><strong>${escapeHtml(employee.total_hours_label || formatHoursLabel(employee.total_minutes, employee.total_hours_label))}</strong></span>
            <span><strong>${escapeHtml(formatCurrency(employee.total_pay))}</strong> gross</span>
            <span><strong>${escapeHtml(formatCurrency(employee.final_owed))}</strong> owed</span>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Day</th>
              <th>Date</th>
              <th>Worked</th>
              <th>Break</th>
              <th>Daily Pay</th>
              <th>Daily Adj.</th>
              <th>Daily Final</th>
            </tr>
          </thead>
          <tbody>
            ${dailyRows || '<tr><td colspan="7">No daily breakdown found.</td></tr>'}
          </tbody>
        </table>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Source</th>
              <th>Task</th>
              <th>Order</th>
              <th>Description</th>
              <th>Worked</th>
              <th>In</th>
              <th>Out</th>
              <th>Break</th>
              <th>Pay</th>
            </tr>
          </thead>
          <tbody>
            ${entryRows || '<tr><td colspan="10">No entries found for this employee.</td></tr>'}
          </tbody>
        </table>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Impact</th>
            </tr>
          </thead>
          <tbody>
            ${transactionRows || '<tr><td colspan="5">No transactions found for this employee.</td></tr>'}
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
        /* Hard reset: iframe inherits styles from the parent app.
           Force every element in the export to render as plain solid text
           so nothing comes through as outline / transparent / hollow. */
        *, *::before, *::after {
          -webkit-text-stroke: 0 !important;
          -webkit-text-fill-color: currentColor !important;
          text-shadow: none !important;
          text-decoration: none !important;
          background-clip: border-box !important;
          -webkit-background-clip: border-box !important;
          font-variation-settings: normal !important;
          filter: none !important;
        }
        html, body {
          font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif !important;
          color: #0f172a !important;
          background: #ffffff !important;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        body { margin: 32px; }
        h1, h2, h3, h4, p, span, strong, div, th, td {
          font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif !important;
          color: #0f172a !important;
        }
        h1 { font-size: 26px; font-weight: 700 !important; }
        h2 { font-size: 18px; font-weight: 700 !important; }
        h3 { font-size: 15px; font-weight: 700 !important; }
        strong { font-weight: 700 !important; }
        h1, h2, h3, p { margin: 0; }
        .page-header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 24px; }
        .meta { color: #334155 !important; font-size: 13px; display: grid; gap: 6px; }
        .summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px; }
        .summary-card { border: 1px solid #64748b; border-radius: 10px; padding: 14px 16px; background: #ffffff !important; }
        .summary-card span { display: block; color: #1e293b !important; font-size: 11px; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
        .summary-card strong { font-size: 20px; font-weight: 700 !important; color: #0f172a !important; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #94a3b8; font-size: 13px; vertical-align: top; }
        thead th {
          background: #e2e8f0 !important;
          color: #0f172a !important;
          font-weight: 700 !important;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-size: 11px;
        }
        .employee-section { margin-top: 28px; page-break-inside: avoid; }
        .employee-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-end; margin-bottom: 8px; }
        .employee-header p { color: #334155 !important; margin-top: 4px; font-weight: 500; }
        .employee-totals { display: flex; gap: 16px; color: #0f172a !important; font-size: 13px; font-weight: 600; }
        @media print {
          body { margin: 20px; }
          .summary-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
          /* Belt-and-suspenders: re-assert solid fill at print time */
          *, *::before, *::after {
            -webkit-text-stroke: 0 !important;
            -webkit-text-fill-color: currentColor !important;
            text-shadow: none !important;
          }
        }
      </style>
    </head>
    <body>
      <header class="page-header">
        <div>
          <p style="color:#1e293b !important; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px; -webkit-text-fill-color:#1e293b;">Payroll export</p>
          <h1>Payroll Report</h1>
        </div>
        <div class="meta">
          <div><strong>Scope:</strong> ${escapeHtml(selectedEmployeeLabel)}</div>
          <div><strong>Range:</strong> ${escapeHtml(rangeLabel)}</div>
          <div><strong>Generated:</strong> ${escapeHtml(dateTimeFormatter.format(new Date()))}</div>
        </div>
      </header>

      <section class="summary-grid">
        <div class="summary-card"><span>Total Time</span><strong>${escapeHtml(report?.totals?.total_hours_label || formatHoursLabel(report?.totals?.total_minutes, report?.totals?.total_hours_label))}</strong></div>
        <div class="summary-card"><span>Gross Pay</span><strong>${escapeHtml(formatCurrency(report?.totals?.earnings))}</strong></div>
        <div class="summary-card"><span>Carryover</span><strong>${escapeHtml(formatCurrency(report?.totals?.carryover_balance))}</strong></div>
        <div class="summary-card"><span>Adjustments</span><strong>${escapeHtml(formatSignedCurrency(report?.totals?.adjustments_total))}</strong></div>
        <div class="summary-card"><span>Final Owed</span><strong>${escapeHtml(formatCurrency(report?.totals?.final_owed ?? report?.totals?.balance))}</strong></div>
      </section>

      <section>
        <h2>Payroll Summary</h2>
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Rate</th>
              <th>Total Time</th>
              <th>Regular</th>
              <th>OT</th>
              <th>Carryover</th>
              <th>Gross Pay</th>
              <th>Earnings Adj.</th>
              <th>Advances</th>
              <th>Payments</th>
              <th>Adjustments</th>
              <th>Final Owed</th>
            </tr>
          </thead>
          <tbody>
            ${summaryRows || '<tr><td colspan="11">No payroll data found for the selected range.</td></tr>'}
          </tbody>
        </table>
      </section>

      ${employeeSections || '<section class="employee-section"><h2>Time Details</h2><p>No entries found for the selected range.</p></section>'}
    </body>
  </html>`;
};