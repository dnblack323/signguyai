import { Link } from 'react-router-dom';
import { ArrowRight, Image, Palette, FileText, Share2, Sparkles, Zap, CheckCircle, HelpCircle, Coins } from 'lucide-react';

const categories = [
  {
    name: 'Design Tools',
    icon: Image,
    tools: [
      { name: 'Photo Enhancer Analyzer', desc: 'Upload a photo and get an enhancement plan + verdict (Approved / Needs Fixing / Not Usable)' },
      { name: 'Vectorization Analyzer', desc: 'Check whether an image is a good candidate for vector conversion before sending it to your designer' },
      { name: 'Font Identifier', desc: 'Upload an image of text and get the most likely matching fonts' },
      { name: 'AI Sign Designer', desc: 'Generates AI sign concept images PLUS a written design brief (direction, colors, readability, production notes)' },
      { name: 'AI Banner Designer', desc: 'Generates AI banner concept images PLUS a written design brief (layout, readability, material/finish notes)' },
      { name: 'Mockup Creator', desc: 'AI-rendered concept mockups of a described design in real environments. The AI illustrates your description; it does not place the customer\'s actual artwork.' },
      { name: 'Vehicle Wrap Mockup Generator', desc: 'AI-rendered concept mockups of a wrap idea across vehicle types' },
      { name: 'AI Image Concept Creator', desc: 'Generate AI concept images from a text description for inspiration or rough creative direction. NOT print-ready production artwork.' },
    ]
  },
  {
    name: 'Branding',
    icon: Palette,
    tools: [
      { name: 'Idea Brainstormer', desc: 'Generate brand ideas, names, taglines from a brief' },
      { name: 'Branding Kit Generator', desc: 'Full brand identity package (palette, type, voice). Saves directly to a customer\'s Branding Profile when one is attached.' },
      { name: 'Logo Creator', desc: 'AI logo concepts. Saves directly to the attached customer\'s Branding Profile.' },
    ]
  },
  {
    name: 'Business & Writing',
    icon: FileText,
    tools: [
      { name: 'Business Assistant', desc: 'Ask questions about sign shop operations' },
      { name: 'Business Copywriter', desc: 'Generate professional copy for any use' },
      { name: 'Proposal Writer', desc: 'Create project proposals and pitches' },
      { name: 'Review Responder', desc: 'Draft responses to customer reviews' },
      { name: 'Email Templates', desc: 'Generate professional email templates' },
    ]
  },
  {
    name: 'Marketing & Social',
    icon: Share2,
    tools: [
      { name: 'Blog Creator', desc: 'Write blog posts about your work' },
      { name: 'Completed Order Post Creator', desc: 'One tool, two modes: pick "With Image" to attach a photo of the finished work, or "Text Only" for a quick description-based post. Replaces the old separate "Social Order Post" tool.' },
      { name: 'Social Media Pack Generator', desc: 'Generate 5–30 numbered post ideas with caption, visual suggestion, platform fit and hashtags. Required: services + pack size; new fields: brand voice, target platforms.' },
      { name: 'Content Calendar Creator', desc: 'Builds an actual day-by-day calendar from your start date, frequency and brand voice. Output is a YYYY-MM-DD | Theme | Platform | Idea | CTA table plus a production checklist.' },
    ]
  },
  {
    name: 'Racing & Motorsports',
    icon: Sparkles,
    tools: [
      { name: 'Race Number Designer', desc: 'AI-rendered raster concept images of racing numbers. Final cut/print artwork may need vectorization.' },
      { name: 'Driver Name Plate Generator', desc: 'AI raster concept images of driver name plates and roof strips' },
      { name: 'Race Team Branding Kit', desc: 'AI raster brand-kit concepts PLUS a written racing branding brief (logo direction, number design, colors, sponsor placement, merchandise, production file notes)' },
    ]
  },
];

