import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, CalendarDays, Clock3, MapPin, User2 } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

export default function AppointmentDetailPage() {
  const { appointmentId } = useParams();
  const { api } = useApp();
  const [appointment, setAppointment] = useState(null);

  useEffect(() => {
    api.get(`/appointments/${appointmentId}`).then((response) => setAppointment(response.data));
  }, [api, appointmentId]);

  return (
    <div className="space-y-6" data-testid="appointment-detail-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-[0.22em] text-slate-400">Appointment</p>
          <h1 className="text-4xl font-bold text-white">{appointment?.title || 'Loading appointment…'}</h1>
        </div>
        <Button asChild variant="outline" data-testid="appointment-back-button"><Link to="/productivity?view=calendar"><ArrowLeft className="mr-2 h-4 w-4" />Back to Calendar</Link></Button>
      </div>

      <Card className="bg-white border-gray-200" data-testid="appointment-detail-card">
        <CardHeader><CardTitle>Appointment Details</CardTitle></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 text-sm text-slate-700">
          <div className="flex items-center gap-2"><CalendarDays className="h-4 w-4 text-slate-400" />Status: {appointment?.status || '—'}</div>
          <div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-slate-400" />Scheduled: {appointment?.scheduled_at || appointment?.scheduled_date || '—'}</div>
          <div className="flex items-center gap-2"><User2 className="h-4 w-4 text-slate-400" />Customer: {appointment?.customer_name || '—'}</div>
          <div className="flex items-center gap-2"><MapPin className="h-4 w-4 text-slate-400" />Location: {appointment?.location || '—'}</div>
          <p><span className="font-semibold text-slate-900">Type:</span> {appointment?.appointment_type || '—'}</p>
          <p><span className="font-semibold text-slate-900">Duration:</span> {appointment?.duration_minutes || 60} minutes</p>
          <p className="sm:col-span-2"><span className="font-semibold text-slate-900">Notes:</span> {appointment?.description || appointment?.notes || 'No appointment notes saved.'}</p>
        </CardContent>
      </Card>
    </div>
  );
}