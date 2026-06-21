# SignGuyAI Rebuilt Data Layer Blueprint

Status: Proposed architecture contract  
Scope: MongoDB collections, Pydantic v2 document shapes, domain ownership, legacy reconciliation, and index enforcement  
Out of scope: API routes, frontend implementation, and migration execution code

## 1. Global Data Rules

These rules apply to every authoritative collection.

1. Every tenant-owned document MUST contain `tenant_id`.
2. IDs are application-generated UUIDv7 strings. MongoDB `_id` remains internal and is never exposed as a domain identifier.
3. Persist native UTC BSON datetimes, not ISO date strings.
4. Persist money as integer minor units (`amount_minor`, cents for USD). Never persist financial values as binary floats.
5. Every mutable aggregate has `created_at`, `updated_at`, and integer `version`.
6. Every migrated document has optional `migration` provenance.
7. Cross-domain references use IDs only. A domain may not embed another domain's mutable aggregate.
8. Small immutable snapshots are allowed only when required to preserve historical truth, such as the customer name printed on an accepted quote or the pricing rules used for a sold item.
9. Snapshots are never used as the authoritative current state of the referenced domain.
10. Unbounded arrays are prohibited. Activities, messages, files, transactions, tasks, and revisions use separate collections.
11. Soft deletion is used only where business restoration or auditability is required. Otherwise use explicit archival state.
12. All tenant-scoped unique indexes begin with `tenant_id`.
13. Schema changes are additive first, migrated second, and removed only after compatibility verification.

### Common Pydantic v2 Value Objects

```python
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

TenantId = Annotated[str, Field(min_length=1)]
EntityId = Annotated[str, Field(min_length=1)]
MoneyMinor = Annotated[int, Field(ge=0)]

def new_id() -> str:
    # Implementation should use UUIDv7 when the runtime standardizes on it.
    return str(uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DocumentModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

class MigrationSource(DocumentModel):
    source_collection: str
    source_id: str
    source_schema: str | None = None
    migrated_at: datetime = Field(default_factory=utc_now)
    warnings: list[str] = Field(default_factory=list)

class TenantDocument(DocumentModel):
    id: EntityId = Field(default_factory=new_id)
    tenant_id: TenantId
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    migration: MigrationSource | None = None
```

## 2. Conflict Area One: Orders, Tickets, Legacy Jobs, And Job Items

### Decision

`orders` and `order_items` are the only authoritative sellable-work aggregates.

- An **Order** represents the customer's commercial request and lifecycle.
- An **Order Item** represents one independently priced and produced deliverable.
- A "job ticket" becomes an `order_item`; ticket terminology may remain a UI label.
- Legacy `jobs` and `job_items` become read-only migration sources and are removed after reconciliation.
- Production tasks, quotes, invoices, files, approvals, and pricing calculations remain separate domain-owned collections referencing `order_id` and `order_item_id`.

### Canonical Schemas

