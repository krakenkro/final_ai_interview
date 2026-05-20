# SQL questions

- topic: sql_questions
- role: java_backend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: question_bank
- source_url: https://www.postgresql.org/docs/current/indexes.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Основные вопросы

1. Что такое индекс и почему он ускоряет запросы?
2. Почему слишком много индексов вредно?
3. Как понять, какие колонки стоит индексировать?
4. Почему write-heavy таблица требует осторожной стратегии индексации?
5. Как индексы связаны с `WHERE`, `JOIN` и сортировкой?
6. Что проверять, если endpoint тормозит из-за SQL-запроса?

## Follow-up идеи

- Что здесь важнее: чтение или запись?
- Какой query pattern ты оптимизируешь?
- Какой overhead готов принять?

## Retrieval tags

`sql interview`, `indexes`, `query performance`, `reads writes`, `join`, `endpoint latency`
