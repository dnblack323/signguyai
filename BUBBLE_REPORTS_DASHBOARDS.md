# Sign Guy AI - Reports & Dashboards Specification

## OVERVIEW

This document defines recommended reports and dashboards for Sign Guy AI. These extend beyond the current MVP implementation to provide comprehensive business intelligence.

**Architecture Note (Updated March 2026):**
The app now uses a 4-layer production system:
- **Layer 1: Order** — Master container for customer requests
- **Layer 2: Job Tickets** — Individual production items within an order
- **Layer 3: Quotes/Invoices** — Financial documents generated from tickets
- **Layer 4: Production Tasks** — Department-level workflow stages

**Report Categories:**
1. Order Pipeline Overview
2. Revenue Summaries
3. Outstanding Invoices
4. Payroll Summaries
5. Productivity Metrics

---

## 1. ORDER PIPELINE OVERVIEW

### 1.1 Pipeline Kanban Dashboard

**Purpose:** Visual overview of all orders by status stage

**Data Sources:**
- `Order` (primary)
- `Customer` (for customer name)
- `JobTicket` (for item count)

**Filters:**
| Filter | Type | Options | Default |
|--------|------|---------|---------|
| Date Range | date picker | Any range | Last 30 days |
| Customer | dropdown | All customers | All |
| Include Archived | toggle | yes/no | no |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Orders per Stage | COUNT(Orders) GROUP BY status |
| Total Pipeline Value | SUM(Order.subtotal) WHERE status NOT IN [complete, archived] |
| Value per Stage | SUM(Order.subtotal) GROUP BY status |
| Average Days in Stage | AVG(days since status changed) GROUP BY status |
| Conversion Rate | Orders moved to next stage / Total orders per stage |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ORDER PIPELINE OVERVIEW                          [Date Range] [Customer ▼]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ QUOTED   │  │ APPROVED │  │IN PROD   │  │INSTALLED │  │ COMPLETE │     │
│  │          │  │          │  │          │  │          │  │          │     │
│  │  12 orders │  │  8 orders  │  │  15 orders │  │  3 orders  │  │  45 orders │     │
│  │  $24,500 │  │  $18,200 │  │  $42,100 │  │  $8,400  │  │  $95,000 │     │
│  │          │  │          │  │          │  │          │  │          │     │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │     │
│  │ │ Ord1 │ │  │ │ Ord4 │ │  │ │ Ord7 │ │  │ │Ord12│ │  │ │Ord15│ │     │
│  │ │$2,500│ │  │ │$3,100│ │  │ │$4,200│ │  │ │$2,800│ │  │ │$3,500│ │     │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │     │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │          │  │ ┌──────┐ │     │
│  │ │ Ord2 │ │  │ │ Ord5 │ │  │ │ Ord8 │ │  │          │  │ │Ord16│ │     │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │          │  │ └──────┘ │     │
│  │   ...    │  │   ...    │  │   ...    │  │          │  │   ...    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ PIPELINE SUMMARY                                                            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ Active Orders │ │Pipeline Val │ │ Avg Order Val │ │ Avg Days to │            │
│ │     38      │ │  $93,200    │ │   $2,453    │ │  Complete   │            │
│ │             │ │             │ │             │ │    12 days  │            │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Pipeline Funnel Report

**Purpose:** Track conversion rates through pipeline stages

**Data Sources:**
- `Order`
- `OrderActivity` (for stage transition timestamps)

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Last 90 days |
| Customer Type | dropdown | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Stage Entry Count | COUNT(Orders) that entered each stage in period |
| Stage Exit Count | COUNT(Orders) that left each stage in period |
| Conversion Rate | Exit Count / Entry Count per stage |
| Drop-off Rate | 1 - Conversion Rate |
| Average Time in Stage | AVG(time between stage entry and exit) |
| Bottleneck Stage | Stage with lowest conversion rate |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ PIPELINE FUNNEL                                  [Date Range]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     ┌─────────────────────────────────────┐                    │
│     │           QUOTED (50)               │  100%              │
│     │           $125,000                  │                    │
│     └──────────────┬──────────────────────┘                    │
│                    │ 72% conversion                            │
│        ┌───────────▼───────────────┐                           │
│        │      APPROVED (36)        │  72%                      │
│        │        $90,000            │                           │
│        └───────────┬───────────────┘                           │
│                    │ 89% conversion                            │
│           ┌────────▼────────────┐                              │
│           │  IN PRODUCTION (32) │  64%                         │
│           │      $80,000        │                              │
│           └────────┬────────────┘                              │
│                    │ 94% conversion                            │
│              ┌─────▼─────────┐                                 │
│              │ INSTALLED (30)│  60%                            │
│              │   $75,000     │                                 │
│              └─────┬─────────┘                                 │
│                    │ 100% conversion                           │
│                ┌───▼───────┐                                   │
│                │COMPLETE(30)│  60%                             │
│                │  $75,000   │                                  │
│                └────────────┘                                  │
│                                                                 │
│  INSIGHTS:                                                      │
│  • Bottleneck: Quoted → Approved (28% drop-off)                │
│  • Strongest: Installed → Complete (100%)                      │
│  • Avg cycle time: 14 days                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1.3 Orders by Due Date Report

**Purpose:** Identify upcoming deadlines and overdue orders

**Data Sources:**
- `Order`
- `Customer`
- `JobTicket`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Status | multi-select | Active statuses |
| Look-ahead Days | number | 14 |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Overdue Orders | COUNT(Orders) WHERE due_date < TODAY AND status NOT IN [complete, archived] |
| Due This Week | COUNT(Orders) WHERE due_date BETWEEN TODAY AND TODAY+7 |
| Due Next Week | COUNT(Orders) WHERE due_date BETWEEN TODAY+7 AND TODAY+14 |
| No Due Date | COUNT(Orders) WHERE due_date IS NULL AND status NOT IN [complete, archived] |
| Overdue Value | SUM(subtotal) of overdue orders |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ORDERS BY DUE DATE                                                │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │  🔴 OVERDUE │ │ ⚠️ THIS WEEK│ │ 📅 NEXT WEEK│ │ ⚪ NO DATE  ││
│ │     5       │ │     8       │ │     12      │ │     3       ││
│ │   $12,400   │ │   $19,500   │ │   $28,000   │ │   $7,200    ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ OVERDUE ORDERS (Immediate Attention Required)                     │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Order Name          │ Customer    │ Due Date │ Days Over│ $ │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Smith Storefront  │ Smith LLC   │ Dec 10   │ 5 days   │2.4k│  │
│ │ Banner Order #42  │ ABC Corp    │ Dec 12   │ 3 days   │1.1k│  │
│ │ Vehicle Wrap      │ Johnson     │ Dec 13   │ 2 days   │4.2k│  │
│ └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│ THIS WEEK                                                       │
│ [Timeline view with orders plotted by due date]                   │
│                                                                 │
│ Mon   Tue   Wed   Thu   Fri   Sat   Sun                        │
│  │     │     │     │     │     │     │                         │
│  ●─────●     ●     ●─────●─────●     │                         │
│  2     1     1     3     1           │                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. REVENUE SUMMARIES

