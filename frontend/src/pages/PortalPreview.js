import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle, Clock, AlertCircle, Building2, Mail, Phone, Printer } from 'lucide-react';
import { Button } from '../components/ui/button';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PortalPreview() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | success | expired | error
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/api/portal/preview/${token}`)
      .then(async (res) => {
        if (res.status === 410) { setStatus('expired'); return; }
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Not found'); }
        return res.json();
      })
      .then((d) => { if (d) { setData(d); setStatus('success'); } })
      .catch((e) => { setErrorMsg(e.message); setStatus('error'); });
  }, [token]);

  const formatCurrency = (v) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v || 0);

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading quote…</p>
        </div>
      </div>
    );
  }

  if (status === 'expired') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow p-8 max-w-md text-center">
          <Clock className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-900 mb-2">Link Expired</h1>
          <p className="text-gray-500">This quote link has expired. Please contact us for a new link.</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow p-8 max-w-md text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-900 mb-2">Quote Not Found</h1>
          <p className="text-gray-500">{errorMsg || 'This link is invalid or no longer available.'}</p>
        </div>
      </div>
    );
  }

  const { resource: quote, customer, tenant } = data || {};
  const lineItems = quote?.line_items || [];
  const total = quote?.total || 0;
  const quoteNumber = quote?.quote_number || (quote?.id || '').slice(0, 8).toUpperCase();

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">

        {/* Shop header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-4 flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
            <Building2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">{tenant?.name || 'Sign Shop'}</h2>
            {tenant?.email && (
              <p className="text-sm text-gray-500 flex items-center gap-1">
                <Mail className="h-3 w-3" /> {tenant.email}
              </p>
            )}
            {tenant?.phone && (
              <p className="text-sm text-gray-500 flex items-center gap-1">
                <Phone className="h-3 w-3" /> {tenant.phone}
              </p>
            )}
          </div>
        </div>

        {/* Quote card */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Quote #{quoteNumber}</h1>
              {customer && (
                <p className="text-gray-500 mt-1">
                  Prepared for {customer.name || customer.company_name || 'Valued Customer'}
                </p>
              )}
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              quote?.status === 'approved' ? 'bg-green-100 text-green-700' :
              quote?.status === 'sent' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-600'
            }`}>
              {(quote?.status || 'draft').charAt(0).toUpperCase() + (quote?.status || 'draft').slice(1)}
            </span>
          </div>

          {/* Line items */}
          <table className="w-full text-sm mb-6">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-gray-600 font-medium">Description</th>
                <th className="text-right py-2 text-gray-600 font-medium w-16">Qty</th>
                <th className="text-right py-2 text-gray-600 font-medium w-24">Unit</th>
                <th className="text-right py-2 text-gray-600 font-medium w-24">Total</th>
              </tr>
            </thead>
            <tbody>
              {lineItems.map((item, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-3 text-gray-900">{item.description || 'Item'}</td>
                  <td className="py-3 text-right text-gray-700">{item.quantity}</td>
                  <td className="py-3 text-right text-gray-700">{formatCurrency(item.unit_price)}</td>
                  <td className="py-3 text-right text-gray-900 font-medium">{formatCurrency(item.total)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="3" className="pt-4 text-right font-bold text-gray-900 text-base">Total</td>
                <td className="pt-4 text-right font-bold text-gray-900 text-base">{formatCurrency(total)}</td>
              </tr>
            </tfoot>
          </table>

          {quote?.notes && (
            <div className="border-t pt-4 mb-4">
              <p className="text-sm text-gray-500 italic">{quote.notes}</p>
            </div>
          )}

          <div className="flex justify-between items-center text-xs text-gray-400 border-t pt-4">
            <span>This quote is valid for 30 days from issue date.</span>
            <Button variant="outline" size="sm" onClick={() => window.print()} className="flex items-center gap-1">
              <Printer className="h-3 w-3" /> Print
            </Button>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Powered by SignGuy AI · Quote expires{' '}
          {data?.link_expires_at ? new Date(data.link_expires_at).toLocaleDateString() : 'soon'}
        </p>
      </div>
    </div>
  );
}
