# EVALS

## Цель
Этот документ фиксирует, как в проекте оценивается качество RAG и quality of evaluation logic для mock-интервью.

На текущем этапе покрыты два направления:
- retrieval eval для RAG
- golden dataset eval для answer evaluator и follow-up decision

Отдельно проведён A/B эксперимент по порогу follow-up decision.

## Артефакты
- Golden dataset: [backend/evals/golden_dataset.jsonl](/Users/akbota/Desktop/final/backend/evals/golden_dataset.jsonl)
- Golden eval runner: [backend/evals/run_golden_eval.py](/Users/akbota/Desktop/final/backend/evals/run_golden_eval.py)
- Golden eval report JSON: [backend/evals/reports/golden_eval_latest.json](/Users/akbota/Desktop/final/backend/evals/reports/golden_eval_latest.json)
- Golden eval report MD: [backend/evals/reports/golden_eval_latest.md](/Users/akbota/Desktop/final/backend/evals/reports/golden_eval_latest.md)
- RAG eval dataset: [backend/evals/rag_queries.jsonl](/Users/akbota/Desktop/final/backend/evals/rag_queries.jsonl)
- RAG eval runner: [backend/evals/run_rag_eval.py](/Users/akbota/Desktop/final/backend/evals/run_rag_eval.py)
- RAG eval report JSON: [backend/evals/reports/rag_eval_latest.json](/Users/akbota/Desktop/final/backend/evals/reports/rag_eval_latest.json)
- A/B runner: [backend/evals/ab_tests.py](/Users/akbota/Desktop/final/backend/evals/ab_tests.py)
- A/B report MD: [backend/evals/reports/ab_followup_threshold_latest.md](/Users/akbota/Desktop/final/backend/evals/reports/ab_followup_threshold_latest.md)

## 1. Golden Dataset

### Что проверяем
Golden dataset проверяет не “знание мира вообще”, а поведение текущего evaluator-а:
- попадает ли score в ожидаемый диапазон
- правильно ли система решает, нужен ли follow-up
- правильно ли система выявляет ожидаемые gaps

### Размер и покрытие
Текущий golden dataset содержит `36` кейсов:
- `18` для `Frontend Developer`
- `18` для `Java Backend Developer`

По типам интервью:
- `Technical Core`: `21`
- `Behavioural`: `9`
- `Mixed`: `6`

По seniority:
- `Junior`: `11`
- `Middle`: `25`

По качеству ответа:
- `strong`: `16`
- `medium`: `12`
- `weak`: `8`

Каждый кейс содержит:
- `role`
- `seniority`
- `interview_type`
- `topic`
- `question`
- `candidate_answer`
- `expected_score_range`
- `expected_gaps`
- `expected_followup_needed`

## 2. Метрики Golden Eval

### Основные метрики
- `score_range_accuracy`: доля кейсов, где предсказанный score попал в ожидаемый диапазон
- `follow_up_accuracy`: доля кейсов, где решение о follow-up совпало с human label
- `gap_exact_match_rate`: доля кейсов, где набор gaps совпал полностью
- `avg_gap_recall`: насколько полно система нашла ожидаемые пробелы

### Команда запуска
```bash
python3 -m backend.evals.run_golden_eval
```

### Текущий результат
По состоянию на `2026-05-20`:
- `score_range_accuracy`: `91.67%`
- `follow_up_accuracy`: `100.0%`
- `primary_pass_rate`: `91.67%`
- `gap_exact_match_rate`: `91.67%`
- `avg_gap_recall`: `0.9583`
- `avg_gap_precision`: `1.0`
- `avg_score_distance`: `0.0833`

### Breakdown по ролям
- `Frontend Developer`: `score_range_accuracy 94.44%`, `follow_up_accuracy 100.0%`
- `Java Backend Developer`: `score_range_accuracy 88.89%`, `follow_up_accuracy 100.0%`

