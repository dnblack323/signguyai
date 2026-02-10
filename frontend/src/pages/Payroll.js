import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
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
} from '../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { formatCurrency, formatDate } from '../lib/utils';
import { DollarSign, Plus, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const transactionTypes = ['earnings', 'advance', 'payment'];

export default function Payroll() {
  const { hasPermission } = useAuth();
  const canViewPayroll = hasPermission(Permission.PAYROLL_VIEW);
  const canEditPayroll = hasPermission(Permission.PAYROLL_EDIT);
  
  const { 
    employees, fetchEmployees,
    createPayrollTransaction, getPayrollTransactions, 
    getPayrollBalance, getPayrollReport 
  } = useApp();
  
  // Permission denied view
  if (!canViewPayroll) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4" style={{ color: '#d97706' }} />
        <h2 className="text-xl font-semibold mb-2" style={{ color: '#1A1A1A' }}>Access Denied</h2>
        <p style={{ color: '#5A5A5A' }}>You don't have permission to view payroll.</p>
      </div>
    );
  }
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [balance, setBalance] = useState(null);
  const [report, setReport] = useState([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [formData, setFormData] = useState({
    employee_id: '',
    type: 'earnings',
    amount: 0,
    description: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      loadEmployeeData();
    }
  }, [selectedEmployee]);

  useEffect(() => {
    loadReport();
  }, [dateRange]);

  const loadData = async () => {
    setLoading(true);
    await fetchEmployees();
    setLoading(false);
  };

  const loadEmployeeData = async () => {
    if (!selectedEmployee) return;
    try {
      const [txns, bal] = await Promise.all([
        getPayrollTransactions({ employee_id: selectedEmployee }),
        getPayrollBalance(selectedEmployee)
      ]);
      setTransactions(txns);
      setBalance(bal);
    } catch (err) {
      console.error('Error loading payroll data:', err);
    }
  };

  const loadReport = async () => {
    try {
      const reportData = await getPayrollReport(dateRange.start, dateRange.end);
      setReport(reportData);
    } catch (err) {
      console.error('Error loading report:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.employee_id) {
      toast.error('Please select an employee');
      return;
    }
    if (formData.amount <= 0) {
      toast.error('Amount must be greater than 0');
      return;
    }
    try {
      await createPayrollTransaction(formData);
      toast.success('Transaction recorded');
      setIsDialogOpen(false);
      setFormData({
        employee_id: '',
        type: 'earnings',
        amount: 0,
        description: '',
        date: new Date().toISOString().split('T')[0]
      });
      if (selectedEmployee === formData.employee_id) {
        await loadEmployeeData();
      }
      await loadReport();
    } catch (err) {
      toast.error('Failed to record transaction');
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'earnings': return <TrendingUp className="h-4 w-4 text-green-400" />;
      case 'advance': return <Minus className="h-4 w-4 text-yellow-400" />;
      case 'payment': return <TrendingDown className="h-4 w-4 text-blue-400" />;
      default: return null;
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'earnings': return 'text-green-400';
      case 'advance': return 'text-yellow-400';
      case 'payment': return 'text-blue-400';
      default: return '';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Payroll</h1>
          <p className="text-muted-foreground mt-1">Manage employee earnings and payments</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-transaction-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Transaction
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">New Transaction</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Employee *</Label>
                <Select
                  value={formData.employee_id}
                  onValueChange={(val) => setFormData({ ...formData, employee_id: val })}
                >
                  <SelectTrigger data-testid="payroll-employee-select">
                    <SelectValue placeholder="Select employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees.map((emp) => (
                      <SelectItem key={emp.id} value={emp.id}>
                        {emp.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Type *</Label>
                  <Select
                    value={formData.type}
                    onValueChange={(val) => setFormData({ ...formData, type: val })}
                  >
                    <SelectTrigger data-testid="payroll-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {transactionTypes.map((t) => (
                        <SelectItem key={t} value={t}>
                          {t.charAt(0).toUpperCase() + t.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Amount *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                    data-testid="payroll-amount-input"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Date</Label>
                <Input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  data-testid="payroll-date-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional notes"
                  data-testid="payroll-description-input"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="payroll-submit-btn">Record</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Employee Selector & Balance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-card border-border/50 lg:col-span-2">
          <CardHeader>
            <CardTitle className="font-heading uppercase">Employee Ledger</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Select value={selectedEmployee} onValueChange={setSelectedEmployee}>
                <SelectTrigger data-testid="ledger-employee-select">
                  <SelectValue placeholder="Select employee to view ledger" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedEmployee && balance && (
                <div className="grid grid-cols-4 gap-3">
                  <div className="p-3 bg-green-500/10 rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Earnings</p>
                    <p className="text-lg font-bold text-green-400">
                      {formatCurrency(balance.total_earnings)}
                    </p>
                  </div>
                  <div className="p-3 bg-yellow-500/10 rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Advances</p>
                    <p className="text-lg font-bold text-yellow-400">
                      {formatCurrency(balance.total_advances)}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-lg text-center">
                    <p className="text-xs text-muted-foreground">Payments</p>
                    <p className="text-lg font-bold text-blue-400">
                      {formatCurrency(balance.total_payments)}
                    </p>
                  </div>
                  <div className={`p-3 rounded-lg text-center ${balance.balance >= 0 ? 'bg-primary/10' : 'bg-red-500/10'}`}>
                    <p className="text-xs text-muted-foreground">Balance</p>
                    <p className={`text-lg font-bold ${balance.balance >= 0 ? 'text-primary' : 'text-red-400'}`}>
                      {formatCurrency(balance.balance)}
                    </p>
                  </div>
                </div>
              )}

              {selectedEmployee && transactions.length > 0 && (
                <div className="max-h-[300px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {transactions.map((txn, idx) => (
                        <TableRow key={txn.id} className={idx % 2 === 0 ? '' : 'bg-muted/30'}>
                          <TableCell className="text-sm">{formatDate(txn.date)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {getTypeIcon(txn.type)}
                              <span className="capitalize">{txn.type}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {txn.description || '-'}
                          </TableCell>
                          <TableCell className={`text-right font-bold ${getTypeColor(txn.type)}`}>
                            {formatCurrency(txn.amount)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Balance Explanation */}
        <Card className="bg-card border-border/50">
          <CardHeader>
            <CardTitle className="font-heading uppercase flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary" />
              Balance Info
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="p-3 bg-muted/30 rounded-lg">
              <p className="font-medium text-green-400">Earnings</p>
              <p className="text-muted-foreground">Hours × Rate = Money owed to employee</p>
            </div>
            <div className="p-3 bg-muted/30 rounded-lg">
              <p className="font-medium text-yellow-400">Advances</p>
              <p className="text-muted-foreground">Money borrowed by employee (reduces balance)</p>
            </div>
            <div className="p-3 bg-muted/30 rounded-lg">
              <p className="font-medium text-blue-400">Payments</p>
              <p className="text-muted-foreground">Wages paid to employee (reduces balance)</p>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg border border-primary/30">
              <p className="font-medium text-primary">Balance Formula</p>
              <p className="text-muted-foreground">Earnings - Advances - Payments</p>
              <p className="text-xs mt-2 text-muted-foreground">
                Positive = Employer owes employee<br/>
                Negative = Employee overpaid
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payroll Report */}
      <Card className="bg-card border-border/50">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="font-heading uppercase">Payroll Report</CardTitle>
            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                className="w-[150px]"
                data-testid="report-start-date"
              />
              <span className="text-muted-foreground">to</span>
              <Input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                className="w-[150px]"
                data-testid="report-end-date"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {report.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No data for selected period</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead className="text-right">Earnings</TableHead>
                  <TableHead className="text-right">Advances</TableHead>
                  <TableHead className="text-right">Payments</TableHead>
                  <TableHead className="text-right">Period Balance</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.map((row, idx) => (
                  <TableRow key={row.employee_id} className={idx % 2 === 0 ? '' : 'bg-muted/30'}>
                    <TableCell className="font-medium">{row.employee_name}</TableCell>
                    <TableCell className="text-right text-green-400">
                      {formatCurrency(row.period_earnings)}
                    </TableCell>
                    <TableCell className="text-right text-yellow-400">
                      {formatCurrency(row.period_advances)}
                    </TableCell>
                    <TableCell className="text-right text-blue-400">
                      {formatCurrency(row.period_payments)}
                    </TableCell>
                    <TableCell className={`text-right font-bold ${row.period_balance >= 0 ? 'text-primary' : 'text-red-400'}`}>
                      {formatCurrency(row.period_balance)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
