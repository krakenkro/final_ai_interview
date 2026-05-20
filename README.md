# Interview Prep Copilot

Working MVP for the final LLM engineering project: a web app for mock technical interviews with document upload, intake parsing, candidate/job profiling, a curated RAG knowledge base, LangGraph orchestration, custom MCP tools, voice mode, and evaluation pipelines.

Текущий прогресс по этапам и уже реализованным частям проекта зафиксирован в [IMPLEMENTED_STEPS.md](/Users/akbota/Desktop/final/IMPLEMENTED_STEPS.md).

## Что уже реализовано

- frontend на `Next.js + React + TypeScript`
- создание session records
- upload резюме и сохранение данных вакансии
- intake analysis endpoint с построением `candidate_profile`, `job_profile`, `skill_gap_map`
- HR-style semantic analysis поверх intake через MCP + LLM
- вывод тем интервью на основе резюме и вакансии
- SQLite storage для сессий, документов и истории ответов
- parser layer с fallback для `PDF`, `DOCX`, `HTML`, `TXT`, `MD`
- RAG-backed mock interview flow с выбором вопросов и follow-up по knowledge base
- curated knowledge base в `data/raw/` и `data/processed/`
- stage 3 ingestion pipeline с canonical metadata mapping
- section-aware chunking и сбор artifacts в `data/vectordb/`
- `text-embedding-3-large` embeddings + persistent `Chroma`
- vector retrieval с lexical JSONL fallback
- LangGraph workflow для planner/interviewer/evaluator/follow-up/report
- custom MCP server `interview_kb_mcp`
- custom Skill `Interview Coach`
- voice mode с `STT` через OpenAI и `TTS` через `fal.ai`

## Структура

```text
backend/
  api/
  services/
  storage/
frontend/
  app/
  components/
  lib/
data/
  raw/
  processed/
  vectordb/
```

## Локальный запуск

### Backend

```bash
python3.11 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python main.py
```

