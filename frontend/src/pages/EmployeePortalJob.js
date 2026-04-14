import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { EmployeePortalLayout } from './EmployeePortalDashboard';
import { ArrowLeft, CheckCircle2, Pause, Play } from 'lucide-react';
import { toast } from 'sonner';
import { getEmployeePortalToken, getEmployeePortalName, getEmployeePortalConfig } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatDateTime = (value) => value ? new Date(value).toLocaleString() : '-';

export default function EmployeePortalJob() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const token = getEmployeePortalToken();
  const employeeName = getEmployeePortalName() || 'Employee';
  const portalConfig = getEmployeePortalConfig();
  const canSeeJobDetails = portalConfig?.can_see_job_details === true;
  const [loading, setLoading] = useState(true);
  const [jobData, setJobData] = useState(null);

  const loadJob = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/employee-portal/jobs/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setJobData(res.data);
    } catch (err) {
      toast.error('Failed to load assigned job');
      navigate('/employee-portal');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate('/employee-portal/login');
      return;
    }
    loadJob();
  }, [jobId, token]);

  const actOnStage = async (timelineId, stageOrder, action) => {
    try {
      await axios.post(
        `${API_URL}/api/employee-portal/jobs/${jobId}/timeline/${timelineId}/stage/${stageOrder}`,
        { action },
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );
      toast.success(`Stage ${action}ed`);
      await loadJob();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update stage');
    }
  };

  if (loading) {
    return (
      <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
        <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500" /></div>
      </EmployeePortalLayout>
    );
  }

  if (!canSeeJobDetails) {
    return (
      <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
        <div className="space-y-6 pb-24">
          <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
            <CardContent className="p-8 text-center">
              <ArrowLeft className="h-10 w-10 mx-auto mb-3 text-amber-500" />
              <p className="font-medium" style={{ color: 'var(--text)' }}>Order details are hidden</p>
              <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>Your admin has disabled job-detail access for this portal account.</p>
            </CardContent>
          </Card>
        </div>
      </EmployeePortalLayout>
    );
  }

  const { job, customer_name, timelines = [] } = jobData || {};

  return (
    <EmployeePortalLayout employeeName={employeeName} portalConfig={portalConfig}>
      <div className="space-y-6 pb-24" data-testid="employee-job-detail-page">
        <Link to="/employee-portal">
          <Button variant="outline" data-testid="employee-job-back-button"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Dashboard</Button>
        </Link>

        <Card style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }}>
          <CardHeader>
            <CardTitle style={{ color: 'var(--text)' }}>{job?.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p style={{ color: 'var(--text-muted)' }}>Customer: {customer_name}</p>
            <p style={{ color: 'var(--text-muted)' }}>Due Date: {job?.due_date || 'Not set'}</p>
          </CardContent>
        </Card>

        {timelines.map((timeline) => (
          <Card key={timeline.id} style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border-light)' }} data-testid={`employee-job-timeline-${timeline.id}`}>
            <CardHeader>
              <CardTitle style={{ color: 'var(--text)' }}>Production Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {timeline.stages.map((stage) => (
                <div key={stage.id} className="rounded-lg p-4" style={{ backgroundColor: 'var(--surface-2)' }}>
                  <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium" style={{ color: 'var(--text)' }}>{stage.stage_name}</p>
                        <Badge variant="outline">{stage.status}</Badge>
                      </div>
                      <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                        Start: {formatDateTime(stage.started_at)} · End: {formatDateTime(stage.completed_at)}
                      </p>
                    </div>
                    {stage.status !== 'completed' && (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => actOnStage(timeline.id, stage.stage_order, 'start')} data-testid={`employee-stage-start-${timeline.id}-${stage.stage_order}`}>
                          <Play className="h-4 w-4 mr-1" /> Start
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => actOnStage(timeline.id, stage.stage_order, 'pause')} data-testid={`employee-stage-pause-${timeline.id}-${stage.stage_order}`}>
                          <Pause className="h-4 w-4 mr-1" /> Pause
                        </Button>
                        <Button size="sm" onClick={() => actOnStage(timeline.id, stage.stage_order, 'complete')} data-testid={`employee-stage-complete-${timeline.id}-${stage.stage_order}`}>
                          <CheckCircle2 className="h-4 w-4 mr-1" /> Complete
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </EmployeePortalLayout>
  );
}