export default function DocsAITools() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-pink-400 text-sm font-medium mb-2">
          <Sparkles className="h-4 w-4" /> Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">AI Tools & Credit Usage</h1>
        <p className="text-lg text-gray-400">
          SignGuy AI uses AI in multiple places: visual generation, writing tools, product description generation, pricing guidance, historical invoice analysis, and assistant workflows.
        </p>
      </div>

      {/* Screenshot */}
      <div className="rounded-xl overflow-hidden border border-gray-700">
        <img 
          src="/screenshots/feature_ai_tools.jpeg" 
          alt="AI Tools Interface" 
          className="w-full"
        />
        <div className="bg-gray-800/80 px-4 py-2 text-xs text-gray-400">
          AI Tools page with categories and tool selection
        </div>
      </div>

      {/* How to Access */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/30">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5 text-pink-400" /> How to Access AI Tools
        </h2>
        <ol className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">1</span>
            Click <strong className="text-white">AI Tools</strong> in the main navigation
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">2</span>
            Browse categories or search for a specific tool
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">3</span>
            Click on a tool to open its interface
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">4</span>
            Enter your prompt or upload required files
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-pink-500/20 text-pink-400 text-sm flex items-center justify-center">5</span>
            Click <strong className="text-white">Generate</strong> and wait for results
          </li>
        </ol>
      </div>

      {/* Credit System */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Coins className="h-5 w-5 text-amber-400" /> How AI Credits Work
        </h2>
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          <div className="bg-green-500/10 rounded-lg p-3 border border-green-500/30 text-center">
            <p className="text-2xl font-bold text-green-400">1</p>
            <p className="text-sm text-gray-400">Credit</p>
            <p className="text-xs text-gray-500 mt-1">Low compute (text)</p>
          </div>
          <div className="bg-amber-500/10 rounded-lg p-3 border border-amber-500/30 text-center">
            <p className="text-2xl font-bold text-amber-400">2</p>
            <p className="text-sm text-gray-400">Credits</p>
            <p className="text-xs text-gray-500 mt-1">Medium compute</p>
          </div>
          <div className="bg-red-500/10 rounded-lg p-3 border border-red-500/30 text-center">
            <p className="text-2xl font-bold text-red-400">3</p>
            <p className="text-sm text-gray-400">Credits</p>
            <p className="text-xs text-gray-500 mt-1">High compute (images)</p>
          </div>
        </div>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span>Monthly credits are used before purchased credits</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span>Credits are deducted only after successful AI execution</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span>Confirmation popup shows cost and balance before running</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-green-400 mt-1 flex-shrink-0" />
            <span>Purchase more credits anytime from Billing settings</span>
          </li>
        </ul>
      </div>

      {/* Recently Updated */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-emerald-500/15 to-cyan-500/15 border border-emerald-500/30">
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-emerald-300" /> What's new in AI Tools
        </h2>
        <ul className="space-y-2 text-gray-200 text-sm">
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">AI Sign / Banner Designer + Race Team Branding Kit</strong> now also produce a <em>written design brief</em> (direction, colors, readability, production notes) alongside the images — no extra credit cost.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Customer Branding Profile</strong> integration — open a customer → Branding tab → click "Create Brand Kit / Logo Concepts / Brainstorm Ideas" and the AI tool opens with that customer pre-attached. Generated outputs save back to their profile automatically.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Completed Order Post Creator</strong> merged the old "Social Order Post" tool — pick "With Image" or "Text Only" mode to choose the workflow.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Content Calendar Creator</strong> now takes a real start date + posting frequency and outputs a day-by-day table you can paste straight into a planner.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Document Library auto-tagging</strong> — when you click "Save to Library" on an AI output, it lands in the right category automatically (logo concept, brand kit, social post, content calendar, blog article, etc.).</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-300 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Wording cleanup:</strong> AI image tools now clearly say "concept image" — they're a starting point, not print-ready production artwork. The two tools that didn't actually use uploaded images (Logo Refresher, Generative Fill) are hidden until true image-to-image works.</span>
          </li>
        </ul>
      </div>

      {/* Tool Categories */}
      {categories.map((category) => (
        <div key={category.name} className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center gap-2 mb-4">
            <category.icon className="h-5 w-5 text-cyan-400" />
            <h2 className="text-xl font-semibold text-white">{category.name}</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {category.tools.map((tool) => (
              <div key={tool.name} className="p-3 rounded-lg bg-gray-800/50 border border-gray-700">
                <p className="font-medium text-white">{tool.name}</p>
                <p className="text-xs text-gray-400 mt-1">{tool.desc}</p>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* AI Outside Tools Page */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <HelpCircle className="h-5 w-5 text-cyan-400" /> AI Throughout the App
        </h2>
        <p className="text-gray-300 mb-3">AI is also available in these other areas:</p>
        <ul className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Product Description Generator</strong> — Auto-generate descriptions in Products</span>
          </li>
          <li className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">AI Pricing Advisor</strong> — Get pricing suggestions in the Calculator</span>
          </li>
          <li className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">AI Email Composer</strong> — Draft emails for invoices/quotes</span>
          </li>
          <li className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Floating Assistant</strong> — Get help anywhere in the app</span>
          </li>
          <li className="flex items-start gap-2">
            <Sparkles className="h-4 w-4 text-pink-400 mt-1 flex-shrink-0" />
            <span><strong className="text-white">Invoice Analysis</strong> — AI analyzes historical data for pricing insights</span>
          </li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/pricing-calculator" className="text-gray-400 hover:text-white">← Pricing Calculator</Link>
        <Link to="/docs/time-tracking" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Time Tracking <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
