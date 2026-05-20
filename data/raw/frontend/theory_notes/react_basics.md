# React Basics

- Topic: React fundamentals
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://react.dev/learn
- Language: English
- Collected On: 2026-05-10

## Source Summary

React Learn introduces the core mental model of React as a UI library built from reusable components. The quick-start material focuses on the concepts that appear in day-to-day frontend work: components, JSX, props, state, event handling, conditional rendering, list rendering, and sharing data between components.

## Key Notes

### Components

- A React app is composed of components.
- Components are JavaScript functions that return markup.
- Component names start with a capital letter.
- Components can be nested to build larger UI trees from smaller pieces.

### JSX

- JSX is a syntax for writing UI markup inside JavaScript.
- JSX is stricter than HTML: tags must be closed and sibling nodes need a shared wrapper.
- JavaScript expressions can be embedded inside JSX with curly braces.

### Rendering Data

- Values from JavaScript can be rendered directly in JSX.
- Expressions can be used in text nodes and attribute values.
- Data usually flows from parent to child via props.

### Conditional and List Rendering

- React uses standard JavaScript control flow for conditions.
- Common patterns include `if`, ternary expressions, and logical `&&`.
- Lists are usually rendered with `Array.map`.
- Stable `key` values are required so React can track list items correctly.

### Interactivity and State

- Event handlers connect user actions to UI updates.
- State is the component's memory and is used for data that changes over time.
- Updating state schedules a re-render so the UI reflects the latest data.

### Sharing Data

- Parent components pass data down to children.
- When multiple components need the same changing data, state should usually live in the closest common parent.
- This pattern is the foundation for "lifting state up".

## Interview-Relevant Takeaways

- Candidates should explain the difference between markup, component logic, props, and state without mixing their responsibilities.
- A strong answer connects React's component model to maintainability, reuse, and predictable data flow.
- Good middle-level answers usually mention why state placement matters and why list keys affect correctness.

## Retrieval Keywords

`react`, `components`, `jsx`, `props`, `state`, `event handling`, `conditional rendering`, `list rendering`, `keys`, `lifting state up`
