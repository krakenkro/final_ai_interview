# HTTP and REST Basics

- Topic: HTTP fundamentals for backend APIs
- Role: Java Backend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://developer.mozilla.org/en-US/docs/Web/HTTP
- Language: English
- Collected On: 2026-05-10

## Source Summary

MDN's HTTP overview provides the protocol foundations behind backend API design: request-response flow, message structure, methods, status codes, content negotiation, and related web concepts such as caching and authentication. For backend interviews, this is essential context for REST endpoint design.

## Key Notes

### Protocol Basics

- HTTP is a client-server protocol built around requests and responses.
- Each message has defined structure and metadata in headers.

### Methods and Intent

- `GET` reads data.
- `POST` usually creates or triggers processing.
- `PUT` typically replaces a resource representation.
- `PATCH` partially updates.
- `DELETE` removes a resource.

### Status Codes

- Status codes communicate outcome and are part of API contract design.
- Correct use of `2xx`, `4xx`, and `5xx` helps clients react predictably.

### Headers and Content

- Headers define metadata like content type, authentication, and caching rules.
- Payload format and error format should be consistent across an API.

### Backend Design Relevance

- Good REST discussions connect endpoint design, validation, idempotency, and error semantics.
- Candidates should be able to explain why method choice affects retries, caching, and client behavior.

## Interview-Relevant Takeaways

- Strong answers link HTTP theory to actual endpoint design.
- Good backend candidates treat status codes and methods as business semantics, not trivia.
- Middle-level answers should mention idempotency, validation boundaries, and clear error contracts.

## Retrieval Keywords

`http`, `rest`, `backend api`, `methods`, `status codes`, `headers`, `idempotency`, `content-type`, `error contract`
