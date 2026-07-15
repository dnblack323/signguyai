import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  CheckCircle, AlertCircle, Upload, Loader2, FileText, Lock, PenLine
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function PublicQuestionnaire() {
  const { questionnaireId } = useParams();
  const [questionnaire, setQuestionnaire] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [answers, setAnswers] = useState({});
  const [errors, setErrors] = useState({});

  // IDs of questions whose answers are locked (set by provider)
  const [lockedIds, setLockedIds] = useState(new Set());
  // Maps question label→id for is_contact_name / is_contact_email fields
  const [contactNameId, setContactNameId] = useState(null);
  const [contactEmailId, setContactEmailId] = useState(null);

  const fetchQuestionnaire = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/questionnaires/public/${questionnaireId}`);
      const qData = res.data;
      setQuestionnaire(qData);

      const locked = new Set(qData.locked_answer_ids || []);
      setLockedIds(locked);

      const prefills = qData.prefill_answers || {};
      const initial = {};
      let nameId = null;
      let emailId = null;

      qData.questions?.forEach(q => {
        // Determine initial value
        if (q.type === 'checkbox' || q.type === 'multi_select') {
          initial[q.id] = prefills[q.id] ?? [];
        } else if (q.type === 'date' && !prefills[q.id] && q.label?.toLowerCase().includes("today")) {
          initial[q.id] = new Date().toISOString().split('T')[0];
        } else {
          initial[q.id] = prefills[q.id] ?? '';
        }

        // Track contact-flag fields
        if (q.is_contact_name) nameId = q.id;
        if (q.is_contact_email) emailId = q.id;
      });

      // Auto-fill email from questionnaire-level recipient_email if present
      if (emailId && !initial[emailId] && qData.recipient_email) {
        initial[emailId] = qData.recipient_email;
        locked.add(emailId);
      }

      setContactNameId(nameId);
      setContactEmailId(emailId);
      setLockedIds(new Set(locked));
      setAnswers(initial);
    } catch {
      // handled via questionnaire staying null
    } finally {
      setLoading(false);
    }
  }, [questionnaireId]);

  useEffect(() => { fetchQuestionnaire(); }, [fetchQuestionnaire]);

  // customerInfo is derived from the contact-flag questions (no separate block)
  const customerName = answers[contactNameId] || '';
  const customerEmail = answers[contactEmailId] || '';

  const validateForm = () => {
    const newErrors = {};

    questionnaire?.questions?.forEach(q => {
      if (lockedIds.has(q.id)) return;
      if (q.required && q.type !== 'heading' && q.type !== 'paragraph') {
        const answer = answers[q.id];
        if (!answer || (Array.isArray(answer) && answer.length === 0) ||
            (typeof answer === 'string' && answer.trim() === '')) {
          newErrors[q.id] = 'This field is required';
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      toast.error('Please fill in all required fields');
      // scroll to first error
      const firstErrId = Object.keys(errors)[0];
      if (firstErrId) {
        document.getElementById(`q-${firstErrId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/questionnaires/public/${questionnaireId}/submit`, {
        questionnaire_id: questionnaireId,
        answers,
        customer_name: customerName,
        customer_email: customerEmail,
        webstore_id: questionnaire?.webstore_id || null,
      });
      setSubmitted(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateAnswer = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
    if (errors[questionId]) setErrors(prev => ({ ...prev, [questionId]: null }));
  };

  const toggleCheckbox = (questionId, value) => {
    const current = answers[questionId] || [];
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    updateAnswer(questionId, updated);
  };

  const renderQuestion = (question) => {
    const hasError = errors[question.id];
    const isLocked = lockedIds.has(question.id);

    const LockedBadge = () => (
      <span className="inline-flex items-center gap-1 ml-2 px-2 py-0.5 rounded-full
                        bg-amber-50 text-amber-700 border border-amber-200 text-xs font-medium">
        <Lock className="h-3 w-3" /> Pre-filled
      </span>
    );

    const labelClass = hasError ? 'text-red-600' : 'text-gray-700 font-medium';
    const inputClass = `bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:ring-blue-500
      ${hasError ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : ''}
      ${isLocked ? 'bg-gray-50 cursor-not-allowed opacity-75' : ''}`;

    const ErrorMsg = () => hasError ? (
      <p className="text-xs text-red-600 mt-1">{hasError}</p>
    ) : null;

    switch (question.type) {
      case 'heading':
        return (
          <div className="pt-6 pb-2 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-900">{question.label}</h3>
            {question.description && (
              <p className="text-sm text-gray-500 mt-1">{question.description}</p>
            )}
          </div>
        );

      case 'paragraph':
        return (
          <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
            <p className="text-sm text-blue-800">{question.label}</p>
          </div>
        );

      case 'text':
      case 'email':
      case 'phone':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center flex-wrap gap-1">
              <Label className={labelClass}>
                {question.label}
                {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
              {isLocked && <LockedBadge />}
            </div>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Input
              type={question.type === 'phone' ? 'tel' : question.type}
              value={answers[question.id] || ''}
              onChange={(e) => !isLocked && updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder || ''}
              className={inputClass}
              readOnly={isLocked}
              disabled={isLocked}
            />
            <ErrorMsg />
          </div>
        );

      case 'number':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Input
              type="number"
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder || '0'}
              className={inputClass}
            />
            <ErrorMsg />
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Textarea
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder || ''}
              rows={4}
              className={`${inputClass} resize-none`}
            />
            <ErrorMsg />
          </div>
        );

      case 'date':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Input
              type="date"
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              className={inputClass}
            />
            <ErrorMsg />
          </div>
        );

      case 'select':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center flex-wrap gap-1">
              <Label className={labelClass}>
                {question.label}
                {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
              {isLocked && <LockedBadge />}
            </div>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Select
              value={answers[question.id] || ''}
              onValueChange={(v) => !isLocked && updateAnswer(question.id, v)}
              disabled={isLocked}
            >
              <SelectTrigger className={inputClass}>
                <SelectValue placeholder="Select an option..." />
              </SelectTrigger>
              <SelectContent>
                {question.options?.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <ErrorMsg />
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <RadioGroup
              value={answers[question.id] || ''}
              onValueChange={(v) => !isLocked && updateAnswer(question.id, v)}
              disabled={isLocked}
            >
              {question.options?.map((opt) => (
                <div key={opt.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={opt.value} id={`${question.id}-${opt.value}`} disabled={isLocked} />
                  <Label htmlFor={`${question.id}-${opt.value}`} className="font-normal text-gray-700">
                    {opt.label}
                  </Label>
                </div>
              ))}
            </RadioGroup>
            <ErrorMsg />
          </div>
        );

      case 'checkbox':
      case 'multi_select':
        return (
          <div className="space-y-2" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <div className="space-y-2 mt-1">
              {question.options?.map((opt) => (
                <div key={opt.value} className={`flex items-center space-x-2.5 ${isLocked ? 'opacity-60' : ''}`}>
                  <Checkbox
                    id={`${question.id}-${opt.value}`}
                    checked={(answers[question.id] || []).includes(opt.value)}
                    onCheckedChange={() => !isLocked && toggleCheckbox(question.id, opt.value)}
                    disabled={isLocked}
                    className="border-gray-300"
                  />
                  <Label htmlFor={`${question.id}-${opt.value}`} className="font-normal text-gray-700 cursor-pointer">
                    {opt.label}
                  </Label>
                </div>
              ))}
            </div>
            <ErrorMsg />
          </div>
        );

      case 'signature':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center gap-2">
              <PenLine className="w-4 h-4 text-gray-500" />
              <Label className={labelClass}>
                {question.label || 'Electronic Signature'}
                {question.required && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
            </div>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <Input
              type="text"
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder="Type your full name to sign"
              className={`${inputClass} italic`}
              style={{ fontFamily: 'Georgia, serif', fontSize: '1.05rem' }}
            />
            <p className="text-xs text-gray-400">By typing your name you are providing an electronic signature.</p>
            <ErrorMsg />
          </div>
        );

      case 'file_upload':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={labelClass}>
              {question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-gray-500">{question.description}</p>
            )}
            <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center bg-gray-50">
              <Upload className="h-7 w-7 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">File upload will be available after submission</p>
              <p className="text-xs text-gray-400 mt-1">We'll follow up with instructions to send your files.</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // ─── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
      </div>
    );
  }

  // ─── Not found ─────────────────────────────────────────────────────────────
  if (!questionnaire) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full shadow-sm">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Form Not Found</h2>
            <p className="text-gray-500 text-sm">
              This form may have been removed or is no longer active. Please contact the store owner.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ─── Success ───────────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full shadow-sm">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-9 w-9 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h2>
            <p className="text-gray-600">
              {questionnaire.thank_you_message || "Your information has been received. We'll be in touch soon."}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ─── Form ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header card */}
        <Card className="shadow-sm mb-2 border-gray-200">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg flex-shrink-0">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-xl text-gray-900">{questionnaire.name}</CardTitle>
                {questionnaire.description && (
                  <CardDescription className="text-gray-500 mt-0.5">{questionnaire.description}</CardDescription>
                )}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Questions */}
        <Card className="shadow-sm border-gray-200">
          <CardContent className="p-6 sm:p-8">
            <form onSubmit={handleSubmit} noValidate className="space-y-6">
              {questionnaire.questions?.map((question) => (
                <div key={question.id}>
                  {renderQuestion(question)}
                </div>
              ))}

              {/* Error summary */}
              {Object.keys(errors).length > 0 && (
                <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">
                    Please fill in all required fields highlighted above before submitting.
                  </p>
                </div>
              )}

              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white h-11 text-base font-medium mt-2"
                disabled={submitting}
                data-testid="questionnaire-submit-btn"
              >
                {submitting ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Submitting...</>
                ) : (
                  'Submit'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-400 mt-4">
          Powered by SignGuy AI
        </p>
      </div>
    </div>
  );
}
