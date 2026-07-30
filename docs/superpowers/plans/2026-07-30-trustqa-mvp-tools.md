# TrustQA MVP Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build three independent Python Agent tools that classify topics,
retrieve semantically related Q&A threads, and return trusted thread details.

**Architecture:** Tool folders expose validated functions and Agent-ready
metadata. Shared modules own corpus access, embedding/cache behavior, and
similarity functions. OpenAI Embeddings is the production default while tests
inject deterministic vectors.

**Tech Stack:** Python 3.14, OpenAI Python SDK, Pydantic 2, pytest.

## Global Constraints

- Read only `data/discord_qa_mock.json`; never mutate the corpus.
- Read `OPENAI_API_KEY` only from the environment.
- Default to `text-embedding-3-small`.
- Keep each tool in its own folder with `description.md`.
- Always include source thread URLs in search/detail results.
- Do not let source trust turn an unrelated result into a direct match.
- Fail closed when data or evidence is missing.

---

### Task 1: Shared corpus and embedding infrastructure

**Files:**
- Create: `src/tools/_shared/repository.py`
- Create: `src/tools/_shared/embeddings.py`
- Create: `src/tools/_shared/similarity.py`
- Test: `src/tools/_shared/test_shared.py`

**Interfaces:**
- Produces: `CorpusRepository`, `Embedder`, `OpenAIEmbedder`,
  `CachedEmbedder`, `cosine_similarity`, and `jaccard_similarity`.

- [ ] Write tests that load the real corpus, reject missing API configuration,
  cache repeat embeddings, and calculate hand-checked similarities.
- [ ] Run the tests and verify they fail because shared modules do not exist.
- [ ] Implement the smallest shared modules satisfying the tests.
- [ ] Run the shared tests and confirm they pass.

### Task 2: Topic detection tool

**Files:**
- Create: `src/tools/detect_question_topics/__init__.py`
- Create: `src/tools/detect_question_topics/tool.py`
- Create: `src/tools/detect_question_topics/description.md`
- Test: `src/tools/detect_question_topics/test_tool.py`

**Interfaces:**
- Consumes: `CorpusRepository`, `Embedder`, and cosine similarity.
- Produces:
  `detect_question_topics(question: str, *, repository=None, embedder=None)
  -> dict` and `TOOL_DEFINITION`.

- [ ] Write tests for a known topic, secondary topics, invalid input, and the
  `other` fallback.
- [ ] Run the tests and verify they fail because the tool does not exist.
- [ ] Implement corpus-derived taxonomy profiles and intent mapping.
- [ ] Run the topic tool tests and confirm they pass.

### Task 3: Semantic thread search tool

**Files:**
- Create: `src/tools/search_qa_threads/__init__.py`
- Create: `src/tools/search_qa_threads/tool.py`
- Create: `src/tools/search_qa_threads/description.md`
- Test: `src/tools/search_qa_threads/test_tool.py`

**Interfaces:**
- Consumes: repository, embedder, cosine and Jaccard similarity.
- Produces:
  `search_qa_threads(query: str, topics: list[str], search_mode: str,
  top_k: int, *, repository=None, embedder=None) -> dict` and
  `TOOL_DEFINITION`.

- [ ] Write tests with hand-authored vectors for direct, topic, unrelated,
  verified/community ordering, modes, and validation.
- [ ] Run the tests and verify they fail because the tool does not exist.
- [ ] Implement classification before trust-aware ranking.
- [ ] Run search tests and confirm they pass.

### Task 4: Thread detail and answer selection tool

**Files:**
- Create: `src/tools/get_qa_thread/__init__.py`
- Create: `src/tools/get_qa_thread/tool.py`
- Create: `src/tools/get_qa_thread/description.md`
- Test: `src/tools/get_qa_thread/test_tool.py`

**Interfaces:**
- Consumes: `CorpusRepository`.
- Produces:
  `get_qa_thread(thread_id: str, max_answers: int = 2, *,
  repository=None) -> dict` and `TOOL_DEFINITION`.

- [ ] Write tests for trusted selection, community labels, noise filtering,
  answer limits, and `THREAD_NOT_FOUND`.
- [ ] Run the tests and verify they fail because the tool does not exist.
- [ ] Implement deterministic answer filtering and ranking.
- [ ] Run detail tests and confirm they pass.

### Task 5: Registry, descriptions, and full verification

**Files:**
- Create: `src/tools/__init__.py`
- Create: `src/tools/requirements.txt`
- Create: `src/tools/test_registry.py`

**Interfaces:**
- Produces: `TOOL_REGISTRY`, a list of the three tool definitions.

- [ ] Write a failing registry test for unique names, schemas, descriptions,
  and callables.
- [ ] Implement the registry and dependency list.
- [ ] Run all tests with
  `.venv/Scripts/python.exe -m pytest src/tools -v`.
- [ ] Run Python compilation over `src/tools`.
- [ ] Review the implementation against this plan and the approved design.

