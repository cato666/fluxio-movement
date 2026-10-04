---
name: Fluxio Movement
description: Training notebook, guided registration and authorized weekly recap.
colors:
  canvas: "#f8f9f7"
  surface: "#fff"
  soft: "#f0f2ee"
  text: "#0d1f1a"
  muted: "#626e67"
  border: "#e5e9e3"
  brand: "#235d43"
  brand-dark: "#194b34"
  navy: "#102f24"
  lime: "#c8ef70"
  rail-text: "#bdd0c4"
  ok: "#246044"
  ok-bg: "#edf5ef"
  warn: "#825317"
  warn-bg: "#fbf3e5"
  error: "#a3333d"
  error-bg: "#fbedef"
  processing: "#305e83"
  processing-bg: "#e4edf6"
  pending: "#59695e"
  pending-bg: "#edf0ec"
  nav-active: "#244437"
  field-border: "#858b83"
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
    fontSize: "32px"
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
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontSize: "14px"
    fontWeight: 600
  metric:
    fontSize: "28px"
    fontWeight: 600
    letterSpacing: "-.03em"
  training-heading:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: 1.12
  recap-display:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(32px,4vw,48px)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-.035em"
rounded:
  progress: "4px"
  state: "6px"
  control: "12px"
  nav-video: "10px"
  upload: "12px"
  surface: "#fff"
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
  button-training-main:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.navy}"
    rounded: "{rounded.control}"
    height: "48px"
    padding: "10px 18px"
  session:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.showcase}"
    padding: "18px"
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

# Design System: Fluxio Movement

## Overview

**Creative North Star: "Libreta de rendimiento"**

Deep evergreen navigation, lime selection and white work areas frame a shared training workspace. Video, measurements and human feedback carry the hierarchy. Athletes and coaches have equal priority; role navigation follows the existing permissions and routes.

Implemented V2 covers the shared shell, training journal, registration/editing and authorized public weekly recap. Analysis, coach review, marketing and authentication retain incumbent compositions. The user-approved evergreen rail and lime registration/save actions supersede the initial light-rail and evergreen-main-action proposal. Stylesheet order is styles.css, training.css, then visual-v2.css; public recap adds weekly.css last. The approved recomposition adds a structured journal header, WhatsApp feature row, factual weekly activity card, session category badges and date/RPE icons, guided form panels and compact editorial recap. Short control feedback keeps the interface focused on training tasks.

**Key Characteristics:**
- Evergreen shell and lime selection.
- White content surfaces with restrained depth on a neutral canvas.
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

The frontmatter records the incumbent public display, workspace headline, title, subheading, body, label and metric roles, plus the recomposed training heading (44px desktop, 28px through 900px) and recap display. Journal subtitles are 16px desktop and 14px mobile. Public section headings use `clamp(28px,3.3vw,42px)` with tight tracking. Supporting context is 13px; hints and metric labels are 12px. Workspace introductions are 16px. Body paragraphs are bounded to 72ch.

**The Measured Numbers Rule.** Use tabular numerals for measurements, repetition counts, timestamps and prices. Metrics reduce to 25px on narrow screens; the public hero becomes 42px.

## Layout

Above 900px the workspace has a fixed evergreen 208px rail. Main content uses `clamp(24px,3.3vw,56px)` horizontal padding and a 1200px maximum section width. Standard cards use the card spacing token; two-column grids have the grid gap token.

At 1100px and above, upload forms split training fields and file selection into `1fr` and `minmax(280px,.8fr)` columns with a 36px gap. Coach review uses `1.15fr` and `minmax(320px,.85fr)` columns; the video column is sticky 24px from the top and feedback occupies the adjacent column.

At 1050px and below, review rows use smaller thumbnails and wrap their actions; coach and demo grids become two columns. At 900px and below, the rail becomes a normal-flow header with horizontally scrollable role links; main padding is 24px and navigation stays compact.

At 600px and below, workspace padding is 16px, cards use 20px padding, form and content grids become one column, metrics become two columns, and annotation actions wrap. Page actions expand to full width. Body minimum width is 320px.

The public content is bounded to 1104px, with a 1200px header. Existing 960px rules stack public product, role and plan grids and reduce steps to two columns; 600px rules stack steps and features. Public navigation is hidden at 1050px and below. Authentication forms remain bounded to 460px.

## Elevation & Depth

Depth is restrained: borders, tonal fills and dark player areas carry separation, with low ambient shadows for journal and recap session units. The landing showcase and featured plan explicitly remove their former shadows. V2 removes active navigation inset stripes; session options use 0 8px 24px rgba(24,28,25,.10). Shared work cards remain borderless. Journal sessions use a discreet ambient shadow; recap metrics and factual highlight cards use thin borders. Keyboard focus uses a 3px brand outline with a 4px offset, switching to lime within the dark rail.

**The Restrained Depth Rule.** Use tonal fills and whitespace for work areas, low ambient depth for session units, floating-menu depth for options and outlines for focus.

## Shapes

Cards use the surface radius, controls the control radius, state labels the state radius, and videos the navigation/video radius. Upload areas use dashed borders and the upload radius. Timeline and annotation rows are flat, full-width rows with bottom dividers. Preserve the existing identity assets and their proportions; the shell retains its existing inline stroke mark.

