# Category 3: Pricing, Products, And Catalog
**Objective:** Verify that every launch-visible product can be configured, priced accurately, saved, sold, and understood without dead actions, misleading settings, broken layouts, or unsafe data behavior.

**Sections:** Pricing Calculator · Pricing Foundation · Pricing Setup And Invoice Import · Pricing Settings · Materials Administration · Products And Product Catalog · Promo Codes · Promotional Items Pricing · Cut Vinyl Pricing · Services Pricing · Digital Print Pricing · Banner Pricing · Rigid Sign Pricing · Apparel Pricing · Vehicle Graphics Pricing · Custom And Other Pricing

---

## Category Readiness Summary
**Status:** Strong pricing backend and configuration foundation, but **not launch-approved** until known calculation bugs, promo-code tenant-safety bugs, incomplete actions, and live category accuracy checks are resolved.

### Verified Strengths
- [x] Pricing Calculator, Pricing Foundation, historical Pricing Setup, Products, Promo Codes, Pricing Settings, and Materials compatibility routes exist.
- [x] Pricing defaults, materials, hardware, category rules, benchmarks, templates, and calculation endpoints exist.
- [x] Pricing default updates require owner/admin access.
- [x] Pricing templates are tenant scoped.
- [x] Historical invoice imports are tenant scoped and owner/admin restricted.
- [x] Historical invoice review saves accepted findings to selling-price benchmarks instead of silently changing cost settings.
- [x] Product CRUD endpoints exist and product records are tenant scoped.
- [x] Product create, update, and delete operations use product permissions.
- [x] Product images are limited to three by frontend and backend behavior.
- [x] Stored pricing reports show 67 passing tests across the main pricing, foundation, expansion, and setup reports.
- [x] Stored iteration 128 report shows 23 passed and 2 skipped/xfail known bugs.
- [x] Stored iteration 130 report includes passing product CRUD coverage.

### Current Launch Blockers
- [x] Fix or hide promotional double-sided pricing because the field is visible but ignored by the calculator. ✅ *2026-06-09 — Reviewed: Promotional section UI has no double_sided field; Rigid Signs double_sided_art is conditionally disabled when sidedness != double. No fix needed.*
- [x] Fix Custom/Other job-ticket description persistence. ✅ *Fixed 2026-06-08 — description field added to AddTicketToOrder state and POST body*
- [x] Fix Promo Codes update and updated-record read to include `tenant_id`. ✅ *Fixed 2026-06-08 — update_one and find_one both use tenant_id filter*
- [x] Fix Promo Codes redemption to include atomic usage-limit enforcement (prevent race condition on max_uses). ✅ *Fixed 2026-06-09 — apply-promo uses find_one_and_update with conditional $expr filter*
- [x] Decide whether promo codes are platform-global or tenant-owned — **DECIDED: platform-only (platform_creator/platform_admin only)**. ✅ *Fixed 2026-06-09 — require_platform_admin() enforces role; codes are unscoped (no tenant_id); tenants have no access to create/view/edit/delete codes*
- [ ] Add backend validation for promo discount values, trial days, expiration, and maximum uses.
- [x] Fix `PricingSetup.handleAnalyze` returning `response.json` instead of parsed response data. ✅ *Fixed 2026-06-08 — changed to await response.json()*
- [ ] Add historical import upload file-size, file-count, row-count, and PDF-page limits.
- [ ] Remove or complete Pricing Foundation Category Methods actions that currently only show "coming in next phase."
- [x] Remove or development-gate the pricing-calculation console log. ✅ *Fixed 2026-06-08 — removed console.log from Pricing.js*
- [ ] Verify every visible pricing category against real shop examples.
- [ ] Complete authenticated live clickthrough and responsive visual QA.

---

## Required Category Workflow
- [ ] Confirm the intended workflow is Pricing Foundation setup → materials/hardware → category rules → test calculation → Pricing Calculator → product/order use.
- [ ] Confirm historical invoice import is clearly optional benchmark assistance, not the source of cost settings.
- [ ] Confirm Products is the reusable ecommerce catalog and Pricing Calculator is the quoting/order-item calculator.
- [ ] Document where product retail prices are independent of calculated production pricing.
- [ ] Remove duplicate settings entry points that do not clarify their purpose.
- [ ] Ensure users can always identify the next action and the source of each calculated price.

---

## Section 1 — Pricing Calculator

### Verified Structure And Behavior
- [x] Route `/pricing-calculator` exists.
- [x] Calculator links to Pricing Foundation when a material needs to be added.
- [x] Calculate endpoint requires authentication.
- [x] Calculator loads tenant pricing defaults.
- [x] Calculator normalizes legacy category aliases.
- [x] Calculator normalizes legacy dimension fields.
- [x] Unknown categories fall back to Custom/Other behavior.
- [x] Template list, create, update, delete, and favorite endpoints exist.
- [x] Stored `pricing_results.xml` reports 19 passing tests.
- [x] Stored `pricing_expansion_results.xml` reports 16 passing tests.