### 2.1 Revenue Dashboard

**Purpose:** Comprehensive view of business revenue and trends

**Data Sources:**
- `Invoice` (primary revenue source)
- `SalesEntry` (daily sales)
- `Order` (pipeline value)
- `Quote` (potential revenue)

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current month |
| Comparison Period | toggle | Previous period |
| Customer | dropdown | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Total Revenue | SUM(Invoice.total) WHERE status = paid AND paid_date IN range |
| Invoiced (Unpaid) | SUM(Invoice.total) WHERE status IN [sent, overdue] |
| Pipeline Value | SUM(Order.subtotal) WHERE status NOT IN [complete, archived] |
| Quote Value | SUM(Quote.total) WHERE status IN [draft, sent] |
| Average Invoice | AVG(Invoice.total) for period |
| Revenue Growth | (This Period - Last Period) / Last Period × 100 |
| Daily Sales | SUM(SalesEntry.amount) per day |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ REVENUE DASHBOARD                              [Dec 2024 ▼] [vs Nov 2024]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│ │ 💰 COLLECTED  │ │ 📄 INVOICED   │ │ 🔧 PIPELINE   │ │ 📝 QUOTED     │    │
│ │   $45,200     │ │   $18,400     │ │   $93,200     │ │   $24,500     │    │
│ │   ▲ 12%       │ │   ▼ 5%        │ │   ▲ 8%        │ │   ▲ 15%       │    │
│ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│ REVENUE TREND (Last 12 Months)                                              │
│                                                                             │
│  $50k ┤                                            ╭──╮                    │
│       │                              ╭──╮    ╭──╮  │  │                    │
│  $40k ┤                    ╭──╮ ╭──╮ │  │╭──╮│  │──╯  │                    │
│       │              ╭──╮  │  │ │  │ │  ││  ││  │     │                    │
│  $30k ┤         ╭──╮ │  │──╯  │ │  │─╯  ││  ╰╯  │     │                    │
│       │    ╭──╮ │  │ │  │     │─╯  │    ╰╯       │     │                    │
│  $20k ┤────╯  │─╯  │─╯  │     │    │             │     │                    │
│       │       │    │    │                              │                    │
│  $10k ┤       │                                        │                    │
│       └───────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────     │
│        Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec          │
│                                                                             │
│        ── Collected    ╌╌ Invoiced    ░░ Target                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ REVENUE BY CATEGORY                    │ TOP CUSTOMERS THIS PERIOD          │
│                                        │                                    │
│ ┌────────────────────────────────┐    │ 1. ABC Corporation    $12,400      │
│ │ Vehicle Wraps      ████████ 35%│    │ 2. Smith LLC          $8,200       │
│ │ Channel Letters    ██████   28%│    │ 3. Johnson & Sons     $6,100       │
│ │ Banners           ████     18%│    │ 4. Downtown Retail    $4,800       │
│ │ Window Graphics   ███      12%│    │ 5. Metro Signs Co     $3,900       │
│ │ Other             ██        7%│    │                                    │
│ └────────────────────────────────┘    │ [View All →]                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Daily Sales Report

**Purpose:** Track daily cash flow and sales activity

**Data Sources:**
- `SalesEntry`
- `Invoice` (payments received)

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current week |
| Entry Type | multi-select | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Daily Total | SUM(SalesEntry.amount) per day |
| Daily Tax | SUM(SalesEntry.tax_amount) per day |
| Daily Average | AVG of daily totals |
| Best Day | MAX daily total |
| Worst Day | MIN daily total (excluding $0) |
| Week Total | SUM of daily totals |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ DAILY SALES REPORT                          [This Week ▼]       │
├─────────────────────────────────────────────────────────────────┤
│ WEEK SUMMARY: $12,450 (+8% vs last week)                        │
│ Tax Collected: $1,120                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  $3k ┤         ╭───╮                                           │
│      │    ╭───╮│   │    ╭───╮                                  │
│  $2k ┤╭───│   ││   │╭───│   │╭───╮                             │
│      ││   │   ││   ││   │   ││   │                             │
│  $1k ┤│   │   ││   ││   │   ││   │                             │
│      ││   │   ││   ││   │   ││   │                             │
│   $0 ┼┴───┴───┴┴───┴┴───┴───┴┴───┴───────                      │
│       Mon   Tue   Wed   Thu   Fri   Sat   Sun                  │
│      $1,850 $2,100 $2,650 $1,950 $2,400 $1,500  --             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ DAILY BREAKDOWN                                                 │
│ ┌─────────┬──────────┬─────────┬──────────────────────────────┐│
│ │ Date    │ Sales    │ Tax     │ Notes                        ││
│ ├─────────┼──────────┼─────────┼──────────────────────────────┤│
│ │ Dec 15  │ $2,650   │ $238    │ Best day - 3 vehicle wraps   ││
│ │ Dec 14  │ $1,950   │ $175    │                              ││
│ │ Dec 13  │ $2,400   │ $216    │ ABC Corp final payment       ││
│ │ ...     │ ...      │ ...     │                              ││
│ └─────────┴──────────┴─────────┴──────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Revenue by Customer Report

**Purpose:** Identify top customers and revenue concentration

**Data Sources:**
- `Invoice` (paid)
- `Customer`
- `Order`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | YTD |
| Minimum Revenue | number | $0 |
| Customer Status | multi-select | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Revenue per Customer | SUM(Invoice.total) WHERE paid, GROUP BY customer |
| Order Count per Customer | COUNT(Orders) GROUP BY customer |
| Average Order Value | Revenue / Order Count |
| Customer Lifetime Value | Total revenue from customer (all time) |
| Revenue Concentration | Top 20% customers / Total revenue |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ REVENUE BY CUSTOMER                              [YTD 2024 ▼]   │
├─────────────────────────────────────────────────────────────────┤
│ CONCENTRATION: Top 5 customers = 62% of revenue                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Customer         │ Revenue  │ Orders │ Avg Order │ % Total   │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ ABC Corporation  │ $48,200  │  15  │ $3,213  │ 22% ████  │  │
│ │ Smith LLC        │ $32,100  │  12  │ $2,675  │ 15% ███   │  │
│ │ Johnson & Sons   │ $24,500  │   8  │ $3,062  │ 11% ██    │  │
│ │ Downtown Retail  │ $18,900  │  10  │ $1,890  │  9% ██    │  │
│ │ Metro Signs Co   │ $12,400  │   6  │ $2,066  │  6% █     │  │
│ │ [Other 45]       │ $82,900  │  89  │   $931  │ 37% ████  │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ CUSTOMER REVENUE DISTRIBUTION                                   │
│ ┌─────────────────────────────────────────────────────────┐    │
│ │                                                         │    │
│ │  ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │    │
│ │  Top 20% customers (10)  │  Remaining 80% (40)         │    │
│ │       68% revenue        │     32% revenue             │    │
│ │                                                         │    │
│ └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. OUTSTANDING INVOICES

