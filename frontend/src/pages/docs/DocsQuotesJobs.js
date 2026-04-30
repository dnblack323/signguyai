import { ArrowLeft, Package, FileText, Wrench, Calculator, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DocsOrdersTickets() {
  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/docs" className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Docs
      </Link>

      <h1 className="text-3xl font-bold text-white mb-2">Orders & Order Items</h1>
      <p className="text-gray-400 mb-8">The 4-layer production workflow system</p>

      <div className="space-y-8">
        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><Package className="w-5 h-5 text-cyan-400" /> How It Works</h2>
          <p className="text-gray-300 mb-3">SignGuy AI uses a 4-layer system that mirrors how a real sign shop operates:</p>
          <div className="bg-gray-800/50 rounded-lg p-4 space-y-2 border border-gray-700">
            <p className="font-medium text-white">Layer 1: Order — The master container for a customer's request</p>
            <p className="ml-4 text-gray-400">Layer 2: Order Items — Individual production items within an order</p>
            <p className="ml-8 text-gray-400">Layer 3: Quotes / Invoices — Financial documents generated from order items</p>
            <p className="ml-8 text-gray-400">Layer 4: Production Tasks — Department-level workflow stages</p>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><Layers className="w-5 h-5 text-cyan-400" /> Creating an Order</h2>
          <ol className="list-decimal pl-6 space-y-2 text-gray-300">
            <li>Go to <strong className="text-white">Orders → + New Order</strong></li>
            <li>Search or enter customer information</li>
            <li>Upload any artwork, drawings, or reference files</li>
            <li>Add order items using <strong className="text-white">Quick Entry</strong> (fast, simple) or <strong className="text-white">Detailed Entry</strong> (full specs + calculator)</li>
            <li>Click <strong className="text-white">Save Order</strong></li>
          </ol>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">Order Item Entry Modes</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <h3 className="font-semibold text-white mb-2">Quick Entry</h3>
              <p className="text-sm text-gray-400">For fast intake. Item name, category, quantity, price, and description. No calculator needed. Can be expanded to Detailed Entry later.</p>
            </div>
            <div className="bg-cyan-900/30 rounded-lg p-4 border border-cyan-700/50">
              <h3 className="font-semibold text-cyan-300 mb-2">Detailed Entry</h3>
              <p className="text-sm text-cyan-200/70">Full category-specific form with dynamic fields, settings-driven material options, and live pricing calculator. Shows real-time price estimate.</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><Calculator className="w-5 h-5 text-cyan-400" /> Categories</h2>
          <p className="text-gray-300 mb-3">Each category loads its own form fields:</p>
          <div className="grid md:grid-cols-2 gap-3">
            {[
              { name: 'Banners', desc: 'Width, height, material, hems, grommets, pole pockets, wind slits' },
              { name: 'Rigid Signs', desc: 'Substrate, thickness, stakes, mounting hardware, lamination, drill holes' },
              { name: 'Cut Vinyl', desc: 'Vinyl type, colors, layered/single, weed, mask, inside/outside mount' },
              { name: 'Digital Print', desc: 'Media type, roll/sheet, print quality, lamination, mounting, contour cut' },
              { name: 'Vehicle Wrap', desc: 'Vehicle type, coverage level, areas covered, install difficulty, paneling' },
              { name: 'Apparel', desc: 'Garment type, brand, size breakdown (XS-5XL), decoration method, print locations with per-location details' },
            ].map(c => (
              <div key={c.name} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                <p className="font-medium text-white">{c.name}</p>
                <p className="text-xs text-gray-400 mt-1">{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><FileText className="w-5 h-5 text-cyan-400" /> Order Actions</h2>
          <ul className="list-disc pl-6 space-y-1 text-gray-300">
            <li><strong className="text-white">Generate Quote</strong> — creates a financial quote from order items</li>
            <li><strong className="text-white">Generate Invoice</strong> — creates an invoice from order items</li>
            <li><strong className="text-white">Generate Work Order</strong> — creates a production document with full specs</li>
            <li><strong className="text-white">Email Quote/Invoice</strong> — sends to customer via email</li>
            <li><strong className="text-white">Start Production</strong> — activates workflow for all enabled order items</li>
            <li><strong className="text-white">Status Change</strong> — quick status update (Approved, In Production, Ready, etc.)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><Wrench className="w-5 h-5 text-cyan-400" /> Production Workflow</h2>
          <p className="text-gray-300 mb-3">When an order item has workflow enabled, the system auto-generates production tasks based on the category template:</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-300">
            <li>6 default templates (Rigid Signs 11 stages, Banners 12, Cut Vinyl 8, Vehicle Wrap 14, Apparel 11, Promo 5)</li>
            <li>Each task has: department, status, assigned employee, timestamps</li>
            <li>Task controls: Start, Complete, Pause, On Hold, Rework</li>
            <li>Progress automatically rolls up: tasks → order item → order</li>
            <li>Production Board shows all tasks grouped by department</li>
            <li>Admin can customize templates in Settings → Workflow Templates</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3">Pricing</h2>
          <p className="text-gray-300 mb-3">All pricing comes from your settings (Settings → Materials & Pricing):</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-300">
            <li>Material costs, labor rates, markup, overhead — all configurable</li>
            <li>Live estimate updates as you fill in the form</li>
            <li>Calculator mode (from settings) or Manual mode (override)</li>
            <li>Pricing snapshots preserved on each order item</li>
            <li>Apparel quantity discounts: 12+ (5%), 24+ (10%), 48+ (15%), 72+ (20%), 144+ (25%)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-white mb-3 flex items-center gap-2"><Layers className="w-5 h-5 text-cyan-400" /> Signatures & Drawings</h2>
          <p className="text-gray-300 mb-3">Orders support in-app signature capture and whiteboard drawings:</p>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
              <h3 className="font-semibold text-white mb-2">Signature Capture</h3>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• Capture customer signatures on tablet or desktop</li>
                <li>• Records signer name, timestamp, and IP address</li>
                <li>• View full signature history on any order</li>
                <li>• Send signature requests via email link</li>
                <li>• Supports quote approvals, order authorizations, delivery confirmations</li>
              </ul>
            </div>
            <div className="bg-cyan-900/30 rounded-lg p-4 border border-cyan-700/50">
              <h3 className="font-semibold text-cyan-300 mb-2">Order Drawings (Whiteboard)</h3>
              <ul className="text-sm text-cyan-200/70 space-y-1">
                <li>• Create sketches, measurement notes, install diagrams</li>
                <li>• Tools: pen, arrow, circle, text with colors and sizes</li>
                <li>• Autosaves as you draw</li>
                <li>• Multiple drawings per order</li>
                <li>• Works with mouse or finger on mobile</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
