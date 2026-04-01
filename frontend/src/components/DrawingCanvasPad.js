import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, Loader2, Palette, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const COLORS = [
  { value: '#0F172A', label: 'Slate' },
  { value: '#2563EB', label: 'Blue' },
  { value: '#DC2626', label: 'Red' },
  { value: '#059669', label: 'Green' },
  { value: '#D97706', label: 'Amber' },
];

const SIZES = ['2', '4', '6', '8', '12'];

const waitForImage = (src) => new Promise((resolve) => {
  const image = new Image();
  image.crossOrigin = 'anonymous';
  image.onload = () => resolve(image);
  image.onerror = () => resolve(image);
  image.src = src;
});

const configureContext = (context, strokeColor, penSize) => {
  context.lineCap = 'round';
  context.lineJoin = 'round';
  context.strokeStyle = strokeColor;
  context.lineWidth = Number(penSize);
};

const drawCenteredImage = (context, image, width, height) => {
  if (!image.width || !image.height) return;
  const scale = Math.min(width / image.width, height / image.height);
  const drawWidth = image.width * scale;
  const drawHeight = image.height * scale;
  const offsetX = (width - drawWidth) / 2;
  const offsetY = (height - drawHeight) / 2;
  context.drawImage(image, offsetX, offsetY, drawWidth, drawHeight);
};

const getCanvasPosition = (canvas, event) => {
  const rect = canvas.getBoundingClientRect();
  if (event.touches?.length) {
    return { x: event.touches[0].clientX - rect.left, y: event.touches[0].clientY - rect.top };
  }
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
};

const getCanvasSnapshot = (canvas) => canvas.toDataURL('image/png');