Backend API будет доступен на [http://127.0.0.1:8000](http://127.0.0.1:8000).

Ключевой intake endpoint:

- `POST /api/sessions/{session_id}/analyze`

### RAG ingestion

Команда сборки knowledge base artifacts:

```bash
./.venv/bin/python -m backend.services.rag_ingestion
```

После прогона pipeline создаёт:

- [data/vectordb/documents.jsonl](/Users/akbota/Desktop/final/data/vectordb/documents.jsonl)
- [data/vectordb/chunks.jsonl](/Users/akbota/Desktop/final/data/vectordb/chunks.jsonl)
- [data/vectordb/manifest.json](/Users/akbota/Desktop/final/data/vectordb/manifest.json)
- [data/vectordb/embedding_manifest.json](/Users/akbota/Desktop/final/data/vectordb/embedding_manifest.json)
- persistent Chroma collection в [data/vectordb/chroma](/Users/akbota/Desktop/final/data/vectordb/chroma)

Текущая реализация ingestion:

- читает `raw` и `processed` markdown-слои
- приводит metadata двух схем к единому canonical виду
- режет документы на section-aware chunks
- строит embeddings через `text-embedding-3-large`
- сохраняет embeddings и metadata в persistent `Chroma`
- готовит lexical fallback artifacts для planner / evaluator / recommendation flow

Перед запуском ingestion убедитесь, что задан `OPENAI_API_KEY`. Проект автоматически подхватывает `.env` из корня репозитория.

### RAG evaluation

Команда оценки retrieval качества:

```bash
./.venv/bin/python -m backend.evals.run_rag_eval
```

Артефакты evaluation:

- [backend/evals/rag_queries.jsonl](/Users/akbota/Desktop/final/backend/evals/rag_queries.jsonl)
- [backend/evals/reports/rag_eval_latest.json](/Users/akbota/Desktop/final/backend/evals/reports/rag_eval_latest.json)
- [backend/evals/reports/rag_eval_latest.md](/Users/akbota/Desktop/final/backend/evals/reports/rag_eval_latest.md)

Текущий baseline:

- `14` eval-cases
- `100%` pass rate
- `100%` topic hit rate
- `100%` document type hit rate
- `100%` backend expected rate
- observed backend: `chroma_openai`

### MCP server and Skill

Проект использует domain-specific MCP и custom Skill поверх RAG и LangGraph flow.

MCP server:

- path: [mcp_servers/interview_kb_mcp/server.py](/Users/akbota/Desktop/final/mcp_servers/interview_kb_mcp/server.py)
- transport: `stdio`
- process model: отдельный Python-процесс
- tools:
  - `search_interview_questions`
  - `get_topic_cheatsheet`
  - `get_evaluation_rubric`
  - `get_followup_questions`

Дополнительно для intake analysis теперь есть отдельный MCP server:

- path: [mcp_servers/hr_resume_mcp/server.py](/Users/akbota/Desktop/final/mcp_servers/hr_resume_mcp/server.py)
- transport: `stdio`
- tool:
  - `analyze_resume_vacancy_fit_tool`

Этот MCP server не заменяет текущий deterministic intake pipeline. Он работает как enrichment-слой поверх:

- parser summary
- `candidate_profile`
- `job_profile`
- `skill_gap_map`
- `interview_topics`

и добавляет `hr_analysis` с match score, HR verdict, ATS keyword analysis, improvement suggestions и rewritten resume fragments.

Запуск MCP server вручную:

```bash
./.venv/bin/python -m mcp_servers.interview_kb_mcp.server
```

Custom Skill:

- path: [skills/interview_coach/SKILL.md](/Users/akbota/Desktop/final/skills/interview_coach/SKILL.md)
- назначение: стандартизировать итоговый coaching report
- используется в report-node workflow и формирует блоки:
  - `What was good`
  - `What was weak`
  - `How to improve`
  - `Recommended drills`

### Voice mode

Проект поддерживает рабочий voice MVP поверх уже существующего mock interview flow.

Что теперь поддерживается:

- `STT` для ответов пользователя через [backend/services/asr.py](/Users/akbota/Desktop/final/backend/services/asr.py)
- `TTS` для текущего вопроса интервьюера через [backend/services/tts.py](/Users/akbota/Desktop/final/backend/services/tts.py)
- frontend voice controls на экране интервью:
  - запись ответа через `MediaRecorder`
  - выбор готового аудиофайла
  - распознавание аудио в текст ответа
  - генерация озвучки текущего вопроса

API routes:

- `POST /api/sessions/{session_id}/voice/transcribe`
- `POST /api/sessions/{session_id}/voice/question-audio`

Текущая voice-конфигурация:

- ASR model: `whisper-1`
- TTS model: `fal-ai/minimax/speech-02-hd`
- provider: `OpenAI + fal.ai`

Для voice mode нужны:

- `OPENAI_API_KEY` для `STT`
- `FAL_KEY` для `TTS`
- `FAL_TTS_MODEL=fal-ai/minimax/speech-02-hd`
- `FAL_TTS_LANGUAGE=Russian`

`FAL_VOICE_CLONE_PREVIEW_MODEL=speech-02-hd` уже можно держать в `.env` как подготовку к следующему voice-этапу, хотя текущий MVP его ещё не вызывает.

### Frontend

Frontend находится в [frontend/package.json](/Users/akbota/Desktop/final/frontend/package.json) и запускается так:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

или любой совместимый package manager.

## Parsing notes

- `Docling` теперь входит в проектные зависимости и должен устанавливаться сразу в локальное `.venv`
- parser сначала пытается использовать `Docling`
- если `Docling` отсутствует, включается fallback:
  - `pypdf` для `PDF`
  - `python-docx` для `DOCX`
  - стандартный `html.parser` для `HTML`
- для vacancy URL поддержан простой `urllib` fetch, но dynamic pages позже лучше закрыть через `Playwright`

## HR analysis

Intake analysis теперь состоит из двух слоёв:

1. deterministic parser/profile pipeline
2. HR-style semantic analysis через MCP + LLM

Во время `POST /api/sessions/{session_id}/analyze` backend:

- парсит резюме и вакансию
- строит `candidate_profile`, `job_profile`, `skill_gap_map`, `interview_topics`
- затем вызывает `hr_resume_mcp`
- сохраняет результат в `analysis.hr_analysis`

Если MCP/LLM-слой не сработает, основной intake analysis не ломается: deterministic artifacts всё равно сохраняются, а `hr_analysis.status` будет `skipped` или `failed`.

Новые env-переменные:

- `HR_ANALYSIS_PROVIDER=openai`
- `HR_ANALYSIS_MODEL=gpt-4o-mini`
- `HR_ANALYSIS_MAX_INPUT_CHARS=16000`
- `HR_ANALYSIS_MAX_OUTPUT_TOKENS=2200`

## Model choice and inference settings

Текущий основной LLM-backed сценарий в проекте:

- `OpenAI gpt-4o-mini` для `HR-style resume / vacancy analysis`
- structured JSON output поверх deterministic intake pipeline

Почему выбрана эта модель:

- даёт хороший баланс `cost / latency / quality` для MVP
- отвечает быстрее и дешевле, чем более тяжёлые модели уровня `gpt-4.1`
- качества достаточно для короткого semantic analysis и стабильного structured output

Текущие inference settings:

- `temperature=0.2`
- `max_tokens=2200`
- `top_p` не переопределяется и остаётся provider default

Почему такие параметры:

- низкая `temperature` уменьшает variance и помогает получать более стабильный JSON
- `max_tokens=2200` хватает для подробного match analysis без лишнего роста latency и стоимости
- `top_p` оставлен по умолчанию, потому что в этом сценарии основная управляемость уже достигается через низкую `temperature`

Текущий trade-off:

- приоритет на стороне скорости ответа и стоимости demo
- небольшая потеря в глубине reasoning по сравнению с более сильными моделями принята осознанно
- для следующей итерации логичный A/B-кандидат: `gpt-4.1` для более LLM-heavy planner / interviewer сценариев

## Dependency workflow

- backend-зависимости ставим сразу в проектное `.venv`
- базовый локальный интерпретатор для backend сейчас: `Python 3.11`
- если на следующем этапе понадобится новый пакет, добавляем его в [requirements.txt](/Users/akbota/Desktop/final/requirements.txt) и сразу ставим в `.venv`, а не откладываем на потом
- для stage 3 embeddings используются:
  - `openai`
  - `chromadb`
  - `python-dotenv`
- для stage 4-5 orchestration и MCP используются:
  - `langgraph`
  - `fastmcp`
- для stage 6 voice используются:
  - `OpenAI Whisper`
  - `fal.ai MiniMax Speech 02 HD`
  - browser `MediaRecorder`

## Проверено

- backend parser/profile builder проходит синтаксическую и сценарную проверку
- `yarn build` для frontend проходит успешно
- backend CORS готов для работы с frontend на `http://localhost:3000`
- ingestion pipeline успешно собирает `documents.jsonl`, `chunks.jsonl`, `manifest.json`
- retrieval поддерживает vector search через `Chroma` и lexical fallback по JSONL
- retrieval eval runner успешно проходит на baseline dataset
- `build_first_question()` и `evaluate_answer()` используют RAG retrieval для topic-aware question planning
- LangGraph workflow проходит end-to-end текстовую mock interview сессию
- workflow trace и final report сохраняются в session storage
- custom MCP tools реально вызываются в interview workflow и влияют на question planning, follow-up и evaluator context
- final report включает coaching block, собранный через custom Skill
- voice mode умеет озвучивать текущий вопрос и транскрибировать голосовой ответ в текст

## Ограничения текущего этапа

- profile builder пока эвристический, без LLM extraction
- evaluator остаётся упрощённым deterministic слоем, хотя planner/interviewer уже опираются на RAG
- retrieval зависит от `OPENAI_API_KEY` для vector search; без него остаётся lexical fallback
- persistent vector store локальный (`Chroma`), внешний managed vector DB пока не подключён
- MCP client сейчас поднимает отдельный stdio process per tool call; для MVP это нормально, но позже можно оптимизировать reuse соединения
- voice pipeline сейчас non-streaming: вопрос сначала синтезируется целиком, а ответ сначала записывается целиком, потом отправляется в STT
