import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function MaterialsAdmin() {
  return (
    <div className="max-w-3xl mx-auto py-10" data-testid="materials-admin-compat">
      <Card>
        <CardHeader>
          <CardTitle>Materials Library moved</CardTitle>
          <CardDescription>The unified Materials Library now lives inside Pricing Foundation.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <Link to="/pricing-foundation">
            <Button data-testid="materials-admin-go-foundation">Go to Pricing Foundation</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
