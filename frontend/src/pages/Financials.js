import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { formatCurrency, formatDate } from '../lib/utils';
import { Plus, TrendingUp, TrendingDown, Receipt, DollarSign, Wallet, CreditCard, Mail, Banknote } from 'lucide-react';
import { toast } from 'sonner';

const expenseCategories = [
  { value: 'materials', label: 'Materials' },
  { value: 'labor', label: 'Labor' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'rent', label: 'Rent' },
  { value: 'insurance', label: 'Insurance' },
  { value: 'cell_phone', label: 'Cell Phone' },
  { value: 'garbage', label: 'Garbage' },
  { value: 'printing_supplies', label: 'Printing Supplies' },
  { value: 'meals', label: 'Meals' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'donations', label: 'Donations' },
  { value: 'office_supplies', label: 'Office Supplies' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'vehicle', label: 'Vehicle' },
  { value: 'advertising', label: 'Advertising' },
  { value: 'legal', label: 'Legal' },
  { value: 'repairs', label: 'Repairs' },
  { value: 'taxes', label: 'Taxes' },
  { value: 'travel', label: 'Travel' },
  { value: 'other', label: 'Other' },
];
const paymentMethods = [
  { value: 'cash', label: 'Cash', icon: Banknote },
  { value: 'credit', label: 'Credit/Debit Card', icon: CreditCard },
  { value: 'check', label: 'Check', icon: Mail },
  { value: 'other', label: 'Other', icon: Wallet }
];

// Helper to get category label
const getCategoryLabel = (value) => {
  const cat = expenseCategories.find(c => c.value === value);
  return cat ? cat.label : value;
};

