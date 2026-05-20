# REST API questions

- topic: rest_api_questions
- role: java_backend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://developer.mozilla.org/en-US/docs/Web/HTTP
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Как решить, нужен ли endpoint-у `GET`, `POST`, `PUT`, `PATCH` или `DELETE`?
2. Что делает API предсказуемым для клиентов?
3. Как выбирать между `200`, `201`, `204`, `400`, `404`, `409` в типичных backend-сценариях?
4. Что такое idempotency и почему она важна?
5. Как представлять validation errors в API?
6. Какие признаки говорят, что controller делает слишком много?
7. Как спроектировать endpoint, зависящий от медленного downstream-сервиса?

## Follow-up идеи

- Какого retry behavior ты ожидаешь от клиента?
- Какое state transition реально делает endpoint?
- Какие failure modes API должен явно показать?

## Retrieval tags

`rest api`, `http methods`, `status codes`, `idempotency`, `validation`, `controller`, `downstream service`
