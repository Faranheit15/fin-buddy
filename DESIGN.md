---
name: Fin Buddy
description: India-first credit card and friend-lending ledger — category-standard ops craft with warm professional edges.
colors:
  background: "oklch(1 0 0)"
  foreground: "oklch(0.145 0 0)"
  primary: "oklch(0.205 0 0)"
  primary-foreground: "oklch(0.985 0 0)"
  secondary: "oklch(0.97 0 0)"
  secondary-foreground: "oklch(0.205 0 0)"
  muted: "oklch(0.97 0 0)"
  muted-foreground: "oklch(0.556 0 0)"
  accent: "oklch(0.97 0 0)"
  accent-foreground: "oklch(0.205 0 0)"
  destructive: "oklch(0.577 0.245 27.325)"
  border: "oklch(0.922 0 0)"
  input: "oklch(0.922 0 0)"
  ring: "oklch(0.708 0 0)"
  card: "oklch(1 0 0)"
  card-foreground: "oklch(0.145 0 0)"
  sidebar: "oklch(0.985 0 0)"
  sidebar-foreground: "oklch(0.145 0 0)"
  sidebar-primary: "oklch(0.205 0 0)"
  sidebar-primary-foreground: "oklch(0.985 0 0)"
  chart-1: "oklch(0.87 0 0)"
  chart-2: "oklch(0.556 0 0)"
  chart-3: "oklch(0.439 0 0)"
  dark-background: "oklch(0.145 0 0)"
  dark-foreground: "oklch(0.985 0 0)"
  dark-primary: "oklch(0.922 0 0)"
  dark-card: "oklch(0.205 0 0)"
  dark-border: "oklch(1 0 0 / 10%)"
  dark-sidebar: "oklch(0.205 0 0)"
  dark-sidebar-primary: "oklch(0.488 0.243 264.376)"
  marketing-glow: "oklch(0.95 0.02 250)"
  marketing-glow-dark: "oklch(0.25 0.04 250)"
typography:
  display:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 5vw, 3.75rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "normal"
  body:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  body-lg:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  label:
    fontFamily: "Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.2em"
  mono:
    fontFamily: "Geist Mono, ui-monospace, SFMono-Regular, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
rounded:
  sm: "0.375rem"
  md: "0.5rem"
  lg: "0.625rem"
  xl: "0.875rem"
  "2xl": "1.125rem"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
  "2xl": "4rem"
  page-x: "1.5rem"
  container: "72rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.lg}"
    padding: "0 0.625rem"
    height: "2rem"
  button-primary-hover:
    backgroundColor: "color-mix(in oklch, {colors.primary} 80%, transparent)"
    textColor: "{colors.primary-foreground}"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    height: "2rem"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    height: "2rem"
  button-destructive:
    backgroundColor: "color-mix(in oklch, {colors.destructive} 10%, transparent)"
    textColor: "{colors.destructive}"
    rounded: "{rounded.lg}"
  card-default:
    backgroundColor: "{colors.card}"
    textColor: "{colors.card-foreground}"
    rounded: "{rounded.xl}"
    padding: "1.25rem"
  input-default:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
  mark-brand:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.lg}"
    size: "2rem"
---

# Design System: Fin Buddy

## Overview

**Creative North Star: "The Ledger Shelf"**

Fin Buddy’s visual system is an authoritative, scannable money ledger dressed for daily use — not a lifestyle wallet and not a conceptual “art world.” Surfaces should feel like a shelf of permanent records: dense enough for multi-card power users, calm enough for a morning dues check. The craft bar is category-standard Indian fintech ops (Zerodha Kite / Coin density for positions, urgency, and figures), with structural density allowed to echo finance-admin shells (sidebar, KPI strip, tables, activity) without cloning any template chrome.

Personality is **warm professional with soft marketing edges**: marketing routes (landing, auth) may breathe — generous max-width prose, soft radial wash, slightly larger type — while the authenticated app stays cooler, denser, and task-first. Dark mode is first-class and inverts surfaces without inventing a second brand.

Source of truth for tokens is **OKLCH CSS variables** in `frontend/src/app/globals.css` (shadcn base-nova), with **Geist** / **Geist Mono** loaded in `frontend/src/app/layout.tsx`. Components start from shadcn/ui (Base UI + CVA).

**Key Characteristics:**

- Operate-first density for app surfaces; marketing may open the measure
- Near-monochrome primary ink with semantic red for danger
- Soft card lift (`shadow-sm`) as the default elevation language
- Gentle 10px-class radii; rounded-lg controls, rounded-xl / 2xl panels
- Dark mode parity; India presentation lives in formatters (INR, IST, en-IN), not decorative motifs
- No purple gradients, no nested card soup, no display-serif “fintech editorial” default

