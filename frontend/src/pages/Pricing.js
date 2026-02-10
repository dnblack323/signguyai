import PricingCalculator from '../components/PricingCalculator';
import { MainLayout } from '../components/MainLayout';
import { toast } from 'sonner';

export default function PricingPage() {
  const handleCalculationComplete = (itemData) => {
    console.log('Item calculated:', itemData);
    toast.success(`Item added: ${itemData.description} - $${itemData.line_total.toFixed(2)}`);
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Pricing Calculator</h1>
          <p className="text-slate-400 mt-1">Calculate pricing for quotes and jobs</p>
        </div>
        <PricingCalculator 
          onCalculationComplete={handleCalculationComplete}
          embedded={true}
        />
      </div>
    </MainLayout>
  );
}
