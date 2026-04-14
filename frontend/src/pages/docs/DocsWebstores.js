import { Link } from 'react-router-dom';
import { ArrowRight, Store, ShoppingCart, CreditCard, Package, Settings, Globe, Tag, Image, Truck } from 'lucide-react';

export default function DocsWebstores() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Store className="h-4 w-4" /> Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Webstores</h1>
        <p className="text-lg text-gray-400">
          Webstores let you sell products online, route orders into jobs, and use Stripe Connect for checkout when enabled.
        </p>
      </div>

      {/* Screenshot */}
      <div className="rounded-xl overflow-hidden border border-gray-700">
        <img 
          src="/screenshots/feature_webstores.jpeg" 
          alt="Webstore Manager" 
          className="w-full"
        />
        <div className="bg-gray-800/80 px-4 py-2 text-xs text-gray-400">
          Webstore Manager showing stores, sales, and store types
        </div>
      </div>

      {/* What's Included */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Package className="h-5 w-5 text-cyan-400" /> What a Webstore Includes
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <Globe className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Store branding and public URL</span>
            </li>
            <li className="flex items-start gap-2">
              <Tag className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Selected products from master catalog</span>
            </li>
            <li className="flex items-start gap-2">
              <CreditCard className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Optional price overrides per store</span>
            </li>
          </ul>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <ShoppingCart className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Customer checkout flow</span>
            </li>
            <li className="flex items-start gap-2">
              <Package className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Auto-create jobs from orders</span>
            </li>
            <li className="flex items-start gap-2">
              <Truck className="h-4 w-4 text-cyan-400 mt-1 flex-shrink-0" />
              <span>Order tracking for customers</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Creating a Webstore */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Store className="h-5 w-5 text-cyan-400" /> Creating a Webstore
        </h2>
        <ol className="space-y-3">
          {[
            'Go to Webstores in the main navigation',
            'Click "+ New Webstore" button',
            'Enter store name and customize URL slug',
            'Upload a logo and set brand colors',
            'Add products from your master product list',
            'Set any store-specific price overrides',
            'Enable Stripe checkout (if connected)',
            'Publish the store'
          ].map((step, index) => (
            <li key={step} className="flex items-start gap-3 text-gray-300">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{index + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      {/* Products Setup */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Tag className="h-5 w-5 text-cyan-400" /> Products Setup
        </h2>
        <p className="text-gray-300 mb-3">Before creating a webstore, set up your products:</p>
        <ul className="space-y-2 text-gray-300">
          <li>• Go to <strong className="text-white">Products</strong> in the main nav</li>
          <li>• Add products with: name, description, base price, images</li>
          <li>• Set up variants (size, color, etc.) if needed</li>
          <li>• Configure inventory tracking (optional)</li>
          <li>• Products can be added to multiple webstores</li>
        </ul>
      </div>

      {/* Store Appearance */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Image className="h-5 w-5 text-cyan-400" /> Store Appearance
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-white mb-2">Branding Options</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Store logo upload</li>
              <li>• Primary brand color</li>
              <li>• Banner/hero image</li>
              <li>• Store description text</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-white mb-2">Layout Features</h3>
            <ul className="space-y-1 text-sm text-gray-300">
              <li>• Product grid display</li>
              <li>• Category filtering</li>
              <li>• Search functionality</li>
              <li>• Mobile-responsive design</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Checkout & Payments */}
      <div className="p-6 rounded-xl bg-gradient-to-r from-green-500/20 to-cyan-500/20 border border-green-500/30">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-green-400" /> Checkout & Payments
        </h2>
        <p className="text-gray-300 mb-3">When Stripe Connect is enabled:</p>
        <ul className="space-y-2 text-gray-300">
          <li>• Customers can pay directly at checkout</li>
          <li>• Secure payment processing via Stripe</li>
          <li>• Automatic receipt and confirmation emails</li>
          <li>• Orders automatically create order items</li>
          <li>• Payment status syncs with invoice records</li>
        </ul>
      </div>

      {/* Best Practice */}
      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5 text-cyan-400" /> Best Practices
        </h2>
        <ul className="space-y-2 text-gray-300">
          <li>• Use the <strong className="text-white">Products</strong> module to maintain reusable product data</li>
          <li>• Use <strong className="text-white">Webstores</strong> to decide which products each store exposes</li>
          <li>• Set up multiple stores for different customer segments or event types</li>
          <li>• Use store-specific pricing for promotional or volume deals</li>
          <li>• Test checkout flow before sharing the store URL</li>
        </ul>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/employees" className="text-gray-400 hover:text-white">← Employees</Link>
        <Link to="/docs/customer-portal" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">Customer Portal <ArrowRight className="h-4 w-4" /></Link>
      </div>
    </div>
  );
}
