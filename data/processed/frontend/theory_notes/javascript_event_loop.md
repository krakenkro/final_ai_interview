# JavaScript event loop

- topic: javascript_event_loop
- role: frontend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://developer.mozilla.org/ru/docs/Web/JavaScript/Reference/Execution_model
- source_language: ru
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

JavaScript в браузере обычно выполняет задачи на одном основном потоке. Пока текущая задача не завершится, следующая из очереди не начнётся. Поэтому длинный синхронный код напрямую бьёт по отзывчивости интерфейса.

## Ключевые идеи

1. Есть стек вызовов:
   туда попадают текущие функции и execution contexts.
2. Есть очередь задач:
   туда попадают новые сообщения, колбэки и отложенные работы.
3. Event loop:
   берёт следующую задачу только когда стек свободен.
4. Run-to-completion:
   текущий обработчик выполняется до конца без прерывания другой задачей.
5. Blocking:
   тяжёлые циклы и CPU-bound работа стопорят ввод, рендер и таймеры.

## Что важно для интервью

- Объяснить, почему `setTimeout(fn, 0)` не выполняется мгновенно.
- Уметь связать event loop с лагами UI.
- Показать, как разбивать тяжёлую работу или выносить её с main thread.

## Сигналы сильного ответа

- Кандидат упоминает стек, очередь и освобождение main thread.
- Связывает модель с реальными проблемами: freeze UI, delayed click handlers, jank.
- Не сводит всё к заученной фразе про "однопоточность" без последствий для продукта.

## Retrieval tags

`event loop`, `call stack`, `queue`, `main thread`, `blocking`, `run to completion`, `setTimeout`
