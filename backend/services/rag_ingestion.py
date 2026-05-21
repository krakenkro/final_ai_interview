import hashlib
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from dotenv import load_dotenv
from backend.observability.langsmith import wrap_openai_client

try:
    import chromadb
except ImportError:  # pragma: no cover - handled at runtime
    chromadb = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORDB_DIR = DATA_DIR / "vectordb"
CHROMA_DIR = VECTORDB_DIR / "chroma"

DOCUMENTS_PATH = VECTORDB_DIR / "documents.jsonl"
CHUNKS_PATH = VECTORDB_DIR / "chunks.jsonl"
MANIFEST_PATH = VECTORDB_DIR / "manifest.json"
EMBEDDING_MANIFEST_PATH = VECTORDB_DIR / "embedding_manifest.json"

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large").strip() or "text-embedding-3-large"
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_chunks").strip() or "knowledge_chunks"
EMBEDDING_BATCH_SIZE = int(os.getenv("OPENAI_EMBEDDING_BATCH_SIZE", "64"))

RAW_METADATA_MAP = {
    "Topic": "topic",
    "Role": "role",
    "Seniority": "seniority",
    "Interview Type": "interview_type",
    "Document Type": "document_type",
    "Source URL": "source_url",
    "Language": "language",
    "Collected On": "collected_on",
}

PROCESSED_METADATA_MAP = {
    "topic": "topic",
    "role": "role",
    "seniority": "seniority",
    "interview_type": "interview_type",
    "document_type": "document_type",
    "source_url": "source_url",
    "source_language": "source_language",
    "normalized_language": "normalized_language",
    "normalized_on": "normalized_on",
}

CSV_FIELDS = {"seniority", "interview_type"}
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "why",
    "with",
    "и",
    "в",
    "во",
    "на",
    "с",
    "со",
    "по",
    "как",
    "что",
    "это",
    "для",
    "не",
    "но",
    "или",
    "из",
    "к",
    "у",
    "о",
    "об",
    "от",
    "за",
}

ACTIVE_KB_ROOTS = {
    "frontend",
    "behavioural",
    "interview_modes",
    "level_notes",
}


@dataclass
class KnowledgeDocument:
    document_id: str
    layer: str
    path: str
    title: str
    role: str
    seniority: List[str]
    interview_type: List[str]
    document_type: str
    topic: str
    source_url: str
    language: str
    metadata: Dict[str, object]
    body: str
    char_count: int
    token_count_estimate: int


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    layer: str
    path: str
    title: str
    section: str
    chunk_index: int
    text: str
    role: str
    seniority: List[str]
    interview_type: List[str]
    document_type: str
    topic: str
    source_url: str
    language: str
    char_count: int
    token_count_estimate: int


@dataclass
class EmbeddingBuildResult:
    enabled: bool
    backend: str
    collection_name: str
    embedding_model: str
    embedding_dimensions: Optional[int]
    chunks_embedded: int
    notes: str
    error: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if path.name == ".gitkeep":
            continue
        if path.name == "METADATA_SCHEMA.md":
            continue
        if not is_active_ingestion_path(root, path):
            continue
        yield path


