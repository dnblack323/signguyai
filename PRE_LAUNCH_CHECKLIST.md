# SignGuy AI - Pre-Launch Checklist

## 🔴 CRITICAL - Must Fix Before Launch

### 1. Security Issues
- [x] **CORS is now configurable via env var CORS_ORIGINS (`*`)** - Should be restricted to your production domain
  - File: `/app/backend/server.py` line 1065
  - Change `allow_origins=["*"]` to `allow_origins=["https://yourdomain.com"]`

- [ ] **Admin Portal routes missing authentication** - Multiple endpoints don't verify user
  - File: `/app/backend/routes/admin_portal.py`
  - Affected: `/dashboard`, `/conversations`, `/documents`, `/artwork-queue`, `/customers`, `/jobs`
  - Add `current_user: UserInDB = Depends(get_current_active_user)` to each

- [ ] **AI routes missing authentication** - AI generation endpoints are public
  - File: `/app/backend/routes/ai.py`
  - Affected: `/generate`, `/generate-images`, `/history`, `/assistant`
  - Add authentication dependency

- [x] **Rate limiting implemented** - App vulnerable to abuse/DoS
  - Implement rate limiting using `slowapi` or similar
  - Critical for AI endpoints (credit consumption)

### 2. Environment Variables for Production
Ensure these are set in production environment:
- [ ] `JWT_SECRET_KEY` - Change from default, use strong random value
- [ ] `SECRET_KEY` - Change from default
- [ ] `STRIPE_SECRET_KEY` - Switch to LIVE key (currently TEST)
- [ ] `STRIPE_WEBHOOK_SECRET` - Configure for production webhook endpoint
- [ ] `MONGO_URL` - Production MongoDB connection string
- [ ] `EMERGENT_LLM_KEY` - Verify sufficient balance
- [ ] `SENDGRID_API_KEY` - If using email features

### 3. Stripe Configuration
- [ ] **Switch from TEST to LIVE mode**
  - Update all `STRIPE_PRICE_*` IDs to production Price IDs
  - Update webhook endpoint URL in Stripe Dashboard
  - Test complete payment flow with real card

- [ ] **Webhook endpoint verification**
  - Verify `/api/billing/webhook/stripe` is accessible
  - Test all webhook events: `checkout.session.completed`, `invoice.payment_succeeded`, `customer.subscription.deleted`

---

## 🟠 HIGH PRIORITY - Should Fix Before Launch

### 4. Data & Database
- [x] **Database indexes created** - Ensure indexes are created
  - Run: `/app/backend/migrations/2025_12_01_add_webstore_indexes.py`
  
- [ ] **Remove/disable sample data creation** - Or make it opt-in
  - File: `/app/backend/routes/auth.py` lines 138-144
  - Sample data creates fake customers/jobs on every registration

- [ ] **Database backup strategy** - Set up automated backups for MongoDB

### 4.1 Data Safety & Soft Deletes ✅ COMPLETE
All critical data models now use soft delete instead of permanent deletion:
- [x] **Customers** - `DELETE /api/customers/{id}` now soft deletes
- [x] **Jobs** - `DELETE /api/jobs/{id}` now soft deletes (with related job_items, job_notes)
- [x] **Invoices** - `DELETE /api/invoices/{id}` now soft deletes
- [x] **Quotes** - `DELETE /api/quotes/{id}` now soft deletes
- [x] **Products** - `DELETE /api/products/{id}` now soft deletes
- [x] **Webstores** - `DELETE /api/webstores/v2/{id}` now soft deletes
- [x] **Employees** - `DELETE /api/employees/{id}` now soft deletes

**Implementation Details:**
- All GET list endpoints exclude soft-deleted records by default
- All GET single item endpoints exclude soft-deleted records
- Use `include_deleted=true` query param to include soft-deleted items
- Restore endpoints: `POST /api/{model}/{id}/restore`
- View deleted items: `GET /api/{model}/deleted/list`
- Hard delete (permanent): Add `permanent=true` query param to DELETE

**Files Created/Updated:**
- `backend/services/soft_delete_service.py` - Core soft delete logic
- `backend/scripts/run_migrations.py` - Migration runner
- `backend/migrations/0001_soft_delete_fields.py` - Add deleted_at fields

