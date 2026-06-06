import { Receipt, Mail, FileText } from 'lucide-react';

/**
 * Live preview of how branding settings render across invoices, emails, and
 * documents. Purely presentational — reflects the in-progress `branding` state
 * so the owner sees changes before saving.
 */
export const BrandingPreview = ({ branding = {}, company = {} }) => {
  const primary = branding.primary_color || '#0D9488';
  const accent = branding.invoice_accent_color || primary;
  const emailHeader = branding.email_header_color || primary;
  const logoUrl = company.logo_url;
  const companyName = company.name || 'Your Company';

  const logoAlign =
    branding.invoice_logo_position === 'center'
      ? 'center'
      : branding.invoice_logo_position === 'right'
      ? 'flex-end'
      : 'flex-start';

  const addressLine = [company.city, company.state, company.zip_code].filter(Boolean).join(', ');

  const panelStyle = {
    background: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: '10px',
    overflow: 'hidden',
  };

  return (
    <div className="grid gap-4 lg:grid-cols-3" data-testid="branding-live-preview">
      {/* Invoice preview */}
      <div style={panelStyle} className="flex flex-col" data-testid="branding-preview-invoice">
        <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400 border-b flex items-center gap-1" style={{ borderColor: '#EEF1F4' }}>
          <Receipt className="h-3 w-3" /> Invoice
        </div>
        <div className="p-3 space-y-2 text-[11px] text-gray-700">
          {branding.invoice_show_logo !== false && logoUrl && (
            <div className="flex" style={{ justifyContent: logoAlign }}>
              <img src={logoUrl} alt={companyName} style={{ maxHeight: 24, maxWidth: 90 }} />
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="font-bold tracking-tight" style={{ color: accent, fontSize: 14 }}>INVOICE</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600">SENT</span>
          </div>
          <div className="leading-tight">
            <div className="font-semibold text-gray-900">{companyName}</div>
            {branding.invoice_show_company_info !== false && (
              <>
                {company.address && <div className="text-gray-500">{company.address}</div>}
                {addressLine && <div className="text-gray-500">{addressLine}</div>}
              </>
            )}
          </div>
          <div className="flex justify-between border-t pt-1.5" style={{ borderColor: '#EEF1F4' }}>
            <span>Banner 3x6</span>
            <span>$150.00</span>
          </div>
          <div className="flex justify-between font-bold">
            <span>Balance Due</span>
            <span style={{ color: accent }}>$162.00</span>
          </div>
          {branding.invoice_payment_terms && (
            <div className="text-[10px] text-gray-500">Terms: {branding.invoice_payment_terms}</div>
          )}
          <div className="text-center text-[9px] text-gray-400 border-t pt-1.5" style={{ borderColor: '#EEF1F4' }}>
            {branding.invoice_footer_text || 'Thank you for your business!'}
          </div>
        </div>
      </div>

      {/* Email preview */}
      <div style={panelStyle} className="flex flex-col" data-testid="branding-preview-email">
        <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400 border-b flex items-center gap-1" style={{ borderColor: '#EEF1F4' }}>
          <Mail className="h-3 w-3" /> Email
        </div>
        <div className="flex flex-col">
          <div className="px-3 py-2.5" style={{ background: emailHeader }}>
            {branding.email_show_logo !== false && logoUrl ? (
              <img src={logoUrl} alt={companyName} style={{ maxHeight: 22, maxWidth: 100 }} />
            ) : (
              <span className="text-white font-bold text-[12px]">{companyName}</span>
            )}
          </div>
          <div className="p-3 space-y-1.5 text-[11px] text-gray-700">
            <div className="text-[9px] text-gray-400">From: {branding.email_from_name || companyName}</div>
            <div>Hi Jordan,</div>
            <div className="text-gray-500 leading-snug">Your order is ready for pickup. Thanks for choosing us!</div>
            {branding.email_signature && (
              <div className="border-t pt-1.5 text-gray-500 whitespace-pre-wrap text-[10px]" style={{ borderColor: '#EEF1F4' }}>
                {branding.email_signature}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Document preview */}
      <div style={panelStyle} className="flex flex-col" data-testid="branding-preview-document">
        <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400 border-b flex items-center gap-1" style={{ borderColor: '#EEF1F4' }}>
          <FileText className="h-3 w-3" /> Document (PDF)
        </div>
        <div className="p-3 space-y-2 text-[11px] text-gray-700">
          {branding.document_show_logo !== false && logoUrl && (
            <img src={logoUrl} alt={companyName} style={{ maxHeight: 24, maxWidth: 90 }} />
          )}
          {branding.document_header_text && (
            <div className="text-[10px] text-gray-500">{branding.document_header_text}</div>
          )}
          <div className="font-bold text-gray-900" style={{ fontSize: 13 }}>Sample Document</div>
          <div className="space-y-1 text-gray-500 leading-snug">
            <div>Lorem ipsum dolor sit amet, consectetur.</div>
            <div>Adipiscing elit sed do eiusmod tempor.</div>
          </div>
          {branding.document_footer_text && (
            <div className="text-[9px] text-gray-400 border-t pt-1.5" style={{ borderColor: '#EEF1F4' }}>
              {branding.document_footer_text}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BrandingPreview;