## Colors

Near-neutral monochrome with a single ink primary and a warm-coral **destructive**. Marketing may add a faint cool radial wash; app chrome should not rely on it.

### Primary

- **Ledger Ink** (`oklch(0.205 0 0)` → near `#1a1a1a`): Primary actions, brand mark, emphasis. In dark mode primary flips to light ink (`oklch(0.922 0 0)`).
- **Ledger Ink Inverse** (`oklch(0.985 0 0)`): Text/icons on primary fills.

### Secondary / Accent (neutral layers)

- **Shelf Mist** (`oklch(0.97 0 0)`): Secondary buttons, muted fills, hover wash, soft panels.
- **Shelf Mist Foreground** (`oklch(0.205 0 0)`): Text on mist surfaces.
- Accent tokens currently alias the same mist family — treat accent as a **neutral interactive wash**, not a second brand hue.

### Neutral

- **Paper White** (`oklch(1 0 0)`): Page and card backgrounds (light).
- **Ink Body** (`oklch(0.145 0 0)`): Primary text.
- **Ink Quiet** (`oklch(0.556 0 0)`): Secondary/helper text (`muted-foreground`).
- **Rule Line** (`oklch(0.922 0 0)`): Borders, inputs, dividers.
- **Focus Ring** (`oklch(0.708 0 0)`): Focus-visible rings.
- **Sidebar Paper** (`oklch(0.985 0 0)`): Slightly off-white sidebar rail for tonal separation from content.

### Semantic

- **Alert Coral** (`oklch(0.577 0.245 27.325)`): Destructive and error. Prefer soft fill + coral text for buttons (`destructive/10` pattern), not solid red blocks by default.

### Dark (first-class)

- Background → ink body; cards/popovers step up to `oklch(0.205 0 0)`.
- Borders go translucent white (`oklch(1 0 0 / 10%)`).
- Sidebar primary in dark gains a **cool violet-blue** (`oklch(0.488 0.243 264.376)`) — document as current token behavior; prefer not spreading this hue into marketing unless intentional.

### Marketing-only wash

- **Cool Halo** (`oklch(0.95 0.02 250)` light / `oklch(0.25 0.04 250)` dark): Soft top radial on landing only. Do not place under dense data tables.

### Named Rules

**The One Ink Rule.** Brand primary is near-black (or near-white in dark). Do not introduce a saturated brand purple/blue as the default primary without an explicit redesign of this file.

**The Quiet Accent Rule.** Secondary/accent fills stay mist-gray. Color beyond ink is reserved for **semantic state** (destructive, and future due/success chips when implemented) — rarity is the point.

**The Marketing Halo Rule.** Radial cool wash is a landing/auth device only, never a global app background.

## Typography

**Display / Body Font:** Geist (with `ui-sans-serif, system-ui, sans-serif`)  
**Mono Font:** Geist Mono (with `ui-monospace, SFMono-Regular, monospace`)

**Character:** One highly legible sans for product and marketing. No display serif. Mono is for money figures, last-four digits, IDs, and technical labels — not decorative body.

### Hierarchy

- **Display** (600, clamp ~2.25–3.75rem, tight tracking): Landing heroes only (`text-4xl` → `md:text-6xl`).
- **Headline** (600, ~1.5rem / `text-2xl`): Auth titles, page titles in app.
- **Title** (500–600, ~1.125rem): Card titles, section heads, nav emphasis.
- **Body** (400, 1rem): Default UI copy.
- **Body large** (400, 1.125rem / `text-lg`): Marketing supporting paragraphs (~65ch max preferred).
- **Label** (500, 0.875rem, wide tracking ~0.2em, often uppercase): Eyebrow labels (“Credit cards · Lending ledger · India”).
- **Mono / data** (400, 0.875–1rem): INR amounts, utilization %, last4, timestamps when tabular alignment matters.

### Named Rules

**The Single Family Rule.** Stay on Geist for UI. Do not pair a decorative serif for “premium finance” aesthetics.

**The Money is Mono Rule.** Prefer mono (or tabular-nums) for monetary amounts and fixed-width codes so columns scan like a ledger.

## Layout

- **Container:** Marketing content ~`max-w-6xl` (72rem) with horizontal padding `px-6` (1.5rem).
- **Rhythm:** Vertical stacks use Tailwind scale gaps (`gap-3`–`gap-4` for clusters; `mt-6`–`mt-16` for section separation on landing).
- **Density:** App surfaces (per PRODUCT / shape brief) target **power-user density** — compact controls (default button height 2rem / 32px), tight tables, sidebar + main. Marketing can open spacing.
- **App shell (built):** Collapsible sidebar + top bar; content region full remaining width. Desktop-first; collapse sidebar and stack KPIs on narrow widths.
- **Responsive:** Prefer structural collapse (columns → stack, table scroll) over fluid display type in the app. Landing display may use stepped Tailwind sizes.