### Must Fix Or Decide
- [x] Remove `console.log('Item calculated:', itemData)` from `frontend/src/pages/Pricing.js` or development-gate it. ✅ *Fixed 2026-06-08 — console.log removed*
- [ ] Confirm the Add Item callback actually sends the calculated item to the intended order/quote context.
- [ ] Confirm standalone use explains where the calculated item goes.
- [ ] Confirm all visible fields affect the calculation or saved item.
- [ ] Hide any field that is intentionally unsupported.
- [ ] Confirm manual price override is visible in the breakdown and saved audit data.
- [ ] Confirm failed calculations preserve entered values.
- [ ] Confirm API errors show actionable messages instead of a blank result.

### Live Clickthrough
- [ ] Confirm no blank or black screen.
- [ ] Select every category once.
- [ ] Confirm category switching does not retain incompatible fields.
- [ ] Enter valid values and calculate each category.
- [ ] Enter missing/invalid values and confirm clear validation.
- [ ] Create a pricing template.
- [ ] Load the template.
- [ ] Favorite and unfavorite the template.
- [ ] Delete the template.
- [ ] Use every Add New material link and confirm it opens Pricing Foundation.
- [ ] Confirm every button and link works and serves a clear purpose.
- [ ] Confirm no duplicate actions create confusion.

### Visual And Responsive QA
- [ ] Confirm no light-on-light or dark-on-dark text.
- [ ] Confirm no accidental horizontal scrolling at desktop, tablet, and mobile widths.
- [ ] Confirm category controls do not overlap.
- [ ] Confirm the result breakdown remains readable with long values.
- [ ] Confirm large forms do not create unexplained empty spaces.
- [ ] Confirm the Calculate action remains easy to find after scrolling.
- [ ] Confirm the workflow order is category → specifications → labor/add-ons → calculate → breakdown → save/add.

---

## Section 2 — Pricing Foundation

### Verified Structure And Behavior
- [x] Route `/pricing-foundation` exists.
- [x] Pricing Foundation is described as the single source of truth for production costs, materials, and selling defaults.
- [x] Simple, Advanced, and Audit modes exist.
- [x] The preferred mode is persisted locally.
- [x] Materials, hardware, labor, category rules, category methods, AI rules, benchmarks, global rules, and review/test surfaces exist.
- [x] Unsaved-change detection exists.
- [x] Save All sends settings, materials, and hardware in one pricing-defaults update.
- [x] Edit controls are permission gated.
- [x] Stored foundation reports show 17 passing tests across two reports.

### Must Fix Or Decide
- [ ] Remove or implement Category Methods setup actions that only show "coming in next phase."
- [ ] Remove or implement Category Methods test actions that only show "coming in next phase."
- [ ] Verify each field in `HIDDEN_FIELDS_LEVEL_1` truly does not affect active calculations.
- [ ] Add documentation for any hidden backend field that still changes results.
- [ ] Confirm the Simple mode does not hide a required first-time setup value.
- [ ] Confirm the Audit mode is appropriate for launch users with settings access.
- [ ] Confirm changing modes never drops unsaved changes.
- [ ] Add a navigation warning before leaving with unsaved changes.
- [ ] Confirm Save All handles partial backend failure without falsely showing success.
- [ ] Confirm all editable numeric fields reject invalid negative or nonsensical values.

### Live Clickthrough
- [ ] Open Simple mode and complete the Pricing Setup Quiz.
- [ ] Review suggested changes before applying.
- [ ] Save and reload; confirm values persist.
- [ ] Complete the Shop Rate calculator.
- [ ] Open every Advanced tab.
- [ ] Edit and restore one field in every tab.
- [ ] Add, edit, disable, and delete a test material.
- [ ] Add, edit, disable, and delete a test hardware item.
- [ ] Run an Audit mode calculation.
- [ ] Copy raw settings JSON.
- [ ] Confirm Calculator and Import Invoices links work.

### Visual And Responsive QA
- [ ] Confirm tab wrapping does not create overlap or horizontal scrolling.
- [ ] Confirm mode controls and Save All remain visible and understandable.
- [ ] Confirm no light-on-light text in white, gray, violet, blue, and amber panels.
- [ ] Confirm dense Advanced forms remain usable at tablet width.
- [ ] Confirm no large empty sections appear when a category has no materials.
- [ ] Confirm related fields are grouped in the order users need them.

---

## Section 3 — Pricing Setup And Invoice Import

