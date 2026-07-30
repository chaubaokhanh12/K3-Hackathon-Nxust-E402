# Claude_Working_Log.md

> **Tài liệu/Log này được thiết kế để đọc và phân tích bởi AI Agent.**

Tài liệu ghi nhận quá trình tư duy và thực thi của Claude (Kiến trúc sư Hệ thống AI) trong phiên thiết kế System Prompt cho DupBot (TrustQA). Mọi khối nội dung đều có mã định danh và dấu thời gian để agent khác parse tuần tự hoặc tra theo phase.

- **Định dạng chính:** Markdown có cấu trúc chặt + khối JSON (machine-readable) nhúng sau mỗi giai đoạn. Agent parse ưu tiên khối `<json>`; phần Markdown là lớp dành cho người đọc.
- **Quy ước mã:** `SESSION-<yyyymmdd-hhmm>`, `PHASE-<n>`, `STEP-<n>.<n>`, `CR-<n>` (Change Request), `ART-<n>` (Artifact).
- **Múi giờ:** Timestamp theo `Asia/Ho_Chi_Minh` (UTC+7) khi có ghi giờ; ngày theo ISO `YYYY-MM-DD`.

---

## 0. Thẻ phiên (Session Header)

```json
{
  "session_id": "SESSION-20260730-1430",
  "started_at": "2026-07-30T14:30:00+07:00",
  "agent_role": "Senior AI System Architect & Prompt Engineer",
  "model_self_reported": "glm-5.1",
  "effort_mode": "high",
  "working_directory": "D:\\VinAI\\K3\\K3-Hackathon-Nxust-E402",
  "git_branch": "main",
  "language": "vi-VN",
  "objective": "Thiết kế System Prompt + Guardrail cho DupBot (Discord) và ghi log phiên, KHÔNG sửa code hiện có.",
  "deliverables": [
    { "id": "ART-1", "path": "Bot_System_Instructions.md", "type": "system_prompt" },
    { "id": "ART-2", "path": "Claude_Working_Log.md", "type": "process_log" }
  ],
  "constraints": [
    "Không chỉnh sửa code hiện có trong src/tools/* và frontend.",
    "Bám sát đặc tả src/tools/trustqa_agent_tool_spec.txt.",
    "Ngưỡng trong prompt phải khớp giá trị thực trong tool.py, không bịa số."
  ],
  "status": "COMPLETED",
  "completed_at": "2026-07-30T14:46:00+07:00"
}
```

---

## 1. Đăng ký Change Request (CR Register)

> Phần này tập hợp **mọi yêu cầu thay đổi / chế độ làm việc** được áp dụng cho agent trong phiên. Mỗi CR có trạng thái để agent theo dõi. *(caveman / get-shit-done trong yêu cầu chỉ là ví dụ minh hoạ cho khái niệm CR, bản thân phiên này không áp dụng hai chế độ đó.)*

```json
{
  "change_requests": [
    {
      "id": "CR-1",
      "title": "Effort level = high",
      "source": "lệnh /effort (system)",
      "applied_at": "2026-07-30T14:30:00+07:00",
      "description": "Yêu cầu triển khai đầy đủ: tài liệu chi tiết, kiểm tra ngưỡng đối chiếu code, kịch bản ví dụ. KHÔNG cắt xén.",
      "impact_on_output": "File System Prompt dài, có phụ lục + few-shot; log có nhiều khối JSON.",
      "status": "ACTIVE"
    },
    {
      "id": "CR-2",
      "title": "Model = glm-5.1",
      "source": "lệnh /model (system)",
      "applied_at": "2026-07-30T14:30:00+07:00",
      "description": "Đặt model mặc định cho phiên.",
      "impact_on_output": "Không thay đổi cấu trúc; chỉ ghi nhận metadata.",
      "status": "ACTIVE"
    },
    {
      "id": "CR-3",
      "title": "No-code constraint (chỉ viết tài liệu)",
      "source": "người dùng (nhiệm vụ 1)",
      "applied_at": "2026-07-30T14:30:00+07:00",
      "description": "Tuyệt đối không sửa code đã hiện có. Chỉ tạo 2 file tài liệu mới.",
      "impact_on_output": "Không dùng Edit/Write lên bất kỳ file src/ hay frontend/ nào. Chỉ tạo 2 file mới ở root.",
      "status": "ACTIVE",
      "compliance_check": "PASSED — không có lệnh ghi nào trỏ vào src/ hoặc frontend/."
    },
    {
      "id": "CR-4",
      "title": "Chế độ làm việc: get-shit-done nhẹ (đi thẳng giải pháp)",
      "source": "suy luận agent dựa trên yêu cầu 'làm ngay lập tức'",
      "applied_at": "2026-07-30T14:31:00+07:00",
      "description": "Không hỏi lại clarifying question khi đã đủ ngữ cảnh từ corpus; ưu tiên hành động. Vẫn giữ effort=high nên không phải caveman (nói ít) — output vẫn đầy đủ.",
      "impact_on_output": "Bỏ qua bước hỏi xác nhận, tiến thẳng khảo sát → viết. Chỉ dùng AskUserQuestion nếu gặp ngã rẽ thật sự (không xảy ra).",
      "status": "ACTIVE"
    }
  ],
  "note": "Phiên KHÔNG chạy ở caveman mode (output vẫn đầy đủ, không 'nói ít'). Phiên CHẠY ở biến thể nhẹ của get-shit-done: vào thẳng khảo sát song song, không preamble."
}
```

