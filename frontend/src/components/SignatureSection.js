import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { useSignatureFeature } from '../hooks/useSignatureFeature';
import { SignatureCaptureModal } from './SignatureCaptureModal';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/json' });

const STATUS_STYLES = {
  pending: 'bg-amber-100 text-amber-700',
  signed: 'bg-emerald-100 text-emerald-700',
  declined: 'bg-red-100 text-red-700',
  expired: 'bg-slate-200 text-slate-700',
};

export const SignatureSection = ({
  parentRecordType,
  parentRecordId,
  orderId,
  jobTicketId,
  signatureType,
  documentVersion,
  title = 'Signature',
  compact = false,
}) => {
  const { enabled } = useSignatureFeature();
  const [loading, setLoading] = useState(true);
  const [signatures, setSignatures] = useState([]);
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const [showCaptureDialog, setShowCaptureDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [requestForm, setRequestForm] = useState({ request_email: '', signer_name: '', signer_role: 'customer', notes: '', expires_in_days: 7 });

  const loadSignatures = async () => {
    if (!enabled) {
      setLoading(false);
      setSignatures([]);
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get(`${API}/signatures`, {
        headers: headers(),
        params: {
          parent_record_type: parentRecordType,
          parent_record_id: parentRecordId,
        },
      });
      setSignatures(response.data || []);
    } catch {
      setSignatures([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSignatures(); }, [enabled, parentRecordId, parentRecordType]);

  const latestSignature = useMemo(() => signatures[0] || null, [signatures]);
  const requiresSignature = !!latestSignature?.requires_signature;

  if (!enabled) return null;

  const upsertRequirement = async (nextValue) => {
    try {
      await axios.post(`${API}/signatures/requirement`, {
        parent_record_type: parentRecordType,
        parent_record_id: parentRecordId,
        order_id: orderId,
        job_ticket_id: jobTicketId,
        signature_type: signatureType,
        document_version: documentVersion,
        requires_signature: nextValue,
      }, { headers: headers() });
      await loadSignatures();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update signature requirement');
    }
  };

  const sendRequest = async () => {
    if (!requestForm.request_email.trim()) {
      toast.error('Email is required');
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/signatures/request`, {
        parent_record_type: parentRecordType,
        parent_record_id: parentRecordId,
        order_id: orderId,
        job_ticket_id: jobTicketId,
        signature_type: signatureType,
        document_version: documentVersion,
        request_email: requestForm.request_email,
        signer_name: requestForm.signer_name,
        signer_role: requestForm.signer_role,
        notes: requestForm.notes,
        expires_in_days: Number(requestForm.expires_in_days || 7),
        origin_url: window.location.origin,
      }, { headers: headers() });
      toast.success('Signature request emailed');
      setShowRequestDialog(false);
      await loadSignatures();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send request');
    } finally {
      setSubmitting(false);
    }
  };

  const content = (
    <>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-gray-900">{title}</p>
          <p className="text-xs text-gray-500">Request, capture, and review signatures for this record.</p>
        </div>
        <div className="flex items-center gap-2">
          {loading ? <span className="text-xs text-gray-400">Loading…</span> : latestSignature && <Badge className={STATUS_STYLES[latestSignature.status] || STATUS_STYLES.pending}>{latestSignature.status}</Badge>}
          <div className="flex items-center gap-2">
            <Label className="text-xs text-gray-600">Requires Signature</Label>
            <Switch checked={requiresSignature} onCheckedChange={upsertRequirement} data-testid={`signature-toggle-${parentRecordType}-${parentRecordId}`} />
          </div>
        </div>
      </div>

      {latestSignature && (
        <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
          <div className="space-y-1 text-sm text-gray-600" data-testid={`signature-summary-${parentRecordType}-${parentRecordId}`}>
            <p><span className="font-medium text-gray-800">Signature Type:</span> {latestSignature.signature_type?.replace(/_/g, ' ')}</p>
            <p><span className="font-medium text-gray-800">Signed By:</span> {latestSignature.printed_name || latestSignature.signer_name || '—'}</p>
            <p><span className="font-medium text-gray-800">Signed At:</span> {latestSignature.signed_at ? new Date(latestSignature.signed_at).toLocaleString() : 'Pending'}</p>
            {latestSignature.document_version && <p><span className="font-medium text-gray-800">Version:</span> {latestSignature.document_version}</p>}
          </div>
          {latestSignature.signature_image && <img src={`${process.env.REACT_APP_BACKEND_URL}${latestSignature.signature_image}`} alt="Signature" className="h-20 rounded-lg border border-gray-200 bg-white p-2" data-testid={`signature-preview-${parentRecordId}`} />}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="outline" size="sm" onClick={() => setShowRequestDialog(true)} disabled={!requiresSignature} data-testid={`signature-request-button-${parentRecordId}`}>Request Signature</Button>
        <Button type="button" size="sm" onClick={() => setShowCaptureDialog(true)} disabled={!requiresSignature} data-testid={`signature-capture-button-${parentRecordId}`}>Capture Signature</Button>
      </div>
    </>
  );

  return (
    <>
      {compact ? <div className="space-y-3 rounded-xl border border-gray-200 p-3">{content}</div> : (
        <Card className="bg-white border-gray-200">
          <CardHeader className="pb-3"><CardTitle className="text-base text-gray-900">{title}</CardTitle></CardHeader>
          <CardContent className="space-y-3">{content}</CardContent>
        </Card>
      )}

      <Dialog open={showRequestDialog} onOpenChange={setShowRequestDialog}>
        <DialogContent className="sm:max-w-[460px]" data-testid={`signature-request-dialog-${parentRecordId}`}>
          <DialogHeader><DialogTitle>Request Signature</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="signature-request-email">Customer Email</Label>
              <Input id="signature-request-email" value={requestForm.request_email} onChange={(event) => setRequestForm((current) => ({ ...current, request_email: event.target.value }))} data-testid="signature-request-email-input" />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="signature-request-name">Signer Name</Label>
                <Input id="signature-request-name" value={requestForm.signer_name} onChange={(event) => setRequestForm((current) => ({ ...current, signer_name: event.target.value }))} data-testid="signature-request-name-input" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signature-request-role">Role</Label>
                <Input id="signature-request-role" value={requestForm.signer_role} onChange={(event) => setRequestForm((current) => ({ ...current, signer_role: event.target.value }))} data-testid="signature-request-role-input" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="signature-request-expiry">Expires In (days)</Label>
              <Input id="signature-request-expiry" type="number" min="1" max="30" value={requestForm.expires_in_days} onChange={(event) => setRequestForm((current) => ({ ...current, expires_in_days: event.target.value }))} data-testid="signature-request-expiry-input" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="signature-request-notes">Message</Label>
              <Input id="signature-request-notes" value={requestForm.notes} onChange={(event) => setRequestForm((current) => ({ ...current, notes: event.target.value }))} data-testid="signature-request-notes-input" />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setShowRequestDialog(false)} data-testid="signature-request-cancel-button">Cancel</Button>
              <Button type="button" onClick={sendRequest} disabled={submitting} data-testid="signature-request-submit-button">{submitting ? 'Sending...' : 'Send Link'}</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <SignatureCaptureModal
        open={showCaptureDialog}
        onClose={() => setShowCaptureDialog(false)}
        onSaved={loadSignatures}
        context={{ parentRecordType, parentRecordId, orderId, jobTicketId, signatureType, documentVersion }}
      />
    </>
  );
};