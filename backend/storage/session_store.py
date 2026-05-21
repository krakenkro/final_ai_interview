import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "backend" / "storage" / "app.db"
UPLOADS_DIR = BASE_DIR / "backend" / "storage" / "uploads"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_database() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                role TEXT NOT NULL,
                seniority TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                interview_language TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                voice_mode TEXT NOT NULL,
                status TEXT NOT NULL,
                current_question TEXT,
                question_cursor INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_documents (
                session_id TEXT PRIMARY KEY,
                vacancy_text TEXT,
                vacancy_url TEXT,
                resume_filename TEXT,
                resume_saved_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                topic TEXT,
                question_kind TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                feedback TEXT NOT NULL,
                evaluation_summary_json TEXT NOT NULL DEFAULT '{}',
                next_question TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_profiles (
                session_id TEXT PRIMARY KEY,
                analysis_status TEXT NOT NULL,
                parser_summary_json TEXT NOT NULL,
                candidate_profile_json TEXT NOT NULL,
                job_profile_json TEXT NOT NULL,
                skill_gap_map_json TEXT NOT NULL,
                hr_analysis_json TEXT NOT NULL DEFAULT '{}',
                interview_topics_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_workflows (
                session_id TEXT PRIMARY KEY,
                interview_plan_json TEXT NOT NULL,
                latest_trace_json TEXT NOT NULL,
                last_evaluation_json TEXT NOT NULL,
                final_report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        profile_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(session_profiles)").fetchall()
        }
        if "hr_analysis_json" not in profile_columns:
            connection.execute(
                """
                ALTER TABLE session_profiles
                ADD COLUMN hr_analysis_json TEXT NOT NULL DEFAULT '{}'
                """
            )
        turn_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(session_turns)").fetchall()
        }
        if "topic" not in turn_columns:
            connection.execute(
                """
                ALTER TABLE session_turns
                ADD COLUMN topic TEXT
                """
            )
        if "question_kind" not in turn_columns:
            connection.execute(
                """
                ALTER TABLE session_turns
                ADD COLUMN question_kind TEXT
                """
            )
        if "evaluation_summary_json" not in turn_columns:
            connection.execute(
                """
                ALTER TABLE session_turns
                ADD COLUMN evaluation_summary_json TEXT NOT NULL DEFAULT '{}'
                """
            )
        connection.execute(
            """
            INSERT OR IGNORE INTO session_profiles (
                session_id, analysis_status, parser_summary_json,
                candidate_profile_json, job_profile_json, skill_gap_map_json,
                hr_analysis_json, interview_topics_json, created_at, updated_at
            )
            SELECT id, 'not_started', '{}', '{}', '{}', '{}', '{}', '[]', created_at, updated_at
            FROM sessions
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO session_workflows (
                session_id, interview_plan_json, latest_trace_json,
                last_evaluation_json, final_report_json, created_at, updated_at
            )
            SELECT id, '[]', '[]', '{}', '{}', created_at, updated_at
            FROM sessions
            """
        )
        connection.commit()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    timestamp = utc_now()

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions (
                id, created_at, updated_at, role, seniority, interview_type,
                interview_language, duration_minutes, voice_mode, status,
                current_question, question_cursor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                timestamp,
                timestamp,
                payload["role"],
                payload["seniority"],
                payload["interview_type"],
                payload["interview_language"],
                payload["duration_minutes"],
                payload["voice_mode"],
                "draft",
                None,
                0,
            ),
        )
        connection.execute(
            """
            INSERT INTO session_documents (
                session_id, vacancy_text, vacancy_url, resume_filename,
                resume_saved_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, "", "", "", "", timestamp, timestamp),
        )
        connection.execute(
            """
            INSERT INTO session_profiles (
                session_id, analysis_status, parser_summary_json,
                candidate_profile_json, job_profile_json, skill_gap_map_json,
                hr_analysis_json, interview_topics_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                "not_started",
                json.dumps({}),
                json.dumps({}),
                json.dumps({}),
                json.dumps({}),
                json.dumps({}),
                json.dumps([]),
                timestamp,
                timestamp,
            ),
        )
        connection.execute(
            """
            INSERT INTO session_workflows (
                session_id, interview_plan_json, latest_trace_json,
                last_evaluation_json, final_report_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                json.dumps({}, ensure_ascii=False),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()

    return get_session(session_id)


def save_resume_file(session_id: str, filename: str, file_bytes: bytes) -> str:
    safe_name = Path(filename).name or "resume.bin"
    target_path = UPLOADS_DIR / f"{session_id}_{safe_name}"
    target_path.write_bytes(file_bytes)
    return str(target_path)


def update_documents(
    session_id: str,
    vacancy_text: str,
    vacancy_url: str,
    resume_filename: Optional[str] = None,
    resume_saved_path: Optional[str] = None,
) -> Dict[str, Any]:
    timestamp = utc_now()
    with _connect() as connection:
        existing = connection.execute(
            "SELECT * FROM session_documents WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if existing is None:
            raise KeyError(f"Unknown session: {session_id}")

        connection.execute(
            """
            UPDATE session_documents
            SET vacancy_text = ?, vacancy_url = ?,
                resume_filename = COALESCE(?, resume_filename),
                resume_saved_path = COALESCE(?, resume_saved_path),
                updated_at = ?
            WHERE session_id = ?
            """,
            (
                vacancy_text,
                vacancy_url,
                resume_filename if resume_filename else None,
                resume_saved_path if resume_saved_path else None,
                timestamp,
                session_id,
            ),
        )
        connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )
        connection.commit()

    return get_session(session_id)


def start_session(session_id: str, first_question: str) -> Dict[str, Any]:
    timestamp = utc_now()
    with _connect() as connection:
        connection.execute(
            """
            UPDATE sessions
            SET status = ?, current_question = ?, question_cursor = ?, updated_at = ?
            WHERE id = ?
            """,
            ("in_progress", first_question, 0, timestamp, session_id),
        )
        connection.commit()
    return get_session(session_id)


def advance_session(
    session_id: str,
    next_question: Optional[str],
    next_cursor: int,
    status: str,
) -> Dict[str, Any]:
    timestamp = utc_now()
    with _connect() as connection:
        connection.execute(
            """
            UPDATE sessions
            SET current_question = ?, question_cursor = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (next_question, next_cursor, status, timestamp, session_id),
        )
        connection.commit()
    return get_session(session_id)


