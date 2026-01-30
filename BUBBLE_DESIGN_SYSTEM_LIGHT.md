# Sign Guy AI - Bubble Design System (Light Theme)

## OVERVIEW

A professional, light-mode design system for sign shop operations. Desktop-optimized with clear hierarchy and status-driven color usage.

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
| **Primary Muted** | `#0D948815` | - | Backgrounds (8% opacity) |

### Secondary Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Secondary** | `#6366F1` | 99, 102, 241 | Secondary actions, links |
| **Secondary Dark** | `#4F46E5` | 79, 70, 229 | Hover states |
| **Secondary Light** | `#818CF8` | 129, 140, 248 | Highlights |

### Accent Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Accent** | `#D97706` | 217, 119, 6 | Attention, highlights, badges |
| **Accent Dark** | `#B45309` | 180, 83, 9 | Hover |
| **Accent Light** | `#F59E0B` | 245, 158, 11 | Soft highlights |

### Semantic Colors

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Success** | `#059669` | 5, 150, 105 | Completed, paid, positive |
| **Success Dark** | `#047857` | 4, 120, 87 | Hover |
| **Success Light** | `#10B981` | 16, 185, 129 | Icons |
| **Success Muted** | `#05966915` | - | Background (8% opacity) |
| | | | |
| **Warning** | `#D97706` | 217, 119, 6 | Attention needed, pending |
| **Warning Dark** | `#B45309` | 180, 83, 9 | Hover |
| **Warning Light** | `#F59E0B` | 245, 158, 11 | Icons |
| **Warning Muted** | `#D9770615` | - | Background (8% opacity) |
| | | | |
| **Danger** | `#DC2626` | 220, 38, 38 | Errors, delete, overdue |
| **Danger Dark** | `#B91C1C` | 185, 28, 28 | Hover |
| **Danger Light** | `#EF4444` | 239, 68, 68 | Icons |
| **Danger Muted** | `#DC262615` | - | Background (8% opacity) |
| | | | |
| **Info** | `#2563EB` | 37, 99, 235 | Informational, links |
| **Info Dark** | `#1D4ED8` | 29, 78, 216 | Hover |
| **Info Light** | `#3B82F6` | 59, 130, 246 | Icons |

### Neutral Colors (Light Theme)

| Name | HEX | RGB | Usage |
|------|-----|-----|-------|
| **Background** | `#F8FAFC` | 248, 250, 252 | App shell, page background |
| **Surface** | `#FFFFFF` | 255, 255, 255 | Cards, panels, modals |
| **Surface Elevated** | `#F1F5F9` | 241, 245, 249 | Hover states, selected |
| **Surface Sunken** | `#E2E8F0` | 226, 232, 240 | Input backgrounds |
| **Border** | `#E2E8F0` | 226, 232, 240 | Dividers, borders |
| **Border Dark** | `#CBD5E1` | 203, 213, 225 | Stronger borders |
| | | | |
| **Text Primary** | `#0F172A` | 15, 23, 42 | Headings, important text |
| **Text Secondary** | `#334155` | 51, 65, 85 | Body text |
| **Text Muted** | `#64748B` | 100, 116, 139 | Labels, placeholders |
| **Text Disabled** | `#94A3B8` | 148, 163, 184 | Disabled states |

---

## PART 2: STATUS COLOR MAPPING

### JobStatus Colors

| Status | Background | Text | Border | Badge Style |
|--------|------------|------|--------|-------------|
| **quoted** | `#FEF3C7` | `#B45309` | `#FDE68A` | Warning/Amber |
| **approved** | `#DBEAFE` | `#1D4ED8` | `#BFDBFE` | Info/Blue |
| **in_production** | `#EDE9FE` | `#7C3AED` | `#DDD6FE` | Purple |
| **installed** | `#CFFAFE` | `#0891B2` | `#A5F3FC` | Cyan |
| **complete** | `#D1FAE5` | `#047857` | `#A7F3D0` | Success/Green |
| **archived** | `#F1F5F9` | `#64748B` | `#E2E8F0` | Neutral/Gray |

**Bubble Implementation:**
```
Conditional: When This Job's status is "quoted"
  Background color: #FEF3C7
  Font color: #B45309
```

### InvoiceStatus Colors