### 3.1 Accounts Receivable Dashboard

**Purpose:** Track all unpaid invoices and aging

**Data Sources:**
- `Invoice` (status ≠ paid)
- `Customer`
- `Order`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Status | multi-select | sent, overdue |
| Customer | dropdown | All |
| Minimum Amount | number | $0 |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Total Outstanding | SUM(Invoice.total - Invoice.amount_paid) WHERE status IN [sent, overdue] |
| Current (0-30 days) | Outstanding WHERE due_date > TODAY-30 |
| 31-60 Days | Outstanding WHERE due_date BETWEEN TODAY-60 AND TODAY-30 |
| 61-90 Days | Outstanding WHERE due_date BETWEEN TODAY-90 AND TODAY-60 |
| Over 90 Days | Outstanding WHERE due_date < TODAY-90 |
| Average Days Outstanding | AVG(TODAY - Invoice.created_at) for unpaid |
| Collection Rate | Paid this period / (Paid + Still Outstanding) |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ACCOUNTS RECEIVABLE                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ TOTAL OUTSTANDING: $42,650                                                  │
│                                                                             │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 🟢 CURRENT  │ │ 🟡 31-60    │ │ 🟠 61-90    │ │ 🔴 90+      │            │
│ │  (0-30 days)│ │    DAYS     │ │    DAYS     │ │    DAYS     │            │
│ │             │ │             │ │             │ │             │            │
│ │  $28,400    │ │   $8,200    │ │   $4,100    │ │   $1,950    │            │
│ │  18 invoices│ │  5 invoices │ │  2 invoices │ │  1 invoice  │            │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                                             │
│ AGING BREAKDOWN                                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │█████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│    │
│ │        Current 67%        │ 31-60 19% │61-90 10%│ 90+ 4%           │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────────────┤
│ INVOICES REQUIRING ATTENTION                                                │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ INV #    │ Customer      │ Amount   │ Due Date │ Age   │ Actions   │    │
│ ├─────────────────────────────────────────────────────────────────────┤    │
│ │ INV-089  │ Metro Signs   │ $1,950   │ Sep 15   │ 91 days│ [📧][📞] │    │
│ │ INV-102  │ ABC Corp      │ $2,400   │ Oct 20   │ 56 days│ [📧][📞] │    │
│ │ INV-108  │ Smith LLC     │ $1,700   │ Oct 28   │ 48 days│ [📧][📞] │    │
│ │ INV-115  │ Johnson       │ $3,200   │ Nov 10   │ 35 days│ [📧][📞] │    │
│ │ ...      │ ...           │ ...      │ ...      │ ...    │ ...       │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│ [📧] = Send Reminder    [📞] = Log Call    [✅] = Mark Paid                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Customer Balance Report

**Purpose:** View outstanding balances by customer

