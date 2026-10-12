---
name: improve-ui
description: Comprehensive UI quality inspection, component refinement, typography auditing, and responsive layout polish. Activate when auditing existing screens, modernizing forms and dashboards, and eliminating visual clutter.
---

# UI Polish & Component Refinement Runbook

## Core Directives
Elevate standard interfaces into polished, professional products. Remove visual debt, align spacing grids, and ensure responsive clarity.

---

## 1. Information Density & Layout Grids
* **Container Bounds**: Use max-width containers (`max-w-7xl` or `max-w-screen-2xl`) with horizontal auto-margins.
* **Component Padding**: Maintain a consistent 4-point/8-point spacing cadence (`gap-4`, `gap-6`, `p-6`).
* **Section Dividers**: Use subtle border dividers (`border-slate-800/80`) rather than heavy solid lines.

---

## 2. Forms & Data Inputs
* **Input Styling**:
  * Dark input surfaces: `bg-slate-900/90` with `border border-slate-800`.
  * Focus states: `focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500`.
  * Padding: `px-4 py-2.5`, `text-xs` or `text-sm`.
* **Action Buttons**:
  * Primary: High-contrast gradient or solid fill with colored drop-shadow.
  * Secondary / Ghost: Translucent slate background with border highlight on hover.
  * Destructive: Rose/crimson border and tint with explicit confirmation triggers.

---

## 3. Empty States & Feedback Loop
* Never display a raw empty space. Always render contextual empty states with:
  1. A muted Lucide icon in a translucent container.
  2. A clear explanation sentence.
  3. A direct call-to-action button (e.g. "+ Add New Record").
