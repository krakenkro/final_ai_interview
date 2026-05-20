# JavaScript Event Loop

- Topic: JavaScript execution model and event loop
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://developer.mozilla.org/ru/docs/Web/JavaScript/Reference/Execution_model
- Language: Russian
- Collected On: 2026-05-10

## Source Summary

The MDN execution model page explains how JavaScript processes work items using a call stack and a task queue. It highlights the single-threaded execution model, run-to-completion behavior, and why long synchronous work blocks interactivity.

## Key Notes

### Execution Model

- JavaScript code runs inside execution contexts.
- Function calls are managed through a stack.
- Only one frame is actively executed at a time in the standard single-threaded model.

### Event Loop

- The event loop continually waits for queued work and processes the next message when the stack is free.
- A task waits in the queue until currently running work is fully completed.

### Run to Completion

- Each message runs to completion before the next one starts.
- This simplifies reasoning about shared state because another handler will not interrupt halfway through the current synchronous task.

### Blocking Risks

- Long-running synchronous code blocks the event loop.
- When the main thread is blocked, timers, user interaction, rendering updates, and network callbacks feel delayed.

### Practical Frontend Relevance

- Interview answers should connect event loop knowledge to UI responsiveness, async APIs, debouncing, and avoiding heavy work on the main thread.
- `setTimeout(..., 0)` does not mean "execute immediately"; it means "schedule for a future turn after current work finishes."

## Interview-Relevant Takeaways

- Good answers explain stack, queue, and run-to-completion in plain language.
- Stronger answers link the model to rendering jank, slow handlers, and debugging async behavior.
- Middle-level candidates should be able to explain why short synchronous chunks improve user experience.

## Retrieval Keywords

`javascript`, `event loop`, `execution model`, `call stack`, `task queue`, `run to completion`, `main thread`, `blocking code`, `setTimeout`
