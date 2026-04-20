import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Upload, Trash2, Image as ImageIcon, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ASSET_CATEGORIES = [
  { value: 'artwork', label: 'Artwork' },
  { value: 'logo', label: 'Logo' },
  { value: 'reference', label: 'Reference Image' },
  { value: 'production_note', label: 'Production Note File' },
  { value: 'proof', label: 'Proof' },
  { value: 'other', label: 'Other' },
];

export default function OrderAssetsPanel({ orderId, readOnly = false }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadCategory, setUploadCategory] = useState('artwork');
  const [uploadTags, setUploadTags] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const fileInputRef = useRef(null);

  const load = async () => {
    if (!orderId) return;
    try {
      setLoading(true);
      const token = getAuthToken();
      const url = filterCategory ? `${API}/orders/${orderId}/files?category=${filterCategory}` : `${API}/orders/${orderId}/files`;
      const { data } = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
      setFiles(data || []);
    } catch {
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [orderId, filterCategory]);

  const handleUpload = async (e) => {
    const picked = Array.from(e.target.files || []);
    if (picked.length === 0) return;
    const token = getAuthToken();
    setUploading(true);
    try {
      for (const f of picked) {
        const fd = new FormData();
        fd.append('file', f);
        fd.append('category', uploadCategory);
        fd.append('tags', uploadTags);
        fd.append('is_shared', 'true');
        fd.append('label', f.name);
        await axios.post(`${API}/orders/${orderId}/upload`, fd, { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } });
      }
      toast.success(`${picked.length} file(s) uploaded`);
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const remove = async (id) => {
    try {
      const token = getAuthToken();
      await axios.delete(`${API}/orders/${orderId}/files/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      toast.success('File removed');
      await load();
    } catch {
      toast.error('Remove failed');
    }
  };

  if (!orderId) {
    return (
      <div className="border border-dashed rounded-lg p-4 text-xs text-gray-500 text-center" data-testid="order-assets-panel-empty">
        Save the order first to upload shared artwork & assets.
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-3 bg-white" data-testid="order-assets-panel">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Shared Artwork & Assets</p>
        <div className="flex items-center gap-2">
          <Select value={filterCategory || 'all'} onValueChange={(v) => setFilterCategory(v === 'all' ? '' : v)}>
            <SelectTrigger className="h-7 text-xs w-36" data-testid="assets-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {ASSET_CATEGORIES.map((c) => (<SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!readOnly && (
        <div className="flex flex-wrap items-end gap-2 mb-3 p-2 border-dashed border rounded bg-slate-50">
          <div>
            <Label className="text-[10px] text-gray-500">Category</Label>
            <Select value={uploadCategory} onValueChange={setUploadCategory}>
              <SelectTrigger className="h-7 text-xs w-36" data-testid="asset-upload-category"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ASSET_CATEGORIES.map((c) => (<SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-[10px] text-gray-500">Tags (comma-sep)</Label>
            <Input value={uploadTags} onChange={(e) => setUploadTags(e.target.value)} className="h-7 text-xs w-44" placeholder="primary, vector" data-testid="asset-upload-tags" />
          </div>
          <Button
            size="sm"
            variant="outline"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
            data-testid="asset-upload-button"
          >
            {uploading ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Upload className="w-3 h-3 mr-1" />}
            Upload Files
          </Button>
          <input
            type="file"
            multiple
            ref={fileInputRef}
            onChange={handleUpload}
            className="hidden"
            data-testid="asset-file-input"
          />
        </div>
      )}

      {loading ? (
        <p className="text-xs text-gray-500 py-3 text-center">Loading…</p>
      ) : files.length === 0 ? (
        <p className="text-xs text-gray-500 py-6 text-center">No assets yet. Upload once, reuse across all items.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
          {files.map((f) => (
            <div key={f.id} className="border rounded p-2 text-xs flex items-center gap-2 bg-slate-50" data-testid={`asset-row-${f.id}`}>
              <ImageIcon className="w-5 h-5 text-violet-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="truncate font-medium">{f.label || f.filename}</p>
                <div className="flex items-center gap-1">
                  <Badge variant="outline" className="text-[9px] px-1 py-0">{f.category || 'artwork'}</Badge>
                  <span className="text-[10px] text-gray-500">{Math.round((f.file_size || 0) / 1024)}KB</span>
                  {f.linked_item_ids?.length > 0 && (
                    <Badge className="text-[9px] bg-violet-100 text-violet-700 px-1 py-0">{f.linked_item_ids.length} items</Badge>
                  )}
                </div>
              </div>
              {!readOnly && (
                <button onClick={() => remove(f.id)} className="text-gray-400 hover:text-red-500" data-testid={`asset-remove-${f.id}`}>
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
