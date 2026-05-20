import cgi
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict
from urllib.parse import urlparse

from backend.graph.interview_graph import run_answer_workflow, run_start_workflow
from backend.services.asr import save_audio_file, transcribe_audio
from backend.services.hr_resume_ai import build_default_hr_analysis
from backend.services.hr_resume_mcp_client import analyze_resume_vacancy_fit as analyze_resume_vacancy_fit_mcp
from backend.services.parser import parse_resume_document, parse_vacancy_input
from backend.services.profile_builder import build_intake_artifacts
from backend.services.tts import synthesize_speech
from backend.storage.session_store import (
    advance_session,
    create_session,
    get_session,
    initialize_database,
    list_sessions,
    record_turn,
    save_session_analysis,
    save_resume_file,
    save_workflow_runtime,
    start_session,
    update_documents,
)


ALLOWED_ORIGINS = {
    "http://127.0.0.1:3000",
    "http://localhost:3000",
}


class InterviewAppHandler(BaseHTTPRequestHandler):
    server_version = "InterviewApp/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/api/health":
            self.send_json({"status": "ok"})
            return

        if route == "/api/sessions":
            self.send_json({"sessions": list_sessions()})
            return

        if route.startswith("/api/sessions/"):
            session_id = route.split("/")[3] if len(route.split("/")) > 3 else ""
            if not session_id:
                self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
                return
            self._handle_get_session(session_id)
            return

        if route == "/":
            self.send_json(
                {
                    "name": "Interview Prep API",
                    "status": "ok",
                    "frontend": "Run the Next.js frontend separately on http://localhost:3000",
                }
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Route not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/api/sessions":
            payload = self.read_json_body()
            session_data = create_session(payload)
            self.send_json(session_data, status=HTTPStatus.CREATED)
            return

        if route.endswith("/documents"):
            session_id = route.split("/")[3]
            self._handle_document_upload(session_id)
            return

        if route.endswith("/start"):
            session_id = route.split("/")[3]
            self._handle_start_session(session_id)
            return

        if route.endswith("/analyze"):
            session_id = route.split("/")[3]
            self._handle_analyze_session(session_id)
            return

        if route.endswith("/voice/transcribe"):
            session_id = route.split("/")[3]
            self._handle_voice_transcription(session_id)
            return

        if route.endswith("/voice/question-audio"):
            session_id = route.split("/")[3]
            self._handle_question_audio(session_id)
            return

        if route.endswith("/answers"):
            session_id = route.split("/")[3]
            self._handle_answer(session_id)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Route not found")

    def _handle_get_session(self, session_id: str) -> None:
        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return
        self.send_json(session_data)

    def _handle_document_upload(self, session_id: str) -> None:
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Expected multipart/form-data")
            return

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
        }
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=environ,
        )

        vacancy_text = form.getvalue("vacancy_text", "") or ""
        vacancy_url = form.getvalue("vacancy_url", "") or ""

        resume_filename = None
        resume_saved_path = None
        if "resume" in form and getattr(form["resume"], "filename", None):
            uploaded_file = form["resume"]
            file_bytes = uploaded_file.file.read()
            resume_filename = uploaded_file.filename
            resume_saved_path = save_resume_file(session_id, resume_filename, file_bytes)

        try:
            session_data = update_documents(
                session_id=session_id,
                vacancy_text=vacancy_text,
                vacancy_url=vacancy_url,
                resume_filename=resume_filename,
                resume_saved_path=resume_saved_path,
            )
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        self.send_json(session_data)

    def _handle_start_session(self, session_id: str) -> None:
        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        workflow_result = run_start_workflow(session_data)
        first_question = workflow_result["next_question"]
        updated_session = start_session(session_id, first_question)
        save_workflow_runtime(
            session_id,
            interview_plan=workflow_result.get("interview_plan", []),
            latest_trace=workflow_result.get("trace", []),
            last_evaluation={},
            final_report={},
        )
        updated_session = get_session(session_id)
        self.send_json(updated_session)

    def _handle_analyze_session(self, session_id: str) -> None:
        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        documents = session_data["documents"]
        resume_path = documents.get("resume_saved_path") or ""
        vacancy_text = documents.get("vacancy_text") or ""
        vacancy_url = documents.get("vacancy_url") or ""

        resume_parse = (
            parse_resume_document(str(resume_path))
            if resume_path
            else {
                "source": "resume_missing",
                "source_type": "resume_file",
                "parser_used": "missing_input",
                "raw_text": "",
                "normalized_text": "",
                "char_count": 0,
                "warnings": ["Resume file was not provided."],
            }
        )
        vacancy_parse = parse_vacancy_input(
            vacancy_text=str(vacancy_text),
            vacancy_url=str(vacancy_url),
        )

        artifacts = build_intake_artifacts(
            session=session_data["session"],
            resume_parse=resume_parse,
            vacancy_parse=vacancy_parse,
        )
        try:
            hr_analysis = analyze_resume_vacancy_fit_mcp(
                session=session_data["session"],
                parser_summary=artifacts["parser_summary"],
                candidate_profile=artifacts["candidate_profile"],
                job_profile=artifacts["job_profile"],
                skill_gap_map=artifacts["skill_gap_map"],
                interview_topics=artifacts["interview_topics"],
                resume_text=str(resume_parse.get("normalized_text", "")),
                vacancy_text=str(vacancy_parse.get("normalized_text", "")),
            )
        except Exception as exc:
            hr_analysis = build_default_hr_analysis(
                "failed",
                provider="mcp",
                model="",
                message=f"HR MCP analysis failed: {exc}",
            )

        analysis_status = "completed"
        if artifacts["candidate_profile"]["source_summary"]["has_content"] is False:
            analysis_status = "partial"
        if artifacts["job_profile"]["source_summary"]["has_content"] is False:
            analysis_status = "partial"

        save_session_analysis(
            session_id=session_id,
            analysis_status=analysis_status,
            parser_summary=artifacts["parser_summary"],
            candidate_profile=artifacts["candidate_profile"],
            job_profile=artifacts["job_profile"],
            skill_gap_map=artifacts["skill_gap_map"],
            hr_analysis=hr_analysis,
            interview_topics=artifacts["interview_topics"],
        )
        updated_session = get_session(session_id)
        self.send_json(updated_session)

    def _handle_voice_transcription(self, session_id: str) -> None:
        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Expected multipart/form-data")
            return

        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
        }
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=environ,
        )

        if "audio" not in form or not getattr(form["audio"], "filename", None):
            self.send_error(HTTPStatus.BAD_REQUEST, "Audio file is required")
            return

        uploaded_audio = form["audio"]
        audio_bytes = uploaded_audio.file.read()
        saved_path = save_audio_file(session_id, uploaded_audio.filename, audio_bytes)

        try:
            transcription = transcribe_audio(
                saved_path,
                interview_language=session_data["session"].get("interview_language"),
            )
        except Exception as error:
            self.send_error(
                HTTPStatus.BAD_GATEWAY,
                str(error).replace("\n", " ").strip() or "Voice transcription failed",
            )
            return

        self.send_json(transcription)

    def _handle_question_audio(self, session_id: str) -> None:
        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        payload = self.read_json_body()
        text = str(payload.get("text") or session_data["session"].get("current_question") or "").strip()
        if not text:
            self.send_error(HTTPStatus.BAD_REQUEST, "Question text is required")
            return

        try:
            audio_payload = synthesize_speech(
                text,
                interview_language=session_data["session"].get("interview_language"),
            )
        except Exception as error:
            self.send_error(
                HTTPStatus.BAD_GATEWAY,
                str(error).replace("\n", " ").strip() or "Speech synthesis failed",
            )
            return

        self.send_json(audio_payload)

    def _handle_answer(self, session_id: str) -> None:
        payload = self.read_json_body()
        answer_text = (payload.get("answer_text") or "").strip()
        if not answer_text:
            self.send_error(HTTPStatus.BAD_REQUEST, "answer_text is required")
            return

        try:
            session_data = get_session(session_id)
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND, "Session not found")
            return

        current_question = session_data["session"]["current_question"]
        if not current_question:
            self.send_error(HTTPStatus.BAD_REQUEST, "Interview is not started")
            return

        result = run_answer_workflow(session_data, answer_text)
        record_turn(
            session_id=session_id,
            question=current_question,
            answer=answer_text,
            feedback=result["feedback"],
            next_question=result["next_question"],
        )
        updated_session = advance_session(
            session_id=session_id,
            next_question=result["next_question"],
            next_cursor=result["next_cursor"],
            status=result["status"],
        )
        save_workflow_runtime(
            session_id,
            interview_plan=result.get("interview_plan", []),
            latest_trace=result.get("trace", []),
            last_evaluation=result.get("evaluation", {}),
            final_report=result.get("final_report", {}),
        )
        updated_session = get_session(session_id)
        self.send_json(updated_session)

    def read_json_body(self) -> Dict[str, object]:
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}
        return json.loads(raw_body.decode("utf-8"))

    def send_json(self, payload: Dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def end_headers(self) -> None:
        self.send_cors_headers()
        super().end_headers()

    def send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        else:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Vary", "Origin")

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    initialize_database()
    httpd = ThreadingHTTPServer((host, port), InterviewAppHandler)
    print(f"Interview app listening on http://{host}:{port}")
    httpd.serve_forever()
