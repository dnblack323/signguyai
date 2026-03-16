import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { ChevronRight, Sparkles, X } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OnboardingChecklist({ onDismiss }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const isDismissed = localStorage.getItem('onboarding_dismissed');
    if (isDismissed) {
      setDismissed(true);
      setLoading(false);
      return;
    }
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/api/onboarding/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatus(response.data);
    } catch (err) {
      console.error('Error fetching onboarding status:', err);
      setStatus({ step_statuses: {} });
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('onboarding_dismissed', 'true');
    setDismissed(true);
    onDismiss?.();
  };

  const statuses = Object.values(status?.step_statuses || {});
  const completedCount = statuses.filter((value) => value === 'completed').length;
  const finishLaterCount = statuses.filter((value) => value === 'finish_later').length;
  const totalCount = statuses.length || 1;
  const progress = (completedCount / totalCount) * 100;

  if (dismissed || loading || progress === 100) return null;

  return (
    <Card className="border-2 border-blue-500/30 bg-gradient-to-br from-blue-500/5 to-purple-500/5" data-testid="onboarding-checklist-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg" style={{ color: 'var(--text)' }}>Guided Onboarding</CardTitle>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {completedCount} completed • {finishLaterCount} finish later
              </p>
            </div>
          </div>
          <button onClick={handleDismiss} className="p-1 rounded-lg hover:bg-gray-100 transition" title="Dismiss">
            <X className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
        <Progress value={progress} className="h-2 mt-3" />
      </CardHeader>
      <CardContent className="space-y-4 pt-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-sm text-gray-700">
            Choose between <strong>Quick Start</strong>, <strong>Standard Setup</strong>, and <strong>Full Optimization</strong>.
            Each tier includes a checklist and short class-style walkthrough so new users can learn one part at a time.
          </p>
        </div>

        <div className="grid gap-2 md:grid-cols-3 text-sm">
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <p className="font-medium text-gray-900">Quick Start</p>
            <p className="text-gray-500 mt-1">Get operational in about 10 minutes</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <p className="font-medium text-gray-900">Standard Setup</p>
            <p className="text-gray-500 mt-1">Configure pricing, workflows, and forms</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <p className="font-medium text-gray-900">Full Optimization</p>
            <p className="text-gray-500 mt-1">Review analytics, reporting, and advanced ops</p>
          </div>
        </div>

        <Link to="/onboarding">
          <Button variant="outline" size="sm" className="w-full" data-testid="open-onboarding-hub-btn">
            Resume Setup
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}