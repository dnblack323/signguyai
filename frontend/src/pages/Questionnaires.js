import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Plus, FileText, Settings, Trash2, Copy, Eye, EyeOff,
  ChevronDown, ChevronUp, GripVertical, X, Check,
  Car, SignpostBig, Shirt, FileQuestion, Layers,
  ExternalLink, Users, Clock, BarChart3, Sparkles, Send, Loader2 as Loader2Icon
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const categoryIcons = {
  vehicle_wrap: Car,
  signage: SignpostBig,
  apparel: Shirt,
  print: FileText,
  custom: Layers,
  general: FileQuestion,
};

const categoryColors = {
  vehicle_wrap: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  signage: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  apparel: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  print: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  custom: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  general: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const statusColors = {
  draft: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  archived: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const questionTypes = [
  { value: 'text', label: 'Text (Single Line)' },
  { value: 'textarea', label: 'Text (Multi-Line)' },
  { value: 'number', label: 'Number' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone Number' },
  { value: 'select', label: 'Dropdown Select' },
  { value: 'multi_select', label: 'Multi-Select' },
  { value: 'radio', label: 'Radio Buttons' },
  { value: 'checkbox', label: 'Checkboxes' },
  { value: 'date', label: 'Date Picker' },
  { value: 'file_upload', label: 'File Upload' },
  { value: 'heading', label: 'Section Heading' },
  { value: 'paragraph', label: 'Paragraph Text' },
];

export default function Questionnaires() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [questionnaires, setQuestionnaires] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedTab, setSelectedTab] = useState('all');
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedQuestionnaire, setSelectedQuestionnaire] = useState(null);
  const [showResponsesDialog, setShowResponsesDialog] = useState(false);
  const [responses, setResponses] = useState([]);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'general',
    questions: [],
    thank_you_message: 'Thank you for completing this questionnaire!'
  });

  useEffect(() => {
    fetchQuestionnaires();
    fetchTemplates();
  }, []);

  const fetchQuestionnaires = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/questionnaires`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestionnaires(response.data);
    } catch (error) {
      console.error('Failed to fetch questionnaires:', error);
      toast.error('Failed to load questionnaires');
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/questionnaires/templates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const createFromTemplate = async (templateId) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/questionnaires/from-template/${templateId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuestionnaires([response.data, ...questionnaires]);
      setShowTemplateDialog(false);
      toast.success('Questionnaire created from template!');
      
      // Open for editing
      setSelectedQuestionnaire(response.data);
      setFormData(response.data);
      setShowEditDialog(true);
    } catch (error) {
      console.error('Failed to create from template:', error);
      toast.error('Failed to create questionnaire');
    }
  };

  const createQuestionnaire = async () => {
    if (!formData.name.trim()) {
      toast.error('Please enter a name');
      return;
    }

    try {
      const response = await axios.post(
        `${API_URL}/api/questionnaires`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuestionnaires([response.data, ...questionnaires]);
      setShowCreateDialog(false);
      resetForm();
      toast.success('Questionnaire created!');
    } catch (error) {
      console.error('Failed to create questionnaire:', error);
      toast.error('Failed to create questionnaire');
    }
  };

  const updateQuestionnaire = async () => {
    if (!selectedQuestionnaire) return;

    try {
      const response = await axios.put(
        `${API_URL}/api/questionnaires/${selectedQuestionnaire.id}`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuestionnaires(questionnaires.map(q => 
        q.id === selectedQuestionnaire.id ? response.data : q
      ));
      setShowEditDialog(false);
      toast.success('Questionnaire updated!');
    } catch (error) {
      console.error('Failed to update questionnaire:', error);
      toast.error('Failed to update questionnaire');
    }
  };

  const duplicateQuestionnaire = async (questionnaire) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/questionnaires/${questionnaire.id}/duplicate`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuestionnaires([response.data, ...questionnaires]);
      toast.success('Questionnaire duplicated!');
    } catch (error) {
      console.error('Failed to duplicate:', error);
      toast.error('Failed to duplicate questionnaire');
    }
  };

  const deleteQuestionnaire = async (id) => {
    if (!confirm('Are you sure you want to delete this questionnaire?')) return;

    try {
      await axios.delete(`${API_URL}/api/questionnaires/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQuestionnaires(questionnaires.filter(q => q.id !== id));
      toast.success('Questionnaire deleted');
    } catch (error) {
      console.error('Failed to delete:', error);
      toast.error('Failed to delete questionnaire');
    }
  };

  const toggleStatus = async (questionnaire) => {
    const newStatus = questionnaire.status === 'active' ? 'draft' : 'active';
    try {
      const response = await axios.put(
        `${API_URL}/api/questionnaires/${questionnaire.id}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setQuestionnaires(questionnaires.map(q => 
        q.id === questionnaire.id ? response.data : q
      ));
      toast.success(`Questionnaire ${newStatus === 'active' ? 'activated' : 'deactivated'}`);
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  const viewResponses = async (questionnaire) => {
    try {
      const response = await axios.get(
        `${API_URL}/api/questionnaires/${questionnaire.id}/responses`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResponses(response.data.responses);
      setSelectedQuestionnaire(questionnaire);
      setShowResponsesDialog(true);
    } catch (error) {
      console.error('Failed to fetch responses:', error);
      toast.error('Failed to load responses');
    }
  };

  const copyShareLink = (questionnaire) => {
    const url = `${window.location.origin}/questionnaire/${questionnaire.id}`;
    navigator.clipboard.writeText(url);
    toast.success('Link copied to clipboard!');
  };

  const [sendDialog, setSendDialog] = useState(null);
  const [sendEmail, setSendEmail] = useState('');
  const [sending, setSending] = useState(false);

  const handleSendEmail = async () => {
    if (!sendEmail.trim() || !sendDialog) return;
    setSending(true);
    try {
      await api.post(`/questionnaires/${sendDialog.id}/send-email`, {
        email: sendEmail,
        public_url: window.location.origin,
      });
      toast.success(`Questionnaire sent to ${sendEmail}`);
      setSendDialog(null);
      setSendEmail('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send');
    } finally { setSending(false); }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'general',
      questions: [],
      thank_you_message: 'Thank you for completing this questionnaire!'
    });
  };

  const addQuestion = () => {
    const newQuestion = {
      id: `q_${Date.now()}`,
      type: 'text',
      label: '',
      description: '',
      placeholder: '',
      required: false,
      options: [],
      order: formData.questions.length
    };
    setFormData({ ...formData, questions: [...formData.questions, newQuestion] });
  };

  const updateQuestion = (index, updates) => {
    const newQuestions = [...formData.questions];
    newQuestions[index] = { ...newQuestions[index], ...updates };
    setFormData({ ...formData, questions: newQuestions });
  };

  const removeQuestion = (index) => {
    const newQuestions = formData.questions.filter((_, i) => i !== index);
    setFormData({ ...formData, questions: newQuestions });
  };

  const addOption = (questionIndex) => {
    const newQuestions = [...formData.questions];
    if (!newQuestions[questionIndex].options) {
      newQuestions[questionIndex].options = [];
    }
    newQuestions[questionIndex].options.push({ value: '', label: '' });
    setFormData({ ...formData, questions: newQuestions });
  };

  const updateOption = (questionIndex, optionIndex, field, value) => {
    const newQuestions = [...formData.questions];
    newQuestions[questionIndex].options[optionIndex][field] = value;
    // Auto-set value from label if empty
    if (field === 'label' && !newQuestions[questionIndex].options[optionIndex].value) {
      newQuestions[questionIndex].options[optionIndex].value = value.toLowerCase().replace(/\s+/g, '_');
    }
    setFormData({ ...formData, questions: newQuestions });
  };

  const removeOption = (questionIndex, optionIndex) => {
    const newQuestions = [...formData.questions];
    newQuestions[questionIndex].options = newQuestions[questionIndex].options.filter((_, i) => i !== optionIndex);
    setFormData({ ...formData, questions: newQuestions });
  };

  const filteredQuestionnaires = selectedTab === 'all' 
    ? questionnaires 
    : questionnaires.filter(q => q.category === selectedTab);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#2F8BFB]"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Questionnaires</h1>
          <p className="text-gray-300">Create custom intake forms for different job types</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setShowTemplateDialog(true)}
            data-testid="use-template-btn"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Use Template
          </Button>
          <Button 
            onClick={() => {
              resetForm();
              setShowCreateDialog(true);
            }}
            className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
            data-testid="create-questionnaire-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create New
          </Button>
        </div>
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="bg-white">
          <TabsTrigger value="all">All ({questionnaires.length})</TabsTrigger>
          <TabsTrigger value="vehicle_wrap">
            <Car className="h-4 w-4 mr-1" /> Vehicle Wrap
          </TabsTrigger>
          <TabsTrigger value="signage">
            <SignpostBig className="h-4 w-4 mr-1" /> Signage
          </TabsTrigger>
          <TabsTrigger value="apparel">
            <Shirt className="h-4 w-4 mr-1" /> Apparel
          </TabsTrigger>
          <TabsTrigger value="general">
            <FileQuestion className="h-4 w-4 mr-1" /> General
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Questionnaires Grid */}
      {filteredQuestionnaires.length === 0 ? (
        <Card className="bg-white border-[#1E293B]">
          <CardContent className="p-12 text-center">
            <FileQuestion className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2 text-slate-900">No questionnaires yet</h3>
            <p className="text-gray-600 mb-4">
              Create your first questionnaire to start collecting customer information
            </p>
            <Button onClick={() => setShowTemplateDialog(true)}>
              <Sparkles className="h-4 w-4 mr-2" /> Start with a Template
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredQuestionnaires.map((questionnaire) => {
            const CategoryIcon = categoryIcons[questionnaire.category] || FileQuestion;
            return (
              <Card 
                key={questionnaire.id}
                className="bg-white border-[#1E293B] hover:border-[#2F8BFB]/50 transition-colors"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${categoryColors[questionnaire.category]?.split(' ')[0] || 'bg-slate-500/20'}`}>
                        <CategoryIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{questionnaire.name}</CardTitle>
                        <p className="text-xs text-gray-500 mt-1">
                          {questionnaire.questions?.length || 0} questions
                        </p>
                      </div>
                    </div>
                    <Badge className={statusColors[questionnaire.status]}>
                      {questionnaire.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  {questionnaire.description && (
                    <p className="text-sm text-gray-500 mb-4 line-clamp-2">
                      {questionnaire.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500 mb-4">
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {questionnaire.response_count || 0} responses
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(questionnaire.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedQuestionnaire(questionnaire);
                        setFormData(questionnaire);
                        setShowEditDialog(true);
                      }}
                      className="flex-1"
                    >
                      <Settings className="h-3 w-3 mr-1" /> Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => viewResponses(questionnaire)}
                    >
                      <BarChart3 className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleStatus(questionnaire)}
                    >
                      {questionnaire.status === 'active' ? (
                        <EyeOff className="h-3 w-3" />
                      ) : (
                        <Eye className="h-3 w-3" />
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => { setSendDialog(questionnaire); setSendEmail(''); }}
                      disabled={questionnaire.status !== 'active'}
                      title="Send via Email"
                    >
                      <Send className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyShareLink(questionnaire)}
                      disabled={questionnaire.status !== 'active'}
                      title="Copy Link"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Template Selection Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Choose a Template</DialogTitle>
            <DialogDescription>
              Start with a pre-built questionnaire template
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {templates.map((template) => {
              const CategoryIcon = categoryIcons[template.category] || FileQuestion;
              return (
                <Card 
                  key={template.id}
                  className="cursor-pointer hover:border-[#2F8BFB] transition-colors"
                  onClick={() => createFromTemplate(template.id)}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    <div className={`p-3 rounded-lg ${categoryColors[template.category]?.split(' ')[0] || 'bg-slate-500/20'}`}>
                      <CategoryIcon className="h-6 w-6" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium">{template.name}</h3>
                      <p className="text-sm text-gray-500">{template.description}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {template.question_count} questions
                      </p>
                    </div>
                    <Badge className={categoryColors[template.category]}>
                      {template.category.replace('_', ' ')}
                    </Badge>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </DialogContent>
      </Dialog>

      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false);
          setShowEditDialog(false);
          setSelectedQuestionnaire(null);
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {showEditDialog ? 'Edit Questionnaire' : 'Create Questionnaire'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Name *</Label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Vehicle Wrap Request Form"
                />
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({ ...formData, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vehicle_wrap">Vehicle Wrap</SelectItem>
                    <SelectItem value="signage">Signage</SelectItem>
                    <SelectItem value="apparel">Apparel</SelectItem>
                    <SelectItem value="print">Print</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of this questionnaire..."
                rows={2}
              />
            </div>

            {/* Questions */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label className="text-base">Questions ({formData.questions.length})</Label>
                <Button size="sm" onClick={addQuestion}>
                  <Plus className="h-4 w-4 mr-1" /> Add Question
                </Button>
              </div>

              {formData.questions.map((question, index) => (
                <Card key={question.id} className="bg-gray-50">
                  <CardContent className="p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <GripVertical className="h-4 w-4 text-gray-500" />
                        <span className="text-sm font-medium">Question {index + 1}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeQuestion(index)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Question Type</Label>
                        <Select
                          value={question.type}
                          onValueChange={(value) => updateQuestion(index, { type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {questionTypes.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="flex items-center gap-4 pt-6">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={question.required}
                            onCheckedChange={(checked) => updateQuestion(index, { required: checked })}
                          />
                          <Label>Required</Label>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Label *</Label>
                      <Input
                        value={question.label}
                        onChange={(e) => updateQuestion(index, { label: e.target.value })}
                        placeholder="Enter the question text..."
                      />
                    </div>

                    {question.type !== 'heading' && question.type !== 'paragraph' && (
                      <div className="space-y-2">
                        <Label>Placeholder</Label>
                        <Input
                          value={question.placeholder || ''}
                          onChange={(e) => updateQuestion(index, { placeholder: e.target.value })}
                          placeholder="Optional placeholder text..."
                        />
                      </div>
                    )}

                    {/* Options for select/radio/checkbox */}
                    {['select', 'multi_select', 'radio', 'checkbox'].includes(question.type) && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label>Options</Label>
                          <Button size="sm" variant="ghost" onClick={() => addOption(index)}>
                            <Plus className="h-3 w-3 mr-1" /> Add Option
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {(question.options || []).map((option, optIndex) => (
                            <div key={optIndex} className="flex gap-2">
                              <Input
                                value={option.label}
                                onChange={(e) => updateOption(index, optIndex, 'label', e.target.value)}
                                placeholder="Option label"
                                className="flex-1"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeOption(index, optIndex)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {formData.questions.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No questions added yet. Click "Add Question" to start building your form.
                </div>
              )}
            </div>

            {/* Thank You Message */}
            <div className="space-y-2">
              <Label>Thank You Message</Label>
              <Textarea
                value={formData.thank_you_message}
                onChange={(e) => setFormData({ ...formData, thank_you_message: e.target.value })}
                placeholder="Message shown after submission..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false);
              setShowEditDialog(false);
            }}>
              Cancel
            </Button>
            <Button 
              onClick={showEditDialog ? updateQuestionnaire : createQuestionnaire}
              className="bg-[#2F8BFB] hover:bg-[#2F8BFB]/90"
            >
              {showEditDialog ? 'Save Changes' : 'Create Questionnaire'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Responses Dialog */}
      <Dialog open={showResponsesDialog} onOpenChange={setShowResponsesDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Responses - {selectedQuestionnaire?.name}</DialogTitle>
            <DialogDescription>
              {responses.length} total responses
            </DialogDescription>
          </DialogHeader>
          
          {responses.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No responses yet for this questionnaire.
            </div>
          ) : (
            <div className="space-y-4 py-4">
              {responses.map((response) => (
                <Card key={response.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="font-medium">
                          {response.customer_name || response.customer_email || 'Anonymous'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(response.submitted_at).toLocaleString()}
                        </p>
                      </div>
                      <Button variant="outline" size="sm">
                        View Details
                      </Button>
                    </div>
                    <div className="text-sm text-gray-500">
                      {Object.keys(response.answers || {}).length} answers provided
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Send via Email Dialog */}
      <Dialog open={!!sendDialog} onOpenChange={() => setSendDialog(null)}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Send Questionnaire</DialogTitle>
            <DialogDescription>{sendDialog?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Recipient Email</Label>
              <Input
                type="email"
                value={sendEmail}
                onChange={(e) => setSendEmail(e.target.value)}
                placeholder="customer@example.com"
                className="mt-1"
                data-testid="send-questionnaire-email-input"
              />
            </div>
            <Button onClick={handleSendEmail} disabled={sending || !sendEmail.trim()} className="w-full" data-testid="send-questionnaire-submit-btn">
              {sending ? <Loader2Icon className="w-4 h-4 animate-spin mr-2" /> : <Send className="w-4 h-4 mr-2" />}
              Send via Email
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
