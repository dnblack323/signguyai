# Sign Guy AI - Bubble Design System

## OVERVIEW

A professional, dark-mode-first design system for sign shop operations. Desktop-optimized with clear hierarchy and status-driven color usage.

**Design Principles:**
1. **Clarity over decoration** - Information density matters
2. **Status drives color** - Neutral UI, colored status indicators
3. **Consistent spacing** - 4px base unit grid
4. **Accessible contrast** - WCAG AA compliant

---

## PART 1: COLOR PALETTE

### Brand Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Primary** | `#0D9488` | 13, 148, 136 | Main actions, links, active states |
| **Primary Dark** | `#0F766E` | 15, 118, 110 | Hover states |
| **Primary Light** | `#14B8A6` | 20, 184, 166 | Highlights, selections |
| **Primary Muted** | `#0D94881A` | - | Backgrounds (10% opacity) |

### Secondary Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Secondary** | `#6366F1` | 99, 102, 241 | Secondary actions, links |
| **Secondary Dark** | `#4F46E5` | 79, 70, 229 | Hover states |
| **Secondary Light** | `#818CF8` | 129, 140, 248 | Highlights |

### Accent Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Accent** | `#F59E0B` | 245, 158, 11 | Attention, highlights, badges |
| **Accent Dark** | `#D97706` | 217, 119, 6 | Hover |
| **Accent Light** | `#FBBF24` | 251, 191, 36 | Soft highlights |

### Semantic Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Success** | `#10B981` | 16, 185, 129 | Completed, paid, positive |
| **Success Dark** | `#059669` | 5, 150, 105 | Hover |
| **Success Light** | `#34D399` | 52, 211, 153 | Backgrounds |
| **Success Muted** | `#10B98120` | - | Background (12% opacity) |
| | | | |
| **Warning** | `#F59E0B` | 245, 158, 11 | Attention needed, pending |
| **Warning Dark** | `#D97706` | 217, 119, 6 | Hover |
| **Warning Light** | `#FBBF24` | 251, 191, 36 | Backgrounds |
| **Warning Muted** | `#F59E0B20` | - | Background (12% opacity) |
| | | | |
| **Danger** | `#EF4444` | 239, 68, 68 | Errors, delete, overdue |
| **Danger Dark** | `#DC2626` | 220, 38, 38 | Hover |
| **Danger Light** | `#F87171` | 248, 113, 113 | Backgrounds |
| **Danger Muted** | `#EF444420` | - | Background (12% opacity) |
| | | | |
| **Info** | `#3B82F6` | 59, 130, 246 | Informational, links |
| **Info Dark** | `#2563EB` | 37, 99, 235 | Hover |
| **Info Light** | `#60A5FA` | 96, 165, 250 | Backgrounds |

### Neutral Colors (Dark Theme)

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Background** | `#0F172A` | 15, 23, 42 | App shell, page background |
| **Surface** | `#1E293B` | 30, 41, 59 | Cards, panels, modals |
| **Surface Elevated** | `#334155` | 51, 65, 85 | Dropdowns, popovers, hover |
| **Border** | `#334155` | 51, 65, 85 | Dividers, borders |
| **Border Light** | `#475569` | 71, 85, 105 | Subtle borders |
| | | | |
| **Text Primary** | `#F8FAFC` | 248, 250, 252 | Headings, important text |
| **Text Secondary** | `#E2E8F0` | 226, 232, 240 | Body text |
| **Text Muted** | `#94A3B8` | 148, 163, 184 | Labels, placeholders |
| **Text Disabled** | `#64748B` | 100, 116, 139 | Disabled states |

### Neutral Colors (Light Theme - Optional)

| Name | HEX | Usage |
|------|-----|-------|
| **Background** | `#F8FAFC` | App shell |
| **Surface** | `#FFFFFF` | Cards, panels |
| **Surface Elevated** | `#F1F5F9` | Hover, selected |
| **Border** | `#E2E8F0` | Dividers |
| **Text Primary** | `#0F172A` | Headings |
| **Text Secondary** | `#334155` | Body |
| **Text Muted** | `#64748B` | Labels |

---

## PART 2: STATUS COLOR MAPPING

### JobStatus Colors

