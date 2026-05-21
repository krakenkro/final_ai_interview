# EVALS

## Цель
Этот документ фиксирует, как в проекте оценивается качество RAG и quality of evaluation logic для mock-интервью.

На текущем этапе покрыты три направления:
- retrieval eval для RAG
- golden dataset eval для answer evaluator и follow-up decision
- question quality golden dataset для будущего reset question pipeline

Отдельно проведён A/B эксперимент по порогу follow-up decision.

## Артефакты
- Answer-eval golden dataset: [backend/evals/answer_evaluation_golden_dataset.jsonl](/Users/akbota/Desktop/final/backend/evals/answer_evaluation_golden_dataset.jsonl)
- Golden eval runner: [backend/evals/run_golden_eval.py](/Users/akbota/Desktop/final/backend/evals/run_golden_eval.py)
- Golden eval report JSON: [backend/evals/reports/golden_eval_latest.json](/Users/akbota/Desktop/final/backend/evals/reports/golden_eval_latest.json)
- Golden eval report MD: [backend/evals/reports/golden_eval_latest.md](/Users/akbota/Desktop/final/backend/evals/reports/golden_eval_latest.md)
- Question-quality golden dataset: [backend/evals/question_quality_golden_dataset.jsonl](/Users/akbota/Desktop/final/backend/evals/question_quality_golden_dataset.jsonl)
- Question-quality dataset runner: [backend/evals/run_question_quality_eval.py](/Users/akbota/Desktop/final/backend/evals/run_question_quality_eval.py)
- Question-quality report JSON: [backend/evals/reports/question_quality_dataset_latest.json](/Users/akbota/Desktop/final/backend/evals/reports/question_quality_dataset_latest.json)
- Question-quality report MD: [backend/evals/reports/question_quality_dataset_latest.md](/Users/akbota/Desktop/final/backend/evals/reports/question_quality_dataset_latest.md)
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
Текущий golden dataset содержит `18` кейсов:
- `18` для `Frontend Developer`

По типам интервью:
- `Technical Core`: `9`
- `Behavioural`: `6`
- `Mixed`: `3`

По seniority:
- `Junior`: `5`
- `Middle`: `13`

По качеству ответа:
- `strong`: `10`
- `medium`: `4`
- `weak`: `4`

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

## 1.1 Question Quality Golden Dataset

### Что проверяем
Этот dataset не оценивает ответы кандидата. Он фиксирует editorial contract для user-facing вопросов и follow-up'ов:
- вопрос должен звучать как интервьюер
- вопрос должен быть естественным русским spoken prompt
- вопрос не должен быть retrieval chunk или учебным outline
- follow-up должен добавлять новую ось глубины, а не повторять предыдущий вопрос
- нужно отдельно ловить looped phrases, string mashups и смешанный RU/EN tone

### Размер и покрытие
Текущий question-quality dataset содержит `26` кейсов:
- `13` main question cases
- `13` follow-up cases
- только `Frontend Developer`

Покрыты темы:
- `Vue 3 component model`
- `Vue reactivity and refs`
- `Nuxt 3 fundamentals`
- `Nuxt routing and data fetching`
- `TypeScript in frontend apps`
- `API integration and async flows`
- `browser rendering and event loop`
- `performance and optimization basics`
- `resume-based project deep dive`
- `ownership`
- `conflict resolution`
- `prioritization`
- `failure / lessons learned`

Покрыты обязательные negative patterns:
- `phrase_loop`
- `abstract_label`
- `too_long`
- `mixed_ru_en`
- `no_new_axis`
- `string_mashup`

### Команда запуска
```bash
python3 -m backend.evals.run_question_quality_eval
```

### Зачем нужен этот слой
Этот dataset специально добавлен до переписывания knowledge base и question generation:
- сначала фиксируем стандарт хорошего вопроса
- потом переписываем `question_bank` и `followup_bank`
- только затем меняем retrieval и LLM phrasing layer

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
По состоянию на `2026-05-21`:
- `score_range_accuracy`: `88.89%`
- `follow_up_accuracy`: `94.44%`
- `primary_pass_rate`: `88.89%`
- `gap_exact_match_rate`: `88.89%`
- `avg_gap_recall`: `0.9333`
- `avg_gap_precision`: `0.9444`
- `avg_score_distance`: `0.1111`

### Breakdown по ролям
- `Frontend Developer`: `score_range_accuracy 88.89%`, `follow_up_accuracy 94.44%`

### Breakdown по типам интервью
- `Behavioural`: `score_range_accuracy 100.0%`, `follow_up_accuracy 100.0%`
- `Mixed`: `score_range_accuracy 66.67%`, `follow_up_accuracy 66.67%`
- `Technical Core`: `score_range_accuracy 88.89%`, `follow_up_accuracy 100.0%`

### Breakdown по качеству ответа
- `strong`: `100%` по score-range и follow-up
- `weak`: `75%` по score-range, `100%` по follow-up
- `medium`: `75%` по score-range, `75%` по follow-up

### Интерпретация
Текущий evaluator хорошо держится на явных полюсах:
- хорошо распознаёт явно сильные ответы
- уверенно отправляет явно слабые ответы в follow-up

Основная зона ошибки сейчас находится в `mixed`-кейcах и части `medium`-ответов:
- система иногда завышает score, если ответ звучит уверенно, но в нём не хватает итогового результата
- это особенно заметно на вопросах, где кандидат формулирует общий компромисс, но не доводит ответ до измеримого эффекта

### Кейсы, где score пока расходится с human expectation
- `frontend_003`
- `frontend_011`

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
На текущем датасете из `12` кейсов:
- `pass_rate`: `100.0%`
- `topic_hit_rate`: `100.0%`
- `document_type_hit_rate`: `100.0%`
- `backend_expected_rate`: `100.0%`
- `filters_ok_rate`: `100.0%`

Наблюдаемый backend retrieval:
- `jsonl_lexical`

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
- Variant A `<7`: `follow_up_accuracy 94.44%`, `false_negative 1`, `false_positive 0`
- Variant B `<8`: `follow_up_accuracy 94.44%`, `false_negative 1`, `false_positive 0`

### Принятое решение
Победитель: `threshold <7`

Это решение уже принято как новый baseline в [backend/services/evaluator.py](/Users/akbota/Desktop/final/backend/services/evaluator.py), потому что:
- на текущем датасете обе конфигурации дали одинаковые метрики
- в такой ничьей более строгий baseline `<7` проще интерпретировать и легче защищать
- это оставляет пространство для следующего A/B после расширения mixed-case покрытия

## 5. Что ещё можно улучшить
- Добавить вторую линию evals для `final_report` и `coaching quality`
- Проверять `faithfulness` рекомендаций относительно retrieved context
- Расширить golden dataset кейсами с двусмысленными, partially-correct и overconfident ответами
- Добавить отдельный A/B по `reranker vs no reranker`
- Добавить отдельный A/B по `gpt-4.1` vs более дешёвая evaluator-модель
- После data rewrite добавить rule-based runtime eval для question sanitizer и LLM final phrasing

## 6. Итог
На текущем этапе eval coverage уже достаточный для demo и защиты:
- есть frontend-only golden dataset
- есть automated eval runner
- есть минимум две метрики
- есть retrieval eval
- есть A/B эксперимент с зафиксированным решением

При этом остаётся пространство для следующего цикла улучшений, прежде всего в `score calibration` для `mixed`- и `medium`-ответов.
