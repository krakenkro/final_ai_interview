# Spring basics

- topic: spring_basics
- role: java_backend_developer
- seniority: junior, middle
- interview_type: technical_core, mixed
- document_type: theory_note
- source_url: https://docs.spring.io/spring-framework/reference/
- source_language: en
- normalized_language: ru
- normalized_on: 2026-05-10

## Краткое резюме

Spring нужен не просто для аннотаций, а для управления зависимостями, слоистой архитектуры, транзакций и тестируемости приложения. На интервью важно объяснять не синтаксис `@Autowired` или `@Transactional`, а инженерный смысл этих механизмов.

## Ключевые идеи

1. IoC container:
   управляет созданием и связыванием компонентов приложения.
2. Dependency Injection:
   упрощает замену реализаций и тестирование.
3. Слои:
   `controller`, `service`, `repository` разделяют ответственность.
4. Транзакции:
   задают границы консистентных изменений.
5. Тестируемость:
   хорошая архитектура на Spring делает зависимости явными и заменяемыми.

## Что важно для интервью

- Уметь объяснить, зачем нужен DI на практическом примере.
- Понимать, что плохие transaction boundaries ломают консистентность.
- Показывать, как Spring помогает держать бизнес-логику вне web-слоя.

## Сигналы сильного ответа

- Кандидат говорит про модульность и testability.
- Связывает `@Transactional` с бизнес-операцией, а не с "обязательной аннотацией".
- Понимает цену скрытой framework-магии.

## Retrieval tags

`spring`, `ioc`, `di`, `controller`, `service`, `repository`, `transaction`, `testability`
