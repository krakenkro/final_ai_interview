# Caching questions

- topic: caching_questions
- role: java_backend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://docs.spring.io/spring-framework/reference/integration/cache.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Какую проблему решает caching в backend-сервисе?
2. Когда кеш уменьшает latency, а когда создаёт риски корректности?
3. Что такое cache invalidation и почему это сложно?
4. Какие данные плохо подходят для кеширования?
5. Как балансировать stale data и скорость системы?
6. Что может пойти не так, если кеширование добавили слишком рано?
7. Чем отличается кеширование вычисления от кеширования авторитетного бизнес-состояния?

## Follow-up идеи

- Какая гарантия свежести реально нужна продукту?
- Где должен жить кеш: in-memory, app-layer или external store?
- Какому invalidation trigger ты бы доверял?

## Retrieval tags

`caching`, `latency`, `stale data`, `cache invalidation`, `freshness`, `backend performance`