```python
class OrderStatus(StrEnum):
    DRAFT = "draft"
    INTAKE = "intake"
    ESTIMATING = "estimating"
    AWAITING_CUSTOMER = "awaiting_customer"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    READY = "ready"
    FULFILLED = "fulfilled"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class FulfillmentMethod(StrEnum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    INSTALL = "install"
    SHIP = "ship"
    UNDECIDED = "undecided"

class ContactSnapshot(DocumentModel):
    display_name: str
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None

class FulfillmentDetails(DocumentModel):
    method: FulfillmentMethod = FulfillmentMethod.UNDECIDED
    requested_due_at: datetime | None = None
    event_at: datetime | None = None
    address: dict[str, str] | None = None
    notes: str | None = None

class OrderRecord(TenantDocument):
    order_number: str
    customer_id: EntityId | None = None
    customer_snapshot: ContactSnapshot
    status: OrderStatus = OrderStatus.INTAKE
    source: str
    title: str
    fulfillment: FulfillmentDetails = Field(default_factory=FulfillmentDetails)
    customer_notes: str | None = None
    internal_notes: str | None = None
    created_by_user_id: EntityId | None = None
    archived_at: datetime | None = None

class OrderItemStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_INFO = "awaiting_info"
    AWAITING_PROOF = "awaiting_proof"
    AWAITING_APPROVAL = "awaiting_approval"
    READY_FOR_PRODUCTION = "ready_for_production"
    IN_PRODUCTION = "in_production"
    IN_QC = "in_qc"
    READY = "ready"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    REWORK = "rework"
    CANCELLED = "cancelled"

class Dimensions(DocumentModel):
    width_microns: int | None = Field(default=None, ge=0)
    height_microns: int | None = Field(default=None, ge=0)
    depth_microns: int | None = Field(default=None, ge=0)
    area_square_microns: int | None = Field(default=None, ge=0)

class OrderItemRecord(TenantDocument):
    order_id: EntityId
    item_number: str
    category_code: str
    subcategory_code: str | None = None
    title: str
    description: str | None = None
    quantity: int = Field(default=1, gt=0)
    unit_code: str = "each"
    status: OrderItemStatus = OrderItemStatus.DRAFT
    priority: str = "normal"
    specifications: dict[str, Any] = Field(default_factory=dict)
    dimensions: Dimensions | None = None
    assigned_user_ids: list[EntityId] = Field(default_factory=list)
    pricing_snapshot_id: EntityId | None = None
    workflow_template_id: EntityId | None = None
    source_item_id: EntityId | None = None
    source_item_relation: str | None = None
```

### Boundary And Invariants

- `order_items.order_id` is required and tenant-consistent.
- Orders do not embed items and do not maintain an authoritative `item_ids` array.
- Quotes and invoices reference the order and item IDs from Billing-owned collections.
- Production tasks reference `order_id` and `order_item_id`.
- Files and approvals reference the order/item IDs from Documents-owned collections.
- `customer_snapshot` is immutable historical display data; Customer remains authoritative.
- Order totals, progress, payment state, and item counts are read-model projections, not authoritative fields on `orders`.
- Item specifications are category-specific but validated by a versioned specification schema identified by `category_code`.

### Legacy Mapping

| Legacy source | New target | Mapping rule |
|---|---|---|
| `orders` | `orders` | Normalize statuses, dates, fulfillment, and customer snapshot. Drop linked-ID arrays after dependent records reference the order directly. |
| `job_tickets` | `order_items` | One ticket becomes one order item. `ticket_number` becomes `item_number`; `specs` becomes `specifications`. |
| `jobs` | `orders` | One legacy job becomes one order unless it already maps to an existing order. Preserve source in `migration`. |
| `job_items` | `order_items` | One legacy job item becomes one order item linked to the migrated job/order. |
| Job `line_items` embedded array | `order_items` | Explode into separate order-item records. |
| `job_notes`, `job_activities`, `order_activities` | `order_events` | Normalize into an append-only event/audit collection owned by Order. |
| `pricing_data`, `cost_snapshot`, `pricing_snapshot` | `pricing_snapshots` | Convert to immutable Pricing-owned snapshots and set `order_items.pricing_snapshot_id`. |
| `artwork_files`, `proof_files`, `linked_order_file_ids` | Documents-owned references | Migrate files to authoritative file records; never retain file blobs or growing ID arrays on order items. |
| `estimated_price`, `manual_quote_override` | Pricing/Billing | Preserve in pricing snapshot or quote line; do not treat as current order-item truth. |

Legacy collections remain read-only during migration. New writes must never dual-write to both models.

## 3. Conflict Area Two: Plans, Product Lines, Tiers, And Founder Overrides

### Decision

The rebuilt model separates:

1. **Plan catalog:** versioned commercial definitions.
2. **Tenant subscription:** what the tenant purchased and its billing state.
3. **Entitlement grants:** explicit exceptions, promotions, trials, and support overrides.
4. **Usage counters:** metered feature consumption.

`tier`, `product_line`, and `is_founder` are removed from `tenants`. Founder status becomes a price-lock/promotion grant, never a global feature-gating bypass.