---

## 2. Lịch sử Phase (Phase Timeline)

> Mỗi phase = một cụm công việc logic. Trong phase có nhiều `STEP`. Mỗi phase kết thúc bằng một khối JSON tóm tắt (`phase_summary`) để agent rút dữ liệu nhanh.

### PHASE-1 · Đọc và phân tích Tools & luồng dự án
*Bắt đầu: 14:30 · Kết thúc: 14:36*

- **STEP-1.1** Đọc `README.md` + liệt kê cây file (`find`) → nắm phạm vi hackathon, cấu trúc repo, danh sách tool.
- **STEP-1.2** Đọc 3 đặc tả gốc: `src/tools/README.md`, `trustqa_agent_tool_spec.txt` (§1–§18, đặc biệt §15), `data/SCHEMA.md`.
- **STEP-1.3** Đọc code thực của 3 tool để lấy **ngưỡng thật** (không lấy số từ spec chung):
  - `detect_question_topics/tool.py`: `PRIMARY_TOPIC_THRESHOLD=0.35`, `SUBTOPIC_THRESHOLD=0.45`, taxonomy 25 topic_id.
  - `search_qa_threads/tool.py`: `DIRECT_MATCH_THRESHOLD=0.78`, topic ref `0.40–0.78 ∧ ≥0.50`, `ROLE_TRUST` {Admin/Mentor/BTC=1.0, LabCoach=0.95, Learner=0.40}, ranking `(-problem_similarity, -source_trust, thread_id)`.
  - `get_qa_thread/tool.py`: `max_answers` 1–3 default 2, `ROLE_PRIORITY` Admin5/Mentor4/BTC4/LabCoach3/Learner1, noise removal, fail-closed `THREAD_NOT_FOUND`.
- **STEP-1.4** Đọc giao diện: `BotMessage.jsx` (3 tier confidence HIGH/LOW/NONE + headline/note + 2 nút `Đã giải quyết được`/`Chưa đúng ý tôi`), `SimilarThreadCard.jsx` (cấu trúc thẻ: rank, thanh similarity, excerpt, answeredBy, link), `dupbotService.js` (`markThreadResolved`, `escalateToLabCoach` SLA 25p, `postMessage`).
- **STEP-1.5** Đọc `semanticSearch.js` (frontend mock) + design spec → xác nhận mock dùng concept-set khác ngưỡng thật; prompt production phải neo vào tool Python, không phải mock JS.

```json
{
  "phase_id": "PHASE-1",
  "name": "Đọc và phân tích Tools & luồng dự án",
  "started_at": "2026-07-30T14:30:00+07:00",
  "ended_at": "2026-07-30T14:36:00+07:00",
  "files_read": [
    "README.md", "data/SCHEMA.md", "src/README.md",
    "src/tools/README.md", "src/tools/trustqa_agent_tool_spec.txt",
    "src/tools/detect_question_topics/description.md", "src/tools/detect_question_topics/tool.py",
    "src/tools/search_qa_threads/description.md", "src/tools/search_qa_threads/tool.py",
    "src/tools/get_qa_thread/description.md", "src/tools/get_qa_thread/tool.py",
    "frontend/src/components/BotMessage.jsx",
    "frontend/src/components/SimilarThreadCard.jsx",
    "frontend/src/services/dupbotService.js",
    "frontend/src/lib/semanticSearch.js",
    "frontend/src/App.jsx",
    "docs/superpowers/specs/2026-07-30-trustqa-mvp-tools-design.md"
  ],
  "key_findings": {
    "core_pipeline": ["detect_question_topics", "search_qa_threads", "get_qa_thread"],
    "real_thresholds": {
      "primary_topic": 0.35,
      "direct_match": 0.78,
      "topic_ref_problem_floor": 0.40,
      "topic_ref_topic_floor": 0.50
    },
    "source_trust_map": { "Admin": 1.0, "Mentor": 1.0, "BTC": 1.0, "LabCoach": 0.95, "Learner_verified": 0.85, "Learner_unverified": 0.40 },
    "ui_tiers": ["HIGH", "LOW", "NONE"],
    "ui_buttons": ["Đã giải quyết được (markThreadResolved)", "Chưa đúng ý tôi (escalateToLabCoach)"],
    "critical_rule": "Tier NONE bắt buộc nói 'không biết' + tự escalate; trả gợi ý = lỗi nặng nhất (nhóm khong_co_dap_an trong benchmark)."
  },
  "learning": "Spec §15 là bộ nguyên tắc System Prompt sẵn — không cần sáng tạo, cần hệ thống hoá và đối chiếu số liệu thật trong code để tránh lệch ngưỡng."
}
```

