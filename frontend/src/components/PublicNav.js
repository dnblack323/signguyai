import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X } from 'lucide-react';

const navLinks = [
  { href: '/features', label: 'Features' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/about', label: 'About' },
  { href: '/contact', label: 'Contact' },
  { href: '/docs', label: 'Docs' },
];

export function PublicNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (href) => location.pathname === href;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
              alt="SignGuy AI" 
              className="h-14 w-auto" 
            />
          </Link>
          
          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={`transition ${
                  isActive(link.href)
                    ? 'text-[#2F8BFB] font-medium'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link to="/login">
              <Button variant="ghost" className="text-gray-300 hover:text-white">
                Log In
              </Button>
            </Link>
            <Link to="/login">
              <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0] text-white font-semibold">
                Start Free Trial
              </Button>
            </Link>
          </div>

          {/* Mobile menu button */}
          <button 
            className="md:hidden text-white p-2" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#111826] border-t border-white/10 p-4 animate-fade-in">
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`py-2 ${
                  isActive(link.href)
                    ? 'text-[#2F8BFB] font-medium'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link 
              to="/login" 
              className="text-gray-300 hover:text-white py-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              Log In
            </Link>
            <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
              <Button className="w-full bg-[#2F8BFB] hover:bg-[#1E7AF0] text-white font-semibold">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

export function PublicFooter() {
  return (
    <footer className="bg-[#0a0a0a] border-t border-white/10 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Product */}
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2">
              <li><Link to="/features" className="text-gray-400 hover:text-white transition">Features</Link></li>
              <li><Link to="/pricing" className="text-gray-400 hover:text-white transition">Pricing</Link></li>
              <li><Link to="/docs" className="text-gray-400 hover:text-white transition">Documentation</Link></li>
            </ul>
          </div>
          
          {/* Company */}
          <div>
            <h4 className="text-white font-semibold mb-4">Company</h4>
            <ul className="space-y-2">
              <li><Link to="/about" className="text-gray-400 hover:text-white transition">About Us</Link></li>
              <li><Link to="/contact" className="text-gray-400 hover:text-white transition">Contact</Link></li>
            </ul>
          </div>
          
          {/* Portals */}
          <div>
            <h4 className="text-white font-semibold mb-4">Portals</h4>
            <ul className="space-y-2">
              <li><Link to="/login" className="text-gray-400 hover:text-white transition">Sign In</Link></li>
              <li><Link to="/customer-portal/login" className="text-gray-400 hover:text-white transition">Customer Portal</Link></li>
              <li><Link to="/employee-portal/login" className="text-gray-400 hover:text-white transition">Employee Portal</Link></li>
            </ul>
          </div>
          
          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white transition">Privacy Policy</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white transition">Terms of Service</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <img 
              src="https://customer-assets.emergentagent.com/job_10abf0c0-fdcf-4656-8194-dcbb0dcb1efc/artifacts/k3asaz65_sgai%20long.png" 
              alt="SignGuy AI" 
              className="h-10 w-auto" 
            />
          </div>
          <p className="text-gray-500 text-sm">
            © {new Date().getFullYear()} SignGuy AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

export default PublicNav;
