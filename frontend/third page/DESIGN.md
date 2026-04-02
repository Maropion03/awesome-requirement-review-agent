# Design System Specification: Editorial Precision

## 1. Overview & Creative North Star: "The Digital Atelier"

This design system is built upon the concept of **"The Digital Atelier."** It rejects the industrial, "boxy" nature of traditional SaaS dashboards in favor of a bespoke, editorial workspace. The goal is to make the user feel like they are interacting with a high-end publication or a custom-built physical studio rather than a generic database.

### The Creative North Star
*   **Intentional Asymmetry:** Break the rigid 12-column grid. Use whitespace as a structural element. A dashboard shouldn't be a wall of cards; it should be a composition where the most important metric has "gallery-level" breathing room.
*   **Tactile Sophistication:** We treat pixels like premium materials. Surfaces don't just "exist"; they are layered, frosted, or stacked to create a sense of physical weight and luxury.
*   **Editorial Authority:** Typography is used to guide the eye through scale and weight contrast, not just color. We use `Satoshi-Variable` for a sense of custom craftsmanship and `Inter` for hyper-legible utility.

---

## 2. Color & Surface Philosophy

The palette is anchored in warm, ivory-leaning neutrals to avoid the clinical "coldness" of pure white or standard gray dashboards.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined by:
1.  **Tonal Transitions:** Placing a `surface_container_low` card on a `background` base.
2.  **Negative Space:** Using the `Spacing Scale (8, 10, or 12)` to create a natural visual break.
3.  **Soft Shadows:** Letting the `ambient shadow` define the edge of a container.

### Surface Hierarchy & Nesting
Treat the UI as a series of nested, physical layers:
*   **Base Layer (`background` - #fef8f1):** The "canvas."
*   **Secondary Layer (`surface_container_low` - #f8f3ec):** Used for sidebar navigation or secondary utility panels.
*   **Action Layer (`surface_container_lowest` - #ffffff):** Use pure white only for primary content cards to make them "pop" against the beige base.

### The Glass & Gradient Rule
To elevate the experience, use **Glassmorphism-Lite** for floating elements (modals, dropdowns, or pinned headers). 
*   **Effect:** Apply `surface_container_lowest` at 80% opacity with a `backdrop-blur` of 20px.
*   **Signature Textures:** Use a subtle linear gradient for primary buttons, transitioning from `primary` (#3a2e47) to `primary_container` (#51445f). This adds a three-dimensional "soul" to the action.

---

## 3. Typography

The typographic system balances the character of **Satoshi** with the functional clarity of **Inter**.

| Level | Token | Font | Weight | Size | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` | Satoshi | 700 (97%) | 3.5rem | Hero metrics, high-impact data points. |
| **Headline**| `headline-md`| Satoshi | 600 | 1.75rem | Page titles and primary section headers. |
| **Title**   | `title-md`   | Inter | 600 | 1.125rem | Card headings, navigation categories. |
| **Body**    | `body-md`    | Inter | 400 | 0.875rem | General content, descriptions. |
| **Label**   | `label-sm`   | Inter | 500 | 0.6875rem| Micro-copy, metadata, button text. |

**Editorial Note:** Use tight letter-spacing (-0.02em) on Display and Headline tokens to give them a "printed" feel.

---

## 4. Elevation & Depth

We move away from the "flat" web. Depth is achieved through **Tonal Layering**.

*   **The Layering Principle:** To create a "lifted" card, place a `surface_container_lowest` (#ffffff) element on top of `surface_container_low` (#f8f3ec). The 1% shift in warmth creates a natural, sophisticated edge.
*   **Ambient Shadows:** For floating elements (e.g., Modals), use a "Whisper Shadow":
    *   `box-shadow: 0 12px 40px rgba(31, 24, 23, 0.06);` (using the `on_background` tint).
*   **The "Ghost Border":** If accessibility requires a border, use `outline_variant` at **15% opacity**. Never use 100% opacity borders.
*   **Roundedness:** Stick to `xl (1.5rem)` for large layout containers and `lg (1.0rem)` for inner cards. This "soft-on-softer" nesting reinforces the premium feel.

---

## 5. Components

### Primary Buttons
*   **Style:** `primary` (#3a2e47) background with a subtle gradient to `primary_container`.
*   **Corner Radius:** `full (9999px)` for a modern, pill-shaped look that contrasts against the rectangular layout.
*   **State:** On hover, shift the gradient to be slightly brighter using `primary_fixed_dim`.

### Cards & Lists
*   **Constraint:** Zero dividers. Separate list items using `spacing (3)` and a subtle `surface_container_high` hover state background.
*   **Nesting:** All cards should use the `lg` (1.0rem) radius. Content inside cards should be padded with `spacing (5)`.

### Signature Inputs
*   **Base:** `surface_container_lowest` with a "Ghost Border."
*   **Focus State:** Instead of a thick border, use a 2px outer glow of `primary_fixed` (#eedcfd) and shift the background to pure ivory.

### Status Indicators (Editorial Style)
Instead of standard "dots," use high-contrast **Chips**:
*   **Pass:** `tertiary_fixed_dim` (#f4bd69) text on a very soft ivory base. (Note: We use the Amber/Gold palette for "Pass" to maintain the warm aesthetic, using Red `error` only for Reject).
*   **Reject:** `on_error_container` text on `error_container`.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use asymmetrical layouts (e.g., a wide 2/3 column for a graph and a narrow 1/3 column for text).
*   **Do** use "Editorial Spacing"—if you think there is enough whitespace, add 20% more.
*   **Do** use backdrop blurs on any element that overlays content.
*   **Do** mix weights of Satoshi for emphasis in data visualizations.

### Don’t
*   **Don’t** use black (#000000). Use `on_background` (#1d1b17) for all text to keep the warmth.
*   **Don’t** use 1px dividers to separate content blocks. Use a change in surface tone.
*   **Don’t** use "default" blue for links. Use the brand `primary` or `tertiary` (#482e00).
*   **Don’t** crowd the edges. Every container should have significant internal padding (`spacing 5` or `6`).