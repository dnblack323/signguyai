import { useState, useEffect } from 'react';
import { X, Trash2, Loader2, Pen, Calendar, User, Tag, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}` });

const TYPE_COLORS = {
  sketch: 'bg-blue-100 text-blue-700 border-blue-200',
  markup: 'bg-amber-100 text-amber-700 border-amber-200',
  measurement_note: 'bg-amber-100 text-amber-700 border-amber-200',
  install_note: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  layout_note: 'bg-violet-100 text-violet-700 border-violet-200',
  other: 'bg-slate-100 text-slate-700 border-slate-200',
};

export default function DrawingPreviewModal({ drawing, onClose, onDeleted, isAdmin }) {
  const [imgSrc, setImgSrc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  useEffect(() => {
    if (!drawing) return;
    const loadImage = async () => {
      try {
        const res = await axios.get(`${API}/order-drawings/file/${drawing.id}`, {
          headers: hdr(),
          responseType: 'blob',
        });
        setImgSrc(URL.createObjectURL(res.data));
      } catch {
        setImgSrc(null);
      }
      setLoading(false);
    };
    loadImage();
    return () => {
      if (imgSrc) URL.revokeObjectURL(imgSrc);
    };
  }, [drawing]);

  const handleDelete = async () => {
    if (!window.confirm('Delete this drawing permanently?')) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/order-drawings/${drawing.id}`, { headers: hdr() });
      onDeleted?.();
      onClose();
    } catch (e) {
      const detail = e.response?.data?.detail;
      alert(detail || 'Failed to delete');
    }
    setDeleting(false);
  };

  if (!drawing) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.75)' }}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden" data-testid="drawing-preview-modal">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2 min-w-0">
            <Pen className="w-5 h-5 text-violet-600 flex-shrink-0" />
            <h2 className="text-lg font-semibold text-gray-900 truncate">{drawing.label}</h2>
            <Badge variant="outline" className={`${TYPE_COLORS[drawing.type]} text-xs`}>
              {drawing.type}
            </Badge>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-full transition-colors" data-testid="preview-close-btn">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Image */}
        <div className="flex-1 overflow-auto p-4 bg-gray-50 flex items-center justify-center min-h-[200px]">
          {loading ? (
            <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
          ) : imgSrc ? (
            <img
              src={imgSrc}
              alt={drawing.label}
              className="max-w-full max-h-[60vh] rounded-lg border border-gray-200 shadow-sm"
              data-testid="preview-image"
            />
          ) : (
            <p className="text-gray-500">Failed to load image</p>
          )}
        </div>

        {/* Meta */}
        <div className="px-5 py-3 border-t border-gray-200 space-y-1.5">
          <div className="flex flex-wrap gap-4 text-xs text-gray-600">
            <span className="flex items-center gap-1"><User className="w-3 h-3" /> {drawing.created_by}</span>
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(drawing.created_at).toLocaleString()}</span>
            <span className="flex items-center gap-1"><Tag className="w-3 h-3" /> {drawing.type}</span>
          </div>
          {drawing.notes && (
            <div className="flex items-start gap-1 text-xs text-gray-600 mt-1">
              <FileText className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{drawing.notes}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end px-5 py-3 border-t border-gray-200 bg-gray-50 gap-2">
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              className="text-red-500 hover:text-red-600 hover:bg-red-50 border-red-200"
              onClick={handleDelete}
              disabled={deleting}
              data-testid="preview-delete-btn"
            >
              {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Trash2 className="w-4 h-4 mr-1" />}
              Delete
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  );
}
