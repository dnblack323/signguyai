import { Link } from 'react-router-dom';
import PricingCalculator from '../components/PricingCalculator';
import { Button } from '../components/ui/button';
import { Settings } from 'lucide-react';
import { toast } from 'sonner';

export default function PricingPage() {
  const handleCalculationComplete = (itemData) => {
    console.log('Item calculated:', itemData);
    toast.success(`Item added: ${itemData.description} - $${itemData.line_total.toFixed(2)}`);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Pricing Calculator</h1>
          <p className="text-slate-400 mt-1">Calculate pricing for quotes and jobs</p>
        </div>
        <Link to="/pricing/settings">
          <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
            <Settings className="h-4 w-4 mr-2" />
            Pricing Settings
          </Button>
        </Link>
      </div>
      <PricingCalculator 
        onCalculationComplete={handleCalculationComplete}
        embedded={true}
      />
    </div>
  );
}
