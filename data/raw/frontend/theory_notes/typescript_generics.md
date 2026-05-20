# TypeScript Generics

- Topic: TypeScript generics
- Role: Frontend Developer
- Seniority: Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://www.typescriptlang.org/docs/handbook/2/generics.html
- Language: English
- Collected On: 2026-05-10

## Source Summary

The TypeScript generics chapter explains how to build reusable abstractions without losing type information. Instead of hardcoding a concrete type or falling back to `any`, generics let code carry the caller's type information through functions, interfaces, classes, and constrained utilities.

## Key Notes

### Why Generics Exist

- Generics make reusable code type-safe.
- They preserve information about input and output types.
- They are more precise than using `any`.

### Basic Mental Model

- A generic type parameter is a variable that works on types.
- A function like `identity<Type>(arg: Type): Type` captures the caller's type and returns it consistently.
- Type arguments can often be inferred automatically.

### Working with Generic Parameters

- Generic code must treat type parameters safely.
- If a function needs capabilities like `.length`, that capability must be expressed in the type, not assumed.
- Arrays are a common first example because `Type[]` preserves both the element type and known array behavior.

### Generic Types and APIs

- Generics apply to functions, interfaces, classes, and helper utilities.
- They are useful in frontend code for reusable hooks, API wrappers, table components, form utilities, and strongly typed data transforms.

### Constraints

- Constraints restrict which types are allowed.
- This makes generic utilities flexible without becoming unsafe.
- Examples like `Key extends keyof Type` are common in real TypeScript code.

## Interview-Relevant Takeaways

- A strong answer explains that generics preserve caller-specific type information through reusable code.
- Middle-level candidates should distinguish generics from `any` and from unions.
- Good examples include typed API clients, reusable list/table components, and helper functions that keep response types intact.

## Retrieval Keywords

`typescript generics`, `type parameter`, `generic function`, `type inference`, `constraints`, `keyof`, `reusable abstractions`, `type safety`
