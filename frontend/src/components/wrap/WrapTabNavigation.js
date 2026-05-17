// Phase 1: Tab navigation bar. Horizontal scroll on small screens.
import { WRAP_TABS } from './constants';

export default function WrapTabNavigation({ activeTab, onChange }) {
  return (
    <div className="border-b border-slate-200 overflow-x-auto" data-testid="wrap-tab-nav">
      <div className="flex min-w-max">
        {WRAP_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              activeTab === t.id
                ? 'text-violet-700 border-violet-600'
                : 'text-slate-500 border-transparent hover:text-slate-700'
            }`}
            data-testid={`wrap-tab-${t.id}`}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}