## Components

### Buttons
Training register/save actions are lime with navy labels (48px minimum height, hover #e2f5ae); other primary actions are evergreen with white labels; secondary actions are white with a border. Public primary actions pair deep evergreen with lime. Controls have a minimum 44px height; public main calls to action and inputs reach 48px. Fine-pointer hover changes fill and text. Press scales controls to .97 over 120ms with `cubic-bezier(.23,1,.32,1)`; color and border transitions take 150ms. Reduced motion removes scaling and keeps 100ms color feedback.

### Chips and states
Filter chips are bordered and transparent until selected, when they use deep evergreen and lime. Status labels are compact, noninteractive semantic labels with a small current-color dot. They do not inherit the action-control minimum height.

### Cards / Containers
White borderless cards group incumbent task content; recomposed journal and recap units use restrained depth. Success and error cards use their semantic fills and borders. The review player is a dark container; AI observation panels use the public canvas fill. Metrics are divided by thin vertical rules rather than individual raised cards.

### Inputs / Fields
Fields use white fill, the field-border token, 16px text and 12px by 14px padding. Labels precede fields; hints sit below. Textareas resize vertically and start at 112px high. Disabled fields use canvas and muted text. Upload areas keep the native file selector and existing preview behavior.

### Navigation
Desktop active navigation uses lime text on evergreen tonal fill without an inset line; all route links retain their role-aware visibility. Desktop links are at least 44px high. At 600px and below, navigation is a fixed white bottom bar (72px plus safe-area inset), with evergreen text on pale selected fill and persistent labels. Session identity and logout remain visible within the shell.

### Review timeline
Timestamped rows connect comments and repetitions to the video. Selected classification controls use evergreen; discarded repetitions use muted, struck-through text. Seeking highlights the video with a lime outline. Existing JavaScript generates the metric, filter, row and status patterns.

### Implemented training and recap patterns

Training journal and registration are bounded to 1080px. The 44px desktop heading and 16px subtitle form a real header with the lime register action. WhatsApp is a compact bordered feature row with a stroke icon, title, short description and chevron. The weekly card uses three desktop columns (flexible content, 190px activity, 160px detail action); seven factual day marks accompany existing counts, with sharing controls inside the disclosure. Mobile places activity beside the detail action under the snapshot.

Journal days have 32px separation. Session units use 16px corners, 18px padding, 24px gaps and 12px separation; mobile padding/gaps are 12px. Thumbnails are 112px square desktop and 64px by 88px mobile, with 12px corners. Category badges and date/RPE icons support hierarchy. Names/results/notes/metadata use 16/24/14/13px, becoming 14/20/13/12px through 600px. The 44px overflow trigger opens a 208px anchored menu containing existing Edit/Delete actions; Escape closes and restores focus.

Registration is a bordered white panel with 24px desktop and 16px mobile padding. Principal fields use .7fr/1.3fr columns and stack on mobile. Labels are 13px; fields use 16px text, functional field borders, 12px corners and 48px minimum height. A contextual guided banner accompanies actual validation/proposal state. The result area uses a pale tonal fill and a textarea starting at 112px. Optional/media accordions have inline SVG icons. Prescriptions and metric labels wrap without line clamping. Sticky save sits 24px from desktop bottom or above mobile navigation; keyboard-open state makes it static. Mobile journal registration is fixed above bottom navigation with reserved content space.

Public recap remains bounded to 1120px with 32px padding, becoming safe-area-aware 16px mobile padding. Opening columns use 1fr/1.1fr and a 40px gap, stacking through 900px. Its display is clamp(32px,4vw,48px), 1.08 line height and -.035em tracking. Bordered metrics and factual highlight cards precede a compact timeline with date rail, contained photo, result, adaptations and expandable authorized workout. Timeline session names/results are 17/18px desktop and 15/16px mobile. Recognized repeated movements are counted only from explicitly authorized workout text against eight known names; no technique assessment or new training logs are inferred. Photos use contain, 14px featured corners and 12px timeline corners. Empty/no-photo/no-effort states invent no data or imagery; Existing authorized live-week sharing, expiration, revocation and security remain authoritative; snapshot descriptions belong only to historical proposal context.

Journal reveal uses 240ms; week replacement and disclosure content use 180ms with cubic-bezier(.16,1,.3,1). WhatsApp chevron uses 180ms ease-out. Reveals affect opacity and short translation; reduced-motion gates remove these entrances and training control transforms/transitions. Physical-phone keyboard, safe-area and tap validation remains pending.
## Do's and Don'ts

### Do:
- **Do** preserve role-aware routes, forms and task operations.
- **Do** use semantic status labels alongside color.
- **Do** keep measurements tabular and session depth restrained.
- **Do** keep useful role or demo context below the heading.
- **Do** honor reduced motion and visible keyboard focus.

### Don't:
- **Don't** add above-heading kickers or eyebrow labels.
- **Don't** use lime as a substitute for semantic status colors.
- **Don't** add unbounded entrance effects or heavy decorative shadows.
- **Don't** turn existing example pricing or marketing content into new brand promises.

Not canonized: retained marketing eyebrow/glyph details and nominal stronger font weights are incumbent drift outside the implemented V2 examples. Physical-phone validation remains pending.
