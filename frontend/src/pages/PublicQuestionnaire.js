import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { 
  CheckCircle, AlertCircle, Upload, Calendar as CalendarIcon,
  Loader2, FileText
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
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetchQuestionnaire();
  }, [questionnaireId]);

  const fetchQuestionnaire = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/questionnaires/public/${questionnaireId}`);
      setQuestionnaire(response.data);
      
      // Initialize answers object
      const initialAnswers = {};
      response.data.questions?.forEach(q => {
        if (q.type === 'checkbox' || q.type === 'multi_select') {
          initialAnswers[q.id] = [];
        } else {
          initialAnswers[q.id] = '';
        }
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Failed to fetch questionnaire:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!customerInfo.name.trim()) {
      newErrors.customer_name = 'Please enter your name';
    }
    if (!customerInfo.email.trim()) {
      newErrors.customer_email = 'Please enter your email';
    } else if (!/\S+@\S+\.\S+/.test(customerInfo.email)) {
      newErrors.customer_email = 'Please enter a valid email';
    }

    questionnaire?.questions?.forEach(q => {
      if (q.required && q.type !== 'heading' && q.type !== 'paragraph') {
        const answer = answers[q.id];
        if (!answer || (Array.isArray(answer) && answer.length === 0)) {
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
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API_URL}/api/questionnaires/public/${questionnaireId}/submit`, {
        questionnaire_id: questionnaireId,
        answers,
        customer_name: customerInfo.name,
        customer_email: customerInfo.email
      });
      setSubmitted(true);
    } catch (error) {
      console.error('Failed to submit:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const updateAnswer = (questionId, value) => {
    setAnswers({ ...answers, [questionId]: value });
    // Clear error when user starts typing
    if (errors[questionId]) {
      setErrors({ ...errors, [questionId]: null });
    }
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

    switch (question.type) {
      case 'heading':
        return (
          <div className="pt-4 pb-2">
            <h3 className="text-lg font-semibold text-white">{question.label}</h3>
            {question.description && (
              <p className="text-sm text-muted-foreground mt-1">{question.description}</p>
            )}
          </div>
        );

      case 'paragraph':
        return (
          <p className="text-muted-foreground">{question.label}</p>
        );

      case 'text':
      case 'email':
      case 'phone':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <Input
              type={question.type}
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder}
              className={hasError ? 'border-destructive' : ''}
            />
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <Textarea
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder}
              rows={4}
              className={hasError ? 'border-destructive' : ''}
            />
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              type="number"
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              placeholder={question.placeholder}
              className={hasError ? 'border-destructive' : ''}
            />
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'date':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              type="date"
              value={answers[question.id] || ''}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              className={hasError ? 'border-destructive' : ''}
            />
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <Select
              value={answers[question.id] || ''}
              onValueChange={(value) => updateAnswer(question.id, value)}
            >
              <SelectTrigger className={hasError ? 'border-destructive' : ''}>
                <SelectValue placeholder="Select an option..." />
              </SelectTrigger>
              <SelectContent>
                {question.options?.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <RadioGroup
              value={answers[question.id] || ''}
              onValueChange={(value) => updateAnswer(question.id, value)}
              className="space-y-2"
            >
              {question.options?.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={option.value} id={`${question.id}-${option.value}`} />
                  <Label htmlFor={`${question.id}-${option.value}`} className="font-normal">
                    {option.label}
                  </Label>
                </div>
              ))}
            </RadioGroup>
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'checkbox':
      case 'multi_select':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <div className="space-y-2">
              {question.options?.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`${question.id}-${option.value}`}
                    checked={(answers[question.id] || []).includes(option.value)}
                    onCheckedChange={() => toggleCheckbox(question.id, option.value)}
                  />
                  <Label htmlFor={`${question.id}-${option.value}`} className="font-normal">
                    {option.label}
                  </Label>
                </div>
              ))}
            </div>
            {hasError && <p className="text-xs text-destructive">{hasError}</p>}
          </div>
        );

      case 'file_upload':
        return (
          <div className="space-y-2">
            <Label className={hasError ? 'text-destructive' : ''}>
              {question.label} {question.required && <span className="text-destructive">*</span>}
            </Label>
            {question.description && (
              <p className="text-xs text-muted-foreground">{question.description}</p>
            )}
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
              <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                File upload will be available after submission
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-[#2F8BFB]" />
      </div>
    );
  }

  if (!questionnaire) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-[#111826] border-[#1E293B]">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Questionnaire Not Found</h2>
            <p className="text-muted-foreground">
              This questionnaire may have been removed or is not currently active.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-[#111826] border-[#1E293B]">
          <CardContent className="p-8 text-center">
            <CheckCircle className="h-16 w-16 text-emerald-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Thank You!</h2>
            <p className="text-muted-foreground">
              {questionnaire.thank_you_message}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <Card className="bg-[#111826] text-white border-[#1E293B]">
          <CardHeader className="border-b border-[#1E293B]">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#2F8BFB]/20 rounded-lg">
                <FileText className="h-6 w-6 text-[#2F8BFB]" />
              </div>
              <div>
                <CardTitle className="text-xl text-white">{questionnaire.name}</CardTitle>
                {questionnaire.description && (
                  <CardDescription>{questionnaire.description}</CardDescription>
                )}
              </div>
            </div>
          </CardHeader>
          
          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Customer Info */}
              <div className="bg-[#0B0F17] rounded-lg p-4 space-y-4">
                <h3 className="font-medium text-white">Your Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className={errors.customer_name ? 'text-destructive' : ''}>
                      Name <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      value={customerInfo.name}
                      onChange={(e) => setCustomerInfo({ ...customerInfo, name: e.target.value })}
                      placeholder="Your name"
                      className={errors.customer_name ? 'border-destructive' : ''}
                    />
                    {errors.customer_name && (
                      <p className="text-xs text-destructive">{errors.customer_name}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label className={errors.customer_email ? 'text-destructive' : ''}>
                      Email <span className="text-destructive">*</span>
                    </Label>
                    <Input
                      type="email"
                      value={customerInfo.email}
                      onChange={(e) => setCustomerInfo({ ...customerInfo, email: e.target.value })}
                      placeholder="your@email.com"
                      className={errors.customer_email ? 'border-destructive' : ''}
                    />
                    {errors.customer_email && (
                      <p className="text-xs text-destructive">{errors.customer_email}</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Questions */}
              <div className="space-y-6">
                {questionnaire.questions?.map((question) => (
                  <div key={question.id}>
                    {renderQuestion(question)}
                  </div>
                ))}
              </div>

              {/* Submit */}
              <Button 
                type="submit" 
                className="w-full bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