### 5. Credit System Implementation
- [x] **Credit system verified - GET /api/billing/credits endpoint added** - Test AI tools deduct credits properly
- [ ] **Credit refill on payment** - Verify webhook adds 150 credits on `invoice.payment_succeeded`
- [ ] **Credit expiration** - Implement monthly credit expiration logic
- [ ] **Pre-action credit check UI** - Show "This will cost X credits" before AI actions

### 6. Error Handling & Monitoring
- [ ] **Add error monitoring** - Integrate Sentry, Bugsnag, or similar
- [ ] **582 database operations lack error handling** - Add try/except blocks
- [x] **console.log statements removed** - 2 found in frontend
- [x] **print statements converted to logger.error** - 10 found in backend routes

### 7. Email Configuration
- [ ] **Configure SendGrid/email service** - For:
  - Invoice emails
  - Customer portal notifications
  - Password reset
  - Subscription confirmations

---

## 🟡 MEDIUM PRIORITY - Recommended Before Launch

### 8. UI/UX Polish
- [ ] **Dark Shell layout incomplete** - Apply to remaining pages:
  - Dashboard
  - Customers
  - Products
  - Main Settings page

- [x] **Mobile responsiveness verified - Landing, Dashboard, Jobs all responsive** - Test all pages on mobile devices

- [ ] **Error pages** - Create custom 404, 500 error pages

### 9. Legal & Compliance
- [x] **Terms of Service page created (/terms)** - Required for SaaS
- [x] **Privacy Policy page created (/privacy)** - Required, especially with payment processing
- [ ] **Cookie consent** - If using analytics/tracking
- [ ] **Data deletion policy** - GDPR compliance

### 10. Testing
- [ ] **End-to-end subscription flow test**
  - Register → Trial → Subscribe → Payment → Credit refill
  
- [ ] **Customer portal flow test**
  - Login → View orders → Approve artwork → Make payment

- [ ] **All payment flows**
  - Monthly subscription
  - Annual subscription
  - Credit pack purchase
  - FOUNDERS promo code

### 11. Documentation
- [ ] **API documentation** - Generate/update OpenAPI docs
- [ ] **User onboarding guide** - Help docs for new users
- [ ] **Admin guide** - Documentation for shop owners

---

## 🔵 LOW PRIORITY - Nice to Have

### 12. Performance
- [ ] **Frontend bundle optimization** - Check build size
- [ ] **Image optimization** - Lazy loading, compression
- [ ] **Database query optimization** - Add explain() to slow queries
- [ ] **CDN for static assets** - If high traffic expected

### 13. Analytics
- [ ] **Usage analytics** - Track feature adoption
- [ ] **Conversion tracking** - Trial to paid conversion
- [ ] **Error tracking** - Monitor JS errors

### 14. Features to Complete
- [ ] **Employee assignment shortcut** - For job line items
- [ ] **Trial lockout re-enable** - Currently disabled
- [ ] **Founder counter display** - Show "X of 100 spots remaining"

---

## ✅ Already Complete

- [x] Deployment health check passed
- [x] Founders Edition pricing configured
- [x] Stripe Price IDs configured
- [x] FOUNDERS coupon configured
- [x] Landing page pricing transparency
- [x] Invoice line items fix
- [x] Bulk actions on Jobs page
- [x] Search functionality on Jobs, Invoices, Webstores
- [x] Quick Add Job button on customer modal
- [x] Keyboard shortcuts for bulk actions
- [x] Customer portal authentication

---

## Pre-Launch Testing Checklist

### User Flows to Test
1. [ ] New user registration → Gets 48hr trial + sample data
2. [ ] Login/logout flow
3. [ ] Create customer → Create quote → Convert to job → Create invoice → Send invoice
4. [ ] Webstore creation → Add products → Customer purchase
5. [ ] Customer portal login → View orders → Approve artwork
6. [ ] AI tool usage → Credit deduction
7. [ ] Subscribe to Founders Edition (monthly)
8. [ ] Subscribe to Founders Edition (annual with FOUNDERS code)
9. [ ] Purchase credit pack
10. [ ] Cancel subscription → Verify access restricted

### Devices to Test
- [ ] Desktop Chrome
- [ ] Desktop Firefox
- [ ] Desktop Safari
- [ ] Mobile iOS Safari
- [ ] Mobile Android Chrome
- [ ] Tablet

---

## Post-Launch Monitoring

- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Monitor Stripe webhook delivery
- [ ] Watch error logs for first 48 hours
- [ ] Monitor database performance
- [ ] Track signup/conversion metrics