def is_active_ingestion_path(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    if not relative.parts:
        return False

    top_level = relative.parts[0]
    if top_level in ACTIVE_KB_ROOTS:
        return True

    if top_level == "role_notes":
        return path.stem == "frontend_developer"

    if top_level == "vacancy_archetypes":
        return path.stem.startswith("frontend_")

    return False


def canonicalize_list(value: str) -> List[str]:
    parts = [slugify(part) for part in value.split(",")]
    return [part for part in parts if part]


def canonicalize_scalar(value: str) -> str:
    return value.strip().lower()


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[\/\-]+", "_", lowered)
    lowered = re.sub(r"[^a-z0-9а-я_ ]+", "", lowered)
    lowered = re.sub(r"\s+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered)
    return lowered.strip("_")


def parse_metadata_block(lines: Sequence[str], layer: str) -> tuple[Dict[str, object], int]:
    metadata_map = RAW_METADATA_MAP if layer == "raw" else PROCESSED_METADATA_MAP
    metadata: Dict[str, object] = {}
    index = 1

    while index < len(lines) and not lines[index].strip():
        index += 1

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            break
        if not line.startswith("- "):
            break
        raw_key, _, raw_value = line[2:].partition(":")
        key = metadata_map.get(raw_key.strip())
        if key:
            value = raw_value.strip()
            if key in CSV_FIELDS:
                metadata[key] = canonicalize_list(value)
            else:
                metadata[key] = value
        index += 1

    return metadata, index


def normalize_metadata(layer: str, metadata: Dict[str, object]) -> Dict[str, object]:
    role = str(metadata.get("role", "cross_role")).strip()
    if layer == "raw":
        language = str(metadata.get("language", "unknown")).strip()
    else:
        language = str(metadata.get("normalized_language") or metadata.get("source_language") or "unknown").strip()

    seniority = metadata.get("seniority", [])
    if isinstance(seniority, str):
        seniority = canonicalize_list(seniority)

    interview_type = metadata.get("interview_type", [])
    if isinstance(interview_type, str):
        interview_type = canonicalize_list(interview_type)

    return {
        "topic": slugify(str(metadata.get("topic", "unknown"))),
        "role": slugify(role),
        "seniority": list(seniority),
        "interview_type": list(interview_type),
        "document_type": slugify(str(metadata.get("document_type", "unknown"))),
        "source_url": str(metadata.get("source_url", "")).strip(),
        "language": canonicalize_scalar(language),
        "collected_on": str(metadata.get("collected_on", "")).strip(),
        "source_language": canonicalize_scalar(str(metadata.get("source_language", "")).strip()) if layer == "processed" else "",
        "normalized_language": canonicalize_scalar(str(metadata.get("normalized_language", "")).strip()) if layer == "processed" else "",
        "normalized_on": str(metadata.get("normalized_on", "")).strip() if layer == "processed" else "",
    }


def parse_document(path: Path, layer: str) -> KnowledgeDocument:
    raw_text = path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()
    title = lines[0].lstrip("#").strip() if lines else path.stem
    metadata, body_start = parse_metadata_block(lines, layer)
    normalized = normalize_metadata(layer, metadata)
    body = "\n".join(lines[body_start:]).strip()

    document_id = hashlib.sha1(str(path.relative_to(BASE_DIR)).encode("utf-8")).hexdigest()[:16]
    token_count_estimate = len(tokenize(body))

    return KnowledgeDocument(
        document_id=document_id,
        layer=layer,
        path=str(path.relative_to(BASE_DIR)),
        title=title,
        role=str(normalized["role"]),
        seniority=list(normalized["seniority"]),
        interview_type=list(normalized["interview_type"]),
        document_type=str(normalized["document_type"]),
        topic=str(normalized["topic"]),
        source_url=str(normalized["source_url"]),
        language=str(normalized["language"]),
        metadata=normalized,
        body=body,
        char_count=len(body),
        token_count_estimate=token_count_estimate,
    )


def split_sections(text: str) -> List[tuple[str, str]]:
    if not text.strip():
        return [("Document Body", "")]

    heading_pattern = re.compile(r"^(##+)\s+(.*)$")
    sections: List[tuple[str, List[str]]] = []
    current_heading = "Document Body"
    current_lines: List[str] = []

    for line in text.splitlines():
        match = heading_pattern.match(line)
        if match:
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections.append((current_heading, current_lines))

    result: List[tuple[str, str]] = []
    for heading, lines in sections:
        result.append((heading, "\n".join(lines).strip()))
    return result


def split_long_text(text: str, max_chars: int = 900, overlap_chars: int = 140) -> List[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(
                text.rfind("\n\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("\n", start, end),
            )
            if boundary > start + 200:
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks


def chunk_document(document: KnowledgeDocument) -> List[KnowledgeChunk]:
    chunks: List[KnowledgeChunk] = []
    chunk_index = 0

    for section, section_text in split_sections(document.body):
        if not section_text:
            continue
        for part in split_long_text(section_text):
            text = f"{section}\n\n{part}".strip()
            chunk_id = f"{document.document_id}:{chunk_index}"
            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    layer=document.layer,
                    path=document.path,
                    title=document.title,
                    section=section,
                    chunk_index=chunk_index,
                    text=text,
                    role=document.role,
                    seniority=document.seniority,
                    interview_type=document.interview_type,
                    document_type=document.document_type,
                    topic=document.topic,
                    source_url=document.source_url,
                    language=document.language,
                    char_count=len(text),
                    token_count_estimate=len(tokenize(text)),
                )
            )
            chunk_index += 1

    return chunks


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Zа-яА-Я0-9_]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def build_manifest(documents: Sequence[KnowledgeDocument], chunks: Sequence[KnowledgeChunk]) -> Dict[str, object]:
    docs_by_layer = Counter(document.layer for document in documents)
    docs_by_role = Counter(document.role for document in documents)
    docs_by_type = Counter(document.document_type for document in documents)
    chunks_by_layer = Counter(chunk.layer for chunk in chunks)
    chunks_by_role = Counter(chunk.role for chunk in chunks)
    chunks_by_type = Counter(chunk.document_type for chunk in chunks)

    topic_counts: Dict[str, int] = defaultdict(int)
    for document in documents:
        topic_counts[document.topic] += 1

    return {
        "generated_at": utc_now(),
        "documents_path": str(DOCUMENTS_PATH.relative_to(BASE_DIR)),
        "chunks_path": str(CHUNKS_PATH.relative_to(BASE_DIR)),
        "total_documents": len(documents),
        "total_chunks": len(chunks),
        "documents_by_layer": dict(docs_by_layer),
        "documents_by_role": dict(docs_by_role),
        "documents_by_document_type": dict(docs_by_type),
        "chunks_by_layer": dict(chunks_by_layer),
        "chunks_by_role": dict(chunks_by_role),
        "chunks_by_document_type": dict(chunks_by_type),
        "topics_indexed": len(topic_counts),
        "layers_indexed": ["raw", "processed"],
        "chunking_strategy": {
            "mode": "section_aware_char_window",
            "target_max_chars": 900,
            "overlap_chars": 140,
        },
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def build_chunk_embedding_input(chunk: KnowledgeChunk) -> str:
    header_parts = [
        f"title: {chunk.title}",
        f"section: {chunk.section}",
        f"topic: {chunk.topic}",
        f"role: {chunk.role}",
        f"seniority: {', '.join(chunk.seniority)}" if chunk.seniority else "seniority: unknown",
        f"interview_type: {', '.join(chunk.interview_type)}" if chunk.interview_type else "interview_type: unknown",
        f"document_type: {chunk.document_type}",
        f"language: {chunk.language}",
    ]
    return "\n".join(header_parts + ["", chunk.text]).strip()


def chunk_to_chroma_metadata(chunk: KnowledgeChunk) -> Dict[str, object]:
    metadata: Dict[str, object] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "layer": chunk.layer,
        "path": chunk.path,
        "title": chunk.title,
        "section": chunk.section,
        "chunk_index": chunk.chunk_index,
        "role": chunk.role,
        "document_type": chunk.document_type,
        "topic": chunk.topic,
        "source_url": chunk.source_url,
        "language": chunk.language,
        "seniority_csv": ",".join(chunk.seniority),
        "interview_type_csv": ",".join(chunk.interview_type),
    }
    for value in ("junior", "middle"):
        metadata[f"seniority_{value}"] = value in chunk.seniority
    for value in ("technical_core", "behavioural", "mixed"):
        metadata[f"interview_type_{value}"] = value in chunk.interview_type
    return metadata


def batched(items: Sequence[str], batch_size: int) -> Iterable[Sequence[str]]:
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def get_openai_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("`openai` is not installed. Run `./.venv/bin/pip install -r requirements.txt`.")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to the environment or `.env` before running ingestion.")
    return wrap_openai_client(OpenAI(api_key=api_key))


def get_chroma_collection():
    if chromadb is None:
        raise RuntimeError("`chromadb` is not installed. Run `./.venv/bin/pip install -r requirements.txt`.")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def clear_chroma_store() -> None:
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)


