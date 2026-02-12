import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Calculator, X } from 'lucide-react';
import PricingCalculator from './PricingCalculator';

/**
 * Modal wrapper for the Pricing Calculator
 * Used in Jobs and Quotes to calculate pricing for line items
 */
export default function PricingCalculatorModal({ 
  isOpen, 
  onClose, 
  onItemCalculated,
  initialCategory = null,
  initialData = null 
}) {
  const handleCalculationComplete = (itemData) => {
    // Pass the calculated item data back to the parent
    if (onItemCalculated) {
      onItemCalculated(itemData);
    }
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto p-0">
        <DialogHeader className="p-4 pb-0 flex flex-row items-center justify-between">
          <DialogTitle className="font-heading uppercase flex items-center gap-2">
            <Calculator className="h-5 w-5 text-teal-500" />
            Pricing Calculator
          </DialogTitle>
        </DialogHeader>
        <div className="p-4 pt-2">
          <PricingCalculator
            onCalculationComplete={handleCalculationComplete}
            initialCategory={initialCategory}
            initialData={initialData}
            embedded={true}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Button component to trigger the pricing calculator
 */
export function PricingCalculatorButton({ onClick, variant = "outline", size = "sm", className = "" }) {
  return (
    <Button 
      type="button"
      variant={variant} 
      size={size} 
      onClick={onClick}
      className={`border-teal-500/50 text-teal-500 hover:bg-teal-500/10 ${className}`}
    >
      <Calculator className="h-4 w-4 mr-2" />
      Use Calculator
    </Button>
  );
}
