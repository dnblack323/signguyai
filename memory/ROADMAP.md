# SignGuy AI - Project Status & Roadmap

**Last Updated:** February 13, 2026

---

## ✅ COMPLETED FEATURES

### Phase 1: Core Foundation
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| User Authentication | Register, login, JWT tokens, remember me | ~50 |
| Multi-tenancy | Tenant isolation, data separation | ~30 |
| RBAC System | Owner, Admin, Staff roles with permissions | ~40 |
| Company Settings | Business info, logo, preferences | ~20 |

### Phase 2: Core Business Modules
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| Customer Management | Full CRUD, contact info, notes | ~40 |
| Quotes Module | Create, edit, line items, status tracking | ~50 |
| Jobs Module | Job creation from quotes, status updates | ~60 |
| Invoices Module | Invoice generation, payment tracking | ~50 |
| Job Details Page | Detailed view with items, notes, activity | ~30 |

### Phase 3: Operations
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| Time Clock | Punch in/out, break tracking | ~40 |
| Payroll | Pay period calculations, transactions | ~50 |
| Productivity Page | Basic productivity tracking | ~20 |
| Financials Page | Revenue/expense tracking | ~30 |

### Phase 4: Customer Portal
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| Portal Login/Register | Separate auth for customers | ~30 |
| Portal Dashboard | Customer-facing dashboard | ~30 |
| View Orders/Quotes/Invoices | Read-only access | ~40 |
| Messaging System | Two-way communication | ~50 |
| Artwork Proofs | Upload, approve, reject proofs | ~40 |
| Appointments | Booking system | ~30 |
| Profile Management | Customer self-service | ~20 |

### Phase 5: Webstores
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| Webstore Creation | Fundraiser, Event, Business stores | ~60 |
| Product Management | Products with variants, images | ~50 |
| Public Storefront | Customer-facing store pages | ~50 |
| Order Management | Orders from webstores | ~40 |
| Store Dashboard | Analytics, settings | ~30 |

### Phase 6: Pricing Calculator
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| 8 Calculator Types | Apparel, Vinyl, Signs, Vehicle, etc. | ~80 |
| Save as Template | Reusable pricing templates | ~20 |
| Pricing Settings | Default rates, markups | ~20 |
| Integration with Jobs/Quotes | Calculator modal in forms | ~30 |

### Phase 7: AI Tools
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| AI Tools Page | Basic AI integration placeholder | ~20 |

### Phase 8: SaaS & Billing (Current)
| Feature | Description | Credits Used |
|---------|-------------|--------------|
| Backend Refactoring | 6,349 → 786 lines (88% reduction) | ~100 |
| 3-Tier System | Starter/Pro/Business feature gates | ~80 |
| Frontend Tier Integration | Upgrade modals, lock icons, tier badge | ~60 |
| Stripe Integration | Checkout sessions, webhooks | ~80 |
| Pricing Page | Founder Member pricing display | ~50 |
| 24hr Trial Lockout | Lockout screen, countdown timer | ~50 |

### **TOTAL COMPLETED:** ~1,600 credits estimated

---

## 📋 REMAINING FEATURES (BACKLOG)

### 🔴 P0 - Critical (Revenue/Core)
| # | Feature | Description | Est. Credits |
|---|---------|-------------|--------------|
| 1 | **Dashboard Enhancement** | Greeting, schedule, notifications, stats | 60-80 |
| 2 | **Sidebar Restructure** | Home link at top, cleaner nav | 20-30 |

### 🟠 P1 - High Priority
| # | Feature | Description | Est. Credits |
|---|---------|-------------|--------------|
| 3 | **Employee Portal** | Separate login for employees | 100-150 |
| | - Login Page | `/employee-portal/login` | 30 |
| | - Time Clock View | Punch in/out, current shift | 40 |
| | - My Hours/Pay | Pay stubs, earnings history | 40 |
| | - My Jobs/Tasks | Assigned work list | 40 |
| 4 | **Job Time Tracking** | Track time per job for AI pricing | 80-100 |
| | - Job Selection on Clock-in | Pick job when starting | 30 |
| | - Time Logging per Job | Automatic time records | 30 |
| | - AI Pricing Feedback | Use real time data for pricing | 40 |
| 5 | **Job Status Flow/Timeline** | Visual progress on job tickets | 60-80 |
| | - Status Stages | Design → Production → QC → Complete | 30 |
| | - Timeline View | Timestamps at each stage | 30 |
| | - Stage Analytics | Time spent per stage | 20 |
| 6 | **Subscription Management** | View/cancel subscription page | 40-60 |

### 🟡 P2 - Medium Priority
| # | Feature | Description | Est. Credits |
|---|---------|-------------|--------------|
| 7 | **Theme Audit/Fix** | White-on-white font issues | 40-60 |
| 8 | **Efficiency Dashboard** | Employee performance metrics (Business) | 60-80 |
| 9 | **AI Business Assistant** | Chat interface for business queries | 100-150 |
| 10 | **Calendar View** | Visual calendar for jobs/appointments | 60-80 |
| 11 | **Kanban Board** | Drag-drop job management | 60-80 |

