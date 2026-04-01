# Business Assistant Enhancement Rollout Plan

Last updated: April 1, 2026

## Rollout Rule

**Hard rule:** Do **not** start the next phase until the current phase is fully working, tested, and approved.

That means:
- no overlapping feature rollout
- no partial next-phase work hidden behind current bugs
- every phase must pass real usage tests before the next one begins

---

## Current Progress Snapshot

### Already present in some form
- Floating assistant UI exists
- Text chat exists
- Voice input/output exists
- Structured action parsing exists for some actions
- Confirmation flow exists for some actions
- Quick action suggestions exist in basic form

### Current known weakness
- Voice experience is not yet reliable enough for primary use
- Assistant action flow is not yet polished enough to serve as a true control layer
- Post-response actions and guided next steps are still incomplete

### Current status
- **Phase 0 = NEXT REQUIRED WORK**
- Later phases are planned but should not be started yet

---

## Phase 0 — Stabilization & Core Usability

### Goal
Make the current assistant reliable enough to use daily before adding bigger control-center features.

### Priority
**Highest**

### Scope
1. Fix voice transcription reliability and speed
2. Fix bad response rendering issues like `object, object`
3. Make create/query assistant flows dependable for common commands
4. Improve error handling and clarification prompts
5. Make the current confirmation flow stable

### Features included from master list
- **Feature 9** — Voice Feedback Loop
- **Feature 10** — Error Handling / Clarification
- **Feature 22** — Interrupt + Correct Flow
- **Feature 26** — Confidence Display

### Also include foundational stabilization for
- parsing intent correctly
- clean success/failure responses
- stable execution of existing assistant actions

### Example success criteria
- “Create an order for Sara Manning” no longer fails with broken parsing or object output
- voice transcription is fast enough to feel usable
- assistant asks follow-up questions when missing data
- assistant confirmations are understandable and consistent
- no broken response objects shown in UI

### Status
- **Planned / not yet complete**

---

## Phase 1 — Action-Oriented Response Layer

### Goal
Make every meaningful answer drive the next action.

### Priority
**Very high**

### Features included
- **Feature 1** — Quick Action Buttons (mandatory)
- **Feature 7** — Smart Navigation Links
- **Feature 8** — Result Summaries
- **Feature 15** — Next-Step Action Chaining
- **Feature 20** — Visual Response Blocks
- **Feature 21** — “Why” Explanations
- **Feature 29** — “Handle the Rest” Prompt

### Outcome
Assistant starts feeling like a control center instead of a chatbot.

### Example success criteria
- unpaid invoices response includes real action buttons
- created job response includes next-step actions like invoice/schedule/artwork
- responses are structured visually, not just plain paragraphs

### Status
- **Blocked until Phase 0 is perfect**

---

## Phase 2 — Context Awareness + Multi-Step Guided Actions

### Goal
Reduce manual navigation and repeated data entry.

### Priority
**High**

### Features included
- **Feature 2** — Context Awareness
- **Feature 5** — Multi-Step Action Handling
- **Feature 13** — Action Preview Before Execution
- **Feature 14** — Inline Editing
- **Feature 17** — Smart Defaults
- **Feature 27** — Cross-Check Warnings

### Outcome
Assistant can safely guide users through missing info, previews, and edits before executing.

### Example success criteria
- assistant understands current page/customer/job context
- write actions show editable previews before commit
- user can correct fields inline without restarting command
- system warns about conflicts like schedule overlaps

### Status
- **Blocked until Phase 1 is perfect**

---

## Phase 3 — Cross-System Command Execution

### Goal
Let the assistant execute meaningful real workflows across modules.

### Priority
**High**

### Features included
- **Feature 11** — Cross-System Actions
- **Feature 6** — Confirmation for Critical Actions
- **Feature 23** — Global Search + Action Hybrid

### Outcome
Assistant can perform multi-step flows like create + invoice + schedule from one command.

### Example success criteria
- “Create a job, invoice it, and schedule install Friday” works with preview + confirmation
- search results show actions like open/create/view invoice
- destructive/financial changes always require confirmation

### Status
- **Blocked until Phase 2 is perfect**

---

## Phase 4 — Personalization & Daily Usage Layer

### Goal
Increase daily usage and make the assistant feel tailored to how the shop operates.

### Priority
**Medium**

### Features included
- **Feature 3** — Suggested Commands
- **Feature 4** — Command History + Repeat
- **Feature 16** — Habit-Based Suggestions
- **Feature 18** — Modes
- **Feature 24** — Pin Responses / Commands
- **Feature 28** — Time Saved Feedback

### Outcome
Assistant starts learning common patterns and becomes a faster command surface for repeat workflows.

### Example success criteria
- recent commands can be rerun or edited
- assistant suggests frequent actions based on habits
- Quick / Guided / Power modes are usable and clear

### Status
- **Blocked until Phase 3 is perfect**

---

## Phase 5 — Bulk Workflows & Micro-Automations

### Goal
Let the assistant perform grouped work and saved routines.

### Priority
**Medium**

### Features included
- **Feature 19** — Bulk Actions
- **Feature 25** — Micro Automations
- **Feature 12** — Proactive Insights

### Outcome
Assistant becomes useful for owner/operator batch work and repeated shop routines.

### Example success criteria
- bulk overdue invoice reminder flows work
- simple reusable routines can be saved and triggered
- assistant can surface proactive financial/production alerts safely

### Status
- **Blocked until Phase 4 is perfect**

---

## Recommended Release Order Summary

1. **Phase 0** — Stabilization & Core Usability
2. **Phase 1** — Action-Oriented Response Layer
3. **Phase 2** — Context Awareness + Guided Action Flows
4. **Phase 3** — Cross-System Execution
5. **Phase 4** — Personalization & Daily Usage Layer
6. **Phase 5** — Bulk Workflows & Micro-Automations

---

## What Not To Build Early

Until earlier phases are solid, do **not** rush into:
- pinned command systems
- micro-automations
- bulk actions
- proactive alerts everywhere
- too many modes

Those only make sense after the assistant is already stable, clear, and trustworthy.

---

## Immediate Next Build Recommendation

### Build next:
**Phase 0 — Stabilization & Core Usability**

### First concrete deliverables inside Phase 0
1. reliable voice transcription
2. plain-text assistant response normalization
3. better follow-up questioning when command data is incomplete
4. safer action preview/confirmation for the current action set
5. stable order/job creation phrasing support

### Phase 0 exit gate
Do not move to Phase 1 until these are true:
- voice flow is usable
- no broken response objects
- common create/query commands are dependable
- clarification prompts work consistently
- current assistant actions are stable in real use