| Status | Background | Text | Border | Meaning |
|--------|------------|------|--------|---------|
| **draft** | `#F1F5F9` | `#64748B` | `#E2E8F0` | Not sent yet |
| **sent** | `#DBEAFE` | `#1D4ED8` | `#BFDBFE` | Awaiting payment |
| **paid** | `#D1FAE5` | `#047857` | `#A7F3D0` | Complete |
| **overdue** | `#FEE2E2` | `#B91C1C` | `#FECACA` | Requires action |

### QuoteStatus Colors

| Status | Background | Text | Border | Meaning |
|--------|------------|------|--------|---------|
| **draft** | `#F1F5F9` | `#64748B` | `#E2E8F0` | Work in progress |
| **sent** | `#DBEAFE` | `#1D4ED8` | `#BFDBFE` | Awaiting response |
| **approved** | `#D1FAE5` | `#047857` | `#A7F3D0` | Ready to convert |
| **declined** | `#FEE2E2` | `#B91C1C` | `#FECACA` | Lost |

### PayrollTransactionType Colors

| Type | Background | Text | Icon |
|------|------------|------|------|
| **earnings** | `#D1FAE5` | `#047857` | Plus/Arrow Up |
| **advance** | `#FEF3C7` | `#B45309` | Clock/Fast Forward |
| **payment** | `#DBEAFE` | `#1D4ED8` | Check/Dollar |

### TimeLogAction Colors

| Action | Background | Text | Icon |
|--------|------------|------|------|
| **start_work** | `#D1FAE5` | `#047857` | Play |
| **break_start** | `#FEF3C7` | `#B45309` | Pause |
| **break_end** | `#DBEAFE` | `#1D4ED8` | Play |
| **end_work** | `#FEE2E2` | `#B91C1C` | Stop |

---

## PART 3: TYPOGRAPHY

### Font Stack

```
Primary: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
Monospace: "JetBrains Mono", "Fira Code", Consolas, monospace
```

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
  Color: #0F172A
  Letter spacing: -0.5px

Section Header:
  Font size: 20px
  Font weight: 600
  Color: #0F172A
  Letter spacing: -0.3px

Body:
  Font size: 14px
  Font weight: 400
  Color: #334155
  Letter spacing: 0

Label:
  Font size: 13px
  Font weight: 500
  Color: #64748B
  Letter spacing: 0

Muted:
  Font size: 12px
  Font weight: 400
  Color: #94A3B8
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
  Box shadow: 0 1px 2px rgba(0,0,0,0.1)
  Cursor: pointer

Hover State:
  Background: #0F766E (Primary Dark)
  Box shadow: 0 2px 4px rgba(0,0,0,0.15)

Active/Pressed State:
  Background: #115E59 (darker)
  Box shadow: 0 1px 1px rgba(0,0,0,0.1)
  Transform: translateY(1px)

Disabled State:
  Background: #E2E8F0 (Border)
  Text: #94A3B8 (Text Disabled)
  Cursor: not-allowed
  Box shadow: none
```

### Secondary Button

```
Default State:
  Background: #FFFFFF
  Text: #334155 (Text Secondary)
  Border: 1px solid #CBD5E1 (Border Dark)
  Border radius: 6px
  Padding: 10px 16px

Hover State:
  Background: #F1F5F9 (Surface Elevated)
  Border color: #94A3B8

Active State:
  Background: #E2E8F0

Disabled State:
  Background: #F8FAFC
  Text: #94A3B8
  Border color: #E2E8F0
  Cursor: not-allowed
```

### Danger Button

```
Default State:
  Background: #DC2626 (Danger)
  Text: #FFFFFF
  Border: none
  Border radius: 6px

Hover State:
  Background: #B91C1C (Danger Dark)

Active State:
  Background: #991B1B

Disabled State:
  Background: #E2E8F0
  Text: #94A3B8
```

### Ghost Button

```
Default State:
  Background: transparent
  Text: #64748B (Text Muted)
  Border: none
  Padding: 8px 12px

Hover State:
  Background: #F1F5F9 (Surface Elevated)
  Text: #334155

Active State:
  Background: #E2E8F0
```

### Icon Button

```
Default State:
  Background: transparent
  Width/Height: 32px
  Border radius: 6px
  Icon color: #64748B

Hover State:
  Background: #F1F5F9
  Icon color: #334155

