// Customer Portal: Vehicle Wrap Project section.
// Renders inside the existing PortalOrderDetail page when order.wrap_items[] is
// populated. Shows customer-safe wrap content + customer action buttons that
// hit the existing portal auth route patterns.

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import { getPortalToken } from '../../lib/authStorage';
import {
  Car, CheckCircle, FileText, Image as ImageIcon, ClipboardCheck,
  LifeBuoy, PencilLine, Eye, Download, Loader2, FileSignature,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function fmtDate(s) {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return s;
  }
}

function fmtMoney(n) {
  if (n === null || n === undefined) return '—';
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
  } catch {
    return `$${n}`;
  }
}

async function portalAction(orderId, ticketId, action, body = null) {
  const token = getPortalToken();
  const res = await fetch(`${API_URL}/api/portal/orders/${orderId}/wrap/${ticketId}/${action}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Action failed (${res.status})`);
  }
  return res.json();
}

function FileRow({ orderId, ticketId, file }) {
  const handleOpen = async () => {
    const token = getPortalToken();
    try {
      const r = await fetch(
        `${API_URL}/api/portal/orders/${orderId}/wrap/${ticketId}/files/${file.id}/content`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!r.ok) throw new Error(`Status ${r.status}`);
      const blob = await r.blob();
      const u = URL.createObjectURL(blob);
      window.open(u, '_blank');
      // Cleanup later
      setTimeout(() => URL.revokeObjectURL(u), 60_000);
    } catch (e) {
      alert(`Could not open file: ${e.message}`);
    }
  };
  return (
    <div
      className="flex items-center justify-between gap-3 p-2 border border-slate-200 rounded bg-white"
      data-testid={`portal-wrap-file-${file.id}`}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {(file.content_type || '').startsWith('image/') ? (
          <ImageIcon className="h-4 w-4 text-violet-500 flex-shrink-0" />
        ) : (
          <FileText className="h-4 w-4 text-slate-500 flex-shrink-0" />
        )}
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate" title={file.filename}>
            {file.filename}
          </p>
          <p className="text-[11px] text-slate-500">
            {file.category} · {fmtDate(file.uploaded_at)}
          </p>
        </div>
      </div>
      <Button size="sm" variant="outline" className="h-7 text-xs" onClick={handleOpen} data-testid={`portal-wrap-file-open-${file.id}`}>
        <Download className="h-3 w-3 mr-1" /> Open
      </Button>
    </div>
  );
}

