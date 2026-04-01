# Business Assistant Detailed Requirements

Last updated: April 1, 2026

This file stores the detailed instruction set for the Business Assistant enhancement roadmap.

Hard rule:

**Do not add another phase until the previous one is perfectly working.**

---

# MASTER REQUIREMENTS

Enhance the existing Business Assistant to function as a primary control layer for the application.

## Core Objective

1. Increase usability and daily usage
2. Reduce need for manual navigation
3. Provide guided actions after every response
4. Feel like a control center, not a chatbot

---

## FEATURE 1 — QUICK ACTION BUTTONS (MANDATORY)

After every meaningful response, display context-aware action buttons.

### Example — Unpaid Invoices
User: “Who owes me money?”
Assistant: “You have 8 unpaid invoices totaling $4,320.”
Buttons:
- View Invoices
- Send Reminders
- Export Report
- Mark as Paid

### Example — Job Creation
User: “Create a banner job for John, $120”
Assistant: “Job created successfully.”
Buttons:
- View Job
- Add Another Job
- Schedule This Job
- Create Invoice

### Example — Schedule Request
User: “What’s scheduled tomorrow?”
Assistant: “You have 6 jobs scheduled tomorrow.”
Buttons:
- Open Schedule
- Reassign Jobs
- Add New Job

### Rules
- Buttons must be dynamically generated based on intent
- Buttons must trigger real actions or navigation
- Buttons appear immediately under responses

---

## FEATURE 2 — CONTEXT AWARENESS

Assistant must be aware of current page context.

Track:
- current_page
- current_customer_id
- current_job_id

Behavior:
- Auto-fill customer/job when relevant
- Apply actions to active record when applicable

---

## FEATURE 3 — SUGGESTED COMMANDS

When idle, display suggestions:
- Create a new job
- Show unpaid invoices
- What’s due today?
- How much did we make this week?

Update suggestions based on usage history.

---

## FEATURE 4 — COMMAND HISTORY + REPEAT

Store recent commands.

UI:
- Show recent commands list
- Buttons:
  - Run Again
  - Edit Command

---

## FEATURE 5 — MULTI-STEP ACTION HANDLING

Assistant must handle incomplete commands with guided prompts.

Example flow:
User: “Create a job”
Assistant: “What type?”
User: “Banner”
Assistant: “What size?”

Do not fail or assume missing data.

---

## FEATURE 6 — CONFIRMATION FOR CRITICAL ACTIONS

Require confirmation for:
- Deleting
- Overwriting
- Financial updates

Example:
User: “Delete job 123”
Assistant: “Are you sure?”
Buttons:
- Confirm
- Cancel

---

## FEATURE 7 — SMART NAVIGATION LINKS

Include clickable navigation links in responses.

Example:
“You have 5 overdue invoices.”
Link:
- View Overdue Invoices

---

## FEATURE 8 — RESULT SUMMARIES

Always provide insight, not just raw data.

Example:
“You made $5,200 this week, which is 18% higher than last week.”

---

## FEATURE 9 — VOICE FEEDBACK LOOP

For voice input:
1. Show transcript
2. Confirm interpretation
3. Execute
4. Provide feedback

---

## FEATURE 10 — ERROR HANDLING / CLARIFICATION

If input is unclear, ask follow-up questions.

Example:
User: “Add time”
Assistant: “For which employee?”

---

## FEATURE 11 — CROSS-SYSTEM ACTIONS

Allow multi-step commands across modules.

Example:
“Create a job, invoice it, and schedule install Friday”

System:
- Creates job
- Creates invoice
- Schedules job

Then display buttons:
- View Job
- View Invoice
- View Schedule

---

## FEATURE 12 — PROACTIVE INSIGHTS

Optionally display alerts automatically.

Example:
“You have 3 overdue invoices totaling $1,200.”
Buttons:
- Send Reminders
- View Invoices

---

# CRITICAL UX ENHANCEMENTS

## FEATURE 13 — ACTION PREVIEW BEFORE EXECUTION

Before executing write actions, show a preview panel.

Example:
Preview:
- Customer: Mike
- Item: 4x8 Banner
- Price: $150

Buttons:
- Confirm
- Edit
- Cancel

Rule:
- Required for all CREATE, UPDATE, DELETE actions

---

## FEATURE 14 — INLINE EDITING

Allow editing directly inside preview.

Example:
Price: $150 ✏️ (editable field)

Rule:
- No need to restart command

---

## FEATURE 15 — NEXT-STEP ACTION CHAINING

After completing an action, suggest logical next steps.

Example:
After job creation:
- Create Invoice
- Schedule Job
- Add Artwork

Rule:
- Only show relevant next steps

---

## FEATURE 16 — HABIT-BASED SUGGESTIONS

Track user workflows and suggest patterns.

Example:
“Want me to invoice and schedule this too?”

---

## FEATURE 17 — SMART DEFAULTS

Auto-fill based on past behavior.

Examples:
- Common pricing
- Frequent customers
- Typical job types

---

## FEATURE 18 — MODES

Support different assistant modes:
- Quick Mode (minimal prompts)
- Guided Mode (step-by-step)
- Power Mode (instant execution)

