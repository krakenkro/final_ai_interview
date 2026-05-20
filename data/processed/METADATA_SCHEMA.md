# Processed Metadata Schema

This note documents the metadata schema currently used in `data/processed/`.

## Actual processed fields

- `topic`
- `role`
- `seniority`
- `interview_type`
- `document_type`
- `source_url`
- `source_language`
- `normalized_language`
- `normalized_on`

## Relation to raw schema

`data/raw/` keeps a more source-oriented header:

- `Topic`
- `Role`
- `Seniority`
- `Interview Type`
- `Document Type`
- `Source URL`
- `Language`
- `Collected On`

## Ingestion implication

The ingestion pipeline should not assume the raw and processed headers are identical.

- For `raw`, parse source metadata as-is.
- For `processed`, parse the normalized snake_case fields above.
- If a unified internal schema is needed, map both formats into one canonical object before chunking.
