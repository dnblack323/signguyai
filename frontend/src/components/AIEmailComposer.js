import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Sparkles, Mail, Loader2, Copy, Check, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const emailTypes = {
  invoice_send: {
    label: 'Send Invoice',
    description: 'Professional email to send an invoice to a customer',
  },
  invoice_reminder: {
    label: 'Payment Reminder',
    description: 'Polite reminder about an outstanding invoice',
  },
  invoice_overdue: {
    label: 'Overdue Notice',
    description: 'Firm but professional notice about an overdue payment',
  },
  quote_send: {
    label: 'Send Quote',
    description: 'Professional email to send a quote to a potential customer',
  },
  quote_followup: {
    label: 'Quote Follow-Up',
    description: 'Follow-up email about a quote that hasn\'t been responded to',
  },
  approval_request: {
    label: 'Approval Request',
    description: 'Request customer approval for artwork or design proof',
  },
  job_update: {
    label: 'Job Status Update',
    description: 'Update customer on their job progress',
  },
  job_complete: {
    label: 'Job Complete',
    description: 'Notify customer their job is ready for pickup or installation',
  },
  thank_you: {
    label: 'Thank You',
    description: 'Thank customer for their business after completing a job',
  },
};

const toneOptions = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'formal', label: 'Formal' },
  { value: 'urgent', label: 'Urgent' },
];

export default function AIEmailComposer({ 
  isOpen, 
  onClose, 
  emailType = 'invoice_send',
  context = {},
  onSend 
}) {
  const [loading, setLoading] = useState(false);
  const [generatedSubject, setGeneratedSubject] = useState('');
  const [generatedBody, setGeneratedBody] = useState('');
  const [selectedType, setSelectedType] = useState(emailType);
  const [selectedTone, setSelectedTone] = useState('professional');
  const [additionalContext, setAdditionalContext] = useState('');
  const [copied, setCopied] = useState(false);

  const generateEmail = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.post(
        `${API_URL}/api/ai/generate-email`,
        {
          email_type: selectedType,
          tone: selectedTone,
          context: {
            ...context,
            additional_notes: additionalContext,
          },
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      setGeneratedSubject(response.data.subject);
      setGeneratedBody(response.data.body);
      toast.success('Email draft generated!');
    } catch (error) {
      console.error('Error generating email:', error);
      toast.error('Failed to generate email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    const fullEmail = `Subject: ${generatedSubject}\n\n${generatedBody}`;
    navigator.clipboard.writeText(fullEmail);
    setCopied(true);
    toast.success('Email copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSendEmail = () => {
    if (!context.customer_email) {
      toast.error('Customer email not found');
      return;
    }

    const subject = encodeURIComponent(generatedSubject);
    const body = encodeURIComponent(generatedBody);
    window.open(`mailto:${context.customer_email}?subject=${subject}&body=${body}`, '_blank');
    
    if (onSend) {
      onSend({ subject: generatedSubject, body: generatedBody });
    }
    onClose();
  };

  const handleUseTemplate = () => {
    // Open email client with generated content
    handleSendEmail();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Email Composer
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Email Type Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Email Type</Label>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(emailTypes).map(([key, { label }]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500 mt-1">
                {emailTypes[selectedType]?.description}
              </p>
            </div>
            <div>
              <Label>Tone</Label>
              <Select value={selectedTone} onValueChange={setSelectedTone}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {toneOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Context Display */}
          {context.customer_name && (
            <div className="p-3 bg-gray-50 rounded-lg text-sm">
              <div className="flex flex-wrap gap-2">
                {context.customer_name && (
                  <Badge variant="secondary">To: {context.customer_name}</Badge>
                )}
                {context.invoice_number && (
                  <Badge variant="secondary">Invoice #{context.invoice_number}</Badge>
                )}
                {context.quote_number && (
                  <Badge variant="secondary">Quote #{context.quote_number}</Badge>
                )}
                {context.job_name && (
                  <Badge variant="secondary">Job: {context.job_name}</Badge>
                )}
                {context.amount && (
                  <Badge variant="secondary">${context.amount}</Badge>
                )}
              </div>
            </div>
          )}

          {/* Additional Context */}
          <div>
            <Label>Additional Notes (optional)</Label>
            <Textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Add any specific details you want included in the email..."
              className="mt-1"
              rows={2}
            />
          </div>

          {/* Generate Button */}
          <Button 
            onClick={generateEmail} 
            disabled={loading}
            className="w-full bg-purple-500 hover:bg-purple-600"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Email Draft
              </>
            )}
          </Button>

          {/* Generated Email Preview */}
          {generatedSubject && (
            <div className="space-y-3 border rounded-lg p-4 bg-white">
              <div className="flex items-center justify-between">
                <Label className="text-purple-600">Generated Email</Label>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={generateEmail}
                    disabled={loading}
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Regenerate
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopy}
                  >
                    {copied ? (
                      <Check className="h-4 w-4 mr-1 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4 mr-1" />
                    )}
                    Copy
                  </Button>
                </div>
              </div>

              <div>
                <Label className="text-xs text-gray-500">Subject</Label>
                <div className="p-2 bg-gray-50 rounded border text-sm font-medium">
                  {generatedSubject}
                </div>
              </div>

              <div>
                <Label className="text-xs text-gray-500">Body</Label>
                <Textarea
                  value={generatedBody}
                  onChange={(e) => setGeneratedBody(e.target.value)}
                  className="min-h-[200px] text-sm"
                  rows={10}
                />
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          {generatedSubject && (
            <Button onClick={handleUseTemplate} className="bg-blue-500 hover:bg-blue-600">
              <Mail className="h-4 w-4 mr-2" />
              Open in Email Client
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