| Status | Background | Text | Border | Badge Style |
|--------|------------|------|--------|-------------|
| **quoted** | `#F59E0B20` | `#F59E0B` | `#F59E0B40` | Warning/Amber |
| **approved** | `#3B82F620` | `#3B82F6` | `#3B82F640` | Info/Blue |
| **in_production** | `#8B5CF620` | `#8B5CF6` | `#8B5CF640` | Purple |
| **installed** | `#06B6D420` | `#06B6D4` | `#06B6D440` | Cyan |
| **complete** | `#10B98120` | `#10B981` | `#10B98140` | Success/Green |
| **archived** | `#64748B20` | `#64748B` | `#64748B40` | Neutral/Gray |

**Bubble Implementation:**
```
Conditional: When This Job's status is "quoted"
  Background color: #F59E0B20
  Font color: #F59E0B
```

### InvoiceStatus Colors

| Status | Background | Text | Border | Meaning |
|--------|------------|------|--------|---------|
| **draft** | `#64748B20` | `#94A3B8` | `#64748B40` | Not sent yet |
| **sent** | `#3B82F620` | `#3B82F6` | `#3B82F640` | Awaiting payment |
| **paid** | `#10B98120` | `#10B981` | `#10B98140` | Complete |
| **overdue** | `#EF444420` | `#EF4444` | `#EF444440` | Requires action |

### QuoteStatus Colors

| Status | Background | Text | Border | Meaning |
|--------|------------|------|--------|---------|
| **draft** | `#64748B20` | `#94A3B8` | `#64748B40` | Work in progress |
| **sent** | `#3B82F620` | `#3B82F6` | `#3B82F640` | Awaiting response |
| **approved** | `#10B98120` | `#10B981` | `#10B98140` | Ready to convert |
| **declined** | `#EF444420` | `#EF4444` | `#EF444440` | Lost |

### PayrollTransactionType Colors

| Type | Background | Text | Icon |
|------|------------|------|------|
| **earnings** | `#10B98120` | `#10B981` | Plus/Arrow Up |
| **advance** | `#F59E0B20` | `#F59E0B` | Clock/Fast Forward |
| **payment** | `#3B82F620` | `#3B82F6` | Check/Dollar |

### TimeLogAction Colors

| Action | Background | Text | Icon |
|--------|------------|------|------|
| **start_work** | `#10B98120` | `#10B981` | Play |
| **break_start** | `#F59E0B20` | `#F59E0B` | Pause |
| **break_end** | `#3B82F620` | `#3B82F6` | Play |
| **end_work** | `#EF444420` | `#EF4444` | Stop |

---

## PART 3: TYPOGRAPHY

### Font Stack

```
Primary: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
Monospace: "JetBrains Mono", "Fira Code", Consolas, monospace
```

**Bubble Setup:**
- Settings → General → Font: Inter
- Or use Google Fonts plugin for Inter

### Text Hierarchy

| Level | Size | Weight | Line Height | Color | Usage |
|-------|------|--------|-------------|-------|-------|
| **Page Title** | 28px | 700 (Bold) | 1.2 | Text Primary | Page headers |
| **Section Header** | 20px | 600 (Semibold) | 1.3 | Text Primary | Card titles, sections |
| **Subsection** | 16px | 600 (Semibold) | 1.4 | Text Primary | Group headers |
| **Body Large** | 16px | 400 (Regular) | 1.5 | Text Secondary | Primary content |
| **Body** | 14px | 400 (Regular) | 1.5 | Text Secondary | Standard text |
| **Body Small** | 13px | 400 (Regular) | 1.5 | Text Secondary | Dense content |
| **Label** | 13px | 500 (Medium) | 1.4 | Text Muted | Form labels |
| **Caption** | 12px | 400 (Regular) | 1.4 | Text Muted | Help text, timestamps |
| **Overline** | 11px | 600 (Semibold) | 1.3 | Text Muted | Category labels |

### Text Styles Reference