def build_vector_store(chunks: Sequence[KnowledgeChunk]) -> EmbeddingBuildResult:
    client = get_openai_client()
    chroma_client, _ = get_chroma_collection()
    try:
        chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    chunk_ids = [chunk.chunk_id for chunk in chunks]
    embedding_inputs = [build_chunk_embedding_input(chunk) for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [chunk_to_chroma_metadata(chunk) for chunk in chunks]

    embeddings: List[List[float]] = []
    for batch in batched(embedding_inputs, EMBEDDING_BATCH_SIZE):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=list(batch),
        )
        embeddings.extend([item.embedding for item in response.data])

    collection.upsert(
        ids=chunk_ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    embedding_dimensions = len(embeddings[0]) if embeddings else None
    result = EmbeddingBuildResult(
        enabled=True,
        backend="chroma_persistent",
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_model=EMBEDDING_MODEL,
        embedding_dimensions=embedding_dimensions,
        chunks_embedded=len(embeddings),
        notes="OpenAI embeddings were generated and stored in the local Chroma collection.",
    )
    write_json(EMBEDDING_MANIFEST_PATH, asdict(result))
    return result


def resolve_embedding_status(chunks: Sequence[KnowledgeChunk], *, build_embeddings: bool) -> EmbeddingBuildResult:
    if not build_embeddings:
        clear_chroma_store()
        return EmbeddingBuildResult(
            enabled=False,
            backend="jsonl_artifacts",
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_model=EMBEDDING_MODEL,
            embedding_dimensions=None,
            chunks_embedded=0,
            notes="Embeddings were skipped. Retrieval can still use lexical JSONL fallback.",
        )
    try:
        return build_vector_store(chunks)
    except Exception as exc:
        clear_chroma_store()
        result = EmbeddingBuildResult(
            enabled=False,
            backend="jsonl_artifacts",
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_model=EMBEDDING_MODEL,
            embedding_dimensions=None,
            chunks_embedded=0,
            notes="Embedding build failed, so ingestion kept JSONL artifacts and lexical fallback active.",
            error=f"{type(exc).__name__}: {exc}",
        )
        write_json(EMBEDDING_MANIFEST_PATH, asdict(result))
        return result


def build_knowledge_base(*, build_embeddings: bool = True) -> Dict[str, object]:
    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

    documents: List[KnowledgeDocument] = []
    for layer, root in (("raw", RAW_DIR), ("processed", PROCESSED_DIR)):
        for path in iter_markdown_files(root):
            documents.append(parse_document(path, layer))

    chunks: List[KnowledgeChunk] = []
    for document in documents:
        chunks.extend(chunk_document(document))

    write_jsonl(DOCUMENTS_PATH, (asdict(document) for document in documents))
    write_jsonl(CHUNKS_PATH, (asdict(chunk) for chunk in chunks))

    manifest = build_manifest(documents, chunks)
    embedding_status = resolve_embedding_status(chunks, build_embeddings=build_embeddings)
    manifest["embedding_provider"] = {
        "name": "openai",
        "model": EMBEDDING_MODEL,
        "batch_size": EMBEDDING_BATCH_SIZE,
    }
    manifest["vector_store_status"] = {
        "backend": embedding_status.backend,
        "collection_name": embedding_status.collection_name,
        "embeddings_built": embedding_status.enabled,
        "embedding_dimensions": embedding_status.embedding_dimensions,
        "chunks_embedded": embedding_status.chunks_embedded,
        "chroma_path": str(CHROMA_DIR.relative_to(BASE_DIR)),
        "notes": embedding_status.notes,
        "error": embedding_status.error,
    }
    manifest["active_scope"] = {
        "roles": ["frontend_developer", "cross_role"],
        "roots": sorted(ACTIVE_KB_ROOTS),
        "role_notes": ["frontend_developer"],
        "vacancy_archetypes": ["frontend_*"],
    }
    write_json(MANIFEST_PATH, manifest)
    return manifest


if __name__ == "__main__":
    manifest = build_knowledge_base()
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
