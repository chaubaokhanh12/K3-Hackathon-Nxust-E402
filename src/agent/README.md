# DupBot Agent — System Prompt & Guardrails (code)

Package này biến tài liệu `Bot_System_Instructions.md` thành **code chạy được**: System Prompt cho LLM + guardrail xác định. Không sửa `tools/` hay `frontend/`; chỉ tiêu thụ output của chúng qua JSON.

```
src/agent/
├── __init__.py          ← re-export API công khai
├── guardrails.py        ← logic quyết định + validator cứng (lấy ngưỡng từ tools)
├── system_prompt.py     ← SYSTEM_PROMPT + build_system_prompt() (inject ngưỡng thật)
├── test_guardrails.py
└── test_system_prompt.py
```

## 1. Vì sao tách riêng

LLM giỏi ngôn ngữ nhưng kém一致的 ở các quyết định **có quy tắc cứng**: "khi nào được phép trả gợi ý", "thread nào đứng trước", "khi nào sinh nút". Việc đó chuyển sang code (`guardrails.py`), lấy **ngưỡng thật từ `tools/*`** — đổi threshold một chỗ, cả prompt lẫn logic đều theo. LLM chỉ còn làm phần nó giỏi: chọn topic, viết văn案, tóm tắt.

## 2. Luồng tích hợp

```text
học viên hỏi
    │  (LLM, dùng SYSTEM_PROMPT)
    ▼
detect_question_topics → search_qa_threads → get_qa_thread(direct matches)
    │
    ▼
build_bot_response(search_result, thread_details)   ← guardrails.py
    │
    ▼
enforce(response)   ← raise GuardrailViolation nếu vi phạm
    │
    ▼
response.model_dump_json()  → frontend / Discord
```

## 3. Ví dụ dùng cùng TOOL_REGISTRY

```python
from tools import TOOL_REGISTRY
from agent import build_bot_response, enforce, SYSTEM_PROMPT

TOOLS_BY_NAME = {t["name"]: t for t in TOOL_REGISTRY}


def answer(question: str, status: str = "pending") -> dict:
    # 1) detect
    detected = TOOLS_BY_NAME["detect_question_topics"]["execute"](question=question)
    topics = [detected["primary_topic"]["id"], *[s["id"] for s in detected["subtopics"]]]

    # 2) search
    search = TOOLS_BY_NAME["search_qa_threads"]["execute"](
        query=detected["normalized_query"], topics=topics,
        search_mode="hybrid", top_k=5,
    )

    # 3) get_qa_thread cho từng direct match cần trích lời giải
    details = {}
    get = TOOLS_BY_NAME["get_qa_thread"]["execute"]
    for m in search["direct_matches"][:3]:
        d = get(thread_id=m["thread_id"], max_answers=2)
        if d.get("found"):
            details[m["thread_id"]] = d

    # 4) guardrail tổng hợp + validate
    response = build_bot_response(search, details, status=status)
    enforce(response)  # raise GuardrailViolation -> bot rơi về tin NONE an toàn
    return response.model_dump(mode="json")
```

Gửi `SYSTEM_PROMPT` (hoặc `build_system_prompt()`) làm system message cho LLM; `answer()` trả payload JSON map thẳng vào `BotMessage.jsx`.

## 4. Guardrail được mã hoá thành những gì

| Quy tắc (Bot_System_Instructions §B) | Code thực thi |
|---|---|
| G1: mọi claim phải có thread_id | `validate_no_fabrication` |
| G3/G7: link gốc bắt buộc | `validate_links_present` |
| §8/C.4: ≤1 chính + ≤1 bổ sung/thread | `validate_answer_limits` |
| B.2 (lỗi nặng nhất): NONE phải rỗng | `validate_none_is_empty` |
| §15.3: topic match không thành lời giải | `validate_topic_not_solution` |
| §5.3: thứ tự verified-direct > community > topic | `rank_for_display` |
| §6: tier HIGH/LOW/NONE theo verified | `decide_confidence` |
| §8: nút chỉ khi pending ∧ tier∈{HIGH,LOW} | `decide_buttons` |

## 5. Chạy test

```powershell
$env:PYTHONPATH = "src"
python -m pytest src/agent -q
```

Không cần `OPENAI_API_KEY` (test dùng dict mô phỏng output tool; import tool không gọi API).

## 6. Lưu ý

- Cần `PYTHONPATH=src` (giống `tools`).
- `build_bot_response` không gọi tool — nó chỉ xử lý output đã có. Việc gọi tool thuộc về adapter (mục 3).
- Khi `enforce` raise, **không** in payload lỗi: rơi về `BotResponse` tier NONE (tin "chưa có, đã chuyển LabCoach") để an toàn.
