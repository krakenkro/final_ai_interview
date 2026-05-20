# interview_kb_mcp

Custom MCP server for the mock interview copilot.

## Purpose

The server gives the interview workflow controlled access to the curated knowledge base.

It is designed to support:

- topic-aware interview planning
- retrieval of question candidates
- follow-up generation
- rubric and cheatsheet lookup during evaluation

## Transport

- process model: separate Python process
- protocol: `stdio`

## Tools

- `search_interview_questions(topic, level, limit=5, role=None, interview_type="technical_core")`
- `get_topic_cheatsheet(topic, role=None, level="middle", interview_type="technical_core")`
- `get_evaluation_rubric(question_type, level, role=None)`
- `get_followup_questions(topic, previous_answer_summary="", level="middle", role=None, interview_type="mixed", limit=3)`

## Run locally

```bash
./.venv/bin/python -m mcp_servers.interview_kb_mcp.server
```

## Notes

- the server reads from the local RAG layer in `backend/services/rag.py`
- when vector retrieval is unavailable, it falls back to lexical JSONL retrieval
- the LangGraph interview flow invokes this server through `backend/services/interview_mcp_client.py`
