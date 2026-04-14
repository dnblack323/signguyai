import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, Circle, Loader2, MousePointer2, MoveRight, Palette, Pen, Trash2, Type } from 'lucide-react';
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

const TOOLS = [
  { id: 'pen', label: 'Draw', icon: Pen },
  { id: 'arrow', label: 'Arrow', icon: MoveRight },
  { id: 'circle', label: 'Circle', icon: Circle },
  { id: 'text', label: 'Text', icon: Type },
];

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

const drawArrow = (ctx, fromX, fromY, toX, toY) => {
  const headLen = Math.max(12, Number(ctx.lineWidth) * 3);
  const angle = Math.atan2(toY - fromY, toX - fromX);
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLen * Math.cos(angle - Math.PI / 6), toY - headLen * Math.sin(angle - Math.PI / 6));
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLen * Math.cos(angle + Math.PI / 6), toY - headLen * Math.sin(angle + Math.PI / 6));
  ctx.stroke();
};

const drawEllipse = (ctx, fromX, fromY, toX, toY) => {
  const cx = (fromX + toX) / 2;
  const cy = (fromY + toY) / 2;
  const rx = Math.abs(toX - fromX) / 2;
  const ry = Math.abs(toY - fromY) / 2;
  if (rx < 2 && ry < 2) return;
  ctx.beginPath();
  ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
  ctx.stroke();
};

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
  const shapeStartRef = useRef(null);
  const isDrawingRef = useRef(false);
  const onChangeRef = useRef(onChange);
  const onAutosaveRef = useRef(onAutosave);
  const preShapeSnapshotRef = useRef(null);

  const [loadingBase, setLoadingBase] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);
  const [strokeColor, setStrokeColor] = useState('#DC2626');
  const [penSize, setPenSize] = useState('4');
  const [autosaveState, setAutosaveState] = useState('');
  const [activeTool, setActiveTool] = useState('pen');
  const [textPlacement, setTextPlacement] = useState(null);
  const [textInputValue, setTextInputValue] = useState('');

  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => { onAutosaveRef.current = onAutosave; }, [onAutosave]);

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

    const snapshot = getCanvasSnapshot(canvas);
    historyRef.current = initialImageUrl ? [baseSnapshot, snapshot] : [snapshot];
    setHasChanges(false);
    onChangeRef.current?.({ hasChanges: false, imageData: snapshot });
    setLoadingBase(false);
  }, [backgroundImageUrl, initialImageUrl]);

  useEffect(() => {
    buildBaseCanvas();
    const handleResize = () => buildBaseCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [buildBaseCanvas]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    configureContext(context, strokeColor, penSize);
  }, [penSize, strokeColor]);

  const scheduleAutosave = useCallback(() => {
    if (!autosaveEnabled || !onAutosaveRef.current) return;
    if (drawIdleTimeoutRef.current) clearTimeout(drawIdleTimeoutRef.current);
    drawIdleTimeoutRef.current = setTimeout(async () => {
      setAutosaveState('Saving...');
      await onAutosaveRef.current?.(getCanvasSnapshot(canvasRef.current));
      setAutosaveState('Draft autosaved');
    }, 1800);
  }, [autosaveEnabled]);

  useEffect(() => {
    if (!autosaveEnabled || !onAutosaveRef.current) return undefined;
    autosaveIntervalRef.current = setInterval(async () => {
      if (!hasChanges) return;
      setAutosaveState('Saving...');
      await onAutosaveRef.current?.(getCanvasSnapshot(canvasRef.current));
      setAutosaveState('All changes saved');
    }, 45000);
    return () => {
      if (autosaveIntervalRef.current) clearInterval(autosaveIntervalRef.current);
      if (drawIdleTimeoutRef.current) clearTimeout(drawIdleTimeoutRef.current);
    };
  }, [autosaveEnabled, hasChanges]);

  const commitSnapshot = () => {
    const snapshot = getCanvasSnapshot(canvasRef.current);
    historyRef.current = [...historyRef.current, snapshot];
    setHasChanges(true);
    onChangeRef.current?.({ hasChanges: true, imageData: snapshot });
    scheduleAutosave();
  };

  // --- Text tool: place text on click ---
  const commitText = () => {
    if (!textPlacement || !textInputValue.trim()) {
      setTextPlacement(null);
      setTextInputValue('');
      return;
    }
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const fontSize = Math.max(14, Number(penSize) * 4);
    ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
    ctx.fillStyle = strokeColor;
    ctx.fillText(textInputValue.trim(), textPlacement.x, textPlacement.y);
    setTextPlacement(null);
    setTextInputValue('');
    commitSnapshot();
  };

  // --- Freehand pen ---
  const startDraw = (event) => {
    event.preventDefault();
    if (activeTool === 'text') {
      // place text cursor
      commitText(); // commit any pending
      const pos = getCanvasPosition(canvasRef.current, event);
      setTextPlacement(pos);
      return;
    }
    isDrawingRef.current = true;
    const pos = getCanvasPosition(canvasRef.current, event);

    if (activeTool === 'arrow' || activeTool === 'circle') {
      shapeStartRef.current = pos;
      preShapeSnapshotRef.current = getCanvasSnapshot(canvasRef.current);
      return;
    }

    // pen mode
    const context = canvasRef.current.getContext('2d');
    context.strokeStyle = strokeColor;
    context.lineWidth = Number(penSize);
    lastPointRef.current = pos;
    context.beginPath();
    context.moveTo(pos.x, pos.y);
  };

  const draw = (event) => {
    if (!isDrawingRef.current) return;
    event.preventDefault();
    const pos = getCanvasPosition(canvasRef.current, event);

    if ((activeTool === 'arrow' || activeTool === 'circle') && shapeStartRef.current && preShapeSnapshotRef.current) {
      // live preview: restore pre-shape snapshot then draw shape
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      img.onload = () => {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);
        configureContext(ctx, strokeColor, penSize);
        if (activeTool === 'arrow') drawArrow(ctx, shapeStartRef.current.x, shapeStartRef.current.y, pos.x, pos.y);
        else drawEllipse(ctx, shapeStartRef.current.x, shapeStartRef.current.y, pos.x, pos.y);
      };
      img.src = preShapeSnapshotRef.current;
      return;
    }

    // pen mode
    const context = canvasRef.current.getContext('2d');
    if (lastPointRef.current) {
      const midpoint = {
        x: (lastPointRef.current.x + pos.x) / 2,
        y: (lastPointRef.current.y + pos.y) / 2,
      };
      context.quadraticCurveTo(lastPointRef.current.x, lastPointRef.current.y, midpoint.x, midpoint.y);
      context.stroke();
      context.beginPath();
      context.moveTo(midpoint.x, midpoint.y);
    }
    lastPointRef.current = pos;
  };

  const endDraw = (event) => {
    if (!isDrawingRef.current) return;
    event.preventDefault();
    isDrawingRef.current = false;

    if ((activeTool === 'arrow' || activeTool === 'circle') && shapeStartRef.current) {
      // finalize shape — the live preview already drew it, just commit
      shapeStartRef.current = null;
      preShapeSnapshotRef.current = null;
    }

    lastPointRef.current = null;
    commitSnapshot();
  };

  const handleUndo = () => {
    if (historyRef.current.length <= 1) return;
    historyRef.current = historyRef.current.slice(0, -1);
    applySnapshot(historyRef.current[historyRef.current.length - 1]);
    setHasChanges(historyRef.current.length > 1);
    onChangeRef.current?.({ hasChanges: historyRef.current.length > 1, imageData: historyRef.current[historyRef.current.length - 1] });
  };

  const handleClear = () => {
    if (!window.confirm('Clear this canvas?')) return;
    historyRef.current = [baseSnapshotRef.current];
    applySnapshot(baseSnapshotRef.current);
    setHasChanges(false);
    onChangeRef.current?.({ hasChanges: false, imageData: baseSnapshotRef.current });
  };

  return (
    <div className="space-y-3" data-testid="drawing-canvas-pad">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2">
        <div className="flex flex-wrap items-center gap-2">
          {/* Tool selector */}
          <div className="flex items-center gap-0.5 rounded-lg border border-gray-200 bg-white p-0.5" data-testid="drawing-tool-picker">
            {TOOLS.map((tool) => {
              const Icon = tool.icon;
              return (
                <button
                  key={tool.id}
                  type="button"
                  onClick={() => { setActiveTool(tool.id); if (tool.id !== 'text') commitText(); }}
                  className={`flex items-center gap-1 px-2 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    activeTool === tool.id
                      ? 'bg-violet-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                  data-testid={`drawing-tool-${tool.id}`}
                  title={tool.label}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">{tool.label}</span>
                </button>
              );
            })}
          </div>
          {allowColor && (
            <Select value={strokeColor} onValueChange={setStrokeColor}>
              <SelectTrigger className="w-[100px] h-8 text-xs bg-white" data-testid="drawing-color-select">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full border border-gray-300" style={{ backgroundColor: strokeColor }} />
                  <SelectValue />
                </div>
              </SelectTrigger>
              <SelectContent>
                {COLORS.map((color) => (
                  <SelectItem key={color.value} value={color.value}>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color.value }} />
                      {color.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {allowPenSize && (
            <Select value={penSize} onValueChange={setPenSize}>
              <SelectTrigger className="w-[72px] h-8 text-xs bg-white" data-testid="drawing-pen-size-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SIZES.map((size) => (
                  <SelectItem key={size} value={size}>{size}px</SelectItem>
                ))}
              </SelectContent>
            </Select>
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
        <div className="relative min-h-[320px]">
          <canvas
            ref={canvasRef}
            className={`w-full touch-none rounded-xl border border-dashed border-gray-300 bg-white ${
              activeTool === 'text' ? 'cursor-text' : activeTool === 'arrow' || activeTool === 'circle' ? 'cursor-crosshair' : 'cursor-default'
            }`}
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
          {loadingBase && <div className="absolute inset-0 flex items-center justify-center bg-white/75 rounded-xl"><Loader2 className="w-6 h-6 animate-spin text-violet-500" /></div>}
          {/* Text input overlay */}
          {textPlacement && (
            <div
              className="absolute z-10"
              style={{ left: textPlacement.x, top: textPlacement.y - 32 }}
            >
              <input
                autoFocus
                type="text"
                placeholder="Type note..."
                value={textInputValue}
                onChange={(e) => setTextInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') commitText(); if (e.key === 'Escape') { setTextPlacement(null); setTextInputValue(''); } }}
                onBlur={commitText}
                className="px-2 py-1 text-sm border-2 border-violet-500 rounded-md shadow-lg bg-white text-gray-900 min-w-[120px] focus:outline-none"
                style={{ color: strokeColor }}
                data-testid="drawing-text-input"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