### 🟢 P3 - Lower Priority
| # | Feature | Description | Est. Credits |
|---|---------|-------------|--------------|
| 12 | **Reports & Exports** | PDF/CSV exports for reports | 50-70 |
| 13 | **BNPL Integration** | Affirm/Klarna for Business tier | 80-100 |
| 14 | **SMS Notifications** | Twilio integration (Business) | 60-80 |
| 15 | **QuickBooks Integration** | Accounting sync | 80-100 |
| 16 | **Webstores Phase 3** | B2B, Creator/Affiliate stores | 100-150 |

### 🔵 RaceWrap AI Tool (Future AI Feature - P2)
| Item | Details |
|------|---------|
| **Feature Name** | RaceWrap AI - Race Car Number & Sponsor Wrap Designer |
| **What It Does** | 1) Custom race car numbers optimized for motorsports visibility, 2) Full/partial race car wrap concepts, 3) Sponsor logo placement strategies based on hierarchy and visibility |
| **Required Inputs** | Car type (late model, sprint car, dirt modified, stock car, drag car, kart, etc.), car views needed (side, hood, roof, rear), primary race number, team/driver name, primary color preference |
| **Optional Inputs** | Sponsor logos upload (PNG, SVG, JPG), sponsor priority ranking (primary, secondary, minor), series rules/restrictions (number color, outline rules, placement rules), existing brand colors or logo, style preference (aggressive/clean/retro/modern) |
| **Core Outputs** | Race number design options (multiple font/style variations, outline/shadow suggestions, color contrast optimized for speed visibility), wrap concept mockups (side view, top view, number placement previews) |
| **Sponsor Outputs** | Suggested sponsor hierarchy, optimal logo placement zones, balanced layout suggestions, conflict warnings (too many logos, unreadable clustering, poor contrast) |
| **Smart Behavior** | Auto-scale sponsor logos proportionally, avoid placing critical sponsors on high-damage zones, prioritize driver number legibility over aesthetics, suggest alternates when logos clash visually, warn when sponsor logo is too low-res for wrap use |

### **TOTAL REMAINING:** ~1,100-1,500 credits estimated

---

## 📊 PROPOSED IMPLEMENTATION ORDER

### Sprint 1: Dashboard & Navigation (80-110 credits)
```
1. Sidebar restructure - Move Home to top
2. Dashboard enhancement:
   - Morning greeting with user name
   - Today's schedule/appointments
   - Pending customer approvals
   - Unread portal messages
   - Employees currently clocked in
   - Key stats (jobs in progress, invoices due, etc.)
```

### Sprint 2: Employee Portal MVP (100-150 credits)
```
1. Employee Portal login page
2. Employee-specific auth (check role)
3. Time Clock view (their punches only)
4. My Hours summary
5. My Jobs/Tasks list
```

### Sprint 3: Job Time Tracking (80-100 credits)
```
1. Job selection on clock-in
2. Time logging per job
3. Job time reports
4. Integration with pricing calculator
```

### Sprint 4: Job Status Flow (60-80 credits)
```
1. Define status stages
2. Timeline component on job detail
3. Status change logging with timestamps
4. Stage duration analytics
```

### Sprint 5: Theme & Polish (40-60 credits)
```
1. Audit all pages for theme issues
2. Fix white-on-white problems
3. Ensure dark/light mode consistency
```

### Sprint 6: Employee Efficiency (60-80 credits)
```
1. Efficiency score calculation
2. Employee dashboard (Business tier)
3. Performance metrics display
```

### Sprint 7: Advanced Features (200-300 credits)
```
1. AI Business Assistant
2. Calendar View
3. Kanban Board
4. Subscription Management
```

### Sprint 8: Integrations (200-300 credits)
```
1. BNPL (Affirm/Klarna)
2. SMS (Twilio)
3. QuickBooks
```

---

## 💰 CREDIT COST SUMMARY

| Phase | Features | Est. Credits |
|-------|----------|--------------|
| Sprint 1 | Dashboard + Navigation | 80-110 |
| Sprint 2 | Employee Portal MVP | 100-150 |
| Sprint 3 | Job Time Tracking | 80-100 |
| Sprint 4 | Job Status Flow | 60-80 |
| Sprint 5 | Theme Fix | 40-60 |
| Sprint 6 | Efficiency Dashboard | 60-80 |
| Sprint 7 | Advanced Features | 200-300 |
| Sprint 8 | Integrations | 200-300 |
| **TOTAL** | **All Remaining** | **820-1,180** |

---

## 🎯 RECOMMENDED NEXT STEPS

**Immediate (This Session):**
1. ✅ Sidebar restructure (Home at top)
2. ✅ Enhanced Dashboard

**Next Session:**
3. Employee Portal MVP
4. Job Time Tracking

**Following Sessions:**
5. Job Status Flow/Timeline
6. Theme Audit
7. Remaining features

---

## 📝 NOTES

- Credit estimates are approximate and may vary based on complexity
- Testing is included in estimates
- Bug fixes that arise are not included
- AI integrations (Assistant) will require more credits due to LLM API setup
- Integrations (Stripe, Twilio, QuickBooks) require API key setup

**Questions to Address:**
1. What job status stages do you want? (e.g., New → Design → Production → QC → Complete → Delivered)
2. For Employee Portal - should employees see job pricing/costs? (You said no for most, yes for Business tier)
3. For efficiency metrics - what KPIs matter most? (Time accuracy, jobs completed, error rate?)