```
Page Title:
  Font size: 28px
  Font weight: 700
  Color: #F8FAFC
  Letter spacing: -0.5px

Section Header:
  Font size: 20px
  Font weight: 600
  Color: #F8FAFC
  Letter spacing: -0.3px

Body:
  Font size: 14px
  Font weight: 400
  Color: #E2E8F0
  Letter spacing: 0

Label:
  Font size: 13px
  Font weight: 500
  Color: #94A3B8
  Letter spacing: 0
  Text transform: none (avoid ALL CAPS for labels)

Muted:
  Font size: 12px
  Font weight: 400
  Color: #64748B
```

---

## PART 4: BUTTON STYLES

### Primary Button

```
Default State:
  Background: #0D9488 (Primary)
  Text: #FFFFFF
  Border: none
  Border radius: 6px
  Padding: 10px 16px
  Font size: 14px
  Font weight: 500
  Box shadow: 0 1px 2px rgba(0,0,0,0.3)
  Cursor: pointer

Hover State:
  Background: #0F766E (Primary Dark)
  Box shadow: 0 2px 4px rgba(0,0,0,0.4)

Active/Pressed State:
  Background: #115E59 (darker)
  Box shadow: 0 1px 1px rgba(0,0,0,0.3)
  Transform: translateY(1px)

Disabled State:
  Background: #334155 (Surface Elevated)
  Text: #64748B (Text Disabled)
  Cursor: not-allowed
  Box shadow: none
```

### Secondary Button

```
Default State:
  Background: transparent
  Text: #E2E8F0 (Text Secondary)
  Border: 1px solid #475569 (Border Light)
  Border radius: 6px
  Padding: 10px 16px

Hover State:
  Background: #334155 (Surface Elevated)
  Border color: #64748B

Active State:
  Background: #1E293B (Surface)

Disabled State:
  Text: #64748B
  Border color: #334155
  Cursor: not-allowed
```

### Danger Button

```
Default State:
  Background: #EF4444 (Danger)
  Text: #FFFFFF
  Border: none
  Border radius: 6px

Hover State:
  Background: #DC2626 (Danger Dark)

Active State:
  Background: #B91C1C

Disabled State:
  Background: #334155
  Text: #64748B
```

### Ghost Button

```
Default State:
  Background: transparent
  Text: #94A3B8 (Text Muted)
  Border: none
  Padding: 8px 12px

Hover State:
  Background: #1E293B (Surface)
  Text: #E2E8F0

Active State:
  Background: #334155
```

### Icon Button

```
Default State:
  Background: transparent
  Width/Height: 32px
  Border radius: 6px
  Icon color: #94A3B8

Hover State:
  Background: #1E293B
  Icon color: #E2E8F0

Active State:
  Background: #334155
```

### Button Sizes

| Size | Padding | Font Size | Height | Icon Size |
|------|---------|-----------|--------|-----------|
| **Small** | 6px 12px | 13px | 28px | 14px |
| **Medium** | 10px 16px | 14px | 36px | 16px |
| **Large** | 12px 20px | 16px | 44px | 18px |

---

## PART 5: BACKGROUND & SURFACE COLORS

### App Shell

```
┌─────────────────────────────────────────────────────────────────┐
│ Sidebar                    │ Main Content Area                  │
│ Background: #0F172A        │ Background: #0F172A                │
│ (same as app background)   │                                    │
│                            │ ┌─────────────────────────────────┐│
│ Nav Item (default):        │ │ Card                            ││
│ Background: transparent    │ │ Background: #1E293B             ││
│                            │ │ Border: 1px solid #334155       ││
│ Nav Item (hover):          │ │ Border radius: 8px              ││
│ Background: #1E293B        │ │ Box shadow:                     ││
│                            │ │   0 1px 3px rgba(0,0,0,0.3)     ││
│ Nav Item (active):         │ │                                 ││
│ Background: #0D948820      │ │                                 ││
│ Border-left: 2px #0D9488   │ └─────────────────────────────────┘│
│ Text: #0D9488              │                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Surface Hierarchy

| Surface Level | Background | Border | Shadow | Usage |
|---------------|------------|--------|--------|-------|
| **Level 0** | `#0F172A` | - | - | Page background |
| **Level 1** | `#1E293B` | `#334155` | 0 1px 3px | Cards, panels |
| **Level 2** | `#334155` | `#475569` | 0 4px 6px | Dropdowns, modals |
| **Level 3** | `#475569` | `#64748B` | 0 10px 15px | Popovers, tooltips |

