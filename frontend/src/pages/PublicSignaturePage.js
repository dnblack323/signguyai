import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { Loader2, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { DrawingCanvasPad } from '../components/DrawingCanvasPad';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PublicSignaturePage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [signatureRequest, setSignatureRequest] = useState(null);
  const [signatureImage, setSignatureImage] = useState('');
  const [form, setForm] = useState({ signer_name: '', signer_role: 'customer', printed_name: '', notes: '' });

  const fetchRequest = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/signatures/public/${token}`);
      setSignatureRequest(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signature request not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequest(); }, [token]);

  const review = useMemo(() => signatureRequest?.review_snapshot || {}, [signatureRequest]);

  const signRequest = async () => {
    if (!form.signer_name.trim()) {
      toast.error('Signer name is required');
      return;
    }
    if (!signatureImage) {
      toast.error('Please add your signature');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/signatures/public/${token}/sign`, {
        signer_name: form.signer_name,
        signer_role: form.signer_role,
        printed_name: form.printed_name || form.signer_name,
        notes: form.notes,
        image_data: signatureImage,
      });
      toast.success('Thank you — your signature has been saved');
      await fetchRequest();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save signature');
    } finally {
      setSubmitting(false);
    }
  };

  const declineRequest = async () => {
    setSubmitting(true);
    try {
      await axios.post(`${API}/signatures/public/${token}/decline`, {
        signer_name: form.signer_name,
        notes: form.notes,
      });
      toast.success('Your response has been recorded');
      await fetchRequest();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to decline request');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-950"><Loader2 className="w-8 h-8 animate-spin text-teal-400" /></div>;
  }

  if (!signatureRequest) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white">Signature request not available.</div>;
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Review & Sign</h1>
          <p className="mt-2 text-slate-300">Review the record details below, then sign to confirm.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="bg-white border-gray-200">
            <CardHeader>
              <CardTitle className="text-gray-900 flex items-center gap-2"><FileText className="w-5 h-5 text-teal-600" /> Record Review</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-gray-700">
              <p><span className="font-semibold text-gray-900">Type:</span> {signatureRequest.signature_type?.replace(/_/g, ' ')}</p>
              {review.label && <p><span className="font-semibold text-gray-900">Record:</span> {review.label}</p>}
              {review.customer_name && <p><span className="font-semibold text-gray-900">Customer:</span> {review.customer_name}</p>}
              {review.order_number && <p><span className="font-semibold text-gray-900">Order / Job:</span> {review.order_number}</p>}
              {review.job_name && <p><span className="font-semibold text-gray-900">Job:</span> {review.job_name}</p>}
              {review.document_version && <p><span className="font-semibold text-gray-900">Version:</span> {review.document_version}</p>}
              {review.total && <p><span className="font-semibold text-gray-900">Total:</span> ${Number(review.total).toFixed(2)}</p>}
              {review.notes && <p><span className="font-semibold text-gray-900">Notes:</span> {review.notes}</p>}

              {!!review.line_items?.length && (
                <div className="rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full text-sm" data-testid="public-signature-line-items-table">
                    <thead className="bg-gray-50 text-gray-600">
                      <tr>
                        <th className="px-3 py-2 text-left">Description</th>
                        <th className="px-3 py-2 text-left">Qty</th>
                        <th className="px-3 py-2 text-left">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {review.line_items.map((item, index) => (
                        <tr key={`${item.description}-${index}`} className="border-t border-gray-100">
                          <td className="px-3 py-2">{item.description || item.item_name || item.ticket_number}</td>
                          <td className="px-3 py-2">{item.quantity || '-'}</td>
                          <td className="px-3 py-2">{item.total ? `$${Number(item.total).toFixed(2)}` : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {review.file_url && (
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <img src={review.file_url} alt={review.label || 'Review file'} className="w-full rounded-lg object-contain" data-testid="public-signature-review-image" />
                </div>
              )}

              {signatureRequest.status === 'signed' && signatureRequest.signature_image && (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3">
                  <div className="flex items-center gap-2 text-emerald-700 font-medium"><CheckCircle2 className="w-4 h-4" /> Signature already completed</div>
                  <img src={`${process.env.REACT_APP_BACKEND_URL}${signatureRequest.signature_image}`} alt="Signed" className="mt-3 h-24 rounded-lg border border-emerald-200 bg-white p-2" />
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200">
            <CardHeader>
              <CardTitle className="text-gray-900">Signature</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {signatureRequest.status === 'signed' ? (
                <div className="space-y-2 text-sm text-gray-700" data-testid="public-signature-complete-state">
                  <p><span className="font-semibold text-gray-900">Signed at:</span> {new Date(signatureRequest.signed_at).toLocaleString()}</p>
                  <p>Your approval has already been recorded.</p>
                </div>
              ) : signatureRequest.status === 'declined' ? (
                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700" data-testid="public-signature-declined-state">
                  <div className="flex items-center gap-2 font-medium"><XCircle className="w-4 h-4" /> This request was declined.</div>
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="public-signature-name">Signer Name</Label>
                    <Input id="public-signature-name" value={form.signer_name} onChange={(event) => setForm((current) => ({ ...current, signer_name: event.target.value }))} data-testid="public-signature-name-input" />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="public-signature-role">Role</Label>
                      <Input id="public-signature-role" value={form.signer_role} onChange={(event) => setForm((current) => ({ ...current, signer_role: event.target.value }))} data-testid="public-signature-role-input" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="public-signature-printed-name">Printed Name</Label>
                      <Input id="public-signature-printed-name" value={form.printed_name} onChange={(event) => setForm((current) => ({ ...current, printed_name: event.target.value }))} data-testid="public-signature-printed-name-input" />
                    </div>
                  </div>
                  <DrawingCanvasPad allowColor={false} autosaveEnabled={false} onChange={({ imageData }) => setSignatureImage(imageData)} />
                  <div className="space-y-2">
                    <Label htmlFor="public-signature-notes">Notes</Label>
                    <Input id="public-signature-notes" value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} data-testid="public-signature-notes-input" />
                  </div>
                  <div className="flex flex-wrap justify-end gap-2">
                    <Button type="button" variant="outline" onClick={declineRequest} disabled={submitting} data-testid="public-signature-decline-button">Decline</Button>
                    <Button type="button" onClick={signRequest} disabled={submitting} data-testid="public-signature-submit-button">{submitting ? 'Saving...' : 'Sign & Confirm'}</Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}