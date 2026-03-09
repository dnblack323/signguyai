import { Link } from 'react-router-dom';
import PricingCalculator from '../components/PricingCalculator';
import { Button } from '../components/ui/button';
import { Settings } from 'lucide-react';
import { toast } from 'sonner';

export default function PricingPage() {
  const handleCalculationComplete = (itemData) => {
    toast.success(`Item added: ${itemData.description} - $${itemData.line_total.toFixed(2)}`);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pricing Calculator</h1>
          <p className="text-gray-500 mt-1">Calculate pricing for quotes and jobs</p>
        </div>
        <Link to="/pricing-calculator/settings">
          <Button variant="outline" className="border-gray-300 text-gray-700 hover:bg-gray-100">
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
