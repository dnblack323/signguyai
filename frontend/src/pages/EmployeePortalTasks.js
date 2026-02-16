import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { 
  ListTodo, CheckCircle, Clock, Briefcase, 
  Calendar, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { EmployeePortalLayout } from './EmployeePortalDashboard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatDate = (dateStr) => {
  if (!dateStr) return 'No due date';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
};

const isOverdue = (dateStr) => {
  if (!dateStr) return false;
  const dueDate = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return dueDate < today;
};

export default function EmployeePortalTasks() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState([]);
  const [showCompleted, setShowCompleted] = useState(false);
  
  const employeeName = localStorage.getItem('employee_name') || 'Employee';
  const token = localStorage.getItem('employee_token');

  useEffect(() => {
    if (!token) {
      navigate('/employee-portal/login');
      return;
    }
    loadTasks();
  }, [token, navigate, showCompleted]);

  const loadTasks = async () => {
    try {
      const res = await axios.get(
        `${API_URL}/api/employee-portal/tasks?include_completed=${showCompleted}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTasks(res.data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      if (err.response?.status === 401) {
        navigate('/employee-portal/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await axios.put(
        `${API_URL}/api/employee-portal/tasks/${taskId}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Task completed!');
      loadTasks();
    } catch (err) {
      toast.error('Failed to complete task');
    }
  };

  if (loading) {
    return (
      <EmployeePortalLayout employeeName={employeeName}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--accent)' }}></div>
        </div>
      </EmployeePortalLayout>
    );
  }

  const pendingTasks = tasks.filter(t => !t.is_complete);
  const completedTasks = tasks.filter(t => t.is_complete);

  return (
    <EmployeePortalLayout employeeName={employeeName}>
      <div className="space-y-6 pb-24">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold font-heading" style={{ color: 'var(--text)' }}>
            My Tasks
          </h2>
          <Badge 
            className="px-3 py-1"
            style={{ backgroundColor: 'var(--accent-soft)', color: 'var(--accent)' }}
          >
            {pendingTasks.length} pending
          </Badge>
        </div>

        {/* Pending Tasks */}
        <div className="space-y-3">
          {pendingTasks.length === 0 ? (
            <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
              <CardContent className="p-8 text-center">
                <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                <p className="font-medium" style={{ color: 'var(--text)' }}>All caught up!</p>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  No pending tasks assigned to you.
                </p>
              </CardContent>
            </Card>
          ) : (
            pendingTasks.map((task) => (
              <Card 
                key={task.id}
                className={`transition-all ${isOverdue(task.due_date) ? 'border-red-500/50' : ''}`}
                style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => handleCompleteTask(task.id)}
                      className="mt-1 w-5 h-5 rounded border-2 flex items-center justify-center hover:bg-green-500/20 transition-colors"
                      style={{ borderColor: 'var(--border-light)' }}
                      data-testid={`complete-task-${task.id}`}
                    >
                      {/* Empty checkbox */}
                    </button>
                    <div className="flex-1">
                      <p className="font-medium" style={{ color: 'var(--text)' }}>
                        {task.title}
                      </p>
                      {task.description && (
                        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                          {task.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2">
                        {task.job_name && (
                          <span className="text-xs flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                            <Briefcase className="h-3 w-3" /> {task.job_name}
                          </span>
                        )}
                        {task.due_date && (
                          <span 
                            className={`text-xs flex items-center gap-1 ${
                              isOverdue(task.due_date) ? 'text-red-500' : ''
                            }`}
                            style={!isOverdue(task.due_date) ? { color: 'var(--text-muted)' } : {}}
                          >
                            {isOverdue(task.due_date) ? (
                              <AlertTriangle className="h-3 w-3" />
                            ) : (
                              <Calendar className="h-3 w-3" />
                            )}
                            {formatDate(task.due_date)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Show Completed Toggle */}
        <div className="flex items-center justify-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCompleted(!showCompleted)}
            style={{ color: 'var(--text-muted)' }}
          >
            {showCompleted ? 'Hide completed' : `Show completed (${completedTasks.length})`}
          </Button>
        </div>

        {/* Completed Tasks */}
        {showCompleted && completedTasks.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
              Completed
            </h3>
            {completedTasks.map((task) => (
              <Card 
                key={task.id}
                className="opacity-60"
                style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div 
                      className="mt-1 w-5 h-5 rounded bg-green-500 flex items-center justify-center"
                    >
                      <CheckCircle className="h-3 w-3 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium line-through" style={{ color: 'var(--text-muted)' }}>
                        {task.title}
                      </p>
                      {task.job_name && (
                        <span className="text-xs flex items-center gap-1 mt-1" style={{ color: 'var(--text-muted)' }}>
                          <Briefcase className="h-3 w-3" /> {task.job_name}
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </EmployeePortalLayout>
  );
}
