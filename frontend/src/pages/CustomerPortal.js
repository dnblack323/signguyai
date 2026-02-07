import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, FileText, Briefcase, Receipt, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CustomerPortal() {
  const { token } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchResource = async () => {
      try {
        const response = await fetch(`${API_URL}/api/portal/${token}`);
        
        if (response.ok) {
          const result = await response.json();
          setData(result);
        } else {
          const errorData = await response.json();
          setError(errorData.detail || 'Failed to load resource');
        }
      } catch (err) {
        setError('Network error. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchResource();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center">
              <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
              <h2 className="text-xl font-bold text-gray-900 mb-2">Unable to Access</h2>
              <p className="text-gray-600">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { resource_type, resource, customer, link_expires_at } = data;

  const getIcon = () => {
    switch (resource_type) {
      case 'quote': return <FileText className="h-6 w-6" />;
      case 'job': return <Briefcase className="h-6 w-6" />;
      case 'invoice': return <Receipt className="h-6 w-6" />;
      default: return <FileText className="h-6 w-6" />;
    }
  };

  const getTitle = () => {
    switch (resource_type) {
      case 'quote': return 'Quote';
      case 'job': return 'Job Details';
      case 'invoice': return 'Invoice';
      default: return 'Document';
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-700', label: 'Draft' },
      sent: { color: 'bg-blue-100 text-blue-700', label: 'Sent' },
      approved: { color: 'bg-green-100 text-green-700', label: 'Approved' },
      declined: { color: 'bg-red-100 text-red-700', label: 'Declined' },
      paid: { color: 'bg-green-100 text-green-700', label: 'Paid' },
      overdue: { color: 'bg-red-100 text-red-700', label: 'Overdue' },
      quoted: { color: 'bg-purple-100 text-purple-700', label: 'Quoted' },
      in_production: { color: 'bg-amber-100 text-amber-700', label: 'In Production' },
      complete: { color: 'bg-green-100 text-green-700', label: 'Complete' },
    };
    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-700', label: status };
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-teal-500/10 text-teal-600 mb-4">
            {getIcon()}
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{getTitle()}</h1>
          {customer && (
            <p className="text-gray-600 mt-1">
              Prepared for {customer.name}{customer.company ? ` - ${customer.company}` : ''}
            </p>
          )}
        </div>

        {/* Link Expiry Notice */}
        <Alert className="mb-6 bg-amber-50 border-amber-200">
          <Clock className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            This link expires on {formatDate(link_expires_at)}
          </AlertDescription>
        </Alert>

        {/* Main Content Card */}
        <Card className="shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">
                {resource_type === 'quote' && `Quote #${resource.id?.slice(0, 8).toUpperCase()}`}
                {resource_type === 'job' && (resource.name || `Job #${resource.id?.slice(0, 8).toUpperCase()}`)}
                {resource_type === 'invoice' && `Invoice #${resource.id?.slice(0, 8).toUpperCase()}`}
              </CardTitle>
              <CardDescription>Created {formatDate(resource.created_at)}</CardDescription>
            </div>
            {getStatusBadge(resource.status)}
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Line Items */}
            {(resource.line_items?.length > 0 || resource.items?.length > 0) && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Items</h3>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="text-left px-4 py-2 text-sm font-medium text-gray-700">Description</th>
                        <th className="text-right px-4 py-2 text-sm font-medium text-gray-700">Qty</th>
                        <th className="text-right px-4 py-2 text-sm font-medium text-gray-700">Price</th>
                        <th className="text-right px-4 py-2 text-sm font-medium text-gray-700">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {(resource.line_items || resource.items || []).map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-gray-900">{item.description}</td>
                          <td className="px-4 py-3 text-right text-gray-600">{item.quantity}</td>
                          <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(item.unit_price)}</td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            {formatCurrency(item.total || item.line_total || (item.quantity * item.unit_price))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <Separator />

            {/* Total */}
            <div className="flex justify-between items-center">
              <span className="text-lg font-semibold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-teal-600">
                {formatCurrency(resource.total || resource.subtotal)}
              </span>
            </div>

            {/* Notes */}
            {resource.notes && (
              <>
                <Separator />
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Notes</h3>
                  <p className="text-gray-600 whitespace-pre-wrap">{resource.notes}</p>
                </div>
              </>
            )}

            {/* Due Date for Jobs/Invoices */}
            {resource.due_date && (
              <>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Due Date</span>
                  <span className="font-medium text-gray-900">{formatDate(resource.due_date)}</span>
                </div>
              </>
            )}

            {/* Payment Status for Invoices */}
            {resource_type === 'invoice' && (
              <>
                <Separator />
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-700">Amount Paid</span>
                    <span className="font-medium text-gray-900">{formatCurrency(resource.amount_paid)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Balance Due</span>
                    <span className="font-bold text-lg text-gray-900">
                      {formatCurrency((resource.total || 0) - (resource.amount_paid || 0))}
                    </span>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Questions? Contact us at your convenience.</p>
          <p className="mt-2">Powered by Sign Guy AI</p>
        </div>
      </div>
    </div>
  );
}
