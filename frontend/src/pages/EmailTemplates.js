import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Separator } from '../components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Mail, Edit2, Eye, RotateCcw, Save, FileText, 
  Bell, UserPlus, Send, Info, Code, CheckCircle2
} from 'lucide-react';
import { toast } from 'sonner';

const TEMPLATE_ICONS = {
  portal_notification: Bell,
  portal_welcome: UserPlus,
  document_delivery: FileText
};

export default function EmailTemplates() {
  const { api } = useApp();
  
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');
  const [previewSubject, setPreviewSubject] = useState('');
  const [saving, setSaving] = useState(false);
  
  // Edit form
  const [editSubject, setEditSubject] = useState('');
  const [editHtml, setEditHtml] = useState('');

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await api.get('/email-templates');
      setTemplates(res.data);
    } catch (err) {
      toast.error('Failed to load email templates');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleEdit = (template) => {
    setSelectedTemplate(template);
    setEditSubject(template.subject);
    setEditHtml(template.html_content);
    setIsEditOpen(true);
  };

  const handlePreview = async (template) => {
    try {
      const res = await api.post(`/email-templates/${template.id}/preview`);
      setPreviewSubject(res.data.subject);
      setPreviewHtml(res.data.html_content);
      setIsPreviewOpen(true);
    } catch (err) {
      toast.error('Failed to generate preview');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/email-templates/${selectedTemplate.id}`, {
        subject: editSubject,
        html_content: editHtml
      });
      toast.success('Template saved successfully');
      setIsEditOpen(false);
      await loadTemplates();
    } catch (err) {
      toast.error('Failed to save template');
    }
    setSaving(false);
  };

  const handleReset = async (templateId) => {
    if (!confirm('Are you sure you want to reset this template to default? Your customizations will be lost.')) {
      return;
    }
    
    try {
      await api.post(`/email-templates/${templateId}/reset`);
      toast.success('Template reset to default');
      await loadTemplates();
    } catch (err) {
      toast.error('Failed to reset template');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="email-templates-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight" style={{ color: 'var(--text)' }}>
          Email Templates
        </h1>
        <p className="text-muted-foreground mt-1">
          Customize the emails sent to your customers
        </p>
      </div>

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-primary mt-0.5" />
            <div>
              <p className="text-sm">
                <strong>Template Variables:</strong> Use <code className="bg-muted px-1 rounded">{'{{variable_name}}'}</code> to insert dynamic content. 
                Variables are automatically replaced when emails are sent.
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Example: <code className="bg-muted px-1 rounded">{'{{customer_name}}'}</code> will be replaced with the actual customer&apos;s name.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Templates List */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid gap-4">
          {templates.map(template => {
            const Icon = TEMPLATE_ICONS[template.id] || Mail;
            return (
              <Card key={template.id} className="bg-card border-border/50">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Icon className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-lg">{template.name}</h3>
                          {template.is_customized && (
                            <Badge variant="outline" className="text-primary border-primary">
                              <CheckCircle2 className="h-3 w-3 mr-1" /> Customized
                            </Badge>
                          )}
                        </div>
                        <p className="text-muted-foreground text-sm mt-1">{template.description}</p>
                        <div className="mt-3">
                          <p className="text-xs text-muted-foreground">Subject Line:</p>
                          <p className="text-sm font-mono bg-muted/50 px-2 py-1 rounded mt-1">
                            {template.subject}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePreview(template)}
                      >
                        <Eye className="h-4 w-4 mr-1" /> Preview
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(template)}
                      >
                        <Edit2 className="h-4 w-4 mr-1" /> Edit
                      </Button>
                      {template.is_customized && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleReset(template.id)}
                          className="text-muted-foreground"
                        >
                          <RotateCcw className="h-4 w-4 mr-1" /> Reset
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* Variables */}
                  <div className="mt-4 pt-4 border-t border-border/50">
                    <p className="text-xs text-muted-foreground mb-2">Available Variables:</p>
                    <div className="flex flex-wrap gap-2">
                      {template.variables?.map(v => (
                        <Badge key={v.name} variant="secondary" className="font-mono text-xs">
                          {`{{${v.name}}}`}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">
              Edit Template: {selectedTemplate?.name}
            </DialogTitle>
          </DialogHeader>
          
          {selectedTemplate && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Subject Line</Label>
                <Input
                  value={editSubject}
                  onChange={(e) => setEditSubject(e.target.value)}
                  placeholder="Email subject..."
                />
                <p className="text-xs text-muted-foreground">
                  You can use variables like {'{{customer_name}}'} in the subject
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Email HTML Content</Label>
                <Textarea
                  value={editHtml}
                  onChange={(e) => setEditHtml(e.target.value)}
                  placeholder="HTML content..."
                  className="font-mono text-sm min-h-[400px]"
                />
                <p className="text-xs text-muted-foreground">
                  Edit the HTML template. Use {'{{variable}}'} for dynamic content and {'{{#if variable}}...{{/if}}'} for conditional blocks.
                </p>
              </div>
              
              <div className="p-3 rounded-lg bg-muted/50">
                <p className="text-sm font-medium mb-2">Available Variables:</p>
                <div className="flex flex-wrap gap-2">
                  {selectedTemplate.variables?.map(v => (
                    <div key={v.name} className="text-xs">
                      <code className="bg-primary/10 px-2 py-1 rounded text-primary">
                        {`{{${v.name}}}`}
                      </code>
                      <span className="text-muted-foreground ml-1">- {v.description}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <Separator />
              
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsEditOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving...' : <><Save className="h-4 w-4 mr-2" /> Save Template</>}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh]">
          <DialogHeader>
            <DialogTitle className="font-heading uppercase">Email Preview</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label className="text-xs text-muted-foreground">Subject:</Label>
              <p className="font-medium">{previewSubject}</p>
            </div>
            
            <Separator />
            
            <div className="border rounded-lg overflow-hidden bg-white">
              <iframe
                srcDoc={previewHtml}
                className="w-full h-[500px] border-0"
                title="Email Preview"
              />
            </div>
            
            <div className="flex justify-end">
              <Button onClick={() => setIsPreviewOpen(false)}>Close</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
