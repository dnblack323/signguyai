import { Link } from 'react-router-dom';
import { Store, ArrowRight, ShoppingBag, Globe, Settings, DollarSign, Package } from 'lucide-react';

export default function DocsWebstores() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-medium mb-2">
          <Store className="h-4 w-4" />
          Advanced Features
        </div>
        <h1 className="text-3xl font-bold text-white mb-4">Webstores</h1>
        <p className="text-lg text-gray-400">
          Create online stores for fundraisers, B2B customers, or public product catalogs. Let customers order directly without phone calls or emails.
        </p>
      </div>

      <div className="p-6 rounded-xl bg-gray-900/50 border border-gray-800">
        <h2 className="text-lg font-semibold text-white mb-4">Store Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { type: 'Fundraiser Store', desc: 'Perfect for schools, sports teams, and organizations', color: 'bg-green-500' },
            { type: 'B2B Portal', desc: 'Private ordering for business customers with custom pricing', color: 'bg-blue-500' },
            { type: 'Public Catalog', desc: 'Open store for anyone to browse and order products', color: 'bg-purple-500' },
          ].map((item) => (
            <div key={item.type} className="p-4 rounded-lg bg-gray-800/50">
              <div className={`w-3 h-3 rounded-full ${item.color} mb-2`} />
              <span className="text-white font-medium">{item.type}</span>
              <p className="text-gray-400 text-sm mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Creating a Webstore</h2>
        <ol className="space-y-4">
          {[
            { title: 'Navigate to Webstores', desc: 'Click "Webstores" in the sidebar navigation' },
            { title: 'Click New Store', desc: 'Click the "New Store" button to start the setup wizard' },
            { title: 'Choose Store Type', desc: 'Select Fundraiser, B2B Portal, or Public Catalog' },
            { title: 'Configure Settings', desc: 'Set store name, description, and branding options' },
            { title: 'Add Products', desc: 'Select which products to include in this store' },
            { title: 'Set Pricing', desc: 'Configure prices (can be different from your standard pricing)' },
            { title: 'Publish', desc: 'Click Publish to make your store live' },
          ].map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-400 text-sm flex items-center justify-center">{i + 1}</span>
              <div>
                <strong className="text-white">{step.title}</strong>
                <p className="text-gray-400">{step.desc}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Store Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: Globe, title: 'Custom URL', desc: 'Each store gets a unique shareable link' },
            { icon: ShoppingBag, title: 'Product Selection', desc: 'Choose which products appear in each store' },
            { icon: DollarSign, title: 'Custom Pricing', desc: 'Set different prices per store or use your defaults' },
            { icon: Package, title: 'Order Management', desc: 'All orders flow into your main job queue' },
            { icon: Settings, title: 'Branding', desc: 'Add your logo and customize colors' },
            { icon: Store, title: 'Inventory', desc: 'Optional stock tracking per product' },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-lg bg-gray-800/30">
              <item.icon className="h-5 w-5 text-cyan-400 mt-0.5" />
              <div>
                <strong className="text-white">{item.title}</strong>
                <p className="text-gray-400 text-sm">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-6 rounded-xl bg-cyan-500/10 border border-cyan-500/30">
        <h3 className="text-white font-semibold mb-2">Pro Tip: Fundraiser Stores</h3>
        <p className="text-gray-300">
          For fundraiser stores, you can set a deadline and goal amount. Supporters can see progress toward the goal, which increases engagement and orders.
        </p>
      </div>

      <div className="flex items-center justify-between pt-8 border-t border-gray-800">
        <Link to="/docs/employees" className="text-gray-400 hover:text-white">
          ← Employee Management
        </Link>
        <Link to="/docs/customer-portal" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300">
          Customer Portal <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