### Verified Structure And Behavior
- [x] Route `/settings/pricing-setup` exists.
- [x] Access is restricted to users with settings access or owner/admin status.
- [x] Edit actions are restricted to settings-edit or owner access.
- [x] Backend allows PDF, CSV, XLSX, and XLS files.
- [x] Import sessions and operations are tenant scoped.
- [x] Mapping saves normalized rows.
- [x] Analysis produces category suggestions and confidence information.
- [x] Users can exclude identified outliers.
- [x] Accepted review values save only to selling-price benchmarks.
- [x] Stored `pricing_setup_results.xml` reports 15 passing tests.

### Must Fix Or Decide
- [x] Fix `handleAnalyze` to return parsed response data rather than `response.json`. ✅ *Fixed 2026-06-08 — changed to await response.json()*
- [ ] Add maximum individual file size.
- [ ] Add maximum combined upload size.
- [ ] Add maximum files per import.
- [ ] Add maximum spreadsheet row count.
- [ ] Add maximum PDF page count and extracted-text size.
- [ ] Reject empty and malformed files with clear messages.
- [ ] Confirm object-storage failures do not leave unusable partial imports.
- [ ] Add a delete/archive action for obsolete import sessions or document why none exists.
- [ ] Confirm failed AI analysis does not deduct credits.
- [ ] Confirm successful analysis deducts credits once.
- [ ] Confirm repeated Analyze clicks cannot duplicate charges or overwrite reviewed work unexpectedly.
- [ ] Confirm users understand benchmarks do not change production costs.

### Live Clickthrough
- [ ] Upload one valid CSV.
- [ ] Upload one valid Excel file.
- [ ] Upload one valid PDF.
- [ ] Attempt unsupported and oversized files.
- [ ] Confirm mapping suggestions are correct.
- [ ] Correct an incorrect mapping.
- [ ] Override one category.
- [ ] Exclude one outlier.
- [ ] Run analysis and review confidence explanations.
- [ ] Accept, edit, and ignore separate suggestions.
- [ ] Save review and confirm only benchmarks change.
- [ ] Reload and confirm import state persists.

### Visual And Responsive QA
- [ ] Confirm import list, mapping, rows, and suggestions have no horizontal-page scrolling.
- [ ] Use internal table scrolling only where unavoidable.
- [ ] Confirm long filenames and descriptions wrap or truncate with accessible detail.
- [ ] Confirm accepted, edited, ignored, pending, and low-confidence states are distinguishable without color alone.
- [ ] Confirm no large empty space appears when no import is selected.

---

## Section 4 — Pricing Settings

### Verified Structure And Behavior
- [x] Route `/pricing-settings` exists.
- [x] Page explains that Pricing Foundation replaced the old pricing settings.
- [x] Page links to Pricing Foundation.
- [x] Page links to historical Pricing Setup.
- [x] Legacy `/pricing-calculator/settings` redirects to Pricing Foundation.

### Completion Checklist
- [ ] Decide whether `/pricing-settings` should remain as a compatibility page or redirect directly.
- [ ] Confirm every old navigation entry now points to the intended new location.
- [ ] Remove duplicate settings links that add no value.
- [ ] Confirm compatibility page never appears as an unexplained dead end.
- [ ] Confirm both buttons work.
- [ ] Confirm page has no light-on-light text or large empty area.
- [ ] Confirm the user-facing distinction between Foundation and historical import is clear.

---

## Section 5 — Materials Administration

### Verified Structure And Behavior
- [x] Legacy `/materials` redirects to Pricing Foundation.
- [x] `/materials-admin` exists as a compatibility page.
- [x] Materials are stored inside the tenant pricing configuration.
- [x] Materials support categories, purchasing units, costs, markup, active state, compatibility, and notes.
- [x] Hardware/accessory records support purchase cost, sell price, labor add-on, active state, and category compatibility.
- [x] Calculator material selections read from Pricing Foundation data.

### Must Fix Or Decide
- [ ] Decide whether `/materials-admin` should redirect directly or remain as an explanation page.
- [ ] Confirm material keys are unique before save.
- [ ] Prevent deletion of a material still referenced by category defaults or templates, or show an impact warning.
- [ ] Prevent incompatible purchase-unit and dimension combinations.
- [ ] Validate cost, roll, sheet, unit, and linear-foot values.
- [ ] Confirm inactive materials disappear from new calculations but do not corrupt old saved cost snapshots.
- [ ] Confirm material changes do not silently rewrite historical order pricing.
- [ ] Add clear help for compatible categories and required key formats.
- [ ] Confirm materials, hardware, product catalog items, and wrap-job materials are not presented as interchangeable concepts.

### Live CRUD And Accuracy Pass
- [ ] Add one roll material and verify calculated cost per square foot.
- [ ] Add one sheet material and verify calculated cost per square foot.
- [ ] Add one each/unit material and verify unit cost.
- [ ] Add one linear-foot material and verify cost.
- [ ] Add one hardware item and verify sell price and labor add-on.
- [ ] Assign compatibility and confirm only intended category selectors show the item.
- [ ] Disable and re-enable each test item.
- [ ] Delete test items after confirming impact behavior.
- [ ] Save, reload, and confirm values persist.

