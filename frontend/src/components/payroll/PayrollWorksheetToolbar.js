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
  exporting,
  onEmployeeChange,
  onExportCsv,
  onPrint,
  onSave,
  saveDisabled,
  saving,
  weekStart,
  onWeekChange,
}) => (
  <div className="grid gap-3 border-b border-slate-200 px-6 py-5 lg:grid-cols-[1.2fr_180px_auto] lg:items-end" data-testid="payroll-worksheet-toolbar">
    <div className="grid gap-3 md:grid-cols-2">
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
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Week Of</p>
        <div className="relative">
          <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input className="pl-9" type="date" value={weekStart} onChange={(event) => onWeekChange(event.target.value)} data-testid="payroll-worksheet-week-input" />
        </div>
      </div>
    </div>

    <div className="flex flex-wrap items-center gap-2 lg:justify-end">
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
