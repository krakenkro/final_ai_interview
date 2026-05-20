# Frontend performance questions

- topic: performance_questions
- role: frontend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://react.dev/learn/render-and-commit
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Что происходит между React state update и появлением нового UI на экране?
2. Чем React render отличается от DOM commit?
3. Почему re-render не всегда означает реальное обновление DOM?
4. Как бы ты диагностировал страницу, которая лагает при взаимодействиях?
5. Почему блокировка main thread ломает UX даже при "правильной" логике?
6. Что такое critical rendering path и почему он важен?
7. Почему одни CSS-свойства анимировать дороже, чем другие?
8. Почему `transform` и `opacity` обычно предпочтительнее layout-affecting свойств?
9. Когда `requestAnimationFrame()` лучше, чем `setInterval()`?
10. Как связаны responsiveness, frame rate и perceived performance?

## Follow-up идеи

- На какой слой ты бы смотрел первым: JavaScript, layout, paint или network?
- Что бы ты изменил первым без premature optimization?
- Как отличить React bottleneck от browser rendering bottleneck?

## Retrieval tags

`frontend performance`, `render commit`, `critical rendering path`, `layout`, `paint`, `jank`, `requestAnimationFrame`, `main thread`