### Canonical Schemas

```python
class ProductLineCode(StrEnum):
    OS = "os"
    WEBSTORES = "webstores"
    AI_STUDIO = "ai_studio"

class EntitlementMode(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    METERED = "metered"

class EntitlementDefinition(DocumentModel):
    key: str
    mode: EntitlementMode
    limit: int | None = Field(default=None, ge=0)
    period: str | None = None

class PlanPrice(DocumentModel):
    currency: str = "usd"
    interval: str
    amount_minor: MoneyMinor
    external_price_id: str | None = None

class PlanCatalogRecord(DocumentModel):
    id: EntityId = Field(default_factory=new_id)
    plan_code: str
    revision: int = Field(ge=1)
    product_line: ProductLineCode
    display_name: str
    active: bool = True
    prices: list[PlanPrice]
    entitlements: list[EntitlementDefinition]
    effective_from: datetime
    effective_to: datetime | None = None

class SubscriptionItem(DocumentModel):
    plan_code: str
    plan_revision: int
    external_subscription_item_id: str | None = None
    quantity: int = Field(default=1, gt=0)

class PriceLock(DocumentModel):
    grant_code: str
    price_amount_minor: MoneyMinor | None = None
    discount_percent_basis_points: int | None = Field(default=None, ge=0, le=10_000)
    locked_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class TenantSubscriptionRecord(TenantDocument):
    status: str
    billing_interval: str
    items: list[SubscriptionItem]
    external_customer_id: str | None = None
    external_subscription_id: str | None = None
    trial_start_at: datetime | None = None
    trial_end_at: datetime | None = None
    current_period_start_at: datetime | None = None
    current_period_end_at: datetime | None = None
    cancel_at_period_end: bool = False
    price_locks: list[PriceLock] = Field(default_factory=list)

class EntitlementGrantRecord(TenantDocument):
    entitlement_key: str
    mode: EntitlementMode
    limit: int | None = Field(default=None, ge=0)
    reason_code: str
    starts_at: datetime
    ends_at: datetime | None = None
    granted_by_user_id: EntityId | None = None

class UsageCounterRecord(TenantDocument):
    entitlement_key: str
    period_start_at: datetime
    period_end_at: datetime
    consumed: int = Field(default=0, ge=0)
```

### Entitlement Resolution Rule

Effective entitlements are calculated in this order:

1. Load active subscription items and their exact plan revisions.
2. Merge plan entitlements using the most permissive purchased entitlement.
3. Apply time-valid entitlement grants.
4. Compare metered entitlements with usage counters.
5. Optionally cache the result in a disposable read-model collection keyed by subscription/grant versions.

The cache is never authoritative.

### Legacy Mapping

| Legacy field/source | New target |
|---|---|
| `tenants.plan` containing `starter/pro/business` | Map to `os_starter/os_pro/os_business` subscription item. |
| `tenants.plan` containing `os_*`, `ws_*`, or `ai_*` | Map directly to a plan-catalog code. |
| `tenants.product_line` | Derived from purchased plan items; remove from tenant record. |
| `tenants.is_founder`, `founder_number`, `founder_locked_at` | Create `PriceLock(grant_code="founder")`; preserve founder number in metadata. |
| `users.is_founder` | Remove. Founder commercial status belongs to the tenant subscription, not users. |
| `subscriptions.plan`, `subscriptions.tier` | Normalize to subscription items referencing exact plan revisions. |
| `has_ai_addon` | Add AI plan/add-on as a separate subscription item. |
| Tier feature definitions | Convert once into versioned plan catalog entitlements. |
| `tenant_usage`, `user_credits`, `ai_credits` | Normalize to entitlement usage and AI credit ledger records according to ownership. |
| Founders-only environment bypass | Remove from persisted business rules. Use explicit launch grants if temporary universal access is required. |

## 4. Conflict Area Three: Canonical Pricing Configuration And Snapshots

### Decision

Pricing has three distinct records:

