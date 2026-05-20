# TypeScript Basics

- Topic: TypeScript everyday types and basic type system
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html
- Language: English
- Collected On: 2026-05-10

## Source Summary

The TypeScript handbook section on everyday types introduces the most common building blocks used in production TypeScript code. It explains primitive types, arrays, objects, functions, unions, aliases, interfaces, literals, and how type inference reduces annotation noise.

## Key Notes

### Primitive and Basic Types

- Common primitive types are `string`, `number`, and `boolean`.
- Arrays can be written as `T[]` or `Array<T>`.
- `any` disables useful checking and should be used sparingly.

### Type Annotations and Inference

- Variable annotations come after the variable name.
- TypeScript often infers types automatically from initial values.
- Good code does not require explicit annotations everywhere.

### Functions

- Function parameters and return values can be typed.
- TypeScript checks argument counts and compatibility.
- Function signatures are central in API and component design.

### Object Types

- Object types describe required and optional properties.
- They are common for props, API payloads, configuration objects, and domain models.

### Union Types

- Union types describe values that may be one of several alternatives.
- A value of type `number | string` is not both at once; code must handle valid branches safely.

### Type Aliases and Interfaces

- Type aliases give names to existing types.
- Interfaces are another way to name object shapes.
- Both are important in frontend codebases for props, DTOs, and reusable contracts.

### Literal Types

- Literal types allow APIs to accept only specific values.
- They are useful for controlled modes, variants, and discriminated unions.

## Interview-Relevant Takeaways

- Junior answers should clearly distinguish `any`, unions, optional fields, and inference.
- Middle answers should connect types to API safety, component props, and maintainability.
- Strong answers usually mention that fewer but well-placed annotations are better than noisy typing.

## Retrieval Keywords

`typescript`, `primitives`, `arrays`, `object types`, `functions`, `union types`, `type aliases`, `interfaces`, `literal types`, `type inference`
