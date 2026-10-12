---
name: antigravity-design-expert
description: Expert design system and aesthetic authority for layered glassmorphism, depth, spatial hierarchy, dark-mode luminosity, and modern SaaS interfaces. Activate when designing or refining UI layouts, surfaces, visual contrast, and card architectures.
---

# Antigravity Design Expert

## Core Philosophy
Craft interfaces that feel tangible, premium, and spatially coherent. Avoid flat, uninspired gray blocks in favor of multi-layered depth, subtle light physics, and refined typography.

---

## 1. Layered Glassmorphism & Surface Elevation

### Depth Stacking Order (Z-Index & Opacity)
* **Canvas Ground (Z-0)**: Deep obsidian/slate base (`#020617` / `#090d16`).
* **Subtle Ambient Radiance (Background)**: Low-opacity blurred radial gradients (`blur-3xl`, 10-20% opacity) positioned behind focal areas.
* **Structural Panels (Z-10)**: 
  * Background: `linear-gradient(135deg, rgba(15, 23, 42, 0.75), rgba(30, 41, 59, 0.45))`
  * Border: `1px solid rgba(255, 255, 255, 0.08)`
  * Blur: `backdrop-filter: blur(16px)`
* **Floating Cards (Z-20)**:
  * Background: `linear-gradient(145deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8))`
  * Border: `1px solid rgba(255, 255, 255, 0.06)`
  * Box Shadow: `0 10px 30px -10px rgba(0, 0, 0, 0.5)`
* **Interactive Elements (Modals / Popovers / Tooltips, Z-50+)**: High-contrast, sharp border highlights with deep drop shadows (`shadow-2xl`).

---

## 2. Spatial Hierarchy & Visual Weight

1. **Heading Scaling**:
   * Hero Metric: `text-3xl` to `text-4xl`, `font-extrabold`, `tracking-tight`.
   * Section Header: `text-lg` to `text-xl`, `font-bold`.
   * Label / Metric Subtext: `text-[10px]` to `text-xs`, `font-bold`, uppercase `tracking-wider`.
2. **Padding Cadence**:
   * Containers: `p-6 md:p-8`.
   * Cards: `p-5 md:p-6`.
   * Micro-controls / Pills: `px-3 py-1.5`.
3. **Corner Radii Consistency**:
   * Global Panels: `rounded-2xl` (16px).
   * Cards & Modules: `rounded-xl` to `rounded-2xl` (12px - 16px).
   * Buttons & Form Inputs: `rounded-xl` (10px - 12px).
   * Badges & Status Pills: `rounded-full` (9999px).

---

## 3. Luminosity & Accent Color Theory

* **Primary Action**: Electric Indigo / Violet (`#6366f1` / `#7c3aed`).
* **Success / Approval**: Emerald (`#10b981` / `#059669`) with subtle green glow.
* **Alert / Escalation**: Rose (`#f43f5e` / `#e11d48`) with translucent crimson backgrounds.
* **Warning / 30-Day Checkpoints**: Amber (`#f59e0b` / `#d97706`).
* **Glow Accents**: Use soft box-shadows rather than intense neon (`box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.35)`).

---

## 4. Implementation Checklist
- [ ] Ensure all frosted panels define `-webkit-backdrop-filter` alongside standard `backdrop-filter`.
- [ ] Provide 1px semi-transparent borders (`rgba(255, 255, 255, 0.06)`) on all cards to maintain edge sharpness against dark canvases.
- [ ] Use SVG icons (e.g. Lucide) with consistent stroke widths (`1.75px` or `2px`) instead of emojis or mismatched icon fonts.
- [ ] Test layout legibility on both low-brightness monitors and high-DPI displays.
