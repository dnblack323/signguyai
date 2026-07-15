import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import {
  CheckCircle, AlertCircle, Upload, Loader2, FileText,
  Lock, PenLine, X, File as FileIcon, Image as ImageIcon
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

// ─── Conditional visibility ────────────────────────────────────────────────
function shouldShowQuestion(question, allQuestions, answers) {
  const cond = question.conditional;
  if (!cond) return true;

  // Resolve target question by ID or by label
  let targetId = cond.depends_on || null;
  if (!targetId && cond.depends_on_label) {
    const tgt = allQuestions.find(q => q.label === cond.depends_on_label);
    targetId = tgt?.id || null;
  }
  if (!targetId) return true;

  const answer = answers[targetId];
  const val    = cond.value;

  switch (cond.operator) {
    case 'equals':       return String(answer ?? '') === String(val);
    case 'not_equals':   return String(answer ?? '') !== String(val);
    case 'contains':
      return Array.isArray(answer) ? answer.includes(val) : String(answer ?? '').includes(val);
    case 'not_contains':
      return Array.isArray(answer) ? !answer.includes(val) : !String(answer ?? '').includes(val);
    case 'greater_than': return parseFloat(answer) > parseFloat(val);
    case 'less_than':    return parseFloat(answer) < parseFloat(val);
    default:             return true;
  }
}

// ─── File Upload Widget ────────────────────────────────────────────────────
function FileUploadWidget({ questionId, questionnaireId, value, onChange, disabled }) {
  const inputRef  = useRef();
  const [uploading, setUploading] = useState(false);
  const files = Array.isArray(value) ? value : (value ? [value] : []);

  const handleFiles = async (selected) => {
    const arr = Array.from(selected);
    if (!arr.length) return;
    setUploading(true);
    const newFiles = [...files];
    for (const f of arr) {
      try {
        const fd = new FormData();
        fd.append('file', f);
        fd.append('question_id', questionId);
        const res = await axios.post(
          `${API_URL}/api/questionnaires/public/${questionnaireId}/upload`,
          fd, { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        newFiles.push({ url: res.data.url, filename: res.data.filename || f.name, size: res.data.size_bytes });
      } catch (err) {
        toast.error(`Failed to upload ${f.name}: ${err.response?.data?.detail || 'Upload error'}`);
      }
    }
    onChange(newFiles);
    setUploading(false);
  };

  const remove = (idx) => {
    const updated = files.filter((_, i) => i !== idx);
    onChange(updated.length ? updated : '');
  };

  return (
    <div className="space-y-2">
      <div
        className="border-2 border-dashed border-gray-200 rounded-lg p-5 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
        onClick={() => !disabled && inputRef.current?.click()}
      >
        {uploading ? (
          <><Loader2 className="h-6 w-6 text-blue-500 animate-spin mx-auto mb-1" /><p className="text-sm text-blue-600">Uploading…</p></>
        ) : (
          <>
            <Upload className="h-6 w-6 text-gray-400 mx-auto mb-1" />
            <p className="text-sm font-medium text-gray-700">Click to choose files</p>
            <p className="text-xs text-gray-400 mt-0.5">JPG, PNG, PDF, SVG, AI, EPS, ZIP · Max 25MB each</p>
          </>
        )}
      </div>
      <input ref={inputRef} type="file" multiple className="hidden" disabled={disabled || uploading}
        accept="image/*,.pdf,.ai,.eps,.svg,.zip,.doc,.docx"
        onChange={e => handleFiles(e.target.files)} />

      {files.length > 0 && (
        <div className="space-y-1.5 mt-1">
          {files.map((f, i) => (
            <div key={i} className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2 min-w-0">
                {/\.(jpg|jpeg|png|gif|webp)/i.test(f.filename || '') ? (
                  <ImageIcon className="w-4 h-4 text-blue-500 flex-shrink-0" />
                ) : (
                  <FileIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                )}
                <a href={f.url} target="_blank" rel="noreferrer"
                   className="text-sm text-blue-600 hover:underline truncate">
                  {f.filename}
                </a>
                {f.size && <span className="text-xs text-gray-400 flex-shrink-0">{(f.size / 1024).toFixed(0)} KB</span>}
              </div>
              {!disabled && (
                <button type="button" onClick={() => remove(i)}
                        className="ml-2 text-gray-400 hover:text-red-500 flex-shrink-0">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────
export default function PublicQuestionnaire() {
  const { questionnaireId } = useParams();
  const [questionnaire, setQuestionnaire] = useState(null);
  const [loading, setLoading]     = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted]  = useState(false);
  const [answers, setAnswers]      = useState({});
  const [errors, setErrors]        = useState({});
  const [lockedIds, setLockedIds]  = useState(new Set());

  const fetchQuestionnaire = useCallback(async () => {
    try {
      const res  = await axios.get(`${API_URL}/api/questionnaires/public/${questionnaireId}`);
      const qData = res.data;
      setQuestionnaire(qData);

      const locked = new Set(qData.locked_answer_ids || []);
      const prefills = qData.prefill_answers || {};
      const initial  = {};

      qData.questions?.forEach(q => {
        if (q.type === 'checkbox' || q.type === 'multi_select') {
          initial[q.id] = prefills[q.id] ?? [];
        } else if (q.type === 'date' && !prefills[q.id] && (q.label || '').toLowerCase().includes('today')) {
          initial[q.id] = new Date().toISOString().split('T')[0];
        } else if (q.type === 'file_upload') {
          initial[q.id] = prefills[q.id] ?? [];
        } else {
          initial[q.id] = prefills[q.id] ?? '';
        }

        if (q.is_contact_email && !initial[q.id] && qData.recipient_email) {
          initial[q.id] = qData.recipient_email;
          locked.add(q.id);
        }
      });

      setLockedIds(new Set(locked));
      setAnswers(initial);
    } catch {
      /* questionnaire stays null → Not Found screen */
    } finally {
      setLoading(false);
    }
  }, [questionnaireId]);

  useEffect(() => { fetchQuestionnaire(); }, [fetchQuestionnaire]);

  const allQuestions = questionnaire?.questions || [];

  const visibleQuestions = allQuestions.filter(q =>
    shouldShowQuestion(q, allQuestions, answers)
  );

  const validateForm = () => {
    const errs = {};
    visibleQuestions.forEach(q => {
      if (lockedIds.has(q.id)) return;
      if (q.required && q.type !== 'heading' && q.type !== 'paragraph') {
        const a = answers[q.id];
        const empty = !a || (Array.isArray(a) && a.length === 0) || (typeof a === 'string' && !a.trim());
        if (empty) errs[q.id] = 'This field is required';
      }
    });
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      toast.error('Please fill in all required fields');
      const firstId = Object.keys(errors)[0] || Object.keys(
        (() => {
          const e2 = {};
          visibleQuestions.forEach(q => {
            if (lockedIds.has(q.id)) return;
            if (q.required && q.type !== 'heading' && q.type !== 'paragraph') {
              const a = answers[q.id];
              if (!a || (Array.isArray(a) && !a.length) || (typeof a === 'string' && !a.trim()))
                e2[q.id] = 1;
            }
          });
          return e2;
        })()
      )[0];
      if (firstId) document.getElementById(`q-${firstId}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    setSubmitting(true);
    const contactNameQ  = allQuestions.find(q => q.is_contact_name);
    const contactEmailQ = allQuestions.find(q => q.is_contact_email);

    try {
      await axios.post(`${API_URL}/api/questionnaires/public/${questionnaireId}/submit`, {
        questionnaire_id:  questionnaireId,
        answers,
        customer_name:  contactNameQ  ? (answers[contactNameQ.id]  || '') : '',
        customer_email: contactEmailQ ? (answers[contactEmailQ.id] || '') : '',
        webstore_id: questionnaire?.webstore_id || null,
      });
      setSubmitted(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateAnswer = (id, val) => {
    setAnswers(prev => ({ ...prev, [id]: val }));
    if (errors[id]) setErrors(prev => ({ ...prev, [id]: null }));
  };

  const toggleCheckbox = (id, val) => {
    const cur = answers[id] || [];
    updateAnswer(id, cur.includes(val) ? cur.filter(v => v !== val) : [...cur, val]);
  };

  // ── Render a single question ─────────────────────────────────────────────
  const renderQuestion = (question) => {
    const err      = errors[question.id];
    const isLocked = lockedIds.has(question.id);

    const LockedBadge = () => (
      <span className="inline-flex items-center gap-1 ml-2 px-2 py-0.5 rounded-full
                        bg-amber-50 text-amber-700 border border-amber-200 text-xs font-medium">
        <Lock className="h-3 w-3" /> Pre-filled
      </span>
    );

    const lbl  = err ? 'text-red-600' : 'text-gray-700 font-medium';
    const inp  = [
      'bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-blue-500',
      err    ? 'border-red-400 focus:border-red-400' : '',
      isLocked ? 'bg-gray-50 cursor-not-allowed opacity-75' : '',
    ].join(' ');

    const Err = () => err ? <p className="text-xs text-red-600 mt-1">{err}</p> : null;

    switch (question.type) {
      case 'heading':
        return (
          <div className="pt-6 pb-2 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-900">{question.label}</h3>
            {question.description && <p className="text-sm text-gray-500 mt-0.5">{question.description}</p>}
          </div>
        );

      case 'paragraph':
        return (
          <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
            <p className="text-sm text-blue-800 leading-relaxed">{question.label}</p>
          </div>
        );

      case 'text':
      case 'email':
      case 'phone':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center flex-wrap gap-1">
              <Label className={lbl}>
                {question.label}
                {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
              {isLocked && <LockedBadge />}
            </div>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <Input type={question.type === 'phone' ? 'tel' : question.type}
              value={answers[question.id] || ''}
              onChange={e => !isLocked && updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder || ''} className={inp}
              readOnly={isLocked} disabled={isLocked} />
            <Err />
          </div>
        );

      case 'number':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}{question.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <Input type="number" value={answers[question.id] || ''} placeholder={question.placeholder || ''}
              onChange={e => updateAnswer(question.id, e.target.value)} className={inp} />
            <Err />
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}{question.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <Textarea value={answers[question.id] || ''}
              onChange={e => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder || ''} rows={4} className={`${inp} resize-none`} />
            <Err />
          </div>
        );

      case 'date':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}{question.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
            <Input type="date" value={answers[question.id] || ''}
              onChange={e => updateAnswer(question.id, e.target.value)} className={inp} />
            <Err />
          </div>
        );

      case 'select':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center flex-wrap gap-1">
              <Label className={lbl}>{question.label}
                {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
              {isLocked && <LockedBadge />}
            </div>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <Select value={answers[question.id] || ''} onValueChange={v => !isLocked && updateAnswer(question.id, v)} disabled={isLocked}>
              <SelectTrigger className={inp}><SelectValue placeholder="Select an option…" /></SelectTrigger>
              <SelectContent>
                {question.options?.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
            <Err />
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}{question.required && <span className="text-red-500 ml-0.5">*</span>}</Label>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <RadioGroup value={answers[question.id] || ''} onValueChange={v => updateAnswer(question.id, v)} disabled={isLocked}>
              {question.options?.map(o => (
                <div key={o.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={o.value} id={`${question.id}-${o.value}`} disabled={isLocked} />
                  <Label htmlFor={`${question.id}-${o.value}`} className="font-normal text-gray-700">{o.label}</Label>
                </div>
              ))}
            </RadioGroup>
            <Err />
          </div>
        );

      case 'checkbox':
      case 'multi_select':
        return (
          <div className="space-y-2" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}
              {question.required && !isLocked && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <div className="space-y-2 mt-1">
              {question.options?.map(o => (
                <div key={o.value} className={`flex items-center space-x-2.5 ${isLocked ? 'opacity-60' : ''}`}>
                  <Checkbox id={`${question.id}-${o.value}`}
                    checked={(answers[question.id] || []).includes(o.value)}
                    onCheckedChange={() => !isLocked && toggleCheckbox(question.id, o.value)}
                    disabled={isLocked} className="border-gray-300" />
                  <Label htmlFor={`${question.id}-${o.value}`} className="font-normal text-gray-700 cursor-pointer">{o.label}</Label>
                </div>
              ))}
            </div>
            <Err />
          </div>
        );

      case 'signature':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <div className="flex items-center gap-2">
              <PenLine className="w-4 h-4 text-gray-500" />
              <Label className={lbl}>{question.label || 'Electronic Signature'}
                {question.required && <span className="text-red-500 ml-0.5">*</span>}
              </Label>
            </div>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <Input type="text" value={answers[question.id] || ''}
              onChange={e => updateAnswer(question.id, e.target.value)}
              placeholder="Type your full name to sign" className={inp}
              style={{ fontFamily: 'Georgia, serif', fontSize: '1.05rem' }} />
            <p className="text-xs text-gray-400">By typing your name you are providing an electronic signature.</p>
            <Err />
          </div>
        );

      case 'file_upload':
        return (
          <div className="space-y-1.5" id={`q-${question.id}`}>
            <Label className={lbl}>{question.label}
              {question.required && <span className="text-red-500 ml-0.5">*</span>}
            </Label>
            {question.description && <p className="text-xs text-gray-500">{question.description}</p>}
            <FileUploadWidget
              questionId={question.id}
              questionnaireId={questionnaireId}
              value={answers[question.id] || []}
              onChange={v => updateAnswer(question.id, v)}
              disabled={isLocked}
            />
            <Err />
          </div>
        );

      default:
        return null;
    }
  };

  // ── Screens ──────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
    </div>
  );

  if (!questionnaire) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-md w-full shadow-sm">
        <CardContent className="p-8 text-center">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Form Not Found</h2>
          <p className="text-gray-500 text-sm">This form may no longer be active. Please contact the store owner.</p>
        </CardContent>
      </Card>
    </div>
  );

  if (submitted) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full shadow-sm">
        <CardContent className="p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="h-9 w-9 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">You're all set!</h2>
          <p className="text-gray-600 mb-4">
            {questionnaire.thank_you_message || "We received your submission and will be in touch soon."}
          </p>
          <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-left space-y-2 mt-4">
            <p className="text-sm font-semibold text-blue-900">What happens next:</p>
            <ol className="text-sm text-blue-800 space-y-1.5 list-decimal list-inside">
              <li>We'll review your submission and begin planning your store.</li>
              <li>We'll send you a <strong>Pre-Launch Packet</strong> with mockups and final details for your approval.</li>
              <li>Watch for a <strong>Stripe email</strong> to set up payments — check your spam folder.</li>
              <li>Once you approve everything and Stripe is connected, your store goes live.</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <Card className="shadow-sm mb-2 border-gray-200">
          <CardHeader className="pb-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-50 rounded-lg flex-shrink-0 mt-0.5">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-xl text-gray-900">{questionnaire.name}</CardTitle>
                {questionnaire.description && (
                  <CardDescription className="text-gray-500 mt-0.5">{questionnaire.description}</CardDescription>
                )}
                {questionnaire.intro_text && (
                  <p className="text-sm text-gray-600 mt-2 leading-relaxed">{questionnaire.intro_text}</p>
                )}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Questions */}
        <Card className="shadow-sm border-gray-200">
          <CardContent className="p-6 sm:p-8">
            <form onSubmit={handleSubmit} noValidate className="space-y-6">
              {visibleQuestions.map(q => (
                <div key={q.id}>{renderQuestion(q)}</div>
              ))}

              {Object.keys(errors).length > 0 && (
                <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                  <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">Please fill in all required fields highlighted above.</p>
                </div>
              )}

              <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white h-11 text-base font-medium mt-2"
                disabled={submitting} data-testid="questionnaire-submit-btn">
                {submitting ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting…</> : 'Submit'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-gray-400 mt-4">Powered by SignGuy AI</p>
      </div>
    </div>
  );
}
