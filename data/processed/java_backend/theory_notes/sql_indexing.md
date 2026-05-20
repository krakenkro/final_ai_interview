# SQL indexing

- topic: sql_indexing
- role: java_backend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://www.postgresql.org/docs/current/indexes.html
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

Индексы ускоряют поиск строк и часто критичны для latency backend-эндпоинтов, но за это приходится платить дополнительной стоимостью записей и хранения. Поэтому зрелый ответ про индексы всегда включает trade-off, а не только выгоду.

## Ключевые идеи

1. Индекс ускоряет чтение:
   особенно для частых фильтров и типовых query paths.
2. Индекс не бесплатен:
   увеличивает overhead на `INSERT`, `UPDATE`, `DELETE`.
3. Индексация должна идти от реальных запросов:
   сначала смотрим workload, потом выбираем стратегию.
4. Слишком много индексов:
   могут ухудшить общую производительность системы.

## Что важно для интервью

- Объяснить, почему "добавим индекс" не универсальное решение.
- Понимать связь индексов с `WHERE`, `JOIN`, `ORDER BY`.
- Уметь говорить о read-heavy и write-heavy сценариях.

## Сигналы сильного ответа

- Кандидат обсуждает query pattern.
- Учитывает стоимость записи.
- Связывает индексирование с продуктовой latency и нагрузкой.

## Retrieval tags

`indexes`, `sql performance`, `postgresql`, `where`, `join`, `reads vs writes`, `latency`