### PHASE-2 · Thiết kế workflow & Persona
*Bắt đầu: 14:36 · Kết thúc: 14:40*

- **STEP-2.1** Định nghĩa persona DupBot: triage agent, tiếng Việt, xưng "mình"/"bạn", ngắn gọn, trung thực về độ chắc chắn, không giảng bài.
- **STEP-2.2** Mô hình hoá đường ống tool như **dòng chảy bắt buộc** (đường ống, không thực đơn) với bảng "khi nào gọi / khi nào bỏ qua" cho từng tool.
- **STEP-2.3** Ánh xạ 3 tier confidence (HIGH/LOW/NONE) sang **điều kiện dựa trên tool thực** + headline/note đồng bộ `BotMessage.jsx`.
- **STEP-2.4** Quyết định logic sinh 2 nút: chỉ khi `status=pending` ∧ tier ∈ {HIGH,LOW}; **không** sinh nút khi NONE (đã tự escalate).

```json
{
  "phase_id": "PHASE-2",
  "name": "Thiết kế workflow & Persona",
  "started_at": "2026-07-30T14:36:00+07:00",
  "ended_at": "2026-07-30T14:40:00+07:00",
  "design_decisions": [
    { "id": "DD-1", "topic": "Persona", "decision": "DupBot = triage agent, không phải tri thức chung; chỉ nói có bằng chứng." },
    { "id": "DD-2", "topic": "Tool pipeline", "decision": "detect → search(hybrid) → get_qa_thread; nhánh quyết định theo direct/topic rỗng." },
    { "id": "DD-3", "topic": "Confidence mapping", "decision": "HIGH=có direct+verified; LOW=direct unverified hoặc chỉ topic; NONE=hai nhóm rỗng." },
    { "id": "DD-4", "topic": "Button logic", "decision": "Sinh 2 nút iff pending ∧ (HIGH|LOW). NONE không nút." }
  ],
  "learning": "Gắn confidence vào cờ has_verified_answer của direct match trực tiếp hơn là dùng ngưỡng số tùy ý — giảm rủi ro lệch khi đổi embedding model."
}
```

### PHASE-3 · Viết Bot_System_Instructions.md (ART-1)
*Bắt đầu: 14:40 · Kết thúc: 14:43*

- **STEP-3.1** Tạo `Bot_System_Instructions.md` với 4 phần: A. Persona & Workflow | B. Strict Guardrails | C. Phụ lục tích hợp | D. Kịch bản few-shot.
- **STEP-3.2** Khối System Prompt được đóng khối `(BẮT ĐẦU)/(KẾT THÚC)` để copy-paste dễ; phần C/D tách riêng để khi eo hẹp token có thể bỏ.
- **STEP-3.3** Đối chiếu từng con số trong bảng ngưỡng (C.2) với code thật — không dùng số ước lượng.

```json
{
  "phase_id": "PHASE-3",
  "name": "Viết Bot_System_Instructions.md",
  "started_at": "2026-07-30T14:40:00+07:00",
  "ended_at": "2026-07-30T14:43:00+07:00",
  "artifact": "ART-1",
  "output_file": "Bot_System_Instructions.md",
  "structure": [
    "A. Persona & Workflow (10 mục)",
    "B. Strict Guardrails (B.1–B.5: anti-hallucination, fallback matrix, source labeling, limits, security)",
    "C. Phụ lục (contract tool, bảng ngưỡng, phân tầng nguồn, bảng tra nhanh)",
    "D. 3 kịch bản few-shot (HIGH / LOW / NONE)"
  ],
  "compliance": {
    "no_code_modified": true,
    "thresholds_verified_against_code": true,
    "spec_section_15_covered": true
  },
  "learning": "Đặt bảng tra nhanh C.4 ở cuối phần phụ lục — đó là phần agent adapter thực tế sẽ dùng nhiều nhất; giữ gọn 1 khối text."
}
```

