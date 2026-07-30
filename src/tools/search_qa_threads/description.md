# search_qa_threads

Tìm thread bằng OpenAI semantic embeddings, topic và độ tin cậy của nguồn.

## Khi nào dùng

Gọi sau `detect_question_topics`. Truyền `normalized_query` làm `query` và các
topic đã phát hiện vào `topics`.

## Input

```json
{
  "query": "Node vẫn báo Missing credentials dù đã set API key",
  "topics": ["api_key"],
  "search_mode": "hybrid",
  "top_k": 5
}
```

`search_mode` nhận một trong:

- `direct`: chỉ trả thread cùng vấn đề;
- `topic`: chỉ trả tài liệu tham khảo cùng chủ đề;
- `hybrid`: trả cả hai nhóm.

## Output

```json
{
  "direct_matches": [
    {
      "thread_id": "152...",
      "title": "Node không nhận API key",
      "problem_similarity": 0.91,
      "topic_similarity": 1.0,
      "matched_topics": ["api_key"],
      "has_verified_answer": true,
      "source_trust": 0.95,
      "thread_url": "https://discord.com/channels/..."
    }
  ],
  "topic_matches": []
}
```

Tool phân loại mức độ liên quan trước, sau đó mới dùng độ tin cậy để xếp hạng
trong cùng nhóm. Topic reference không được dùng như câu trả lời trực tiếp.
