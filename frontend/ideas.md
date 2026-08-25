# SiOslo Frontend Design Direction

## Three Candidate Directions

### Theme Name: Midnight Data Observatory
Very dark analytical workspace with luminous violet and cyan signals, designed to make CSV quality and AI-derived insight feel precise, calm, and instrument-like.

**Probability:** 0.07

### Theme Name: Arctic Operations Console
Cool blue-gray operations interface with restrained green status signals, compact information density, and a more utilitarian enterprise tone.

**Probability:** 0.03

### Theme Name: Ink & Signal Editorial Lab
Editorial dark canvas with oversized type, high-contrast cards, and warm paper-like accents that frame analysis as strategic product storytelling.

**Probability:** 0.08

## Chosen Direction: Midnight Data Observatory

### Design Movement
A contemporary fusion of **dark-mode data visualization**, observatory instrumentation, and premium SaaS analytics. The interface should feel like a quiet control room for turning messy sales data into confident product decisions.

### Core Principles
1. **Evidence before ornament.** Every visual accent supports a metric, state, or action.
2. **Layered depth.** Deep navy canvases, translucent panels, fine borders, and controlled blur establish hierarchy without flattening the UI.
3. **Signal colors are semantic.** Violet/indigo indicates active analysis, teal indicates trustworthy health, amber indicates review, and rose indicates errors.
4. **Asymmetrical focus.** Hero copy, upload actions, and insight results use intentional offsets instead of generic centered blocks.

### Color Philosophy
The base is `#0A111E` and `#060D1F`, matching the supplied references and creating a low-distraction environment for dense information. Violet `#A78BFA` and indigo `#5147C8` are used for active paths and AI work, while cyan `#08C5FF` is reserved for energy and highlights. Teal `#3DCBB1` represents data reliability and successful validation. Lavender `#E9D5FF` carries secondary text without reducing contrast. The ownable signature color is **Observatory Violet `#7B3FE8`**, used in gradients, active indicators, and primary CTAs.

### Layout Paradigm
A persistent left navigation and wide working canvas. Landing/upload content uses a hero-to-workbench composition; dashboard pages use a narrow title rail, modular cards, and full-width history rows. Primary actions sit near the dominant content rather than at the bottom of long forms.

### Signature Elements
- A small circular SiOslo mark with a violet-to-cyan orbit motif.
- Dashed CSV drop zones and pill-shaped validation badges from the reference screens.
- Thin data-grid lines and understated blur halos behind important analysis panels.

### Interaction Philosophy
Interactions should confirm that the system has received and understood user input. Buttons compress slightly on press, upload areas brighten on drag-over, health scores animate only when a real response arrives, and unsupported backend features are represented by functional adjacent controls rather than decorative dead ends.

### Animation
Use short, interruptible transitions under 240ms with a strong ease-out. File upload progress uses a restrained horizontal fill; analysis result cards reveal with 40ms staggered opacity/translate transitions; navigation state changes are immediate; loading states use a soft pulse rather than a spinning neon ornament. Respect reduced-motion preferences.

### Typography System
Use **Plus Jakarta Sans** for interface copy and headings, **DM Mono** for filenames, row counts, timestamps, confidence values, and endpoint/state labels. Use **Plaster** only for the compact brand wordmark if the font is available; otherwise use a tracked geometric fallback without replacing the body system. Heading hierarchy is 48/60px on the upload hero, 32/40px for page titles, 16/24px for card titles, and 12–14px for metadata.

### Brand Essence
SiOslo is a local-first market-driven R&D buddy for small F&B and retail teams that turns imperfect sales CSVs into actionable product innovation blueprints. Personality: **precise, inventive, grounded**.

### Brand Voice
Headlines are direct and evidence-led. CTAs describe the next concrete action instead of using generic onboarding filler. Microcopy is calm about uncertainty and makes data quality visible.

Example lines:
- “Upload the evidence. Leave with a product direction.”
- “Your file is readable; 8.4% of rows need review before the blueprint is trusted.”

### Wordmark & Logo
The mark is a compact orbital “S” formed by two offset arcs around a central square data point. The wordmark uses a slightly expanded geometric treatment of `SiOslo`, with the “O” treated as a data ring rather than a normal letter.

### Signature Brand Color
**Observatory Violet — `#7B3FE8`**.

## Implementation Reminders

- Preserve the supplied CSS’s visual language rather than copying absolute Figma coordinates directly; translate those values into a responsive React layout while retaining the same font families, colors, borders, pills, cards, and contrast relationships.
- The backend currently returns the primary analysis response but does not persist `analyses` history. The frontend will expose history methods behind the API client and show a clear empty/error state until corresponding backend read/write endpoints exist.
- No frontend-only rerun action will be provided, matching the requirement that history entries can be opened, filtered, renamed, exported, or deleted but not rerun.
