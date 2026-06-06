/**
 * StoreSnapshotModal — generates a branded, printable/saveable PDF snapshot
 * of a webstore. Includes QR code, key stats, top products, fundraiser
 * progress and event deadline info.
 *
 * No new dependencies required — uses QRCodeCanvas (qrcode.react, already
 * installed) to produce a data-URL for the print window, and plain inline
 * styles for cross-window portability.
 */
import { useRef, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { QRCodeCanvas } from 'qrcode.react';
import { formatCurrency } from '../lib/utils';
import { Printer, Download, X, Store, TrendingUp, ShoppingCart, DollarSign, Package } from 'lucide-react';

// ── helpers ──────────────────────────────────────────────────────────────────
const storeTypeLabel = (t) => ({
  business: 'Business (B2B)',
  fundraiser: 'Fundraiser',
  creator: 'Creator / Team',
  event: 'Event Store',
}[t] || t);

const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : null;

// ── StoreSnapshotModal ────────────────────────────────────────────────────────
export default function StoreSnapshotModal({ store, analytics, open, onClose }) {
  const qrCanvasRef = useRef(null);
  const [printing, setPrinting] = useState(false);

  if (!store) return null;

  const storeUrl    = `${window.location.origin}/store/${store.id}`;
  const accent      = store?.branding?.primary_color || '#0D9488';
  const logoUrl     = store?.branding?.logo_url || store?.logo_url || null;
  const summary     = analytics?.summary || {};
  const topProducts = Array.isArray(analytics?.top_products) ? analytics.top_products.slice(0, 5) : [];
  const fundraiser  = analytics?.fundraiser_metrics || null;

  const deadlineDate = store?.order_deadline || store?.event_end_date || null;
  const pickupDate   = store?.pickup_delivery_date || null;

  // ── print handler ─────────────────────────────────────────────────────────
  const handlePrint = () => {
    setPrinting(true);

    // Grab QR as data URL from the hidden canvas
    let qrDataUrl = '';
    try {
      const canvas = qrCanvasRef.current?.querySelector('canvas');
      if (canvas) qrDataUrl = canvas.toDataURL('image/png');
    } catch (_) {}

    const topProductsHtml = topProducts.length
      ? topProducts.map((p, i) => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-radius:6px;background:${i % 2 === 0 ? '#f8f8f8' : '#fff'};font-size:13px;">
            <span><strong>${i + 1}.</strong> ${p.name}</span>
            <span style="font-weight:600;color:#059669">${formatCurrency(p.revenue)}</span>
          </div>`).join('')
      : '<p style="color:#888;font-size:13px;">No sales recorded yet</p>';

    const fundraiserHtml = fundraiser ? `
      <div style="margin-top:20px;padding:16px;border-radius:8px;background:#f0fdf4;border:1px solid #86efac;">
        <h3 style="font-size:14px;font-weight:600;color:#166534;margin-bottom:10px;">Fundraiser Progress</h3>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <span style="font-size:22px;font-weight:700;color:#16a34a">${formatCurrency(fundraiser.raised)}</span>
          <span style="font-size:16px;font-weight:600;color:#166534">${(Number(fundraiser.progress_percent) || 0).toFixed(1)}%</span>
        </div>
        <div style="background:#dcfce7;border-radius:9999px;height:10px;overflow:hidden;">
          <div style="background:#16a34a;height:100%;width:${Math.min(fundraiser.progress_percent || 0, 100)}%;border-radius:9999px;"></div>
        </div>
        <p style="margin-top:6px;font-size:12px;color:#166534;">of ${formatCurrency(fundraiser.goal)} goal</p>
      </div>` : '';

    const deadlineHtml = (deadlineDate || pickupDate) ? `
      <div style="margin-top:16px;padding:12px 16px;border-radius:8px;background:#fff7ed;border:1px solid #fed7aa;font-size:13px;color:#9a3412;">
        ${deadlineDate ? `<div><strong>Order Deadline:</strong> ${fmtDate(deadlineDate)}</div>` : ''}
        ${pickupDate   ? `<div style="margin-top:4px;"><strong>Pickup / Delivery:</strong> ${fmtDate(pickupDate)}</div>` : ''}
      </div>` : '';

    const statsHtml = `
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-top:20px;">
        ${[
          { label: 'Total Revenue',  value: formatCurrency(summary.total_revenue), color: '#059669' },
          { label: 'Total Orders',   value: summary.total_orders ?? '—',           color: '#2563eb' },
          { label: 'Avg. Order',     value: formatCurrency(summary.average_order_value), color: '#7c3aed' },
          { label: 'Items Sold',     value: summary.total_items_sold ?? '—',       color: '#d97706' },
        ].map(s => `
          <div style="padding:12px;border-radius:8px;background:#f9fafb;border:1px solid #e5e7eb;text-align:center;">
            <div style="font-size:20px;font-weight:700;color:${s.color}">${s.value}</div>
            <div style="font-size:11px;color:#6b7280;margin-top:2px;">${s.label}</div>
          </div>`).join('')}
      </div>`;

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${store.name} — Store Snapshot</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; color: #111; background: #fff; }
    @page { size: A4 portrait; margin: 0.6in; }
    @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  </style>
</head>
<body style="padding:32px;">

  <!-- Header bar -->
  <div style="background:${accent};border-radius:10px;padding:20px 24px;display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    ${logoUrl ? `<img src="${logoUrl}" style="height:56px;width:auto;object-fit:contain;background:#fff;border-radius:6px;padding:4px;" onerror="this.style.display='none'" />` : ''}
    <div style="flex:1;">
      <h1 style="font-size:22px;font-weight:700;color:#fff;letter-spacing:-0.5px;">${store.name}</h1>
      <div style="margin-top:4px;display:flex;gap:8px;flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,0.2);color:#fff;font-size:11px;padding:2px 8px;border-radius:999px;font-weight:500;">${storeTypeLabel(store.store_type)}</span>
        <span style="background:${store.status === 'active' ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.15)'};color:#fff;font-size:11px;padding:2px 8px;border-radius:999px;font-weight:500;">${store.status}</span>
      </div>
    </div>
    <div style="font-size:11px;color:rgba(255,255,255,0.7);text-align:right;">
      Generated ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
    </div>
  </div>

  <!-- QR + URL -->
  <div style="display:flex;gap:24px;align-items:flex-start;margin-bottom:20px;">
    <div style="text-align:center;padding:16px;border-radius:10px;border:1px solid #e5e7eb;background:#f9fafb;min-width:160px;">
      ${qrDataUrl ? `<img src="${qrDataUrl}" style="width:128px;height:128px;" />` : ''}
      <div style="font-size:10px;color:#6b7280;margin-top:8px;word-break:break-all;max-width:140px;">${storeUrl}</div>
    </div>
    <div style="flex:1;">
      ${deadlineHtml}
      ${fundraiserHtml}
    </div>
  </div>

  <!-- Stats -->
  ${statsHtml}

  <!-- Top Products -->
  ${topProducts.length ? `
  <div style="margin-top:24px;">
    <h3 style="font-size:13px;font-weight:600;color:#374151;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px;">Top Products</h3>
    ${topProductsHtml}
  </div>` : ''}

  <!-- Footer -->
  <div style="margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#9ca3af;">
    <span>SignGuy AI — Sign Shop Operating System</span>
    <span>Store ID: ${store.id.slice(0, 8).toUpperCase()}</span>
  </div>

</body>
</html>`;

    const win = window.open('', '_blank', 'width=850,height=1100');
    if (!win) {
      setPrinting(false);
      return;
    }
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => {
      win.print();
      win.close();
      setPrinting(false);
    }, 700);
  };

  // ── preview render ─────────────────────────────────────────────────────────
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto" data-testid="store-snapshot-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 font-heading uppercase">
            <Store className="h-4 w-4" />
            Store Snapshot
          </DialogTitle>
        </DialogHeader>

        {/* Snapshot preview */}
        <div className="space-y-4 mt-1">

          {/* Header bar */}
          <div
            className="rounded-xl p-5 flex items-center gap-4"
            style={{ background: accent }}
          >
            {logoUrl && (
              <img
                src={logoUrl}
                alt="logo"
                className="h-14 w-auto object-contain bg-white rounded-lg p-1"
              />
            )}
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white">{store.name}</h2>
              <div className="flex gap-2 mt-1 flex-wrap">
                <span className="text-xs text-white/80 bg-white/20 rounded-full px-2 py-0.5">{storeTypeLabel(store.store_type)}</span>
                <span className={`text-xs text-white/80 rounded-full px-2 py-0.5 ${store.status === 'active' ? 'bg-emerald-500/40' : 'bg-white/15'}`}>{store.status}</span>
              </div>
            </div>
            <p className="text-xs text-white/60">{new Date().toLocaleDateString()}</p>
          </div>

          {/* QR + Deadline row */}
          <div className="flex gap-4 flex-wrap">
            <div className="p-4 rounded-xl border bg-muted/30 flex flex-col items-center gap-2 min-w-[148px]">
              <QRCodeCanvas
                value={storeUrl}
                size={120}
                level="M"
                data-testid="snapshot-qr-canvas"
              />
              {/* hidden canvas reference for data URL extraction */}
              <div ref={qrCanvasRef} className="hidden">
                <QRCodeCanvas value={storeUrl} size={160} level="M" />
              </div>
              <p className="text-[10px] text-muted-foreground text-center break-all max-w-[130px]">{storeUrl}</p>
            </div>

            <div className="flex-1 space-y-3 min-w-[160px]">
              {(deadlineDate || pickupDate) && (
                <div className="p-3 rounded-lg bg-orange-50 border border-orange-200 text-sm text-orange-800 space-y-1">
                  {deadlineDate && <p><strong>Order Deadline:</strong> {fmtDate(deadlineDate)}</p>}
                  {pickupDate   && <p><strong>Pickup/Delivery:</strong> {fmtDate(pickupDate)}</p>}
                </div>
              )}
              {fundraiser && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-emerald-700">{formatCurrency(fundraiser.raised)}</span>
                    <span className="text-sm font-semibold text-emerald-600">{(Number(fundraiser.progress_percent) || 0).toFixed(1)}%</span>
                  </div>
                  <Progress value={fundraiser.progress_percent} className="h-2" />
                  <p className="text-xs text-emerald-700">of {formatCurrency(fundraiser.goal)} goal</p>
                </div>
              )}
            </div>
          </div>

          {/* KPI stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: DollarSign,    label: 'Total Revenue', value: formatCurrency(summary.total_revenue),        color: 'text-emerald-600' },
              { icon: ShoppingCart,  label: 'Total Orders',  value: summary.total_orders ?? '—',                  color: 'text-blue-600'    },
              { icon: TrendingUp,    label: 'Avg. Order',    value: formatCurrency(summary.average_order_value),   color: 'text-purple-600'  },
              { icon: Package,       label: 'Items Sold',    value: summary.total_items_sold ?? '—',               color: 'text-amber-600'   },
            ].map(({ icon: Icon, label, value, color }) => (
              <div key={label} className="p-3 rounded-lg border bg-muted/30 text-center">
                <p className={`text-xl font-bold ${color}`}>{value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Top products */}
          {topProducts.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Top Products</p>
              <div className="space-y-1">
                {topProducts.map((p, i) => (
                  <div key={p.product_id} className={`flex justify-between items-center px-3 py-2 rounded-lg text-sm ${i % 2 === 0 ? 'bg-muted/40' : ''}`}>
                    <span><strong>{i + 1}.</strong> {p.name} <span className="text-muted-foreground text-xs">({p.quantity} sold)</span></span>
                    <span className="font-semibold text-emerald-600">{formatCurrency(p.revenue)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <p className="text-[11px] text-muted-foreground border-t pt-3 flex justify-between">
            <span>SignGuy AI — Sign Shop Operating System</span>
            <span>ID: {store.id.slice(0, 8).toUpperCase()}</span>
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={onClose} data-testid="snapshot-close-btn">
            <X className="h-4 w-4 mr-1" /> Close
          </Button>
          <Button
            size="sm"
            onClick={handlePrint}
            disabled={printing}
            className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90 text-white"
            data-testid="snapshot-print-btn"
          >
            <Printer className="h-4 w-4 mr-1" />
            {printing ? 'Opening...' : 'Print / Save as PDF'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
