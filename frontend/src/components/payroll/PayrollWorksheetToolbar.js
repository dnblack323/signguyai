import { CalendarDays, Download, Loader2, Printer, Save } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';

export const PayrollWorksheetToolbar = ({
  employees,
  employeeId,
  endDate,
  exporting,
  onEmployeeChange,
  onEndDateChange,
  onExportCsv,
  onPresetChange,
  onPrint,
  onSave,
  onStartDateChange,
  saveDisabled,
  saving,
  startDate,
}) => (
  <div className="grid gap-4 border-b border-slate-200 px-6 py-5 xl:grid-cols-[1.15fr_1.2fr_auto] xl:items-end" data-testid="payroll-worksheet-toolbar">
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Employee</p>
      <Select value={employeeId || ''} onValueChange={onEmployeeChange}>
        <SelectTrigger data-testid="payroll-worksheet-employee-select">
          <SelectValue placeholder="Select employee" />
        </SelectTrigger>
        <SelectContent>
          {employees.map((employee) => (
            <SelectItem key={employee.id} value={employee.id}>{employee.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>

    <div className="grid gap-3 md:grid-cols-[170px_170px_1fr]">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Start Date</p>
        <div className="relative">
          <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input className="pl-9" type="date" value={startDate} onChange={(event) => onStartDateChange(event.target.value)} data-testid="payroll-worksheet-start-date-input" />
        </div>
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">End Date</p>
        <div className="relative">
          <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input className="pl-9" type="date" value={endDate} onChange={(event) => onEndDateChange(event.target.value)} data-testid="payroll-worksheet-end-date-input" />
        </div>
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Quick Fill</p>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => onPresetChange('weekly')} data-testid="payroll-worksheet-preset-weekly-button">Weekly</Button>
          <Button type="button" variant="outline" onClick={() => onPresetChange('biweekly')} data-testid="payroll-worksheet-preset-biweekly-button">Biweekly</Button>
          <Button type="button" variant="outline" onClick={() => onPresetChange('current-cycle')} data-testid="payroll-worksheet-preset-current-cycle-button">Current Cycle</Button>
        </div>
      </div>
    </div>

    <div className="flex flex-wrap items-center gap-2 xl:justify-end">
      <Button variant="outline" onClick={onExportCsv} disabled={exporting !== ''} data-testid="payroll-worksheet-export-csv-button">
        {exporting === 'csv' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}Export CSV
      </Button>
      <Button variant="outline" onClick={onPrint} disabled={exporting !== ''} data-testid="payroll-worksheet-print-button">
        {exporting === 'print' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Printer className="mr-2 h-4 w-4" />}Print
      </Button>
      <Button onClick={onSave} disabled={saveDisabled} data-testid="payroll-worksheet-save-button">
        {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}Save Worksheet
      </Button>
    </div>
  </div>
);