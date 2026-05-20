# Spring Basics

- Topic: Spring framework fundamentals
- Role: Java Backend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://docs.spring.io/spring-framework/reference/
- Language: English
- Collected On: 2026-05-10

## Source Summary

The Spring Framework reference organizes the platform around core technologies such as the IoC container and dependency injection, plus data access, transaction management, web applications, and testing. For interviews, Spring knowledge is usually evaluated through architecture decisions rather than memorized annotations alone.

## Key Notes

### IoC and Dependency Injection

- The IoC container creates and wires application components.
- Dependency Injection reduces manual construction and improves modularity and testability.
- Candidates should explain why DI matters for replacing implementations, isolating concerns, and writing tests.

### Beans and Configuration

- Spring manages application objects as beans.
- Bean lifecycle and dependency graphs affect application startup, wiring, and runtime behavior.

### Web Layer

- Spring is commonly used to build HTTP APIs and MVC-style web applications.
- Interview answers often involve controllers, services, repositories, and validation boundaries.

### Transaction Management

- Spring provides declarative transaction management and `@Transactional`.
- Candidates should understand that transactions are not only annotations, but consistency boundaries around operations.

### Testing and Maintainability

- Spring projects are expected to be testable through clear separation of layers and replaceable dependencies.

## Interview-Relevant Takeaways

- Good answers explain the purpose of DI, not just its syntax.
- Middle-level answers should discuss service boundaries, transactions, and the role of Spring in layered architecture.
- Strong candidates know when framework convenience hides complexity, especially around proxies and transactions.

## Retrieval Keywords

`spring`, `ioc`, `dependency injection`, `beans`, `layered architecture`, `controllers`, `services`, `repositories`, `transaction management`, `testing`
