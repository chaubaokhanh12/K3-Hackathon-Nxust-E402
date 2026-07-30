# detect_question_topics

Phân tích câu hỏi của học viên trước khi tìm kiếm.

## Khi nào dùng

Luôn gọi đầu tiên khi nhận một câu hỏi mới liên quan đến nội dung khóa học.
Kết quả chỉ chọn topic từ các `topic_id` đang tồn tại trong corpus, không tự
sinh nhãn mới.

## Input

```json
{
  "question": "Em đã set API key nhưng Node vẫn báo Missing credentials."
}
```

## Output

```json
{
  "primary_topic": {
    "id": "api_key",
    "name": "API key",
    "confidence": 0.91
  },
  "subtopics": [],
  "intent": "TECHNICAL_ERROR",
  "normalized_query": "Em đã set API key nhưng Node vẫn báo Missing credentials."
}
```

Nếu không có topic đủ tin cậy, tool trả `primary_topic.id = "other"` và giữ
nguyên câu hỏi đã chuẩn hóa. Tool không tự loại bỏ câu hỏi.
