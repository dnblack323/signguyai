import { useRef, useState, useEffect, useCallback } from 'react';
import { X, Trash2, Save, Loader2, Pen } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}` });

export default function DrawingModal({ orderId, onClose, onSaved }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [label, setLabel] = useState('');
  const [type, setType] = useState('sketch');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [hasStrokes, setHasStrokes] = useState(false);
  const lastPoint = useRef(null);

  // High DPI canvas setup
  const setupCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = rect.width;
    const h = Math.max(300, Math.min(w * 0.6, 500));

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, w, h);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#0F172A';
    ctx.lineWidth = 2.5;

    setHasStrokes(false);
  }, []);

  useEffect(() => {
    setupCanvas();
    const handleResize = () => setupCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [setupCanvas]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const getPos = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    if (e.touches && e.touches.length > 0) {
      return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    }
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const startDraw = (e) => {
    e.preventDefault();
    setIsDrawing(true);
    const pos = getPos(e);
    lastPoint.current = pos;
    const ctx = canvasRef.current.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    const pos = getPos(e);
    const ctx = canvasRef.current.getContext('2d');

    // Smooth line using quadratic bezier
    if (lastPoint.current) {
      const mid = {
        x: (lastPoint.current.x + pos.x) / 2,
        y: (lastPoint.current.y + pos.y) / 2,
      };
      ctx.quadraticCurveTo(lastPoint.current.x, lastPoint.current.y, mid.x, mid.y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(mid.x, mid.y);
    }
    lastPoint.current = pos;
    setHasStrokes(true);
  };

  const endDraw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    setIsDrawing(false);
    lastPoint.current = null;
    const ctx = canvasRef.current.getContext('2d');
    ctx.closePath();
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.scale(dpr, dpr);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#0F172A';
    ctx.lineWidth = 2.5;
    setHasStrokes(false);
  };

  const handleSave = async () => {
    if (!hasStrokes) {
      toast.error('Please draw something before saving');
      return;
    }

    // Confirm if closing without label
    const finalLabel = label.trim() || `${type.charAt(0).toUpperCase() + type.slice(1)}`;

    setSaving(true);
    try {
      const canvas = canvasRef.current;
      // Export at original resolution for clarity
      const imageData = canvas.toDataURL('image/png');

      await axios.post(`${API}/order-drawings/`, {
        order_id: orderId,
        type,
        label: finalLabel,
        notes: notes.trim(),
        image_data: imageData,
      }, { headers: { ...hdr(), 'Content-Type': 'application/json' } });

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
    if (hasStrokes && !window.confirm('Discard this drawing?')) return;
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}>
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[95vh] flex flex-col shadow-2xl overflow-hidden" data-testid="drawing-modal">
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
                <SelectItem value="signature">Signature</SelectItem>
                <SelectItem value="sketch">Sketch</SelectItem>
                <SelectItem value="markup">Markup</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 px-5 py-3 overflow-hidden" ref={containerRef}>
          <canvas
            ref={canvasRef}
            className="rounded-lg border-2 border-dashed border-gray-300 cursor-crosshair touch-none"
            onMouseDown={startDraw}
            onMouseMove={draw}
            onMouseUp={endDraw}
            onMouseLeave={endDraw}
            onTouchStart={startDraw}
            onTouchMove={draw}
            onTouchEnd={endDraw}
            onTouchCancel={endDraw}
            data-testid="drawing-canvas"
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
          <Button variant="outline" size="sm" onClick={clearCanvas} className="text-red-500 hover:text-red-600 hover:bg-red-50 border-red-200" data-testid="drawing-clear-btn">
            <Trash2 className="w-4 h-4 mr-1" /> Clear
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleClose} data-testid="drawing-cancel-btn">
              Cancel
            </Button>
            <Button
              size="sm"
              className="bg-violet-600 hover:bg-violet-700 text-white"
              onClick={handleSave}
              disabled={saving || !hasStrokes}
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
