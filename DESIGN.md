# sourcetrail design system

Read this before changing the site's UI. Do not introduce a new direction; extend this one. English only. Values below come from `docs/index.html` as of this commit.

## Concept

An evidence trail: a claim is traced by a dotted line to the exact files and places that support or contradict it.

Theme: light.

## Color tokens

| Token | Value | Role |
|---|---|---|
| `--bg` | `#f4ecd8` | page background |
| `--fg` | `#2b2218` | body text |
| `--mut` | `#75664f` | secondary text (AA on bg) |
| `--card` | `#fbf6e9` | card and panel surface |
| `--line` | `#d8c9a6` | borders and dividers |
| `--acc` | `#8a3b12` | primary action, links, focus ring |
| `--accfg` | `#fff8ec` | text on accent |
| `--code` | `#efe5cb` | code block background |
| `--codefg` | `#2b2218` | code block text |
| `--warn` | `#b5651d` | warning border and limits |

Contrast: every text node on the page is checked against WCAG AA (4.5:1, 3:1 for large text) with a script in the repo owner's QA harness. Keep it passing when you change a color.

## Type

| Token | Stack | Role |
|---|---|---|
| `--arabic` | `'Noto Naskh Arabic',sans-serif` | Arabic font stack |
| `--body` | `'Lora','Noto Naskh Arabic',system-ui,sans-serif` | body font stack |
| `--head` | `'Libre Caslon Text','Noto Naskh Arabic',system-ui,sans-serif` | heading font stack |

Font sizes in use: `.86rem`, `1.5rem`, `1rem`, `.9rem`, `.72rem`, `clamp(2rem,8vw,3rem)`, `1.2rem`, `clamp(2.5rem,8.5vw,4.2rem)`, `1.3rem`, `1.15rem`, `.95rem`.

## Spacing, radius, elevation

- Spacing values in use: `1px`, `2px`, `4px`, `5px`, `6px`, `8px`, `9px`, `10px`, `11px`, `12px`, `14px`, `16px`. Prefer these; do not add new ones.
- Radius: `--r` (2px). Use the token, not literals.
- Elevation: borders only; no shadows.

## Motion

- Durations in use: `.05s`, `.15s`, `.25s`, `.2s`, `.34s`, `.42s`, `.45s`, `.6s`, `1.4s`, `1s`, `2s`.
- Curves: `cubic-bezier(.16,1,.3,1)`, `cubic-bezier(.2,.8,.2,1)`, `cubic-bezier(.22,1.36,.32,1)`.
- Every animation sits behind `prefers-reduced-motion: reduce`, which turns animation and transition off.
- Motion shows state or order. It is never decoration.

## Components and states

- Button `.btn` (filled) and `.btn.alt` (outline): min height 44px, visible `:focus-visible` outline (2px accent), hover and active states.
- Card `.card`, warning card `.card.warn` (left border in `--warn`).
- Language toggle `.langtoggle` with `aria-pressed`.
- Code block `pre`: always LTR, monospace.
- Status words use `.ok b` and `.no b` colors (AA checked).

## RTL rules

- The language toggle sets `dir` and `lang` on `<html>`. Arabic text uses the `--arabic` font and line-height 1.75.
- Use logical CSS (`margin-inline`, `inset-inline-start`, `text-align:start`). No `left` or `right` for layout.
- Letter-spacing is 0 and text-transform none in Arabic.
- Code, terminal output and demo panels stay LTR (`direction:ltr`). Install and demo output stay English.
- Arabic is Egyptian-leaning plain language. Brand names and commands stay Latin.

## Microcopy voice

Plain, specific, honest about limits. Say what it does and what it does not. No hype, no invented numbers.

Examples from the site:

1. Where did I get that number from?
2. Research_Paper.pdf, page 2
3. SUPPORTED does not prove a claim is true.
4. Sources disagree on the number.
5. CONFLICTING

## Do / Don't

| Do | Don't |
|---|---|
| Quote the source sentence | Paraphrase it |
| Show different numbers as different | Hide the disagreement |
| Serif and stamp motifs | Add icon sets |
| Square 2px corners | Rounded pills |
| Say matching is by words, not meaning | Imply understanding |

## Known hard-coded values (should become tokens)

These literal colors appear in the CSS outside `:root`: `#17703f`, `#1f5d36`, `#2e9e5b`, `#a8281b`, `#c0392b`, `#f3c98b`.
Also: status colors in `.ok b` and `.no b`, and several literal pixel sizes in component CSS. Move them into tokens next time that block is touched.
