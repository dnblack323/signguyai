import { useEffect, useState } from 'react';
import axios from 'axios';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useSignatureFeature } from '../hooks/useSignatureFeature';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SignatureActivityList = ({ orderId }) => {
  const { enabled } = useSignatureFeature();
  const [signatures, setSignatures] = useState([]);

  useEffect(() => {
    if (!enabled || !orderId) return;
    axios.get(`${API}/signatures`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
      params: { order_id: orderId },
    }).then((response) => setSignatures(response.data || [])).catch(() => setSignatures([]));
  }, [enabled, orderId]);

  if (!enabled) return null;

  return (
    <Card className="bg-white border-gray-200">
      <CardHeader><CardTitle className="text-base text-gray-900">Order Signature History</CardTitle></CardHeader>
      <CardContent>
        {signatures.length === 0 ? (
          <p className="text-sm text-gray-500">No signature history yet.</p>
        ) : (
          <div className="space-y-2" data-testid="order-signature-history-list">
            {signatures.map((signature) => (
              <div key={signature.id} className="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-700">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-gray-900">{signature.signature_type?.replace(/_/g, ' ')}</span>
                  <Badge variant="outline">{signature.status}</Badge>
                </div>
                <p className="mt-1">{signature.parent_record_type.replace(/_/g, ' ')} · {signature.parent_record_id.slice(0, 8)}</p>
                <p className="text-xs text-gray-500 mt-1">{signature.signed_at ? `Signed ${new Date(signature.signed_at).toLocaleString()}` : 'Pending signature'}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};