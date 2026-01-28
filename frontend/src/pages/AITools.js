import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { formatDateTime } from '../lib/utils';
import { 
  Sparkles, Layout, CheckSquare, Palette, FileText, 
  AlertCircle, MessageSquare, Loader2, Copy, History
} from 'lucide-react';
import { toast } from 'sonner';

const aiTools = [
  {
    id: 'layout_generator',
    name: 'Layout Generator',
    description: 'Create multiple layout concepts for signs',
    icon: Layout,
    category: 'design',
    fields: [
      { name: 'product_type', label: 'Product Type', type: 'text', placeholder: 'e.g., Banner, Window Sign, Vehicle Wrap' },
      { name: 'size', label: 'Size', type: 'text', placeholder: 'e.g., 4ft x 8ft' },
      { name: 'text_content', label: 'Text Content', type: 'textarea', placeholder: 'Main text and secondary text' },
      { name: 'colors', label: 'Colors', type: 'text', placeholder: 'e.g., Blue, White, Gold' },
      { name: 'style', label: 'Style Preference', type: 'text', placeholder: 'e.g., Modern, Classic, Bold' }
    ]
  },
  {
    id: 'print_checklist',
    name: 'Print-Ready Checklist',
    description: 'Check designs for print production issues',
    icon: CheckSquare,
    category: 'design',
    fields: [
      { name: 'design_description', label: 'Design Description', type: 'textarea', placeholder: 'Describe the design, dimensions, colors, and any concerns' },
      { name: 'print_method', label: 'Print Method', type: 'text', placeholder: 'e.g., Digital, Screen Print, Large Format' },
      { name: 'material', label: 'Material', type: 'text', placeholder: 'e.g., Vinyl, Acrylic, Coroplast' }
    ]
  },
  {
    id: 'brand_kit',
    name: 'Brand Kit Generator',
    description: 'Create color palettes, font pairings, and taglines',
    icon: Palette,
    category: 'branding',
    fields: [
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Client\'s business name' },
      { name: 'industry', label: 'Industry', type: 'text', placeholder: 'e.g., Restaurant, Retail, Construction' },
      { name: 'target_audience', label: 'Target Audience', type: 'text', placeholder: 'Who are their customers?' },
      { name: 'brand_values', label: 'Brand Values/Personality', type: 'textarea', placeholder: 'e.g., Professional, Fun, Eco-friendly, Premium' },
      { name: 'existing_colors', label: 'Existing Colors (if any)', type: 'text', placeholder: 'Any colors they already use' }
    ]
  },
  {
    id: 'document_creator',
    name: 'Document Creator',
    description: 'Generate proposals, scope documents, and install notes',
    icon: FileText,
    category: 'business',
    fields: [
      { name: 'document_type', label: 'Document Type', type: 'select', options: ['proposal', 'scope_of_work', 'installation_notes', 'project_brief'] },
      { name: 'project_name', label: 'Project Name', type: 'text', placeholder: 'Name of the project' },
      { name: 'client_name', label: 'Client Name', type: 'text', placeholder: 'Client\'s name or company' },
      { name: 'project_details', label: 'Project Details', type: 'textarea', placeholder: 'Describe the project, deliverables, timeline, etc.' },
      { name: 'special_requirements', label: 'Special Requirements', type: 'textarea', placeholder: 'Any special terms, conditions, or notes' }
    ]
  },
  {
    id: 'overdue_assistant',
    name: 'Overdue Payment Assistant',
    description: 'Draft reminder messages for overdue invoices',
    icon: AlertCircle,
    category: 'business',
    fields: [
      { name: 'client_name', label: 'Client Name', type: 'text', placeholder: 'Client\'s name' },
      { name: 'invoice_amount', label: 'Invoice Amount', type: 'text', placeholder: 'e.g., $1,500.00' },
      { name: 'days_overdue', label: 'Days Overdue', type: 'text', placeholder: 'e.g., 15' },
      { name: 'invoice_details', label: 'Invoice Details', type: 'textarea', placeholder: 'What was the invoice for?' },
      { name: 'previous_attempts', label: 'Previous Contact Attempts', type: 'textarea', placeholder: 'Have you already reached out?' }
    ]
  },
  {
    id: 'design_intake',
    name: 'Design Intake Chat',
    description: 'Extract project requirements from customer conversations',
    icon: MessageSquare,
    category: 'customer',
    fields: [
      { name: 'conversation', label: 'Customer Conversation', type: 'textarea', placeholder: 'Paste or describe the conversation with the customer about their sign needs' },
      { name: 'additional_context', label: 'Additional Context', type: 'textarea', placeholder: 'Any other relevant information' }
    ]
  }
];