export default function PortalWrapProjectCard({ orderId, wrap, onRefresh }) {
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');
  const [revisionOpen, setRevisionOpen] = useState(false);
  const [revisionNotes, setRevisionNotes] = useState('');
  const [contractOpen, setContractOpen] = useState(false);
  const [signedBy, setSignedBy] = useState('');

  if (!wrap) return null;

  const runAction = async (key, body = null) => {
    setBusy(key);
    setError('');
    try {
      await portalAction(orderId, wrap.ticket_id, key, body);
      await onRefresh?.();
    } catch (e) {
      setError(e.message || 'Action failed');
    } finally {
      setBusy(null);
    }
  };

  const proofStatus = wrap.design?.proof_status || '';
  const proofApproved = wrap.approvals?.proof_approved;
  const contractSigned = wrap.approvals?.contract_signed;
  const quoteApproved = wrap.approvals?.quote_approved;
  const inspectionVisible = !!wrap.inspection?.customer_visible;
  const inspectionAcked = wrap.approvals?.inspection_acknowledged;
  const aftercareAcked = wrap.aftercare?.customer_acknowledged;

  const filesByCategory = (cat) => (wrap.files || []).filter((f) => f.category === cat);

  return (
    <Card className="border-violet-200" data-testid={`portal-wrap-project-${wrap.ticket_id}`}>
      <CardHeader className="bg-violet-50/40 border-b border-violet-100">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <CardTitle className="text-lg flex items-center gap-2 text-violet-800">
              <Car className="h-5 w-5" />
              Vehicle Wrap Project
            </CardTitle>
            <CardDescription>
              {wrap.wrap_type?.replace(/_/g, ' ')} · {[wrap.vehicle?.year, wrap.vehicle?.make, wrap.vehicle?.model].filter(Boolean).join(' ') || 'Vehicle'}
            </CardDescription>
          </div>
          <Badge className="bg-violet-100 text-violet-800">
            {fmtMoney(wrap.pricing?.quoted_price)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        {error && (
          <div className="text-sm text-rose-700 bg-rose-50 border border-rose-200 p-2 rounded" data-testid="portal-wrap-error">
            {error}
          </div>
        )}

        {/* ─── Quote approval ─── */}
        <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-quote-card">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="font-medium text-slate-900">Quote</p>
              <p className="text-sm text-slate-500">
                Total: <span className="font-medium text-slate-800">{fmtMoney(wrap.pricing?.quoted_price)}</span>
              </p>
            </div>
            {quoteApproved ? (
              <Badge className="bg-emerald-100 text-emerald-700">
                <CheckCircle className="h-3 w-3 mr-1" /> Approved
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={() => runAction('approve-quote')}
                disabled={busy === 'approve-quote' || !wrap.pricing?.quoted_price}
                className="bg-violet-600 hover:bg-violet-700 text-white"
                data-testid="portal-wrap-approve-quote-btn"
              >
                {busy === 'approve-quote' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5 mr-1" />}
                Approve Quote
              </Button>
            )}
          </div>
        </div>

        {/* ─── Proof / Artwork ─── */}
        <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-proof-card">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="font-medium text-slate-900">Artwork / Proof</p>
              <p className="text-sm text-slate-500">
                Status: <span className="font-medium">{(proofStatus || 'pending').replace(/_/g, ' ')}</span>
              </p>
            </div>
            {proofApproved ? (
              <Badge className="bg-emerald-100 text-emerald-700">
                <CheckCircle className="h-3 w-3 mr-1" /> Approved
              </Badge>
            ) : (
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setRevisionOpen((o) => !o)}
                  data-testid="portal-wrap-request-revision-btn"
                >
                  <PencilLine className="h-3.5 w-3.5 mr-1" /> Request Revision
                </Button>
                <Button
                  size="sm"
                  className="bg-violet-600 hover:bg-violet-700 text-white"
                  onClick={() => runAction('approve-proof')}
                  disabled={busy === 'approve-proof'}
                  data-testid="portal-wrap-approve-proof-btn"
                >
                  {busy === 'approve-proof' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <CheckCircle className="h-3.5 w-3.5 mr-1" />}
                  Approve Artwork
                </Button>
              </div>
            )}
          </div>
          {revisionOpen && !proofApproved && (
            <div className="mt-3 space-y-2" data-testid="portal-wrap-revision-form">
              <Textarea
                rows={3}
                placeholder="What would you like changed?"
                value={revisionNotes}
                onChange={(e) => setRevisionNotes(e.target.value)}
                data-testid="portal-wrap-revision-notes"
              />
              <div className="flex items-center justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => { setRevisionOpen(false); setRevisionNotes(''); }} data-testid="portal-wrap-revision-cancel">
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                  onClick={async () => {
                    await runAction('request-revision', { notes: revisionNotes });
                    setRevisionOpen(false);
                    setRevisionNotes('');
                  }}
                  disabled={busy === 'request-revision' || !revisionNotes.trim()}
                  data-testid="portal-wrap-revision-submit"
                >
                  Send Revision Request
                </Button>
              </div>
            </div>
          )}
          {filesByCategory('Proofs').length > 0 && (
            <div className="mt-3 space-y-1" data-testid="portal-wrap-proof-files">
              {filesByCategory('Proofs').map((f) => (
                <FileRow key={f.id} orderId={orderId} ticketId={wrap.ticket_id} file={f} />
              ))}
            </div>
          )}
        </div>

        {/* ─── Contract ─── */}
        <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-contract-card">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="font-medium text-slate-900">Contract</p>
              <p className="text-sm text-slate-500">
                Status: <span className="font-medium">{(wrap.contract?.contract_status || 'pending').replace(/_/g, ' ')}</span>
              </p>
            </div>
            {contractSigned ? (
              <Badge className="bg-emerald-100 text-emerald-700">
                <CheckCircle className="h-3 w-3 mr-1" /> Signed
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={() => setContractOpen((o) => !o)}
                className="bg-violet-600 hover:bg-violet-700 text-white"
                data-testid="portal-wrap-acknowledge-contract-btn"
              >
                <FileSignature className="h-3.5 w-3.5 mr-1" /> Sign Contract
              </Button>
            )}
          </div>
          {wrap.contract?.terms_summary && (
            <details className="mt-2">
              <summary className="text-xs cursor-pointer text-slate-600 underline">View terms summary</summary>
              <pre className="text-xs text-slate-700 whitespace-pre-wrap mt-2 bg-slate-50 p-2 rounded border border-slate-100" data-testid="portal-wrap-terms-summary">
                {wrap.contract.terms_summary}
              </pre>
            </details>
          )}
          {contractOpen && !contractSigned && (
            <div className="mt-3 space-y-2" data-testid="portal-wrap-contract-form">
              <p className="text-xs text-slate-600">
                Type your full name to acknowledge the wrap contract terms above. This counts as your electronic signature.
              </p>
              <Textarea
                rows={1}
                placeholder="Your full name"
                value={signedBy}
                onChange={(e) => setSignedBy(e.target.value)}
                data-testid="portal-wrap-contract-signedby"
              />
              <div className="flex items-center justify-end gap-2">
                <Button size="sm" variant="outline" onClick={() => { setContractOpen(false); setSignedBy(''); }} data-testid="portal-wrap-contract-cancel">
                  Cancel
                </Button>
                <Button
                  size="sm"
                  className="bg-violet-600 hover:bg-violet-700 text-white"
                  onClick={async () => {
                    await runAction('acknowledge-contract', { signed_by: signedBy.trim() || null, accepted_terms: true });
                    setContractOpen(false);
                    setSignedBy('');
                  }}
                  disabled={busy === 'acknowledge-contract'}
                  data-testid="portal-wrap-contract-submit"
                >
                  Acknowledge &amp; Sign
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* ─── Inspection ─── */}
        {inspectionVisible && (
          <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-inspection-card">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <p className="font-medium text-slate-900 flex items-center gap-1">
                  <ClipboardCheck className="h-4 w-4 text-violet-600" /> Vehicle Inspection
                </p>
                <p className="text-sm text-slate-500">
                  {wrap.inspection?.damage_marker_count || 0} pre-existing item{wrap.inspection?.damage_marker_count === 1 ? '' : 's'} noted by the shop.
                </p>
              </div>
              {inspectionAcked ? (
                <Badge className="bg-emerald-100 text-emerald-700">
                  <CheckCircle className="h-3 w-3 mr-1" /> Acknowledged
                </Badge>
              ) : (
                <Button
                  size="sm"
                  className="bg-violet-600 hover:bg-violet-700 text-white"
                  onClick={() => runAction('acknowledge-inspection')}
                  disabled={busy === 'acknowledge-inspection'}
                  data-testid="portal-wrap-acknowledge-inspection-btn"
                >
                  {busy === 'acknowledge-inspection' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <ClipboardCheck className="h-3.5 w-3.5 mr-1" />}
                  Acknowledge Inspection
                </Button>
              )}
            </div>
            {filesByCategory('Inspection Photos').length > 0 && (
              <div className="mt-3 space-y-1" data-testid="portal-wrap-inspection-files">
                {filesByCategory('Inspection Photos').map((f) => (
                  <FileRow key={f.id} orderId={orderId} ticketId={wrap.ticket_id} file={f} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─── Aftercare ─── */}
        <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-aftercare-card">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <p className="font-medium text-slate-900 flex items-center gap-1">
                <LifeBuoy className="h-4 w-4 text-teal-600" /> Aftercare
              </p>
              <p className="text-sm text-slate-500">
                Install date: <span className="font-medium">{fmtDate(wrap.install?.install_date)}</span>
              </p>
            </div>
            {aftercareAcked ? (
              <Badge className="bg-emerald-100 text-emerald-700">
                <CheckCircle className="h-3 w-3 mr-1" /> Received
              </Badge>
            ) : (
              <Button
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white"
                onClick={() => runAction('acknowledge-aftercare')}
                disabled={busy === 'acknowledge-aftercare'}
                data-testid="portal-wrap-acknowledge-aftercare-btn"
              >
                {busy === 'acknowledge-aftercare' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <LifeBuoy className="h-3.5 w-3.5 mr-1" />}
                I Received Aftercare Instructions
              </Button>
            )}
          </div>
          {wrap.care_instructions?.length > 0 && (
            <details className="mt-2">
              <summary className="text-xs cursor-pointer text-slate-600 underline">View care instructions</summary>
              <ul className="list-disc list-inside text-xs text-slate-700 space-y-1 mt-2" data-testid="portal-wrap-care-instructions">
                {wrap.care_instructions.map((line, i) => <li key={i}>{line}</li>)}
              </ul>
            </details>
          )}
          {filesByCategory('Aftercare Documents').length > 0 && (
            <div className="mt-3 space-y-1" data-testid="portal-wrap-aftercare-files">
              {filesByCategory('Aftercare Documents').map((f) => (
                <FileRow key={f.id} orderId={orderId} ticketId={wrap.ticket_id} file={f} />
              ))}
            </div>
          )}
        </div>

        {/* ─── Receipt / Signed Documents ─── */}
        {filesByCategory('Signed Documents').length > 0 && (
          <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-receipts-card">
            <p className="font-medium text-slate-900 mb-2 flex items-center gap-1">
              <FileText className="h-4 w-4 text-violet-600" /> Receipts &amp; Signed Documents
            </p>
            <div className="space-y-1">
              {filesByCategory('Signed Documents').map((f) => (
                <FileRow key={f.id} orderId={orderId} ticketId={wrap.ticket_id} file={f} />
              ))}
            </div>
          </div>
        )}

        {/* ─── Final / After photos ─── */}
        {filesByCategory('After Photos').length > 0 && (
          <div className="border border-slate-200 rounded-lg p-3" data-testid="portal-wrap-after-photos-card">
            <p className="font-medium text-slate-900 mb-2 flex items-center gap-1">
              <Eye className="h-4 w-4 text-emerald-600" /> Final Photos
            </p>
            <div className="space-y-1">
              {filesByCategory('After Photos').map((f) => (
                <FileRow key={f.id} orderId={orderId} ticketId={wrap.ticket_id} file={f} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
