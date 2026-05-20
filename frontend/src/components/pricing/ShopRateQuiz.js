// Shop Rate Quiz - Calculate loaded hourly shop rate
// Helps shops calculate their default hourly rate including wages, overhead, payroll burden, and profit buffer

import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { AlertCircle, ArrowLeft, ArrowRight, Calculator, CheckCircle, DollarSign, Info } from 'lucide-react';
import { toast } from 'sonner';

const n = (v) => Number(v || 0);
const f2 = (v) => n(v).toFixed(2);

// Overhead presets
const OVERHEAD_PRESETS = [
  { value: 'home', label: 'Home / Garage Shop', amount: 1750, range: '$1,000–$2,500/month' },
  { value: 'small', label: 'Small Commercial Shop', amount: 5250, range: '$3,000–$7,500/month' },
  { value: 'growing', label: 'Growing Shop with Staff/Equipment', amount: 11500, range: '$8,000–$15,000/month' },
  { value: 'custom', label: 'Custom - Enter Line by Line', amount: 0, range: '' },
];

// Billable percentage presets
const BILLABLE_PRESETS = [
  { value: '40', label: 'Low Efficiency (40%)', hint: 'Lots of non-billable time' },
  { value: '50', label: 'Average Small Shop (50%)', hint: 'Recommended if unsure' },
  { value: '60', label: 'Organized Shop (60%)', hint: 'Good systems in place' },
  { value: '70', label: 'Very Efficient Shop (70%)', hint: 'Optimized workflow' },
];

// Payroll burden presets
const BURDEN_PRESETS = [
  { value: '10', label: 'Very Lean / Owner Labor (10%)' },
  { value: '15', label: 'Basic Employer Cost (15%)' },
  { value: '20', label: 'Safer Small Business Estimate (20%)', recommended: true },
  { value: '25', label: 'Higher Burden (25%)' },
];

// Profit/safety buffer presets
const BUFFER_PRESETS = [
  { value: '10', label: 'Lean / Competitive ($10/hr)' },
  { value: '20', label: 'Balanced ($20/hr)', recommended: true },
  { value: '30', label: 'Premium / Custom Shop ($30/hr)' },
  { value: '40', label: 'Aggressive Growth ($40/hr)' },
];

