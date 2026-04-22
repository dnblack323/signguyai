import { useEffect, useState } from 'react';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Plus, Play, Trash2, Loader2, ListOrdered, X } from 'lucide-react';
import { toast } from 'sonner';
import {
  listRoutines,
  createRoutine,
  deleteRoutine,
  recordRoutineRun,
} from '../../utils/assistantPrefsApi';

/**
 * Modal to manage micro-automations (routines).
 * A routine = 1–8 commands run sequentially through the assistant.
 *
 * Parent provides:
 *  - onRunCommand(command)  runs a single command via handleSend
 *  - open / onOpenChange    controlled visibility
 */
export default function AssistantRoutinesModal({
  token,
  open,
  onOpenChange,
  onRunCommand,
}) {
  const [routines, setRoutines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [runningId, setRunningId] = useState(null);

  const [newName, setNewName] = useState('');
  const [newCommands, setNewCommands] = useState('');

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await listRoutines(token);
      setRoutines(data?.items || []);
    } catch {
      setRoutines([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      load();
    } else {
      // Clear create-form state when modal closes so reopening is fresh.
      setNewName('');
      setNewCommands('');
    }
  }, [token, open]); // eslint-disable-line

  const handleCreate = async () => {
    const name = newName.trim();
    const commands = newCommands
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!name || !commands.length) {
      toast.error('Give the routine a name and at least one command.');
      return;
    }
    if (commands.length > 8) {
      toast.error('A routine can have at most 8 steps.');
      return;
    }
    setCreating(true);
    try {
      const created = await createRoutine(token, { name, commands });
      setRoutines((prev) => [created, ...prev]);
      setNewName('');
      setNewCommands('');
      toast.success(`Routine "${name}" saved`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Could not save routine');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteRoutine(token, id);
      setRoutines((prev) => prev.filter((r) => r.id !== id));
    } catch {
      toast.error('Could not delete routine');
    }
  };

  const handleRun = async (routine) => {
    if (!onRunCommand || runningId) return;
    setRunningId(routine.id);
    // Close the modal immediately so the user can watch commands run
    // in the assistant panel behind it.
    onOpenChange?.(false);
    try {
      for (const cmd of routine.commands) {
        // eslint-disable-next-line no-await-in-loop
        await onRunCommand(cmd);
      }
      try { await recordRoutineRun(token, routine.id); } catch {}
      toast.success(`Routine "${routine.name}" complete`);
    } catch (err) {
      toast.error('Routine stopped: ' + (err?.message || 'error'));
    } finally {
      setRunningId(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="assistant-routines-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ListOrdered className="h-4 w-4 text-violet-600" />
            Routines
          </DialogTitle>
          <DialogDescription>
            Chain 1–8 assistant commands together. Runs them in order.
          </DialogDescription>
        </DialogHeader>

        {/* Existing routines */}
        <div className="space-y-2 max-h-64 overflow-y-auto" data-testid="assistant-routines-list">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-slate-500 py-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading…
            </div>
          ) : routines.length === 0 ? (
            <p className="text-sm text-slate-500 italic py-2">
              No routines yet. Create one below to chain recurring commands.
            </p>
          ) : (
            routines.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border p-2 hover:border-violet-200 hover:bg-violet-50/40 transition"
                data-testid={`assistant-routine-${r.id}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-slate-800 truncate">{r.name}</div>
                    <div className="text-[11px] text-slate-500">
                      {r.commands.length} step{r.commands.length > 1 ? 's' : ''}
                      {r.run_count ? ` · run ${r.run_count}×` : ''}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleRun(r)}
                    disabled={runningId !== null}
                    className="bg-violet-600 hover:bg-violet-700 h-7 px-2"
                    data-testid={`assistant-routine-run-${r.id}`}
                  >
                    {runningId === r.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Play className="h-3 w-3" />
                    )}
                    <span className="ml-1 text-xs">Run</span>
                  </Button>
                  <button
                    type="button"
                    onClick={() => handleDelete(r.id)}
                    className="p-1 text-slate-400 hover:text-red-600"
                    title="Delete"
                    data-testid={`assistant-routine-delete-${r.id}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <ol className="mt-1.5 pl-4 text-[11px] text-slate-600 list-decimal space-y-0.5">
                  {r.commands.map((cmd, i) => (
                    <li key={i} className="truncate">{cmd}</li>
                  ))}
                </ol>
              </div>
            ))
          )}
        </div>

        {/* Create form */}
        <div className="border-t pt-3 space-y-2">
          <p className="text-[11px] uppercase tracking-wide font-semibold text-slate-500 flex items-center gap-1">
            <Plus className="h-3 w-3" /> New routine
          </p>
          <Input
            placeholder='Name (e.g., "Monday morning review")'
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            data-testid="assistant-routine-new-name"
          />
          <Textarea
            placeholder="One command per line. Example:&#10;Show overdue invoices&#10;What jobs are due this week?&#10;Revenue this month"
            value={newCommands}
            onChange={(e) => setNewCommands(e.target.value)}
            rows={4}
            className="text-xs font-mono"
            data-testid="assistant-routine-new-commands"
          />
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onOpenChange?.(false)}
              data-testid="assistant-routine-close"
            >
              <X className="h-3 w-3 mr-1" /> Close
            </Button>
            <Button
              size="sm"
              onClick={handleCreate}
              disabled={creating}
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="assistant-routine-save"
            >
              {creating ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Plus className="h-3 w-3 mr-1" />}
              Save routine
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