1. **Pricing profile revisions:** versioned tenant configuration used to calculate prices.
2. **Pricing templates:** reusable input presets.
3. **Pricing snapshots:** immutable calculation evidence attached to sold/quoted work.

There is exactly one active pricing profile revision per tenant. Editing pricing creates a new revision; it never mutates historical revisions used by snapshots.

### Canonical Schemas

```python
class RateComponent(DocumentModel):
    code: str
    label: str
    unit_code: str
    cost_minor: MoneyMinor
    sell_rate_minor: MoneyMinor | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class LaborRate(DocumentModel):
    role_code: str
    hourly_cost_minor: MoneyMinor
    hourly_sell_minor: MoneyMinor
    minimum_minutes: int = Field(default=0, ge=0)
    billing_increment_minutes: int = Field(default=1, gt=0)

class PricingRule(DocumentModel):
    rule_code: str
    rule_type: str
    priority: int = 0
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)

class PricingProfileRecord(TenantDocument):
    profile_code: str = "default"
    revision: int = Field(ge=1)
    status: str
    currency: str = "usd"
    materials: list[RateComponent] = Field(default_factory=list)
    hardware: list[RateComponent] = Field(default_factory=list)
    labor_rates: list[LaborRate] = Field(default_factory=list)
    rules: list[PricingRule] = Field(default_factory=list)
    category_settings: dict[str, dict[str, Any]] = Field(default_factory=dict)
    activated_at: datetime | None = None
    superseded_at: datetime | None = None

class PricingTemplateRecord(TenantDocument):
    name: str
    category_code: str
    specification_schema_version: int
    input_values: dict[str, Any]
    default_quantity: int = Field(default=1, gt=0)
    active: bool = True

class CostLine(DocumentModel):
    component_code: str
    label: str
    kind: str
    quantity_microunits: int
    unit_code: str
    unit_cost_minor: MoneyMinor
    total_cost_minor: MoneyMinor

class PriceLine(DocumentModel):
    label: str
    amount_minor: MoneyMinor

class PricingSnapshotRecord(TenantDocument):
    order_id: EntityId
    order_item_id: EntityId
    pricing_profile_id: EntityId
    pricing_profile_revision: int
    calculator_version: str
    category_code: str
    specification_schema_version: int
    normalized_inputs: dict[str, Any]
    cost_lines: list[CostLine]
    price_lines: list[PriceLine]
    subtotal_minor: MoneyMinor
    tax_minor: MoneyMinor = 0
    total_minor: MoneyMinor
    true_cost_minor: MoneyMinor
    profit_minor: int
    margin_basis_points: int
    override_amount_minor: MoneyMinor | None = None
    override_reason: str | None = None
    calculated_at: datetime = Field(default_factory=utc_now)
```

### Pricing Invariants

- A profile revision becomes immutable once activated.
- A pricing snapshot is always immutable.
- Quotes and invoices copy immutable commercial line snapshots from Pricing; they do not recalculate historical prices.
- Inventory may reference a pricing material `component_code`, but Pricing does not own inventory quantities or vendor costs.
- Category-specific inputs are validated against versioned schemas. `dict[str, Any]` is only the storage envelope; validation occurs before persistence.
- All measurements use canonical integer base units. Legacy inches/square feet are converted during migration.
- Every override stores amount, reason, actor, and timestamp.

### Legacy Mapping

| Legacy source/field | New target |
|---|---|
| `pricing_configuration` | Create active `pricing_profiles` revision. |
| `pricing_defaults` | Use only as seed input when no tenant configuration exists; never migrate as a second active profile. |
| `pricing_templates` | Normalize to `pricing_templates` with schema version. |
| `pricing_data` | Normalize into snapshot `normalized_inputs` or template `input_values`. |
| `pricing_calculation`, `cost_snapshot`, `pricing_snapshot` | Normalize into immutable `pricing_snapshots`. |
| `length_inches` | Map to canonical height measurement. |
| `square_footage` | Map to canonical area measurement. |
| `additional_costs` | Split into known cost lines where evidence exists; otherwise preserve as `legacy_additional_cost` line with migration warning. |
| `production_cost`, `total_cost`, `true_cost` | Map to `true_cost_minor`; preserve disagreement as migration warning. |
| `selling_price`, `estimated_price`, `manual_quote_override` | Map to total or explicit override according to source context. |
| Float currency fields | Convert once to integer minor units using decimal rounding rules. |