export default function ShopRateQuiz({ open, onClose, onApply }) {
  const [step, setStep] = useState(1);
  const [setupStyle, setSetupStyle] = useState('');
  
  // Quick/Detailed path data
  const [overheadPreset, setOverheadPreset] = useState('small');
  const [overheadLines, setOverheadLines] = useState({
    rent: 0, utilities: 0, phone: 0, insurance: 0, software: 0,
    equipment: 0, vehicle: 0, marketing: 0, repairs: 0, accounting: 0,
    loans: 0, supplies: 0, other: 0,
  });
  const [productionWorkers, setProductionWorkers] = useState(1);
  const [hoursPerWeek, setHoursPerWeek] = useState(40);
  const [ownerHours, setOwnerHours] = useState(0);
  const [billablePercent, setBillablePercent] = useState(50);
  
  const [laborMethod, setLaborMethod] = useState('average'); // 'average' or 'payroll'
  const [averageWage, setAverageWage] = useState(20);
  const [totalWeeklyPayroll, setTotalWeeklyPayroll] = useState(0);
  const [totalWeeklyHours, setTotalWeeklyHours] = useState(0);
  const [payrollBurden, setPayrollBurden] = useState(20);
  
  const [profitBuffer, setProfitBuffer] = useState(20);
  const [roundingRule, setRoundingRule] = useState('5');
  
  // "I Already Know My Rate" path
  const [knownShopRate, setKnownShopRate] = useState(0);
  const [knownProductionRate, setKnownProductionRate] = useState(0);
  const [knownDesignRate, setKnownDesignRate] = useState(0);
  const [knownInstallRate, setKnownInstallRate] = useState(0);

  // Calculations
  const totalOverhead = overheadPreset === 'custom'
    ? Object.values(overheadLines).reduce((sum, v) => sum + n(v), 0)
    : OVERHEAD_PRESETS.find(p => p.value === overheadPreset)?.amount || 0;
  
  const weeklyAvailableHours = n(productionWorkers) * n(hoursPerWeek) + n(ownerHours);
  const weeklyBillableHours = weeklyAvailableHours * (n(billablePercent) / 100);
  const monthlyBillableHours = weeklyBillableHours * 4.33;
  const overheadPerHour = monthlyBillableHours > 0 ? totalOverhead / monthlyBillableHours : 0;
  
  let loadedLaborCost = 0;
  if (laborMethod === 'average') {
    loadedLaborCost = n(averageWage) * (1 + n(payrollBurden) / 100);
  } else {
    const laborCostPerHour = n(totalWeeklyHours) > 0 ? n(totalWeeklyPayroll) / n(totalWeeklyHours) : 0;
    loadedLaborCost = laborCostPerHour * (1 + n(payrollBurden) / 100);
  }
  
  const suggestedShopRate = loadedLaborCost + overheadPerHour + n(profitBuffer);
  
  const roundedShopRate = (() => {
    const r = roundingRule;
    if (r === '1') return Math.round(suggestedShopRate);
    if (r === '5') return Math.round(suggestedShopRate / 5) * 5;
    if (r === '10') return Math.round(suggestedShopRate / 10) * 10;
    return suggestedShopRate;
  })();

  // Warnings
  const warnings = [];
  if (monthlyBillableHours < 40) warnings.push('Monthly billable hours seem very low. Your calculated shop rate may be very high.');
  if (payrollBurden === 0) warnings.push('Payroll burden is 0%. Labor cost may be understated.');
  if (totalOverhead === 0) warnings.push('Overhead is $0. The rate may not reflect real shop costs.');
  if (profitBuffer === 0) warnings.push('Profit buffer is $0. The rate may leave little room for mistakes or profit.');
  if (roundedShopRate < 40) warnings.push('Calculated shop rate is under $40/hr. This seems low for a sign shop.');
  if (roundedShopRate > 200) warnings.push('Calculated shop rate is over $200/hr. This seems high and should be reviewed.');

  const handleNext = () => {
    if (step === 1 && !setupStyle) {
      toast.error('Please select a setup style');
      return;
    }
    if (setupStyle === 'known' && step === 1) {
      setStep(8); // Skip to final step
      return;
    }
    setStep(step + 1);
  };

  const handleBack = () => {
    if (setupStyle === 'known' && step === 8) {
      setStep(1);
      return;
    }
    setStep(step - 1);
  };

  const handleApply = () => {
    const result = setupStyle === 'known' ? {
      shop_rate_quiz_completed: true,
      shop_rate_quiz_method: 'known',
      default_shop_rate: n(knownShopRate),
      production_hourly_rate: n(knownProductionRate) || n(knownShopRate),
      design_hourly_rate: n(knownDesignRate) || n(knownShopRate),
      install_hourly_rate: n(knownInstallRate) || n(knownShopRate),
    } : {
      shop_rate_quiz_completed: true,
      shop_rate_quiz_method: setupStyle,
      default_shop_rate: roundedShopRate,
      production_hourly_rate: roundedShopRate,
      design_hourly_rate: Math.round(roundedShopRate * 1.1 / 5) * 5, // +10%
      install_hourly_rate: Math.round(roundedShopRate * 1.15 / 5) * 5, // +15%
      monthly_overhead_total: totalOverhead,
      monthly_billable_hours: monthlyBillableHours,
      overhead_per_billable_hour: overheadPerHour,
      payroll_burden_percent: n(payrollBurden),
      labor_profit_buffer_per_hour: n(profitBuffer),
      loaded_labor_cost: loadedLaborCost,
    };
    
    onApply(result);
    toast.success('Shop rate saved successfully');
    onClose();
  };

  const renderStep = () => {
    if (step === 1) {
      return (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Your shop rate is not just what you pay an employee. It should include wages, payroll-related costs,
            a share of monthly shop expenses, and a profit/safety buffer. This helps make sure your labor time
            pays for the real cost of running the shop.
          </p>
          <div className="space-y-3">
            {[
              { value: 'quick', label: 'Quick Estimate', hint: 'Best if you do not know all your exact numbers. We\'ll use a few simple questions and safe defaults.' },
              { value: 'detailed', label: 'Detailed Business Numbers', hint: 'Best if you know your monthly expenses, payroll, and production hours.' },
              { value: 'known', label: 'I Already Know My Shop Rate', hint: 'Use this if you already know the hourly rate you want the calculator to use.' },
            ].map(opt => (
              <Card key={opt.value} className={`cursor-pointer transition-all ${setupStyle === opt.value ? 'ring-2 ring-violet-500 bg-violet-50' : 'hover:bg-gray-50'}`}
                onClick={() => setSetupStyle(opt.value)}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{opt.label}</CardTitle>
                  <CardDescription className="text-xs">{opt.hint}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Monthly Overhead</h3>
            <p className="text-sm text-gray-600 mb-4">
              Overhead means the bills your shop has to pay whether you have one job or fifty jobs.
              These are the costs of keeping the doors open.
            </p>
          </div>
          <div>
            <Label className="text-sm">Overhead Preset</Label>
            <Select value={overheadPreset} onValueChange={setOverheadPreset}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OVERHEAD_PRESETS.map(p => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label} {p.range && `(${p.range})`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {overheadPreset === 'custom' && (
            <div className="grid grid-cols-2 gap-3">
              {Object.keys(overheadLines).map(key => (
                <div key={key}>
                  <Label className="text-xs capitalize">{key.replace('_', ' ')}</Label>
                  <Input
                    type="number"
                    value={overheadLines[key]}
                    onChange={(e) => setOverheadLines({ ...overheadLines, [key]: n(e.target.value) })}
                    className="h-8 text-sm"
                  />
                </div>
              ))}
            </div>
          )}
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <p className="text-sm text-blue-900">
              <strong>Total Monthly Overhead:</strong> ${f2(totalOverhead)}
            </p>
          </div>
          <div className="text-xs text-gray-500 space-y-1">
            <p>💡 Do not include job materials here. Vinyl, banners, shirts, substrates should be in Materials Library.</p>
            <p>💡 Do not include production wages here unless you intentionally want wages treated as overhead.</p>
          </div>
        </div>
      );
    }

    if (step === 3) {
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Billable Hours</h3>
            <p className="text-sm text-gray-600 mb-4">
              Billable hours are the hours spent doing work that directly earns money, like printing, cutting,
              installing, designing, producing, or finishing jobs. Not every hour at work is billable.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-sm">Production Workers</Label>
              <Input type="number" value={productionWorkers} onChange={(e) => setProductionWorkers(n(e.target.value))} className="h-8" />
            </div>
            <div>
              <Label className="text-sm">Hours Per Week Per Worker</Label>
              <Input type="number" value={hoursPerWeek} onChange={(e) => setHoursPerWeek(n(e.target.value))} className="h-8" />
            </div>
            <div>
              <Label className="text-sm">Owner Production Hours/Week</Label>
              <Input type="number" value={ownerHours} onChange={(e) => setOwnerHours(n(e.target.value))} className="h-8" />
            </div>
            <div>
              <Label className="text-sm">Billable % (Recommended: 50%)</Label>
              <Select value={String(billablePercent)} onValueChange={(v) => setBillablePercent(n(v))}>
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {BILLABLE_PRESETS.map(p => (
                    <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                  ))}
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm space-y-1">
            <p><strong>Weekly Available Hours:</strong> {f2(weeklyAvailableHours)}</p>
            <p><strong>Weekly Billable Hours:</strong> {f2(weeklyBillableHours)}</p>
            <p><strong>Monthly Billable Hours:</strong> {f2(monthlyBillableHours)}</p>
          </div>
        </div>
      );
    }

    if (step === 4) {
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Labor Cost & Payroll Burden</h3>
            <p className="text-sm text-gray-600 mb-4">
              Payroll burden is the extra cost of having an employee beyond their hourly wage. It can include
              payroll taxes, workers comp, unemployment insurance, benefits, paid time off, and other employment costs.
            </p>
          </div>
          <div>
            <Label className="text-sm">How do you want to enter labor cost?</Label>
            <Select value={laborMethod} onValueChange={setLaborMethod}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="average">Average Wage Method</SelectItem>
                <SelectItem value="payroll">Total Payroll Method</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {laborMethod === 'average' ? (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-sm">Average Production Wage ($/hr)</Label>
                <Input type="number" value={averageWage} onChange={(e) => setAverageWage(n(e.target.value))} className="h-8" />
              </div>
              <div>
                <Label className="text-sm">Payroll Burden % (Recommended: 20%)</Label>
                <Select value={String(payrollBurden)} onValueChange={(v) => setPayrollBurden(n(v))}>
                  <SelectTrigger className="h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BURDEN_PRESETS.map(p => (
                      <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-sm">Total Weekly Payroll ($)</Label>
                <Input type="number" value={totalWeeklyPayroll} onChange={(e) => setTotalWeeklyPayroll(n(e.target.value))} className="h-8" />
              </div>
              <div>
                <Label className="text-sm">Total Weekly Production Hours</Label>
                <Input type="number" value={totalWeeklyHours} onChange={(e) => setTotalWeeklyHours(n(e.target.value))} className="h-8" />
              </div>
              <div>
                <Label className="text-sm">Payroll Burden % (Recommended: 20%)</Label>
                <Select value={String(payrollBurden)} onValueChange={(v) => setPayrollBurden(n(v))}>
                  <SelectTrigger className="h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {BURDEN_PRESETS.map(p => (
                      <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <p className="text-sm text-blue-900">
              <strong>Loaded Labor Cost:</strong> ${f2(loadedLaborCost)}/hr
            </p>
          </div>
        </div>
      );
    }

    if (step === 5) {
      return (
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-semibold mb-2">Profit / Safety Buffer</h3>
            <p className="text-sm text-gray-600 mb-4">
              The profit/safety buffer is extra money added to each billable labor hour. It helps cover mistakes,
              slow days, wasted time, quoting time, small unpaid tasks, growth, and actual profit.
            </p>
          </div>
          <div>
            <Label className="text-sm">Profit/Safety Buffer ($/hr) - Recommended: $20/hr</Label>
            <Select value={String(profitBuffer)} onValueChange={(v) => setProfitBuffer(n(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {BUFFER_PRESETS.map(p => (
                  <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-sm">Round Final Shop Rate To:</Label>
            <Select value={roundingRule} onValueChange={setRoundingRule}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Nearest $1</SelectItem>
                <SelectItem value="5">Nearest $5</SelectItem>
                <SelectItem value="10">Nearest $10</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      );
    }

    if (step === 6) {
      return (
        <div className="space-y-4">
          <h3 className="text-base font-semibold">Result Breakdown</h3>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-gray-600">Monthly Overhead:</div>
              <div className="font-medium">${f2(totalOverhead)}</div>
              <div className="text-gray-600">Monthly Billable Hours:</div>
              <div className="font-medium">{f2(monthlyBillableHours)} hrs</div>
              <div className="text-gray-600">Overhead Per Billable Hour:</div>
              <div className="font-medium">${f2(overheadPerHour)}/hr</div>
              <div className="text-gray-600">Loaded Labor Cost:</div>
              <div className="font-medium">${f2(loadedLaborCost)}/hr</div>
              <div className="text-gray-600">Profit/Safety Buffer:</div>
              <div className="font-medium">${f2(profitBuffer)}/hr</div>
              <div className="col-span-2 border-t pt-2 mt-2"></div>
              <div className="text-gray-600">Suggested Shop Rate (before rounding):</div>
              <div className="font-medium">${f2(suggestedShopRate)}/hr</div>
              <div className="text-gray-900 font-semibold">Rounded Shop Rate:</div>
              <div className="text-lg font-bold text-violet-700">${f2(roundedShopRate)}/hr</div>
            </div>
          </div>
          {warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded p-3 space-y-1">
              <div className="flex items-center gap-2 text-amber-900 font-medium text-sm">
                <AlertCircle className="h-4 w-4" />
                Warnings
              </div>
              <ul className="text-xs text-amber-800 space-y-1 ml-6 list-disc">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      );
    }

    if (step === 8) {
      // "I Already Know My Rate" path
      return (
        <div className="space-y-4">
          <h3 className="text-base font-semibold mb-2">Enter Your Known Rates</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <Label className="text-sm">Default Shop Rate ($/hr) *</Label>
              <Input type="number" value={knownShopRate} onChange={(e) => setKnownShopRate(n(e.target.value))} className="h-8" />
            </div>
            <div>
              <Label className="text-sm">Production Rate ($/hr) - Optional</Label>
              <Input type="number" value={knownProductionRate} onChange={(e) => setKnownProductionRate(n(e.target.value))} className="h-8" placeholder="Same as shop rate" />
            </div>
            <div>
              <Label className="text-sm">Design Rate ($/hr) - Optional</Label>
              <Input type="number" value={knownDesignRate} onChange={(e) => setKnownDesignRate(n(e.target.value))} className="h-8" placeholder="Same as shop rate" />
            </div>
            <div>
              <Label className="text-sm">Install Rate ($/hr) - Optional</Label>
              <Input type="number" value={knownInstallRate} onChange={(e) => setKnownInstallRate(n(e.target.value))} className="h-8" placeholder="Same as shop rate" />
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  const canProceed = () => {
    if (step === 1) return setupStyle !== '';
    if (step === 8) return n(knownShopRate) > 0;
    return true;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-violet-600" />
            Shop Rate Calculator
          </DialogTitle>
          <DialogDescription>
            Calculate your loaded hourly shop rate including overhead, payroll burden, and profit buffer
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {/* Progress indicator */}
          {setupStyle !== 'known' && step > 1 && step < 8 && (
            <div className="mb-4 flex items-center gap-2">
              {[2, 3, 4, 5, 6].map(s => (
                <div key={s} className={`h-1.5 flex-1 rounded-full ${s <= step ? 'bg-violet-600' : 'bg-gray-200'}`} />
              ))}
            </div>
          )}

          {renderStep()}
        </div>

        <DialogFooter className="flex items-center justify-between">
          <div>
            {step > 1 && (
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="h-4 w-4 mr-1" /> Back
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {(step === 6 || step === 8) ? (
              <Button onClick={handleApply} className="bg-violet-600 hover:bg-violet-700" disabled={!canProceed()}>
                <CheckCircle className="h-4 w-4 mr-1" /> Save Shop Rate
              </Button>
            ) : (
              <Button onClick={handleNext} disabled={!canProceed()}>
                Next <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
