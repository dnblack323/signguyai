import { useState, useEffect } from 'react';
import axios from 'axios';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';
import { getAuthToken } from '../../lib/authStorage';
import { Image as ImageIcon } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SharedArtworkPickerDialog({ open, orderId, onClose, onPicked }) {
  const [files, setFiles] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !orderId) return;
    setLoading(true);
    const token = getAuthToken();
    axios
      .get(`${API}/orders/${orderId}/files?category=artwork`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => setFiles(res.data || []))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  }, [open, orderId]);

  const toggle = (fileId) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(fileId)) next.delete(fileId);
      else next.add(fileId);
      return next;
    });
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent className="max-w-2xl" data-testid="shared-artwork-picker-dialog">
        <DialogHeader>
          <DialogTitle>Select Shared Artwork Files</DialogTitle>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh]">
          {loading && <p className="text-sm text-gray-500 py-4 text-center">Loading artwork…</p>}
          {!loading && files.length === 0 && (
            <div className="py-6 text-center text-sm text-gray-500">
              No shared artwork yet.
              <br />
              <span className="text-xs">Upload artwork on the order's Assets panel first.</span>
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {files.map((f) => {
              const isSelected = selected.has(f.id);
              return (
                <label
                  key={f.id}
                  className={`border rounded-lg p-3 cursor-pointer transition-all ${isSelected ? 'bg-violet-50 border-violet-400' : 'hover:border-violet-200'}`}
                  data-testid={`shared-art-${f.id}`}
                >
                  <div className="flex items-start gap-2">
                    <Checkbox checked={isSelected} onCheckedChange={() => toggle(f.id)} className="mt-1" />
                    <ImageIcon className="w-8 h-8 text-violet-400 mt-1" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{f.label || f.filename}</p>
                      <p className="text-[10px] text-gray-500">{Math.round((f.file_size || 0) / 1024)} KB</p>
                      {f.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {f.tags.slice(0, 2).map((t) => <Badge key={t} variant="outline" className="text-[9px] px-1 py-0">{t}</Badge>)}
                        </div>
                      )}
                    </div>
                  </div>
                </label>
              );
            })}
          </div>
        </ScrollArea>
        <div className="flex justify-between mt-4">
          <p className="text-xs text-gray-500 self-center">{selected.size} file(s) selected</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} data-testid="shared-art-cancel">Cancel</Button>
            <Button
              disabled={selected.size === 0}
              onClick={() => onPicked?.(Array.from(selected))}
              className="bg-violet-600 hover:bg-violet-700 text-white"
              data-testid="shared-art-continue"
            >
              Continue → Pick Category
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
