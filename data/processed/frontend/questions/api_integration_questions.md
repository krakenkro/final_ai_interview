# API integration questions

- topic: api_integration_questions
- role: frontend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Как `fetch()` работает на высоком уровне?
2. Почему `fetch()` резолвится даже при HTTP error status?
3. Как бы ты организовал обработку API-ошибок во frontend-приложении?
4. Какую роль играют `Request` и `Response`?
5. Как CORS и origin rules влияют на интеграцию?
6. Как не допустить UI-хаоса во время ожидания ответа?
7. Какие trade-offs между optimistic UI и ожиданием подтверждения от сервера?
8. Как headers и content types влияют на клиент-серверную интеграцию?

## Follow-up идеи

- Что делать при `401`, `403`, `404`, `500`?
- Что можно ретраить автоматически, а что нет?
- Как представить loading/success/error состояния в UI?

## Retrieval tags

`api integration`, `fetch`, `request`, `response`, `cors`, `error handling`, `headers`, `optimistic ui`
