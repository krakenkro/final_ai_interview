import html
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional

from backend.observability.langsmith import traceable

try:
    from docling.document_converter import DocumentConverter  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    DocumentConverter = None

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None

try:
    import docx  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    docx = None


class VisibleTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignore_depth += 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "br"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignore_depth > 0:
            self._ignore_depth -= 1
        if tag in {"p", "div", "section", "article", "li"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0 and data.strip():
            self._parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self._parts)


@traceable(run_type="parser", name="parse_resume_document")
def parse_resume_document(document_path: str) -> Dict[str, object]:
    return parse_document(document_path, source_type="resume_file")


@traceable(run_type="parser", name="parse_vacancy_input")
def parse_vacancy_input(vacancy_text: str = "", vacancy_url: str = "") -> Dict[str, object]:
    if vacancy_text.strip():
        normalized = normalize_text(vacancy_text)
        return build_parse_result(
            source="vacancy_text",
            source_type="vacancy_text",
            parser_used="direct_text",
            raw_text=vacancy_text,
            normalized_text=normalized,
            warnings=[],
        )

    if vacancy_url.strip():
        return parse_remote_html(vacancy_url.strip())

    return build_parse_result(
        source="vacancy_empty",
        source_type="vacancy_text",
        parser_used="empty_input",
        raw_text="",
        normalized_text="",
        warnings=["Vacancy text or URL was not provided."],
    )


@traceable(run_type="parser", name="parse_document")
def parse_document(document_path: str, source_type: str = "file") -> Dict[str, object]:
    path = Path(document_path)
    if not path.exists():
        return build_parse_result(
            source=str(path),
            source_type=source_type,
            parser_used="missing_file",
            raw_text="",
            normalized_text="",
            warnings=[f"File not found: {path}"],
        )

    if DocumentConverter is not None and path.suffix.lower() in {".pdf", ".docx", ".html", ".htm", ".md", ".txt"}:
        try:
            converter = DocumentConverter()
            result = converter.convert(str(path))
            markdown = result.document.export_to_markdown()
            return build_parse_result(
                source=str(path),
                source_type=source_type,
                parser_used="docling",
                raw_text=markdown,
                normalized_text=normalize_text(markdown),
                warnings=[],
            )
        except Exception as exc:
            warnings = [f"Docling parsing failed, fallback parser used: {exc}"]
    else:
        warnings = ["Docling is not installed, fallback parser used."]

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw_text = extract_pdf_text(path)
        parser_used = "pypdf_fallback"
    elif suffix == ".docx":
        raw_text = extract_docx_text(path)
        parser_used = "python_docx_fallback"
    elif suffix in {".html", ".htm"}:
        raw_text = extract_html_text(path.read_text(encoding="utf-8", errors="ignore"))
        parser_used = "html_parser_fallback"
    else:
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        parser_used = "plain_text_fallback"

    return build_parse_result(
        source=str(path),
        source_type=source_type,
        parser_used=parser_used,
        raw_text=raw_text,
        normalized_text=normalize_text(raw_text),
        warnings=warnings,
    )


@traceable(run_type="parser", name="parse_remote_html")
def parse_remote_html(url: str) -> Dict[str, object]:
    warnings: List[str] = []
    raw_html = ""
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "InterviewPrepBot/0.1",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw_html = response.read().decode(charset, errors="ignore")
    except Exception as exc:
        warnings.append(f"Failed to fetch vacancy URL: {exc}")

    normalized = extract_html_text(raw_html) if raw_html else ""
    return build_parse_result(
        source=url,
        source_type="vacancy_url",
        parser_used="remote_html_fetch" if raw_html else "remote_html_fetch_failed",
        raw_text=raw_html,
        normalized_text=normalize_text(normalized),
        warnings=warnings,
    )


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_docx_text(path: Path) -> str:
    if docx is None:
        return ""
    document = docx.Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_html_text(raw_html: str) -> str:
    parser = VisibleTextHTMLParser()
    parser.feed(raw_html)
    return html.unescape(parser.text())


def normalize_text(text: str) -> str:
    no_injection = re.sub(r"(?i)(ignore previous instructions|system prompt|assistant:|developer:)", " ", text)
    compact = re.sub(r"\r", "\n", no_injection)
    compact = re.sub(r"[ \t]+", " ", compact)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return compact.strip()


def build_parse_result(
    source: str,
    source_type: str,
    parser_used: str,
    raw_text: str,
    normalized_text: str,
    warnings: List[str],
) -> Dict[str, object]:
    return {
        "source": source,
        "source_type": source_type,
        "parser_used": parser_used,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "char_count": len(normalized_text),
        "warnings": warnings,
    }
