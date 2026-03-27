import { ArrowLeft, Package, FileText, Wrench, Calculator, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function DocsOrdersTickets() {
  return (
    <div className="max-w-4xl mx-auto">
      <Link to="/docs" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-900 mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Docs
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Orders & Job Tickets</h1>
      <p className="text-gray-500 mb-8">The 4-layer production workflow system</p>

      <div className="space-y-8">
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Package className="w-5 h-5 text-violet-600" /> How It Works</h2>
          <p className="text-gray-700 mb-3">SignGuy AI uses a 4-layer system that mirrors how a real sign shop operates:</p>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <p className="font-medium text-gray-900">Layer 1: Order — The master container for a customer's request</p>
            <p className="ml-4 text-gray-600">Layer 2: Job Tickets — Individual production items within an order</p>
            <p className="ml-8 text-gray-600">Layer 3: Quotes / Invoices — Financial documents generated from tickets</p>
            <p className="ml-8 text-gray-600">Layer 4: Production Tasks — Department-level workflow stages</p>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Layers className="w-5 h-5 text-violet-600" /> Creating an Order</h2>
          <ol className="list-decimal pl-6 space-y-2 text-gray-700">
            <li>Go to <strong>Orders → + New Order</strong></li>
            <li>Search or enter customer information</li>
            <li>Upload any artwork, drawings, or reference files</li>
            <li>Add job tickets using <strong>Quick Entry</strong> (fast, simple) or <strong>Detailed Entry</strong> (full specs + calculator)</li>
            <li>Click <strong>Save Order</strong></li>
          </ol>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Job Ticket Entry Modes</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Quick Entry</h3>
              <p className="text-sm text-gray-600">For fast intake. Item name, category, quantity, price, and description. No calculator needed. Can be expanded to Detailed Entry later.</p>
            </div>
            <div className="bg-violet-50 rounded-lg p-4 border border-violet-200">
              <h3 className="font-semibold text-violet-900 mb-2">Detailed Entry</h3>
              <p className="text-sm text-violet-700">Full category-specific form with dynamic fields, settings-driven material options, and live pricing calculator. Shows real-time price estimate.</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Calculator className="w-5 h-5 text-violet-600" /> Categories</h2>
          <p className="text-gray-700 mb-3">Each category loads its own form fields:</p>
          <div className="grid md:grid-cols-2 gap-3">
            {[
              { name: 'Banners', desc: 'Width, height, material, hems, grommets, pole pockets, wind slits' },
              { name: 'Rigid Signs', desc: 'Substrate, thickness, stakes, mounting hardware, lamination, drill holes' },
              { name: 'Cut Vinyl', desc: 'Vinyl type, colors, layered/single, weed, mask, inside/outside mount' },
              { name: 'Digital Print', desc: 'Media type, roll/sheet, print quality, lamination, mounting, contour cut' },
              { name: 'Vehicle Wrap', desc: 'Vehicle type, coverage level, areas covered, install difficulty, paneling' },
              { name: 'Apparel', desc: 'Garment type, brand, size breakdown (XS-5XL), decoration method, print locations with per-location details' },
            ].map(c => (
              <div key={c.name} className="bg-gray-50 rounded-lg p-3">
                <p className="font-medium text-gray-900">{c.name}</p>
                <p className="text-xs text-gray-500 mt-1">{c.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText className="w-5 h-5 text-violet-600" /> Order Actions</h2>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li><strong>Generate Quote</strong> — creates a financial quote from job tickets</li>
            <li><strong>Generate Invoice</strong> — creates an invoice from job tickets</li>
            <li><strong>Generate Work Order</strong> — creates a production document with full specs</li>
            <li><strong>Email Quote/Invoice</strong> — sends to customer via email</li>
            <li><strong>Start Production</strong> — activates workflow for all enabled tickets</li>
            <li><strong>Status Change</strong> — quick status update (Approved, In Production, Ready, etc.)</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3 flex items-center gap-2"><Wrench className="w-5 h-5 text-violet-600" /> Production Workflow</h2>
          <p className="text-gray-700 mb-3">When a job ticket has workflow enabled, the system auto-generates production tasks based on the category template:</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li>6 default templates (Rigid Signs 11 stages, Banners 12, Cut Vinyl 8, Vehicle Wrap 14, Apparel 11, Promo 5)</li>
            <li>Each task has: department, status, assigned employee, timestamps</li>
            <li>Task controls: Start, Complete, Pause, On Hold, Rework</li>
            <li>Progress automatically rolls up: tasks → ticket → order</li>
            <li>Production Board shows all tasks grouped by department</li>
            <li>Admin can customize templates in Settings → Workflow Templates</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Pricing</h2>
          <p className="text-gray-700 mb-3">All pricing comes from your settings (Settings → Materials & Pricing):</p>
          <ul className="list-disc pl-6 space-y-1 text-gray-700">
            <li>Material costs, labor rates, markup, overhead — all configurable</li>
            <li>Live estimate updates as you fill in the form</li>
            <li>Calculator mode (from settings) or Manual mode (override)</li>
            <li>Pricing snapshots preserved on each ticket</li>
            <li>Apparel quantity discounts: 12+ (5%), 24+ (10%), 48+ (15%), 72+ (20%), 144+ (25%)</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
