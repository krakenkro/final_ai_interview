# HTTP and API Basics

- Topic: HTTP fundamentals for frontend API integration
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://developer.mozilla.org/en-US/docs/Web/HTTP
- Language: English
- Collected On: 2026-05-10

## Source Summary

MDN's HTTP overview presents HTTP as the application-layer protocol used for communication between clients and servers on the web. It points to the core concepts needed by frontend engineers: request-response flow, message structure, methods, status codes, content types, caching, cookies, authentication, and CORS-related topics.

## Key Notes

### Request-Response Model

- HTTP communication is built around a client sending a request and a server returning a response.
- A typical session includes connection setup, request transmission, response handling, and optional reuse of the connection.

### Message Structure

- Requests and responses have a defined structure.
- Important parts include start line, headers, and optional body.
- Headers carry metadata such as content type, caching rules, authentication data, and accepted formats.

### Methods and Semantics

- Common methods include `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`.
- Method choice communicates intent and affects idempotency expectations, caching behavior, and backend design.

### Status Codes

- `2xx` indicates success.
- `3xx` covers redirection.
- `4xx` means the client request has an issue or lacks permission.
- `5xx` signals server-side failure.

### Web-Relevant Concepts

- MIME types and `Content-Type` help clients interpret payloads correctly.
- Caching, cookies, authentication, and cross-origin rules are important for real application behavior.

## Interview-Relevant Takeaways

- Good answers go beyond "HTTP is a protocol" and explain request structure and method semantics.
- Strong frontend candidates connect HTTP knowledge to fetch clients, REST integration, CORS, error handling, and caching behavior.
- Middle-level answers should show judgment about which method and status code fit a given API action.

## Retrieval Keywords

`http`, `request`, `response`, `headers`, `body`, `methods`, `status codes`, `content-type`, `caching`, `cors`, `rest`
