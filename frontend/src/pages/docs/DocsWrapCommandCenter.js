import { Link } from 'react-router-dom';
import { ArrowRight, Car, Ruler, DollarSign, Palette, FileText, CheckSquare, Camera, Wrench, Sparkles, Zap, CheckCircle } from 'lucide-react';

export default function DocsWrapCommandCenter() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Car className="h-4 w-4" /> Vehicle Wrap Management
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Wrap Command Center</h1>
        <p className="text-lg text-gray-400">
          The Wrap Command Center is your all-in-one hub for managing vehicle wrap projects from quote to completion. 
          Every wrap-related order item gets its own command center with 12 specialized tabs covering every aspect of the wrap workflow.
        </p>
      </div>

      {/* How to Access */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5 text-cyan-400" /> How to Access
        </h2>
        <ol className="space-y-2 text-gray-300">
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">1</span>
            Open any order that contains a vehicle wrap order item
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">2</span>
            Click the <strong className="text-white">"Open Wrap Center"</strong> button on the wrap order item
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">3</span>
            The Wrap Command Center opens with all project details and tabs
          </li>
        </ol>
      </div>

      {/* What Makes It Special */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">What Makes It Special</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-white/5 border border-gray-700">
            <CheckCircle className="h-5 w-5 text-green-400 mb-2" />
            <h3 className="font-semibold text-white mb-1">Unified Workflow</h3>
            <p className="text-sm text-gray-400">
              Everything for one wrap project lives in one place - no more jumping between different tools or spreadsheets.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-gray-700">
            <CheckCircle className="h-5 w-5 text-green-400 mb-2" />
            <h3 className="font-semibold text-white mb-1">Auto-Save</h3>
            <p className="text-sm text-gray-400">
              Changes are automatically saved as you work. The header shows save status in real-time.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-gray-700">
            <CheckCircle className="h-5 w-5 text-green-400 mb-2" />
            <h3 className="font-semibold text-white mb-1">Built-in Checklists</h3>
            <p className="text-sm text-gray-400">
              Phase-specific checklists ensure nothing gets missed from pre-production through aftercare.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-gray-700">
            <CheckCircle className="h-5 w-5 text-green-400 mb-2" />
            <h3 className="font-semibold text-white mb-1">AI Assistant Built-In</h3>
            <p className="text-sm text-gray-400">
              Get instant help, recommendations, and automated tasks without leaving the command center.
            </p>
          </div>
        </div>
      </div>

      {/* The 12 Tabs */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-6">The 12 Tabs</h2>
        
        <div className="space-y-4">
          {/* Overview */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                <CheckSquare className="h-5 w-5 text-cyan-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">1. Overview</h3>
                <p className="text-gray-400 mb-3">
                  High-level project summary, quick actions, and status at a glance. See order details, customer info, and current phase.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Quick Actions</span>
                  <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Phase Summary</span>
                  <span className="text-xs px-2 py-1 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Key Metrics</span>
                </div>
              </div>
            </div>
          </div>

          {/* Vehicle Info */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                <Car className="h-5 w-5 text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">2. Vehicle Info</h3>
                <p className="text-gray-400 mb-3">
                  Complete vehicle details: year, make, model, VIN, color, condition notes, and mileage. Track vehicle-specific requirements and notes.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Auto-Save</span>
                  <span className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">VIN Lookup</span>
                  <span className="text-xs px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Condition Log</span>
                </div>
              </div>
            </div>
          </div>

          {/* Measurements */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                <Ruler className="h-5 w-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">3. Measurements</h3>
                <p className="text-gray-400 mb-3">
                  Record precise measurements for every panel and section. Calculate total material needed. Interactive vehicle diagram helps visualize coverage areas.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">Panel-by-Panel</span>
                  <span className="text-xs px-2 py-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">Material Calculator</span>
                  <span className="text-xs px-2 py-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">Visual Diagram</span>
                </div>
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <DollarSign className="h-5 w-5 text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">4. Pricing</h3>
                <p className="text-gray-400 mb-3">
                  Detailed cost breakdown: materials, labor, design, prep, extras. Compare quote vs. actual costs. Track profitability.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20">Cost Breakdown</span>
                  <span className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20">Profit Tracking</span>
                  <span className="text-xs px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20">Quote Generation</span>
                </div>
              </div>
            </div>
          </div>

          {/* Design */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-pink-500/20 flex items-center justify-center flex-shrink-0">
                <Palette className="h-5 w-5 text-pink-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">5. Design</h3>
                <p className="text-gray-400 mb-3">
                  Design file management, approval workflow, revision tracking, and design notes. Upload mockups, proofs, and final artwork.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">File Upload</span>
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">Approval Tracking</span>
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">Revision History</span>
                </div>
              </div>
            </div>
          </div>

          {/* Contract */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                <FileText className="h-5 w-5 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">6. Contract</h3>
                <p className="text-gray-400 mb-3">
                  Contract terms, customer signature, deposit tracking, and agreement details. Generate contract PDFs and track sign-off.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Digital Signature</span>
                  <span className="text-xs px-2 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Terms & Conditions</span>
                  <span className="text-xs px-2 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Deposit Status</span>
                </div>
              </div>
            </div>
          </div>

          {/* Inspection */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                <CheckSquare className="h-5 w-5 text-orange-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">7. Inspection</h3>
                <p className="text-gray-400 mb-3">
                  Pre-installation inspection checklist. Document existing damage, paint condition, body defects. Photo documentation.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">Damage Log</span>
                  <span className="text-xs px-2 py-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">Photo Upload</span>
                  <span className="text-xs px-2 py-1 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">Condition Report</span>
                </div>
              </div>
            </div>
          </div>

          {/* Production */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-teal-500/20 flex items-center justify-center flex-shrink-0">
                <Wrench className="h-5 w-5 text-teal-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">8. Production</h3>
                <p className="text-gray-400 mb-3">
                  Material ordering, print queue management, plotter settings, lamination tracking. Track each production phase from print to lamination.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">Print Tracking</span>
                  <span className="text-xs px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">Material Log</span>
                  <span className="text-xs px-2 py-1 rounded bg-teal-500/10 text-teal-400 border border-teal-500/20">Quality Control</span>
                </div>
              </div>
            </div>
          </div>

          {/* Install */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                <Car className="h-5 w-5 text-indigo-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">9. Install</h3>
                <p className="text-gray-400 mb-3">
                  Installation schedule, team assignments, installation notes, time tracking. Document installation progress and completion.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Schedule</span>
                  <span className="text-xs px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Team Assignment</span>
                  <span className="text-xs px-2 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Time Log</span>
                </div>
              </div>
            </div>
          </div>

          {/* Photos & Files */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-rose-500/20 flex items-center justify-center flex-shrink-0">
                <Camera className="h-5 w-5 text-rose-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">10. Photos & Files</h3>
                <p className="text-gray-400 mb-3">
                  Centralized media library for the wrap project. Upload and organize before/during/after photos, reference images, and related documents.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Before/After Photos</span>
                  <span className="text-xs px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">File Management</span>
                  <span className="text-xs px-2 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Gallery View</span>
                </div>
              </div>
            </div>
          </div>

          {/* Aftercare */}
          <div className="p-5 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <CheckCircle className="h-5 w-5 text-emerald-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">11. Aftercare</h3>
                <p className="text-gray-400 mb-3">
                  Warranty information, care instructions, follow-up schedule. Set reminders for maintenance checks and warranty renewals.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Warranty Tracking</span>
                  <span className="text-xs px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Care Guide</span>
                  <span className="text-xs px-2 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Follow-up Schedule</span>
                </div>
              </div>
            </div>
          </div>

          {/* AI Assistant */}
          <div className="p-5 rounded-lg bg-white/5 border border-pink-500/30 hover:border-pink-500/50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-pink-500/20 to-purple-500/20 flex items-center justify-center flex-shrink-0">
                <Sparkles className="h-5 w-5 text-pink-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-2">12. AI Assistant</h3>
                <p className="text-gray-400 mb-3">
                  Context-aware AI help specific to this wrap project. Get instant answers, recommendations, and automated suggestions based on your project data.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">Project Context</span>
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">Smart Recommendations</span>
                  <span className="text-xs px-2 py-1 rounded bg-pink-500/10 text-pink-400 border border-pink-500/20">Instant Help</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Benefits */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20">
        <h2 className="text-xl font-bold text-white mb-4">Why Shops Love the Wrap Command Center</h2>
        <div className="grid md:grid-cols-2 gap-4 text-gray-300">
          <div className="flex gap-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Reduced Errors:</strong> Built-in checklists and guided workflows ensure nothing gets forgotten
            </div>
          </div>
          <div className="flex gap-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Faster Onboarding:</strong> New team members can follow the structured tabs without extensive training
            </div>
          </div>
          <div className="flex gap-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Better Profitability:</strong> Track actual vs. quoted costs to improve future pricing
            </div>
          </div>
          <div className="flex gap-3">
            <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white">Professional Documentation:</strong> Complete project records for warranty and customer history
            </div>
          </div>
        </div>
      </div>

      {/* Related Links */}
      <div className="border-t border-gray-700 pt-8">
        <h3 className="text-lg font-semibold text-white mb-4">Related Documentation</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <Link
            to="/docs/quotes-jobs"
            className="p-4 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors flex items-center gap-3 group"
          >
            <div className="text-gray-400 group-hover:text-cyan-400 transition-colors">
              <ArrowRight className="h-5 w-5" />
            </div>
            <div>
              <div className="font-medium text-white group-hover:text-cyan-400 transition-colors">Orders & Production</div>
              <div className="text-sm text-gray-500">How orders feed into wrap projects</div>
            </div>
          </Link>
          <Link
            to="/docs/ai-tools"
            className="p-4 rounded-lg bg-white/5 border border-gray-700 hover:border-cyan-500/50 transition-colors flex items-center gap-3 group"
          >
            <div className="text-gray-400 group-hover:text-cyan-400 transition-colors">
              <ArrowRight className="h-5 w-5" />
            </div>
            <div>
              <div className="font-medium text-white group-hover:text-cyan-400 transition-colors">AI Tools</div>
              <div className="text-sm text-gray-500">AI assistance throughout your wrap workflow</div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
