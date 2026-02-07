import { useState, useRef } from 'react';
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
  Download, ChevronRight, Check, RefreshCw, ImageIcon
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
    generatesImages: false,
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
    generatesImages: false,
    fields: [
      { name: 'image_description', label: 'Image Description', type: 'textarea', placeholder: 'Describe the image to vectorize (logo, artwork, etc.)' },
      { name: 'complexity_level', label: 'Complexity Level', type: 'select', options: ['simple', 'balanced', 'detailed'] },
      { name: 'preserve_transparency', label: 'Preserve Transparency', type: 'select', options: ['yes', 'no'] }
    ]
  },
  {
    id: 'font_identifier',
    name: 'Font Identifier',
    description: 'Upload an image to identify fonts and get similar alternatives.',
    icon: Type,
    category: 'design',
    generatesImages: false,
    fields: [
      { name: 'image_upload', label: 'Upload Image with Text', type: 'image_upload', placeholder: 'Upload an image containing the font' },
      { name: 'text_sample', label: 'Text in Image (if readable)', type: 'text', placeholder: 'e.g., "GRAND OPENING" - helps with identification' },
      { name: 'usage_intent', label: 'What will you use this font for?', type: 'select', options: ['signage', 'vehicle_graphics', 'banners', 'apparel', 'business_cards', 'other'] }
    ]
  },
  {
    id: 'ai_sign_designer',
    name: 'AI Sign Designer',
    description: 'Generate sign layout concepts based on customer requirements.',
    icon: Layout,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Name to display on sign' },
      { name: 'business_type', label: 'Business Type', type: 'text', placeholder: 'e.g., Restaurant, Retail, Law Office' },
      { name: 'sign_type', label: 'Sign Type', type: 'select', options: ['channel_letters', 'monument_sign', 'pylon_sign', 'wall_sign', 'window_graphics', 'awning', 'blade_sign', 'lightbox', 'other'] },
      { name: 'size', label: 'Size', type: 'text', placeholder: 'e.g., 4ft x 8ft' },
      { name: 'colors', label: 'Brand Colors', type: 'text', placeholder: 'e.g., Navy Blue, Gold' },
      { name: 'additional_text', label: 'Additional Text (tagline, phone, etc.)', type: 'textarea', placeholder: 'Any other text to include' },
      { name: 'style_preference', label: 'Style Preference', type: 'select', options: ['modern', 'classic', 'bold', 'elegant', 'playful', 'industrial', 'rustic'] }
    ]
  },
  {
    id: 'ai_banner_designer',
    name: 'AI Banner Designer',
    description: 'Generate banner designs optimized for promotions and events.',
    icon: Flag,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'banner_size', label: 'Banner Size', type: 'select', options: ['2x4ft', '3x6ft', '4x8ft', '3x10ft', '4x12ft', 'retractable_33x80', 'custom'] },
      { name: 'custom_size', label: 'Custom Size (if applicable)', type: 'text', placeholder: 'e.g., 5ft x 12ft' },
      { name: 'headline', label: 'Main Headline', type: 'text', placeholder: 'e.g., GRAND OPENING!' },
      { name: 'subtext', label: 'Supporting Text', type: 'textarea', placeholder: 'Date, location, offer details, call to action' },
      { name: 'event_type', label: 'Event Type/Purpose', type: 'select', options: ['grand_opening', 'sale_promotion', 'event_announcement', 'sports_team', 'birthday_celebration', 'business_promotion', 'political', 'real_estate', 'other'] },
      { name: 'brand_colors', label: 'Brand Colors', type: 'text', placeholder: 'e.g., Red, White, Blue' },
      { name: 'include_logo', label: 'Include Logo Placeholder?', type: 'select', options: ['yes', 'no'] },
      { name: 'style', label: 'Design Style', type: 'select', options: ['bold_modern', 'elegant', 'fun_colorful', 'professional', 'vintage_retro', 'minimalist'] }
    ]
  },
  {
    id: 'mockup_creator',
    name: 'Mockup Creator',
    description: 'Generate realistic mockup previews for customer approval.',
    icon: Box,
    category: 'design',
    generatesImages: true,
    imageCount: 2,
    fields: [
      { name: 'design_description', label: 'Describe Your Design', type: 'textarea', placeholder: 'Describe the sign/graphic design to show in mockup' },
      { name: 'product_type', label: 'Product Type', type: 'select', options: ['storefront_sign', 'vehicle_wrap', 'window_graphics', 'monument_sign', 'wall_sign', 'banner_outdoor', 'yard_sign', 'tshirt', 'trade_show_booth', 'other'] },
      { name: 'environment', label: 'Environment/Setting', type: 'select', options: ['urban_street', 'suburban_plaza', 'parking_lot', 'highway_visible', 'indoor_office', 'trade_show', 'residential', 'custom'] },
      { name: 'custom_environment', label: 'Custom Environment (if applicable)', type: 'text', placeholder: 'Describe the setting' },
      { name: 'time_of_day', label: 'Time of Day', type: 'select', options: ['daytime', 'evening_lit', 'night_illuminated', 'both_day_night'] }
    ]
  },
  // Branding Tools
  {
    id: 'logo_creator',
    name: 'Logo Creator',
    description: 'Generate logo design concepts with multiple options to choose from.',
    icon: PenTool,
    category: 'branding',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Name to appear in/with logo' },
      { name: 'tagline', label: 'Tagline (Optional)', type: 'text', placeholder: 'e.g., "Quality Signs Since 1995"' },
      { name: 'industry', label: 'Industry', type: 'select', options: ['construction', 'restaurant_food', 'retail', 'automotive', 'healthcare', 'legal_financial', 'technology', 'real_estate', 'fitness_sports', 'beauty_salon', 'education', 'nonprofit', 'other'] },
      { name: 'logo_type', label: 'Logo Type Preference', type: 'select', options: ['wordmark_text_only', 'lettermark_initials', 'icon_with_text', 'icon_only', 'emblem_badge', 'no_preference'] },
      { name: 'style_preferences', label: 'Style', type: 'select', options: ['minimalist_clean', 'vintage_classic', 'modern_bold', 'playful_fun', 'corporate_professional', 'artistic_creative', 'luxurious_elegant'] },
      { name: 'color_preferences', label: 'Color Preferences', type: 'text', placeholder: 'e.g., Blues and greens, warm tones, black and gold' },
      { name: 'icon_ideas', label: 'Icon/Symbol Ideas (Optional)', type: 'text', placeholder: 'e.g., mountain, wrench, leaf, abstract shapes' }
    ]
  },
  {
    id: 'branding_kit_generator',
    name: 'Branding Kit Generator',
    description: 'Create a consistent brand system with colors, fonts, and guidelines.',
    icon: Palette,
    category: 'branding',
    generatesImages: false,
    fields: [
      { name: 'logo_description', label: 'Logo Description (or upload URL)', type: 'textarea', placeholder: 'Describe the existing logo or paste image URL' },
      { name: 'brand_tone', label: 'Brand Personality', type: 'select', options: ['professional_trustworthy', 'friendly_approachable', 'luxurious_premium', 'playful_energetic', 'innovative_modern', 'traditional_established'] },
      { name: 'target_audience', label: 'Target Audience', type: 'textarea', placeholder: 'Who are your customers? Demographics, interests' },
      { name: 'competitors', label: 'Competitor Names (Optional)', type: 'text', placeholder: 'Help us differentiate from competitors' },
      { name: 'usage_context', label: 'Primary Brand Applications', type: 'select', options: ['signage_focused', 'vehicle_fleet', 'retail_storefront', 'digital_web', 'print_materials', 'all_applications'] }
    ]
  },
  // Business Tools
  {
    id: 'business_copywriter',
    name: 'Business Copywriter',
    description: 'Generate professional copy on demand.',
    icon: FileText,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'copy_type', label: 'Copy Type', type: 'select', options: ['tagline_slogan', 'about_us', 'service_description', 'email_template', 'ad_copy', 'social_media_post', 'website_copy', 'press_release'] },
      { name: 'business_info', label: 'Business Info', type: 'textarea', placeholder: 'What does the business do? Key services? Unique selling points?' },
      { name: 'tone', label: 'Tone', type: 'select', options: ['professional', 'casual_friendly', 'urgent_action', 'authoritative_expert', 'playful_fun', 'inspirational'] },
      { name: 'length', label: 'Length Preference', type: 'select', options: ['short_punchy', 'medium_balanced', 'long_detailed'] },
      { name: 'key_points', label: 'Must-Include Points', type: 'textarea', placeholder: 'What must be mentioned? Special offers, contact info, etc.' }
    ]
  },
  {
    id: 'document_composer',
    name: 'Document Composer',
    description: 'Generate professional business documents including proposals, late payment letters, and more.',
    icon: FileEdit,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'document_type', label: 'Document Type', type: 'select', options: ['proposal', 'scope_of_work', 'late_payment_reminder', 'final_payment_notice', 'collections_letter', 'thank_you_letter', 'project_brief', 'installation_instructions', 'warranty_info', 'maintenance_guide', 'other_custom'] },
      { name: 'custom_document_type', label: 'Custom Document Type (if Other)', type: 'text', placeholder: 'Describe what type of document you need' },
      { name: 'client_name', label: 'Client/Company Name', type: 'text', placeholder: 'Client or company name' },
      { name: 'project_or_invoice_details', label: 'Project/Invoice Details', type: 'textarea', placeholder: 'For proposals: describe the project. For payment letters: invoice #, amount, due date' },
      { name: 'tone', label: 'Document Tone', type: 'select', options: ['formal_professional', 'firm_but_polite', 'friendly', 'urgent'] },
      { name: 'your_company_name', label: 'Your Company Name', type: 'text', placeholder: 'Your sign shop name' },
      { name: 'special_terms', label: 'Special Terms/Notes', type: 'textarea', placeholder: 'Payment terms, conditions, or any specific requirements' }
    ]
  },
  {
    id: 'pricing_intelligence',
    name: 'Pricing Intelligence Assistant',
    description: 'Analyze pricing and profit margins.',
    icon: DollarSign,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'service_type', label: 'Service/Product Type', type: 'text', placeholder: 'e.g., Vehicle Wrap, Channel Letters, Banner' },
      { name: 'specifications', label: 'Specifications', type: 'textarea', placeholder: 'Size, materials, complexity, installation requirements' },
      { name: 'material_cost', label: 'Material Cost ($)', type: 'text', placeholder: 'e.g., 500' },
      { name: 'labor_hours', label: 'Estimated Labor Hours', type: 'text', placeholder: 'e.g., 8' },
      { name: 'current_price', label: 'Current/Proposed Price ($)', type: 'text', placeholder: 'e.g., 1500' },
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
    generatesImages: false,
    fields: [
      { name: 'job_description', label: 'Job Description', type: 'textarea', placeholder: 'What was the project? Vehicle wrap, storefront, etc.' },
      { name: 'job_type', label: 'Job Type', type: 'select', options: ['vehicle_wrap', 'storefront_sign', 'monument_sign', 'interior_signage', 'banner', 'window_graphics', 'fleet_graphics', 'dimensional_letters', 'other'] },
      { name: 'client_industry', label: 'Client Industry (no names)', type: 'text', placeholder: 'e.g., local restaurant, construction company' },
      { name: 'tone', label: 'Post Tone', type: 'select', options: ['professional', 'excited_proud', 'casual_friendly', 'storytelling'] },
      { name: 'platforms', label: 'Target Platforms', type: 'select', options: ['facebook', 'instagram', 'linkedin', 'all_platforms'] }
    ]
  },
  {
    id: 'social_pack_generator',
    name: 'Social Media Pack Generator',
    description: 'Generate batches of content for social media.',
    icon: Share2,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'services_offered', label: 'Services You Offer', type: 'textarea', placeholder: 'List your main services: wraps, signs, banners, etc.' },
      { name: 'posting_frequency', label: 'Posting Frequency', type: 'select', options: ['daily', '3x_per_week', '2x_per_week', 'weekly'] },
      { name: 'pack_size', label: 'Number of Posts', type: 'select', options: ['5_posts', '10_posts', '15_posts', '30_posts'] },
      { name: 'target_audience', label: 'Target Audience', type: 'text', placeholder: 'Local businesses, contractors, restaurants, etc.' },
      { name: 'content_mix', label: 'Content Mix', type: 'select', options: ['mostly_promotional', 'mostly_educational', 'behind_the_scenes', 'balanced_mix'] }
    ]
  },
  {
    id: 'content_calendar',
    name: 'Content Calendar Creator',
    description: 'Plan consistent posting schedule.',
    icon: Calendar,
    category: 'marketing',
    generatesImages: false,
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
    generatesImages: false,
    fields: [
      { name: 'campaign_type', label: 'Campaign Type', type: 'select', options: ['grand_opening', 'seasonal_sale', 'new_service_launch', 'referral_program', 'local_event', 'brand_awareness', 'holiday_promotion'] },
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
  const { generateAIContent, fetchAIHistory, generateAIImages } = useApp();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState(aiTools[0]);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [selectedImageIndex, setSelectedImageIndex] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [uploadedImagePreview, setUploadedImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  const filteredTools = selectedCategory === 'all' 
    ? aiTools 
    : aiTools.filter(t => t.category === selectedCategory);

  const handleToolSelect = (toolId) => {
    const tool = aiTools.find(t => t.id === toolId);
    setSelectedTool(tool);
    setFormData({});
    setResult(null);
    setGeneratedImages([]);
    setSelectedImageIndex(null);
    setUploadedImagePreview(null);
  };

  const handleFieldChange = (fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setUploadedImagePreview(previewUrl);
      
      // Convert to base64 for API
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData(prev => ({ 
          ...prev, 
          image_upload: reader.result,
          image_filename: file.name
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerate = async () => {
    const hasContent = Object.values(formData).some(v => v && String(v).trim());
    if (!hasContent) {
      toast.error('Please fill in at least one field');
      return;
    }

    setLoading(true);
    setResult(null);
    setGeneratedImages([]);
    setSelectedImageIndex(null);
    
    try {
      // Check if this tool generates images
      if (selectedTool.generatesImages) {
        // Generate images using the AI image generation
        const imagePromises = [];
        const count = selectedTool.imageCount || 3;
        
        // First get text guidance/concepts
        const textResponse = await generateAIContent(selectedTool.id, formData);
        setResult(textResponse);
        
        // Then generate images
        toast.info(`Generating ${count} design options...`);
        
        const imageResponse = await generateAIImages(selectedTool.id, formData, count);
        if (imageResponse && imageResponse.images) {
          setGeneratedImages(imageResponse.images);
          toast.success(`Generated ${imageResponse.images.length} design options!`);
        }
      } else {
        // Text-only generation
        const response = await generateAIContent(selectedTool.id, formData);
        setResult(response);
        toast.success('Generated successfully!');
      }
    } catch (err) {
      console.error('Generation error:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate content');
    }
    setLoading(false);
  };

  const handleSelectImage = (index) => {
    setSelectedImageIndex(index);
    toast.success(`Option ${index + 1} selected! You can request modifications below.`);
  };

  const handleRegenerateImage = async (index) => {
    toast.info('Regenerating this option...');
    try {
      const imageResponse = await generateAIImages(selectedTool.id, {
        ...formData,
        regenerate_index: index,
        modification_notes: formData.modification_notes || ''
      }, 1);
      
      if (imageResponse && imageResponse.images && imageResponse.images[0]) {
        const newImages = [...generatedImages];
        newImages[index] = imageResponse.images[0];
        setGeneratedImages(newImages);
        toast.success('Design regenerated!');
      }
    } catch (err) {
      toast.error('Failed to regenerate');
    }
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
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-muted-foreground capitalize">{tool.category}</span>
                          {tool.generatesImages && (
                            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">
                              <ImageIcon className="h-2.5 w-2.5 mr-0.5" />
                              Images
                            </Badge>
                          )}
                        </div>
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
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-2xl font-bold font-heading uppercase">{selectedTool.name}</h2>
                    <Badge variant="outline" className="capitalize">{selectedTool.category}</Badge>
                    {selectedTool.generatesImages && (
                      <Badge className="bg-gradient-to-r from-purple-500 to-pink-500">
                        <ImageIcon className="h-3 w-3 mr-1" />
                        Generates Images
                      </Badge>
                    )}
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
                  {field.type === 'image_upload' && (
                    <div className="space-y-3">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        ref={fileInputRef}
                        className="hidden"
                        data-testid={`input-${field.name}`}
                      />
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => fileInputRef.current?.click()}
                        className="w-full h-24 border-dashed"
                      >
                        <div className="flex flex-col items-center gap-2">
                          <Upload className="h-6 w-6" />
                          <span>{uploadedImagePreview ? 'Change Image' : 'Click to Upload Image'}</span>
                        </div>
                      </Button>
                      {uploadedImagePreview && (
                        <div className="relative">
                          <img 
                            src={uploadedImagePreview} 
                            alt="Uploaded preview" 
                            className="w-full max-h-48 object-contain rounded-lg border border-border"
                          />
                          <Badge className="absolute top-2 right-2 bg-green-500">
                            <Check className="h-3 w-3 mr-1" /> Image Uploaded
                          </Badge>
                        </div>
                      )}
                    </div>
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
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> 
                    {selectedTool.generatesImages ? 'Generating Designs...' : 'Generating...'}
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" /> 
                    {selectedTool.generatesImages ? `Generate ${selectedTool.imageCount} Design Options` : 'Generate'}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Generated Images Section */}
          {generatedImages.length > 0 && (
            <Card className="bg-card border-border/50 border-primary/30">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm text-primary flex items-center gap-2">
                    <ImageIcon className="h-4 w-4" />
                    Generated Design Options
                  </CardTitle>
                  <Badge variant="outline">Click to select your favorite</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {generatedImages.map((img, index) => (
                    <div 
                      key={index}
                      className={`relative rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
                        selectedImageIndex === index 
                          ? 'border-primary ring-2 ring-primary/30' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => handleSelectImage(index)}
                    >
                      <img 
                        src={img.url} 
                        alt={`Design option ${index + 1}`}
                        className="w-full aspect-square object-cover"
                      />
                      <div className="absolute top-2 left-2">
                        <Badge className={selectedImageIndex === index ? 'bg-primary' : 'bg-black/60'}>
                          Option {index + 1}
                        </Badge>
                      </div>
                      {selectedImageIndex === index && (
                        <div className="absolute top-2 right-2">
                          <Badge className="bg-green-500">
                            <Check className="h-3 w-3 mr-1" /> Selected
                          </Badge>
                        </div>
                      )}
                      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="secondary"
                            className="flex-1 h-8 text-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRegenerateImage(index);
                            }}
                          >
                            <RefreshCw className="h-3 w-3 mr-1" /> Regenerate
                          </Button>
                          <Button 
                            size="sm" 
                            variant="secondary"
                            className="h-8 text-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              window.open(img.url, '_blank');
                            }}
                          >
                            <Download className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Modification Request */}
                {selectedImageIndex !== null && (
                  <div className="mt-4 p-4 bg-muted/30 rounded-lg space-y-3">
                    <Label>Request Changes to Option {selectedImageIndex + 1}</Label>
                    <Textarea
                      value={formData.modification_notes || ''}
                      onChange={(e) => handleFieldChange('modification_notes', e.target.value)}
                      placeholder="Describe changes you'd like... e.g., 'Make the text larger', 'Use darker colors', 'Add more space around the logo'"
                      rows={2}
                    />
                    <Button 
                      onClick={() => handleRegenerateImage(selectedImageIndex)}
                      variant="outline"
                    >
                      <RefreshCw className="h-4 w-4 mr-2" /> Apply Changes
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Text Result */}
          {result && (
            <Card className="bg-card border-border/50 border-primary/30">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm text-primary">
                    {selectedTool.generatesImages ? 'Design Notes & Guidance' : 'Result'}
                  </CardTitle>
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