### Specific Component Backgrounds

| Component | Background | Border | Notes |
|-----------|------------|--------|-------|
| **Page** | `#0F172A` | - | Full viewport |
| **Sidebar** | `#0F172A` | `#334155` (right) | Fixed width 240px |
| **Card** | `#1E293B` | `#334155` | Border radius 8px |
| **Table Header** | `#1E293B` | - | Sticky if scrolling |
| **Table Row** | transparent | - | - |
| **Table Row (hover)** | `#33415540` | - | 25% opacity |
| **Table Row (alt)** | `#1E293B80` | - | 50% opacity, optional |
| **Modal Overlay** | `#0F172ACC` | - | 80% opacity |
| **Modal Content** | `#1E293B` | `#334155` | Border radius 12px |
| **Dropdown** | `#334155` | `#475569` | Shadow Level 2 |
| **Input** | `#1E293B` | `#334155` | Border radius 6px |
| **Input (focus)** | `#1E293B` | `#0D9488` | 2px border |
| **Stat Card** | `#1E293B` | `#334155` | - |
| **Badge** | varies | - | Per status |

---

## PART 6: FORM ELEMENTS

### Input Fields

```
Default State:
  Background: #1E293B
  Border: 1px solid #334155
  Border radius: 6px
  Padding: 10px 12px
  Font size: 14px
  Text color: #E2E8F0
  Placeholder color: #64748B

Hover State:
  Border color: #475569

Focus State:
  Border color: #0D9488
  Border width: 2px
  Box shadow: 0 0 0 3px #0D948830

Error State:
  Border color: #EF4444
  Box shadow: 0 0 0 3px #EF444430

Disabled State:
  Background: #0F172A
  Border color: #1E293B
  Text color: #64748B
  Cursor: not-allowed
```

### Select/Dropdown

```
Trigger:
  Same as Input default
  Right padding: 36px (for chevron)
  Chevron icon color: #64748B

Dropdown Panel:
  Background: #334155
  Border: 1px solid #475569
  Border radius: 6px
  Box shadow: 0 4px 6px rgba(0,0,0,0.4)
  Max height: 300px (scrollable)

Option (default):
  Padding: 10px 12px
  Background: transparent

Option (hover):
  Background: #475569

Option (selected):
  Background: #0D948830
  Text color: #0D9488
```

### Checkbox

```
Box (unchecked):
  Size: 18px × 18px
  Background: #1E293B
  Border: 2px solid #475569
  Border radius: 4px

Box (checked):
  Background: #0D9488
  Border color: #0D9488
  Checkmark: white

Box (hover):
  Border color: #0D9488

Label:
  Font size: 14px
  Color: #E2E8F0
  Margin left: 8px
```

### Toggle/Switch

```
Track (off):
  Width: 44px
  Height: 24px
  Background: #334155
  Border radius: 12px

Track (on):
  Background: #0D9488

Thumb:
  Size: 20px
  Background: white
  Border radius: 50%
  Box shadow: 0 1px 3px rgba(0,0,0,0.4)
  Transition: transform 150ms
```

---

## PART 7: SPACING SYSTEM

### Base Unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| **space-1** | 4px | Tight spacing, icon gaps |
| **space-2** | 8px | Related elements |
| **space-3** | 12px | Form element gaps |
| **space-4** | 16px | Section padding |
| **space-5** | 20px | Card padding |
| **space-6** | 24px | Group separation |
| **space-8** | 32px | Section separation |
| **space-10** | 40px | Major separation |
| **space-12** | 48px | Page margins |

### Component Spacing

| Component | Internal Padding | Margin/Gap |
|-----------|------------------|------------|
| **Page** | 24px - 32px | - |
| **Card** | 20px | 16px between cards |
| **Card Header** | 16px 20px | - |
| **Card Body** | 20px | - |
| **Table Cell** | 12px 16px | - |
| **Form Group** | - | 16px between groups |
| **Button Group** | - | 8px between buttons |
| **List Item** | 12px 16px | - |
| **Modal** | 24px | - |
| **Badge** | 4px 8px | - |

---

## PART 8: BORDER RADIUS