## 5. Authoritative Domain Boundaries

The following are the only authoritative business domains.

| Domain | Owns authoritative collections |
|---|---|
| Customer | `customers`, `customer_contacts`, `customer_notes`, `customer_tags` |
| Order | `orders`, `order_items`, `order_events` |
| Pricing | `pricing_profiles`, `pricing_templates`, `pricing_snapshots`, `pricing_component_cost_history` |
| Production | `workflow_templates`, `production_tasks`, `production_events`, `inventory_items`, `inventory_lots`, `inventory_locations`, `inventory_transactions`, `material_requirements`, `inventory_shortages`, `inventory_vendors`, `purchase_orders` |
| Billing | `quotes`, `invoices`, `payments`, `payment_events`, `subscriptions`, `entitlement_grants`, `usage_counters`, `plan_catalog`, `promo_codes`, `financial_entries` |
| Workforce | `employees`, `employee_schedules`, `time_entries`, `payroll_periods`, `payroll_entries`, `payroll_signoffs` |
| Webstore | `products`, `webstores`, `webstore_products`, `webstore_orders`, `webstore_payouts`, `webstore_owner_accounts`, `webstore_events` |
| Portal | `portal_accounts`, `portal_sessions`, `conversations`, `conversation_messages`, `customer_notifications`, `appointments`, `form_requests`, `form_responses` |
| Documents | `files`, `documents`, `document_templates`, `proofs`, `approvals`, `signatures`, `questionnaires`, `questionnaire_responses` |
| AI | `ai_requests`, `ai_results`, `ai_usage_ledger`, `ai_action_audit`, `assistant_sessions`, `assistant_messages`, `assistant_preferences` |
| Platform Administration | `tenants`, `users`, `roles`, `platform_settings`, `admin_audit_log`, `impersonation_sessions`, `email_logs`, `analytics_events`, `schema_migrations`, `index_registry` |

### Cross-Domain Reference Rules

1. A reference is stored on the dependent/child side only. Avoid authoritative bidirectional ID arrays.
2. Every cross-domain lookup must include `tenant_id` plus referenced `id`.
3. Cross-domain deletion is never implemented as an implicit cascade. The owning domain publishes a deletion/archive decision and dependent domains handle it explicitly.
4. Cross-domain updates may not mutate another domain's collection directly. They invoke that domain's application service or consume an event.
5. Immutable snapshots may copy display/commercial facts, but must include the source ID and snapshot timestamp.
6. Read models and analytics projections may combine domains, but are disposable and cannot accept authoritative writes.
7. Files are always Documents-owned. Other domains store file IDs only.
8. Users and tenants are Platform-owned. Other domains store `tenant_id` and actor/user IDs only.
9. Customer is authoritative for current customer identity. Orders, quotes, and invoices may keep immutable customer snapshots.
10. Billing is authoritative for payment/subscription state. Orders may expose derived payment status only through read models.
11. Production is authoritative for work progress and inventory. Orders may expose derived progress only through read models.

## 6. Startup Index Enforcement

### Strategy

Indexes are declared as version-controlled data beside each domain's schema definitions, then enforced by one central index manager during deployment/startup.

Each index specification includes:

- collection
- stable index name
- ordered keys
- uniqueness
- partial filter expression
- TTL settings
- collation
- owning domain
- index schema version

Startup behavior:

1. Acquire a distributed lease in `index_registry` so only one process reconciles indexes.
2. Read the desired index manifest and MongoDB's actual indexes.
3. Create missing safe indexes using stable names.
4. Validate key order and options for existing indexes.
5. Record successful reconciliation and manifest checksum.
6. Fail readiness for missing required unique/security indexes.
7. Warn, but do not auto-drop, unexpected or obsolete indexes.
8. Destructive index changes require an explicit numbered migration and preflight duplicate scan.
9. Release the lease and expose index status through operational health checks.

