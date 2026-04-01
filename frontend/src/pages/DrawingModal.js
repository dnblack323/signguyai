import { useEffect, useState } from 'react';
import { X, Save, Loader2, Pen, Image as ImageIcon } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';
import { DrawingCanvasPad } from '../components/DrawingCanvasPad';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}` });

export default function DrawingModal({
  orderId,
  parentType = 'order',
  parentId,
  jobTicketId,
  uploadedImage,
  existingDrawing,
  defaultType = 'sketch',
  onClose,
  onSaved,
  onLocalSave,
}) {
  const [label, setLabel] = useState(existingDrawing?.label || (uploadedImage ? `Markup — ${uploadedImage.label || 'Image'}` : ''));
  const [type, setType] = useState(existingDrawing?.type || defaultType);
  const [notes, setNotes] = useState(existingDrawing?.notes || '');
  const [saving, setSaving] = useState(false);
  const [draftId, setDraftId] = useState(existingDrawing?.id || null);
  const [currentImageData, setCurrentImageData] = useState('');
  const [hasDrawingData, setHasDrawingData] = useState(false);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const saveDrawing = async (status, imageData) => {
    const response = await axios.post(`${API}/order-drawings/`, {
      id: draftId || undefined,
      order_id: orderId,
      parent_type: parentType,
      parent_id: parentId || orderId,
      job_ticket_id: jobTicketId || undefined,
      uploaded_image_id: uploadedImage?.id || undefined,
      drawing_type: type,
      title: (label.trim() || type.replace(/_/g, ' ')).trim(),
      notes: notes.trim(),
      image_data: imageData,
      status,
    }, { headers: { ...hdr(), 'Content-Type': 'application/json' } });
    setDraftId(response.data.id);
    return response.data;
  };

  const handleSave = async () => {
    if (!hasDrawingData || !currentImageData) {
      toast.error('Please draw something before saving');
      return;
    }

    // Local save mode (for new order form — no order ID yet)
    if (onLocalSave) {
      onLocalSave(currentImageData, label.trim() || type, type);
      return;
    }

    setSaving(true);
    try {
      await saveDrawing('saved', currentImageData);
      toast.success('Drawing saved');
      onSaved?.();
      onClose();
    } catch (e) {
      const detail = e.response?.data?.detail;
      toast.error(detail || 'Failed to save drawing');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (hasDrawingData && !window.confirm('Discard this drawing?')) return;
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}>
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[95vh] flex flex-col shadow-2xl overflow-hidden" data-testid="drawing-modal">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Pen className="w-5 h-5 text-violet-600" />
            <h2 className="text-lg font-semibold text-gray-900">New Drawing</h2>
          </div>
          <button onClick={handleClose} className="p-1.5 hover:bg-gray-100 rounded-full transition-colors" data-testid="drawing-close-btn">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {uploadedImage && (
          <div className="px-5 py-3 border-b border-gray-100 bg-amber-50 text-sm text-amber-700 flex items-center gap-2" data-testid="drawing-markup-banner">
            <ImageIcon className="w-4 h-4" /> Markup mode is active for {uploadedImage.label || 'this uploaded image'}.
          </div>
        )}

        {/* Form Fields */}
        <div className="px-5 py-3 flex flex-col sm:flex-row gap-3 border-b border-gray-100">
          <div className="flex-1">
            <Label className="text-xs text-gray-600 mb-1 block">Label</Label>
            <Input
              placeholder="e.g. Customer Approval, Wrap Notes"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="h-9 text-sm bg-white text-gray-900 border-gray-300"
              data-testid="drawing-label-input"
            />
          </div>
          <div className="w-full sm:w-40">
            <Label className="text-xs text-gray-600 mb-1 block">Type</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger className="h-9 text-sm bg-white text-gray-900 border-gray-300" data-testid="drawing-type-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sketch">Sketch</SelectItem>
                <SelectItem value="markup">Markup</SelectItem>
                <SelectItem value="measurement_note">Measurement Note</SelectItem>
                <SelectItem value="install_note">Install Note</SelectItem>
                <SelectItem value="layout_note">Layout Note</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 px-5 py-3 overflow-hidden">
          <DrawingCanvasPad
            backgroundImageUrl={uploadedImage?.contentUrl}
            initialImageUrl={existingDrawing ? `${process.env.REACT_APP_BACKEND_URL}${existingDrawing.image_url}` : undefined}
            autosaveEnabled={!onLocalSave && !!orderId}
            onAutosave={async (imageData) => {
              if (!imageData || !orderId) return;
              try {
                await saveDrawing('draft', imageData);
              } catch {
                // Silent autosave failure to keep the canvas smooth.
              }
            }}
            onChange={({ hasChanges, imageData }) => {
              setHasDrawingData(hasChanges);
              setCurrentImageData(imageData);
            }}
          />
        </div>

        {/* Notes */}
        <div className="px-5 py-2 border-t border-gray-100">
          <Input
            placeholder="Add notes (optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="h-8 text-sm bg-white text-gray-900 border-gray-200"
            data-testid="drawing-notes-input"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500" data-testid="drawing-context-label">
            {parentType === 'job_ticket' ? 'Saving to this item' : uploadedImage ? 'Saving to this image markup' : 'Saving to the full order'}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleClose} data-testid="drawing-cancel-btn">
              Cancel
            </Button>
            <Button
              size="sm"
              className="bg-violet-600 hover:bg-violet-700 text-white"
              onClick={handleSave}
              disabled={saving || !hasDrawingData}
              data-testid="drawing-save-btn"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Save className="w-4 h-4 mr-1" />}
              Save Drawing
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
