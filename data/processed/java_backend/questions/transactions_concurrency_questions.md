# Transactions and concurrency questions

- topic: transactions_concurrency_questions
- role: java_backend_developer
- seniority: middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://docs.spring.io/spring-framework/reference/
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Что такое транзакция и зачем backend-сервису нужны transaction boundaries?
2. Какие проблемы возникают, если часть многошаговой операции выполнилась, а часть нет?
3. Как объяснить isolation issues на примере API?
4. Когда concurrency bugs появляются даже в "правильной" бизнес-логике?
5. Чем thread safety в памяти отличается от консистентности в базе?
6. Как duplicate requests или retries могут ломать корректность?

## Follow-up идеи

- Какой ресурс тут общий?
- Какая гарантия консистентности нужна?
- Решение должно жить в коде, в БД или в обоих слоях?

## Retrieval tags

`transactions`, `concurrency`, `consistency`, `thread safety`, `duplicate requests`, `backend correctness`
