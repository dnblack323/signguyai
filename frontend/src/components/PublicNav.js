import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X } from 'lucide-react';

// Simplified nav - Founders Edition only
// Legacy nav config saved at: /src/config/legacyNavConfig.js
const navLinks = [
  { href: '/features', label: 'Features' },
  { href: '/why-founder', label: 'Why Be a Founder' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/docs', label: 'Docs' },
];

export function PublicNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (href) => location.pathname === href;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center">
            <img 
              src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
              alt="SignGuy AI" 
              className="h-8 w-auto" 
            />
          </Link>
          
          {/* Desktop Nav - Simplified */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={`px-4 py-2 text-sm font-medium transition rounded-md ${
                  isActive(link.href)
                    ? 'text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
            
            <div className="ml-4 flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost" className="!text-gray-400 hover:!text-white hover:!bg-white/10 text-sm">
                  Log In
                </Button>
              </Link>
              <Link to="/register">
                <Button className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-black font-semibold text-sm">
                  Get Founders Edition
                </Button>
              </Link>
            </div>
          </div>

          {/* Mobile menu button */}
          <button 
            className="md:hidden text-white p-2" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav - Simplified */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#111826] border-t border-white/10 p-4">
          <div className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`px-4 py-2 text-sm ${
                  isActive(link.href) ? 'text-amber-400' : 'text-gray-300'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-4 pt-4 border-t border-white/10">
              <Link 
                to="/login" 
                className="block px-4 py-2 text-sm text-gray-300"
                onClick={() => setMobileMenuOpen(false)}
              >
                Log In
              </Link>
              <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full mt-2 bg-gradient-to-r from-amber-500 to-orange-500 text-black font-semibold">
                  Get Founders Edition
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

export function PublicFooter() {
  return (
    <footer className="bg-[#0a0a0a] border-t border-white/10 py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Product */}
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2">
              <li><Link to="/features" className="text-gray-400 hover:text-white text-sm">Features</Link></li>
              <li><Link to="/pricing" className="text-gray-400 hover:text-white text-sm">Pricing</Link></li>
            </ul>
          </div>
          
          {/* Get Started */}
          <div>
            <h4 className="text-white font-semibold mb-4">Get Started</h4>
            <ul className="space-y-2">
              <li><Link to="/register" className="text-gray-400 hover:text-white text-sm">Sign Up</Link></li>
              <li><Link to="/login" className="text-gray-400 hover:text-white text-sm">Log In</Link></li>
            </ul>
          </div>
          
          {/* Portals */}
          <div>
            <h4 className="text-white font-semibold mb-4">Portals</h4>
            <ul className="space-y-2">
              <li><Link to="/customer-portal/login" className="text-gray-400 hover:text-white text-sm">Customer Portal</Link></li>
              <li><Link to="/employee-portal/login" className="text-gray-400 hover:text-white text-sm">Employee Portal</Link></li>
            </ul>
          </div>
          
          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><Link to="/privacy" className="text-gray-400 hover:text-white text-sm">Privacy Policy</Link></li>
              <li><Link to="/terms" className="text-gray-400 hover:text-white text-sm">Terms of Service</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <img 
            src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
            alt="SignGuy AI" 
            className="h-8 w-auto" 
          />
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} SignGuy AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

export default PublicNav;