**Data Sources:**
- `Invoice`
- `Customer`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Minimum Balance | number | $100 |
| Sort By | dropdown | Balance (desc) |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Balance per Customer | SUM(Invoice.total - Invoice.amount_paid) GROUP BY customer |
| Invoice Count | COUNT(unpaid invoices) per customer |
| Oldest Invoice Age | MAX(days since created) per customer |
| Payment History | % of invoices paid on time (historical) |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ CUSTOMER BALANCES                        [Min $100 ▼] [Sort ▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Customer        │ Balance  │ Invoices │ Oldest  │ History │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ ABC Corporation │ $8,400   │    3     │ 45 days │ ⚠️ 67%  │  │
│ │ Smith LLC       │ $4,200   │    2     │ 32 days │ ✅ 92%  │  │
│ │ Metro Signs Co  │ $3,950   │    1     │ 91 days │ 🔴 45%  │  │
│ │ Johnson & Sons  │ $2,800   │    2     │ 28 days │ ✅ 88%  │  │
│ │ Downtown Retail │ $1,650   │    1     │ 15 days │ ✅ 95%  │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ History Legend: ✅ >80% on-time │ ⚠️ 50-80% │ 🔴 <50%          │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Collection Forecast Report

**Purpose:** Project expected cash collections

**Data Sources:**
- `Invoice` (unpaid)
- Historical payment patterns

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Expected This Week | SUM(amounts) WHERE likely to pay (based on history) |
| Expected This Month | Projected collections |
| At Risk | Invoices with low collection probability |
| Write-off Candidates | Invoices > 120 days with poor payment history |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ COLLECTION FORECAST                              [Next 30 Days] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ EXPECTED COLLECTIONS                                            │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │                                                             ││
│ │ Week 1 (Dec 16-22)                                          ││
│ │ ████████████████████████░░░░░░░░░░  $12,400 expected       ││
│ │ High confidence: $10,200 │ Medium: $2,200                   ││
│ │                                                             ││
│ │ Week 2 (Dec 23-29)                                          ││
│ │ ██████████████████░░░░░░░░░░░░░░░░  $8,600 expected        ││
│ │ High confidence: $6,100 │ Medium: $2,500                    ││
│ │                                                             ││
│ │ Week 3 (Dec 30 - Jan 5)                                     ││
│ │ ████████████░░░░░░░░░░░░░░░░░░░░░░  $6,200 expected        ││
│ │ High confidence: $4,800 │ Medium: $1,400                    ││
│ │                                                             ││
│ │ Week 4 (Jan 6-12)                                           ││
│ │ ██████████░░░░░░░░░░░░░░░░░░░░░░░░  $5,100 expected        ││
│ │                                                             ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ AT RISK: $4,950 (3 invoices with <30% collection probability)  │
│ [View At-Risk Invoices →]                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. PAYROLL SUMMARIES

### 4.1 Payroll Dashboard

**Purpose:** Overview of labor costs and employee balances

**Data Sources:**
- `Employee`
- `PayrollTransaction`
- `TimeLog`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current pay period |
| Employee | dropdown | All |
| Active Only | toggle | yes |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Total Earnings | SUM(PayrollTransaction.amount) WHERE type = earnings |
| Total Advances | SUM(PayrollTransaction.amount) WHERE type = advance |
| Total Paid | SUM(PayrollTransaction.amount) WHERE type = payment |
| Outstanding Balance | Total Earnings - Total Advances - Total Paid |
| Total Hours | SUM(net_hours) from TimeLog calculations |
| Average Hourly Cost | Total Earnings / Total Hours |
| Labor Cost % | Total Earnings / Revenue × 100 |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PAYROLL DASHBOARD                               [Dec 1-15, 2024 ▼]         │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ 💵 EARNINGS │ │ 🏦 ADVANCES │ │ ✅ PAID OUT │ │ ⚖️ BALANCE  │            │
│ │  $12,450    │ │   $1,200    │ │   $8,400    │ │   $2,850    │            │
│ │ (320 hrs)   │ │ (2 employees│ │             │ │   (owed)    │            │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────────────────────┤
│ EMPLOYEE SUMMARY                                                            │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ Employee      │ Hours  │ Rate  │ Earnings │ Advances │ Paid  │Balance│    │
│ ├─────────────────────────────────────────────────────────────────────┤    │
│ │ John Smith    │  82.5  │ $22   │  $1,815  │   $200   │ $1,400│  $215 │    │
│ │ Maria Garcia  │  78.0  │ $25   │  $1,950  │    $0    │ $1,500│  $450 │    │
│ │ Mike Johnson  │  85.0  │ $20   │  $1,700  │   $500   │ $1,000│  $200 │    │
│ │ Sarah Wilson  │  74.5  │ $24   │  $1,788  │   $500   │ $1,000│  $288 │    │
│ │ ...           │  ...   │ ...   │   ...    │   ...    │  ...  │  ...  │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│ LABOR COST TREND                                                            │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │ $15k│                    ╭──╮                                       │    │
│ │     │              ╭──╮  │  │  ╭──╮                                 │    │
│ │ $10k│         ╭──╮ │  │──╯  │──╯  │                                 │    │
│ │     │    ╭──╮ │  │ │  │     │     │                                 │    │
│ │  $5k│────╯  │─╯  │─╯  │     │     │                                 │    │
│ │     └────────────────────────────────                               │    │
│ │      PP1   PP2   PP3   PP4   PP5   PP6                              │    │
│ │                                                                     │    │
│ │ ── Earnings    ╌╌ Revenue (÷10)    Labor Cost: 28%                  │    │
│ └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Time & Attendance Report

**Purpose:** Detailed view of employee hours and attendance

**Data Sources:**
- `TimeLog`
- `Employee`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current week |
| Employee | dropdown | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Total Hours | SUM(net_hours) per employee |
| Regular Hours | Hours up to 40/week |
| Overtime Hours | Hours over 40/week |
| Break Time | SUM(break_minutes) / 60 |
| Attendance % | Days worked / Expected days |
| Average Start Time | AVG(first start_work timestamp) |
| Average End Time | AVG(last end_work timestamp) |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ TIME & ATTENDANCE                        [Dec 9-15, 2024 ▼]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ WEEKLY HOURS BY EMPLOYEE                                        │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Employee      │ Mon │ Tue │ Wed │ Thu │ Fri │ Total │ OT  │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ John Smith    │ 8.5 │ 9.0 │ 8.0 │ 8.5 │ 8.5 │ 42.5  │ 2.5 │  │
│ │ Maria Garcia  │ 8.0 │ 8.0 │ 8.0 │ 8.0 │ 8.0 │ 40.0  │ 0.0 │  │
│ │ Mike Johnson  │ 9.0 │ 9.5 │ 9.0 │ 9.0 │ 8.5 │ 45.0  │ 5.0 │  │
│ │ Sarah Wilson  │ 7.5 │ 8.0 │ 8.0 │ 7.5 │ 8.0 │ 39.0  │ 0.0 │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ DAILY DETAIL: John Smith                                        │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Date    │ Clock In │ Clock Out │ Breaks │ Net Hrs │       │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Dec 15  │  7:55 AM │  4:32 PM  │  35min │   8.5   │       │  │
│ │ Dec 14  │  7:48 AM │  5:18 PM  │  30min │   9.0   │       │  │
│ │ Dec 13  │  8:02 AM │  4:15 PM  │  45min │   8.0   │       │  │
│ │ ...     │   ...    │   ...     │  ...   │   ...   │       │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ ATTENDANCE OVERVIEW                                             │
│ ┌─────────────────────────────────────────────────┐            │
│ │ ✅ On Time: 18  │ ⚠️ Late: 2  │ ❌ Absent: 0  │            │
│ │      90%        │     10%     │      0%       │            │
│ └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.3 Payroll Period Report

**Purpose:** Generate payroll for a specific period

**Data Sources:**
- `Employee`
- `TimeLog`
- `PayrollTransaction`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Pay Period | dropdown | Current period |
| Include Inactive | toggle | no |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Gross Pay | Hours × Hourly Rate (+ OT at 1.5×) |
| Advances to Deduct | Advances not yet deducted |
| Net Pay | Gross Pay - Advances |
| Running Balance | Prior balance + Gross - Advances - Payments |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ PAYROLL PERIOD REPORT                    [Dec 1-15, 2024 ▼]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Employee      │ Reg Hrs│OT Hrs│ Gross  │Advance│ Net Pay │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ John Smith    │  40.0  │  2.5 │ $946.00│ $200  │ $746.00 │  │
│ │   $22/hr      │ $880   │ $66  │        │       │         │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Maria Garcia  │  40.0  │  0.0 │$1,000.00│  $0  │$1,000.00│  │
│ │   $25/hr      │$1,000  │  $0  │        │       │         │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Mike Johnson  │  40.0  │  5.0 │ $950.00│ $500  │ $450.00 │  │
│ │   $20/hr      │ $800   │$150  │        │       │         │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ TOTALS        │ 120.0  │  7.5 │$2,896.00│$700  │$2,196.00│  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ [Generate Earnings Transactions]  [Mark as Processed]           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. PRODUCTIVITY METRICS

### 5.1 Productivity Dashboard

**Purpose:** Track team efficiency and workload

**Data Sources:**
- `Order`
- `JobTicket`
- `Task`
- `Employee`
- `TimeLog`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current month |
| Employee | dropdown | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Orders Completed | COUNT(Orders) WHERE completed_at IN range |
| Revenue per Hour | Revenue / Total Hours |
| Average Order Duration | AVG(days from created to complete) |
| Items Produced | COUNT(JobTickets) completed |
| Tasks Completed | COUNT(Tasks) WHERE is_complete = true |
| Utilization Rate | Billable hours / Total hours |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PRODUCTIVITY DASHBOARD                           [December 2024 ▼]         │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ ORDERS DONE   │ │ REV/HOUR    │ │ AVG CYCLE   │ │ UTILIZATION │            │
│ │     32      │ │   $142      │ │  8.5 days   │ │    78%      │            │
│ │   ▲ 8%      │ │   ▲ 5%      │ │   ▼ 2 days  │ │   ▲ 3%      │            │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────────────────────┤
│ PRODUCTIVITY BY EMPLOYEE                                                    │
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │ Employee      │ Orders │ Revenue │ Hours │ Rev/Hr │ Util% │ Avg Cycle │  │
│ ├───────────────────────────────────────────────────────────────────────┤  │
│ │ John Smith    │  10  │ $14,200 │  82   │  $173  │  85%  │  7.2 days │  │
│ │ Maria Garcia  │   8  │ $12,800 │  78   │  $164  │  82%  │  9.1 days │  │
│ │ Mike Johnson  │   9  │ $11,500 │  85   │  $135  │  78%  │  8.8 days │  │
│ │ Sarah Wilson  │   5  │  $6,900 │  74   │   $93  │  65%  │ 10.5 days │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│ WEEKLY TREND                                                                │
│ ┌───────────────────────────────────────────────────────────────────────┐  │
│ │                                                                       │  │
│ │ Orders│    8   7   9   8                                                │  │
│ │     │   ╭─╮ ╭─╮ ╭─╮ ╭─╮                                               │  │
│ │     │   │ │ │ │ │ │ │ │                                               │  │
│ │     └───┴─┴─┴─┴─┴─┴─┴─┴──                                             │  │
│ │         W1  W2  W3  W4                                                │  │
│ │                                                                       │  │
│ └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 5.2 Order Type Analysis

**Purpose:** Understand profitability by job/item type

**Data Sources:**
- `JobTicket`
- `Order`
- `TimeLog` (if tracked per order)

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Last 90 days |
| Minimum Orders | number | 3 |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Revenue by Type | SUM(JobTicket.line_total) GROUP BY item_type |
| Order Count by Type | COUNT(DISTINCT order_id) GROUP BY item_type |
| Average Order Value | Revenue / Order Count per type |
| Average Item Value | AVG(JobTicket.line_total) per type |
| Growth Trend | Compare to previous period |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ ORDER TYPE ANALYSIS                            [Last 90 Days ▼]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ REVENUE BY JOB TYPE                                             │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │                                                             ││
│ │      Vehicle Wraps    ████████████████████  $42,500 (35%)  ││
│ │     Channel Letters    ███████████████      $33,600 (28%)  ││
│ │           Banners    ██████████            $21,600 (18%)  ││
│ │    Window Graphics    ███████              $14,400 (12%)  ││
│ │       Yard Signs    ████                  $8,400  (7%)   ││
│ │                                                             ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ TYPE BREAKDOWN                                                  │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Type            │ Orders │ Revenue │ Avg Order │ Avg Item│Trend│  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Vehicle Wraps   │  12  │ $42,500 │ $3,542  │ $1,180  │ ▲8% │  │
│ │ Channel Letters │  15  │ $33,600 │ $2,240  │ $840    │ ▲12%│  │
│ │ Banners         │  28  │ $21,600 │  $771   │ $385    │ ▼3% │  │
│ │ Window Graphics │  10  │ $14,400 │ $1,440  │ $720    │ ▲5% │  │
│ │ Yard Signs      │  35  │  $8,400 │  $240   │ $120    │ ▲2% │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│ INSIGHTS:                                                       │
│ • Highest margin: Vehicle Wraps ($3,542 avg)                   │
│ • Growth leader: Channel Letters (+12%)                        │
│ • Volume leader: Yard Signs (35 orders)                          │
│ • Declining: Banners (-3% - consider promotion)                │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Task Completion Report

**Purpose:** Track task management and completion rates

**Data Sources:**
- `Task`
- `Order`

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Current week |
| Status | multi-select | All |
| Order | dropdown | All |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Tasks Created | COUNT(Tasks) created in range |
| Tasks Completed | COUNT(Tasks) WHERE is_complete = true |
| Completion Rate | Completed / Created × 100 |
| Overdue Tasks | COUNT(Tasks) WHERE due_date < TODAY AND is_complete = false |
| Average Time to Complete | AVG(completed_at - created_at) |
| Tasks per Order | AVG(COUNT Tasks) per Order |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ TASK COMPLETION REPORT                    [This Week ▼]         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│ │ CREATED     │ │ COMPLETED   │ │ COMPLETION  │ │ OVERDUE     ││
│ │     24      │ │     18      │ │    75%      │ │     3       ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                 │
│ COMPLETION BY DAY                                               │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │        Created  ████                                        ││
│ │       Completed ░░░░                                        ││
│ │                                                             ││
│ │ Mon │ ████  │░░░░│                                          ││
│ │ Tue │ ██████│░░░░░░│                                        ││
│ │ Wed │ ████  │░░░│                                           ││
│ │ Thu │ ████████│░░░░░░░░│                                    ││
│ │ Fri │ ████  │░░░░│                                          ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ OVERDUE TASKS                                                   │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │ Task                    │ Order           │ Due    │ Days  │  │
│ ├───────────────────────────────────────────────────────────┤  │
│ │ Order vinyl material    │ Smith Wrap    │ Dec 12 │   3   │  │
│ │ Schedule install        │ ABC Signage   │ Dec 13 │   2   │  │
│ │ Send proof for approval │ Metro Letters │ Dec 14 │   1   │  │
│ └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## IMPLEMENTATION PRIORITY

### Phase 1: Essential (Build First)
1. **Order Pipeline Kanban** - Core operational visibility
2. **Outstanding Invoices Dashboard** - Cash flow critical
3. **Payroll Period Report** - Required for operations

### Phase 2: Important (Build Second)
4. **Revenue Dashboard** - Business health monitoring
5. **Time & Attendance Report** - Labor management
6. **Orders by Due Date** - Deadline management

### Phase 3: Valuable (Build Third)
7. **Daily Sales Report** - Cash tracking
8. **Productivity Dashboard** - Efficiency insights
9. **Customer Balance Report** - AR management

### Phase 4: Nice to Have
10. **Pipeline Funnel Report** - Conversion analysis
11. **Order Type Analysis** - Product mix insights
12. **Collection Forecast** - Predictive AR
13. **Revenue by Customer** - Customer analysis
14. **Task Completion Report** - Workflow metrics

---

## DATA AGGREGATION NOTES

### For Bubble Implementation

1. **Use Backend Workflows** for heavy calculations
   - Scheduled daily aggregation for dashboards
   - Store pre-calculated metrics in dedicated type

2. **Create Aggregation Data Types:**
   ```
   DailyMetrics:
     - date
     - total_revenue
     - total_orders_completed
     - total_hours_worked
     - total_outstanding
   
   EmployeePeriodMetrics:
     - employee
     - period_start
     - period_end
     - total_hours
     - total_earnings
   ```

3. **Performance Tips:**
   - Avoid nested searches in repeating groups
   - Pre-calculate totals where possible
   - Use "Do a search for" with constraints, not filters
   - Limit chart data points (daily for 30 days, weekly for 90+)

4. **Chart Plugins:**
   - Chart.js Plugin (recommended)
   - Google Charts
   - ApexCharts

5. **Export Options:**
   - PDF generation for reports
   - CSV export for data tables
   - Scheduled email delivery

---

## AI-POWERED REPORTS

These reports leverage AI to provide deeper insights, predictions, and actionable recommendations specific to sign shop operations.

---

### 1. AI PRODUCTION EFFICIENCY REPORT

**Purpose:** Analyze production times vs estimates to identify bottlenecks and improvement opportunities.

**AI Analysis Includes:**
- Comparison of estimated vs actual production time per order/ticket
- Identification of consistently over/under-estimated job types
- Bottleneck detection (which stages cause delays)
- Employee efficiency patterns
- Recommendations for estimate adjustments

**Data Sources:**
- `Order` (estimates, due dates)
- `JobTicket` (category, specs, timestamps)
- `ProductionTask` (stage times, status changes)
- `TimeEntry` (labor hours per task)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI PRODUCTION EFFICIENCY INSIGHTS                           │
├─────────────────────────────────────────────────────────────────┤
│ ⚠️  Vehicle Wraps averaging 2.3x estimated time               │
│     → Recommendation: Increase wrap estimates by 40%           │
│                                                                 │
│ 🔴 Bottleneck Detected: "Lamination" stage                     │
│     → 67% of delays occur here. Consider equipment upgrade.    │
│                                                                 │
│ ✅ Banner production running 15% ahead of estimates            │
│     → Top performer: Employee "Mike S." (23% faster avg)       │
│                                                                 │
│ 📊 This Month vs Last Month:                                   │
│     Production efficiency: +8% improvement                      │
│     Average delay: 1.2 days → 0.8 days                         │
└─────────────────────────────────────────────────────────────────┘
```

**Metrics Generated:**
| Metric | Calculation | AI Enhancement |
|--------|-------------|----------------|
| Efficiency Ratio | Actual Time / Estimated Time | Pattern recognition across job types |
| Bottleneck Score | Delay time per stage | Root cause analysis |
| Employee Efficiency | Tasks completed vs time | Performance recommendations |
| Estimate Accuracy | % within 10% of actual | Auto-suggest estimate adjustments |

---

### 2. AI CUSTOMER PROFITABILITY ANALYSIS

**Purpose:** Identify which customers are most/least profitable after accounting for all costs.

**AI Analysis Includes:**
- True profit margin per customer (revenue - materials - labor - overhead)
- Customer lifetime value prediction
- Payment behavior patterns (early, on-time, late)
- Maintenance level (high-touch vs low-touch customers)
- Cross-sell/upsell opportunity identification

**Data Sources:**
- `Customer` (all orders, invoices, communications)
- `Order` (totals, costs, timelines)
- `Invoice` (payment dates, amounts)
- `TimeEntry` (labor hours per customer's orders)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI CUSTOMER PROFITABILITY ANALYSIS                          │
├─────────────────────────────────────────────────────────────────┤
│ 💎 TOP 5 MOST PROFITABLE CUSTOMERS (Last 12 Months)            │
│    1. ABC Corp — $47,200 revenue, 42% margin, always on-time   │
│    2. City Events — $31,500 revenue, 38% margin, repeat buyer  │
│    3. Joe's Auto — $28,900 revenue, 45% margin, low maintenance│
│                                                                 │
│ ⚠️  HIGH REVENUE, LOW PROFIT CUSTOMERS                         │
│    • Downtown Restaurant Group — $52,000 revenue, 8% margin    │
│      → Issue: Excessive revisions (avg 4.2 per order)          │
│      → Recommendation: Implement revision fee policy           │
│                                                                 │
│ 📈 GROWTH OPPORTUNITIES                                        │
│    • "Quick Print Co" — Only uses banners, good candidate for  │
│      vehicle wrap services (similar profile to top wrap buyers)│
│                                                                 │
│ 💰 PAYMENT BEHAVIOR                                             │
│    • 78% of customers pay within terms                         │
│    • 3 customers consistently 30+ days late (flag for review)  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3. AI MATERIAL WASTE & USAGE REPORT

**Purpose:** Track material consumption, identify waste patterns, and optimize inventory.

**AI Analysis Includes:**
- Actual vs theoretical material usage per job type
- Waste percentage trends over time
- Correlation between waste and specific employees/equipment
- Optimal material ordering recommendations
- Cost-saving opportunities

**Data Sources:**
- `JobTicket` (dimensions, material specs)
- `MaterialUsage` (logged consumption)
- `Inventory` (stock levels, costs)
- `Order` (quantity, pricing)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI MATERIAL WASTE ANALYSIS                                  │
├─────────────────────────────────────────────────────────────────┤
│ 📊 WASTE SUMMARY (This Month)                                  │
│    Total Material Cost: $12,450                                │
│    Estimated Waste: $1,870 (15%)                               │
│    Industry Benchmark: 10-12%                                  │
│                                                                 │
│ 🔴 HIGH WASTE AREAS                                            │
│    • 3M IJ180 Vinyl — 22% waste rate                          │
│      → Pattern: Small cut vinyl jobs not being nested properly │
│      → Recommendation: Batch similar size jobs together        │
│                                                                 │
│    • Coroplast 4mm — 18% waste rate                           │
│      → Pattern: Standard sizes don't match common job sizes    │
│      → Recommendation: Stock 18x24 sheets instead of 24x36    │
│                                                                 │
│ ✅ LOW WASTE (Best Practices)                                  │
│    • Banner material — 6% waste (excellent)                    │
│    • Vehicle wrap film — 9% waste (good)                       │
│                                                                 │
│ 💰 POTENTIAL MONTHLY SAVINGS: $620                             │
│    If waste reduced to 12% benchmark                           │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4. AI SEASONAL DEMAND FORECAST

**Purpose:** Predict busy/slow periods based on historical data to optimize staffing and inventory.

**AI Analysis Includes:**
- Order volume predictions by week/month
- Category-specific seasonality (election signs, holiday banners, etc.)
- Revenue forecasting
- Staffing recommendations
- Inventory pre-stocking suggestions

**Data Sources:**
- `Order` (historical dates, categories, values)
- `JobTicket` (category trends)
- `Customer` (industry types for B2B patterns)
- External: Local event calendars, election cycles

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI SEASONAL DEMAND FORECAST                                 │
├─────────────────────────────────────────────────────────────────┤
│ 📅 NEXT 90-DAY FORECAST                                        │
│                                                                 │
│    April: ████████████████░░░░ 78% capacity predicted          │
│    May:   ████████████████████ 95% capacity predicted ⚠️       │
│    June:  █████████████░░░░░░░ 65% capacity predicted          │
│                                                                 │
│ 🔥 UPCOMING DEMAND SPIKES                                      │
│    • May 1-15: Graduation season (banners +180% vs avg)        │
│    • May 20-31: Memorial Day events (yard signs +120%)         │
│                                                                 │
│ 📦 INVENTORY RECOMMENDATIONS                                   │
│    Pre-stock by April 15:                                      │
│    • 13oz banner material: +500 sq ft                          │
│    • Coroplast 4mm: +200 sheets                                │
│    • Graduation templates: Prepare 5 new designs               │
│                                                                 │
│ 👥 STAFFING RECOMMENDATION                                     │
│    May: Consider 1 temp production worker                      │
│    Estimated additional labor cost: $2,400                     │
│    Estimated additional revenue enabled: $8,500                │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5. AI QUOTE WIN/LOSS ANALYSIS

**Purpose:** Understand why quotes convert or don't convert, and optimize pricing/follow-up strategy.

**AI Analysis Includes:**
- Win rate by category, customer type, quote value
- Time-to-decision patterns
- Price sensitivity analysis
- Competitor loss reasons
- Follow-up timing optimization

**Data Sources:**
- `Quote` (status, values, dates, notes)
- `Order` (converted quotes)
- `Customer` (history, type)
- `QuoteActivity` (follow-ups, communications)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI QUOTE WIN/LOSS ANALYSIS                                  │
├─────────────────────────────────────────────────────────────────┤
│ 📊 OVERALL WIN RATE: 34% (Industry avg: 25-35%)                │
│                                                                 │
│ ✅ HIGHEST WIN RATES                                           │
│    • Repeat customers: 67% win rate                            │
│    • Vehicle wraps: 52% win rate                               │
│    • Quotes under $500: 48% win rate                           │
│    • Same-day quote delivery: 45% win rate                     │
│                                                                 │
│ 🔴 LOWEST WIN RATES                                            │
│    • New customers, quotes over $2000: 18% win rate            │
│      → AI Suggestion: Offer payment plans for large orders     │
│                                                                 │
│    • Quotes taking 3+ days to send: 12% win rate               │
│      → AI Suggestion: Prioritize quote turnaround              │
│                                                                 │
│ 💡 PRICING INSIGHTS                                            │
│    • Sweet spot: Quotes 5-10% below competitor tend to win     │
│    • Over-discounting (>15%) doesn't improve win rate          │
│                                                                 │
│ ⏰ OPTIMAL FOLLOW-UP TIMING                                    │
│    • Day 2 follow-up: +15% conversion vs no follow-up          │
│    • Day 5 second follow-up: +8% additional conversion         │
│    • After Day 10: Minimal impact                              │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6. AI LABOR COST OPTIMIZATION REPORT

**Purpose:** Identify overtime patterns, scheduling inefficiencies, and labor cost reduction opportunities.

**AI Analysis Includes:**
- Overtime patterns and causes
- Underutilization periods
- Skill-matching efficiency (right person for right job)
- Schedule optimization suggestions
- Cost comparison: overtime vs new hire

**Data Sources:**
- `TimeEntry` (clock times, breaks, overtime)
- `Employee` (rates, skills, schedule)
- `ProductionTask` (assignments, completion times)
- `Order` (due dates, rush status)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI LABOR COST OPTIMIZATION                                  │
├─────────────────────────────────────────────────────────────────┤
│ 💰 LABOR COST BREAKDOWN (This Month)                           │
│    Regular hours: $18,400 (82%)                                │
│    Overtime: $4,050 (18%) ⚠️ Above 10% target                  │
│                                                                 │
│ 📈 OVERTIME PATTERNS                                           │
│    • Fridays: 65% of all overtime occurs                       │
│      → Cause: Rush orders accepted Thursday afternoon          │
│      → Suggestion: Rush fee increase for Thu-Fri deadlines     │
│                                                                 │
│    • Employee "Sarah M": 12 OT hours (highest)                 │
│      → Cause: Only trained lamination operator                 │
│      → Suggestion: Cross-train 1 additional employee           │
│                                                                 │
│ 📉 UNDERUTILIZATION DETECTED                                   │
│    • Tuesday mornings: Avg 60% productivity                    │
│    • Suggestion: Schedule equipment maintenance here           │
│                                                                 │
│ 💡 COST-SAVING OPPORTUNITIES                                   │
│    1. Cross-train for lamination: Save ~$800/month             │
│    2. Adjust rush pricing: Reduce Thu-Fri overtime 40%         │
│    3. Batch similar jobs: Reduce setup time 15%                │
│                                                                 │
│    TOTAL POTENTIAL MONTHLY SAVINGS: $1,650                     │
└─────────────────────────────────────────────────────────────────┘
```

---

### 7. AI REPEAT CUSTOMER & RETENTION REPORT

**Purpose:** Track customer loyalty, identify at-risk customers, and find reactivation opportunities.

**AI Analysis Includes:**
- Customer purchase frequency patterns
- Churn risk scoring
- Reactivation candidates (dormant customers likely to return)
- Loyalty program effectiveness
- Referral tracking

**Data Sources:**
- `Customer` (order history, last contact)
- `Order` (dates, values, categories)
- `Communication` (touchpoints, responses)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI CUSTOMER RETENTION ANALYSIS                              │
├─────────────────────────────────────────────────────────────────┤
│ 📊 RETENTION METRICS                                           │
│    Active customers (ordered in 12 months): 145                │
│    Repeat rate: 62% (customers with 2+ orders)                 │
│    Average orders per customer: 3.4                            │
│                                                                 │
│ ⚠️  AT-RISK CUSTOMERS (12)                                     │
│    Previously active, no order in 4-6 months:                  │
│    • ABC Events — Last order: 5 months ago                     │
│      → Previously ordered monthly, sudden stop                 │
│      → AI Suggestion: Personal outreach recommended            │
│                                                                 │
│ 💤 REACTIVATION OPPORTUNITIES (8)                              │
│    Dormant 6-12 months, high previous value:                   │
│    • Johnson Realty — $12,400 lifetime value                   │
│      → Similar customers reactivate with 15% discount offer    │
│                                                                 │
│ 🌟 LOYALTY PROGRAM IMPACT                                      │
│    • VIP customers (5+ orders): 89% retention rate             │
│    • Non-VIP: 54% retention rate                               │
│    • Suggestion: Lower VIP threshold to 3 orders               │
│                                                                 │
│ 📧 RECOMMENDED OUTREACH                                        │
│    • 12 at-risk: Personal call/email                          │
│    • 8 dormant: "We miss you" campaign with offer              │
│    • 23 seasonal: Pre-season reminder (based on past orders)   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8. AI PRODUCT MIX & MARGIN ANALYSIS

**Purpose:** Understand which product categories are most profitable and identify optimization opportunities.

**AI Analysis Includes:**
- Revenue and margin by category
- Trending products (growing vs declining)
- Cross-sell patterns (what customers buy together)
- Pricing optimization suggestions
- Category profitability ranking

**Data Sources:**
- `JobTicket` (category, specs, pricing)
- `Order` (totals, costs)
- `PricingSettings` (costs, markups)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI PRODUCT MIX ANALYSIS                                     │
├─────────────────────────────────────────────────────────────────┤
│ 📊 CATEGORY PERFORMANCE (Last 12 Months)                       │
│                                                                 │
│ Category        │ Revenue  │ Margin │ Trend  │ Recommendation  │
│─────────────────┼──────────┼────────┼────────┼─────────────────│
│ Vehicle Wraps   │ $89,400  │ 45%    │ ↑ +22% │ ✅ Invest more  │
│ Banners         │ $67,200  │ 35%    │ → 0%   │ Maintain        │
│ Yard Signs      │ $34,500  │ 28%    │ ↓ -8%  │ ⚠️ Review pricing│
│ Cut Vinyl       │ $28,100  │ 52%    │ ↑ +15% │ ✅ Promote more │
│ Rigid Signs     │ $45,300  │ 38%    │ → +3%  │ Maintain        │
│                                                                 │
│ 💡 CROSS-SELL PATTERNS                                         │
│    • Vehicle wrap buyers also buy cut vinyl (67% rate)         │
│    • Banner buyers rarely buy other products (12% rate)        │
│      → Opportunity: Bundle banner + yard sign packages         │
│                                                                 │
│ 🎯 PRICING RECOMMENDATIONS                                     │
│    • Yard signs: Cost increased 15%, price only 5%             │
│      → Suggest price increase of $0.50/sign                    │
│                                                                 │
│    • Cut vinyl: High margin, underpriced vs market             │
│      → Could increase 10% without affecting volume             │
│                                                                 │
│ 📈 GROWTH OPPORTUNITY                                          │
│    Vehicle wraps showing strongest growth.                     │
│    Consider: Dedicated wrap bay, wrap-specific marketing       │
└─────────────────────────────────────────────────────────────────┘
```

---

### 9. AI COMPETITIVE PRICING INTELLIGENCE

**Purpose:** Compare your pricing to market rates and identify adjustment opportunities.

**AI Analysis Includes:**
- Price positioning vs market (from historical invoice imports)
- Win rate correlation with pricing
- Margin optimization suggestions
- Rush pricing effectiveness
- Quantity discount analysis

**Data Sources:**
- `PricingSettings` (your rates)
- `HistoricalImport` (analyzed invoices, benchmarks)
- `Quote` (win/loss with pricing)
- `Order` (final pricing, discounts applied)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI PRICING INTELLIGENCE                                     │
├─────────────────────────────────────────────────────────────────┤
│ 📊 YOUR PRICING VS MARKET                                      │
│                                                                 │
│ Category        │ Your Avg │ Market Avg │ Position │ Action    │
│─────────────────┼──────────┼────────────┼──────────┼───────────│
│ Banners/sq ft   │ $4.25    │ $4.50      │ -6%      │ ↑ Can raise│
│ Vehicle Wraps   │ $2,800   │ $2,650     │ +6%      │ OK (premium)│
│ Yard Signs      │ $8.50    │ $9.00      │ -6%      │ ↑ Can raise│
│ Cut Vinyl/sq ft │ $12.00   │ $14.00     │ -14%     │ ↑ Underpriced│
│                                                                 │
│ 💰 POTENTIAL REVENUE INCREASE                                  │
│    If prices adjusted to market average:                       │
│    • Monthly revenue increase: ~$2,800                         │
│    • Annual increase: ~$33,600                                 │
│    • Without significant volume impact (based on win rates)    │
│                                                                 │
│ ⏰ RUSH PRICING ANALYSIS                                       │
│    Current rush fee: 25%                                       │
│    Acceptance rate: 78%                                        │
│    AI Suggestion: Test 35% rush fee — competitors at 30-40%    │
│                                                                 │
│ 📦 QUANTITY DISCOUNT EFFECTIVENESS                             │
│    Current: 10% at 25+ units                                   │
│    Analysis: 85% of quantity orders are 25-35 units            │
│    Suggestion: Tier at 50+ for better margin preservation      │
└─────────────────────────────────────────────────────────────────┘
```

---

### 10. AI CASH FLOW FORECAST

**Purpose:** Predict cash flow based on outstanding invoices, expected orders, and recurring expenses.

**AI Analysis Includes:**
- Expected collections (based on customer payment patterns)
- Upcoming expenses prediction
- Cash position forecast (30/60/90 days)
- Warning alerts for potential shortfalls
- Recommendations for cash management

**Data Sources:**
- `Invoice` (outstanding, payment history)
- `Order` (pipeline, expected completion)
- `Expense` (recurring, one-time)
- `Customer` (payment behavior patterns)
- `Sale` (historical revenue patterns)

**Sample AI Insights:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI CASH FLOW FORECAST                                       │
├─────────────────────────────────────────────────────────────────┤
│ 💵 CURRENT POSITION                                            │
│    Cash on hand: $24,500                                       │
│    Outstanding receivables: $18,200                            │
│    Outstanding payables: $8,400                                │
│                                                                 │
│ 📅 30-DAY FORECAST                                             │
│                                                                 │
│    Expected Collections:                                       │
│    • Week 1: $6,200 (85% confidence)                          │
│    • Week 2: $4,800 (75% confidence)                          │
│    • Week 3: $3,100 (70% confidence)                          │
│    • Week 4: $2,400 (65% confidence)                          │
│    Total: $16,500                                              │
│                                                                 │
│    Expected Expenses:                                          │
│    • Payroll (2x): $9,200                                     │
│    • Materials: $4,500                                         │
│    • Rent/Utilities: $3,200                                    │
│    • Other: $1,800                                             │
│    Total: $18,700                                              │
│                                                                 │
│    Projected End Balance: $22,300                              │
│                                                                 │
│ ⚠️  ALERTS                                                     │
│    • Invoice #1842 (ABC Corp, $4,200) — Usually pays Day 15   │
│      but no payment yet (Day 22). Follow up recommended.       │
│                                                                 │
│    • Large material order due Week 3 ($3,200)                  │
│      Consider: Delay to Week 4 or negotiate terms              │
│                                                                 │
│ 💡 RECOMMENDATIONS                                             │
│    1. Send payment reminders to 3 overdue accounts ($7,400)    │
│    2. Offer 2% early payment discount to accelerate $5,200     │
│    3. Consider: Line of credit for seasonal cash gaps          │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI REPORT IMPLEMENTATION NOTES

### How AI Reports Work

1. **Data Collection:** Reports pull from existing database tables
2. **Pattern Analysis:** AI analyzes historical data for trends and anomalies
3. **Benchmark Comparison:** Compares against industry standards and your historical averages
4. **Insight Generation:** Generates specific, actionable recommendations
5. **Confidence Scoring:** Each prediction includes confidence level

### AI Credit Usage

| Report Type | Credits | Frequency Recommendation |
|-------------|---------|--------------------------|
| Production Efficiency | 2 | Weekly |
| Customer Profitability | 3 | Monthly |
| Material Waste | 2 | Weekly |
| Seasonal Forecast | 3 | Monthly |
| Quote Win/Loss | 2 | Weekly |
| Labor Optimization | 2 | Weekly |
| Customer Retention | 2 | Monthly |
| Product Mix | 2 | Monthly |
| Pricing Intelligence | 3 | Monthly |
| Cash Flow Forecast | 2 | Weekly |

### Integration Points

- **Dashboard Widgets:** Summary cards for each AI report
- **Email Alerts:** Automatic alerts for critical insights
- **PDF Export:** Full report generation for stakeholder review
- **Action Items:** Convert AI suggestions to tasks automatically