Do not run expensive index builds independently in every API worker. In production, the preferred execution point is a dedicated pre-deploy migration job. Startup enforcement remains a final verifier.

### Required Foundational Indexes

```text
All tenant collections:
  (tenant_id, id) UNIQUE

orders:
  (tenant_id, order_number) UNIQUE
  (tenant_id, customer_id, created_at DESC)
  (tenant_id, status, updated_at DESC)

order_items:
  (tenant_id, order_id, item_number) UNIQUE
  (tenant_id, status, updated_at DESC)
  (tenant_id, assigned_user_ids, status)

pricing_profiles:
  (tenant_id, profile_code, revision) UNIQUE
  (tenant_id, profile_code, status) PARTIAL UNIQUE where status="active"

pricing_snapshots:
  (tenant_id, order_item_id, calculated_at DESC)
  (tenant_id, pricing_profile_id, pricing_profile_revision)

subscriptions:
  (tenant_id, status)
  (external_subscription_id) UNIQUE PARTIAL where present

entitlement_grants:
  (tenant_id, entitlement_key, starts_at, ends_at)

usage_counters:
  (tenant_id, entitlement_key, period_start_at, period_end_at) UNIQUE

production_tasks:
  (tenant_id, order_item_id, status, stage_sequence)
  (tenant_id, assigned_user_id, status, due_at)

customers:
  (tenant_id, normalized_email) PARTIAL UNIQUE where normalized_email exists
  (tenant_id, normalized_name)

webstores:
  (tenant_id, slug) UNIQUE
  (tenant_id, status, updated_at DESC)

webstore_orders:
  (tenant_id, webstore_id, created_at DESC)
  (external_checkout_id) PARTIAL UNIQUE where present

payments:
  (tenant_id, invoice_id, created_at DESC)
  (external_payment_id) PARTIAL UNIQUE where present

conversation_messages:
  (tenant_id, conversation_id, created_at)

files:
  (tenant_id, owner_type, owner_id, created_at DESC)

schema_migrations:
  (migration_id) UNIQUE

password/session/token collections:
  token hash UNIQUE
  expires_at TTL
```

### Index Governance

- CI validates that every authoritative collection has an owner and index manifest.
- CI rejects unnamed indexes and duplicate index names.
- Query-review tooling records slow queries and requires an `explain()` plan before adding indexes.
- Index cardinality and write amplification are reviewed quarterly.
- Search requirements that exceed compound/text indexes move to a dedicated search projection, not ad hoc regex scans on authoritative collections.

## 7. Migration And Cutover Contract

1. Snapshot and inventory current collection counts and orphaned references.
2. Establish deterministic legacy-to-new ID maps.
3. Migrate Platform, Customer, and plan catalog first.
4. Migrate pricing profiles before order items so snapshots can reference valid revisions.
5. Migrate orders/jobs into orders, then tickets/job-items into order items.
6. Migrate Production, Billing, Documents, Portal, Workforce, Webstore, and AI dependents using ID maps.
7. Run reconciliation reports for counts, totals, tenant isolation, orphan references, and financial sums.
8. Freeze legacy writes.
9. Perform final delta migration.
10. Switch reads/writes to canonical collections.
11. Retain legacy collections read-only for a defined rollback window.
12. Remove compatibility code only after production reconciliation passes.

## 8. Final Lock Decisions

- Canonical work model: `orders` plus `order_items`.
- Canonical subscription model: versioned `plan_catalog` plus `subscriptions`, `entitlement_grants`, and `usage_counters`.
- Canonical pricing model: versioned `pricing_profiles` plus immutable `pricing_snapshots`.
- No `tier`, `product_line`, or founder feature-bypass fields on tenants/users.
- No mutable cross-domain aggregates embedded in another domain.
- No unbounded arrays or authoritative bidirectional reference lists.
- No float money or ISO-string timestamps in rebuilt authoritative collections.
- No unmanaged indexes.
