import { useEffect, useState } from 'react';
import { Pin, Play, Trash2, Loader2, Pencil, Check, X } from 'lucide-react';
import {
  listSavedCommands,
  deleteSavedCommand,
  updateSavedCommand,
  recordSavedCommandRun,
} from '../../utils/assistantPrefsApi';

/**
 * Saved / pinned commands list. Lives in the assistant's empty/idle state.
 * Each item can be: Run (triggers onRunCommand), Rename (inline), or Delete.
 */
export default function AssistantSavedCommands({ token, refreshKey, onRunCommand }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editLabel, setEditLabel] = useState('');

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await listSavedCommands(token);
      setItems(data?.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [token, refreshKey]); // eslint-disable-line

  const handleRun = async (cmd) => {
    try { await recordSavedCommandRun(token, cmd.id); } catch {}
    onRunCommand?.(cmd.command);
  };

  const handleDelete = async (id) => {
    try {
      await deleteSavedCommand(token, id);
      setItems((prev) => prev.filter((c) => c.id !== id));
    } catch {}
  };

  const startEdit = (cmd) => {
    setEditingId(cmd.id);
    setEditLabel(cmd.label);
  };

  const saveEdit = async (cmd) => {
    const trimmed = editLabel.trim();
    if (!trimmed) return;
    try {
      await updateSavedCommand(token, cmd.id, { label: trimmed });
      setItems((prev) => prev.map((c) => (c.id === cmd.id ? { ...c, label: trimmed } : c)));
    } catch {}
    setEditingId(null);
  };

  if (!loading && items.length === 0) return null;

  return (
    <div data-testid="assistant-saved-commands">
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-wide text-slate-500 font-semibold px-1 mb-1">
        <Pin className="h-3 w-3" /> Pinned
      </div>
      {loading ? (
        <div className="flex items-center gap-1 text-xs text-slate-400 px-1 py-1">
          <Loader2 className="h-3 w-3 animate-spin" /> Loading…
        </div>
      ) : (
        <div className="space-y-1">
          {items.map((cmd) => (
            <div
              key={cmd.id}
              className="flex items-center gap-1 rounded-md border border-transparent hover:border-violet-200 hover:bg-violet-50 transition group px-1"
              data-testid={`assistant-saved-cmd-${cmd.id}`}
            >
              {editingId === cmd.id ? (
                <>
                  <input
                    autoFocus
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveEdit(cmd);
                      if (e.key === 'Escape') setEditingId(null);
                    }}
                    className="flex-1 text-xs px-1.5 py-1 rounded border border-violet-300 focus:outline-none focus:ring-1 focus:ring-violet-400"
                    data-testid={`assistant-saved-cmd-edit-${cmd.id}`}
                  />
                  <button
                    type="button"
                    onClick={() => saveEdit(cmd)}
                    className="p-1 text-green-600 hover:text-green-800"
                    title="Save"
                  >
                    <Check className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingId(null)}
                    className="p-1 text-slate-400 hover:text-slate-600"
                    title="Cancel"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => handleRun(cmd)}
                    className="flex-1 text-left text-xs px-1 py-1 text-slate-700 hover:text-violet-800 flex items-center gap-1.5 truncate"
                    title={cmd.command}
                    data-testid={`assistant-saved-cmd-run-${cmd.id}`}
                  >
                    <Play className="h-3 w-3 text-violet-500 flex-shrink-0" />
                    <span className="truncate">{cmd.label}</span>
                    {cmd.run_count > 0 && (
                      <span className="text-[9px] text-slate-400 ml-auto flex-shrink-0">×{cmd.run_count}</span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => startEdit(cmd)}
                    className="p-1 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-violet-600 transition"
                    title="Rename"
                    data-testid={`assistant-saved-cmd-edit-btn-${cmd.id}`}
                  >
                    <Pencil className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(cmd.id)}
                    className="p-1 opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 transition"
                    title="Delete"
                    data-testid={`assistant-saved-cmd-delete-${cmd.id}`}
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
