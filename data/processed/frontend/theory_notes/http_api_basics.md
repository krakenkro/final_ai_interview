# HTTP API basics

- topic: http_api_basics
- role: frontend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://developer.mozilla.org/en-US/docs/Web/HTTP
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

HTTP определяет, как клиент и сервер обмениваются запросами и ответами. Для frontend-интервью это база для разговоров про `fetch`, REST API, ошибки, заголовки, авторизацию, кэширование и CORS.

## Ключевые идеи

1. Request-response:
   клиент отправляет запрос, сервер возвращает ответ.
2. Структура сообщений:
   start line, headers, optional body.
3. Методы:
   `GET`, `POST`, `PUT`, `PATCH`, `DELETE` выражают намерение операции.
4. Статусы:
   `2xx` успех, `3xx` редиректы, `4xx` клиентские ошибки, `5xx` серверные ошибки.
5. `Content-Type` и MIME:
   помогают корректно интерпретировать payload.
6. Веб-контекст:
   важны cookies, caching, auth и cross-origin ограничения.

## Что важно для интервью

- Уметь объяснить различие между `PUT` и `PATCH`.
- Понимать, почему `204`, `400`, `401`, `403`, `404`, `500` несут разный смысл.
- Показать, как HTTP влияет на клиентскую обработку ошибок и retry-логику.

## Сигналы сильного ответа

- Кандидат не ограничивается перечислением методов.
- Объясняет, как headers влияют на поведение клиента.
- Связывает HTTP с реальным API integration flow в приложении.

## Retrieval tags

`http`, `rest`, `methods`, `status codes`, `headers`, `content-type`, `cookies`, `caching`, `cors`
