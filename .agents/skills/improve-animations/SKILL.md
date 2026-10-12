---
name: improve-animations
description: Authority on UI motion choreography, physics-based springs, route transitions, and micro-interactions. Activate when adding motion to components, page transitions, loading states, or interactive gestures using Framer Motion or modern CSS.
---

# UI Motion & Animations Playbook

## Motion Principles
Motion must convey causality, state change, and spatial continuity. Never animate for the sake of decoration; every transition should orient the user.

---

## 1. Timing, Curves & Physics

* **Standard Micro-Interaction**: `150ms - 200ms` with `cubic-bezier(0.16, 1, 0.3, 1)` (out-expo).
* **Modal / Dialog Reveal**: `250ms - 320ms` with gentle spring stiffness (`stiffness: 380, damping: 30`).
* **Page / View Transitions**: `200ms - 240ms` with staggered exit and entrance.
* **Layout Shifts**: Use Framer Motion's `layout` and `layoutId` props for shared element transitions.

---

## 2. Framer Motion Implementation Patterns

### A. Shared Element Springs (e.g. Active Navigation Pill)
```tsx
<button className="relative px-4 py-2">
  {isActive && (
    <motion.div
      layoutId="activeNavIndicator"
      className="absolute inset-0 bg-indigo-600 rounded-xl"
      transition={{ type: "spring", stiffness: 380, damping: 30 }}
    />
  )}
  <span className="relative z-10">{label}</span>
</button>
```

### B. Staggered Grid Cascade
```tsx
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] } }
};
```

### C. Route & Tab Blur-Crossfade
```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={activeRouteKey}
    initial={{ opacity: 0, y: 10, filter: "blur(4px)" }}
    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
    exit={{ opacity: 0, y: -10, filter: "blur(4px)" }}
    transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
  >
    {children}
  </motion.div>
</AnimatePresence>
```

---

## 3. Micro-Interaction Rules
* **Buttons**: Use subtle scale responses:
  * `whileHover={{ scale: 1.02 }}`
  * `whileTap={{ scale: 0.98 }}`
* **Card Lift**: Combine a translateY with dynamic border-color illumination on hover:
  * `transform: translateY(-2px);`
  * `box-shadow: 0 16px 36px -10px rgba(79, 70, 229, 0.2);`
* **Accessibility**: Always respect `@media (prefers-reduced-motion: reduce)`.
