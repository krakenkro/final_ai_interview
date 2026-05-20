import json
from typing import Dict, List, Optional, Sequence

from backend.observability.langsmith import traceable
from backend.services.rag_ingestion import (
    BASE_DIR,
    CHUNKS_PATH,
    CHROMA_COLLECTION_NAME,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    build_knowledge_base,
    get_chroma_collection,
    get_openai_client,
    tokenize,
)


_CHUNK_CACHE: Optional[List[Dict[str, object]]] = None


def _load_chunks() -> List[Dict[str, object]]:
    global _CHUNK_CACHE
    if _CHUNK_CACHE is not None:
        return _CHUNK_CACHE

    if not CHUNKS_PATH.exists():
        build_knowledge_base()

    if not CHUNKS_PATH.exists():
        _CHUNK_CACHE = []
        return _CHUNK_CACHE

    chunks: List[Dict[str, object]] = []
    with CHUNKS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    _CHUNK_CACHE = chunks
    return chunks


def _match_filters(
    chunk: Dict[str, object],
    layer: Optional[str],
    role: Optional[str],
    seniority: Optional[str],
    interview_type: Optional[str],
    document_types: Optional[Sequence[str]],
) -> bool:
    if layer and chunk.get("layer") != layer:
        return False
    if role and chunk.get("role") != role.lower():
        return False
    if seniority and seniority.lower() not in chunk.get("seniority", []):
        return False
    if interview_type and interview_type.lower() not in chunk.get("interview_type", []):
        return False
    if document_types:
        allowed = {document_type.lower() for document_type in document_types}
        if str(chunk.get("document_type", "")).lower() not in allowed:
            return False
    return True


def _score_chunk(query_tokens: Sequence[str], chunk: Dict[str, object]) -> float:
    chunk_text = str(chunk.get("text", ""))
    chunk_tokens = tokenize(chunk_text)
    if not chunk_tokens:
        return 0.0

    overlap = set(query_tokens) & set(chunk_tokens)
    score = float(len(overlap))

    topic = str(chunk.get("topic", ""))
    section = str(chunk.get("section", ""))
    title = str(chunk.get("title", ""))
    haystack = " ".join([topic, section, title]).lower()
    for token in query_tokens:
        if token in haystack:
            score += 1.5

    if chunk.get("layer") == "processed":
        score += 0.25

    return score


def _to_result(chunk: Dict[str, object], score: float, *, source: str) -> Dict[str, object]:
    return {
        "chunk_id": chunk.get("chunk_id"),
        "document_id": chunk.get("document_id"),
        "path": chunk.get("path"),
        "title": chunk.get("title"),
        "section": chunk.get("section"),
        "topic": chunk.get("topic"),
        "document_type": chunk.get("document_type"),
        "role": chunk.get("role"),
        "seniority": chunk.get("seniority"),
        "interview_type": chunk.get("interview_type"),
        "score": score,
        "retrieval_backend": source,
        "text": chunk.get("text"),
    }


