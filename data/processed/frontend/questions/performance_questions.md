# Frontend performance questions

- topic: performance_questions
- role: frontend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://vuejs.org/guide/best-practices/performance.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-21

## Основные вопросы

1. Что вы проверяете в первую очередь, если после релиза страница стала заметно медленнее?
2. Почему блокировка main thread сразу бьёт по perceived performance?
3. Почему `transform` и `opacity` обычно дешевле для анимаций, чем свойства, влияющие на layout?
4. Когда `requestAnimationFrame()` уместнее, чем `setInterval()`?
5. Как вы определяете, где узкое место: JavaScript, layout, paint или сеть?
6. Какое улучшение вы бы попробовали первым, не уходя в premature optimization?
7. Как SSR, hydration или тяжёлая клиентская логика могут ухудшить производительность Nuxt-страницы?
8. Чем вы подтверждаете, что оптимизация реально помогла пользователям?

## Retrieval tags

`frontend performance`, `layout`, `paint`, `jank`, `requestAnimationFrame`, `main thread`, `hydration`, `nuxt performance`
