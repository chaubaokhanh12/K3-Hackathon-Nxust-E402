# get_qa_thread

Lấy nội dung đầy đủ của một thread và chọn các câu trả lời tốt nhất.

## Khi nào dùng

Gọi sau `search_qa_threads` và trước khi Agent tóm tắt hoặc kết luận từ một
thread. Không được tóm tắt nội dung chỉ từ kết quả search.

## Input

```json
{
  "thread_id": "1529643349835907072",
  "max_answers": 2
}
```

`max_answers` mặc định là `2` và chỉ nhận giá trị từ `1` đến `3`.

## Output thành công

```json
{
  "found": true,
  "thread_id": "1529643349835907072",
  "title": "Node không nhận API key",
  "question": "Node báo Missing credentials",
  "topics": ["api_key"],
  "selected_answers": [
    {
      "answer_id": "151...",
      "content": "Hãy mở terminal mới...",
      "author_name": "Minh | LabCoach",
      "author_role": "LabCoach",
      "is_verified": true,
      "is_accepted": true,
      "verification_label": "VERIFIED"
    }
  ],
  "verified_answer": true,
  "thread_url": "https://discord.com/channels/..."
}
```

## Fail-closed

```json
{
  "found": false,
  "error": "THREAD_NOT_FOUND",
  "thread_id": "unknown"
}
```

Tool không tự tạo nội dung khi thread hoặc answer không tồn tại.
