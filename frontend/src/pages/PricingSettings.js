import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function PricingSettings() {
  return (
    <div className="max-w-3xl mx-auto py-10" data-testid="pricing-settings-compat">
      <Card>
        <CardHeader>
          <CardTitle>Pricing Settings moved</CardTitle>
          <CardDescription>Pricing Foundation is now the single source of truth for pricing defaults, materials, and rules.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <Link to="/pricing-foundation">
            <Button data-testid="pricing-settings-go-foundation">Go to Pricing Foundation</Button>
          </Link>
          <Link to="/settings/pricing-setup">
            <Button variant="outline" data-testid="pricing-settings-go-setup">Open Pricing Setup (Historical)</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
