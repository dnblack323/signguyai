import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Wrench, Clock, User, ChevronRight, Filter, CheckCircle, Pause, Play,
  Loader2, GripVertical, Settings, Plus, X, ArrowRight,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });
const fmt = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
const TASK_COLORS = {
  not_started: 'bg-gray-100 text-gray-600', waiting: 'bg-yellow-50 text-yellow-700', ready: 'bg-blue-50 text-blue-700',
  in_progress: 'bg-violet-50 text-violet-700', paused: 'bg-orange-50 text-orange-700', on_hold: 'bg-red-50 text-red-700',
  needs_review: 'bg-amber-50 text-amber-700', complete: 'bg-green-50 text-green-700', rework: 'bg-red-100 text-red-700',
};
const PRIORITY_DOT = { rush: 'bg-red-500', urgent: 'bg-orange-500', high: 'bg-amber-500', normal: 'bg-gray-400' };

export default function ProductionBoard() {
  const navigate = useNavigate();
  const [stages, setStages] = useState([]);
  const [groups, setGroups] = useState({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [taskLoading, setTaskLoading] = useState('');
  const [dragItem, setDragItem] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/production-tasks/board?view=stage`, { headers: hdr() });
      setStages(res.data.stages || []);
      setGroups(res.data.groups || {});
    } catch { toast.error('Failed to load production board'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const updateTask = async (taskId, updates) => {
    setTaskLoading(taskId);
    try {
      await axios.put(`${API}/production-tasks/${taskId}`, updates, { headers: hdr() });
      await load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Update failed'); }
    finally { setTaskLoading(''); }
  };

  const moveToStage = async (taskId, stageKey) => {
    await updateTask(taskId, { production_stage: stageKey });
    toast.success(`Moved to ${fmt(stageKey)}`);
  };

  // Drag and drop
  const handleDragStart = (e, task) => {
    setDragItem(task);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', task.id);
  };

  const handleDragOver = (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; };

  const handleDrop = async (e, stageKey) => {
    e.preventDefault();
    if (!dragItem) return;
    if ((dragItem.production_stage || dragItem.department || 'intake') === stageKey) { setDragItem(null); return; }
    await moveToStage(dragItem.id, stageKey);
    setDragItem(null);
  };

  const filterTasks = (tasks) => {
    if (statusFilter === 'all') return tasks;
    return tasks.filter(t => t.status === statusFilter);
  };

  const allTasks = Object.values(groups).flat();
  const inProgress = allTasks.filter(t => t.status === 'in_progress').length;
  const completedCount = allTasks.filter(t => t.status === 'complete').length;

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;

  return (
    <div className="space-y-4" data-testid="production-board-page">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2" data-testid="production-board-title">
            <Wrench className="w-5 h-5 text-violet-600" /> Production Board
          </h1>
          <p className="text-gray-500 text-sm">{allTasks.length} tasks | {inProgress} in progress | {completedCount} complete</p>
        </div>
        <div className="flex gap-2">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36 h-8 text-xs" data-testid="production-status-filter">
              <Filter className="w-3 h-3 mr-1" /><SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="not_started">Not Started</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="complete">Complete</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" className="h-8 text-xs gap-1" onClick={() => navigate('/settings/production')} data-testid="production-settings-btn">
            <Settings className="w-3.5 h-3.5" /> Stages
          </Button>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="flex gap-3 overflow-x-auto pb-4" data-testid="kanban-columns" style={{ minHeight: 400 }}>
        {stages.map((stage) => {
          const stageTasks = filterTasks(groups[stage.key] || []);
          return (
            <div
              key={stage.key}
              className="flex-shrink-0 w-72 bg-gray-50 rounded-xl border border-gray-200 flex flex-col"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, stage.key)}
              data-testid={`kanban-column-${stage.key}`}
            >
              {/* Column Header */}
              <div className="flex items-center justify-between px-3 py-2.5 border-b border-gray-200">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: stage.color || '#6366F1' }} />
                  <span className="text-sm font-semibold text-gray-900">{stage.label}</span>
                </div>
                <Badge variant="secondary" className="text-[10px] h-5 min-w-[20px] justify-center">{stageTasks.length}</Badge>
              </div>

              {/* Cards */}
              <div className="flex-1 p-2 space-y-2 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 260px)' }}>
                {stageTasks.length === 0 && (
                  <div className="flex items-center justify-center h-20 text-xs text-gray-400">No tasks</div>
                )}
                {stageTasks.map((task) => (
                  <Card
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task)}
                    className={`cursor-grab active:cursor-grabbing bg-white border border-gray-200 shadow-sm hover:shadow-md transition-shadow ${dragItem?.id === task.id ? 'opacity-40' : ''}`}
                    data-testid={`kanban-card-${task.id?.slice(0, 8)}`}
                  >
                    <CardContent className="p-2.5">
                      <div className="flex items-start gap-2">
                        <div className={`w-1.5 h-full min-h-[32px] rounded-full flex-shrink-0 mt-0.5 ${PRIORITY_DOT[task.ticket_priority] || PRIORITY_DOT.normal}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{task.ticket_name || task.task_name}</p>
                          <p className="text-[11px] text-gray-500 truncate">{task.task_name}{task.ticket_number ? ` — ${task.ticket_number}` : ''}</p>
                          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                            <Badge className={`text-[10px] px-1.5 py-0 h-4 ${TASK_COLORS[task.status] || TASK_COLORS.not_started}`}>{fmt(task.status)}</Badge>
                            {task.assigned_to_name && <span className="text-[10px] text-gray-400 flex items-center gap-0.5"><User className="w-2.5 h-2.5" />{task.assigned_to_name}</span>}
                            {task.ticket_due_date && <span className="text-[10px] text-gray-400 flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />{new Date(task.ticket_due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>}
                          </div>
                          {/* Quick Actions */}
                          <div className="flex gap-1 mt-2">
                            {task.status !== 'complete' && task.status !== 'in_progress' && (
                              <Button size="sm" variant="ghost" className="h-6 px-1.5 text-[10px] text-violet-600" onClick={() => updateTask(task.id, { status: 'in_progress' })} disabled={taskLoading === task.id}>
                                {taskLoading === task.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <><Play className="w-3 h-3 mr-0.5" />Start</>}
                              </Button>
                            )}
                            {task.status === 'in_progress' && (
                              <>
                                <Button size="sm" variant="ghost" className="h-6 px-1.5 text-[10px] text-green-600" onClick={() => updateTask(task.id, { status: 'complete' })} disabled={taskLoading === task.id}>
                                  <CheckCircle className="w-3 h-3 mr-0.5" />Done
                                </Button>
                                <Button size="sm" variant="ghost" className="h-6 px-1.5 text-[10px] text-orange-600" onClick={() => updateTask(task.id, { status: 'paused' })} disabled={taskLoading === task.id}>
                                  <Pause className="w-3 h-3 mr-0.5" />Pause
                                </Button>
                              </>
                            )}
                            {/* Move to next stage */}
                            {stages.findIndex(s => s.key === stage.key) < stages.length - 1 && task.status !== 'complete' && (
                              <Button size="sm" variant="ghost" className="h-6 px-1.5 text-[10px] text-blue-600 ml-auto" onClick={() => moveToStage(task.id, stages[stages.findIndex(s => s.key === stage.key) + 1].key)} disabled={taskLoading === task.id}>
                                <ArrowRight className="w-3 h-3 mr-0.5" />Next
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
