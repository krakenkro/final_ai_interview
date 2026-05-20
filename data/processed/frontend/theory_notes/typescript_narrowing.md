# TypeScript narrowing

- topic: typescript_narrowing
- role: frontend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://www.typescriptlang.org/docs/handbook/2/narrowing.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

Narrowing нужен для безопасной работы с union-типами. TypeScript уточняет тип значения, когда код доказывает, что возможна только часть вариантов: через `typeof`, проверки на truthy, `in`, `instanceof`, discriminated unions и анализ control flow.

## Ключевые идеи

1. `typeof`:
   Подходит для примитивов и простых ветвлений.
2. Truthiness:
   Часто используется для nullable и optional значений.
3. `in`:
   Удобен для объектов с разными полями.
4. `instanceof`:
   Работает для классов и конструкторов.
5. Control flow analysis:
   TypeScript учитывает не только условие, но и достижимость кода после `return`, `throw` и ветвлений.
6. Discriminated unions:
   Лучший паттерн для статусов загрузки, результатов API и UI-state машин.
7. `never`:
   Полезен для exhaustiveness checks.

## Что важно для интервью

- Уметь объяснить narrowing на примере реальной задачи, а не только дать определение.
- Понимать, как проектировать unions так, чтобы их было удобно сужать.
- Показывать, почему discriminated unions лучше набора несвязанных optional-полей.

## Сигналы сильного ответа

- Кандидат приводит пример async-state: `idle | loading | success | error`.
- Упоминает exhaustiveness check при `switch`.
- Связывает narrowing с безопасностью UI и API logic.

## Retrieval tags

`narrowing`, `discriminated unions`, `control flow analysis`, `typeof`, `in`, `instanceof`, `never`, `async state`