### Visual And Flow QA
- [ ] Confirm material rows do not overlap at mobile/tablet widths.
- [ ] Confirm long names, keys, and compatibility lists do not force page-level horizontal scrolling.
- [ ] Confirm edit and delete icon buttons have tooltips or accessible labels.
- [ ] Confirm no low-contrast text in gray material cards.
- [ ] Confirm empty categories do not create excessive blank space.

---

## Section 6 — Products And Product Catalog

### Verified Structure And Behavior
- [x] Route `/products` exists.
- [x] Products are described as the master catalog for webstores.
- [x] Product create, list, detail, update, and delete endpoints exist.
- [x] Product operations are tenant scoped.
- [x] Product create and management permissions exist.
- [x] Products support categories, cost, retail price, images, variants, size options, color options, featured state, and stock state.
- [x] Product images are limited to three.
- [x] Product deletion also removes webstore product assignments.
- [x] AI product-description generation exists and uses the AI credit guard.
- [x] Stored iteration 130 includes passing product CRUD, defaults, and field-round-trip coverage.
- [x] Stored product-description AI report shows 9 passing tests.
- [x] Stored webstore-add-product report shows 10 passing tests.

### Must Fix Or Decide
- [ ] Add backend validation that base cost and retail price are valid positive amounts.
- [ ] Decide whether retail price below base cost is allowed; warn or block consistently.
- [ ] Validate image URLs and reject unsafe/invalid content.
- [ ] Decide whether base64 product images are acceptable for production storage and payload size.
- [ ] Confirm deleting a product assigned to active stores shows an impact warning.
- [ ] Confirm duplicate quick-add variant actions do not create duplicate variants.
- [ ] Confirm variant IDs remain stable after edits.
- [ ] Confirm unavailable variants cannot be purchased.
- [ ] Confirm stock state and featured state can be managed from the Product page if launch-required.
- [ ] Confirm categories align with webstore filters and storefront display.
- [ ] Clarify the relationship between Product retail price and Pricing Calculator results.
- [ ] Remove unnecessary production console errors or ensure they contain no sensitive product data.

### Live Clickthrough
- [ ] Create one product in every product category.
- [ ] Upload valid product images and add a valid image URL.
- [ ] Attempt invalid type, oversized image, invalid URL, and more than three images.
- [ ] Generate an AI description and confirm credit behavior.
- [ ] Add one manual variant.
- [ ] Add apparel quick variants once and twice; confirm duplicate handling.
- [ ] Add decal quick variants once and twice; confirm duplicate handling.
- [ ] Edit cost, retail price, images, and variants.
- [ ] Assign the product to a webstore and confirm storefront display.
- [ ] Delete an unassigned product.
- [ ] Attempt to delete an assigned product and confirm warning/cleanup behavior.
- [ ] Confirm every visible button, filter, expand action, and link works.

### Visual And Responsive QA
- [ ] Confirm product cards/table do not create horizontal page scrolling.
- [ ] Confirm product images use stable dimensions.
- [ ] Confirm long descriptions and variant lists remain readable.
- [ ] Confirm product-dialog fields fit at mobile width.
- [ ] Confirm color badges have readable text.
- [ ] Confirm expanded details do not duplicate the same data without purpose.
- [ ] Confirm no large empty space appears for small catalogs.

---

## Section 7 — Promo Codes

### Verified Structure And Behavior
- [x] Route `/promo-codes` exists.
- [x] List, create, update, delete, public validation, and authenticated redemption endpoints exist.
- [x] Promo management requires founder access.
- [x] Promo create and list operations use tenant scope.
- [x] Delete operation uses tenant scope.
- [x] UI supports percent, fixed, free trial, and free-days codes.
- [x] UI supports active state, expiration date, max uses, copy, edit, and delete.

### PO Security And Integrity Fixes
- [ ] Add `tenant_id` to the promo-code update filter.
- [ ] Add `tenant_id` to the updated-record read after update.
- [ ] Add `tenant_id` or an explicit platform-global identifier to redemption.
- [ ] Make public validation select the intended promo deterministically.
- [ ] Prevent duplicate code collisions across tenants if validation remains global.
- [ ] Enforce expiry and max-use checks during redemption, not validation only.
- [x] Make usage-limit check and increment atomic. ✅ *Fixed 2026-06-09 — find_one_and_update with $expr conditional*
- [ ] Prevent inactive or expired codes from being redeemed.
- [ ] Confirm checkout uses the same validation and redemption rules.
- [ ] Add tests proving one tenant cannot update or redeem another tenant's code.