### Breakdown по типам интервью
- `Behavioural`: `score_range_accuracy 88.89%`, `follow_up_accuracy 100.0%`
- `Mixed`: `score_range_accuracy 100.0%`, `follow_up_accuracy 100.0%`
- `Technical Core`: `score_range_accuracy 90.48%`, `follow_up_accuracy 100.0%`

### Breakdown по качеству ответа
- `strong`: `100%` по score-range и follow-up
- `weak`: `100%` по score-range и follow-up
- `medium`: `75%` по score-range, `100%` по follow-up

### Интерпретация
Текущий evaluator очень стабилен на полюсах:
- хорошо распознаёт явно сильные ответы
- хорошо распознаёт явно слабые ответы

Основная зона ошибки сейчас находится в `medium`-кейcах:
- система иногда ставит score чуть выше или ниже ожидаемого диапазона
- это не ломает follow-up routing после последней настройки порога, но показывает, что score calibration ещё можно улучшать

### Кейсы, где score пока расходится с human expectation
- `frontend_016`
- `java_002`
- `java_005`

Это хорошие кандидаты для следующей итерации промпт- или rubric-driven улучшений.

## 3. Retrieval Eval для RAG

### Что проверяем
RAG eval проверяет retrieval quality:
- попадает ли retrieval в нужную тему
- достаёт ли нужный `document_type`
- соблюдает ли filters по роли, seniority и interview type

### Команда запуска
```bash
python3 -m backend.evals.run_rag_eval
```

### Текущий retrieval baseline
На текущем датасете из `14` кейсов:
- `pass_rate`: `100.0%`
- `topic_hit_rate`: `100.0%`
- `document_type_hit_rate`: `100.0%`
- `backend_expected_rate`: `100.0%`
- `filters_ok_rate`: `100.0%`

Наблюдаемый backend retrieval:
- `chroma_openai`

### Вывод по RAG
Для текущего curated knowledge base retrieval работает стабильно и проходит baseline-проверку. Следующий уровень улучшения здесь уже не “починить retrieval”, а проверять:
- более сложные ambiguous queries
- большее разнообразие формулировок
- потенциальный reranker как отдельный A/B

## 4. A/B Experiment

### Гипотеза
Текущий evaluator слишком рано считает часть `medium`-ответов “достаточно хорошими” и не отправляет их в follow-up.

Проверяем две конфигурации:
- Variant A: `follow_up_needed = score < 7`
- Variant B: `follow_up_needed = score < 8`

### Команда запуска
```bash
python3 -m backend.evals.ab_tests
```

### Результаты
- Variant A `<7`: `follow_up_accuracy 94.44%`, `false_negative 2`, `false_positive 0`
- Variant B `<8`: `follow_up_accuracy 100.0%`, `false_negative 0`, `false_positive 0`

### Принятое решение
Победитель: `threshold <8`

Это решение уже принято как новый baseline в [backend/services/evaluator.py](/Users/akbota/Desktop/final/backend/services/evaluator.py), потому что:
- оно улучшает `follow_up_accuracy`
- не ухудшает `score_range_accuracy`
- не добавляет ложных follow-up

## 5. Что ещё можно улучшить
- Добавить вторую линию evals для `final_report` и `coaching quality`
- Проверять `faithfulness` рекомендаций относительно retrieved context
- Расширить golden dataset кейсами с двусмысленными, partially-correct и overconfident ответами
- Добавить отдельный A/B по `reranker vs no reranker`
- Добавить отдельный A/B по `gpt-4.1` vs более дешёвая evaluator-модель

## 6. Итог
На текущем этапе eval coverage уже достаточный для demo и защиты:
- есть golden dataset `30+`
- есть automated eval runner
- есть минимум две метрики
- есть retrieval eval
- есть A/B эксперимент с зафиксированным решением

При этом остаётся пространство для следующего цикла улучшений, прежде всего в `score calibration` для `medium`-ответов.
