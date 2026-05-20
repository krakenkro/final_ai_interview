# TypeScript Narrowing

- Topic: Type narrowing and control flow analysis
- Role: Frontend Developer
- Seniority: Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://www.typescriptlang.org/docs/handbook/2/narrowing.html
- Language: English
- Collected On: 2026-05-10

## Source Summary

The narrowing chapter explains how TypeScript refines broader types into more specific ones when code proves that only certain cases are possible. The chapter covers built-in guards, control flow analysis, user-defined predicates, discriminated unions, and exhaustiveness checks.

## Key Notes

### Built-in Narrowing Techniques

- `typeof` guards narrow primitive unions.
- Truthiness checks narrow nullable or optional values.
- Equality checks narrow by comparing compatible branches.
- The `in` operator narrows object unions based on property existence.
- `instanceof` narrows values created by class constructors.

### Control Flow Analysis

- TypeScript tracks reachability through branches and returns.
- A variable can have different narrowed types at different points in the same function.
- Narrowing is not only about the `if` condition itself; it also depends on what code paths remain possible.

### User-Defined Type Predicates

- Custom functions can describe runtime checks in a way TypeScript understands.
- They are useful when domain validation logic is reused across many call sites.

### Discriminated Unions

- A shared literal field can act as a discriminator for safe branching.
- This pattern is especially useful for UI state, async status objects, and API result handling.

### Exhaustiveness

- The `never` type helps verify that all union cases were handled.
- Exhaustiveness checks are useful when reducers, state machines, or planner outputs evolve over time.

## Interview-Relevant Takeaways

- Strong answers explain not only what narrowing is, but why it matters for safe code on top of unions.
- Middle-level candidates should be comfortable with discriminated unions and control-flow-based refinement.
- Good examples include API response handling, form validation, and async request states.

## Retrieval Keywords

`typescript narrowing`, `typeof`, `truthiness`, `equality`, `in operator`, `instanceof`, `control flow analysis`, `type predicates`, `discriminated unions`, `never`
