# SignGuy AI - Changelog

## March 14, 2026 - Community Hub + Backup System + Pricing Transparency

### New Feature: Community Hub (`/community`)
- Searchable message board for bug reports, feature requests, questions, and feedback
- Category system: Bug Report, Feature Request, Question, Feedback
- Upvote system for prioritizing posts
- Owner can reply with "Official" badge, pin posts, change status (Open/In Progress/Resolved/Closed)
- Owner replies auto-mark posts as "Answered"
- Direct "Contact Support" email link to app owner
- Search across titles, descriptions, and replies
- Filter by category and status
- Added to main navigation bar
- Backend: `/api/community/posts`, `/api/community/stats` + CRUD endpoints
- Frontend: `CommunityHub.js` with list and detail views

### New Feature: Tenant Data Backup & Restore (`/settings/backup`)
- Owner-only backup/restore system
- Download all tenant data as JSON (images excluded, ~31KB vs 20MB)
- Restore with preview summary and confirmation ("This will replace all existing data")
- Weekly backup reminder banner (dismissable per session)
- Link from Company Settings > Data Management
- Backend: `/api/backup/export`, `/api/backup/status`, `/api/backup/preview-restore`, `/api/backup/restore`

### Enhancement: Webstore Product Image Upload
- Added image upload UI (up to 3 images per product) to Create Product form
- Product list shows image thumbnails

### Enhancement: Landing Page Pricing Transparency (8 Sections)
- Founder Launch Offer banner, How AI Credits Work block, Billing & Payments section
- AI Usage Transparency notice with example UI, Fair Usage Protection notice
- 4 new FAQ questions on both FoundersEditionPricing.js and LandingPage.js

### Bug Fix: Login Network Error (P0)
- Tenant response optimization: 2.95MB → 497 bytes (base64 logo separated to `/api/tenant/logo`)
- Production routing issue identified: `quote-to-invoice-3.emergent.host` → "Deployment not found" (Emergent support contacted)