### Named Rules

**The Shelf Density Rule.** Authenticated views prioritize scannable information per viewport over hero whitespace.

## Elevation & Depth

**Soft card lift everywhere** (confirmed): resting cards and auth panels use a light ambient shadow (`shadow-sm`) plus border. Surfaces are not purely flat; lift signals “panel” without heavy Material elevation stacks.

### Shadow Vocabulary

- **Panel lift** (`box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05)` ≈ Tailwind `shadow-sm`): Cards, login panel, feature tiles.
- **Backdrop** (`backdrop-blur-sm` + `bg-card/80`): Optional glass on marketing feature tiles only.

No multi-level shadow ramp is defined yet. Avoid large soft glows and colored shadows.

### Named Rules

**The Soft Shelf Rule.** Default panels lift lightly. Reserve stronger elevation for true overlays (dialogs, popovers) when those components land.

## Shapes

Base radius token `--radius: 0.625rem` (10px). Derived: sm ~6px, md ~8px, lg 10px, xl ~14px, 2xl ~18px.

- **Controls (buttons, inputs):** `rounded-lg` (~10px).
- **Cards / feature tiles:** `rounded-xl` (~14px).
- **Auth panel:** `rounded-2xl` (~18px).
- **Brand mark:** `rounded-lg` square tile with monogram “FB”.

Borders are 1px `border-border` hairlines; do not use heavy 2px chrome.

### Named Rules

**The Gentle Corner Rule.** Stay in the 6–18px radius band. No full-pill buttons for primary app actions; no sharp 0px industrial corners.

## Components

### Buttons

Compact, medium-weight, no uppercase forced.

- **Shape:** Gently curved (`rounded-lg` / ~10px).
- **Primary:** Ledger Ink fill, inverse text; hover softens to ~80% primary. Heights: default 32px, sm 28px, lg 36px.
- **Outline:** Background + border; hover mist fill.
- **Ghost:** No border; hover mist.
- **Destructive:** Soft coral wash + coral text (not solid red blocks).
- **Focus:** Ring + border ring (`ring-3` / `ring-ring/50` pattern).
- **Disabled:** 50% opacity, non-interactive.
- **Active press:** Subtle 1px translateY on non-menu buttons.

### Cards / Containers

- **Corner:** `rounded-xl` to `rounded-2xl`.
- **Background:** `card` with optional 80% + blur on marketing.
- **Border + soft lift:** Always pair border with `shadow-sm` for shelf panels.
- **Padding:** ~1.25rem (`p-5`) typical; auth ~2rem (`p-8`).

### Brand mark

- Square tile (`size-8` / `size-10`), primary fill, inverse monogram, `rounded-lg`, semibold small type.

### Inputs / Fields (token-ready; few built yet)

- Use `input` / `border` / `ring` tokens; radius matches controls (`rounded-lg`).
- Focus via ring; invalid via destructive border/ring (button pattern already encodes this).

### Navigation

- **Marketing header:** Horizontal, max-w-6xl, wordmark + outline Sign in.
- **App shell:** Sidebar with muted rail (`sidebar` tokens), active item via `sidebar-primary` / accent fill; top bar for notifications and user.

### Status chips (intended for dashboard; not yet built)

When implemented: small rounded-lg / rounded-md pills for due-soon (amber TBD), overdue (destructive), healthy/available (muted or future success green). Prefer semantic tokens over ad-hoc hex.

## Do's and Don'ts

### Do:

- **Do** keep app UI dense, scannable, and monochrome-first — Ledger Shelf, not lifestyle fintech.
- **Do** use Geist + soft card lift + hairline borders as the default panel language.
- **Do** format money as INR (`en-IN`) and time in IST at the presentation layer; store paise integers.
- **Do** support dark mode with the existing `.dark` token set.
- **Do** use mono/tabular treatment for amounts, last4, and IDs.
- **Do** reserve marketing halo and open whitespace for landing/auth only.

### Don't:

- **Don't** introduce purple-to-blue gradients, neon glows, or “AI SaaS” glassmorphism as the product identity.
- **Don't** nest cards inside cards or wrap every list row in a heavy elevated tile.
- **Don't** use display serifs, Inter-as-brand, or random third typefaces without updating this file.
- **Don't** store or display full card numbers; last4 + metadata only.
- **Don't** invent testimonials, bank partnerships, or performance claims in UI copy.
- **Don't** make primary actions solid coral; coral is for danger, not brand CTA.
- **Don't** ship bounce/elastic motion; keep state transitions ~150–250ms when motion is added.
