# Messaging questions

- topic: messaging_questions
- role: java_backend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://docs.spring.io/spring-integration/reference/
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Когда выбрать messaging вместо синхронного HTTP-вызова?
2. Какие преимущества дают очереди и брокеры?
3. Какие trade-offs появляются в асинхронной системе?
4. Как retries и duplicate messages влияют на корректность?
5. Что такое eventual consistency на практическом языке продукта?
6. Чем отличается "сообщение принято" от "бизнес-работа завершена"?
7. Какие типы сбоев сложнее дебажить в асинхронных системах?

## Follow-up идеи

- Что делать, если consumer медленный или временно недоступен?
- Где нужна idempotency?
- Как бы ты наблюдал и трассировал такой workflow?

## Retrieval tags

`messaging`, `queues`, `brokers`, `async systems`, `eventual consistency`, `duplicates`, `idempotency`
