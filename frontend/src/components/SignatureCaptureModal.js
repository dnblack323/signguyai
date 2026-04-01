import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { DrawingCanvasPad } from './DrawingCanvasPad';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const headers = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

export const SignatureCaptureModal = ({ open, onClose, context, onSaved }) => {
  const [saving, setSaving] = useState(false);
  const [signatureImage, setSignatureImage] = useState('');
  const [form, setForm] = useState({ signer_name: '', signer_role: '', printed_name: '', notes: '' });

  const handleSave = async () => {
    if (!form.signer_name.trim()) {
      toast.error('Signer name is required');
      return;
    }
    if (!signatureImage) {
      toast.error('Please add a signature before saving');
      return;
    }
    setSaving(true);
    try {
      await axios.post(`${API}/signatures/capture`, {
        parent_record_type: context.parentRecordType,
        parent_record_id: context.parentRecordId,
        order_id: context.orderId,
        job_ticket_id: context.jobTicketId,
        signature_type: context.signatureType,
        document_version: context.documentVersion,
        signer_name: form.signer_name,
        signer_role: form.signer_role,
        printed_name: form.printed_name || form.signer_name,
        notes: form.notes,
        image_data: signatureImage,
      }, { headers: headers() });
      toast.success('Signature saved');
      onSaved?.();
      onClose?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save signature');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose?.()}>
      <DialogContent className="sm:max-w-[760px]" data-testid="signature-capture-modal">
        <DialogHeader>
          <DialogTitle data-testid="signature-capture-title">Capture Signature</DialogTitle>
          <DialogDescription>Capture an internal signature for this exact record and store who signed, when, and what was approved.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="signature-signer-name">Signer Name</Label>
              <Input id="signature-signer-name" value={form.signer_name} onChange={(event) => setForm((current) => ({ ...current, signer_name: event.target.value }))} data-testid="signature-signer-name-input" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="signature-signer-role">Role</Label>
              <Input id="signature-signer-role" value={form.signer_role} onChange={(event) => setForm((current) => ({ ...current, signer_role: event.target.value }))} placeholder="Customer" data-testid="signature-signer-role-input" />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="signature-printed-name">Printed Name</Label>
            <Input id="signature-printed-name" value={form.printed_name} onChange={(event) => setForm((current) => ({ ...current, printed_name: event.target.value }))} data-testid="signature-printed-name-input" />
          </div>
          <DrawingCanvasPad allowColor={false} autosaveEnabled={false} onChange={({ imageData }) => setSignatureImage(imageData)} />
          <div className="space-y-2">
            <Label htmlFor="signature-notes">Notes</Label>
            <Input id="signature-notes" value={form.notes} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} data-testid="signature-notes-input" />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} data-testid="signature-cancel-button">Cancel</Button>
            <Button type="button" onClick={handleSave} disabled={saving} data-testid="signature-save-button">{saving ? 'Saving...' : 'Save Signature'}</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};