### Validation And Product Decisions
- [ ] Validate percent discounts are greater than 0 and no more than 100.
- [ ] Validate fixed discounts are greater than 0.
- [ ] Validate free-day/trial-day values are within an approved range.
- [ ] Validate max uses is positive or null.
- [ ] Validate expiration date format and reject invalid dates instead of silently ignoring parse failures.
- [ ] Decide whether codes can be edited after use.
- [ ] Decide whether deletion or deactivation is the preferred audit-safe action.
- [ ] Confirm fixed discounts cannot reduce checkout below the allowed floor.
- [ ] Confirm codes cannot be applied multiple times to the same purchase/account unless intended.
- [ ] Replace beta/friend-specific wording if this is a production administration tool.

### Live Clickthrough
- [ ] Verify a non-founder cannot open or use management actions.
- [ ] Create each discount type.
- [ ] Edit each discount type.
- [ ] Copy each code.
- [ ] Validate active, inactive, expired, exhausted, invalid, and malformed codes.
- [ ] Redeem a valid code.
- [ ] Attempt repeat and concurrent redemption at the max-use boundary.
- [ ] Delete or deactivate a test code.
- [ ] Confirm every button and link works without a dead screen.

### Visual And Responsive QA
- [ ] Confirm cards and modal fit without horizontal scrolling.
- [ ] Confirm expiration, usage, active, and discount states are readable without color alone.
- [ ] Confirm text remains readable on accent-soft, surface, badge, and button colors.
- [ ] Confirm empty state does not consume excessive space.
- [ ] Confirm founder-only navigation does not expose the page to unrelated users.

---

## Section 8 — Promotional Items Pricing

### Verified Coverage
- [x] Promotional calculator supports magnets, yard signs, stickers, branded items, and custom items.
- [x] Quantity-tier behavior is covered by stored tests.
- [x] Rush pricing behavior is covered by stored tests.
- [x] Stored iteration 128 verifies several promotional calculations.

### Known Bug
- [ ] Fix promotional double-sided upcharge because `double_sided_art` is currently ignored.
- [ ] If double-sided pricing is intentionally unsupported, remove the field from the promotional UI.
- [ ] Add a passing regression test for the chosen behavior.

### Accuracy Scenarios
- [ ] Price 100 vehicle magnets and verify unit cost, markup, minimum, and total.
- [ ] Price 25 and 100 yard signs and verify quantity discount behavior.
- [ ] Price 100 and 1,000 stickers and verify tier transition.
- [ ] Price a branded purchased item and verify unit-cost markup.
- [ ] Compare single-sided, same-art double-sided, and different-art double-sided totals.
- [ ] Compare normal and rush totals.
- [ ] Verify manual override and breakdown.
- [ ] Save the expected results as regression fixtures.

### UI QA
- [ ] Confirm product-type-dependent fields appear in logical order.
- [ ] Confirm unsupported fields disappear.
- [ ] Confirm quantity tier and per-unit price are understandable.
- [ ] Confirm no horizontal scrolling, overlap, low contrast, dead buttons, or blank results.

---

## Section 9 — Cut Vinyl Pricing

### Verified Coverage
- [x] Cut vinyl calculator and category defaults exist.
- [x] Vinyl material options come from Pricing Foundation.
- [x] Use type, dimensions, weeding, colors, design, installation, surface, masking, quantity tiers, minimum, and sell method controls exist.
- [x] Stored pricing expansion tests cover cut vinyl calculations and cost snapshots.

### Accuracy Scenarios
- [ ] Price simple one-color indoor lettering.
- [ ] Price multi-color outdoor lettering.
- [ ] Compare simple, complex, and extreme weeding.
- [ ] Compare flat, glass, vehicle, textured, and curved surfaces.
- [ ] Compare masking required and not required.
- [ ] Compare install included and excluded.
- [ ] Verify inches and feet conversions.
- [ ] Verify quantity-tier boundaries.
- [ ] Verify minimum charge and rate-only behavior.
- [ ] Verify material, labor, overhead, waste, markup/margin, and profit breakdown.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm changing vinyl type changes price.
- [ ] Confirm every visible complexity and surface field changes price as intended.
- [ ] Confirm Add New opens Pricing Foundation.
- [ ] Confirm fields appear in dimensions → material → production complexity → install → price order.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 10 — Services Pricing

### Verified Coverage
- [x] Services calculator and category defaults exist.
- [x] Services support service type, labor role, hours, billing unit, travel, subcontracting, equipment, complexity, rush, minimum, and manual override behavior.
- [x] Stored iteration 128 contains broad services tests.
- [x] Stored services pricing tests cover detailed service behavior.

### Accuracy Scenarios
- [ ] Price general hourly labor.
- [ ] Price installation with its labor role and minimum.
- [ ] Price flat-fee service.
- [ ] Price per-mile delivery.
- [ ] Price per-trip delivery.
- [ ] Price subcontracted work with markup.
- [ ] Price equipment rental.
- [ ] Price file cleanup/design service.
- [ ] Price site survey with travel.
- [ ] Compare medium and difficult complexity.
- [ ] Compare normal and rush pricing.
- [ ] Verify manual override and service minimum.
- [ ] Save expected results as regression fixtures.