def _build_where_clause(
    *,
    layer: Optional[str],
    role: Optional[str],
    seniority: Optional[str],
    interview_type: Optional[str],
    document_types: Optional[Sequence[str]],
) -> Optional[Dict[str, object]]:
    clauses: List[Dict[str, object]] = []
    if layer:
        clauses.append({"layer": layer})
    if role:
        clauses.append({"role": role.lower()})
    if seniority:
        clauses.append({f"seniority_{seniority.lower()}": True})
    if interview_type:
        clauses.append({f"interview_type_{interview_type.lower()}": True})
    if document_types:
        values = [document_type.lower() for document_type in document_types]
        if len(values) == 1:
            clauses.append({"document_type": values[0]})
        else:
            clauses.append({"$or": [{"document_type": value} for value in values]})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _retrieve_vector_context(
    topic: str,
    top_k: int,
    *,
    role: Optional[str],
    seniority: Optional[str],
    interview_type: Optional[str],
    document_types: Optional[Sequence[str]],
    layer: Optional[str],
) -> List[Dict[str, object]]:
    client = get_openai_client()
    _, collection = get_chroma_collection()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[topic],
    )
    query_embedding = response.data[0].embedding
    where = _build_where_clause(
        layer=layer,
        role=role,
        seniority=seniority,
        interview_type=interview_type,
        document_types=document_types,
    )

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(top_k, 10),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    metadatas = result.get("metadatas", [[]])[0]
    documents = result.get("documents", [[]])[0]
    distances = result.get("distances", [[]])[0]

    entries: List[Dict[str, object]] = []
    for metadata, document, distance in zip(metadatas, documents, distances):
        seniority_values = str(metadata.get("seniority_csv", "")).split(",") if metadata.get("seniority_csv") else []
        interview_type_values = (
            str(metadata.get("interview_type_csv", "")).split(",") if metadata.get("interview_type_csv") else []
        )
        entries.append(
            {
                "chunk_id": metadata.get("chunk_id"),
                "document_id": metadata.get("document_id"),
                "path": metadata.get("path"),
                "title": metadata.get("title"),
                "section": metadata.get("section"),
                "topic": metadata.get("topic"),
                "document_type": metadata.get("document_type"),
                "role": metadata.get("role"),
                "seniority": [value for value in seniority_values if value],
                "interview_type": [value for value in interview_type_values if value],
                "text": document,
                "distance": float(distance),
            }
        )

    entries.sort(key=lambda item: (item["distance"], str(item.get("chunk_id", ""))))
    return [_to_result(entry, 1.0 - min(float(entry["distance"]), 1.0), source="chroma_openai") for entry in entries[:top_k]]


def _retrieve_lexical_context(
    topic: str,
    top_k: int,
    *,
    role: Optional[str],
    seniority: Optional[str],
    interview_type: Optional[str],
    document_types: Optional[Sequence[str]],
    layer: Optional[str],
) -> List[Dict[str, object]]:
    query_tokens = tokenize(topic)
    chunks = _load_chunks()

    scored: List[tuple[float, Dict[str, object]]] = []
    for chunk in chunks:
        if not _match_filters(
            chunk=chunk,
            layer=layer,
            role=role,
            seniority=seniority,
            interview_type=interview_type,
            document_types=document_types,
        ):
            continue
        score = _score_chunk(query_tokens, chunk)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: (-item[0], str(item[1].get("chunk_id", ""))))
    return [_to_result(chunk, score, source="jsonl_lexical") for score, chunk in scored[:top_k]]


@traceable(run_type="retriever", name="retrieve_context")
def retrieve_context(
    topic: str,
    top_k: int = 5,
    *,
    role: Optional[str] = None,
    seniority: Optional[str] = None,
    interview_type: Optional[str] = None,
    document_types: Optional[Sequence[str]] = None,
    layer: str = "processed",
) -> List[Dict[str, object]]:
    chunks = _load_chunks()

    if not chunks:
        return [
            {
                "topic": topic,
                "status": "index_missing",
                "message": "Knowledge base chunks are missing. Run `python -m backend.services.rag_ingestion` first.",
            }
        ]

    try:
        if CHROMA_DIR.exists():
            results = _retrieve_vector_context(
                topic,
                top_k,
                role=role,
                seniority=seniority,
                interview_type=interview_type,
                document_types=document_types,
                layer=layer,
            )
            if results:
                return results
    except Exception:
        pass

    results = _retrieve_lexical_context(
        topic,
        top_k,
        role=role,
        seniority=seniority,
        interview_type=interview_type,
        document_types=document_types,
        layer=layer,
    )
    if results:
        return results

    return [
        {
            "topic": topic,
            "status": "no_match",
            "message": f"No retrieval chunks matched `{topic}` in layer `{layer}`.",
            "chunks_path": str(CHUNKS_PATH.relative_to(BASE_DIR)),
            "vector_collection": CHROMA_COLLECTION_NAME,
        }
    ]
