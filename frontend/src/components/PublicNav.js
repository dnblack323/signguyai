import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { Menu, X, ChevronDown } from 'lucide-react';

const navLinks = [
  { 
    href: '/platform', 
    label: 'Platform',
    dropdown: [
      { href: '/platform', label: 'Overview' },
      { href: '/starter', label: 'Starter' },
      { href: '/pro', label: 'Pro' },
      { href: '/business', label: 'Business' },
    ]
  },
  { href: '/webstores', label: 'Webstores' },
  { href: '/ai-studio', label: 'AI Studio' },
  { href: '/pricing', label: 'Pricing' },
];

export function PublicNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState(null);
  const location = useLocation();
  const dropdownRef = useRef(null);

  const isActive = (href) => location.pathname === href;

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpenDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
          
          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1" ref={dropdownRef}>
            {navLinks.map((link) => (
              link.dropdown ? (
                <div key={link.href} className="relative">
                  <button
                    onClick={() => setOpenDropdown(openDropdown === link.href ? null : link.href)}
                    className={`flex items-center gap-1 px-4 py-2 text-sm font-medium transition rounded-md ${
                      isActive(link.href) || link.dropdown.some(d => isActive(d.href))
                        ? 'text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    {link.label}
                    <ChevronDown className={`h-4 w-4 transition-transform ${openDropdown === link.href ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {openDropdown === link.href && (
                    <div className="absolute top-full left-0 mt-1 w-40 bg-[#111826] border border-white/10 rounded-lg shadow-xl py-1">
                      {link.dropdown.map((item) => (
                        <Link
                          key={item.href}
                          to={item.href}
                          onClick={() => setOpenDropdown(null)}
                          className={`block px-4 py-2 text-sm transition ${
                            isActive(item.href)
                              ? 'text-blue-400 bg-blue-500/10'
                              : 'text-gray-400 hover:text-white hover:bg-white/5'
                          }`}
                        >
                          {item.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
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
              )
            ))}
            
            <div className="ml-4 flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost" className="text-gray-400 hover:text-white text-sm">
                  Log In
                </Button>
              </Link>
              <Link to="/login">
                <Button className="bg-blue-600 hover:bg-blue-700 text-white text-sm">
                  Start Free Trial
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

      {/* Mobile Nav */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#111826] border-t border-white/10 p-4">
          <div className="flex flex-col gap-1">
            {navLinks.map((link) => (
              link.dropdown ? (
                <div key={link.href}>
                  <p className="px-4 py-2 text-xs font-medium text-gray-500 uppercase">{link.label}</p>
                  {link.dropdown.map((item) => (
                    <Link
                      key={item.href}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`block px-4 py-2 text-sm ${
                        isActive(item.href) ? 'text-blue-400' : 'text-gray-300'
                      }`}
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              ) : (
                <Link
                  key={link.href}
                  to={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-4 py-2 text-sm ${
                    isActive(link.href) ? 'text-blue-400' : 'text-gray-300'
                  }`}
                >
                  {link.label}
                </Link>
              )
            ))}
            <div className="mt-4 pt-4 border-t border-white/10">
              <Link 
                to="/login" 
                className="block px-4 py-2 text-sm text-gray-300"
                onClick={() => setMobileMenuOpen(false)}
              >
                Log In
              </Link>
              <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white">
                  Start Free Trial
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
          {/* Products */}
          <div>
            <h4 className="text-white font-semibold mb-4">Products</h4>
            <ul className="space-y-2">
              <li><Link to="/platform" className="text-gray-400 hover:text-white text-sm">Platform</Link></li>
              <li><Link to="/webstores" className="text-gray-400 hover:text-white text-sm">Webstores</Link></li>
              <li><Link to="/ai-studio" className="text-gray-400 hover:text-white text-sm">AI Studio</Link></li>
              <li><Link to="/pricing" className="text-gray-400 hover:text-white text-sm">Pricing</Link></li>
            </ul>
          </div>
          
          {/* OS Plans */}
          <div>
            <h4 className="text-white font-semibold mb-4">OS Plans</h4>
            <ul className="space-y-2">
              <li><Link to="/starter" className="text-gray-400 hover:text-white text-sm">Starter</Link></li>
              <li><Link to="/pro" className="text-gray-400 hover:text-white text-sm">Pro</Link></li>
              <li><Link to="/business" className="text-gray-400 hover:text-white text-sm">Business</Link></li>
            </ul>
          </div>
          
          {/* Portals */}
          <div>
            <h4 className="text-white font-semibold mb-4">Portals</h4>
            <ul className="space-y-2">
              <li><Link to="/login" className="text-gray-400 hover:text-white text-sm">Sign In</Link></li>
              <li><Link to="/customer-portal/login" className="text-gray-400 hover:text-white text-sm">Customer Portal</Link></li>
              <li><Link to="/employee-portal/login" className="text-gray-400 hover:text-white text-sm">Employee Portal</Link></li>
            </ul>
          </div>
          
          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><a href="#" className="text-gray-400 hover:text-white text-sm">Privacy Policy</a></li>
              <li><a href="#" className="text-gray-400 hover:text-white text-sm">Terms of Service</a></li>
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