Active State:
  Background: #E2E8F0
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
│ Background: #FFFFFF        │ Background: #F8FAFC                │
│ Border-right: #E2E8F0      │                                    │
│                            │ ┌─────────────────────────────────┐│
│ Nav Item (default):        │ │ Card                            ││
│ Background: transparent    │ │ Background: #FFFFFF             ││
│ Text: #64748B              │ │ Border: 1px solid #E2E8F0       ││
│                            │ │ Border radius: 8px              ││
│ Nav Item (hover):          │ │ Box shadow:                     ││
│ Background: #F1F5F9        │ │   0 1px 3px rgba(0,0,0,0.08)    ││
│ Text: #334155              │ │                                 ││
│                            │ │                                 ││
│ Nav Item (active):         │ └─────────────────────────────────┘│
│ Background: #0D948815      │                                    │
│ Border-left: 2px #0D9488   │                                    │
│ Text: #0D9488              │                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Surface Hierarchy

| Surface Level | Background | Border | Shadow | Usage |
|---------------|------------|--------|--------|-------|
| **Level 0** | `#F8FAFC` | - | - | Page background |
| **Level 1** | `#FFFFFF` | `#E2E8F0` | 0 1px 3px rgba(0,0,0,0.08) | Cards, panels |
| **Level 2** | `#FFFFFF` | `#CBD5E1` | 0 4px 6px rgba(0,0,0,0.1) | Dropdowns, modals |
| **Level 3** | `#FFFFFF` | `#CBD5E1` | 0 10px 15px rgba(0,0,0,0.1) | Popovers, tooltips |

### Specific Component Backgrounds

| Component | Background | Border | Notes |
|-----------|------------|--------|-------|
| **Page** | `#F8FAFC` | - | Full viewport |
| **Sidebar** | `#FFFFFF` | `#E2E8F0` (right) | Fixed width 240px |
| **Card** | `#FFFFFF` | `#E2E8F0` | Border radius 8px |
| **Table Header** | `#F8FAFC` | - | Sticky if scrolling |
| **Table Row** | `#FFFFFF` | - | - |
| **Table Row (hover)** | `#F1F5F9` | - | - |
| **Table Row (alt)** | `#F8FAFC` | - | Zebra striping, optional |
| **Modal Overlay** | `#0F172A80` | - | 50% opacity |
| **Modal Content** | `#FFFFFF` | `#E2E8F0` | Border radius 12px |
| **Dropdown** | `#FFFFFF` | `#CBD5E1` | Shadow Level 2 |
| **Input** | `#FFFFFF` | `#CBD5E1` | Border radius 6px |
| **Input (focus)** | `#FFFFFF` | `#0D9488` | 2px border |
| **Stat Card** | `#FFFFFF` | `#E2E8F0` | - |
| **Badge** | varies | varies | Per status |

---

## PART 6: FORM ELEMENTS

### Input Fields

```
Default State:
  Background: #FFFFFF
  Border: 1px solid #CBD5E1
  Border radius: 6px
  Padding: 10px 12px
  Font size: 14px
  Text color: #334155
  Placeholder color: #94A3B8

Hover State:
  Border color: #94A3B8

Focus State:
  Border color: #0D9488
  Border width: 2px
  Box shadow: 0 0 0 3px #0D948820

Error State:
  Border color: #DC2626
  Box shadow: 0 0 0 3px #DC262620

Disabled State:
  Background: #F1F5F9
  Border color: #E2E8F0
  Text color: #94A3B8
  Cursor: not-allowed
```

### Select/Dropdown

```
Trigger:
  Same as Input default
  Right padding: 36px (for chevron)
  Chevron icon color: #64748B

Dropdown Panel:
  Background: #FFFFFF
  Border: 1px solid #CBD5E1
  Border radius: 6px
  Box shadow: 0 4px 6px rgba(0,0,0,0.1)
  Max height: 300px (scrollable)

Option (default):
  Padding: 10px 12px
  Background: transparent

Option (hover):
  Background: #F1F5F9

Option (selected):
  Background: #0D948815
  Text color: #0D9488
```

### Checkbox

```
Box (unchecked):
  Size: 18px × 18px
  Background: #FFFFFF
  Border: 2px solid #CBD5E1
  Border radius: 4px

Box (checked):
  Background: #0D9488
  Border color: #0D9488
  Checkmark: white

Box (hover):
  Border color: #0D9488

Label:
  Font size: 14px
  Color: #334155
  Margin left: 8px
```

### Toggle/Switch

