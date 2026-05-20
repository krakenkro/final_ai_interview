# HTTP REST basics

- topic: http_rest_basics
- role: java_backend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://developer.mozilla.org/en-US/docs/Web/HTTP
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

Backend API-дизайн опирается на HTTP-семантику: методы, статус-коды, headers, payload contracts и idempotency. Хороший backend-разработчик должен уметь перевести бизнес-операцию в понятное API-поведение.

## Ключевые идеи

1. Request-response:
   клиент делает запрос, сервер формирует ответ и контракт ошибки/успеха.
2. Методы:
   `GET`, `POST`, `PUT`, `PATCH`, `DELETE` отражают смысл операции.
3. Статусы:
   важны для предсказуемой реакции клиента и диагностики.
4. Headers:
   несут metadata про типы данных, auth, caching и negotiation.
5. Idempotency:
   влияет на retries и устойчивость распределённых систем.

## Что важно для интервью

- Уметь выбрать правильный метод под сценарий.
- Понимать, чем `PUT` отличается от `PATCH`.
- Уметь связать статус-коды с контрактом API, а не с личными предпочтениями.

## Сигналы сильного ответа

- Кандидат обсуждает не только happy path, но и ошибки.
- Говорит про ясность контрактов и поведение клиента.
- Связывает HTTP-семантику с backend reliability.

## Retrieval tags

`http`, `rest`, `idempotency`, `status codes`, `api contract`, `headers`, `backend design`
