# Browser rendering questions

- topic: browser_rendering_questions
- role: frontend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Critical_rendering_path
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Что такое critical rendering path браузера?
2. Как HTML, CSS и JavaScript превращаются в пиксели на экране?
3. Чем отличаются DOM, CSSOM, render tree, layout и paint?
4. Почему одни изменения UI вызывают layout и paint, а другие дешевле?
5. Что такое reflow и почему частые reflow вредят производительности?
6. Как объяснить jank не-фронтенд коллеге?
7. Как React rendering связан с browser rendering?
8. Почему понимание rendering pipeline помогает дебажить slow UI?

## Follow-up идеи

- Какой шаг пайплайна здесь, вероятно, дорогой?
- Бутылочное горлышко в JavaScript, layout, paint или DOM-size?
- Что бы ты померил первым?

## Retrieval tags

`browser rendering`, `critical rendering path`, `dom`, `cssom`, `layout`, `paint`, `reflow`, `jank`
