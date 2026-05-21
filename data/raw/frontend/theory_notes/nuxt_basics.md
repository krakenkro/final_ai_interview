# Nuxt Basics

- Topic: Nuxt 3 application model and data loading fundamentals
- Role: Frontend Developer
- Seniority: Junior, Middle
- Interview Type: Technical Core, Mixed
- Document Type: theory_note
- Source URL: https://nuxt.com/docs/getting-started/views
- Language: English
- Collected On: 2026-05-21

## Source Summary

Nuxt extends Vue with file-based routing, server rendering options, and integrated data-loading patterns. The important interview themes are route structure, SSR versus CSR versus SSG, `useFetch` and `useAsyncData`, middleware, hydration, and the boundary between server-only and browser-only code.

## Key Notes

### Routing and Pages

- Files inside the pages directory become routes.
- This affects how teams structure features and shared layout logic.

### Rendering Strategies

- SSR can improve first load and SEO, but adds runtime complexity.
- CSR can be simpler for heavily interactive authenticated surfaces.
- SSG works well for stable content and predictable publishing flows.

### Data Loading

- Nuxt provides built-in patterns for loading data during navigation and rendering.
- The server/client boundary changes caching, latency, and debugging behavior.

### Runtime Constraints

- Browser-only APIs cannot be used blindly during SSR.
- Hydration mismatches appear when server-rendered markup and client state diverge.

## Interview-Relevant Takeaways

- Strong answers connect rendering strategy to product requirements, not just definitions.
- Good middle-level answers talk about hydration, stale data, and repeated navigation behavior.
- Real-world examples often come from dashboards, landing pages, account areas, or filtered lists.

## Retrieval Keywords

`nuxt`, `routing`, `ssr`, `csr`, `ssg`, `useFetch`, `useAsyncData`, `middleware`, `hydration`, `server client boundary`
