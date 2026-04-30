import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import { formatDateTime } from '../lib/utils';
import { 
  Sparkles, Image, Wand2, Type, Layout, Flag, Box, 
  Palette, FileText, PenTool, Share2, Calendar, Target,
  FileEdit, DollarSign, Loader2, Copy, History, Upload,
  Download, ChevronRight, Check, RefreshCw, ImageIcon,
  ExternalLink, MessageSquare, ClipboardList, Save, Send,
  FileDown, FolderPlus, Users
} from 'lucide-react';
import { toast } from 'sonner';
import { useAICreditGuard } from '../components/credits/AICreditConfirmationDialog';
import CustomerBrandingPicker from '../components/CustomerBrandingPicker';

const aiTools = [
  // NEW AI Tools
  {
    id: 'logo_refresher',
    name: 'Logo Refresher',
    description: 'Upload your logo and get it refreshed in multiple modern styles.',
    icon: RefreshCw,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    hidden: true, // Audit 2026-04: uploaded logo is not actually sent to image gen — hide until true image-to-image works.
    fields: [
      { name: 'image_upload', label: 'Upload Your Current Logo', type: 'image_upload', required: true },
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Name on the logo', required: true },
      { name: 'style_direction', label: 'Style Direction', type: 'select', options: ['modernize_minimal', 'make_bold_impactful', 'add_elegance', 'make_playful', 'vintage_retro', 'tech_futuristic', 'hand_drawn_organic'] },
      { name: 'keep_elements', label: 'Elements to Keep', type: 'textarea', placeholder: 'e.g., keep the mountain icon, keep the color blue, preserve the shield shape' },
      { name: 'change_elements', label: 'Elements to Change', type: 'textarea', placeholder: 'e.g., update the font, simplify the icon, change to single color' }
    ]
  },
  {
    id: 'generative_fill',
    name: 'Generative Fill / Image Expander',
    description: 'Expand your images beyond their borders or fill in missing areas with AI.',
    icon: ImageIcon,
    category: 'design',
    generatesImages: true,
    imageCount: 2,
    hidden: true, // Audit 2026-04: uploaded image is not actually sent to image gen — hide until true outpainting works.
    fields: [
      { name: 'image_upload', label: 'Upload Image to Expand', type: 'image_upload', required: true },
      { name: 'expand_direction', label: 'Expansion Direction', type: 'select', options: ['expand_all_sides', 'expand_left', 'expand_right', 'expand_top', 'expand_bottom', 'expand_horizontal', 'expand_vertical'] },
      { name: 'content_description', label: 'Describe What to Generate', type: 'textarea', placeholder: 'Describe what should appear in the expanded area, e.g., continue the sky and clouds, add more storefront, extend the road' },
      { name: 'style_match', label: 'Style Matching', type: 'select', options: ['match_exactly', 'enhance_quality', 'artistic_interpretation'] }
    ]
  },
  {
    id: 'text_to_image',
    name: 'AI Image Concept Creator',
    description: 'Create AI-generated concept images from a text description for design inspiration, marketing visuals, or rough creative direction. Not print-ready production artwork.',
    icon: Sparkles,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'image_prompt', label: 'Describe the Image You Want', type: 'textarea', placeholder: 'Be specific! e.g., A modern coffee shop storefront with large windows, outdoor seating, and a warm inviting glow at sunset', required: true },
      { name: 'image_style', label: 'Image Style', type: 'select', options: ['photorealistic', 'illustration', 'digital_art', 'sketch', 'watercolor', 'minimalist', '3d_render', 'vintage_photo'] },
      { name: 'aspect_ratio', label: 'Aspect Ratio', type: 'select', options: ['square_1x1', 'landscape_16x9', 'portrait_9x16', 'wide_banner_3x1', 'standard_4x3'] },
      { name: 'color_mood', label: 'Color/Mood', type: 'select', options: ['vibrant_colorful', 'muted_soft', 'dark_moody', 'bright_airy', 'warm_tones', 'cool_tones', 'black_and_white', 'neon_glow'] }
    ]
  },
  {
    id: 'idea_brainstormer',
    name: 'Idea Brainstormer',
    description: 'Generate creative taglines, logo concepts, and business ideas.',
    icon: Sparkles,
    category: 'branding',
    generatesImages: false,
    fields: [
      { name: 'brainstorm_type', label: 'What Do You Need?', type: 'select', options: ['taglines_slogans', 'logo_concepts', 'business_names', 'campaign_ideas', 'product_names', 'event_themes'], required: true },
      { name: 'business_name', label: 'Business/Brand Name', type: 'text', placeholder: 'Name of the business (if applicable)' },
      { name: 'industry', label: 'Industry', type: 'text', placeholder: 'e.g., Restaurant, Auto Repair, Law Firm, Fitness' },
      { name: 'target_audience', label: 'Target Audience', type: 'textarea', placeholder: 'Who are you trying to reach? What do they care about?' },
      { name: 'key_values', label: 'Key Values/USP', type: 'textarea', placeholder: 'What makes this business unique? Core values, differentiators' },
      { name: 'competitors', label: 'Competitors (Optional)', type: 'text', placeholder: 'Comma-separated names of competing brands' },
      { name: 'differentiation', label: 'Differentiation / What makes this brand different', type: 'textarea', placeholder: 'Why a customer would choose this brand over the competitors' },
      { name: 'tone', label: 'Desired Tone', type: 'select', options: ['professional_serious', 'friendly_approachable', 'fun_playful', 'luxurious_premium', 'bold_edgy', 'warm_caring', 'innovative_tech'] },
      { name: 'avoid', label: 'Things to Avoid', type: 'text', placeholder: 'Any words, themes, or styles to avoid' }
    ],
    supportsCustomerBranding: true,
  },
  {
    id: 'permit_research',
    name: 'Sign Permit Research',
    description: 'Get guidance on sign permit requirements for any location.',
    icon: FileText,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'city_state', label: 'City and State', type: 'text', placeholder: 'e.g., Austin, TX or Los Angeles, CA', required: true },
      { name: 'sign_type', label: 'Type of Sign', type: 'select', options: ['monument_sign', 'pylon_sign', 'channel_letters', 'wall_sign', 'awning_sign', 'window_graphics', 'a_frame_sidewalk', 'digital_led', 'banner_temporary', 'vehicle_wrap'], required: true },
      { name: 'sign_size', label: 'Approximate Sign Size', type: 'text', placeholder: 'e.g., 4ft x 8ft, 24 inch tall letters' },
      { name: 'location_type', label: 'Location Type', type: 'select', options: ['commercial_strip', 'shopping_center', 'downtown_historic', 'industrial', 'residential_area', 'highway_visible'] },
      { name: 'illumination', label: 'Illumination', type: 'select', options: ['non_illuminated', 'internally_lit', 'externally_lit', 'led_digital', 'neon'] },
      { name: 'specific_questions', label: 'Specific Questions', type: 'textarea', placeholder: 'Any specific permit questions you have?' }
    ]
  },
  {
    id: 'ai_business_assistant',
    name: 'AI Business Assistant',
    description: 'Chat with an AI assistant about your sign shop business, pricing, operations, and more.',
    icon: Sparkles,
    category: 'business',
    generatesImages: false,
    isExternalLink: true,
    externalUrl: '/ai-assistant',
    fields: []
  },
  // Design Tools
  {
    id: 'photo_enhancer',
    name: 'Photo Enhancer Analyzer',
    description: 'Upload a photo to get professional enhancement recommendations and a print-readiness assessment with verdict (Approved / Needs Fixing / Not Usable).',
    icon: Image,
    category: 'design',
    generatesImages: false,
    fields: [
      { name: 'image_upload', label: 'Upload Image to Analyze', type: 'image_upload', required: true },
      { name: 'enhancement_notes', label: 'Enhancement Goals', type: 'textarea', placeholder: 'e.g., make it brighter, need for large banner print, fix colors' },
      { name: 'output_type', label: 'Intended Use', type: 'select', options: ['print_large_format', 'print_standard', 'web_digital', 'social_media'] }
    ]
  },
  {
    id: 'image_vectorizer',
    name: 'Vectorization Analyzer',
    description: 'Upload an image to get vectorization guidance, complexity assessment, and production tips.',
    icon: Wand2,
    category: 'design',
    generatesImages: false,
    fields: [
      { name: 'image_upload', label: 'Upload Image to Analyze', type: 'image_upload', required: true },
      { name: 'num_colors', label: 'Target Color Count', type: 'select', options: ['2_colors', '3_colors', '4_colors', '6_colors', '8_colors', 'full_color'] },
      { name: 'image_type', label: 'Source Image Type', type: 'select', options: ['crisp_line_art', 'logo_clean_edges', 'photo_simple', 'photo_complex', 'hand_drawn', 'blurry_edges'] }
    ]
  },
  {
    id: 'font_identifier',
    name: 'Font Identifier',
    description: 'Upload an image containing text to identify the font and get alternatives.',
    icon: Type,
    category: 'design',
    generatesImages: false,
    fields: [
      { name: 'image_upload', label: 'Upload Image with Text', type: 'image_upload', required: true },
      { name: 'text_sample', label: 'Text Visible in Image (helps accuracy)', type: 'text', placeholder: 'Type the text you see, e.g., "GRAND OPENING"' }
    ]
  },
  {
    id: 'ai_sign_designer',
    name: 'AI Sign Designer',
    description: 'Generate AI sign concept images with a short written design brief (direction, colors, readability, production notes). Concepts are a starting point — final production artwork may need cleanup.',
    icon: Layout,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'business_name', label: 'Business Name (text on sign)', type: 'text', placeholder: 'e.g., "Joe\'s Auto Shop"', required: true },
      { name: 'business_type', label: 'Business Type', type: 'text', placeholder: 'e.g., Restaurant, Retail Store, Law Office' },
      { name: 'sign_type', label: 'Sign Type', type: 'select', options: ['channel_letters', 'monument_sign', 'pylon_sign', 'wall_sign', 'lightbox_cabinet', 'dimensional_letters', 'awning', 'blade_sign'] },
      { name: 'size', label: 'Approximate Size', type: 'text', placeholder: 'e.g., 4ft x 8ft, 24 inches tall' },
      { name: 'colors', label: 'Brand Colors', type: 'text', placeholder: 'e.g., Navy Blue, Gold, White' },
      { name: 'additional_text', label: 'Additional Text (tagline, phone, etc.)', type: 'textarea', placeholder: 'Any other text to include on the sign' },
      { name: 'style_preference', label: 'Style', type: 'select', options: ['modern_clean', 'classic_traditional', 'bold_impactful', 'elegant_upscale', 'playful_fun', 'industrial_rugged', 'rustic_vintage'] }
    ]
  },
  {
    id: 'ai_banner_designer',
    name: 'AI Banner Designer',
    description: 'Generate AI banner concept images with a short written design brief (layout, readability, material/finish notes). Concepts are a starting point — final artwork may need cleanup before printing.',
    icon: Flag,
    category: 'design',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'headline', label: 'Main Headline', type: 'text', placeholder: 'e.g., GRAND OPENING!', required: true },
      { name: 'subtext', label: 'Supporting Text', type: 'textarea', placeholder: 'Date, location, offer details, call to action, phone number' },
      { name: 'banner_size', label: 'Banner Size', type: 'select', options: ['2x4ft', '3x6ft', '4x8ft', '3x10ft', '4x12ft', 'retractable_33x80'] },
      { name: 'event_type', label: 'Purpose', type: 'select', options: ['grand_opening', 'sale_promotion', 'event_announcement', 'sports_team', 'birthday_celebration', 'business_promotion', 'now_hiring', 'real_estate', 'political'] },
      { name: 'brand_colors', label: 'Colors to Use', type: 'text', placeholder: 'e.g., Red, White, Blue' },
      { name: 'style', label: 'Design Style', type: 'select', options: ['bold_modern', 'elegant_classy', 'fun_colorful', 'professional_corporate', 'vintage_retro', 'minimalist_clean'] }
    ]
  },
  {
    id: 'mockup_creator',
    name: 'Mockup Creator',
    description: 'Generate AI-rendered concept mockups showing a described design in real environments. The AI illustrates the description — it does not place your customer\'s actual artwork.',
    icon: Box,
    category: 'design',
    generatesImages: true,
    imageCount: 2,
    fields: [
      { name: 'design_description', label: 'Describe the Design to Show', type: 'textarea', placeholder: 'Describe your sign/graphic - e.g., "Red channel letters spelling PIZZA on white background"', required: true },
      { name: 'product_type', label: 'Product Type', type: 'select', options: ['storefront_sign', 'vehicle_wrap_car', 'vehicle_wrap_truck', 'vehicle_wrap_van', 'window_graphics', 'monument_sign', 'wall_sign_interior', 'banner_outdoor', 'yard_sign', 'trade_show_booth'] },
      { name: 'environment', label: 'Environment Setting', type: 'select', options: ['urban_street_day', 'suburban_plaza', 'parking_lot', 'highway_view', 'indoor_office', 'indoor_retail', 'night_illuminated'] }
    ]
  },
  {
    id: 'vehicle_wrap_mockup',
    name: 'Vehicle Wrap Mockup Generator',
    description: 'Generate AI-rendered concept mockups of a wrap design across vehicle types. The AI illustrates your description — it does not apply your customer\'s actual artwork.',
    icon: Box,
    category: 'design',
    generatesImages: true,
    imageCount: 2,
    fields: [
      { name: 'design_description', label: 'Describe Your Wrap Design', type: 'textarea', placeholder: 'Describe the wrap: colors, logo placement, text, graphics, style. E.g., "Blue and white design with company logo on doors, phone number on rear, website on hood"', required: true },
      { name: 'business_name', label: 'Business Name on Wrap', type: 'text', placeholder: 'Name to show on the vehicle', required: true },
      { name: 'vehicle_type', label: 'Vehicle Type', type: 'select', options: ['sedan_car', 'suv_crossover', 'pickup_truck', 'box_truck', 'cargo_van', 'sprinter_van', 'semi_truck', 'trailer', 'bus', 'sports_car'], required: true },
      { name: 'wrap_coverage', label: 'Wrap Coverage', type: 'select', options: ['full_wrap', 'partial_wrap_sides', 'partial_wrap_rear', 'spot_graphics_logo_only', 'half_wrap_lower'] },
      { name: 'primary_colors', label: 'Primary Colors', type: 'text', placeholder: 'e.g., Navy Blue, Orange, White' },
      { name: 'style', label: 'Design Style', type: 'select', options: ['clean_corporate', 'bold_aggressive', 'elegant_luxury', 'fun_playful', 'industrial_rugged', 'tech_modern', 'classic_traditional'] },
      { name: 'view_angle', label: 'View Angle', type: 'select', options: ['three_quarter_front', 'side_view', 'three_quarter_rear', 'front_view'] }
    ]
  },
  // Branding Tools
  {
    id: 'logo_creator',
    name: 'Logo Creator',
    description: 'Generate AI logo concept images (raster — final production may need vectorization).',
    icon: PenTool,
    category: 'branding',
    generatesImages: true,
    imageCount: 3,
    rasterDisclaimer: true,
    supportsCustomerBranding: true,
    fields: [
      { name: 'business_name', label: 'Business Name', type: 'text', placeholder: 'Name to appear in/with logo', required: true },
      { name: 'tagline', label: 'Tagline (Optional)', type: 'text', placeholder: 'e.g., "Quality Signs Since 1995"' },
      { name: 'industry', label: 'Industry', type: 'select', options: ['construction_trades', 'restaurant_food', 'retail_shop', 'automotive', 'healthcare_medical', 'legal_financial', 'technology', 'real_estate', 'fitness_sports', 'beauty_salon', 'education', 'nonprofit'] },
      { name: 'logo_type', label: 'Logo Style Preference', type: 'select', options: ['wordmark_text_only', 'lettermark_initials', 'icon_with_text', 'icon_symbol_only', 'emblem_badge_style'] },
      { name: 'style_preferences', label: 'Design Style', type: 'select', options: ['minimalist_clean', 'vintage_classic', 'modern_bold', 'playful_fun', 'corporate_professional', 'artistic_creative', 'luxurious_elegant'] },
      { name: 'color_preferences', label: 'Color Preferences', type: 'text', placeholder: 'e.g., Blues and greens, warm earth tones, black and gold' },
      { name: 'icon_ideas', label: 'Icon/Symbol Ideas (Optional)', type: 'text', placeholder: 'e.g., mountain, wrench, leaf, house' }
    ]
  },
  {
    id: 'branding_kit_generator',
    name: 'Branding Kit Generator',
    description: 'Create a complete brand system with colors, fonts, and guidelines.',
    icon: Palette,
    category: 'branding',
    generatesImages: false,
    supportsCustomerBranding: true,
    fields: [
      { name: 'business_name', label: 'Business / Brand Name', type: 'text', placeholder: 'e.g., Acme Signs', required: true },
      { name: 'industry', label: 'Industry', type: 'text', placeholder: 'e.g., Restaurant, Auto Repair, Law Firm', required: true },
      { name: 'existing_tagline', label: 'Existing Tagline (Optional)', type: 'text', placeholder: 'Leave blank if none' },
      { name: 'website', label: 'Website or Social Link (Optional)', type: 'text', placeholder: 'https://...' },
      { name: 'brand_color_preferences', label: 'Brand Color Preferences (Optional)', type: 'text', placeholder: 'e.g., navy & gold, earthy greens, black & red' },
      { name: 'logo_description', label: 'Describe Your Logo', type: 'textarea', placeholder: 'Describe the existing logo or what it should look like' },
      { name: 'brand_tone', label: 'Brand Personality', type: 'select', options: ['professional_trustworthy', 'friendly_approachable', 'luxurious_premium', 'playful_energetic', 'innovative_modern', 'traditional_established'] },
      { name: 'target_audience', label: 'Target Audience', type: 'textarea', placeholder: 'Who are your customers? What do they care about?' },
      { name: 'competitors', label: 'Competitors (Optional)', type: 'text', placeholder: 'Names of competitors to differentiate from' }
    ]
  },
  // Business Tools
  {
    id: 'business_copywriter',
    name: 'Business Copywriter',
    description: 'Generate professional marketing copy on demand.',
    icon: FileText,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'copy_type', label: 'Copy Type', type: 'select', options: ['tagline_slogan', 'about_us_page', 'service_description', 'email_template', 'ad_copy', 'social_media_post', 'website_homepage', 'brochure_text'] },
      { name: 'business_info', label: 'About the Business', type: 'textarea', placeholder: 'What does the business do? Key services? What makes them different?' },
      { name: 'tone', label: 'Tone', type: 'select', options: ['professional', 'casual_friendly', 'urgent_action', 'authoritative_expert', 'playful_fun', 'inspirational'] },
      { name: 'key_points', label: 'Must-Include Points', type: 'textarea', placeholder: 'What must be mentioned? Special offers, phone number, etc.' }
    ]
  },
  {
    id: 'document_composer',
    name: 'Document Composer',
    description: 'Generate professional business documents including proposals and payment letters.',
    icon: FileEdit,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'document_type', label: 'Document Type', type: 'select', options: ['proposal', 'scope_of_work', 'late_payment_reminder', 'final_payment_notice', 'collections_letter', 'thank_you_letter', 'project_brief', 'installation_instructions', 'warranty_info', 'other_custom'] },
      { name: 'custom_document_type', label: 'Custom Document Description (if Other)', type: 'text', placeholder: 'Describe what kind of document you need' },
      { name: 'client_name', label: 'Client/Company Name', type: 'text', placeholder: 'Who is this document for?' },
      { name: 'project_or_invoice_details', label: 'Project/Invoice Details', type: 'textarea', placeholder: 'For proposals: describe the project. For payment letters: invoice #, amount owed, due date' },
      { name: 'tone', label: 'Document Tone', type: 'select', options: ['formal_professional', 'firm_but_polite', 'friendly', 'urgent'] },
      { name: 'your_company_name', label: 'Your Company Name', type: 'text', placeholder: 'Your sign shop name for letterhead' }
    ]
  },
  {
    id: 'pricing_intelligence',
    name: 'Pricing Intelligence Assistant',
    description: 'Analyze pricing and get profit margin recommendations.',
    icon: DollarSign,
    category: 'business',
    generatesImages: false,
    fields: [
      { name: 'service_type', label: 'Service/Product Type', type: 'text', placeholder: 'e.g., Vehicle Wrap, Channel Letters, 4x8 Banner' },
      { name: 'specifications', label: 'Specifications', type: 'textarea', placeholder: 'Size, materials, complexity, installation requirements' },
      { name: 'material_cost', label: 'Material Cost ($)', type: 'text', placeholder: 'Your cost for materials' },
      { name: 'labor_hours', label: 'Estimated Labor Hours', type: 'text', placeholder: 'Design + production + install hours' },
      { name: 'current_price', label: 'Current/Proposed Price ($)', type: 'text', placeholder: 'What you plan to charge' }
    ]
  },
  // Marketing Tools
  {
    id: 'blog_creator',
    name: 'Blog Article Creator',
    description: 'Generate full blog articles for your website on any sign industry topic.',
    icon: FileText,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'topic_type', label: 'Topic Source', type: 'select', options: ['i_have_a_topic', 'suggest_topics_for_me'], required: true },
      { name: 'topic', label: 'Your Topic (if you have one)', type: 'text', placeholder: 'e.g., "Benefits of Vehicle Wraps for Small Businesses"' },
      { name: 'topic_area', label: 'Topic Area (for suggestions)', type: 'select', options: ['vehicle_wraps', 'business_signage', 'trade_shows', 'window_graphics', 'branding', 'marketing_tips', 'industry_trends', 'how_to_guides', 'customer_stories'] },
      { name: 'article_length', label: 'Article Length', type: 'select', options: ['short_500_words', 'medium_800_words', 'long_1200_words', 'comprehensive_1500_plus'] },
      { name: 'tone', label: 'Writing Tone', type: 'select', options: ['professional_informative', 'friendly_conversational', 'authoritative_expert', 'casual_engaging'] },
      { name: 'target_audience', label: 'Target Reader', type: 'text', placeholder: 'e.g., small business owners, marketing managers, fleet managers' },
      { name: 'include_cta', label: 'Call to Action', type: 'select', options: ['contact_for_quote', 'schedule_consultation', 'view_portfolio', 'download_guide', 'none'] },
      { name: 'seo_keywords', label: 'SEO Keywords (optional)', type: 'text', placeholder: 'e.g., vehicle wrap cost, business signs, custom graphics' }
    ]
  },
  {
    id: 'completed_job_post',
    name: 'Completed Order Post Creator',
    description: 'Turn a completed order into ready-to-post social content (with or without a photo).',
    icon: Share2,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'post_mode', label: 'Post Mode', type: 'select', options: ['with_image', 'text_only'], required: true, helpText: 'Choose "With Image" to upload a photo of the completed work, or "Text Only" for a quick text-based post.' },
      { name: 'image_upload', label: 'Upload Completed Order Photo', type: 'image_upload', requiredWhen: { field: 'post_mode', equals: 'with_image' }, showWhen: { field: 'post_mode', equals: 'with_image' } },
      { name: 'job_description', label: 'Describe the Completed Order', type: 'textarea', placeholder: 'Required for text-only posts. Describe colors, materials, scale, what made it special.', requiredWhen: { field: 'post_mode', equals: 'text_only' }, showWhen: { field: 'post_mode', equals: 'text_only' } },
      { name: 'job_type', label: 'What Did You Create?', type: 'select', options: ['full_vehicle_wrap', 'partial_vehicle_wrap', 'fleet_graphics', 'storefront_sign', 'channel_letters', 'monument_sign', 'wall_mural', 'window_graphics', 'banner', 'trade_show_display', 'dimensional_letters', 'awning', 'a_frame_sign', 'yard_signs', 'interior_signage', 'other'], required: true },
      { name: 'job_details', label: 'Order Details (optional)', type: 'textarea', placeholder: 'Extra context: challenges overcome, materials, turnaround time, special features.' },
      { name: 'client_industry', label: 'Client Industry (no names)', type: 'text', placeholder: 'e.g., local plumber, restaurant, real estate agent' },
      { name: 'platforms', label: 'Posting To', type: 'select', options: ['facebook', 'instagram', 'linkedin', 'tiktok', 'all_platforms'] },
      { name: 'post_style', label: 'Post Style', type: 'select', options: ['professional_showcase', 'behind_the_scenes', 'before_after', 'educational', 'casual_fun'] },
      { name: 'brand_voice', label: 'Brand Voice / Tone', type: 'select', options: ['professional', 'friendly', 'bold_confident', 'witty_playful', 'inspirational'] },
      { name: 'include_hashtags', label: 'Include Hashtags?', type: 'select', options: ['yes_full_set', 'yes_minimal', 'no'] }
    ]
  },
  {
    id: 'social_pack_generator',
    name: 'Social Media Pack Generator',
    description: 'Generate a batch of social media post ideas (5–30) you can drop straight into a calendar.',
    icon: Share2,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'services_offered', label: 'Services You Offer', type: 'textarea', placeholder: 'List your main services: vehicle wraps, signs, banners, etc.', required: true },
      { name: 'pack_size', label: 'Number of Posts', type: 'select', options: ['5_posts', '10_posts', '15_posts', '30_posts'], required: true },
      { name: 'platforms', label: 'Target Platforms', type: 'select', options: ['facebook', 'instagram', 'linkedin', 'tiktok', 'all_platforms'] },
      { name: 'target_audience', label: 'Target Audience', type: 'text', placeholder: 'Local businesses, contractors, restaurants, etc.' },
      { name: 'brand_voice', label: 'Brand Voice / Tone', type: 'select', options: ['professional', 'friendly', 'bold_confident', 'witty_playful', 'inspirational'] },
      { name: 'content_mix', label: 'Content Focus', type: 'select', options: ['mostly_promotional', 'mostly_educational', 'behind_the_scenes', 'balanced_mix'] }
    ]
  },
  {
    id: 'content_calendar',
    name: 'Content Calendar Creator',
    description: 'Plan a posting calendar with start date, frequency, themes and ideas per day.',
    icon: Calendar,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'start_date', label: 'Start Date', type: 'date', required: true },
      { name: 'date_range', label: 'Time Period', type: 'select', options: ['1_week', '2_weeks', '1_month'], required: true },
      { name: 'post_frequency', label: 'Posting Frequency', type: 'select', options: ['1x_per_day', '5x_per_week', '3x_per_week', '2x_per_week', '1x_per_week'], required: true },
      { name: 'platforms', label: 'Platforms', type: 'text', placeholder: 'e.g., Facebook, Instagram, LinkedIn' },
      { name: 'goals', label: 'Marketing Goals', type: 'textarea', placeholder: 'What do you want to achieve? More leads, brand awareness?' },
      { name: 'upcoming_events', label: 'Upcoming Events / Promotions', type: 'textarea', placeholder: 'Any sales, holidays, or events to plan around?' },
      { name: 'brand_voice', label: 'Brand Voice / Tone', type: 'select', options: ['professional', 'friendly', 'bold_confident', 'witty_playful', 'inspirational'] }
    ]
  },
  {
    id: 'campaign_builder',
    name: 'Campaign Builder',
    description: 'Design a complete marketing campaign.',
    icon: Target,
    category: 'marketing',
    generatesImages: false,
    fields: [
      { name: 'campaign_type', label: 'Campaign Type', type: 'select', options: ['grand_opening', 'seasonal_sale', 'new_service_launch', 'referral_program', 'holiday_promotion'] },
      { name: 'campaign_goal', label: 'Primary Goal', type: 'text', placeholder: 'e.g., Get 20 new leads, Increase sales 15%' },
      { name: 'target_audience', label: 'Target Audience', type: 'textarea', placeholder: 'Who are you trying to reach?' },
      { name: 'budget_range', label: 'Budget Range', type: 'select', options: ['under_500', '500_to_1000', '1000_to_2500', '2500_plus'] },
      { name: 'duration', label: 'Campaign Duration', type: 'select', options: ['1_week', '2_weeks', '1_month'] }
    ]
  },
  // Racing & Motorsports Tools
  {
    id: 'race_number_designer',
    name: 'Race Number Designer',
    description: 'Generate professional racing number designs with custom fonts, colors, and effects.',
    icon: Flag,
    category: 'racing',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'race_number', label: 'Race Number', type: 'text', placeholder: 'e.g., 24, 88, 3', required: true },
      { name: 'number_style', label: 'Number Style', type: 'select', options: ['classic_bold', 'italic_speed', 'blocky_industrial', 'script_elegant', 'grunge_distressed', 'outline_stroke', 'gradient_fade', '3d_dimensional', 'retro_vintage', 'futuristic_tech'], required: true },
      { name: 'color_scheme', label: 'Color Scheme', type: 'select', options: ['red_white', 'blue_white', 'yellow_black', 'green_white', 'orange_black', 'purple_gold', 'black_gold', 'custom_colors'] },
      { name: 'custom_colors', label: 'Custom Colors (if selected above)', type: 'text', placeholder: 'e.g., Primary: #FF0000, Outline: #000000' },
      { name: 'background_type', label: 'Background', type: 'select', options: ['transparent', 'solid_white', 'solid_black', 'checkered_flag', 'carbon_fiber', 'brushed_metal'] },
      { name: 'effects', label: 'Special Effects', type: 'select', options: ['none', 'drop_shadow', 'glow_effect', 'chrome_shine', 'racing_stripes', 'speed_lines'] },
      { name: 'racing_series', label: 'Racing Series Style', type: 'select', options: ['nascar_style', 'dirt_track', 'drag_racing', 'motocross', 'karting', 'sprint_car', 'rally', 'formula_style', 'custom'] }
    ]
  },
  {
    id: 'driver_name_plate',
    name: 'Driver Name Plate Generator',
    description: 'Create professional driver name plates and roof strips for race cars.',
    icon: Users,
    category: 'racing',
    generatesImages: true,
    imageCount: 2,
    fields: [
      { name: 'driver_name', label: 'Driver Name', type: 'text', placeholder: 'e.g., John Smith', required: true },
      { name: 'plate_type', label: 'Plate Type', type: 'select', options: ['door_name_strip', 'roof_strip', 'windshield_banner', 'quarter_panel_name', 'hero_card_style'], required: true },
      { name: 'include_number', label: 'Include Race Number?', type: 'select', options: ['yes', 'no'] },
      { name: 'race_number', label: 'Race Number (if included)', type: 'text', placeholder: 'e.g., 24' },
      { name: 'hometown', label: 'Hometown (optional)', type: 'text', placeholder: 'e.g., Charlotte, NC' },
      { name: 'sponsor_text', label: 'Sponsor Text (optional)', type: 'text', placeholder: 'e.g., Sponsored by ABC Racing' },
      { name: 'font_style', label: 'Font Style', type: 'select', options: ['classic_racing', 'modern_clean', 'aggressive_bold', 'script_signature', 'military_stencil'] },
      { name: 'color_scheme', label: 'Color Scheme', type: 'select', options: ['white_on_black', 'black_on_white', 'team_colors_custom', 'gold_on_black', 'red_white_blue'] },
      { name: 'custom_colors', label: 'Custom Team Colors (if selected)', type: 'text', placeholder: 'e.g., Background: #000, Text: #FFF, Accent: #FF0' }
    ]
  },
  {
    id: 'wrap_cost_calculator',
    name: 'Vehicle Wrap Cost Calculator',
    description: 'Calculate accurate pricing for vehicle wraps based on size, complexity, and materials.',
    icon: DollarSign,
    category: 'racing',
    generatesImages: false,
    fields: [
      { name: 'vehicle_type', label: 'Vehicle Type', type: 'select', options: ['sedan_compact', 'sedan_full', 'suv_crossover', 'suv_full_size', 'pickup_truck', 'van_cargo', 'van_sprinter', 'box_truck', 'semi_truck_cab', 'semi_trailer', 'race_car_stock', 'race_car_late_model', 'race_car_modified', 'sprint_car', 'motorcycle', 'atv_utv', 'boat', 'trailer'], required: true },
      { name: 'wrap_coverage', label: 'Wrap Coverage', type: 'select', options: ['full_wrap_100', 'partial_wrap_75', 'partial_wrap_50', 'partial_wrap_25', 'decal_kit_only', 'color_change_full', 'accent_only'], required: true },
      { name: 'wrap_type', label: 'Wrap Material Type', type: 'select', options: ['cast_vinyl_premium', 'cast_vinyl_standard', 'calendered_vinyl', 'reflective_vinyl', 'chrome_mirror', 'carbon_fiber_vinyl', 'matte_finish', 'gloss_finish', 'satin_finish'], required: true },
      { name: 'design_complexity', label: 'Design Complexity', type: 'select', options: ['simple_solid_color', 'simple_logo_text', 'moderate_graphics', 'complex_full_graphics', 'extreme_custom_art'] },
      { name: 'includes_design', label: 'Design Services Needed?', type: 'select', options: ['no_customer_provides', 'yes_simple_layout', 'yes_full_design', 'yes_custom_illustration'] },
      { name: 'installation_difficulty', label: 'Installation Difficulty', type: 'select', options: ['standard', 'moderate_curves', 'complex_surfaces', 'extreme_body_kit'] },
      { name: 'removal_needed', label: 'Old Wrap Removal?', type: 'select', options: ['no_removal', 'partial_removal', 'full_wrap_removal'] },
      { name: 'turnaround', label: 'Turnaround Time', type: 'select', options: ['standard_5_7_days', 'rush_3_days', 'express_24_48_hours'] },
      { name: 'your_hourly_rate', label: 'Your Shop Hourly Rate ($)', type: 'text', placeholder: 'e.g., 75' },
      { name: 'material_markup', label: 'Material Markup %', type: 'text', placeholder: 'e.g., 30' }
    ]
  },
  {
    id: 'race_team_branding',
    name: 'Race Team Branding Kit',
    description: 'Generate complete branding packages for race teams including logos, numbers, and sponsor layouts.',
    icon: Flag,
    category: 'racing',
    generatesImages: true,
    imageCount: 3,
    fields: [
      { name: 'team_name', label: 'Team Name', type: 'text', placeholder: 'e.g., Thunder Racing, Smith Motorsports', required: true },
      { name: 'racing_series', label: 'Racing Series', type: 'select', options: ['nascar_regional', 'dirt_track_late_model', 'dirt_track_modified', 'sprint_car', 'drag_racing', 'road_racing', 'rally', 'motocross', 'karting', 'other'], required: true },
      { name: 'primary_number', label: 'Primary Car Number', type: 'text', placeholder: 'e.g., 24' },
      { name: 'team_colors', label: 'Team Colors', type: 'text', placeholder: 'e.g., Red, White, and Blue or Hex codes: #FF0000, #FFFFFF, #0000FF' },
      { name: 'style_preference', label: 'Style Preference', type: 'select', options: ['aggressive_bold', 'classic_traditional', 'modern_clean', 'retro_vintage', 'tech_futuristic'] },
      { name: 'include_elements', label: 'Include Elements', type: 'select', options: ['logo_number_only', 'logo_number_pattern', 'full_wrap_concept', 'hero_card_template'] },
      { name: 'sponsor_placeholders', label: 'Sponsor Placeholder Locations', type: 'select', options: ['none', 'hood_only', 'hood_and_quarters', 'full_car_layout'] }
    ]
  }
];