export default function Financials() {
  const { 
    createSalesEntry, getSalesEntries, 
    createExpenseEntry, getExpenseEntries,
    getFinancialSummary
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [sales, setSales] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [isSalesDialogOpen, setIsSalesDialogOpen] = useState(false);
  const [isExpenseDialogOpen, setIsExpenseDialogOpen] = useState(false);
  const [salesForm, setSalesForm] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: 0,
    tax_amount: 0,
    payment_method: 'cash',
    description: ''
  });
  const [expenseForm, setExpenseForm] = useState({
    date: new Date().toISOString().split('T')[0],
    amount: 0,
    category: 'materials',
    description: ''
  });

  useEffect(() => {
    loadData();
  }, [dateRange]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [salesData, expensesData, summaryData] = await Promise.all([
        getSalesEntries({ start_date: dateRange.start, end_date: dateRange.end }),
        getExpenseEntries({ start_date: dateRange.start, end_date: dateRange.end }),
        getFinancialSummary(dateRange.start, dateRange.end)
      ]);
      setSales(salesData);
      setExpenses(expensesData);
      setSummary(summaryData);
    } catch (err) {
      console.error('Error loading financial data:', err);
    }
    setLoading(false);
  };

  const handleSalesSubmit = async (e) => {
    e.preventDefault();
    if (salesForm.amount <= 0) {
      toast.error('Amount must be greater than 0');
      return;
    }
    try {
      await createSalesEntry(salesForm);
      toast.success('Sales entry recorded');
      setIsSalesDialogOpen(false);
      setSalesForm({
        date: new Date().toISOString().split('T')[0],
        amount: 0,
        tax_amount: 0,
        payment_method: 'cash',
        description: ''
      });
      await loadData();
    } catch (err) {
      toast.error('Failed to record sales');
    }
  };

  const handleExpenseSubmit = async (e) => {
    e.preventDefault();
    if (expenseForm.amount <= 0) {
      toast.error('Amount must be greater than 0');
      return;
    }
    try {
      await createExpenseEntry(expenseForm);
      toast.success('Expense recorded');
      setIsExpenseDialogOpen(false);
      setExpenseForm({
        date: new Date().toISOString().split('T')[0],
        amount: 0,
        category: 'materials',
        description: ''
      });
      await loadData();
    } catch (err) {
      toast.error('Failed to record expense');
    }
  };

  // Group expenses by category
  const expensesByCategory = expenses.reduce((acc, exp) => {
    acc[exp.category] = (acc[exp.category] || 0) + exp.amount;
    return acc;
  }, {});

  return (
    <div className="space-y-6 animate-fade-in" data-testid="financials-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Financials</h1>
          <p className="text-muted-foreground mt-1">Track sales, expenses, and taxes</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={isSalesDialogOpen} onOpenChange={setIsSalesDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700" data-testid="add-sales-btn">
                <DollarSign className="h-4 w-4 mr-2" /> Enter Daily Sales
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[450px]">
              <DialogHeader>
                <DialogTitle className="font-heading uppercase">Daily Sales Entry</DialogTitle>
              </DialogHeader>
              <p className="text-sm text-muted-foreground -mt-2 mb-4">
                Record actual money received today (cash, credit, checks)
              </p>
              <form onSubmit={handleSalesSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Date</Label>
                  <Input
                    type="date"
                    value={salesForm.date}
                    onChange={(e) => setSalesForm({ ...salesForm, date: e.target.value })}
                    data-testid="sales-date-input"
                  />
                </div>
                
                {/* Payment Method Selection */}
                <div className="space-y-2">
                  <Label>Payment Method *</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {paymentMethods.map((method) => {
                      const Icon = method.icon;
                      return (
                        <button
                          key={method.value}
                          type="button"
                          onClick={() => setSalesForm({ ...salesForm, payment_method: method.value })}
                          className={`flex items-center gap-2 p-3 rounded-lg border transition-all ${
                            salesForm.payment_method === method.value
                              ? 'border-primary bg-primary/10 text-primary'
                              : 'border-border hover:border-primary/50'
                          }`}
                          data-testid={`payment-method-${method.value}`}
                        >
                          <Icon className="h-4 w-4" />
                          <span className="text-sm font-medium">{method.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Amount Received *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={salesForm.amount === 0 ? '' : salesForm.amount}
                      onChange={(e) => setSalesForm({ ...salesForm, amount: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                      onBlur={(e) => {
                        if (e.target.value === '') {
                          setSalesForm({ ...salesForm, amount: 0 });
                        }
                      }}
                      placeholder="Enter amount"
                      data-testid="sales-amount-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Tax Collected</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={salesForm.tax_amount === 0 ? '' : salesForm.tax_amount}
                      onChange={(e) => setSalesForm({ ...salesForm, tax_amount: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                      onBlur={(e) => {
                        if (e.target.value === '') {
                          setSalesForm({ ...salesForm, tax_amount: 0 });
                        }
                      }}
                      placeholder="Enter tax"
                      data-testid="sales-tax-input"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Input
                    value={salesForm.description}
                    onChange={(e) => setSalesForm({ ...salesForm, description: e.target.value })}
                    placeholder="e.g., Morning deposit, Check from ABC Corp"
                    data-testid="sales-description-input"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button type="button" variant="outline" onClick={() => setIsSalesDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="bg-green-600 hover:bg-green-700" data-testid="sales-submit-btn">
                    Record Sales
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={isExpenseDialogOpen} onOpenChange={setIsExpenseDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive" data-testid="add-expense-btn">
                <TrendingDown className="h-4 w-4 mr-2" /> Add Expense
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[400px]">
              <DialogHeader>
                <DialogTitle className="font-heading uppercase">Record Expense</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleExpenseSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Date</Label>
                    <Input
                      type="date"
                      value={expenseForm.date}
                      onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })}
                      data-testid="expense-date-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select
                      value={expenseForm.category}
                      onValueChange={(val) => setExpenseForm({ ...expenseForm, category: val })}
                    >
                      <SelectTrigger data-testid="expense-category-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {expenseCategories.map((c) => (
                          <SelectItem key={c.value} value={c.value}>
                            {c.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Amount *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={expenseForm.amount === 0 ? '' : expenseForm.amount}
                    onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                    onBlur={(e) => {
                      if (e.target.value === '') {
                        setExpenseForm({ ...expenseForm, amount: 0 });
                      }
                    }}
                    placeholder="Enter amount"
                    data-testid="expense-amount-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input
                    value={expenseForm.description}
                    onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
                    placeholder="What was this expense for?"
                    data-testid="expense-description-input"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button type="button" variant="outline" onClick={() => setIsExpenseDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" variant="destructive" data-testid="expense-submit-btn">
                    Record
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Date Range Filter */}
      <Card className="bg-card border-border/50">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <span className="text-sm text-muted-foreground">Date Range:</span>
            <Input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="w-[160px]"
              data-testid="financials-start-date"
            />
            <span className="text-muted-foreground">to</span>
            <Input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="w-[160px]"
              data-testid="financials-end-date"
            />
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card border-border/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-green-400" />
                <span className="text-sm text-muted-foreground">Total Sales</span>
              </div>
              <p className="text-2xl font-bold text-green-400">{formatCurrency(summary.total_sales)}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Receipt className="h-4 w-4 text-yellow-400" />
                <span className="text-sm text-muted-foreground">Sales Tax</span>
              </div>
              <p className="text-2xl font-bold text-yellow-400">{formatCurrency(summary.total_tax)}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="h-4 w-4 text-red-400" />
                <span className="text-sm text-muted-foreground">Expenses</span>
              </div>
              <p className="text-2xl font-bold text-red-400">{formatCurrency(summary.total_expenses)}</p>
            </CardContent>
          </Card>
          <Card className="bg-card border-border/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-4 w-4 text-primary" />
                <span className="text-sm text-muted-foreground">Net Income</span>
              </div>
              <p className={`text-2xl font-bold ${summary.net_income >= 0 ? 'text-primary' : 'text-red-400'}`}>
                {formatCurrency(summary.net_income)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs for Sales/Expenses */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sales">Sales ({sales.length})</TabsTrigger>
          <TabsTrigger value="expenses">Expenses ({expenses.length})</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Expense Breakdown */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase">Expense Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                {Object.keys(expensesByCategory).length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No expenses recorded</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(expensesByCategory).map(([category, amount]) => (
                      <div key={category} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                        <span className="font-medium">{getCategoryLabel(category)}</span>
                        <span className="text-red-400 font-bold">{formatCurrency(amount)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Activity */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {[...sales.map(s => ({ ...s, type: 'sale' })), ...expenses.map(e => ({ ...e, type: 'expense' }))]
                    .sort((a, b) => new Date(b.date) - new Date(a.date))
                    .slice(0, 10)
                    .map((item, idx) => {
                      const methodInfo = item.type === 'sale' 
                        ? (paymentMethods.find(m => m.value === item.payment_method) || paymentMethods[3])
                        : null;
                      const Icon = methodInfo?.icon;
                      return (
                        <div 
                          key={`${item.type}-${item.id}`} 
                          className={`flex items-center justify-between p-3 rounded-lg ${
                            item.type === 'sale' ? 'bg-green-500/10' : 'bg-red-500/10'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            {item.type === 'sale' && Icon && (
                              <Icon className="h-4 w-4 text-green-400" />
                            )}
                            <div>
                              <p className="text-sm font-medium">
                                {item.type === 'sale' ? methodInfo?.label || 'Daily Sales' : getCategoryLabel(item.category)}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {formatDate(item.date)}
                              </p>
                            </div>
                          </div>
                          <span className={`font-bold ${item.type === 'sale' ? 'text-green-400' : 'text-red-400'}`}>
                            {item.type === 'sale' ? '+' : '-'}{formatCurrency(item.amount)}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sales Tab */}
        <TabsContent value="sales" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {sales.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No daily sales recorded for this period
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Payment Method</TableHead>
                      <TableHead>Notes</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Tax</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sales.map((sale, idx) => {
                      const methodInfo = paymentMethods.find(m => m.value === sale.payment_method) || paymentMethods[3];
                      const Icon = methodInfo.icon;
                      return (
                        <TableRow key={sale.id} className={idx % 2 === 0 ? '' : 'bg-muted/30'}>
                          <TableCell>{formatDate(sale.date)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4 text-muted-foreground" />
                              <span className="capitalize">{methodInfo.label}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">{sale.description || '-'}</TableCell>
                          <TableCell className="text-right font-bold text-green-400">
                            {formatCurrency(sale.amount)}
                          </TableCell>
                          <TableCell className="text-right text-yellow-400">
                            {formatCurrency(sale.tax_amount)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Expenses Tab */}
        <TabsContent value="expenses" className="mt-4">
          <Card className="bg-card border-border/50">
            <CardContent className="p-0">
              {expenses.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No expenses recorded for this period
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {expenses.map((expense, idx) => (
                      <TableRow key={expense.id} className={idx % 2 === 0 ? '' : 'bg-muted/30'}>
                        <TableCell>{formatDate(expense.date)}</TableCell>
                        <TableCell>{getCategoryLabel(expense.category)}</TableCell>
                        <TableCell className="text-muted-foreground">{expense.description || '-'}</TableCell>
                        <TableCell className="text-right font-bold text-red-400">
                          {formatCurrency(expense.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
