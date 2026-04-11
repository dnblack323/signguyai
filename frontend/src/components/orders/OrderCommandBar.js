import { BarChart3, Calculator, PenSquare, Plus, Save } from 'lucide-react';
import { Button } from '../ui/button';

export const OrderCommandBar = ({
  onOpenPricingAnalysis,
  onOpenPricingCalculator,
  onOpenSketch,
  onAddTicket,
  onSave,
  saveLabel = 'Save Order',
  testId = 'order-command-bar',
}) => {
  return (
    <div className="sticky top-20 z-20 rounded-2xl border border-gray-200 bg-white/95 p-3 shadow-sm backdrop-blur" data-testid={testId}>
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" onClick={onOpenPricingAnalysis} data-testid={`${testId}-pricing-analysis`}>
          <BarChart3 className="mr-2 h-4 w-4" /> Pricing Analysis
        </Button>
        <Button type="button" variant="outline" onClick={onOpenPricingCalculator} data-testid={`${testId}-pricing-calculator`}>
          <Calculator className="mr-2 h-4 w-4" /> Calculator
        </Button>
        {onOpenSketch && (
          <Button type="button" variant="outline" onClick={onOpenSketch} data-testid={`${testId}-sketch`}>
            <PenSquare className="mr-2 h-4 w-4" /> Sketch
          </Button>
        )}
        {onAddTicket && (
          <Button type="button" variant="outline" onClick={onAddTicket} data-testid={`${testId}-add-ticket`}>
            <Plus className="mr-2 h-4 w-4" /> Add Ticket
          </Button>
        )}
        {onSave && (
          <Button type="button" onClick={onSave} data-testid={`${testId}-save`}>
            <Save className="mr-2 h-4 w-4" /> {saveLabel}
          </Button>
        )}
      </div>
    </div>
  );
};