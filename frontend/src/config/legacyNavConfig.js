/**
 * LEGACY NAVIGATION CONFIGURATION
 * ================================
 * This file contains the original navigation and footer configuration
 * with all platform tiers and product lines. Restore this when the
 * Founders Edition period ends.
 * 
 * To restore: Copy navLinks and footer sections back to PublicNav.js
 */

// Original navigation links with dropdowns
export const LEGACY_NAV_LINKS = [
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
  { href: '/webstores-overview', label: 'Webstores' },
  { href: '/ai-studio', label: 'AI Studio' },
  { href: '/pricing', label: 'Pricing' },
];

// Original footer sections
export const LEGACY_FOOTER_SECTIONS = {
  products: {
    title: 'Products',
    links: [
      { href: '/platform', label: 'Platform' },
      { href: '/webstores-overview', label: 'Webstores' },
      { href: '/ai-studio', label: 'AI Studio' },
      { href: '/pricing', label: 'Pricing' },
    ]
  },
  osPlans: {
    title: 'OS Plans',
    links: [
      { href: '/starter', label: 'Starter' },
      { href: '/pro', label: 'Pro' },
      { href: '/business', label: 'Business' },
    ]
  },
  portals: {
    title: 'Portals',
    links: [
      { href: '/login', label: 'Sign In' },
      { href: '/customer-portal/login', label: 'Customer Portal' },
      { href: '/employee-portal/login', label: 'Employee Portal' },
    ]
  },
  legal: {
    title: 'Legal',
    links: [
      { href: '#', label: 'Privacy Policy' },
      { href: '#', label: 'Terms of Service' },
    ]
  }
};

// Original CTA button
export const LEGACY_CTA = {
  text: 'Start Free Trial',
  href: '/login',
  className: 'bg-blue-600 hover:bg-blue-700 text-white text-sm'
};

/**
 * LEGACY ROUTES (preserved in App.js at /pricing-legacy)
 * 
 * These pages are still accessible but hidden from navigation:
 * - /platform - Platform overview
 * - /starter - Starter tier page
 * - /pro - Pro tier page  
 * - /business - Business tier page
 * - /webstores-overview - Webstores product page
 * - /ai-studio - AI Studio product page
 * - /pricing-legacy - Original multi-tier pricing page
 */

/**
 * HOW TO RESTORE LEGACY NAVIGATION
 * =================================
 * 
 * 1. In PublicNav.js, replace navLinks with LEGACY_NAV_LINKS
 * 
 * 2. Restore the dropdown rendering logic in Desktop Nav:
 *    {navLinks.map((link) => (
 *      link.dropdown ? (
 *        <div key={link.href} className="relative">
 *          <button onClick={() => setOpenDropdown(...)}>
 *            {link.label}
 *            <ChevronDown />
 *          </button>
 *          {openDropdown === link.href && (
 *            <div className="dropdown">
 *              {link.dropdown.map(...)}
 *            </div>
 *          )}
 *        </div>
 *      ) : (
 *        <Link to={link.href}>{link.label}</Link>
 *      )
 *    ))}
 * 
 * 3. Update the CTA button back to "Start Free Trial"
 * 
 * 4. Restore footer sections with all product/plan links
 * 
 * 5. In App.js, change /pricing route back to PricingPagePublic
 */
