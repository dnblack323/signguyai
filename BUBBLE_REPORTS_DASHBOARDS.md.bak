# Sign Guy AI - Reports & Dashboards Specification

## OVERVIEW

This document defines recommended reports and dashboards for Sign Guy AI. These extend beyond the current MVP implementation to provide comprehensive business intelligence.

**Report Categories:**
1. Job Pipeline Overview
2. Revenue Summaries
3. Outstanding Invoices
4. Payroll Summaries
5. Productivity Metrics

---

## 1. JOB PIPELINE OVERVIEW

### 1.1 Pipeline Kanban Dashboard

**Purpose:** Visual overview of all orders by status stage

**Data Sources:**
- `Job` (primary)
- `Customer` (for customer name)
- `JobItem` (for item count)

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
│ JOB PIPELINE OVERVIEW                          [Date Range] [Customer ▼]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ QUOTED   │  │ APPROVED │  │IN PROD   │  │INSTALLED │  │ COMPLETE │     │
│  │          │  │          │  │          │  │          │  │          │     │
│  │  12 orders │  │  8 orders  │  │  15 orders │  │  3 orders  │  │  45 orders │     │
│  │  $24,500 │  │  $18,200 │  │  $42,100 │  │  $8,400  │  │  $95,000 │     │
│  │          │  │          │  │          │  │          │  │          │     │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │     │
│  │ │ Job1 │ │  │ │ Job4 │ │  │ │ Job7 │ │  │ │Job12│ │  │ │Job15│ │     │
│  │ │$2,500│ │  │ │$3,100│ │  │ │$4,200│ │  │ │$2,800│ │  │ │$3,500│ │     │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │     │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │          │  │ ┌──────┐ │     │
│  │ │ Job2 │ │  │ │ Job5 │ │  │ │ Job8 │ │  │          │  │ │Job16│ │     │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │          │  │ └──────┘ │     │
│  │   ...    │  │   ...    │  │   ...    │  │          │  │   ...    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ PIPELINE SUMMARY                                                            │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ Active Orders │ │Pipeline Val │ │ Avg Job Val │ │ Avg Days to │            │
│ │     38      │ │  $93,200    │ │   $2,453    │ │  Complete   │            │
│ │             │ │             │ │             │ │    12 days  │            │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Pipeline Funnel Report

**Purpose:** Track conversion rates through pipeline stages

**Data Sources:**
- `Job`
- `JobActivity` (for stage transition timestamps)

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
- `Job`
- `Customer`
- `JobItem`

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
│ │ Job Name          │ Customer    │ Due Date │ Days Over│ $ │  │
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
- `Job` (pipeline value)
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
- `Job`

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
| Job Count per Customer | COUNT(Orders) GROUP BY customer |
| Average Job Value | Revenue / Job Count |
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
│ │ Customer         │ Revenue  │ Orders │ Avg Job │ % Total   │  │
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
- `Job`

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
- `Job`
- `JobItem`
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
| Average Job Duration | AVG(days from created to complete) |
| Items Produced | COUNT(JobItems) completed |
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

### 5.2 Job Type Analysis

**Purpose:** Understand profitability by job/item type

**Data Sources:**
- `JobItem`
- `Job`
- `TimeLog` (if tracked per job)

**Filters:**
| Filter | Type | Default |
|--------|------|---------|
| Date Range | date picker | Last 90 days |
| Minimum Orders | number | 3 |

**Key Metrics:**

| Metric | Calculation |
|--------|-------------|
| Revenue by Type | SUM(JobItem.line_total) GROUP BY item_type |
| Job Count by Type | COUNT(DISTINCT order_id) GROUP BY item_type |
| Average Job Value | Revenue / Job Count per type |
| Average Item Value | AVG(JobItem.line_total) per type |
| Growth Trend | Compare to previous period |

**Visual Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ JOB TYPE ANALYSIS                            [Last 90 Days ▼]   │
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
│ │ Type            │ Orders │ Revenue │ Avg Job │ Avg Item│Trend│  │
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
- `Job`

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
| Tasks per Job | AVG(COUNT Tasks) per Job |

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
│ │ Task                    │ Job           │ Due    │ Days  │  │
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
1. **Job Pipeline Kanban** - Core operational visibility
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
11. **Job Type Analysis** - Product mix insights
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
