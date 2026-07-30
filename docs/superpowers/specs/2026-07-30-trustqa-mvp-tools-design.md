# TrustQA MVP Tools Design

## Goal

Build three framework-independent Python tools under `src/tools`:

1. `detect_question_topics`
2. `search_qa_threads`
3. `get_qa_thread`

The tools operate on `data/discord_qa_mock.json`, expose explicit descriptions
and JSON-compatible input schemas, and can later be wrapped by an Agent SDK.

## Architecture

Each tool lives in its own folder and exports a validated Python function plus
a tool definition containing `name`, `description`, `input_schema`, and
`execute`. Shared code loads the corpus, calls OpenAI Embeddings, caches
embeddings locally, and calculates cosine similarity.

The default embedder uses `OPENAI_API_KEY` and
`OPENAI_EMBEDDING_MODEL`, defaulting to `text-embedding-3-small`. Tests inject
a deterministic fake embedder, so automated tests do not use network or API
credits.

## Tool Behavior

### detect_question_topics

- Build a fixed taxonomy from the corpus `topic_id` values.
- Build a profile for each topic from thread titles and questions.
- Embed the question and topic profiles.
- Return a primary topic, optional secondary topics, an intent inferred from
  the selected topic, and a normalized query.
- Return `other` with low confidence when no topic exceeds the configured
  threshold.

### search_qa_threads

- Embed `title + "\n" + question.content` for every thread.
- Embed the incoming query.
- Calculate `problem_similarity` using cosine similarity.
- Calculate `topic_similarity` using Jaccard similarity.
- Classify direct matches before applying source trust:
  - `problem_similarity >= 0.78`: direct match.
  - `0.40 <= problem_similarity < 0.78` and `topic_similarity >= 0.50`:
    topic reference.
- Source trust only breaks ties or orders similarly relevant results.
- Every displayed result includes a thread URL.
- Unsupported modes and malformed input fail validation; no match returns
  empty arrays.

### get_qa_thread

- Look up a thread by exact `thread_id`.
- Prefer the reply referenced by `trust`, then verified sources, then role and
  reaction count.
- Remove obvious non-answer noise and near-duplicate replies.
- Return at most two answers by default and three when explicitly requested.
- Use `reply.message_id` as `answer_id`.
- Missing threads fail closed with `THREAD_NOT_FOUND`.

## Storage and Cache

The source corpus remains read-only. Embeddings are cached under
`src/tools/.cache/embeddings.json`. The cache key includes the embedding model
and a SHA-256 digest of the input text, so changing either invalidates the
entry. Cache corruption is treated as an empty cache and never corrupts the
source data.

## Error Handling

- Pydantic validates tool inputs.
- Missing `OPENAI_API_KEY` produces a clear configuration error only when the
  default OpenAI embedder is used.
- Data loading errors identify the corpus path.
- Embedding shape errors fail closed instead of producing rankings.
- `get_qa_thread` never synthesizes missing thread or answer content.

## Testing

Pytest covers:

- topic detection and the `other` fallback;
- verified direct matches;
- community-only matches;
- topic references and empty results;
- search-mode filtering and validation;
- trusted answer selection, noise removal, answer limits, and missing threads;
- registry metadata and OpenAI embedder configuration errors.

