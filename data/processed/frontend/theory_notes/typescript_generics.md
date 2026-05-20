# TypeScript generics

- topic: typescript_generics
- role: frontend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://www.typescriptlang.org/docs/handbook/2/generics.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

Generics позволяют писать переиспользуемый код без потери информации о типах. Вместо жёстко заданного типа или небезопасного `any` generic-абстракция сохраняет тип данных пользователя через вход, внутреннюю логику и результат.

## Ключевые идеи

1. Generic type parameter:
   это переменная на уровне типов.
2. Базовый смысл:
   функция вроде `identity<Type>(arg: Type): Type` возвращает то же самое знание о типе, которое получила на входе.
3. Inference:
   часто TypeScript сам выводит нужный type argument.
4. Precision:
   generics безопаснее `any`, потому что не теряют связь между входом и выходом.
5. Constraints:
   позволяют ограничить generic допустимыми типами или свойствами.
6. Практический use case:
   typed API helpers, reusable hooks, generic UI components, table/form utilities.

## Что важно для интервью

- Уметь объяснить, почему generic не равен `any`.
- Понимать разницу между generics и union types.
- Уметь привести прикладной пример из React или API-клиента.

## Сигналы сильного ответа

- Кандидат говорит о сохранении type information.
- Понимает, когда нужен constraint.
- Даёт пример реально переиспользуемой абстракции.

## Retrieval tags

`generics`, `type parameter`, `constraints`, `type inference`, `reusable abstractions`, `api helpers`
