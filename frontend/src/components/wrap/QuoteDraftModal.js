// Phase 2C: Modal that shows a generated "Updated Quote" email draft.
// Pure presentation — editing subject/body and copy-to-clipboard live here.
import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Label } from '../ui/label';
import { Copy, Check, X } from 'lucide-react';
import { toast } from 'sonner';

export default function QuoteDraftModal({ open, onClose, draft }) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (draft) {
      setSubject(draft.subject || '');
      setBody(draft.body || '');
      setCopied(false);
    }
  }, [draft]);

  const handleCopy = async () => {
    const text = `Subject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Quote draft copied to clipboard');
      setTimeout(() => setCopied(false), 1500);
    } catch (_) {
      toast.error('Copy failed — select and copy manually');
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose?.(); }}>
      <DialogContent className="max-w-2xl" data-testid="quote-draft-modal">
        <DialogHeader>
          <DialogTitle>Draft Updated Quote Message</DialogTitle>
          <DialogDescription>
            Editable email draft built from this wrap's current pricing, vehicle, and customer info.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600" data-testid="quote-draft-meta">
            {draft?.to && <span data-testid="quote-draft-to"><span className="text-slate-500">To:</span> {draft.to}</span>}
            {draft?.customer_name && <span><span className="text-slate-500">Customer:</span> {draft.customer_name}</span>}
            {draft?.order_number && <span><span className="text-slate-500">Order:</span> #{draft.order_number}</span>}
            {draft?.vehicle_summary && <span><span className="text-slate-500">Vehicle:</span> {draft.vehicle_summary}</span>}
            {typeof draft?.quote_amount === 'number' && <span data-testid="quote-draft-amount"><span className="text-slate-500">Quote:</span> ${draft.quote_amount.toFixed(2)}</span>}
          </div>
          <div>
            <Label className="text-xs">Subject</Label>
            <Input value={subject} onChange={(e) => setSubject(e.target.value)} data-testid="quote-draft-subject" />
          </div>
          <div>
            <Label className="text-xs">Body</Label>
            <Textarea rows={12} value={body} onChange={(e) => setBody(e.target.value)} className="font-mono text-xs" data-testid="quote-draft-body" />
          </div>
          {!draft?.to && (
            <p className="text-[11px] text-amber-700" data-testid="quote-draft-no-email">
              No customer email on file — copy the draft and send manually for now.
            </p>
          )}
        </div>
        <DialogFooter className="flex items-center justify-between">
          <Button variant="outline" onClick={onClose} data-testid="quote-draft-close"><X className="h-3.5 w-3.5 mr-1" /> Close</Button>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => toast.message('Send Later', { description: 'Scheduled-send will be connected in a later phase.' })} data-testid="quote-draft-send-later">
              Send Later (placeholder)
            </Button>
            <Button onClick={handleCopy} className="bg-violet-600 hover:bg-violet-700 text-white" data-testid="quote-draft-copy">
              {copied ? <><Check className="h-3.5 w-3.5 mr-1" /> Copied</> : <><Copy className="h-3.5 w-3.5 mr-1" /> Copy Draft</>}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
