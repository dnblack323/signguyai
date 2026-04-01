import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wrench, Clock, User, Calendar, ChevronRight, Filter, AlertTriangle, CheckCircle, Pause, Play, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

const DEPT_LABELS = {
  design: 'Design', print: 'Print', cut_trim: 'Cut / Trim', lamination: 'Lamination', weed_mask: 'Weed / Mask',
  sewing_finishing: 'Sewing / Finishing', assembly: 'Assembly', apparel: 'Apparel', wrap_prep: 'Wrap Prep',
  install: 'Install', qc_review: 'QC / Review', packaging: 'Packaging', delivery: 'Delivery', unassigned: 'Unassigned',
};
const DEPT_COLORS = {
  design: 'border-purple-500/40', print: 'border-blue-500/40', cut_trim: 'border-orange-500/40', lamination: 'border-cyan-500/40',
  weed_mask: 'border-yellow-500/40', sewing_finishing: 'border-pink-500/40', assembly: 'border-emerald-500/40', apparel: 'border-fuchsia-500/40',
  wrap_prep: 'border-teal-500/40', install: 'border-red-500/40', qc_review: 'border-amber-500/40', packaging: 'border-green-500/40',
  delivery: 'border-lime-500/40',
};
const TASK_COLORS = {
  not_started: 'bg-gray-200 text-gray-700', waiting: 'bg-yellow-500/15 text-yellow-400', ready: 'bg-blue-500/15 text-blue-400',
  in_progress: 'bg-violet-500/15 text-violet-400', paused: 'bg-orange-500/15 text-orange-400', on_hold: 'bg-red-500/15 text-red-400',
  needs_review: 'bg-amber-500/15 text-amber-400', complete: 'bg-green-500/15 text-green-400', rework: 'bg-red-600/15 text-red-400',
};
const PRIORITY_DOT = { rush: 'bg-red-500', urgent: 'bg-orange-500', high: 'bg-amber-500', normal: 'bg-slate-500' };
const fmt = (s) => (s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export default function ProductionBoard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('department');
  const [statusFilter, setStatusFilter] = useState('all');
  const [taskLoading, setTaskLoading] = useState('');

  const load = async () => {
    try {
      const res = await axios.get(`${API}/production-tasks/board?view=${view}`, { headers: hdr() });
      setData(res.data);
    } catch { toast.error('Failed to load production board'); }
    finally { setLoading(false); }
  };

  useEffect(() => { setLoading(true); load(); }, [view]);

  const updateTask = async (taskId, status) => {
    setTaskLoading(taskId);
    try {
      await axios.put(`${API}/production-tasks/${taskId}`, { status }, { headers: hdr() });
      toast.success(`Task ${fmt(status)}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setTaskLoading(''); }
  };

  const filterTasks = (tasks) => {
    if (statusFilter === 'all') return tasks;
    return tasks.filter(t => t.status === statusFilter);
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;

  const groups = data?.groups || {};
  const allTasks = data?.tasks || Object.values(groups).flat();
  const totalTasks = allTasks.length;
  const inProgress = allTasks.filter(t => t.status === 'in_progress').length;
  const onHold = allTasks.filter(t => t.status === 'on_hold' || t.status === 'rework').length;

  return (
    <div className="space-y-6" data-testid="production-board-page">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading flex items-center gap-3"><Wrench className="w-8 h-8 text-violet-400" /> Production Board</h1>
          <p className="text-slate-400 text-sm mt-1">Tasks} active tasks | {inProgress} in progress{onHold > 0 ? ` | ${onHold} flagged` : ''}</p>
        </div>
        <div className="flex gap-2">
          <Select value={view} onValueChange={setView}>
            <SelectTrigger className="w-40 bg-gray-50 border-gray-200 text-gray-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="department">By Department</SelectItem>
              <SelectItem value="status">By Status</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36 bg-gray-50 border-gray-200 text-gray-900">
              <Filter className="w-4 h-4 mr-1 text-gray-500" />
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="not_started">Not Started</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="on_hold">On Hold</SelectItem>
              <SelectItem value="needs_review">Needs Review</SelectItem>
              <SelectItem value="rework">Rework</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(groups).slice(0, 4).map(([key, tasks]) => (
          <Card key={key} className={`bg-white border-gray-200 border-l-4 ${DEPT_COLORS[key] || 'border-slate-500/40'}`}>
            <CardContent className="p-3">
              <p className="text-xs text-gray-500 uppercase">{DEPT_LABELS[key] || fmt(key)}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{tasks.length}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Board */}
      <div className="space-y-6">
        {Object.entries(groups).map(([groupKey, tasks]) => {
          const filtered = filterTasks(tasks);
          if (filtered.length === 0) return null;
          return (
            <div key={groupKey} data-testid={`board-group-${groupKey}`}>
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-3 h-3 rounded-full ${DEPT_COLORS[groupKey]?.replace('border-', 'bg-').replace('/40', '') || 'bg-slate-500'}`} />
                <h2 className="text-lg font-bold text-gray-900">{DEPT_LABELS[groupKey] || fmt(groupKey)}</h2>
                <Badge variant="outline" className="text-gray-500">{filtered.length}</Badge>
              </div>
              <div className="grid gap-2">
                {filtered.map(task => (
                  <Card key={task.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:border-gray-300 transition-colors" data-testid={`board-task-${task.id?.slice(0,8)}`}>
                    <CardContent className="p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <div className={`w-2 h-8 rounded-full flex-shrink-0 ${PRIORITY_DOT[task.ticket_priority] || PRIORITY_DOT.normal}`} />
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-gray-900 font-medium text-sm">{task.ticket_name || task.task_name}</span>
                              <Badge variant="outline" className={`text-xs ${TASK_COLORS[task.status]}`}>{fmt(task.status)}</Badge>
                              {task.rework_flag && <Badge className="bg-red-500 text-gray-900 text-xs">Rework</Badge>}
                            </div>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {task.task_name} — <span className="font-mono">{task.ticket_number}</span>
                              {task.ticket_due_date ? ` | Due: ${new Date(task.ticket_due_date).toLocaleDateString()}` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-1 flex-shrink-0">
                          {task.status !== 'complete' && task.status !== 'in_progress' && (
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-violet-400 hover:bg-violet-500/10" onClick={() => updateTask(task.id, 'in_progress')} disabled={taskLoading === task.id} title="Start">
                              {taskLoading === task.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                            </Button>
                          )}
                          {task.status === 'in_progress' && (
                            <>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-green-400 hover:bg-green-500/10" onClick={() => updateTask(task.id, 'complete')} disabled={taskLoading === task.id} title="Complete">
                                <CheckCircle className="w-3.5 h-3.5" />
                              </Button>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-orange-400 hover:bg-orange-500/10" onClick={() => updateTask(task.id, 'paused')} disabled={taskLoading === task.id} title="Pause">
                                <Pause className="w-3.5 h-3.5" />
                              </Button>
                            </>
                          )}
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
