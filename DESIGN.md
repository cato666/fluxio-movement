---
name: Movement Coach AI
description: Shared training workspace for athletes and coaches.
colors:
  canvas: "#f1f4f1"
  surface: "#fff"
  soft: "#e6eee8"
  text: "#182c24"
  muted: "#5a6961"
  border: "#d8e1da"
  brand: "#235d43"
  brand-dark: "#16452f"
  navy: "#102f24"
  lime: "#d5ef87"
  rail-text: "#bdd0c4"
  ok: "#246044"
  ok-bg: "#e5f2e9"
  warn: "#825317"
  warn-bg: "#faf0db"
  error: "#a3333d"
  error-bg: "#fbe9e9"
  processing: "#305e83"
  processing-bg: "#e4edf6"
  pending: "#59695e"
  pending-bg: "#edf0ec"
  nav-active: "#244437"
  field-border: "#bbcbbf"
  public-canvas: "#f7f9f4"
  public-alt: "#e8efe3"
typography:
  display:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(40px,5.7vw,72px)"
    fontWeight: 600
    lineHeight: 1.06
    letterSpacing: "-.04em"
  headline:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(28px,3vw,40px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-.035em"
  title:
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-.025em"
  subheading:
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-.015em"
  body:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontSize: "14px"
    fontWeight: 600
  metric:
    fontSize: "28px"
    fontWeight: 600
    letterSpacing: "-.03em"
rounded:
  progress: "4px"
  state: "6px"
  control: "9px"
  nav-video: "10px"
  upload: "12px"
  surface: "14px"
  showcase: "16px"
spacing:
  xs: "6px"
  sm: "8px"
  compact: "12px"
  md: "16px"
  grid: "20px"
  lg: "24px"
  card: "26px"
  xl: "32px"
  section: "48px"
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "{colors.brand-dark}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.surface}"
    padding: "26px"
  filter-active:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.lime}"
    rounded: "{rounded.control}"
  state-completed:
    backgroundColor: "{colors.ok-bg}"
    textColor: "{colors.ok}"
    rounded: "{rounded.state}"
    padding: "5px 10px"
  navigation-active:
    backgroundColor: "{colors.nav-active}"
    textColor: "{colors.lime}"
    rounded: "{rounded.nav-video}"
    padding: "12px 16px"
---

# Design System: Movement Coach AI

## Overview

**Creative North Star: "Team identity graphics"**

Deep evergreen navigation, lime selection and white work areas frame a shared training workspace. Video, measurements and human feedback carry the hierarchy. Athletes and coaches have equal priority; role navigation follows the existing permissions and routes.

The public landing and authentication use the same identity. Restrained typography, flat surfaces and short control feedback keep the interface focused on training tasks.

**Key Characteristics:**
- Evergreen shell and lime selection.
- Flat white work areas on a pale green-gray canvas.
- Local Inter and tabular measurements.
- Responsive role navigation and video review.

## Colors

### Primary
Evergreen `brand` identifies actions, links and movement context; `brand-dark` is the fine-pointer hover state. Deep evergreen `navy` anchors navigation and the review player.

### Secondary
Lime marks selected navigation, selected filters, public calls to action and video seek focus. It is a selection signal, not a success color.

### Neutral
Canvas, white surface, soft fill, text, muted text and border tokens separate work areas without decorative depth. Public canvas and alternate fill extend this material to the landing page. Rail text supports legibility inside the dark shell.

Success, warning and error each pair a readable foreground with a pale background. Processing and in-review share blue; pending uses a neutral green-gray. Every state retains a text label.

**The State Meaning Rule.** Keep status semantics separate from lime selection and retain the visible status label.

## Typography

Inter is served locally as 400 and 600 files, with UI sans-serif fallbacks. The 600 file is declared for weights 600–900; existing stronger landing declarations resolve to that local face.

The frontmatter records the public display, workspace headline, title, subheading, body, label and metric roles. Public section headings use `clamp(28px,3.3vw,42px)` with tight tracking. Supporting context is 13px; hints and metric labels are 12px. Workspace introductions are 16px. Body paragraphs are bounded to 72ch.