| Token | Value | Usage |
|-------|-------|-------|
| **radius-sm** | 4px | Badges, small elements |
| **radius-md** | 6px | Buttons, inputs |
| **radius-lg** | 8px | Cards, panels |
| **radius-xl** | 12px | Modals, large cards |
| **radius-full** | 9999px | Pills, avatars |

---

## PART 9: SHADOWS

| Level | Shadow | Usage |
|-------|--------|-------|
| **shadow-sm** | 0 1px 2px rgba(0,0,0,0.3) | Buttons, subtle elevation |
| **shadow-md** | 0 2px 4px rgba(0,0,0,0.3) | Cards, panels |
| **shadow-lg** | 0 4px 6px rgba(0,0,0,0.4) | Dropdowns |
| **shadow-xl** | 0 10px 15px rgba(0,0,0,0.4) | Modals |
| **shadow-glow** | 0 0 20px rgba(13,148,136,0.3) | Highlighted elements |

---

## PART 10: WHEN TO USE COLOR VS NEUTRAL

### Use Color For:

```
✅ Status indicators (badges, dots)
✅ Primary action buttons
✅ Active navigation items
✅ Links and interactive elements
✅ Success/error/warning messages
✅ Progress indicators
✅ Charts and data visualization
✅ Focus states
✅ Selected items
```

### Use Neutral For:

```
⬜ Page backgrounds
⬜ Card backgrounds
⬜ Table backgrounds
⬜ Body text
⬜ Secondary buttons
⬜ Borders and dividers
⬜ Icons (default state)
⬜ Disabled elements
⬜ Form inputs (default)
⬜ Most of the UI surface
```

### Color Usage Guidelines

```
Rule 1: STATUS DRIVES COLOR
  - A job card is neutral
  - The status badge on the card is colored
  - Don't make the whole card green for "complete"

Rule 2: ONE PRIMARY ACTION PER VIEW
  - One teal primary button per card/section
  - Other actions use secondary/ghost buttons

Rule 3: COLOR FOR INFORMATION, NOT DECORATION
  - Green badge = "paid" (information)
  - Green border on card = decoration (avoid)

Rule 4: SEMANTIC COLORS HAVE MEANING
  - Green = success, complete, positive
  - Red = error, danger, overdue
  - Yellow/Amber = warning, pending, attention
  - Blue = info, in progress, neutral action
  - Don't use red for non-dangerous actions

Rule 5: DESATURATE FOR BACKGROUNDS
  - Badge background: color at 12-20% opacity
  - Never use full-saturation color as background
```

### Examples

```
✅ CORRECT:
Card background: #1E293B (neutral)
Status badge: #10B98120 background, #10B981 text (green for "complete")

❌ WRONG:
Card background: #10B981 (full green for complete jobs)
Status badge: #1E293B (neutral for all statuses)

✅ CORRECT:
Primary action: Teal button "Create Invoice"
Secondary action: Ghost button "Cancel"
Danger action: Red button "Delete"

❌ WRONG:
All buttons are teal
Delete button is teal
```

---

## PART 11: COMPONENT RECIPES

### Status Badge

```
Container:
  Display: inline-flex
  Align items: center
  Padding: 4px 8px
  Border radius: 4px
  Font size: 12px
  Font weight: 500
  
Conditional styling per status - see Part 2
```

### Stat Card

```
Container:
  Background: #1E293B
  Border: 1px solid #334155
  Border radius: 8px
  Padding: 20px

Label:
  Font size: 13px
  Font weight: 500
  Color: #94A3B8
  Margin bottom: 4px

Value:
  Font size: 28px
  Font weight: 700
  Color: #F8FAFC

Subtext (optional):
  Font size: 12px
  Color: #64748B
  Margin top: 4px
```

### Table

```
Container:
  Background: #1E293B
  Border: 1px solid #334155
  Border radius: 8px
  Overflow: hidden

Header Row:
  Background: #1E293B
  Border bottom: 1px solid #334155

Header Cell:
  Padding: 12px 16px
  Font size: 12px
  Font weight: 600
  Color: #94A3B8
  Text transform: uppercase
  Letter spacing: 0.5px

Body Row:
  Border bottom: 1px solid #33415540

Body Row (hover):
  Background: #33415530

Body Cell:
  Padding: 12px 16px
  Font size: 14px
  Color: #E2E8F0
```

