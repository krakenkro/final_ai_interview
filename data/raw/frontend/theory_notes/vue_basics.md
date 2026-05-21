# Vue Basics

- Topic: Vue 3 component model and reactivity fundamentals
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://vuejs.org/guide/essentials/component-basics.html
- Language: English
- Collected On: 2026-05-21

## Source Summary

Vue's official guide frames the UI as a tree of components that exchange data through `props` and events, while reactivity keeps the view in sync with changing state. The day-to-day core is component responsibility, template bindings, `computed`, `watch`, `ref`, `reactive`, and reusable logic through composables.

## Key Notes

### Component Responsibility

- Components should have a clear UI responsibility.
- A component becomes hard to maintain when it owns too much unrelated state or workflow logic.

### Data Flow

- `props` carry data in.
- Events communicate intent back out.
- Props are read-only from the child component's point of view.

### Reactivity

- `ref` is convenient for single values.
- `reactive` is useful for object-like state.
- `computed` derives state declaratively.
- `watch` is best for side effects, not as a default replacement for `computed`.

### Reuse

- Slots shape component APIs.
- Composables help share stateful logic without forcing a large global abstraction.

## Interview-Relevant Takeaways

- Strong answers explain why responsibility boundaries matter, not only what the API names are.
- Good middle-level answers compare `computed` and `watch`, or `ref` and `reactive`, with concrete UI examples.
- Practical examples usually make the explanation much more believable.

## Retrieval Keywords

`vue`, `components`, `props`, `emits`, `computed`, `watch`, `ref`, `reactive`, `slots`, `composables`