### Must Fix Or Decide
- [ ] Review any service cases that currently depend on workaround behavior documented in tests.
- [ ] Decide whether the server-JSON-only service-type library is acceptable for launch administration.
- [ ] Add UI controls for launch-critical service types that users must customize.

### UI QA
- [ ] Confirm progressive disclosure shows only fields relevant to the service.
- [ ] Confirm AI prefill never overwrites entered values unexpectedly.
- [ ] Confirm unknown AI service types are rejected clearly.
- [ ] Confirm travel, equipment, subcontract, and minimum charges are visible in breakdown.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 11 — Digital Print Pricing

### Verified Coverage
- [x] Digital print calculator and detailed category defaults exist.
- [x] Print media, laminate, substrate, quality, use type, dimensions, contour cut, trim, design, install, quantity tiers, minimum, and sell method controls exist.
- [x] Materials are selected from Pricing Foundation.
- [x] Add New links exist for media, laminate, and substrate.

### Accuracy Scenarios
- [ ] Price unlaminated indoor print.
- [ ] Price laminated outdoor print.
- [ ] Compare standard and high-quality print modes.
- [ ] Compare no contour cut and detailed contour cut.
- [ ] Compare trim/finish options.
- [ ] Compare design complexity.
- [ ] Compare install included and excluded.
- [ ] Verify inches and feet conversion.
- [ ] Verify quantity-tier boundaries.
- [ ] Verify minimum charge and rate-only behavior.
- [ ] Verify material, ink/consumable, laminate, labor, waste, overhead, and profit breakdown.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm incompatible media, laminate, and substrate choices are prevented or explained.
- [ ] Confirm laminate controls follow laminate-required state.
- [ ] Confirm Add New links work.
- [ ] Confirm the flow is dimensions → media/finish → production → install → price.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 12 — Banner Pricing

### Verified Coverage
- [x] Banner calculator and detailed category defaults exist.
- [x] Banner material, coating, hems, grommets, hardware, specialty sewing, wind slits, double-sided behavior, quantity tiers, and rush behavior exist.
- [x] Dedicated banner pricing tests cover broad calculation behavior.

### Accuracy Scenarios
- [ ] Price a basic 3x6 single-sided banner.
- [ ] Compare 13 oz, 18 oz, mesh, and other launch materials.
- [ ] Compare hem options.
- [ ] Compare grommet spacing options.
- [ ] Compare no coating and coating.
- [ ] Compare single-sided, same-art double-sided, and different-art double-sided.
- [ ] Add pole pockets, wind slits, specialty sewing, and hardware separately.
- [ ] Compare normal and rush pricing.
- [ ] Verify quantity-tier boundaries.
- [ ] Verify material, finishing, hardware, labor, waste, overhead, and profit breakdown.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm banner options appear only when applicable.
- [ ] Confirm material and hardware options come from Foundation.
- [ ] Confirm long add-on lists remain understandable.
- [ ] Confirm dimensions and square footage are clear.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 13 — Rigid Sign Pricing

### Verified Coverage
- [x] Rigid sign calculator and detailed category defaults exist.
- [x] Substrate, thickness, graphic method, finish, sidedness, double-sided art, shape, install, hardware, quantity tiers, minimum, and sell method controls exist.
- [x] Material/finish/hardware Add New links exist.
- [x] Stored main pricing tests include rigid-sign behavior.

### Accuracy Scenarios
- [ ] Price a basic single-sided coroplast sign.
- [ ] Compare each launch substrate and thickness.
- [ ] Compare direct print, mounted print, and cut-vinyl graphic methods.
- [ ] Compare finish options.
- [ ] Compare single-sided, same-art double-sided, and different-art double-sided.
- [ ] Compare rectangle and custom shapes.
- [ ] Compare no hardware and each launch hardware option.
- [ ] Compare install included and excluded.
- [ ] Verify quantity-tier boundaries.
- [ ] Verify minimum charge and rate-only behavior.
- [ ] Verify substrate, graphics, finish, hardware, labor, waste, overhead, and profit breakdown.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm incompatible substrate, finish, graphic, and hardware choices are prevented or explained.
- [ ] Confirm Add New links work.
- [ ] Confirm shape and sidedness fields change pricing.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 14 — Apparel Pricing

### Verified Coverage
- [x] Apparel calculator and detailed category defaults exist.
- [x] Apparel supports product type, brand/style, garment color, blank cost, decoration method, placement, quantity, stitch count, specialty options, names/numbers, setup, rush, and manual override.
- [x] Apparel blank materials come from Pricing Foundation.
- [x] Dedicated apparel tests cover quantity tiers, brands, placement, products, add-ons, setup, rush, override, and pricing methods.

