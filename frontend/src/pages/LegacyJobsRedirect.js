import { Navigate, useSearchParams } from 'react-router-dom';

export default function LegacyJobsRedirect() {
  const [searchParams] = useSearchParams();

  if (searchParams.get('new') === 'true') {
    return <Navigate to="/orders/new" replace />;
  }

  if (searchParams.get('filter') === 'quotes') {
    return <Navigate to="/quotes" replace />;
  }

  return <Navigate to="/orders" replace />;
}