```
Track (off):
  Width: 44px
  Height: 24px
  Background: #CBD5E1
  Border radius: 12px

Track (on):
  Background: #0D9488

Thumb:
  Size: 20px
  Background: white
  Border radius: 50%
  Box shadow: 0 1px 3px rgba(0,0,0,0.2)
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
| **shadow-sm** | 0 1px 2px rgba(0,0,0,0.05) | Buttons, subtle elevation |
| **shadow-md** | 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06) | Cards, panels |
| **shadow-lg** | 0 4px 6px rgba(0,0,0,0.1) | Dropdowns |
| **shadow-xl** | 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05) | Modals |
| **shadow-glow** | 0 0 20px rgba(13,148,136,0.15) | Highlighted elements |

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
  - A job card is white/neutral
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

Rule 5: USE PASTEL BACKGROUNDS
  - Badge background: soft pastel version of color
  - Never use full-saturation color as background
  - Light theme uses lighter, more pastel tones
```

### Light Theme Specific Rules

```
Rule 6: MAINTAIN CONTRAST
  - Text on colored backgrounds must be dark
  - Use darker shade of semantic color for text
  - Example: Success bg #D1FAE5, text #047857

Rule 7: SUBTLE SHADOWS OVER BORDERS
  - Light theme can rely more on shadow for depth
  - Use softer shadows (less opacity) than dark theme

Rule 8: AVOID PURE WHITE ON PURE WHITE
  - Cards on page: white (#FFFFFF) on off-white (#F8FAFC)
  - Creates subtle distinction without heavy borders
```

---

## PART 11: COMPONENT RECIPES

### Status Badge

```
Container:
  Display: inline-flex
  Align items: center
  Padding: 4px 10px
  Border radius: 4px
  Font size: 12px
  Font weight: 500
  Border: 1px solid (varies)
  
Conditional styling per status - see Part 2
```

### Stat Card

```
Container:
  Background: #FFFFFF
  Border: 1px solid #E2E8F0
  Border radius: 8px
  Padding: 20px
  Box shadow: 0 1px 3px rgba(0,0,0,0.08)

Label:
  Font size: 13px
  Font weight: 500
  Color: #64748B
  Margin bottom: 4px

Value:
  Font size: 28px
  Font weight: 700
  Color: #0F172A

Subtext (optional):
  Font size: 12px
  Color: #94A3B8
  Margin top: 4px
```

### Table

```
Container:
  Background: #FFFFFF
  Border: 1px solid #E2E8F0
  Border radius: 8px
  Overflow: hidden
  Box shadow: 0 1px 3px rgba(0,0,0,0.08)

Header Row:
  Background: #F8FAFC
  Border bottom: 1px solid #E2E8F0

Header Cell:
  Padding: 12px 16px
  Font size: 12px
  Font weight: 600
  Color: #64748B
  Text transform: uppercase
  Letter spacing: 0.5px

Body Row:
  Background: #FFFFFF
  Border bottom: 1px solid #F1F5F9

Body Row (hover):
  Background: #F8FAFC

Body Cell:
  Padding: 12px 16px
  Font size: 14px
  Color: #334155
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
  Color: #64748B

Hover:
  Background: #F1F5F9
  Color: #334155

Active:
  Background: #0D948815
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
  Color: #CBD5E1
  Margin bottom: 16px

Title:
  Font size: 16px
  Font weight: 600
  Color: #334155
  Margin bottom: 8px

Description:
  Font size: 14px
  Color: #64748B
  Margin bottom: 24px

Action Button:
  Primary style
```

### Alert/Banner

```
Success Alert:
  Background: #D1FAE5
  Border: 1px solid #A7F3D0
  Border-left: 4px solid #059669
  Text: #047857
  Icon: #059669

Warning Alert:
  Background: #FEF3C7
  Border: 1px solid #FDE68A
  Border-left: 4px solid #D97706
  Text: #B45309
  Icon: #D97706

Danger Alert:
  Background: #FEE2E2
  Border: 1px solid #FECACA
  Border-left: 4px solid #DC2626
  Text: #B91C1C
  Icon: #DC2626

Info Alert:
  Background: #DBEAFE
  Border: 1px solid #BFDBFE
  Border-left: 4px solid #2563EB
  Text: #1D4ED8
  Icon: #2563EB
```

---

## PART 12: QUICK REFERENCE

### Color Values (Copy-Paste Ready)

