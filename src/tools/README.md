# TrustQA MVP Tools

Ba Python tool độc lập phục vụ MVP TrustQA:

1. `detect_question_topics`: phát hiện topic và intent của câu hỏi.
2. `search_qa_threads`: tìm kiếm semantic, phân biệt direct match và topic
   reference.
3. `get_qa_thread`: đọc thread đầy đủ và chọn câu trả lời đáng tin cậy.

Các tool không phụ thuộc vào một Agent framework cụ thể. Có thể gọi trực tiếp
từ Python hoặc dùng `TOOL_REGISTRY` để viết adapter cho OpenAI Agents SDK,
LangGraph hay backend Agent khác.

## 1. Yêu cầu

- Python 3.11 trở lên.
- Một `OPENAI_API_KEY` có quyền gọi Embeddings API nếu sử dụng
  `detect_question_topics` hoặc `search_qa_threads`.
- Giữ nguyên cấu trúc project để tool tìm được file
  `data/discord_qa_mock.json`.

Phiên bản đã được kiểm tra trong project:

- Python 3.14.2
- `openai>=2.50,<3`
- `pydantic>=2.13,<3`
- `pytest>=9,<10`

## 2. Cài đặt

Chạy các lệnh từ thư mục gốc của project
`DAY05_MiniHackathon__Nxust`.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r src/tools/requirements.txt
```

Nếu máy có nhiều phiên bản Python, có thể dùng launcher:

```powershell
py -3.11 -m venv .venv
```

### macOS hoặc Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r src/tools/requirements.txt
```

## 3. Cấu hình biến môi trường

Không ghi API key trực tiếp vào source code và không commit key lên Git.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
$env:PYTHONPATH = "src"
```

### macOS hoặc Linux

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
export PYTHONPATH="src"
```

`OPENAI_EMBEDDING_MODEL` là tùy chọn. Nếu không thiết lập, tool dùng
`text-embedding-3-small`.

Các module trong folder này không tự đọc file `.env`. Backend hoặc Agent
runtime phải nạp `.env` trước khi gọi tool nếu project chọn quản lý biến môi
trường bằng file đó.

## 4. Luồng sử dụng đề xuất

```text
Câu hỏi của học viên
        ↓
detect_question_topics
        ↓
search_qa_threads
        ↓
get_qa_thread cho các kết quả cần đọc
        ↓
Agent tổng hợp câu trả lời và dẫn link nguồn
```

Không dùng `topic_matches` như câu trả lời trực tiếp. Agent chỉ nên dùng nhóm
này làm tài liệu tham khảo cùng chủ đề.

## 5. Gọi trực tiếp từ Python

Ví dụ hoàn chỉnh:

```python
from tools.detect_question_topics import detect_question_topics
from tools.get_qa_thread import get_qa_thread
from tools.search_qa_threads import search_qa_threads


question = "Em đã set API key nhưng Node vẫn báo Missing credentials."

detected = detect_question_topics(question)

topics = [
    detected["primary_topic"]["id"],
    *[topic["id"] for topic in detected["subtopics"]],
]

search_result = search_qa_threads(
    query=detected["normalized_query"],
    topics=topics,
    search_mode="hybrid",
    top_k=3,
)

if search_result["direct_matches"]:
    best_match = search_result["direct_matches"][0]
    thread = get_qa_thread(
        thread_id=best_match["thread_id"],
        max_answers=2,
    )
    print(thread)
else:
    print("Chưa tìm thấy câu trả lời trực tiếp đủ tin cậy.")
    print(search_result["topic_matches"])
```

Hai tool đầu gọi OpenAI Embeddings khi vector chưa có trong cache.
`get_qa_thread` chỉ đọc JSON cục bộ nên không cần API key.

## 6. Dùng tool registry để nối Agent

`tools.TOOL_REGISTRY` chứa metadata và hàm thực thi của cả ba tool:

```python
from tools import TOOL_REGISTRY


for tool in TOOL_REGISTRY:
    print(tool["name"])
    print(tool["description"])
    print(tool["input_schema"])
```

Mỗi phần tử có dạng:

```python
{
    "name": "search_qa_threads",
    "description": "Mô tả để Agent biết khi nào gọi tool",
    "input_schema": {"type": "object", "...": "..."},
    "execute": search_qa_threads,
}
```