### Accuracy Scenarios
- [ ] Price a short-sleeve tee using each launch decoration method.
- [ ] Compare at least two brands/styles.
- [ ] Compare front, back, and front-and-back placement.
- [ ] Compare quantity-tier boundaries.
- [ ] Compare standard and plus sizes.
- [ ] Price embroidery at multiple stitch counts.
- [ ] Add names/numbers.
- [ ] Add specialty finish, two-tone, patch, folding, and bagging separately.
- [ ] Compare normal and rush pricing.
- [ ] Verify setup fee behavior.
- [ ] Verify shop-table and cost-plus methods.
- [ ] Verify manual override and full breakdown.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm garment and decoration choices reveal only relevant fields.
- [ ] Confirm blank cost source is visible.
- [ ] Confirm quantity and per-piece totals are understandable.
- [ ] Confirm manual override does not hide the suggested price.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 15 — Vehicle Graphics Pricing

### Verified Coverage
- [x] Vehicle Graphics/Wraps calculator and detailed category defaults exist.
- [x] Vehicle type, coverage, custom coverage, make/model, material, laminate, perforated window scope, install, design, square-foot override, and purchased-item behavior exist.
- [x] Materials and laminates come from Pricing Foundation.
- [x] Stored pricing expansion tests cover vehicle-wrap calculations.

### Accuracy Scenarios
- [ ] Price door lettering.
- [ ] Price spot graphics.
- [ ] Price quarter, half, three-quarter, and full coverage.
- [ ] Price custom coverage percentage.
- [ ] Compare car, truck, van, trailer, and other launch vehicle types.
- [ ] Compare launch material and laminate choices.
- [ ] Add perforated window film and compare scopes.
- [ ] Compare design complexity.
- [ ] Compare install included and excluded.
- [ ] Verify square-foot override.
- [ ] Compare normal and rush pricing.
- [ ] Verify material, laminate, design, production, install, waste, overhead, and profit breakdown.
- [ ] Save expected results as regression fixtures.

### Must Fix Or Decide
- [ ] Confirm the Pricing Calculator vehicle path and Wrap Command Center pricing path use compatible definitions.
- [ ] Document which workflow owns wrap estimates, final quotes, actual materials, and actual profitability.
- [ ] Remove or clarify duplicate vehicle-pricing fields across those modules.

### UI QA
- [ ] Confirm coverage visuals/labels are understandable without shop-specific knowledge.
- [ ] Confirm incompatible material and laminate options are prevented or explained.
- [ ] Confirm custom coverage and square-foot override behavior is clear.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Section 16 — Custom And Other Pricing

### Verified Coverage
- [x] Custom/Other calculator exists.
- [x] Custom calculation supports material, labor, overhead, selling price, profit, and manual override.
- [x] Stored pricing expansion tests cover custom calculations.
- [x] Stored iteration 128 verifies manual override behavior.

### Known Bug
- [ ] Fix Custom/Other job-ticket creation so description persists.
- [ ] Confirm entry mode and manual override persist with the ticket if required.
- [ ] Add a passing regression test for ticket create/read round trip.

### Accuracy Scenarios
- [ ] Price custom work using material cost plus labor.
- [ ] Price purchased/outsourced custom work.
- [ ] Price quantity greater than one.
- [ ] Compare normal calculation and manual quote override.
- [ ] Verify minimum, markup/margin, overhead, and profit behavior.
- [ ] Add the result to an order/job ticket.
- [ ] Reload and confirm description and pricing snapshot persist.
- [ ] Save expected results as regression fixtures.

### UI QA
- [ ] Confirm the custom description is required before saving.
- [ ] Confirm users understand which values are estimates versus overrides.
- [ ] Confirm custom flow does not expose irrelevant category fields.
- [ ] Confirm no overlap, horizontal scrolling, low contrast, dead actions, or blank results.

---

## Cross-Section Data Contract Checklist

- [ ] Confirm Pricing Foundation is the only source of tenant pricing defaults.
- [ ] Confirm all calculators read the intended current Foundation fields.
- [ ] Confirm historical benchmarks never overwrite cost inputs.
- [ ] Confirm calculated order/job items save immutable cost snapshots.
- [ ] Confirm later Foundation changes do not rewrite historical snapshots.
- [ ] Confirm Product catalog retail pricing is intentionally separate or connected through a documented process.
- [ ] Confirm webstore assignment price overrides are intentional and traceable.
- [ ] Confirm inactive/deleted materials do not break old orders, templates, or products.
- [ ] Confirm tenant isolation on every pricing, template, import, material, product, and promo-code operation.
- [ ] Confirm role permissions match the sensitivity of cost, price, product, and promo data.
- [ ] Confirm all money uses consistent rounding and currency behavior.
- [ ] Confirm all quantities, dimensions, units, taxes, and percentages use consistent formats.