def record_turn(
    session_id: str,
    question: str,
    answer: str,
    feedback: str,
    next_question: Optional[str],
    *,
    topic: Optional[str] = None,
    question_kind: Optional[str] = None,
    evaluation_summary: Optional[Dict[str, Any]] = None,
) -> None:
    timestamp = utc_now()
    with _connect() as connection:
        turn_count = connection.execute(
            "SELECT COUNT(*) AS count FROM session_turns WHERE session_id = ?",
            (session_id,),
        ).fetchone()["count"]
        connection.execute(
            """
            INSERT INTO session_turns (
                session_id, turn_index, topic, question_kind, question, answer,
                feedback, evaluation_summary_json, next_question, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                turn_count + 1,
                topic,
                question_kind,
                question,
                answer,
                feedback,
                json.dumps(evaluation_summary or {}, ensure_ascii=False),
                next_question,
                timestamp,
            ),
        )
        connection.commit()


def save_session_analysis(
    session_id: str,
    analysis_status: str,
    parser_summary: Dict[str, Any],
    candidate_profile: Dict[str, Any],
    job_profile: Dict[str, Any],
    skill_gap_map: Dict[str, Any],
    hr_analysis: Optional[Dict[str, Any]],
    interview_topics: List[Dict[str, Any]],
) -> None:
    timestamp = utc_now()
    with _connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO session_profiles (
                session_id, analysis_status, parser_summary_json,
                candidate_profile_json, job_profile_json, skill_gap_map_json,
                hr_analysis_json, interview_topics_json, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
                    (SELECT created_at FROM session_profiles WHERE session_id = ?),
                    ?
                ), ?
            )
            """,
            (
                session_id,
                analysis_status,
                json.dumps(parser_summary, ensure_ascii=False),
                json.dumps(candidate_profile, ensure_ascii=False),
                json.dumps(job_profile, ensure_ascii=False),
                json.dumps(skill_gap_map, ensure_ascii=False),
                json.dumps(hr_analysis or {}, ensure_ascii=False),
                json.dumps(interview_topics, ensure_ascii=False),
                session_id,
                timestamp,
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )
        connection.commit()


def save_workflow_runtime(
    session_id: str,
    *,
    interview_plan: Optional[List[Dict[str, Any]]] = None,
    latest_trace: Optional[List[Dict[str, Any]]] = None,
    last_evaluation: Optional[Dict[str, Any]] = None,
    final_report: Optional[Dict[str, Any]] = None,
) -> None:
    timestamp = utc_now()
    with _connect() as connection:
        existing = connection.execute(
            "SELECT * FROM session_workflows WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if existing is None:
            raise KeyError(f"Unknown session: {session_id}")

        connection.execute(
            """
            UPDATE session_workflows
            SET interview_plan_json = COALESCE(?, interview_plan_json),
                latest_trace_json = COALESCE(?, latest_trace_json),
                last_evaluation_json = COALESCE(?, last_evaluation_json),
                final_report_json = COALESCE(?, final_report_json),
                updated_at = ?
            WHERE session_id = ?
            """,
            (
                json.dumps(interview_plan, ensure_ascii=False) if interview_plan is not None else None,
                json.dumps(latest_trace, ensure_ascii=False) if latest_trace is not None else None,
                json.dumps(last_evaluation, ensure_ascii=False) if last_evaluation is not None else None,
                json.dumps(final_report, ensure_ascii=False) if final_report is not None else None,
                timestamp,
                session_id,
            ),
        )
        connection.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (timestamp, session_id),
        )
        connection.commit()


def get_session(session_id: str) -> Dict[str, Any]:
    with _connect() as connection:
        session_row = connection.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if session_row is None:
            raise KeyError(f"Unknown session: {session_id}")

        documents_row = connection.execute(
            "SELECT * FROM session_documents WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        profiles_row = connection.execute(
            "SELECT * FROM session_profiles WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        workflow_row = connection.execute(
            "SELECT * FROM session_workflows WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        turn_rows = connection.execute(
            """
            SELECT turn_index, topic, question_kind, question, answer,
                   feedback, evaluation_summary_json, next_question, created_at
            FROM session_turns
            WHERE session_id = ?
            ORDER BY turn_index ASC
            """,
            (session_id,),
        ).fetchall()

    return {
        "session": dict(session_row),
        "documents": dict(documents_row) if documents_row else {},
        "analysis": _decode_profile_row(profiles_row),
        "workflow": _decode_workflow_row(workflow_row),
        "turns": [_decode_turn_row(row) for row in turn_rows],
    }


def list_sessions() -> List[Dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, updated_at, role, seniority, interview_type,
                   interview_language, duration_minutes, voice_mode, status
            FROM sessions
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _decode_profile_row(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
    if row is None:
        return {}

    return {
        "session_id": row["session_id"],
        "analysis_status": row["analysis_status"],
        "parser_summary": json.loads(row["parser_summary_json"] or "{}"),
        "candidate_profile": json.loads(row["candidate_profile_json"] or "{}"),
        "job_profile": json.loads(row["job_profile_json"] or "{}"),
        "skill_gap_map": json.loads(row["skill_gap_map_json"] or "{}"),
        "hr_analysis": json.loads(row["hr_analysis_json"] or "{}"),
        "interview_topics": json.loads(row["interview_topics_json"] or "[]"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _decode_workflow_row(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
    if row is None:
        return {}

    return {
        "session_id": row["session_id"],
        "interview_plan": json.loads(row["interview_plan_json"] or "[]"),
        "latest_trace": json.loads(row["latest_trace_json"] or "[]"),
        "last_evaluation": json.loads(row["last_evaluation_json"] or "{}"),
        "final_report": json.loads(row["final_report_json"] or "{}"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _decode_turn_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "turn_index": row["turn_index"],
        "topic": row["topic"],
        "question_kind": row["question_kind"],
        "question": row["question"],
        "answer": row["answer"],
        "feedback": row["feedback"],
        "evaluation_summary": json.loads(row["evaluation_summary_json"] or "{}"),
        "next_question": row["next_question"],
        "created_at": row["created_at"],
    }
