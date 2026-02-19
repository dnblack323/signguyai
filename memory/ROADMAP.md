# SignGuy AI - Development Roadmap & Checklist

**Live URL:** https://signguy-ai.com
**Last Updated:** February 19, 2026

---

## 🔴 HIGH PRIORITY (P0-P1)

### AI Tools to Build
- [ ] **Race Number Creator** - AI tool for generating race car number designs
- [ ] **Visualizer Tour** - Interactive tour/guide for the visualizer tool
- [ ] **RaceWrap AI Tool** - Advanced version for vehicle wraps

### Mobile & UX
- [ ] **Mobile Responsiveness** - Refactor dashboard and key pages for mobile-friendliness
- [ ] **Dashboard Quick Actions** - Make buttons open modals instead of navigating away

---

## 🟠 MEDIUM PRIORITY (P2)

### Webstores
- [ ] **Webstores Enhancement** - Review and improve webstore functionality
  - [ ] Test full webstore flow (create store, add products, customer ordering)
  - [ ] Verify payment processing works correctly
  - [ ] Check order management and fulfillment workflow
  - [ ] Ensure store customization options work (branding, colors, etc.)
  - [ ] Test customer-facing storefront display
  - [ ] Verify inventory tracking (if applicable)

### Marketing Site
- [ ] **Replace "Screenshot coming soon" placeholders** on Features page with real screenshots
- [ ] **Capture screenshots** for each feature section (Customer Management, Jobs, Invoicing, etc.)

### Billing & Monetization
- [ ] **Add-On Module System** - Architecture for selling additional features separately
  - [ ] Advanced Wrap Module (future)
  - [ ] AI Tools Add-On pack
- [ ] **Founder pricing logic** - Track first 100 signups, lock in their rates
- [ ] **Trial credits system** - For AI tool usage limits by tier

### UX Improvements
- [ ] **Kanban card click** - Verify navigation works correctly (user testing)

---

## 🟡 FUTURE FEATURES (Backlog)

### New Modules
- [ ] **Form/Document Library** - Templates for common sign shop forms
- [ ] **AI Smart Quote Builder** - AI-assisted quote generation
- [ ] **Efficiency Dashboard** - Analytics and productivity metrics

### Integrations
- [ ] **BNPL (Buy Now Pay Later)** - Payment plans for customers
- [ ] **SMS Notifications** - Text alerts for jobs, approvals, etc.
- [ ] **QuickBooks Integration** - Sync invoices and financials
- [ ] **Custom Domain Support** - Let shops use their own domain

---

## 💡 BUSINESS IDEAS DISCUSSED

- [ ] **Founder Promo Codes for Add-Ons** - Create codes like `FOUNDER20` for discounts on future add-on modules
- [ ] **Tiered Add-On Pricing** - Founders pay for add-ons but get loyalty discounts
- [ ] **First 100 Founders Tracking** - Lock in pricing for early adopters

---

## 🔧 TECHNICAL DEBT / REFACTORING

- [ ] Break down `Jobs.js` (large monolithic component)
- [ ] Organize API routes (move to `/app/backend/routes/`)
- [ ] Create test files at `/app/backend/tests/` for regression testing

---

## ✅ COMPLETED

### February 19, 2026
- [x] Fixed unreadable dashboard badge (high-contrast colors)
- [x] Applied blue theme (#2F8BFB) across all marketing pages
- [x] Updated logos (slant, long, square) across app
- [x] Created Promo Codes system (Admin > Promo Codes)
- [x] Re-enabled Trial Lockout (founders bypass it)
- [x] Added Employee Portal branding (square logo)
- [x] Employee profile image upload feature
- [x] Founder account setup (owner account marked as founder)
- [x] Preview mode restricted to dev/founders only
- [x] Deployed to production
- [x] Connected custom domain: signguy-ai.com

### Earlier Work
- [x] Core business modules (Customers, Quotes, Jobs, Invoices)
- [x] Employee Portal with time clock
- [x] Customer Portal
- [x] AI Tools suite (15+ tools)
- [x] Pricing calculators
- [x] Multi-tenant architecture
- [x] Role-based access control
- [x] Marketing website with documentation
- [x] Stripe billing integration (TEST mode)
- [x] SendGrid email integration

---

## 📝 NOTES

### Founder Pricing Strategy
- First 100 founders get locked-in tier pricing forever
- Add-on modules are SEPARATE purchases (founders don't get them free)
- Create promo codes for founder discounts on add-ons

### Test Credentials
- **Admin:** thesigntistslab@gmail.com (FOUNDER account)
- **Test Admin:** testuser123@test.com / Test123!
- **Employee Portal:** john@signshop.com / PIN: 5678

### Theme Rules (NON-NEGOTIABLE)
- Dark shell background: `#0B0F17`
- Light content cards: `#FFFFFF` or `#F7F8FA`
- Dark text on cards: `#111827` or `#374151`
- Blue accents ONLY: `#2F8BFB` (hover: `#1E7AF0`)