Một dispatcher tối giản cho Agent backend:

```python
from typing import Any

from tools import TOOL_REGISTRY


TOOLS_BY_NAME = {tool["name"]: tool for tool in TOOL_REGISTRY}


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        raise ValueError(f"Unknown TrustQA tool: {name}")
    return tool["execute"](**arguments)
```

Agent adapter cần gửi ba trường `name`, `description`, `input_schema` cho
model. Khi model yêu cầu gọi tool, adapter chuyển arguments vào
`execute_tool`. Frontend không import các Python function này trực tiếp;
frontend gọi Agent backend, sau đó backend thực thi tool.

## 7. Contract của từng tool

### detect_question_topics

Input:

```json
{
  "question": "Em đã set API key nhưng Node vẫn báo Missing credentials."
}
```

Output chính:

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

Nếu không tìm được topic đủ mạnh, tool trả `primary_topic.id = "other"`.

### search_qa_threads

Input:

```json
{
  "query": "Node báo Missing credentials dù đã set API key",
  "topics": ["api_key"],
  "search_mode": "hybrid",
  "top_k": 5
}
```

Các `search_mode`:

- `direct`: chỉ trả direct match;
- `topic`: chỉ trả topic reference;
- `hybrid`: trả cả hai nhóm.

Output:

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

### get_qa_thread

Input:

```json
{
  "thread_id": "1529643349835907072",
  "max_answers": 2
}
```

Output chính:

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

Nếu thread không tồn tại:

```json
{
  "found": false,
  "error": "THREAD_NOT_FOUND",
  "thread_id": "unknown"
}
```

## 8. Embedding cache

Vector được lưu tại:

```text
src/tools/.cache/embeddings.json
```

Folder cache đã được git-ignore. Cache key chứa embedding model và SHA-256 của
text:

- query giống nhau không phải gọi API lại;
- thay model tự tạo cache key mới;
- thay nội dung thread tự tạo cache key mới;
- cache hỏng được bỏ qua theo cơ chế fail-closed.

Có thể xóa `src/tools/.cache` để index lại toàn bộ corpus. Việc này không xóa
data nguồn.

## 9. Chạy test

### Windows PowerShell

```powershell
$env:PYTHONPATH = "src"
python -m pytest src/tools -q
```

### macOS hoặc Linux

```bash
PYTHONPATH=src python -m pytest src/tools -q
```

Bộ test dùng fake embedder nên:

- không cần API key;
- không gửi corpus ra ngoài;
- không phát sinh chi phí API.

Kiểm tra compile:

```powershell
python -m compileall -q src/tools
```

## 10. Cấu trúc folder

```text
src/tools/
├── _shared/
│   ├── embeddings.py
│   ├── repository.py
│   └── similarity.py
├── detect_question_topics/
│   ├── tool.py
│   ├── description.md
│   └── test_tool.py
├── search_qa_threads/
│   ├── tool.py
│   ├── description.md
│   └── test_tool.py
├── get_qa_thread/
│   ├── tool.py
│   ├── description.md
│   └── test_tool.py
├── __init__.py
├── README.md
└── requirements.txt
```

## 11. Lỗi thường gặp

### `ModuleNotFoundError: No module named 'tools'`

Chạy lệnh từ project root và thiết lập:

```powershell
$env:PYTHONPATH = "src"
```

### `OPENAI_API_KEY is required`

Thiết lập API key trong cùng terminal/process chạy Agent:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

### `THREAD_NOT_FOUND`

Kiểm tra `thread_id` lấy từ kết quả của `search_qa_threads`. Tool chỉ chấp
nhận ID tồn tại chính xác và không tự tạo nội dung thay thế.

### Kết quả semantic thay đổi sau khi đổi model

Xóa `src/tools/.cache`, chạy lại benchmark và hiệu chỉnh các threshold nếu
cần. Không giả định threshold của một embedding model sẽ phù hợp hoàn toàn
với model khác.

## 12. Lưu ý dữ liệu

Hai tool embedding gửi phần text cần thiết tới API khi cache chưa có. Chỉ chạy
với corpus được phép gửi tới nhà cung cấp API. Không in API key, không commit
file `.env`, và không ghi nội dung bí mật vào log.
