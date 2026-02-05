import { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import { formatDateTime } from '../lib/utils';
import { 
  Sparkles, Image, Wand2, Type, Layout, Flag, Box, 
  Palette, FileText, PenTool, Share2, Calendar, Target,
  FileEdit, DollarSign, Loader2, Copy, History, Upload,
  Download, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const aiTools = [
  // Design Tools
  {
    id: 'photo_enhancer',
    name: 'Photo Enhancer',
    description: 'Improve low-quality photos for marketing, mockups, or customer artwork while keeping them realistic and print-safe.',
    icon: Image,
    category: 'design',
    fields: [
      { name: 'image_url', label: 'Image URL', type: 'text', placeholder: 'Paste image URL or describe the image' },
      { name: 'enhancement_notes', label: 'Enhancement Notes (Optional)', type: 'textarea', placeholder: 'e.g., increase brightness, remove glare, sharpen edges' },
      { name: 'output_type', label: 'Output Type', type: 'select', options: ['standard_enhanced', 'print_optimized', 'both'] }
    ]
  },
  {
    id: 'image_vectorizer',
    name: 'Image Vectorizer',
    description: 'Convert raster artwork into clean vector files suitable for cutting or printing.',
    icon: Wand2,
    category: 'design',
    fields: [
      { name: 'image_description', label: 'Image Description', type: 'textarea', placeholder: 'Describe the image to vectorize (logo, artwork, etc.)' },
      { name: 'complexity_level', label: 'Complexity Level', type: 'select', options: ['simple', 'balanced', 'detailed'] },
      { name: 'preserve_transparency', label: 'Preserve Transparency', type: 'select', options: ['yes', 'no'] }
    ]
  },
  {
    id: 'font_identifier',
    name: 'Font Identifier',
    description: 'Identify fonts from images and suggest alternatives.',
    icon: Type,
    category: 'design',
    fields: [
      { name: 'image_description', label: 'Image/Text Description', type: 'textarea', placeholder: 'Describe the text and font style you see' },
      { name: 'text_sample', label: 'Sample Text (if readable)', type: 'text', placeholder: 'e.g., "GRAND OPENING"' },
      { name: 'style_hints', label: 'Style Hints', type: 'text', placeholder: 'e.g., serif, modern, hand-drawn, bold' }
    ]
  },
  {
    id: 'ai_sign_designer',
    name: 'AI Sign Designer',
    description: 'Generate sign layout concepts based on customer requirements.',
    icon: Layout,
    category: 'design',
    fields: [
      { name: 'business_type', label: 'Business Type', type: 'text', placeholder: 'e.g., Restaurant, Retail, Law Office' },
      { name: 'sign_type', label: 'Sign Type', type: 'select', options: ['channel_letters', 'monument_sign', 'pylon_sign', 'wall_sign', 'window_graphics', 'awning', 'blade_sign', 'other'] },
      { name: 'size', label: 'Size', type: 'text', placeholder: 'e.g., 4ft x 8ft' },
      { name: 'colors', label: 'Brand Colors', type: 'text', placeholder: 'e.g., Navy Blue #1E3A5F, Gold #D4AF37' },
      { name: 'text_content', label: 'Text Content', type: 'textarea', placeholder: 'Main text, tagline, phone number, etc.' },
      { name: 'style_preference', label: 'Style Preference', type: 'select', options: ['modern', 'classic', 'bold', 'elegant', 'playful', 'industrial'] }
    ]
  },
  {
    id: 'ai_banner_designer',
    name: 'AI Banner Designer',
    description: 'Design banners optimized for promotions and events.',
    icon: Flag,
    category: 'design',
    fields: [
      { name: 'banner_size', label: 'Banner Size', type: 'select', options: ['2x4ft', '3x6ft', '4x8ft', '3x10ft', 'custom'] },
      { name: 'custom_size', label: 'Custom Size (if applicable)', type: 'text', placeholder: 'e.g., 5ft x 12ft' },
      { name: 'message', label: 'Main Message', type: 'textarea', placeholder: 'Headline and supporting text' },
      { name: 'event_type', label: 'Event Type/Purpose', type: 'text', placeholder: 'e.g., Grand Opening, Sale, Sports Event' },
      { name: 'event_date', label: 'Event Date (Optional)', type: 'text', placeholder: 'e.g., March 15, 2026' },
      { name: 'brand_colors', label: 'Brand Colors', type: 'text', placeholder: 'e.g., Red, White' }
    ]
  },
  {
    id: 'mockup_creator',
    name: 'Mockup Creator',
    description: 'Create realistic previews for customer approval.',
    icon: Box,
    category: 'design',
    fields: [
      { name: 'artwork_description', label: 'Artwork Description', type: 'textarea', placeholder: 'Describe the artwork/design to mock up' },
      { name: 'product_type', label: 'Product Type', type: 'select', options: ['storefront', 'vehicle_wrap', 'window_graphics', 'monument_sign', 'interior_sign', 'banner', 'yard_sign', 'apparel', 'other'] },
      { name: 'environment', label: 'Environment/Setting', type: 'text', placeholder: 'e.g., street view, parking lot, office interior' },
      { name: 'angles', label: 'Desired Angles', type: 'select', options: ['front_view', 'angled_view', 'multiple_angles', 'day_and_night'] }
    ]
  },
  // Branding Tools
  {
    id: 'logo_creator',
    name: 'Logo Creator',
    description: 'Generate logo concepts and creative direction.',
    icon: PenTool,
    category: 'branding',
    fields: [
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Company name' },
      { name: 'keywords', label: 'Keywords', type: 'text', placeholder: 'e.g., professional, modern, eco-friendly' },
      { name: 'industry', label: 'Industry', type: 'text', placeholder: 'e.g., Construction, Restaurant, Tech' },
      { name: 'style_preferences', label: 'Style Preferences', type: 'select', options: ['minimalist', 'vintage', 'modern', 'playful', 'corporate', 'artistic'] },
      { name: 'color_preferences', label: 'Color Preferences', type: 'text', placeholder: 'e.g., Blues and greens, warm tones, monochrome' }
    ]
  },
  {
    id: 'branding_kit_generator',
    name: 'Branding Kit Generator',
    description: 'Create a consistent brand system.',
    icon: Palette,
    category: 'branding',
    fields: [
      { name: 'logo_description', label: 'Logo Description (or existing logo)', type: 'textarea', placeholder: 'Describe the logo or paste URL' },
      { name: 'brand_tone', label: 'Brand Tone', type: 'select', options: ['professional', 'friendly', 'luxurious', 'playful', 'trustworthy', 'innovative'] },
      { name: 'target_audience', label: 'Target Audience', type: 'text', placeholder: 'Who is the brand for?' },
      { name: 'usage_context', label: 'Primary Usage', type: 'text', placeholder: 'e.g., signage, print, digital, all' }
    ]
  },
  // Business Tools
  {
    id: 'business_copywriter',
    name: 'Business Copywriter',
    description: 'Generate professional copy on demand.',
    icon: FileText,
    category: 'business',
    fields: [
      { name: 'copy_type', label: 'Copy Type', type: 'select', options: ['tagline', 'about_us', 'product_description', 'email', 'ad_copy', 'social_post', 'website_copy'] },
      { name: 'business_info', label: 'Business Info', type: 'textarea', placeholder: 'What does the business do? Key services?' },
      { name: 'tone', label: 'Tone', type: 'select', options: ['professional', 'casual', 'urgent', 'friendly', 'authoritative', 'playful'] },
      { name: 'length', label: 'Length Preference', type: 'select', options: ['short', 'medium', 'long'] },
      { name: 'key_points', label: 'Key Points to Include', type: 'textarea', placeholder: 'What must be mentioned?' }
    ]
  },
  {
    id: 'document_composer',
    name: 'Document Composer',
    description: 'Generate business documents using live data.',
    icon: FileEdit,
    category: 'business',
    fields: [
      { name: 'document_type', label: 'Document Type', type: 'select', options: ['proposal', 'scope_of_work', 'installation_notes', 'project_brief', 'thank_you_letter', 'warranty_info', 'maintenance_guide'] },
      { name: 'client_name', label: 'Client Name', type: 'text', placeholder: 'Client or company name' },
      { name: 'project_details', label: 'Project Details', type: 'textarea', placeholder: 'Describe the project, deliverables, timeline' },
      { name: 'tone', label: 'Document Tone', type: 'select', options: ['formal', 'semi_formal', 'friendly'] },
      { name: 'special_terms', label: 'Special Terms/Notes', type: 'textarea', placeholder: 'Any special conditions or requirements' }
    ]
  },
  {
    id: 'pricing_intelligence',
    name: 'Pricing Intelligence Assistant',
    description: 'Analyze pricing and profit margins.',
    icon: DollarSign,
    category: 'business',
    fields: [
      { name: 'service_type', label: 'Service/Product Type', type: 'text', placeholder: 'e.g., Vehicle Wrap, Channel Letters, Banner' },
      { name: 'specifications', label: 'Specifications', type: 'textarea', placeholder: 'Size, materials, complexity, installation requirements' },
      { name: 'material_cost', label: 'Material Cost', type: 'text', placeholder: 'e.g., $500' },
      { name: 'labor_hours', label: 'Estimated Labor Hours', type: 'text', placeholder: 'e.g., 8 hours' },
      { name: 'current_price', label: 'Current/Proposed Price', type: 'text', placeholder: 'e.g., $1,500' },
      { name: 'market_context', label: 'Market Context', type: 'text', placeholder: 'e.g., urban area, competitive market' }
    ]
  },
  // Marketing Tools
  {
    id: 'social_job_post',
    name: 'Social Media Job Post Creator',
    description: 'Create social posts from completed jobs.',
    icon: Share2,
    category: 'marketing',
    fields: [
      { name: 'job_description', label: 'Job Description', type: 'textarea', placeholder: 'What was the project? Vehicle wrap, storefront, etc.' },
      { name: 'job_type', label: 'Job Type', type: 'select', options: ['vehicle_wrap', 'storefront', 'monument_sign', 'interior', 'banner', 'window_graphics', 'fleet', 'other'] },
      { name: 'client_type', label: 'Client Type (no names)', type: 'text', placeholder: 'e.g., local restaurant, construction company' },
      { name: 'tone', label: 'Post Tone', type: 'select', options: ['professional', 'excited', 'casual', 'storytelling'] },
      { name: 'platforms', label: 'Target Platforms', type: 'select', options: ['facebook', 'instagram', 'linkedin', 'all_platforms'] }
    ]
  },
  {
    id: 'social_pack_generator',
    name: 'Social Media Pack Generator',
    description: 'Generate batches of content for social media.',
    icon: Share2,
    category: 'marketing',
    fields: [
      { name: 'services_offered', label: 'Services Offered', type: 'textarea', placeholder: 'List your main services: wraps, signs, banners, etc.' },
      { name: 'posting_frequency', label: 'Posting Frequency', type: 'select', options: ['daily', '3x_per_week', '2x_per_week', 'weekly'] },
      { name: 'pack_size', label: 'Number of Posts', type: 'select', options: ['5_posts', '10_posts', '15_posts', '30_posts'] },
      { name: 'target_audience', label: 'Target Audience', type: 'text', placeholder: 'Local businesses, contractors, restaurants, etc.' },
      { name: 'content_mix', label: 'Content Mix', type: 'select', options: ['promotional', 'educational', 'behind_the_scenes', 'mixed'] }
    ]
  },
  {
    id: 'content_calendar',
    name: 'Content Calendar Creator',
    description: 'Plan consistent posting schedule.',
    icon: Calendar,
    category: 'marketing',
    fields: [
      { name: 'date_range', label: 'Time Period', type: 'select', options: ['1_week', '2_weeks', '1_month', '3_months'] },
      { name: 'platforms', label: 'Platforms', type: 'text', placeholder: 'e.g., Facebook, Instagram, LinkedIn' },
      { name: 'goals', label: 'Marketing Goals', type: 'textarea', placeholder: 'What do you want to achieve? More leads, brand awareness, etc.' },
      { name: 'upcoming_events', label: 'Upcoming Events/Promotions', type: 'textarea', placeholder: 'Any sales, holidays, or events to plan around?' },
      { name: 'posting_days', label: 'Preferred Posting Days', type: 'text', placeholder: 'e.g., Mon, Wed, Fri' }
    ]
  },
  {
    id: 'campaign_builder',
    name: 'Campaign Builder',
    description: 'Design full marketing campaigns.',
    icon: Target,
    category: 'marketing',
    fields: [
      { name: 'campaign_type', label: 'Campaign Type', type: 'select', options: ['grand_opening', 'seasonal_sale', 'new_service_launch', 'referral_program', 'local_event', 'brand_awareness'] },
      { name: 'campaign_goal', label: 'Primary Goal', type: 'text', placeholder: 'e.g., Generate 20 new leads, Increase sales by 15%' },
      { name: 'target_audience', label: 'Target Audience', type: 'textarea', placeholder: 'Who are you trying to reach?' },
      { name: 'budget_range', label: 'Budget Range', type: 'select', options: ['under_500', '500_to_1000', '1000_to_2500', '2500_to_5000', 'over_5000'] },
      { name: 'duration', label: 'Campaign Duration', type: 'select', options: ['1_week', '2_weeks', '1_month', '3_months'] },
      { name: 'channels', label: 'Marketing Channels', type: 'text', placeholder: 'e.g., Social media, Email, Local ads, Signage' }
    ]
  }
];

const categories = [
  { id: 'design', name: 'Design Tools', icon: Image, color: 'text-blue-400' },
  { id: 'branding', name: 'Branding', icon: Palette, color: 'text-purple-400' },
  { id: 'business', name: 'Business', icon: FileText, color: 'text-green-400' },
  { id: 'marketing', name: 'Marketing', icon: Share2, color: 'text-pink-400' }
];

export default function AITools() {
  const { generateAIContent, fetchAIHistory } = useApp();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState(aiTools[0]);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const filteredTools = selectedCategory === 'all' 
    ? aiTools 
    : aiTools.filter(t => t.category === selectedCategory);

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
  const categoryInfo = categories.find(c => c.id === selectedTool.category);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="ai-tools-page">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold font-heading uppercase tracking-tight">AI Tools Suite</h1>
        <p className="text-muted-foreground mt-1">15 AI-powered tools for design, branding, business, and marketing</p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedCategory === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedCategory('all')}
        >
          All Tools ({aiTools.length})
        </Button>
        {categories.map(cat => {
          const CatIcon = cat.icon;
          const count = aiTools.filter(t => t.category === cat.id).length;
          return (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(cat.id)}
            >
              <CatIcon className={`h-4 w-4 mr-1 ${selectedCategory === cat.id ? '' : cat.color}`} />
              {cat.name} ({count})
            </Button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tool Selector */}
        <Card className="bg-card border-border/50 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading uppercase text-sm">Select Tool</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              <div className="space-y-1 p-3">
                {filteredTools.map((tool) => {
                  const ToolIcon = tool.icon;
                  const toolCat = categories.find(c => c.id === tool.category);
                  return (
                    <button
                      key={tool.id}
                      onClick={() => handleToolSelect(tool.id)}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                        selectedTool.id === tool.id 
                          ? 'bg-primary/10 border border-primary/30' 
                          : 'hover:bg-muted/50'
                      }`}
                      data-testid={`tool-${tool.id}`}
                    >
                      <ToolIcon className={`h-5 w-5 flex-shrink-0 ${selectedTool.id === tool.id ? 'text-primary' : toolCat?.color || 'text-muted-foreground'}`} />
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium block truncate ${selectedTool.id === tool.id ? 'text-primary' : ''}`}>
                          {tool.name}
                        </span>
                        <span className="text-xs text-muted-foreground capitalize">{tool.category}</span>
                      </div>
                      {selectedTool.id === tool.id && <ChevronRight className="h-4 w-4 text-primary" />}
                    </button>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Tool Interface */}
        <div className="lg:col-span-3 space-y-6">
          {/* Tool Header */}
          <Card className="bg-card border-border/50">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg ${categoryInfo?.color?.replace('text-', 'bg-').replace('-400', '-500/20')}`}>
                  <Icon className={`h-8 w-8 ${categoryInfo?.color || 'text-primary'}`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-2xl font-bold font-heading uppercase">{selectedTool.name}</h2>
                    <Badge variant="outline" className="capitalize">{selectedTool.category}</Badge>
                  </div>
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
                            {opt.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
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
                  <div className="flex gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => copyToClipboard(result.output)}
                      data-testid="copy-result-btn"
                    >
                      <Copy className="h-4 w-4 mr-2" /> Copy
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4 mr-2" /> Export
                    </Button>
                  </div>
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

          {/* History Panel */}
          {showHistory && (
            <Card className="bg-card border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm">History for {selectedTool.name}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={() => setShowHistory(false)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No history found for this tool</p>
                ) : (
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div 
                          key={item.id} 
                          className="p-3 bg-muted/30 rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
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
