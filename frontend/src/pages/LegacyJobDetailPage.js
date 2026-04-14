import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, CalendarDays, Clock3, FileText, User2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

export default function LegacyJobDetailPage() {
  const { jobId } = useParams();
  const { api } = useApp();
  const [payload, setPayload] = useState(null);

  useEffect(() => {
    api.get(`/jobs/${jobId}/details`).then((response) => setPayload(response.data));
  }, [api, jobId]);

  const job = payload?.job;
  const customer = payload?.customer;

  return (
    <div className="space-y-6" data-testid="legacy-job-detail-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.22em] text-slate-400">Legacy Order Record</p>
          <h1 className="text-4xl font-bold text-white">{job?.name || 'Loading legacy job…'}</h1>
        </div>
        <Button asChild variant="outline" data-testid="legacy-job-back-button"><Link to="/productivity?view=dashboard"><ArrowLeft className="mr-2 h-4 w-4" />Back to Productivity</Link></Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="bg-white border-gray-200 lg:col-span-2" data-testid="legacy-job-summary-card">
          <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 text-sm text-slate-700">
            <p><span className="font-semibold text-slate-900">Status:</span> {job?.status || '—'}</p>
            <p><span className="font-semibold text-slate-900">Customer:</span> {customer?.name || '—'}</p>
            <p><span className="font-semibold text-slate-900">Due Date:</span> {job?.due_date || '—'}</p>
            <p><span className="font-semibold text-slate-900">Total:</span> {job?.total ?? 0}</p>
            <p className="sm:col-span-2"><span className="font-semibold text-slate-900">Description:</span> {job?.description || job?.notes || 'No description saved.'}</p>
          </CardContent>
        </Card>

        <Card className="bg-white border-gray-200" data-testid="legacy-job-financial-card">
          <CardHeader><CardTitle>Snapshot</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-700">
            <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-slate-400" />Quote: {payload?.financial_snapshot?.quote_total ?? 0}</div>
            <div className="flex items-center gap-2"><CalendarDays className="h-4 w-4 text-slate-400" />Invoice: {payload?.financial_snapshot?.invoice_total ?? 0}</div>
            <div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-slate-400" />Balance Due: {payload?.financial_snapshot?.balance_due ?? 0}</div>
            <div className="flex items-center gap-2"><User2 className="h-4 w-4 text-slate-400" />Assigned: {(payload?.assigned_employee_details || []).map((employee) => employee.name).join(', ') || 'Unassigned'}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}