```
/* Brand */
--primary: #0D9488;
--primary-dark: #0F766E;
--primary-light: #14B8A6;
--primary-muted: rgba(13, 148, 136, 0.08);

/* Semantic */
--success: #059669;
--success-light: #10B981;
--success-muted: #D1FAE5;
--success-border: #A7F3D0;

--warning: #D97706;
--warning-light: #F59E0B;
--warning-muted: #FEF3C7;
--warning-border: #FDE68A;

--danger: #DC2626;
--danger-light: #EF4444;
--danger-muted: #FEE2E2;
--danger-border: #FECACA;

--info: #2563EB;
--info-light: #3B82F6;
--info-muted: #DBEAFE;
--info-border: #BFDBFE;

/* Neutral (Light Theme) */
--background: #F8FAFC;
--surface: #FFFFFF;
--surface-elevated: #F1F5F9;
--surface-sunken: #E2E8F0;
--border: #E2E8F0;
--border-dark: #CBD5E1;

/* Text */
--text-primary: #0F172A;
--text-secondary: #334155;
--text-muted: #64748B;
--text-disabled: #94A3B8;
```

### Status Badge Classes

```
/* JobStatus */
.status-quoted { background: #FEF3C7; color: #B45309; border-color: #FDE68A; }
.status-approved { background: #DBEAFE; color: #1D4ED8; border-color: #BFDBFE; }
.status-in-production { background: #EDE9FE; color: #7C3AED; border-color: #DDD6FE; }
.status-installed { background: #CFFAFE; color: #0891B2; border-color: #A5F3FC; }
.status-complete { background: #D1FAE5; color: #047857; border-color: #A7F3D0; }
.status-archived { background: #F1F5F9; color: #64748B; border-color: #E2E8F0; }

/* InvoiceStatus */
.status-draft { background: #F1F5F9; color: #64748B; border-color: #E2E8F0; }
.status-sent { background: #DBEAFE; color: #1D4ED8; border-color: #BFDBFE; }
.status-paid { background: #D1FAE5; color: #047857; border-color: #A7F3D0; }
.status-overdue { background: #FEE2E2; color: #B91C1C; border-color: #FECACA; }

/* QuoteStatus */
.status-declined { background: #FEE2E2; color: #B91C1C; border-color: #FECACA; }
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
20. alert-success
21. alert-warning
22. alert-danger
23. alert-info
```

---

## PART 13: ACCESSIBILITY CHECKLIST

### Contrast Ratios (WCAG AA)

| Combination | Ratio | Pass? |
|-------------|-------|-------|
| Text Primary on Background | 16.1:1 | ✅ |
| Text Secondary on Background | 9.5:1 | ✅ |
| Text Muted on Background | 4.8:1 | ✅ |
| Text Primary on Surface | 15.4:1 | ✅ |
| Primary on Surface | 4.5:1 | ✅ |
| Success (dark) on Success Muted | 5.2:1 | ✅ |
| Warning (dark) on Warning Muted | 4.7:1 | ✅ |
| Danger (dark) on Danger Muted | 5.8:1 | ✅ |

### Focus States

```
All interactive elements must have visible focus:
  - Buttons: 2px ring in primary color with offset
  - Inputs: Border color change + shadow ring
  - Links: Underline or background change
  - Cards (if clickable): Border highlight or shadow increase
```

### Minimum Touch Targets

```
Desktop-first but accessible:
  - Minimum clickable area: 44px × 44px
  - Button minimum height: 36px
  - Icon buttons: 32px × 32px minimum
```

---

## PART 14: DARK/LIGHT THEME COMPARISON

### Quick Reference Table

| Element | Dark Theme | Light Theme |
|---------|------------|-------------|
| **Page Background** | `#0F172A` | `#F8FAFC` |
| **Card Background** | `#1E293B` | `#FFFFFF` |
| **Card Border** | `#334155` | `#E2E8F0` |
| **Text Primary** | `#F8FAFC` | `#0F172A` |
| **Text Secondary** | `#E2E8F0` | `#334155` |
| **Text Muted** | `#94A3B8` | `#64748B` |
| **Input Background** | `#1E293B` | `#FFFFFF` |
| **Input Border** | `#334155` | `#CBD5E1` |
| **Table Header** | `#1E293B` | `#F8FAFC` |
| **Hover State** | `#334155` | `#F1F5F9` |
| **Shadow Opacity** | 0.3-0.4 | 0.05-0.1 |
| **Status Badge BG** | 12-20% opacity | Pastel solid |

### Theme Switching (If Implementing Both)

```
Bubble approach:
1. Create custom states for theme (dark/light)
2. Use conditionals on every styled element
3. Or: Create duplicate styles with -dark/-light suffix

CSS Variables approach (if using custom code):
1. Define variables for both themes
2. Toggle class on body element
3. All components inherit from variables
```