### PHASE-4 · Tạo Claude_Working_Log.md (ART-2, chính file này)
*Bắt đầu: 14:43 · Kết thúc: 14:46*

- **STEP-4.1** Thiết kế cấu trúc machine-readable: Session Header (JSON) → CR Register (JSON) → Phase Timeline (Markdown + JSON sau mỗi phase).
- **STEP-4.2** Ghi dòng thông báo bắt buộc ở ngay đầu file (theo yêu cầu).
- **STEP-4.3** Đăng ký 4 CR (effort, model, no-code, get-shit-done nhẹ), phân biệt rõ KHÔNG chạy caveman.

```json
{
  "phase_id": "PHASE-4",
  "name": "Tạo Claude_Working_Log.md",
  "started_at": "2026-07-30T14:43:00+07:00",
  "ended_at": "2026-07-30T14:46:00+07:00",
  "artifact": "ART-2",
  "output_file": "Claude_Working_Log.md",
  "mandatory_notice_present": true,
  "notice_text": "Tài liệu/Log này được thiết kế để đọc và phân tích bởi AI Agent.",
  "machine_readable_format": "JSON blocks embedded in structured Markdown",
  "grouping_keys": ["Session_ID", "Timestamp", "Phase", "Step"],
  "learning": "Đặt JSON summary SAU mỗi phase (không chỉ ở cuối) giúp agent parse chọn lọc — có thể chỉ đọc phase quan tâm mà không quét toàn file."
}
```

---

## 3. Bài học rút ra (Cross-phase learnings)

```json
{
  "session_learnings": [
    {
      "id": "L-1",
      "phase_origin": ["PHASE-1", "PHASE-3"],
      "lesson": "Luôn lấy ngưỡng từ code thực (tool.py), không từ đặc tả chung — đặc tả có thể dùng số ví dụ.",
      "how_applied": "Đối chiếu DIRECT_MATCH_THRESHOLD=0.78 v.v. trước khi viết bảng C.2."
    },
    {
      "id": "L-2",
      "phase_origin": ["PHASE-2"],
      "lesson": "Neo confidence vào cờ cấu trúc (has_verified_answer) thay vì ngưỡng số — chịu được việc đổi embedding model.",
      "how_applied": "HIGH = có direct match verified; không phụ thuộc cosine tuyệt đối."
    },
    {
      "id": "L-3",
      "phase_origin": ["PHASE-1"],
      "lesson": "Benchmark có nhóm khong_co_dap_an — 'biết nói không biết' là metric quan trọng nhất, không phải precision.",
      "how_applied": "Guardrail B.2 đánh dấu trả gợi ý sai ở NONE là 'lỗi nặng nhất'."
    },
    {
      "id": "L-4",
      "phase_origin": ["PHASE-4"],
      "lesson": "Log machine-readable nên có JSON SAU mỗi phase, không gộp cuối file — agent parse từng phần hiệu quả hơn.",
      "how_applied": "Mỗi phase có phase_summary JSON riêng."
    }
  ]
}
```

---

## 4. Trạng thái cuối phiên (Session Closeout)

```json
{
  "session_id": "SESSION-20260730-1430",
  "final_status": "COMPLETED",
  "artifacts_produced": [
    { "id": "ART-1", "path": "Bot_System_Instructions.md", "created": true, "verified": true },
    { "id": "ART-2", "path": "Claude_Working_Log.md", "created": true, "verified": true }
  ],
  "code_modified": false,
  "open_risks": [
    {
      "risk": "Frontend mock (semanticSearch.js) dùng ngưỡng khác tool Python; nếu demo chạy mock thì tier có thể lệch.",
      "mitigation": "Prompt production neo vào tool Python; ghi chú trong prompt phần C.2."
    },
    {
      "risk": "create_question_draft / verify_community_answer chưa có trong MVP — prompt chỉ nhắc, không triển khai.",
      "mitigation": "Phần §9 và guardrail nêu rõ 'chỉ sau xác nhận'."
    }
  ],
  "next_session_hooks": [
    "Nếu build backend Agent thật: dùng TOOL_REGISTRY + dispatcher (xem src/tools/README.md §6) nối 3 tool.",
    "Khi tinh chỉnh ngưỡng: chạy benchmark test_queries trong data, cập nhật cả tool.py và bảng C.2 đồng bộ."
  ],
  "completed_at": "2026-07-30T14:46:00+07:00"
}
```

---

*Hết log phiên `SESSION-20260730-1430`.*
