# Nuxt basics

- topic: nuxt_basics
- role: frontend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://nuxt.com/docs/getting-started/views
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-21

## Краткое резюме

Nuxt расширяет Vue file-based routing, вариантами рендеринга и встроенными сценариями загрузки данных. Для интервью важнее всего понимать маршруты, SSR/CSR/SSG, `useFetch`, `useAsyncData`, middleware, hydration и границу между серверным и браузерным кодом.

## Ключевые идеи

1. Маршруты:
   файлы страниц превращаются в маршруты и влияют на архитектуру фич.
2. Стратегия рендеринга:
   SSR помогает с первой загрузкой и SEO, CSR проще для сильно интерактивных сценариев, SSG хорош для стабильного контента.
3. Загрузка данных:
   место, где выполняется запрос, влияет на latency, кэширование и отладку.
4. Runtime-ограничения:
   браузерные API нельзя использовать без оглядки на SSR.
5. Hydration:
   проблемы начинаются, когда серверная и клиентская версии страницы расходятся.

## Что важно для интервью

- Привязывать выбор SSR/CSR/SSG к продуктовым требованиям, а не только к определениям.
- Понимать, когда повторные запросы и stale data становятся проблемой.
- Уметь объяснить, где middleware оправдан, а где это лишний слой.

## Сигналы сильного ответа

- Кандидат говорит про границу server/client на конкретном сценарии.
- Видит влияние на SEO, first load и сложность реализации.
- Умеет назвать типичный риск: hydration mismatch, duplicate fetch или browser-only API.

## Retrieval tags

`nuxt`, `routing`, `ssr`, `csr`, `ssg`, `useFetch`, `useAsyncData`, `middleware`, `hydration`, `server client boundary`