export const DrawingCanvasPad = ({
  backgroundImageUrl,
  initialImageUrl,
  autosaveEnabled = false,
  allowColor = true,
  allowPenSize = true,
  onAutosave,
  onChange,
}) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const baseSnapshotRef = useRef(null);
  const historyRef = useRef([]);
  const drawIdleTimeoutRef = useRef(null);
  const autosaveIntervalRef = useRef(null);
  const lastPointRef = useRef(null);

  const [loadingBase, setLoadingBase] = useState(true);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#0F172A');
  const [penSize, setPenSize] = useState('4');
  const [autosaveState, setAutosaveState] = useState('');

  const applySnapshot = useCallback((snapshot) => {
    const canvas = canvasRef.current;
    if (!canvas || !snapshot) return;
    const context = canvas.getContext('2d');
    waitForImage(snapshot).then((image) => {
      context.setTransform(1, 0, 0, 1, 0, 0);
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      context.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);
      configureContext(context, strokeColor, penSize);
    });
  }, [penSize, strokeColor]);

  const buildBaseCanvas = useCallback(async () => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    setLoadingBase(true);

    const width = container.clientWidth;
    const height = Math.max(320, Math.min(width * 0.62, 520));
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const context = canvas.getContext('2d');
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.scale(dpr, dpr);
    context.fillStyle = '#FFFFFF';
    context.fillRect(0, 0, width, height);

    if (backgroundImageUrl) {
      const image = await waitForImage(backgroundImageUrl);
      drawCenteredImage(context, image, width, height);
    }

    const baseSnapshot = getCanvasSnapshot(canvas);
    baseSnapshotRef.current = baseSnapshot;

    if (initialImageUrl) {
      const draftImage = await waitForImage(initialImageUrl);
      if (draftImage.width && draftImage.height) {
        context.drawImage(draftImage, 0, 0, width, height);
      }
    }

    configureContext(context, strokeColor, penSize);
    const snapshot = getCanvasSnapshot(canvas);
    historyRef.current = initialImageUrl ? [baseSnapshot, snapshot] : [snapshot];
    setHasChanges(false);
    onChange?.({ hasChanges: false, imageData: snapshot });
    setLoadingBase(false);
  }, [backgroundImageUrl, initialImageUrl, onChange, penSize, strokeColor]);

  useEffect(() => {
    buildBaseCanvas();
    const handleResize = () => buildBaseCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [buildBaseCanvas]);

  const scheduleAutosave = useCallback(() => {
    if (!autosaveEnabled || !onAutosave) return;
    if (drawIdleTimeoutRef.current) clearTimeout(drawIdleTimeoutRef.current);
    drawIdleTimeoutRef.current = setTimeout(async () => {
      setAutosaveState('Saving...');
      await onAutosave(getCanvasSnapshot(canvasRef.current));
      setAutosaveState('Draft autosaved');
    }, 1800);
  }, [autosaveEnabled, onAutosave]);

  useEffect(() => {
    if (!autosaveEnabled || !onAutosave) return undefined;
    autosaveIntervalRef.current = setInterval(async () => {
      if (!hasChanges) return;
      setAutosaveState('Saving...');
      await onAutosave(getCanvasSnapshot(canvasRef.current));
      setAutosaveState('All changes saved');
    }, 45000);
    return () => {
      if (autosaveIntervalRef.current) clearInterval(autosaveIntervalRef.current);
      if (drawIdleTimeoutRef.current) clearTimeout(drawIdleTimeoutRef.current);
    };
  }, [autosaveEnabled, hasChanges, onAutosave]);

  const startDraw = (event) => {
    event.preventDefault();
    setIsDrawing(true);
    const context = canvasRef.current.getContext('2d');
    context.strokeStyle = strokeColor;
    context.lineWidth = Number(penSize);
    const position = getCanvasPosition(canvasRef.current, event);
    lastPointRef.current = position;
    context.beginPath();
    context.moveTo(position.x, position.y);
  };

  const draw = (event) => {
    if (!isDrawing) return;
    event.preventDefault();
    const context = canvasRef.current.getContext('2d');
    const position = getCanvasPosition(canvasRef.current, event);
    if (lastPointRef.current) {
      const midpoint = {
        x: (lastPointRef.current.x + position.x) / 2,
        y: (lastPointRef.current.y + position.y) / 2,
      };
      context.quadraticCurveTo(lastPointRef.current.x, lastPointRef.current.y, midpoint.x, midpoint.y);
      context.stroke();
      context.beginPath();
      context.moveTo(midpoint.x, midpoint.y);
    }
    lastPointRef.current = position;
  };

  const endDraw = (event) => {
    if (!isDrawing) return;
    event.preventDefault();
    setIsDrawing(false);
    lastPointRef.current = null;
    const snapshot = getCanvasSnapshot(canvasRef.current);
    historyRef.current = [...historyRef.current, snapshot];
    setHasChanges(true);
    onChange?.({ hasChanges: true, imageData: snapshot });
    scheduleAutosave();
  };

  const handleUndo = () => {
    if (historyRef.current.length <= 1) return;
    historyRef.current = historyRef.current.slice(0, -1);
    applySnapshot(historyRef.current[historyRef.current.length - 1]);
    setHasChanges(historyRef.current.length > 1);
    onChange?.({ hasChanges: historyRef.current.length > 1, imageData: historyRef.current[historyRef.current.length - 1] });
  };

  const handleClear = () => {
    if (!window.confirm('Clear this canvas?')) return;
    historyRef.current = [baseSnapshotRef.current];
    applySnapshot(baseSnapshotRef.current);
    setHasChanges(false);
    onChange?.({ hasChanges: false, imageData: baseSnapshotRef.current });
  };

  return (
    <div className="space-y-3" data-testid="drawing-canvas-pad">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
        <div className="flex flex-wrap items-center gap-3">
          {allowColor && (
            <div className="flex items-center gap-2">
              <Palette className="w-4 h-4 text-gray-500" />
              <Select value={strokeColor} onValueChange={setStrokeColor}>
                <SelectTrigger className="w-[130px] bg-white" data-testid="drawing-color-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COLORS.map((color) => (
                    <SelectItem key={color.value} value={color.value}>{color.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {allowPenSize && (
            <div className="flex items-center gap-2">
              <Label className="text-xs text-gray-600">Pen</Label>
              <Select value={penSize} onValueChange={setPenSize}>
                <SelectTrigger className="w-[88px] bg-white" data-testid="drawing-pen-size-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SIZES.map((size) => (
                    <SelectItem key={size} value={size}>{size}px</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {autosaveState && <span className="text-xs text-gray-500" data-testid="drawing-autosave-state">{autosaveState}</span>}
          <Button type="button" variant="outline" size="sm" onClick={handleUndo} disabled={historyRef.current.length <= 1} data-testid="drawing-undo-button">
            <ArrowLeft className="w-4 h-4 mr-1" /> Undo
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={handleClear} data-testid="drawing-clear-canvas-button">
            <Trash2 className="w-4 h-4 mr-1" /> Clear
          </Button>
        </div>
      </div>

      <div ref={containerRef} className="rounded-2xl border border-gray-200 bg-white p-2">
        {loadingBase ? (
          <div className="flex min-h-[320px] items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-violet-500" /></div>
        ) : (
          <canvas
            ref={canvasRef}
            className="w-full touch-none rounded-xl border border-dashed border-gray-300 bg-white"
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
        )}
      </div>
    </div>
  );
};