---

## FEATURE 19 — BULK ACTIONS

Enable multi-record operations.

Example:
“Send reminders to all overdue invoices”

Buttons:
- Preview List
- Send All
- Cancel

---

## FEATURE 20 — VISUAL RESPONSE BLOCKS

Use structured UI instead of plain text.

Example:
- Revenue This Week: $5,200
- ↑ 18% from last week

Buttons:
- View Report
- Breakdown

---

## FEATURE 21 — “WHY” EXPLANATIONS

Explain insights.

Example:
“Revenue is up 18% driven by 3 large wrap jobs.”

---

## FEATURE 22 — INTERRUPT + CORRECT FLOW

If unclear, ask follow-up instead of failing.

---

## FEATURE 23 — GLOBAL SEARCH + ACTION HYBRID

Search results should include actions.

Example:
Customer: John Smith
- Open
- Create Job
- View Invoices

---

## FEATURE 24 — PIN RESPONSES / COMMANDS

Allow saving useful queries.

---

## FEATURE 25 — MICRO AUTOMATIONS

Allow saving command sequences.

Example:
“Close shop routine” runs multiple checks.

---

## FEATURE 26 — CONFIDENCE DISPLAY

If uncertain, confirm before acting.

Example:
“I think you mean John Smith. Confirm?”

---

## FEATURE 27 — CROSS-CHECK WARNINGS

Prevent conflicts.

Example:
“This job overlaps another install at 10am.”

---

## FEATURE 28 — TIME SAVED FEEDBACK

Show efficiency gains.

Example:
“Saved ~3 minutes vs manual entry.”

---

## FEATURE 29 — “HANDLE THE REST” PROMPT

After actions, offer to complete next steps.

Example:
“Want me to invoice and schedule this too?”

---

## Implementation Rules

- Do not remove existing functionality
- Enhance interaction layer only
- Assistant must be faster than manual navigation
- Every response must guide the next step

---

## Test Use Cases

### Sales
- Create a 4x8 banner job for Mike for $150
- Show quotes from this week

### Financials
- How much did we make this month?
- Who owes me money?

### Production
- What jobs are due tomorrow?
- Schedule install for Friday

### Team
- Who worked the most hours?
- Add 3 hours for John

### Reports
- Show revenue trends
- Compare this week to last week

### Documents
- Create a proposal for ABC Company
- Find wrap inspection form

---

# Phase-by-Phase Mapping

## Phase 0 — Stabilization & Core Usability

Build these first:
- Feature 9 — Voice Feedback Loop
- Feature 10 — Error Handling / Clarification
- Feature 22 — Interrupt + Correct Flow
- Feature 26 — Confidence Display

Additional stabilization requirements:
- plain-text response normalization
- reliable voice transcription
- order/job creation phrasing support
- stable current action execution

### Exit gate
Do not move on until:
- voice is reliable and quick
- no `object, object` / broken response rendering
- incomplete commands trigger good follow-up prompts
- current assistant actions work in real use

---

## Phase 1 — Action-Oriented Response Layer

Build after Phase 0 is perfect:
- Feature 1 — Quick Action Buttons
- Feature 7 — Smart Navigation Links
- Feature 8 — Result Summaries
- Feature 15 — Next-Step Action Chaining
- Feature 20 — Visual Response Blocks
- Feature 21 — Why Explanations
- Feature 29 — Handle the Rest Prompt

### Exit gate
Do not move on until:
- every meaningful reply can guide a next step
- buttons are context-aware and real
- result blocks are clear and useful

---

## Phase 2 — Context Awareness + Guided Action Flow

Build after Phase 1 is perfect:
- Feature 2 — Context Awareness
- Feature 5 — Multi-Step Action Handling
- Feature 13 — Action Preview Before Execution
- Feature 14 — Inline Editing
- Feature 17 — Smart Defaults
- Feature 27 — Cross-Check Warnings

### Exit gate
Do not move on until:
- previews work before all write actions
- inline editing is stable
- context autofill is trustworthy

---

## Phase 3 — Cross-System Execution

Build after Phase 2 is perfect:
- Feature 11 — Cross-System Actions
- Feature 6 — Confirmation for Critical Actions
- Feature 23 — Global Search + Action Hybrid

### Exit gate
Do not move on until:
- create + invoice + schedule style commands are dependable
- critical confirmations are consistent

---

## Phase 4 — Personalization & Daily Usage

Build after Phase 3 is perfect:
- Feature 3 — Suggested Commands
- Feature 4 — Command History + Repeat
- Feature 16 — Habit-Based Suggestions
- Feature 18 — Modes
- Feature 24 — Pin Commands
- Feature 28 — Time Saved Feedback

---

## Phase 5 — Bulk Workflows & Micro-Automations

Build after Phase 4 is perfect:
- Feature 19 — Bulk Actions
- Feature 25 — Micro Automations
- Feature 12 — Proactive Insights

---

## Current Build Target

**Current recommended next build:**
- Phase 0 — Stabilization & Core Usability

Do not start later phases until Phase 0 is fully working and verified.