// Phase 2F: Vehicle Diagram visual SVG with click-to-add damage markers.
// Renders a simple generic outline (van/pickup/box-truck/etc) and overlays
// numbered markers at x/y percent positions. Click on empty space => onAdd(x,y).
// Click on existing marker => onSelect(id). Selected marker highlights.

import { useState } from 'react';

// Lightweight stylised outlines. Not a vehicle blueprint — just enough for
// the customer/installer to roughly point to "this fender", "that bumper".
const DIAGRAMS = {
  'Generic Van': (
    <g>
      <rect x="40" y="80" width="320" height="100" rx="14" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="80" y="60" width="240" height="40" rx="10" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <line x1="200" y1="60" x2="200" y2="180" stroke="#cbd5e1" strokeDasharray="4,4" />
      <circle cx="100" cy="190" r="14" fill="#1f2937" />
      <circle cx="300" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic Pickup': (
    <g>
      <rect x="40" y="100" width="200" height="80" rx="10" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="80" y="70" width="120" height="40" rx="8" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="240" y="100" width="120" height="80" rx="8" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="100" cy="190" r="14" fill="#1f2937" />
      <circle cx="300" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic Box Truck': (
    <g>
      <rect x="40" y="60" width="240" height="120" rx="6" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="280" y="90" width="80" height="90" rx="6" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <line x1="280" y1="60" x2="280" y2="180" stroke="#cbd5e1" strokeDasharray="4,4" />
      <circle cx="90" cy="190" r="14" fill="#1f2937" />
      <circle cx="240" cy="190" r="14" fill="#1f2937" />
      <circle cx="320" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic Trailer': (
    <g>
      <rect x="40" y="80" width="320" height="100" rx="6" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="20" y="120" width="20" height="20" fill="#94a3b8" />
      <circle cx="120" cy="190" r="14" fill="#1f2937" />
      <circle cx="280" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic SUV': (
    <g>
      <rect x="40" y="90" width="320" height="90" rx="20" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <path d="M90 90 L150 60 L260 60 L310 90 Z" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="105" cy="190" r="14" fill="#1f2937" />
      <circle cx="295" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic Sedan': (
    <g>
      <rect x="50" y="110" width="300" height="70" rx="22" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <path d="M110 110 L160 75 L260 75 L300 110 Z" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="115" cy="190" r="13" fill="#1f2937" />
      <circle cx="285" cy="190" r="13" fill="#1f2937" />
    </g>
  ),
  'Generic Ambulance': (
    <g>
      <rect x="40" y="70" width="280" height="110" rx="6" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <rect x="320" y="100" width="40" height="80" rx="6" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <path d="M180 100 h-12 v12 h-12 v12 h12 v12 h12 v-12 h12 v-12 h-12 z" fill="#ef4444" />
      <circle cx="100" cy="190" r="14" fill="#1f2937" />
      <circle cx="280" cy="190" r="14" fill="#1f2937" />
    </g>
  ),
  'Generic Bus': (
    <g>
      <rect x="30" y="60" width="340" height="120" rx="12" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <line x1="120" y1="60" x2="120" y2="180" stroke="#cbd5e1" strokeDasharray="4,4" />
      <line x1="200" y1="60" x2="200" y2="180" stroke="#cbd5e1" strokeDasharray="4,4" />
      <line x1="280" y1="60" x2="280" y2="180" stroke="#cbd5e1" strokeDasharray="4,4" />
      <circle cx="80" cy="190" r="13" fill="#1f2937" />
      <circle cx="320" cy="190" r="13" fill="#1f2937" />
    </g>
  ),
  'Generic Race Car': (
    <g>
      <path d="M30 130 L80 100 L290 90 L350 110 L370 140 L350 160 L60 170 Z" fill="#fff" stroke="#94a3b8" strokeWidth="2" />
      <circle cx="100" cy="180" r="14" fill="#1f2937" />
      <circle cx="290" cy="180" r="14" fill="#1f2937" />
    </g>
  ),
  'Custom / Other': (
    <g>
      <rect x="40" y="70" width="320" height="120" rx="14" fill="#fff" stroke="#94a3b8" strokeDasharray="6,4" strokeWidth="2" />
      <text x="200" y="135" textAnchor="middle" fill="#94a3b8" fontSize="14">Custom outline</text>
    </g>
  ),
};

const SEVERITY_COLOR = {
  Low: '#10b981',
  Medium: '#f59e0b',
  High: '#f97316',
  Severe: '#e11d48',
};

export default function WrapVehicleDiagram({
  diagramType,
  markers = [],
  selectedId = null,
  onAdd,
  onSelect,
  testId = 'insp-diagram-svg',
}) {
  const [armed, setArmed] = useState(false);
  const placedMarkers = markers.filter(
    (m) => typeof m.x_percent === 'number' && typeof m.y_percent === 'number'
  );

  const handleClick = (e) => {
    if (!armed) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const xPercent = ((e.clientX - rect.left) / rect.width) * 100;
    const yPercent = ((e.clientY - rect.top) / rect.height) * 100;
    onAdd?.({ x_percent: Math.round(xPercent * 10) / 10, y_percent: Math.round(yPercent * 10) / 10 });
    setArmed(false);
  };

  const outline = DIAGRAMS[diagramType] || DIAGRAMS['Custom / Other'];

  return (
    <div className="space-y-2" data-testid={testId}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-xs text-slate-500">
          {armed
            ? 'Click on the diagram to place a damage marker.'
            : `${placedMarkers.length} marker${placedMarkers.length === 1 ? '' : 's'} on diagram (${markers.length} total)`}
        </p>
        <button
          type="button"
          onClick={() => setArmed((a) => !a)}
          className={`text-xs px-2 py-1 rounded border transition-colors ${
            armed
              ? 'bg-violet-600 text-white border-violet-600'
              : 'bg-white text-violet-700 border-violet-300 hover:bg-violet-50'
          }`}
          data-testid="insp-diagram-arm-btn"
        >
          {armed ? 'Cancel click-to-add' : 'Click to add marker on diagram'}
        </button>
      </div>
      <div
        className={`relative w-full rounded-lg border-2 bg-slate-50 ${
          armed ? 'border-violet-400 cursor-crosshair' : 'border-slate-200 cursor-default'
        }`}
        style={{ aspectRatio: '2 / 1' }}
      >
        <svg
          viewBox="0 0 400 220"
          preserveAspectRatio="xMidYMid meet"
          className="absolute inset-0 w-full h-full"
          onClick={handleClick}
          data-testid="insp-diagram-canvas"
        >
          {outline}
          {placedMarkers.map((m, idx) => {
            const isSelected = selectedId === m.id;
            const fill = SEVERITY_COLOR[m.severity] || SEVERITY_COLOR.Low;
            return (
              <g
                key={m.id}
                transform={`translate(${(m.x_percent / 100) * 400}, ${(m.y_percent / 100) * 220})`}
                onClick={(ev) => {
                  ev.stopPropagation();
                  onSelect?.(m.id);
                }}
                style={{ cursor: 'pointer' }}
                data-testid={`insp-diagram-marker-${m.id}`}
              >
                <circle
                  r={isSelected ? 13 : 10}
                  fill={fill}
                  stroke={isSelected ? '#4338ca' : '#fff'}
                  strokeWidth={isSelected ? 3 : 2}
                />
                <text
                  textAnchor="middle"
                  dy="4"
                  fontSize="10"
                  fontWeight="700"
                  fill="#fff"
                >
                  {idx + 1}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