---

## Full Category Live Clickthrough

- [ ] Start with a new owner/admin account or clean test tenant.
- [ ] Complete shop defaults and shop-rate setup.
- [ ] Add launch materials and hardware.
- [ ] Configure every launch pricing category.
- [ ] Run and save one expected calculation per category.
- [ ] Save, load, favorite, and delete a template.
- [ ] Import historical invoices and review benchmarks.
- [ ] Create products and variants.
- [ ] Assign products to a webstore and confirm pricing.
- [ ] Create, validate, redeem, and retire a promo code.
- [ ] Click every visible button, icon, link, tab, menu, dialog action, and empty-state action.
- [ ] Confirm no dead links, blank screens, black screens, or unhandled errors.
- [ ] Confirm every visible action serves a clear purpose.
- [ ] Confirm duplicate/overlapping surfaces are removed or clearly differentiated.
- [ ] Confirm the overall workflow order makes sense to a first-time shop owner.

## Shared Visual And Accessibility Checklist

- [ ] Check all text, labels, placeholders, badges, helper text, and disabled states for sufficient contrast.
- [ ] Remove all light-on-light and dark-on-dark combinations.
- [ ] Check desktop, tablet, and mobile widths.
- [ ] Remove accidental page-level horizontal scrolling.
- [ ] Remove unexplained large empty spaces.
- [ ] Confirm tables use intentional internal scrolling where needed.
- [ ] Confirm long names, descriptions, keys, prices, and errors fit their containers.
- [ ] Confirm icon-only buttons have accessible names and tooltips.
- [ ] Confirm all inputs have visible labels.
- [ ] Confirm keyboard focus order follows workflow order.
- [ ] Confirm dialogs trap focus and return focus when closed.
- [ ] Confirm errors and status changes are understandable without color alone.
- [ ] Confirm loading, empty, success, error, and permission-denied states are complete.

## Automated Test Work

- [ ] Rerun `backend/tests/test_pricing.py`.
- [ ] Rerun `backend/tests/test_pricing_foundation.py`.
- [ ] Rerun `backend/tests/test_pricing_expansion.py`.
- [ ] Rerun `backend/tests/test_pricing_setup.py`.
- [ ] Rerun `backend/tests/test_iteration128_pricing_sections_g_h_i.py`.
- [ ] Rerun dedicated banner, apparel, and services pricing tests.
- [ ] Rerun product CRUD and product-description tests.
- [ ] Add dedicated Promo Codes tenant-isolation and redemption-integrity tests.
- [ ] Add regression test for Pricing Setup AI response parsing.
- [ ] Add historical-import upload-limit tests.
- [ ] Add regression test for promotional double-sided behavior.
- [ ] Add regression test for Custom/Other description persistence.
- [ ] Add browser tests for Pricing Foundation save/reload.
- [ ] Add browser tests for one calculation per launch category.
- [ ] Add browser tests for Product CRUD and variant handling.
- [ ] Add browser tests for Promo Code CRUD and permission denial.

## Launch Decision Gates

**Category 3 can ship when:**
- [ ] Every visible pricing category has an approved real-shop regression example.
- [ ] Promotional double-sided behavior is fixed or hidden.
- [ ] Custom/Other descriptions persist.
- [ ] Promo-code tenant and redemption safety issues are fixed.
- [ ] Historical import upload limits and response parsing are fixed.
- [ ] No visible action says "coming in next phase."
- [ ] Pricing Foundation saves and reloads every launch-critical value.
- [ ] Products can be created, priced, assigned, purchased, and retired safely.
- [ ] Every visible button/link has been clicked.
- [ ] No primary flow produces a dead link, blank screen, black screen, or unhandled error.
- [ ] Contrast, responsive layout, duplicate-feature, and workflow-order audits pass.

**Exact Work Order:**
1. Fix Promo Codes tenant scoping, redemption checks, and atomic limits.
2. Fix promotional double-sided pricing or hide its field.
3. Fix Custom/Other job-ticket description persistence.
4. Fix Pricing Setup AI response parsing.
5. Add historical import upload and processing limits.
6. Remove or complete Pricing Foundation "coming in next phase" actions.
7. Remove or development-gate pricing console output.
8. Verify hidden Foundation fields and document any remaining dependencies.
9. Build and approve one real-shop expected-price fixture per visible category.
10. Run full Pricing Foundation, Calculator, Products, and Promo Codes clickthrough.
11. Complete contrast, responsive layout, dead-link, duplicate-feature, and workflow-order audits.
12. Rerun automated tests and make the final Category 3 launch decision.

---

*Last updated: 2026-06-07 | No fixes applied yet — full clickthrough and accuracy QA pending*
 full clickthrough and accuracy QA pending*
