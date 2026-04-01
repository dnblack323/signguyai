import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { PortalLayout } from './PortalDashboard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { AlertCircle, CheckCircle, ChevronLeft, FileText, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { getPortalToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const statusBadge = {
  pending: 'bg-amber-100 text-amber-700',
  in_progress: 'bg-blue-100 text-blue-700',
  overdue: 'bg-red-100 text-red-700',
  completed: 'bg-green-100 text-green-700',
};

const getToken = () => getPortalToken();

export function PortalForms() {
  const navigate = useNavigate();
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [forms, setForms] = useState([]);

  const fetchForms = useCallback(async () => {
    const token = getToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }
    setLoading(true);
    try {
      const url = filter === 'all' ? `${API_URL}/api/portal/forms` : `${API_URL}/api/portal/forms?status=${filter}`;
      const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (response.ok) {
        setForms(await response.json());
      }
    } finally {
      setLoading(false);
    }
  }, [filter, navigate]);

  useEffect(() => { fetchForms(); }, [fetchForms]);

  return (
    <PortalLayout activeNav="forms" customerName={customerName}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Forms / Questionnaires</h2>
          <p className="text-slate-600 mt-1">Complete required forms and review past submissions.</p>
        </div>

        <div className="flex gap-2 flex-wrap">
          {['all', 'pending', 'in_progress', 'completed', 'overdue'].map((item) => (
            <Button key={item} variant={filter === item ? 'default' : 'outline'} size="sm" onClick={() => setFilter(item)} className={filter === item ? 'bg-teal-500 hover:bg-teal-600' : ''} data-testid={`portal-forms-filter-${item}`}>
              {item.replace('_', ' ')}
            </Button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-teal-500" /></div>
        ) : forms.length > 0 ? (
          <div className="space-y-4">
            {forms.map((formRequest) => (
              <Card key={formRequest.id} className="border-slate-200" data-testid={`portal-form-row-${formRequest.id}`}>
                <CardContent className="p-4 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-slate-900">{formRequest.questionnaire_name}</p>
                    <p className="text-sm text-slate-500 mt-1">Sent {new Date(formRequest.sent_at).toLocaleDateString()} {formRequest.due_date ? `· Due ${new Date(formRequest.due_date).toLocaleDateString()}` : ''}</p>
                    {formRequest.instructions && <p className="text-sm text-slate-600 mt-2">{formRequest.instructions}</p>}
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge className={statusBadge[formRequest.status] || 'bg-slate-100 text-slate-700'}>{formRequest.status.replace('_', ' ')}</Badge>
                    <Link to={`/customer-portal/forms/${formRequest.id}`}>
                      <Button className="bg-teal-500 hover:bg-teal-600" data-testid={`portal-form-open-${formRequest.id}`}>
                        {formRequest.status === 'completed' ? 'View Submission' : 'Open Form'}
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-slate-200">
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No forms found for this filter</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PortalLayout>
  );
}

export function PortalFormDetail() {
  const navigate = useNavigate();
  const { requestId } = useParams();
  const customerName = localStorage.getItem('portal_customer_name') || 'Customer';
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [detail, setDetail] = useState(null);
  const [answers, setAnswers] = useState({});

  const loadDetail = useCallback(async () => {
    const token = getToken();
    if (!token) {
      navigate('/customer-portal/login');
      return;
    }
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/portal/forms/${requestId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDetail(res.data);
      const initialAnswers = {};
      (res.data.existing_response?.answers ? Object.entries(res.data.existing_response.answers) : []).forEach(([key, value]) => {
        initialAnswers[key] = value;
      });
      res.data.questionnaire?.questions?.forEach((question) => {
        if (!(question.id in initialAnswers)) {
          initialAnswers[question.id] = ['checkbox', 'multi_select'].includes(question.type) ? [] : '';
        }
      });
      setAnswers(initialAnswers);
    } catch (err) {
      toast.error('Failed to load form');
      navigate('/customer-portal/forms');
    } finally {
      setLoading(false);
    }
  }, [navigate, requestId]);

  useEffect(() => { loadDetail(); }, [loadDetail]);

  const updateAnswer = (questionId, value) => setAnswers((current) => ({ ...current, [questionId]: value }));
  const toggleCheckbox = (questionId, value) => {
    const current = answers[questionId] || [];
    updateAnswer(questionId, current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  };

  const handleSubmit = async () => {
    const token = getToken();
    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/portal/forms/${requestId}/submit`, { answers }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Form submitted successfully');
      await loadDetail();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit form');
    } finally {
      setSubmitting(false);
    }
  };

  const questionnaire = detail?.questionnaire;
  const request = detail?.request;
  const existingResponse = detail?.existing_response;

  const renderQuestion = (question) => {
    switch (question.type) {
      case 'heading':
        return <h3 className="text-lg font-semibold text-slate-900">{question.label}</h3>;
      case 'paragraph':
        return <p className="text-slate-600">{question.label}</p>;
      case 'textarea':
        return <Textarea value={answers[question.id] || ''} onChange={(e) => updateAnswer(question.id, e.target.value)} rows={4} disabled={!!existingResponse} data-testid={`portal-form-answer-${question.id}`} />;
      case 'select':
        return (
          <Select value={answers[question.id] || ''} onValueChange={(value) => updateAnswer(question.id, value)} disabled={!!existingResponse}>
            <SelectTrigger data-testid={`portal-form-answer-${question.id}`}><SelectValue placeholder="Select an option" /></SelectTrigger>
            <SelectContent>{question.options?.map((option) => <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>)}</SelectContent>
          </Select>
        );
      case 'radio':
        return (
          <RadioGroup value={answers[question.id] || ''} onValueChange={(value) => updateAnswer(question.id, value)} disabled={!!existingResponse}>
            {question.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2"><RadioGroupItem value={option.value} id={`${question.id}-${option.value}`} /><Label htmlFor={`${question.id}-${option.value}`}>{option.label}</Label></div>
            ))}
          </RadioGroup>
        );
      case 'checkbox':
      case 'multi_select':
        return (
          <div className="space-y-2">
            {question.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2"><Checkbox checked={(answers[question.id] || []).includes(option.value)} onCheckedChange={() => toggleCheckbox(question.id, option.value)} disabled={!!existingResponse} /><Label>{option.label}</Label></div>
            ))}
          </div>
        );
      default:
        return <Input type={question.type === 'number' ? 'number' : 'text'} value={answers[question.id] || ''} onChange={(e) => updateAnswer(question.id, e.target.value)} disabled={!!existingResponse} data-testid={`portal-form-answer-${question.id}`} />;
    }
  };

  return (
    <PortalLayout activeNav="forms" customerName={customerName}>
      {loading ? <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-teal-500" /></div> : (
        <div className="space-y-6">
          <Link to="/customer-portal/forms" className="inline-flex items-center text-sm text-slate-600 hover:text-teal-600"><ChevronLeft className="h-4 w-4 mr-1" /> Back to Forms</Link>
          <Card className="border-slate-200">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-xl">{questionnaire?.name}</CardTitle>
                  <CardDescription>{request?.instructions || questionnaire?.description}</CardDescription>
                </div>
                <Badge className={statusBadge[request?.status] || 'bg-slate-100 text-slate-700'}>{request?.status?.replace('_', ' ')}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {existingResponse && (
                <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-green-700 flex items-center gap-2" data-testid="portal-form-submitted-banner">
                  <CheckCircle className="h-5 w-5" /> This form has already been submitted.
                </div>
              )}
              {!existingResponse && request?.due_date && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-700">Due {new Date(request.due_date).toLocaleDateString()}</div>
              )}
              <div className="space-y-6">
                {questionnaire?.questions?.map((question) => (
                  <div key={question.id} className="space-y-2">
                    {!['heading', 'paragraph'].includes(question.type) && <Label>{question.label}{question.required && ' *'}</Label>}
                    {question.description && !['heading', 'paragraph'].includes(question.type) && <p className="text-xs text-slate-500">{question.description}</p>}
                    {renderQuestion(question)}
                  </div>
                ))}
              </div>
              {!existingResponse && (
                <Button className="bg-teal-500 hover:bg-teal-600" onClick={handleSubmit} disabled={submitting} data-testid="portal-form-submit-button">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />} Submit Form
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </PortalLayout>
  );
}