**The Measured Numbers Rule.** Use tabular numerals for measurements, repetition counts, timestamps and prices. Metrics reduce to 25px on narrow screens; the public hero becomes 42px.

## Layout

Above 900px the workspace has a fixed 232px rail. Main content uses `clamp(24px,3.3vw,56px)` horizontal padding and a 1200px maximum section width. Standard cards use the card spacing token; two-column grids have the grid gap token.

At 1100px and above, upload forms split training fields and file selection into `1fr` and `minmax(280px,.8fr)` columns with a 36px gap. Coach review uses `1.15fr` and `minmax(320px,.85fr)` columns; the video column is sticky 24px from the top and feedback occupies the adjacent column.

At 1050px and below, review rows use smaller thumbnails and wrap their actions; coach and demo grids become two columns. At 900px and below, the rail becomes a normal-flow header with horizontally scrollable role links; main padding is 24px and selected navigation gets a bottom inset line.

At 600px and below, workspace padding is 16px, cards use 20px padding, form and content grids become one column, metrics become two columns, and annotation actions wrap. Page actions expand to full width. Body minimum width is 320px.

The public content is bounded to 1104px, with a 1200px header. Existing 960px rules stack public product, role and plan grids and reduce steps to two columns; 600px rules stack steps and features. Public navigation is hidden at 1050px and below. Authentication forms remain bounded to 460px.

## Elevation & Depth

Surfaces are flat: borders, tonal fills and dark player areas carry separation. The landing showcase and featured plan explicitly remove their former shadows. The only recurring shadow is the lime inset selection line: 3px at the desktop navigation edge and 2px at the mobile bottom edge. Keyboard focus uses a 3px brand outline with a 4px offset, switching to lime within the dark rail.

**The Flat Surface Rule.** Use borders and tonal fills for work areas; reserve inset lines and outlines for selection and focus.

## Shapes

Cards use the surface radius, controls the control radius, state labels the state radius, and videos the navigation/video radius. Upload areas use dashed borders and the upload radius. Timeline and annotation rows are flat, full-width rows with bottom dividers. The identity mark is a coherent inline stroke SVG.

## Components

### Buttons
Primary actions are evergreen with white labels; secondary actions are white with a border. Public primary actions pair deep evergreen with lime. Controls have a minimum 44px height; public main calls to action and inputs reach 48px. Fine-pointer hover changes fill and text. Press scales controls to .97 over 120ms with `cubic-bezier(.23,1,.32,1)`; color and border transitions take 150ms. Reduced motion removes scaling and keeps 100ms color feedback.

### Chips and states
Filter chips are bordered and transparent until selected, when they use deep evergreen and lime. Status labels are compact, noninteractive semantic labels with a small current-color dot. They do not inherit the action-control minimum height.

### Cards / Containers
White bordered cards group task content. Success and error cards use their semantic fills and borders. The review player is a dark container; AI observation panels use the public canvas fill. Metrics are divided by thin vertical rules rather than individual raised cards.

### Inputs / Fields
Fields use white fill, the field-border token, 16px text and 12px by 14px padding. Labels precede fields; hints sit below. Textareas resize vertically and start at 112px high. Disabled fields use canvas and muted text. Upload areas keep the native file selector and existing preview behavior.

### Navigation
The active route uses lime text and an inset line; all route links retain their role-aware visibility. Desktop links are 48px high; mobile links are at least 44px and scroll horizontally. Session identity and logout remain visible within the shell.

### Review timeline
Timestamped rows connect comments and repetitions to the video. Selected classification controls use evergreen; discarded repetitions use muted, struck-through text. Seeking highlights the video with a lime outline. Existing JavaScript generates the metric, filter, row and status patterns.

## Do's and Don'ts

### Do:
- **Do** preserve role-aware routes, forms and task operations.
- **Do** use semantic status labels alongside color.
- **Do** keep measurements tabular and work surfaces flat.
- **Do** keep useful role or demo context below the heading.
- **Do** honor reduced motion and visible keyboard focus.

### Don't:
- **Don't** add above-heading kickers or eyebrow labels.
- **Don't** use lime as a substitute for semantic status colors.
- **Don't** add page entrance animation or decorative card shadows.
- **Don't** turn existing example pricing or marketing content into new brand promises.
