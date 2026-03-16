import { Link } from 'react-router-dom';
import { ArrowRight, Image, Palette, FileText, Share2, Sparkles } from 'lucide-react';

const categories = [
  { name: 'Design & Image', icon: Image, tools: ['Logo Refresher', 'Generative Fill / Image Expander', 'Text to Image Creator', 'AI Sign Designer', 'AI Banner Designer', 'Mockup Creator', 'Vehicle Wrap Mockup', 'Logo Creator', 'Photo Enhancer', 'Vectorization Analyzer', 'Font Identifier'] },
  { name: 'Branding', icon: Palette, tools: ['Idea Brainstormer', 'Branding Kit Generator', 'Brand Color Advisor', 'Brand Voice Guide', 'Tagline Generator'] },
  { name: 'Business & Writing', icon: FileText, tools: ['Business Assistant', 'Business Copywriter', 'Document Composer', 'Pricing Intelligence', 'Proposal Writer', 'Review Responder', 'Email Templates', 'SEO Content'] },
  { name: 'Marketing & Social', icon: Share2, tools: ['Blog Creator', 'Completed Job Post Creator', 'Social Job Post Creator', 'Social Pack Generator', 'Content Calendar', 'Campaign Builder', 'Showcase Post'] },
];

export default function DocsAITools() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-pink-400 text-sm font-medium mb-2"><Sparkles className="h-4 w-4" /> Advanced Features</div>
        <h1 className="text-3xl font-bold text-white mb-4">AI Tools & Credit Usage</h1>
        <p className="text-lg text-gray-400">SignGuy AI uses AI in multiple places: visual generation, writing tools, product description generation, pricing guidance, historical invoice analysis, and assistant workflows.</p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">How AI Credits Work</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Low compute actions use 1 credit</li>
          <li>• Medium compute actions use 2 credits</li>
          <li>• High compute actions use 3 credits</li>
          <li>• Monthly credits are used before purchased credits</li>
          <li>• Credits are deducted only after successful AI execution</li>
          <li>• The system can show a confirmation popup with cost and balance before running the tool</li>
        </ul>
      </div>

      {categories.map((category) => (
        <div key={category.name}>
          <div className="flex items-center gap-2 mb-4">
            <category.icon className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl font-semibold text-white">{category.name}</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {category.tools.map((tool) => (
              <div key={tool} className="p-3 rounded-lg bg-gray-800/50 text-gray-300 text-sm">{tool}</div>
            ))}
          </div>
        </div>
      ))}

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">AI Outside the AI Tools Page</h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Product Description Generator inside Products</li>
          <li>• AI Pricing Advisor inside Pricing Calculator</li>
          <li>• AI Email Composer in invoice/quote communication flows</li>
          <li>• AI Business Assistant page and Floating Assistant</li>
          <li>• Historical invoice AI analysis inside Pricing Setup</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/pricing-calculator" className="text-gray-400 hover:text-white">← Pricing Calculator</Link>
        <Link to="/docs/time-tracking" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Time Tracking <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
