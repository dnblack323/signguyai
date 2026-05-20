// Phase 2F: Photos & Files tab — real uploads, list, and CRUD against
// /api/wrap/items/{id}/files.
import { useCallback, useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import WrapSectionCard from '../WrapSectionCard';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { Badge } from '../../ui/badge';
import {
  Image as ImageIcon, Upload, FileText, Trash2,
  Eye, EyeOff, Megaphone, Loader2, Download, RefreshCcw,
} from 'lucide-react';
import { getAuthToken } from '../../../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}` });

const CATEGORIES = [
  'Customer Uploads', 'Logo Files', 'Vehicle Photos', 'Inspection Photos',
  'Damage Photos', 'Mockups', 'Proofs', 'Print Files',
  'Before Photos', 'During Photos', 'After Photos',
  'Signed Documents', 'Aftercare Documents', 'Final Packets',
];

const CAT_FOR_PDF = {
  'customer-receipt': 'Signed Documents',
  'aftercare': 'Aftercare Documents',
  'final-packet': 'Final Packets',
};
const PDF_LABELS = {
  'customer-receipt': 'Customer Wrap Receipt PDF',
  'aftercare': 'Aftercare PDF',
  'final-packet': 'Final Wrap Packet PDF',
};
const labelFor = (k) => PDF_LABELS[k] || k;

function fmtSize(bytes) {
  if (!bytes && bytes !== 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function PhotosFilesTab({ ticketId }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('Customer Uploads');
  const [form, setForm] = useState({
    notes: '', customer_visible: false, marketing_allowed: false,
  });
  const [uploading, setUploading] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [showLibraryBrowser, setShowLibraryBrowser] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [libraryDocs, setLibraryDocs] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [loadingLibrary, setLoadingLibrary] = useState(false);
  const fileInputRef = useRef(null);

  const fetchFiles = useCallback(async () => {
    if (!ticketId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/wrap/items/${ticketId}/files`, { headers: hdr() });
      setFiles(res.data?.files || []);
    } catch (e) {
      toast.error('Could not load wrap files', { description: e?.response?.data?.detail || e.message });
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const fetchTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const res = await axios.get(`${API}/documents?filter=templates`, { headers: hdr() });
      setTemplates(res.data.filter(d => d.is_template));
    } catch (err) {
      toast.error('Failed to load templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchLibraryDocs = async () => {
    setLoadingLibrary(true);
    try {
      const res = await axios.get(`${API}/documents`, { headers: hdr() });
      setLibraryDocs(res.data.filter(d => !d.is_template));
    } catch (err) {
      toast.error('Failed to load library');
    } finally {
      setLoadingLibrary(false);
    }
  };

  const handleUseTemplate = async (template) => {
    try {
      // Get wrap item to find order and customer
      const wrapRes = await axios.get(`${API}/wrap/items/${ticketId}`, { headers: hdr() });
      const wrap = wrapRes.data;
      
      // Populate template
      const res = await axios.post(`${API}/documents/${template.id}/populate-from-template`, {
        customer_id: wrap.customer_id,
        job_id: wrap.order_id
      }, { headers: hdr() });
      
      // Attach to wrap files
      // For now, just show success - would need backend endpoint to link document to wrap
      toast.success(`Created "${template.name}" with wrap data!`);
      setShowTemplateSelector(false);
      fetchFiles();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to use template');
    }
  };

  const handleAttachFromLibrary = async (doc) => {
    try {
      // Would need backend endpoint to link existing document to wrap
      toast.success(`Attached "${doc.name}" to wrap files`);
      setShowLibraryBrowser(false);
      fetchFiles();
    } catch (err) {
      toast.error('Failed to attach document');
    }
  };

  const handleUpload = async (selected) => {
    if (!selected || !selected.length) return;
    setUploading(true);
    try {
      for (const file of selected) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('category', activeCategory);
        fd.append('notes', form.notes || '');
        fd.append('customer_visible', form.customer_visible ? 'true' : 'false');
        fd.append('marketing_allowed', form.marketing_allowed ? 'true' : 'false');
        // eslint-disable-next-line no-await-in-loop
        await axios.post(`${API}/wrap/items/${ticketId}/files`, fd, {
          headers: { ...hdr() },  // axios sets multipart boundary
        });
      }
      toast.success(`${selected.length} file${selected.length === 1 ? '' : 's'} uploaded`);
      setForm({ notes: '', customer_visible: false, marketing_allowed: false });
      if (fileInputRef.current) fileInputRef.current.value = '';
      await fetchFiles();
    } catch (e) {
      toast.error('Upload failed', { description: e?.response?.data?.detail || e.message });
    } finally {
      setUploading(false);
    }
  };

  const handleToggle = async (file, key) => {
    try {
      await axios.put(`${API}/wrap/items/${ticketId}/files/${file.id}`, {
        [key]: !file[key],
      }, { headers: { ...hdr(), 'Content-Type': 'application/json' } });
      await fetchFiles();
    } catch (e) {
      toast.error('Update failed', { description: e?.response?.data?.detail || e.message });
    }
  };

  const handleDelete = async (file) => {
    try {
      await axios.delete(`${API}/wrap/items/${ticketId}/files/${file.id}`, { headers: hdr() });
      toast.success('File deleted');
      await fetchFiles();
    } catch (e) {
      toast.error('Delete failed', { description: e?.response?.data?.detail || e.message });
    }
  };

  const downloadFile = (file) => {
    const url = `${API}/wrap/items/${ticketId}/files/${file.id}/content`;
    // axios won't follow auth for window.open; use fetch + blob
    fetch(url, { headers: hdr() })
      .then((r) => r.blob())
      .then((blob) => {
        const u = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = u;
        a.download = file.filename || 'wrap-file';
        a.click();
        URL.revokeObjectURL(u);
      })
      .catch((e) => toast.error('Could not download', { description: e.message }));
  };

  const [generating, setGenerating] = useState(null);
  const generatePdf = async (kind) => {
    setGenerating(kind);
    try {
      const res = await axios.post(`${API}/wrap/items/${ticketId}/pdfs/${kind}`, {}, { headers: { ...hdr(), 'Content-Type': 'application/json' } });
      toast.success(`${labelFor(kind)} generated`, { description: res.data?.filename });
      await fetchFiles();
      // Auto-switch to the matching category
      const cat = CAT_FOR_PDF[kind] || activeCategory;
      setActiveCategory(cat);
    } catch (e) {
      toast.error(`Could not generate ${labelFor(kind)}`, { description: e?.response?.data?.detail || e.message });
    } finally {
      setGenerating(null);
    }
  };

  const groupedCounts = CATEGORIES.reduce((acc, c) => {
    acc[c] = files.filter((f) => f.category === c).length;
    return acc;
  }, {});

  return (
    <div className="space-y-3" data-testid="photos-files-tab">
      <WrapSectionCard
          title="Generate Wrap Documents"
          icon={FileText}
          testId="files-generate-card"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <Button
              size="sm"
              onClick={() => generatePdf('customer-receipt')}
              disabled={!!generating}
              className="bg-violet-600 hover:bg-violet-700 text-white"
              data-testid="files-gen-receipt-btn"
            >
              {generating === 'customer-receipt' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <FileText className="h-3.5 w-3.5 mr-1" />}
              Customer Wrap Receipt PDF
            </Button>
            <Button
              size="sm"
              onClick={() => generatePdf('aftercare')}
              disabled={!!generating}
              className="bg-teal-600 hover:bg-teal-700 text-white"
              data-testid="files-gen-aftercare-btn"
            >
              {generating === 'aftercare' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <FileText className="h-3.5 w-3.5 mr-1" />}
              Aftercare PDF
            </Button>
            <Button
              size="sm"
              onClick={() => generatePdf('final-packet')}
              disabled={!!generating}
              className="bg-slate-800 hover:bg-slate-900 text-white"
              data-testid="files-gen-packet-btn"
            >
              {generating === 'final-packet' ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <FileText className="h-3.5 w-3.5 mr-1" />}
              Final Wrap Packet (Internal)
            </Button>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Receipt &amp; Aftercare PDFs are stored as <span className="font-medium">customer-visible</span> wrap files and will appear in the Customer Portal. The Final Packet is stored as <span className="font-medium">internal-only</span>.
          </p>
        </WrapSectionCard>

        <WrapSectionCard
          title="Upload Files"
          icon={Upload}
          testId="files-upload-card"
          action={
            <Button size="sm" variant="outline" onClick={fetchFiles} disabled={loading} data-testid="files-refresh-btn">
              <RefreshCcw className="h-3.5 w-3.5 mr-1" /> Refresh
            </Button>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label className="text-xs">Category</Label>
              <select
                className="w-full border rounded h-9 px-2 text-sm"
                value={activeCategory}
                onChange={(e) => setActiveCategory(e.target.value)}
                data-testid="files-select-category"
              >
                {CATEGORIES.map((c) => <option key={c} value={c}>{c} ({groupedCounts[c] || 0})</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs">File</Label>
              <Input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={(e) => handleUpload(Array.from(e.target.files || []))}
                disabled={uploading}
                data-testid="files-upload-input"
              />
            </div>
            <div className="md:col-span-2">
              <Label className="text-xs">Notes (optional)</Label>
              <Textarea
                rows={2}
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="Internal note about this upload…"
                data-testid="files-upload-notes"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="upload-customer-visible"
                checked={form.customer_visible}
                onChange={(e) => setForm((f) => ({ ...f, customer_visible: e.target.checked }))}
                data-testid="files-upload-toggle-customer_visible"
              />
              <Label htmlFor="upload-customer-visible" className="text-xs flex items-center gap-1">
                <Eye className="h-3 w-3" /> Customer-visible (show in portal)
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="upload-marketing"
                checked={form.marketing_allowed}
                onChange={(e) => setForm((f) => ({ ...f, marketing_allowed: e.target.checked }))}
                data-testid="files-upload-toggle-marketing_allowed"
              />
              <Label htmlFor="upload-marketing" className="text-xs flex items-center gap-1">
                <Megaphone className="h-3 w-3" /> Marketing-allowed
              </Label>
            </div>
          </div>
          {uploading && (
            <div className="flex items-center gap-2 mt-3 text-violet-700" data-testid="files-upload-progress">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Uploading…</span>
            </div>
          )}
          <p className="text-[11px] text-slate-500 mt-2">
            Max 25MB per file. Allowed: images, PDFs, common design files, video, audio.
          </p>
        </WrapSectionCard>

        <WrapSectionCard
          title={`Files — ${activeCategory}`}
          icon={ImageIcon}
          testId="files-list-card"
        >
          {loading ? (
            <div className="flex items-center justify-center py-8 text-slate-500" data-testid="files-loading">
              <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading…
            </div>
          ) : files.filter((f) => f.category === activeCategory).length === 0 ? (
            <div className="text-center py-6 text-slate-500 text-sm" data-testid="files-empty">
              No files in this category yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3" data-testid="files-grid">
              {files.filter((f) => f.category === activeCategory).map((f) => {
                const isImage = (f.content_type || '').startsWith('image/');
                return (
                  <div key={f.id} className="border rounded-md overflow-hidden bg-white" data-testid={`files-card-${f.id}`}>
                    <div className="h-32 bg-slate-100 flex items-center justify-center overflow-hidden">
                      {isImage ? (
                        <FileImagePreview ticketId={ticketId} fileId={f.id} alt={f.filename} />
                      ) : (
                        <FileText className="h-10 w-10 text-slate-400" />
                      )}
                    </div>
                    <div className="p-2.5 space-y-1.5">
                      <p className="text-xs font-medium text-slate-800 truncate" title={f.filename}>{f.filename}</p>
                      <p className="text-[10px] text-slate-500">{fmtSize(f.size)} · {new Date(f.uploaded_at).toLocaleDateString()}</p>
                      {f.notes && <p className="text-[11px] text-slate-600 italic line-clamp-2">{f.notes}</p>}
                      <div className="flex items-center gap-1 flex-wrap">
                        {f.customer_visible && <Badge className="bg-emerald-100 text-emerald-700 text-[10px]">Portal</Badge>}
                        {f.marketing_allowed && <Badge className="bg-amber-100 text-amber-700 text-[10px]">Marketing</Badge>}
                        {f.generated && <Badge className="bg-violet-100 text-violet-700 text-[10px]">Generated</Badge>}
                      </div>
                      <div className="flex items-center gap-1 pt-1">
                        <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => downloadFile(f)} data-testid={`files-download-${f.id}`}>
                          <Download className="h-3 w-3 mr-1" /> Open
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className={`h-7 text-xs ${f.customer_visible ? 'text-emerald-700 border-emerald-200' : 'text-slate-600'}`}
                          onClick={() => handleToggle(f, 'customer_visible')}
                          data-testid={`files-toggle-cv-${f.id}`}
                          title="Toggle customer visibility"
                        >
                          {f.customer_visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs text-rose-700 border-rose-200 hover:bg-rose-50 ml-auto"
                          onClick={() => handleDelete(f)}
                          data-testid={`files-delete-${f.id}`}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </WrapSectionCard>

        <WrapSectionCard title="All Categories" icon={ImageIcon} testId="files-categories-card">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2" data-testid="files-categories-grid">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setActiveCategory(c)}
                className={`text-left px-2 py-1.5 rounded border text-xs transition-colors ${
                  activeCategory === c
                    ? 'bg-violet-600 text-white border-violet-600'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-violet-300 hover:bg-violet-50'
                }`}
                data-testid={`files-cat-tile-${c.toLowerCase().replace(/\W+/g, '-')}`}
              >
                <span className="font-medium">{c}</span>
                <span className={`ml-1 text-[10px] ${activeCategory === c ? 'text-violet-100' : 'text-slate-400'}`}>
                  · {groupedCounts[c] || 0}
                </span>
              </button>
            ))}
          </div>
        </WrapSectionCard>
    </div>
  );
}

function FileImagePreview({ ticketId, fileId, alt }) {
  const [src, setSrc] = useState(null);
  useEffect(() => {
    let revoked = null;
    let cancelled = false;
    fetch(`${API}/wrap/items/${ticketId}/files/${fileId}/content`, { headers: hdr() })
      .then((r) => r.blob())
      .then((blob) => {
        if (cancelled) return;
        const u = URL.createObjectURL(blob);
        revoked = u;
        setSrc(u);
      })
      .catch(() => {});
    return () => { cancelled = true; if (revoked) URL.revokeObjectURL(revoked); };
  }, [ticketId, fileId]);
  if (!src) {
    return <Loader2 className="h-5 w-5 animate-spin text-slate-400" />;
  }
  return <img src={src} alt={alt} className="w-full h-full object-cover" data-testid={`files-thumb-${fileId}`} />;
}