export default function AITools() {
  const { generateAIContent, fetchAIHistory } = useApp();
  const [selectedTool, setSelectedTool] = useState(aiTools[0]);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const handleToolSelect = (toolId) => {
    const tool = aiTools.find(t => t.id === toolId);
    setSelectedTool(tool);
    setFormData({});
    setResult(null);
  };

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleGenerate = async () => {
    // Validate required fields have some content
    const hasContent = Object.values(formData).some(v => v && v.trim());
    if (!hasContent) {
      toast.error('Please fill in at least one field');
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await generateAIContent(selectedTool.id, formData);
      setResult(response);
      toast.success('Generated successfully!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate content');
    }
    setLoading(false);
  };

  const loadHistory = async () => {
    try {
      const data = await fetchAIHistory({ tool: selectedTool.id });
      setHistory(data);
      setShowHistory(true);
    } catch (err) {
      toast.error('Failed to load history');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const Icon = selectedTool.icon;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="ai-tools-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">AI Tools</h1>
        <p className="text-muted-foreground mt-1">AI-powered assistants for sign shop workflows</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tool Selector */}
        <Card className="bg-card border-border/50 lg:col-span-1">
          <CardHeader>
            <CardTitle className="font-heading uppercase text-sm">Select Tool</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="space-y-1 p-3">
              {aiTools.map((tool) => {
                const ToolIcon = tool.icon;
                return (
                  <button
                    key={tool.id}
                    onClick={() => handleToolSelect(tool.id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                      selectedTool.id === tool.id 
                        ? 'bg-primary/10 border border-primary/30 text-primary' 
                        : 'hover:bg-muted/50 text-muted-foreground'
                    }`}
                    data-testid={`tool-${tool.id}`}
                  >
                    <ToolIcon className="h-5 w-5 flex-shrink-0" />
                    <span className="text-sm font-medium">{tool.name}</span>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Tool Interface */}
        <div className="lg:col-span-3 space-y-6">
          {/* Tool Header */}
          <Card className="bg-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-primary/10">
                  <Icon className="h-8 w-8 text-primary" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold font-heading uppercase">{selectedTool.name}</h2>
                  <p className="text-muted-foreground mt-1">{selectedTool.description}</p>
                </div>
                <Button variant="outline" size="sm" onClick={loadHistory} data-testid="view-history-btn">
                  <History className="h-4 w-4 mr-2" /> History
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Input Form */}
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle className="font-heading uppercase text-sm">Input</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedTool.fields.map((field) => (
                <div key={field.name} className="space-y-2">
                  <Label>{field.label}</Label>
                  {field.type === 'text' && (
                    <Input
                      value={formData[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      placeholder={field.placeholder}
                      data-testid={`input-${field.name}`}
                    />
                  )}
                  {field.type === 'textarea' && (
                    <Textarea
                      value={formData[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      placeholder={field.placeholder}
                      rows={4}
                      data-testid={`input-${field.name}`}
                    />
                  )}
                  {field.type === 'select' && (
                    <Select
                      value={formData[field.name] || ''}
                      onValueChange={(val) => handleFieldChange(field.name, val)}
                    >
                      <SelectTrigger data-testid={`input-${field.name}`}>
                        <SelectValue placeholder="Select option" />
                      </SelectTrigger>
                      <SelectContent>
                        {field.options.map((opt) => (
                          <SelectItem key={opt} value={opt}>
                            {opt.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              ))}
              <Button 
                onClick={handleGenerate} 
                disabled={loading}
                className="w-full neon-glow"
                data-testid="generate-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" /> Generate
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Result */}
          {result && (
            <Card className="bg-card border-border/50 border-primary/30">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm text-primary">Result</CardTitle>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => copyToClipboard(result.output)}
                    data-testid="copy-result-btn"
                  >
                    <Copy className="h-4 w-4 mr-2" /> Copy
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="prose prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-sm font-sans bg-muted/30 p-4 rounded-lg">
                      {result.output}
                    </pre>
                  </div>
                </ScrollArea>
                <p className="text-xs text-muted-foreground mt-4">
                  Generated at {formatDateTime(result.created_at)}
                </p>
              </CardContent>
            </Card>
          )}

          {/* History Modal */}
          {showHistory && (
            <Card className="bg-card border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm">History</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setShowHistory(false)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No history found</p>
                ) : (
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div 
                          key={item.id} 
                          className="p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50"
                          onClick={() => {
                            setResult(item);
                            setShowHistory(false);
                          }}
                        >
                          <p className="text-sm font-medium truncate">
                            {JSON.stringify(item.input_data).slice(0, 100)}...
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {formatDateTime(item.created_at)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
