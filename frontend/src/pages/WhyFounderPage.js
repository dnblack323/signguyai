import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Brain, DollarSign, Users, Calendar, Briefcase, FileText,
  Store, Palette, MessageSquare, BarChart3, Clock, CheckCircle2,
  ArrowRight, Crown, Zap, Target, TrendingUp, Shield, Cpu,
  ClipboardList, FolderOpen, Sparkles, Layers, Eye, AlertTriangle
} from 'lucide-react';

export default function WhyFounderPage() {
  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      {/* Hero Section */}
      <section className="pt-20 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <Badge className="mb-6 bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30 px-4 py-1.5">
            <Crown className="w-4 h-4 mr-2" />
            Founder Access - Limited to 100 Shops
          </Badge>
          
          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Turn Your Sign Shop Into an<br />
            <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">Intelligent System.</span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Founder access to the first AI-powered operating system built specifically for sign shops — 
            combining employee tracking, customer portals, smart pricing analysis, workflow intelligence, 
            and advanced AI design tools in one connected platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold px-8 py-6 text-lg h-auto">
                Apply for Founder Access
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 px-8 py-6 text-lg h-auto bg-transparent">
                See Founder Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="py-12 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-[#111826] rounded-xl border border-white/10">
              <Briefcase className="w-8 h-8 text-amber-400 mb-3" />
              <p className="font-semibold text-white">Job Stages</p>
              <p className="text-xs text-gray-500">Visual production tracking</p>
            </div>
            <div className="p-4 bg-[#111826] rounded-xl border border-white/10">
              <Clock className="w-8 h-8 text-blue-400 mb-3" />
              <p className="font-semibold text-white">Time Tracking</p>
              <p className="text-xs text-gray-500">Employee hours per job</p>
            </div>
            <div className="p-4 bg-[#111826] rounded-xl border border-white/10">
              <Brain className="w-8 h-8 text-purple-400 mb-3" />
              <p className="font-semibold text-white">AI Insights</p>
              <p className="text-xs text-gray-500">Intelligent analysis</p>
            </div>
            <div className="p-4 bg-[#111826] rounded-xl border border-white/10">
              <DollarSign className="w-8 h-8 text-green-400 mb-3" />
              <p className="font-semibold text-white">Pricing Analyzer</p>
              <p className="text-xs text-gray-500">Margin validation</p>
            </div>
          </div>
          <p className="text-center text-sm text-gray-500 mt-4">
            Not just pretty UI. <span className="text-amber-400">Show intelligence.</span>
          </p>
        </div>
      </section>

      {/* The Real Problem */}
      <section className="py-20 px-4 bg-gradient-to-b from-red-900/10 to-transparent">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-4 bg-red-500/20 text-red-400 border-red-500/30">
              <AlertTriangle className="w-3 h-3 mr-1" />
              The Real Problem
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Most Shops Track Work.<br />
              <span className="text-red-400">Very Few Understand It.</span>
            </h2>
          </div>

          <div className="bg-[#111826] rounded-2xl p-8 border border-red-500/20">
            <p className="text-lg text-gray-300 mb-6">
              You know jobs are getting done.<br />
              <span className="text-white font-semibold">But do you know:</span>
            </p>
            
            <ul className="space-y-3 mb-8">
              {[
                "Which jobs actually make you money?",
                "Which employee tasks consume the most time?",
                "Where installs slow down?",
                "If your pricing is aligned with your real labor costs?",
                "If your margins are slipping without you noticing?"
              ].map((item, idx) => (
                <li key={idx} className="flex items-start gap-3 text-gray-400">
                  <span className="text-red-400 mt-1">•</span>
                  {item}
                </li>
              ))}
            </ul>

            <div className="flex flex-col md:flex-row gap-4 p-4 bg-[#0B0F17] rounded-xl">
              <div className="flex-1 text-center p-4">
                <p className="text-gray-500 text-sm">Most shops run on</p>
                <p className="text-xl font-bold text-red-400">Instinct</p>
              </div>
              <div className="hidden md:block w-px bg-gray-700" />
              <div className="flex-1 text-center p-4">
                <p className="text-gray-500 text-sm">Founder shops run on</p>
                <p className="text-xl font-bold text-amber-400">Data</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* What Makes This Different */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              This Isn't Just Software.<br />
              <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">It Learns Your Shop.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Intelligent Workforce Tracking */}
            <Card className="bg-[#111826] border-purple-500/30">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
                    <Brain className="w-6 h-6 text-purple-400" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Intelligent Workforce Tracking</h3>
                </div>
                
                <ul className="space-y-2 mb-6">
                  {[
                    "Employee portal with job assignments",
                    "Real-time time tracking",
                    "Job-stage production tracking",
                    "Labor time feeding into AI cost analysis",
                    "Workflow bottleneck detection"
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-400 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-purple-400 mt-0.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                  <p className="text-sm">
                    <span className="text-purple-400 font-semibold">Founder Advantage:</span>
                    <span className="text-gray-300"> Your shop becomes measurable. Not guesswork.</span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Intelligent Pricing */}
            <Card className="bg-[#111826] border-green-500/30">
              <CardContent className="p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-green-400" />
                  </div>
                  <h3 className="text-xl font-bold text-white">Intelligent Pricing & Profit Analysis</h3>
                </div>
                
                <ul className="space-y-2 mb-6">
                  {[
                    "Custom pricing calculators by sign category",
                    "Market-aware pricing analyzer",
                    "Margin validation",
                    "Real labor cost integration",
                    "Install time estimator"
                  ].map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-400 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                  <p className="text-sm">
                    <span className="text-green-400 font-semibold">Founder Advantage:</span>
                    <span className="text-gray-300"> Know exactly what you're making — not what you think you're making.</span>
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Operations & Productivity Core */}
      <section className="py-20 px-4 bg-[#111826]/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/20 text-blue-400 border-blue-500/30">
              Operations & Productivity Core
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Run the Shop. Not Just the Jobs.
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              AI helps you move faster. Operations tools help you stay organized.
              SignGuy AI includes a full productivity and workflow control system built specifically for sign shops.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Payroll & Time Intelligence */}
            <div className="p-6 bg-[#0B0F17] rounded-xl border border-white/10">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-6 h-6 text-blue-400" />
                <h4 className="font-bold text-white">Payroll & Time Intelligence</h4>
              </div>
              <ul className="space-y-2 text-sm text-gray-400 mb-4">
                <li>• Employee time tracking per job</li>
                <li>• Labor hours feeding into cost analysis</li>
                <li>• Track productivity by role</li>
                <li>• Time-based cost reporting</li>
                <li>• Payroll-ready data exports</li>
              </ul>
              <p className="text-xs text-blue-400">
                <strong>Founder Advantage:</strong> You don't just track time. You understand labor efficiency.
              </p>
            </div>

            {/* Smart Scheduling */}
            <div className="p-6 bg-[#0B0F17] rounded-xl border border-white/10">
              <div className="flex items-center gap-3 mb-4">
                <Calendar className="w-6 h-6 text-amber-400" />
                <h4 className="font-bold text-white">Smart Scheduling Calendar</h4>
              </div>
              <ul className="space-y-2 text-sm text-gray-400 mb-4">
                <li>• Schedule installs</li>
                <li>• Assign jobs to employees</li>
                <li>• See workload by day or week</li>
                <li>• Avoid overbooking</li>
                <li>• Sync workflow with production stages</li>
              </ul>
              <p className="text-xs text-amber-400">
                <strong>Founder Advantage:</strong> Clear visibility prevents bottlenecks before they happen.
              </p>
            </div>

            {/* Job Board */}
            <div className="p-6 bg-[#0B0F17] rounded-xl border border-white/10">
              <div className="flex items-center gap-3 mb-4">
                <Layers className="w-6 h-6 text-purple-400" />
                <h4 className="font-bold text-white">Drag-and-Drop Job Board</h4>
              </div>
              <ul className="space-y-2 text-sm text-gray-400 mb-4">
                <li>• Visual production tracking</li>
                <li>• Move jobs through stages</li>
                <li>• See exactly where each job is</li>
                <li>• Track how long it stays in each stage</li>
                <li>• Identify slowdowns instantly</li>
              </ul>
              <p className="text-xs text-purple-400">
                <strong>Founder Advantage:</strong> Production becomes measurable, not mysterious.
              </p>
            </div>

            {/* Productivity Tools */}
            <div className="p-6 bg-[#0B0F17] rounded-xl border border-white/10">
              <div className="flex items-center gap-3 mb-4">
                <ClipboardList className="w-6 h-6 text-green-400" />
                <h4 className="font-bold text-white">Productivity Tools Built for Shops</h4>
              </div>
              <ul className="space-y-2 text-sm text-gray-400 mb-4">
                <li>• Drag-and-drop to-do system</li>
                <li>• Task assignment</li>
                <li>• Internal notes</li>
                <li>• Job production tracking</li>
                <li>• Attach documents directly to jobs</li>
              </ul>
              <p className="text-xs text-green-400">
                <strong>Founder Advantage:</strong> No more scattered reminders or lost job notes.
              </p>
            </div>
          </div>

          {/* Webstore System */}
          <div className="mt-8 p-8 bg-[#0B0F17] rounded-xl border border-amber-500/30">
            <div className="flex items-center gap-3 mb-4">
              <Store className="w-8 h-8 text-amber-400" />
              <h4 className="text-xl font-bold text-white">Webstore System</h4>
            </div>
            <div className="grid md:grid-cols-3 gap-4 mb-4">
              <div className="text-sm text-gray-400">• Create custom webstores</div>
              <div className="text-sm text-gray-400">• B2B storefronts</div>
              <div className="text-sm text-gray-400">• Fundraiser stores</div>
              <div className="text-sm text-gray-400">• Control product categories</div>
              <div className="text-sm text-gray-400">• Track orders connected to jobs</div>
              <div className="text-sm text-gray-400">• Integrated with customer portal</div>
            </div>
            <p className="text-amber-400 font-medium">
              Founder Advantage: Recurring revenue without managing separate platforms.
            </p>
          </div>

          <div className="mt-8 text-center p-6 bg-gradient-to-r from-amber-500/10 to-orange-500/10 rounded-xl border border-amber-500/20">
            <p className="text-lg text-gray-300">
              This isn't separate software stitched together.<br />
              <span className="text-white font-semibold">It's one connected system</span> where labor, pricing, workflow, payroll, and AI intelligence all feed into each other.
            </p>
          </div>
        </div>
      </section>

      {/* Portal System */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <FolderOpen className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Complete Portal System</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card className="bg-[#111826] border-blue-500/30">
              <CardContent className="p-6">
                <h4 className="font-bold text-blue-400 mb-4">Customer Portal</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• Approve artwork</li>
                  <li>• Pay invoices</li>
                  <li>• Fill design questionnaires</li>
                  <li>• Access documents</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-[#111826] border-green-500/30">
              <CardContent className="p-6">
                <h4 className="font-bold text-green-400 mb-4">Employee Portal</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• View assigned jobs</li>
                  <li>• Track time</li>
                  <li>• Monitor tasks</li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-[#111826] border-purple-500/30">
              <CardContent className="p-6">
                <h4 className="font-bold text-purple-400 mb-4">Virtual Document Library</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• Attach inspection sheets to jobs</li>
                  <li>• Store safety forms</li>
                  <li>• Send install instructions</li>
                  <li>• Keep records organized</li>
                </ul>
              </CardContent>
            </Card>
          </div>

          <p className="text-center text-amber-400 mt-6">
            <strong>Founder Advantage:</strong> No more scattered documents or lost communication.
          </p>
        </div>
      </section>

      {/* AI Design Lab */}
      <section className="py-20 px-4 bg-gradient-to-b from-purple-900/20 to-transparent">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Palette className="w-12 h-12 text-purple-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Advanced AI Design & Creation Lab</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="p-6 bg-[#111826] rounded-xl border border-purple-500/30">
              <h4 className="font-bold text-white mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-400" />
                Current Tools
              </h4>
              <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
                <div>• Vectorizer</div>
                <div>• Font identification</div>
                <div>• Text-to-image style transfer</div>
                <div>• Pattern generation</div>
                <div>• Logo refresher</div>
                <div>• Photo enhancements</div>
                <div>• Mock-up tool</div>
                <div>• Banner designer</div>
                <div>• Sign designer</div>
                <div>• Generative fill</div>
              </div>
            </div>

            <div className="p-6 bg-[#111826] rounded-xl border border-amber-500/30">
              <h4 className="font-bold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                In Progress
              </h4>
              <div className="space-y-3 text-gray-400">
                <div className="p-3 bg-amber-500/10 rounded-lg">
                  <p className="font-medium text-amber-400">Advanced Wrap Module</p>
                  <p className="text-xs">Vehicle wrap design intelligence</p>
                </div>
                <div className="p-3 bg-amber-500/10 rounded-lg">
                  <p className="font-medium text-amber-400">Advanced Race Car Design Module</p>
                  <p className="text-xs">Specialized racing graphics tools</p>
                </div>
              </div>
              <p className="text-amber-400 text-sm mt-4">
                <strong>Founder Advantage:</strong> First access to advanced wrap intelligence tools before public launch.
              </p>
            </div>
          </div>

          <p className="text-center text-lg text-gray-300 mt-8">
            This is no longer "AI tools." <span className="text-purple-400 font-semibold">It's an ecosystem.</span>
          </p>
        </div>
      </section>

      {/* AI Business Brain */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <Brain className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">The AI Business Brain</h2>
            <p className="text-xl text-gray-400">Ask Your Shop Questions. Get Real Answers.</p>
          </div>

          <Card className="bg-[#111826] border-amber-500/30">
            <CardContent className="p-8">
              <p className="text-gray-300 mb-6">Your AI Business Assistant can:</p>
              <div className="grid md:grid-cols-3 gap-3 mb-6">
                {[
                  "Analyze pricing decisions",
                  "Summarize logo questionnaires",
                  "Generate business documents",
                  "Research permits",
                  "Draft policies",
                  "Create contracts",
                  "Generate ad campaigns",
                  "Build content calendars",
                  "Write blog posts",
                  "Create social media posts",
                  "Brainstorm business ideas"
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-gray-400">
                    <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
              <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20 text-center">
                <p className="text-amber-400 font-medium">
                  Founder Advantage: You don't just use tools. You have a business co-pilot.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Production Intelligence */}
      <section className="py-20 px-4 bg-[#111826]/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <Eye className="w-12 h-12 text-blue-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Production Intelligence</h2>
            <p className="text-xl text-gray-400">Know Exactly Where Every Job Stands.</p>
          </div>

          <div className="p-8 bg-[#0B0F17] rounded-xl border border-blue-500/30">
            <p className="text-gray-300 mb-6">
              Drag-and-drop task management. Production stage tracking. Time spent in each phase recorded automatically.
            </p>
            
            <p className="text-white font-semibold mb-4">See:</p>
            <ul className="space-y-2 mb-6">
              {[
                "Which stage slows jobs down",
                "Where installs take longer than estimated",
                "Which types of jobs eat time",
                "How to optimize workflow"
              ].map((item, idx) => (
                <li key={idx} className="flex items-center gap-2 text-gray-400">
                  <Target className="w-4 h-4 text-blue-400" />
                  {item}
                </li>
              ))}
            </ul>

            <p className="text-blue-400 font-medium">
              Founder shops don't just complete jobs. They refine the system.
            </p>
          </div>
        </div>
      </section>

      {/* Why Founder Access Matters */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <Crown className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Why Founder Access Matters Now</h2>
            <p className="text-xl text-gray-400">We're Opening Founder Access Before Public Launch.</p>
          </div>

          <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/30">
            <CardContent className="p-8">
              <p className="text-white font-semibold mb-4">Founder shops:</p>
              <ul className="space-y-3 mb-8">
                {[
                  "Lock in permanent discounted pricing",
                  "Get early access to advanced AI modules",
                  "Influence workflow development",
                  "Shape pricing logic improvements",
                  "Get direct communication during rollout"
                ].map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3 text-gray-300">
                    <CheckCircle2 className="w-5 h-5 text-amber-400" />
                    {item}
                  </li>
                ))}
              </ul>

              <div className="p-4 bg-[#0B0F17] rounded-lg text-center">
                <p className="text-gray-400 mb-2">Public release pricing will be higher.</p>
                <p className="text-amber-400 font-semibold text-lg">Founder rates are permanent while active.</p>
                <p className="text-gray-500 text-sm mt-2">No hype. Just math.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4 bg-gradient-to-b from-amber-900/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            The Shops That Measure, <span className="text-amber-400">Win.</span>
          </h2>
          
          <p className="text-lg text-gray-400 mb-8 max-w-2xl mx-auto">
            The future isn't just AI art. It's intelligent pricing. Measured labor. Optimized workflow. 
            Connected portals. And AI-assisted decision-making.
          </p>

          <p className="text-xl text-white font-semibold mb-8">
            Founder shops get there first.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold px-8 py-6 text-lg h-auto">
                Apply for Founder Access
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 px-8 py-6 text-lg h-auto bg-transparent">
                See Founder Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
