# TypeScript basics

- topic: typescript_basics
- role: frontend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://www.typescriptlang.org/docs/handbook/2/everyday-types.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

TypeScript добавляет поверх JavaScript статическую систему типов, которая помогает заранее ловить ошибки в функциях, объектах, API-контрактах и props компонентов. Для повседневной разработки особенно важны базовые типы, unions, object types, functions, interfaces и type inference.

## Ключевые идеи

1. Базовые типы:
   `string`, `number`, `boolean`, массивы, объекты.
2. Type inference:
   TypeScript часто сам выводит тип, поэтому не нужно размечать всё вручную.
3. Функции:
   Типизируются параметры и возвращаемое значение.
4. Object types:
   Описывают форму данных, включая optional-поля.
5. Union types:
   Позволяют выразить несколько допустимых вариантов значения.
6. Type aliases и interfaces:
   Нужны для переиспользуемых контрактов.
7. Literal types:
   Полезны для режимов, вариантов и безопасных API.

## Что важно для интервью

- Уметь объяснить, чем `any` опасен.
- Понимать разницу между `type` и `interface` на практическом уровне.
- Уметь показать, где union помогает описать реальный UI или API.
- Не путать явную аннотацию с type inference.

## Сигналы сильного ответа

- Кандидат приводит примеры типизации props и API responses.
- Понимает, что хороший TypeScript не равен максимальному количеству аннотаций.
- Осознанно говорит про optional fields и ошибки совместимости типов.

## Retrieval tags

`typescript`, `type inference`, `union`, `interface`, `type alias`, `object types`, `props typing`, `api contracts`
