import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Calendar } from '../components/ui/calendar';
import { formatDate, getStatusColor, cn } from '../lib/utils';
import { Plus, CalendarDays, ListTodo, LayoutGrid, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

export default function Productivity() {
  const { 
    tasks, jobs, fetchTasks, fetchJobs,
    createTask, updateTask, deleteTask 
  } = useApp();
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    job_id: '',
    due_date: '',
    is_complete: false
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchTasks(), fetchJobs()]);
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      toast.error('Please enter a task title');
      return;
    }
    try {
      await createTask({
        ...formData,
        due_date: formData.due_date || null,
        job_id: formData.job_id || null
      });
      toast.success('Task created');
      setFormData({
        title: '',
        description: '',
        job_id: '',
        due_date: '',
        is_complete: false
      });
      setIsDialogOpen(false);
    } catch (err) {
      toast.error('Failed to create task');
    }
  };

  const handleToggleComplete = async (task) => {
    try {
      await updateTask(task.id, { is_complete: !task.is_complete });
    } catch (err) {
      toast.error('Failed to update task');
    }
  };

  const handleDelete = async (taskId) => {
    try {
      await deleteTask(taskId);
      toast.success('Task deleted');
    } catch (err) {
      toast.error('Failed to delete task');
    }
  };

  const getJobName = (jobId) => {
    if (!jobId) return null;
    const job = jobs.find(j => j.id === jobId);
    return job?.name || 'Unknown Job';
  };

  // Get tasks for selected date (for calendar view)
  const getTasksForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return tasks.filter(t => t.due_date === dateStr);
  };

  // Get dates with tasks
  const datesWithTasks = tasks
    .filter(t => t.due_date)
    .map(t => new Date(t.due_date));

  // Group jobs by status for Kanban
  const jobStatuses = ['quoted', 'approved', 'in_production', 'installed', 'complete'];
  const jobsByStatus = jobStatuses.reduce((acc, status) => {
    acc[status] = jobs.filter(j => j.status === status);
    return acc;
  }, {});

  const incompleteTasks = tasks.filter(t => !t.is_complete);
  const completedTasks = tasks.filter(t => t.is_complete);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="productivity-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">Productivity</h1>
          <p className="text-muted-foreground mt-1">Tasks, calendar, and job tracking</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="neon-glow" data-testid="add-task-btn">
              <Plus className="h-4 w-4 mr-2" /> New Task
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-heading uppercase">New Task</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Title *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Task title"
                  data-testid="task-title-input"
                />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description"
                  data-testid="task-description-input"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Linked Job</Label>
                  <Select
                    value={formData.job_id}
                    onValueChange={(val) => setFormData({ ...formData, job_id: val })}
                  >
                    <SelectTrigger data-testid="task-job-select">
                      <SelectValue placeholder="Select job" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {jobs.map((j) => (
                        <SelectItem key={j.id} value={j.id}>
                          {j.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                    data-testid="task-due-date-input"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" data-testid="task-submit-btn">Create</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* View Tabs */}
      <Tabs value={view} onValueChange={setView}>
        <TabsList>
          <TabsTrigger value="list" data-testid="productivity-list-view">
            <ListTodo className="h-4 w-4 mr-2" /> Tasks
          </TabsTrigger>
          <TabsTrigger value="calendar" data-testid="productivity-calendar-view">
            <CalendarDays className="h-4 w-4 mr-2" /> Calendar
          </TabsTrigger>
          <TabsTrigger value="kanban" data-testid="productivity-kanban-view">
            <LayoutGrid className="h-4 w-4 mr-2" /> Job Kanban
          </TabsTrigger>
        </TabsList>

        {/* Task List View */}
        <TabsContent value="list" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Incomplete Tasks */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase flex items-center gap-2">
                  <ListTodo className="h-5 w-5 text-primary" />
                  To Do ({incompleteTasks.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {incompleteTasks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No pending tasks</p>
                ) : (
                  <div className="space-y-3">
                    {incompleteTasks.map((task) => (
                      <div 
                        key={task.id} 
                        className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg"
                        data-testid={`task-${task.id}`}
                      >
                        <Checkbox
                          checked={task.is_complete}
                          onCheckedChange={() => handleToggleComplete(task)}
                          data-testid={`task-checkbox-${task.id}`}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium">{task.title}</p>
                          {task.description && (
                            <p className="text-sm text-muted-foreground">{task.description}</p>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            {task.due_date && (
                              <Badge variant="outline" className="text-xs">
                                Due: {formatDate(task.due_date)}
                              </Badge>
                            )}
                            {task.job_id && (
                              <Badge variant="outline" className="text-xs text-primary">
                                {getJobName(task.job_id)}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(task.id)}
                          data-testid={`delete-task-${task.id}`}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Completed Tasks */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase flex items-center gap-2 text-green-400">
                  Completed ({completedTasks.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {completedTasks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No completed tasks</p>
                ) : (
                  <div className="space-y-3 max-h-[400px] overflow-y-auto">
                    {completedTasks.map((task) => (
                      <div 
                        key={task.id} 
                        className="flex items-start gap-3 p-3 bg-green-500/10 rounded-lg"
                      >
                        <Checkbox
                          checked={task.is_complete}
                          onCheckedChange={() => handleToggleComplete(task)}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium line-through text-muted-foreground">
                            {task.title}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(task.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Calendar View */}
        <TabsContent value="calendar" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-card border-border/50 lg:col-span-2">
              <CardContent className="p-4">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={(date) => date && setSelectedDate(date)}
                  className="rounded-md border-0"
                  modifiers={{
                    hasTasks: datesWithTasks
                  }}
                  modifiersStyles={{
                    hasTasks: { 
                      backgroundColor: 'hsl(var(--primary) / 0.2)',
                      borderRadius: '50%'
                    }
                  }}
                />
              </CardContent>
            </Card>
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="font-heading uppercase text-sm">
                  {selectedDate.toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {getTasksForDate(selectedDate).length === 0 ? (
                  <p className="text-muted-foreground text-center py-4 text-sm">
                    No tasks for this date
                  </p>
                ) : (
                  <div className="space-y-2">
                    {getTasksForDate(selectedDate).map((task) => (
                      <div 
                        key={task.id} 
                        className={cn(
                          "p-2 rounded-lg text-sm",
                          task.is_complete ? "bg-green-500/10" : "bg-muted/50"
                        )}
                      >
                        <p className={task.is_complete ? "line-through text-muted-foreground" : ""}>
                          {task.title}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Kanban View */}
        <TabsContent value="kanban" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 overflow-x-auto">
            {jobStatuses.map((status) => (
              <div key={status} className="min-w-[250px]">
                <div className="bg-muted/30 rounded-lg p-3 mb-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-sm uppercase tracking-wide">
                      {status.replace('_', ' ')}
                    </h3>
                    <Badge variant="outline">{jobsByStatus[status].length}</Badge>
                  </div>
                </div>
                <div className="space-y-3">
                  {jobsByStatus[status].map((job) => (
                    <Card 
                      key={job.id} 
                      className="bg-card border-border/50 hover:border-primary/30 transition-all"
                    >
                      <CardContent className="p-4">
                        <h4 className="font-medium text-sm">{job.name}</h4>
                        {job.due_date && (
                          <p className="text-xs text-muted-foreground mt-2">
                            Due: {formatDate(job.due_date)}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                  {jobsByStatus[status].length === 0 && (
                    <div className="text-center py-8 text-muted-foreground text-sm border-2 border-dashed border-border/50 rounded-lg">
                      No jobs
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