const categories = [
  { id: 'all', name: 'All Tools', icon: Sparkles, color: 'text-cyan-400' },
  { id: 'design', name: 'Design Tools', icon: Image, color: 'text-blue-400', count: 8 },
  { id: 'branding', name: 'Branding', icon: Palette, color: 'text-purple-400', count: 3 },
  { id: 'business', name: 'Business', icon: FileText, color: 'text-green-400', count: 5 },
  { id: 'marketing', name: 'Marketing', icon: Share2, color: 'text-pink-400', count: 5 },
  { id: 'racing', name: 'Racing & Motorsports', icon: Flag, color: 'text-red-400', count: 4 }
];

export default function AITools() {
  const navigate = useNavigate();
  const { generateAIContent, fetchAIHistory, generateAIImages, api, customers, fetchCustomers } = useApp();
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTool, setSelectedTool] = useState(() => aiTools.find(t => !t.hidden) || aiTools[0]);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [selectedImageIndex, setSelectedImageIndex] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [uploadedImagePreview, setUploadedImagePreview] = useState(null);
  const fileInputRef = useRef(null);
  
  // Document action states
  const [savingToLibrary, setSavingToLibrary] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [sendingToPortal, setSendingToPortal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [sendMessage, setSendMessage] = useState('');
  const [notifyCustomer, setNotifyCustomer] = useState(true);

  // Branding profile attachment (Branding category tools only)
  const [brandingCustomerId, setBrandingCustomerId] = useState(null);
  const [brandingProfile, setBrandingProfile] = useState(null);
  const [savingToBrandingProfile, setSavingToBrandingProfile] = useState(false);

  // Load customers when needed
  useEffect(() => {
    if (showSendDialog && (!customers || customers.length === 0)) {
      fetchCustomers();
    }
  }, [showSendDialog, customers, fetchCustomers]);

  // Handle URL query parameter for tool selection
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const toolParam = params.get('tool');
    const customerParam = params.get('customer');
    if (toolParam) {
      const tool = aiTools.find(t => t.id === toolParam);
      if (tool) {
        setSelectedTool(tool);
        setSelectedCategory(tool.category);
        setFormData({});
        setResult(null);
        setGeneratedImages([]);
      }
    }
    // Deep-link from a customer's Branding tab: pre-attach + pre-fill
    if (customerParam) {
      (async () => {
        try {
          const r = await api.get(`/customers/${customerParam}/branding`);
          setBrandingCustomerId(customerParam);
          setBrandingProfile(r.data || {});
          handlePrefillFromBrandingProfile(r.data || {});
        } catch (err) {
          console.error('Auto-load customer branding profile failed', err);
        }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Visible tools = all tools minus those flagged as hidden in the audit
  // (hidden tools remain in the array so URL deep-links and ai_history items
  // referencing them still resolve).
  const visibleTools = aiTools.filter(t => !t.hidden);

  const filteredTools = selectedCategory === 'all'
    ? visibleTools
    : visibleTools.filter(t => t.category === selectedCategory);

  const handleToolSelect = (toolId) => {
    const tool = aiTools.find(t => t.id === toolId);
    
    // Handle external link tools
    if (tool.isExternalLink && tool.externalUrl) {
      navigate(tool.externalUrl);
      return;
    }
    
    setSelectedTool(tool);
    setFormData({});
    setResult(null);
    setGeneratedImages([]);
    setSelectedImageIndex(null);
    setUploadedImagePreview(null);
    setBrandingCustomerId(null);
    setBrandingProfile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
          image_filename: file.name,
          image_description: `Uploaded image: ${file.name}`
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  // Conditional-required helpers (used by `requiredWhen` and `showWhen`).
  const matchesCondition = (cond) => {
    if (!cond) return true;
    return formData?.[cond.field] === cond.equals;
  };
  const isFieldRequiredNow = (field) =>
    field.required || (field.requiredWhen && matchesCondition(field.requiredWhen));
  const isFieldVisible = (field) =>
    !field.showWhen || matchesCondition(field.showWhen);

  const handleGenerate = async () => {
    // Check for required fields (static + conditional)
    const requiredFields = selectedTool.fields.filter(isFieldRequiredNow);
    for (const field of requiredFields) {
      if (!isFieldVisible(field)) continue;
      if (!formData[field.name]) {
        toast.error(`Please provide: ${field.label}`);
        return;
      }
    }
    
    const hasContent = Object.values(formData).some(v => v && String(v).trim());
    if (!hasContent) {
      toast.error('Please fill in at least one field');
      return;
    }

    await runGuardedAction({
      actionType: selectedTool.id,
      featureName: selectedTool.name,
      execute: async () => {
        setLoading(true);
        setResult(null);
        setGeneratedImages([]);
        setSelectedImageIndex(null);

        try {
          if (selectedTool.generatesImages) {
            toast.info(`Generating ${selectedTool.imageCount} design options... This may take up to a minute.`);
            const imageResponse = await generateAIImages(selectedTool.id, formData, selectedTool.imageCount);
            if (imageResponse && imageResponse.images && imageResponse.images.length > 0) {
              setGeneratedImages(imageResponse.images);
              if (imageResponse.design_brief) {
                setResult({ content: imageResponse.design_brief });
              }
              toast.success(`Generated ${imageResponse.images.length} design options!`);
            } else {
              toast.error('No images were generated. Please try again.');
            }
          } else {
            const response = await generateAIContent(selectedTool.id, formData);
            setResult(response);
            toast.success('Generated successfully!');
          }
        } catch (err) {
          console.error('Generation error:', err);
          const errorMessage = err.response?.data?.detail || err.message || 'Generation failed. Please try again.';
          toast.error(errorMessage);
          // Don't re-throw - error is handled gracefully with toast
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const handleSelectImage = (index) => {
    setSelectedImageIndex(index);
    toast.success(`Option ${index + 1} selected!`);
  };

  const handleRegenerateImage = async (index) => {
    await runGuardedAction({
      actionType: selectedTool.id,
      featureName: `${selectedTool.name} (Regenerate)`,
      execute: async () => {
        toast.info('Regenerating this option...');
        setLoading(true);
        try {
          const imageResponse = await generateAIImages(selectedTool.id, {
            ...formData,
            modification_notes: formData.modification_notes || ''
          }, 1);
          
          if (imageResponse && imageResponse.images && imageResponse.images[0]) {
            const newImages = [...generatedImages];
            newImages[index] = imageResponse.images[0];
            setGeneratedImages(newImages);
            toast.success('Design regenerated!');
          }
        } catch (err) {
          console.error('Regenerate error:', err);
          toast.error(err.response?.data?.detail || err.message || 'Failed to regenerate');
          // Don't re-throw - error is handled gracefully with toast
        } finally {
          setLoading(false);
        }
      }
    });
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

  // Generate PDF from document content
  const handleGeneratePdf = async () => {
    const content = result?.content || result?.output;
    if (!content) return;
    
    setGeneratingPdf(true);
    try {
      const response = await api.post('/documents/generate-pdf', {
        content: content,
        title: `${selectedTool.name} - ${new Date().toLocaleDateString()}`,
        tool_id: selectedTool.id
      });
      
      // Download the PDF
      const { pdf_data, filename } = response.data;
      const byteCharacters = atob(pdf_data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `${selectedTool.id}_document.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('PDF downloaded successfully');
    } catch (err) {
      console.error('PDF generation error:', err);
      toast.error(err.response?.data?.detail || 'Failed to generate PDF');
    }
    setGeneratingPdf(false);
  };

  // Save document to library
  const handleSaveToLibrary = async () => {
    const content = result?.content || result?.output;
    if (!content) return;

    // Centralized AI tool → Document Library category map (audit 2026-04).
    // Keeps marketing/branding outputs out of the "other" bucket so they're
    // discoverable by category later.
    const TOOL_TO_DOC_CATEGORY = {
      // Branding
      logo_creator: 'logo_concept',
      branding_kit_generator: 'brand_kit',
      idea_brainstormer: 'tagline',
      // Marketing
      blog_creator: 'blog_article',
      completed_job_post: 'social_post',
      social_job_post: 'social_post',
      social_pack_generator: 'marketing_content',
      content_calendar: 'content_calendar',
      campaign_builder: 'campaign_plan',
      // Business
      document_composer: 'contract',
      product_description: 'marketing_content',
    };
    const category = TOOL_TO_DOC_CATEGORY[selectedTool.id] || 'other';

    setSavingToLibrary(true);
    try {
      await api.post('/documents/from-ai', {
        content: content,
        name: `${selectedTool.name} - ${new Date().toLocaleDateString()}`,
        tool_id: selectedTool.id,
        category,
        input_data: formData
      });

      toast.success('Document saved to library');
    } catch (err) {
      console.error('Save to library error:', err);
      toast.error(err.response?.data?.detail || 'Failed to save document');
    }
    setSavingToLibrary(false);
  };

  // ----- Branding Profile helpers (Branding tools only) -----
  const handlePrefillFromBrandingProfile = (profile) => {
    if (!profile) return;
    const next = { ...formData };
    // Generic mappings — only fill what's empty so we don't trample user edits
    const fillMap = {
      business_name: profile.business_name,
      industry: profile.industry,
      target_audience: profile.target_audience,
      brand_tone: profile.brand_personality,
      tone: profile.brand_personality,
      competitors: profile.competitors,
      differentiation: profile.differentiation,
      avoid: profile.things_to_avoid,
      brand_color_preferences:
        profile.brand_colors && profile.brand_colors.length
          ? profile.brand_colors.join(', ')
          : null,
      color_preferences:
        profile.brand_colors && profile.brand_colors.length
          ? profile.brand_colors.join(', ')
          : null,
      existing_tagline: profile.selected_tagline,
      tagline: profile.selected_tagline,
    };
    Object.entries(fillMap).forEach(([key, value]) => {
      if (value && !next[key]) next[key] = value;
    });
    setFormData(next);
    toast.success('Pre-filled from customer branding profile');
  };

  const handleBrandingPickerChange = ({ customerId, profile }) => {
    setBrandingCustomerId(customerId);
    setBrandingProfile(profile);
  };

  const saveToBrandingProfile = async (payload, successMsg = 'Saved to customer branding profile') => {
    if (!brandingCustomerId) {
      toast.error('Pick a customer first');
      return;
    }
    setSavingToBrandingProfile(true);
    try {
      await api.post(`/customers/${brandingCustomerId}/branding/append`, payload);
      toast.success(successMsg);
    } catch (err) {
      console.error('Save to branding profile error:', err);
      toast.error(err.response?.data?.detail || 'Failed to save to branding profile');
    } finally {
      setSavingToBrandingProfile(false);
    }
  };

  const handleSaveBrandKitToProfile = async () => {
    const content = result?.content || result?.output;
    if (!content) return;
    // Best-effort regex parse for hex codes and common font names
    const hexes = Array.from(
      content.matchAll(/#[0-9a-fA-F]{6}\b/g),
      (m) => m[0].toUpperCase()
    );
    const fontMatches = Array.from(
      content.matchAll(/(?:font|typeface)[:\s]+([A-Z][A-Za-z0-9 ]+?)(?:[,.\n]|$)/g),
      (m) => m[1].trim()
    ).filter((f) => f.length > 1 && f.length < 40);
    await saveToBrandingProfile({
      brand_kit_text: content,
      brand_colors: Array.from(new Set(hexes)).slice(0, 6),
      font_suggestions: Array.from(new Set(fontMatches)).slice(0, 4),
    });
  };

  const handleSaveTaglineToProfile = async (tagline, select = false) => {
    if (!tagline) return;
    await saveToBrandingProfile(
      { tagline, select_tagline: select },
      select ? 'Set as selected tagline' : 'Tagline saved'
    );
  };

  const handleSaveLogoToProfile = async (imageDataUrl, summary) => {
    if (!imageDataUrl) return;
    await saveToBrandingProfile({
      logo: {
        image_url: imageDataUrl,
        summary: summary || `Generated by ${selectedTool.name}`,
        source_tool: selectedTool.id,
      },
    });
  };

  // Send document directly to customer portal
  const handleSendToPortal = async () => {
    if (!selectedCustomerId) {
      toast.error('Please select a customer');
      return;
    }
    
    const content = result?.content || result?.output;
    if (!content) return;
    
    setSendingToPortal(true);
    try {
      // First save to library, then send to portal
      const docResponse = await api.post('/documents/from-ai', {
        content: content,
        name: `${selectedTool.name} - ${new Date().toLocaleDateString()}`,
        tool_id: selectedTool.id,
        category: selectedTool.category === 'business' ? 'contract' : 'other',
        input_data: formData
      });
      
      // Send to customer portal
      await api.post(`/documents/${docResponse.data.id}/send-to-portal`, {
        customer_id: selectedCustomerId,
        message: sendMessage,
        notify_customer: notifyCustomer
      });
      
      toast.success('Document sent to customer portal');
      setShowSendDialog(false);
      setSelectedCustomerId('');
      setSendMessage('');
    } catch (err) {
      console.error('Send to portal error:', err);
      toast.error(err.response?.data?.detail || 'Failed to send document');
    }
    setSendingToPortal(false);
  };

  const downloadImage = (imageUrl, index) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${selectedTool.id}_option_${index + 1}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const Icon = selectedTool.icon;
  const categoryInfo = categories.find(c => c.id === selectedTool.category);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="ai-tools-page">
      {creditDialog}
      {/* Header */}
      <div>
          <h1 className="text-4xl font-bold font-heading uppercase tracking-tight text-gray-900">AI Tools Suite</h1>
        <p className="text-gray-700 mt-1">{visibleTools.length} AI-powered tools for design, branding, business, and marketing</p>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedCategory === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedCategory('all')}
        >
          All Tools ({visibleTools.length})
        </Button>
        {categories.map(cat => {
          const CatIcon = cat.icon;
          const count = visibleTools.filter(t => t.category === cat.id).length;
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
        <Card className="bg-white border-gray-200 lg:col-span-1">
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
                          : 'hover:bg-gray-50/50'
                      }`}
                      data-testid={`tool-${tool.id}`}
                    >
                      <ToolIcon className={`h-5 w-5 flex-shrink-0 ${selectedTool.id === tool.id ? 'text-primary' : toolCat?.color || 'text-gray-500'}`} />
                      <div className="flex-1 min-w-0">
                        <span className={`text-sm font-medium block truncate ${selectedTool.id === tool.id ? 'text-primary' : ''}`}>
                          {tool.name}
                        </span>
                        <div className="flex items-center gap-1">
                          <span className="text-xs text-gray-500 capitalize">{tool.category}</span>
                          {tool.generatesImages && (
                            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4 bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-purple-500/30">
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
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
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
                        Generates {selectedTool.imageCount} Images
                      </Badge>
                    )}
                  </div>
                  <p className="text-gray-500 mt-1">{selectedTool.description}</p>
                </div>
                <Button variant="outline" size="sm" onClick={loadHistory} data-testid="view-history-btn">
                  <History className="h-4 w-4 mr-2" /> History
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Input Form */}
          <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <CardHeader>
              <CardTitle className="font-heading uppercase text-sm">Input</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedTool.supportsCustomerBranding && (
                <CustomerBrandingPicker
                  value={brandingCustomerId}
                  onChange={handleBrandingPickerChange}
                  onPrefill={handlePrefillFromBrandingProfile}
                />
              )}
              {selectedTool.rasterDisclaimer && (
                <div
                  className="text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded p-2"
                  data-testid="logo-raster-disclaimer"
                >
                  <strong>Heads up:</strong> AI-generated logo concepts are
                  raster images. Use them as a starting concept — final
                  production artwork may need cleanup or vectorization.
                </div>
              )}
              {selectedTool.fields.map((field) => {
                if (!isFieldVisible(field)) return null;
                const requiredNow = isFieldRequiredNow(field);
                return (
                <div key={field.name} className="space-y-2">
                  <Label>
                    {field.label}
                    {requiredNow && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                  {field.helpText && (
                    <p className="text-xs text-gray-500 -mt-1">{field.helpText}</p>
                  )}
                  {field.type === 'text' && (
                    <Input
                      value={formData[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      placeholder={field.placeholder}
                      data-testid={`input-${field.name}`}
                    />
                  )}
                  {field.type === 'date' && (
                    <Input
                      type="date"
                      value={formData[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      data-testid={`input-${field.name}`}
                    />
                  )}
                  {field.type === 'textarea' && (
                    <Textarea
                      value={formData[field.name] || ''}
                      onChange={(e) => handleFieldChange(field.name, e.target.value)}
                      placeholder={field.placeholder}
                      rows={3}
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
                        className={`w-full h-32 border-dashed flex flex-col items-center justify-center gap-2 ${uploadedImagePreview ? 'border-green-500' : ''}`}
                      >
                        {uploadedImagePreview ? (
                          <>
                            <Check className="h-6 w-6 text-green-500" />
                            <span className="text-green-500">Image Uploaded - Click to Change</span>
                          </>
                        ) : (
                          <>
                            <Upload className="h-8 w-8" />
                            <span>Click to Upload Image</span>
                            <span className="text-xs text-gray-500">JPG, PNG, or WebP</span>
                          </>
                        )}
                      </Button>
                      {uploadedImagePreview && (
                        <div className="relative">
                          <img 
                            src={uploadedImagePreview} 
                            alt="Uploaded preview" 
                            className="w-full max-h-48 object-contain rounded-lg border border-gray-200 bg-black/20"
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
                );
              })}
              
              <Button 
                onClick={handleGenerate} 
                disabled={loading}
                className="w-full neon-glow h-12 text-lg"
                data-testid="generate-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" /> 
                    {selectedTool.generatesImages ? 'Generating Images... (up to 60 sec)' : 'Generating...'}
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 mr-2" /> 
                    {selectedTool.generatesImages ? `Generate ${selectedTool.imageCount} Design Options` : 'Generate'}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Generated Images Section */}
          {generatedImages.length > 0 && (
            <Card className="bg-white border-gray-200 border-green-500/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm text-green-400 flex items-center gap-2">
                    <ImageIcon className="h-4 w-4" />
                    Generated Designs - {generatedImages.length} Options
                  </CardTitle>
                  <Badge variant="outline" className="text-green-400 border-green-500/50">Click image to select</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className={`grid gap-4 ${generatedImages.length === 2 ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1 md:grid-cols-3'}`}>
                  {generatedImages.map((img, index) => (
                    <div 
                      key={index}
                      className={`relative rounded-lg overflow-hidden border-2 transition-all cursor-pointer ${
                        selectedImageIndex === index 
                          ? 'border-green-500 ring-2 ring-green-500/30' 
                          : 'border-gray-200 hover:border-primary/50'
                      }`}
                      onClick={() => handleSelectImage(index)}
                    >
                      <img 
                        src={img} 
                        alt={`Design option ${index + 1}`}
                        className="w-full aspect-square object-contain bg-white"
                      />
                      <div className="absolute top-2 left-2">
                        <Badge className={selectedImageIndex === index ? 'bg-green-500' : 'bg-black/70'}>
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
                      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/90 to-transparent">
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="secondary"
                            className="flex-1 h-8 text-xs"
                            disabled={loading}
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
                              downloadImage(img, index);
                            }}
                          >
                            <Download className="h-3 w-3" />
                          </Button>
                          {selectedTool.supportsCustomerBranding && brandingCustomerId && (
                            <Button
                              size="sm"
                              variant="secondary"
                              className="h-8 text-xs"
                              disabled={savingToBrandingProfile}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSaveLogoToProfile(
                                  img,
                                  `${selectedTool.name} concept #${index + 1} for ${formData.business_name || 'customer'}`
                                );
                              }}
                              title="Save this concept to the customer's Branding Profile"
                              data-testid={`save-logo-to-profile-btn-${index}`}
                            >
                              <Palette className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Modification Request */}
                {selectedImageIndex !== null && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-3 border border-green-500/30">
                    <Label>Request Changes to Option {selectedImageIndex + 1}</Label>
                    <Textarea
                      value={formData.modification_notes || ''}
                      onChange={(e) => handleFieldChange('modification_notes', e.target.value)}
                      placeholder="Describe changes... e.g., 'Make text larger', 'Use darker blue', 'Add more contrast'"
                      rows={2}
                    />
                    <Button 
                      onClick={() => handleRegenerateImage(selectedImageIndex)}
                      variant="outline"
                      disabled={loading}
                      className="border-green-500/50 text-green-400 hover:bg-green-500/10"
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Apply Changes & Regenerate
                    </Button>
                  </div>
                )}

                {/* Design Brief / Notes shown with images */}
                {result && selectedTool.generatesImages && (
                  <div className="mt-4 border-t border-gray-200 pt-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-heading uppercase text-sm text-primary flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        {(selectedTool.id === 'ai_sign_designer' || selectedTool.id === 'ai_banner_designer')
                          ? 'Design Brief'
                          : 'Design Notes & Rationale'}
                      </h4>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => copyToClipboard(result.content || result.output)}
                      >
                        <Copy className="h-4 w-4 mr-2" /> Copy
                      </Button>
                    </div>
                    <ScrollArea className="h-[300px]">
                      <div className="prose prose-invert max-w-none">
                        <pre className="whitespace-pre-wrap text-sm font-sans bg-gray-50 p-4 rounded-lg">
                          {result.content || result.output}
                        </pre>
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Text Result - Only show for non-image tools */}
          {result && !selectedTool.generatesImages && (
            <Card className="bg-white border-gray-200 border-primary/30" data-testid="result-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading uppercase text-sm text-primary">
                    {selectedTool.generatesImages ? 'Design Notes & Guidance' : 'Result'}
                  </CardTitle>
                  <div className="flex gap-2 flex-wrap justify-end">
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => copyToClipboard(result.content || result.output)}
                      data-testid="copy-result-btn"
                    >
                      <Copy className="h-4 w-4 mr-2" /> Copy
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleGeneratePdf}
                      disabled={generatingPdf}
                      data-testid="download-pdf-btn"
                    >
                      {generatingPdf ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileDown className="h-4 w-4 mr-2" />}
                      Download PDF
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={handleSaveToLibrary}
                      disabled={savingToLibrary}
                      data-testid="save-to-library-btn"
                    >
                      {savingToLibrary ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FolderPlus className="h-4 w-4 mr-2" />}
                      Save to Library
                    </Button>
                    {selectedTool.supportsCustomerBranding && brandingCustomerId && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={
                          selectedTool.id === 'branding_kit_generator'
                            ? handleSaveBrandKitToProfile
                            : () => handleSaveTaglineToProfile(result.content || result.output, false)
                        }
                        disabled={savingToBrandingProfile}
                        data-testid="save-to-branding-profile-btn"
                        className="text-purple-700 hover:bg-purple-50"
                      >
                        {savingToBrandingProfile ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Palette className="h-4 w-4 mr-2" />
                        )}
                        Save to Branding Profile
                      </Button>
                    )}
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => setShowSendDialog(true)}
                      className="border-primary text-primary hover:bg-primary/10"
                      data-testid="send-to-portal-btn"
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Send to Customer
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="prose prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-sm font-sans bg-gray-50 p-4 rounded-lg">
                      {result.content || result.output}
                    </pre>
                  </div>
                </ScrollArea>
                <p className="text-xs text-gray-500 mt-4">
                  Generated at {formatDateTime(result.created_at)}
                </p>
              </CardContent>
            </Card>
          )}

          {/* History Panel */}
          {showHistory && (
            <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
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
                  <p className="text-gray-500 text-center py-8">No history found for this tool</p>
                ) : (
                  <ScrollArea className="h-[300px]">
                    <div className="space-y-3">
                      {history.map((item) => (
                        <div 
                          key={item.id} 
                          className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-50/50 transition-colors"
                          onClick={() => {
                            setResult(item);
                            setShowHistory(false);
                          }}
                        >
                          <p className="text-sm font-medium truncate">
                            {JSON.stringify(item.input_data).slice(0, 100)}...
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
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

      {/* Send to Customer Portal Dialog */}
      <Dialog open={showSendDialog} onOpenChange={setShowSendDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="h-5 w-5 text-primary" />
              Send to Customer Portal
            </DialogTitle>
            <DialogDescription>
              Save this document and send it directly to a customer's portal.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Customer</Label>
              <Select value={selectedCustomerId} onValueChange={setSelectedCustomerId}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a customer..." />
                </SelectTrigger>
                <SelectContent>
                  {customers?.filter(c => c.portal_enabled).map((customer) => (
                    <SelectItem key={customer.id} value={customer.id}>
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-500" />
                        {customer.name}
                        {customer.company && <span className="text-gray-500">({customer.company})</span>}
                      </div>
                    </SelectItem>
                  ))}
                  {customers?.filter(c => c.portal_enabled).length === 0 && (
                    <div className="px-2 py-4 text-center text-sm text-gray-500">
                      No customers with portal access enabled.
                      <br />
                      <span className="text-xs">Enable portal access in customer settings.</span>
                    </div>
                  )}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Message (optional)</Label>
              <Textarea
                value={sendMessage}
                onChange={(e) => setSendMessage(e.target.value)}
                placeholder="Add a message for your customer..."
                rows={3}
              />
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="notify-customer"
                checked={notifyCustomer}
                onChange={(e) => setNotifyCustomer(e.target.checked)}
                className="rounded border-gray-300"
              />
              <Label htmlFor="notify-customer" className="text-sm font-normal cursor-pointer">
                Send email notification to customer
              </Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSendDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSendToPortal}
              disabled={sendingToPortal || !selectedCustomerId}
              className="bg-primary"
            >
              {sendingToPortal ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send to Portal
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