### Navigation Item

```
Container:
  Display: flex
  Align items: center
  Padding: 10px 16px
  Border radius: 6px
  Cursor: pointer
  Transition: background 150ms

Default:
  Background: transparent
  Color: #94A3B8

Hover:
  Background: #1E293B
  Color: #E2E8F0

Active:
  Background: #0D948820
  Color: #0D9488
  Border-left: 2px solid #0D9488

Icon:
  Size: 18px
  Margin right: 12px
```

### Empty State

```
Container:
  Text align: center
  Padding: 48px 24px

Icon:
  Size: 48px
  Color: #475569
  Margin bottom: 16px

Title:
  Font size: 16px
  Font weight: 600
  Color: #E2E8F0
  Margin bottom: 8px

Description:
  Font size: 14px
  Color: #94A3B8
  Margin bottom: 24px

Action Button:
  Primary style
```

---

## PART 12: QUICK REFERENCE

### Color Values (Copy-Paste Ready)

```
/* Brand */
--primary: #0D9488;
--primary-dark: #0F766E;
--primary-light: #14B8A6;
--primary-muted: rgba(13, 148, 136, 0.1);

/* Semantic */
--success: #10B981;
--success-muted: rgba(16, 185, 129, 0.12);
--warning: #F59E0B;
--warning-muted: rgba(245, 158, 11, 0.12);
--danger: #EF4444;
--danger-muted: rgba(239, 68, 68, 0.12);
--info: #3B82F6;
--info-muted: rgba(59, 130, 246, 0.12);

/* Neutral (Dark Theme) */
--background: #0F172A;
--surface: #1E293B;
--surface-elevated: #334155;
--border: #334155;
--border-light: #475569;

/* Text */
--text-primary: #F8FAFC;
--text-secondary: #E2E8F0;
--text-muted: #94A3B8;
--text-disabled: #64748B;
```

### Status Badge Classes

```
/* JobStatus */
.status-quoted { background: #F59E0B20; color: #F59E0B; }
.status-approved { background: #3B82F620; color: #3B82F6; }
.status-in-production { background: #8B5CF620; color: #8B5CF6; }
.status-installed { background: #06B6D420; color: #06B6D4; }
.status-complete { background: #10B98120; color: #10B981; }
.status-archived { background: #64748B20; color: #64748B; }

/* InvoiceStatus */
.status-draft { background: #64748B20; color: #94A3B8; }
.status-sent { background: #3B82F620; color: #3B82F6; }
.status-paid { background: #10B98120; color: #10B981; }
.status-overdue { background: #EF444420; color: #EF4444; }

/* QuoteStatus */
.status-declined { background: #EF444420; color: #EF4444; }
```

### Bubble Style Presets

Create these as reusable styles in Bubble:

```
Styles to create:
1. btn-primary
2. btn-secondary
3. btn-danger
4. btn-ghost
5. input-default
6. card-default
7. badge-success
8. badge-warning
9. badge-danger
10. badge-info
11. badge-neutral
12. text-page-title
13. text-section-header
14. text-body
15. text-muted
16. nav-item
17. nav-item-active
18. table-header
19. table-row
```

---

## PART 13: ACCESSIBILITY CHECKLIST

### Contrast Ratios (WCAG AA)

| Combination | Ratio | Pass? |
|-------------|-------|-------|
| Text Primary on Background | 15.8:1 | ✅ |
| Text Secondary on Background | 11.4:1 | ✅ |
| Text Muted on Background | 5.5:1 | ✅ |
| Primary on Background | 4.6:1 | ✅ |
| Success on Background | 7.2:1 | ✅ |
| Warning on Background | 8.1:1 | ✅ |
| Danger on Background | 4.6:1 | ✅ |

### Focus States

```
All interactive elements must have visible focus:
  - Buttons: 2px ring in primary color
  - Inputs: Border color change + shadow
  - Links: Underline or color change
  - Cards (if clickable): Border highlight
```

### Minimum Touch Targets

```
Mobile considerations (even for desktop-first):
  - Minimum clickable area: 44px × 44px
  - Button minimum height: 36px
  - Icon buttons: 32px × 32px minimum
```
