import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, Image, Palette, FileText, Share2 } from 'lucide-react';

const toolCategories = [
  {
    name: 'Design Tools',
    icon: Image,
    color: 'text-blue-400',
    tools: [
      'Logo Refresher - Upload logo, get modern style variations',
      'Generative Fill - Expand images with AI',
      'Text to Image Creator - Generate images from prompts',
      'Vehicle Wrap Mockup - See designs on vehicles',
      'Photo Enhancer - Improve image quality',
      'Vectorization Analyzer - Convert to vector',
      'Font Identifier - Identify fonts from images',
      'AI Sign Designer - Generate sign concepts',
      'AI Banner Designer - Create banner designs',
      'Mockup Creator - Product mockups'
    ]
  },
  {
    name: 'Branding',
    icon: Palette,
    color: 'text-purple-400',
    tools: [
      'Idea Brainstormer - Taglines, logo concepts, business names',
      'Logo Creator - Generate logo concepts',
      'Branding Kit Generator - Complete brand packages'
    ]
  },
  {
    name: 'Business',
    icon: FileText,
    color: 'text-green-400',
    tools: [
      'Sign Permit Research - Permit guidance for any location',
      'AI Business Assistant - Chat interface for sign shop questions',
      'Business Copywriter - Professional copy',
      'Document Composer - Contracts and proposals',
      'Pricing Intelligence - Market pricing insights'
    ]
  },
  {
    name: 'Marketing',
    icon: Share2,
    color: 'text-pink-400',
    tools: [
      'Blog Article Creator - Full blog articles with SEO',
      'Completed Job Post Creator - Social content from job photos',
      'Social Media Job Post - Showcase work on social',
      'Social Media Pack Generator - Content bundles',
      'Content Calendar Creator - Plan your content',
      'Campaign Builder - Marketing campaigns'
    ]
  }
];

export default function DocsAITools() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-pink-400 text-sm font-medium mb-2">
          <Sparkles className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">AI Tools Suite</h1>
        <p className="text-lg text-gray-400">
          Explore 24+ AI-powered tools for design, branding, business operations, and marketing.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="h-6 w-6 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">How to Access</h2>
        </div>
        <p className="text-gray-300">
          Navigate to <strong className="text-white">AI Tools</strong> from the sidebar to access all tools. 
          Select a category to filter, then choose a tool to start generating content.
        </p>
      </div>

      {toolCategories.map((category) => {
        const Icon = category.icon;
        return (
          <div key={category.name}>
            <div className="flex items-center gap-2 mb-4">
              <Icon className={`h-5 w-5 ${category.color}`} />
              <h2 className="text-xl font-semibold text-white">{category.name}</h2>
              <span className="text-sm text-gray-500">({category.tools.length} tools)</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {category.tools.map((tool, i) => (
                <div key={i} className="p-3 rounded-lg bg-gray-800/50 text-gray-300 text-sm">
                  {tool}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Image Generation Tools</h2>
        <p className="text-gray-300 mb-4">
          Several tools generate images using AI. Look for the badge that shows how many images will be created:
        </p>
        <div className="p-4 rounded-lg bg-gray-800/50">
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
            <Image className="h-3 w-3" /> Generates 3 Images
          </span>
          <p className="text-gray-400 text-sm mt-2">
            Image tools will create multiple variations for you to choose from.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/pricing-calculator" className="text-gray-400 hover:text-white">
          ← Pricing Calculator
        </Link>
        <Link to="/docs/time-tracking" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Time Tracking <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
