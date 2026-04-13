import { Navigate, useParams } from 'react-router-dom';

export default function LegacyJobRedirect() {
  const { id } = useParams();
  return <Navigate to={`/productivity/legacy-jobs/${id}`} replace />;
}