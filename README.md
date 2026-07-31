# Mini Hackathon AI — Batch 03 - NXUST

## VAI TRÒ PHỤ TRÁCH - FINAL

| Thành viên | Vai trò | Công việc phụ trách |
|------------|---------|---------------------|
| **Châu** | Leader / PM | Quản lý dự án, lập kế hoạch, xây dựng test cases, review toàn bộ hệ thống, cập nhật pipeline, tích hợp tool, kiểm định chất lượng, cập nhật các phiên bản Retrieval và LLM |
| **Bình An** | AI Engineer | Thiết kế System Prompts, xây dựng Prompt Guardrails và các cơ chế an toàn |
| **Khải** | AI Engineer / Business | Phát triển Tool, chuẩn bị Pitching, thực hiện khảo sát người dùng |
| **Tiến Đạt** | Data & Documentation | Thiết kế và triển khai bài khảo sát, thu thập dữ liệu từ Discord, chuẩn bị slide trình bày |
| **Hội Thắng** | UI/UX Designer | Thiết kế giao diện người dùng (UI/UX), thực hiện khảo sát người dùng |
| **Tâm** | Software Engineer | Tích hợp hệ thống (Integration), hỗ trợ kỹ thuật (IT Support), thu thập dữ liệu từ Discord |


## Chạy prototype DupBot đã tích hợp

Luồng hiện tại đã nối end-to-end:

```text
React UI → FastAPI → bot.answer()
         → detect_question_topics → search_qa_threads → get_qa_thread
         → guardrails → resolve/escalate → UI
```

### Cài đặt lần đầu

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src\tools\requirements.txt
Set-Location frontend
npm install
Set-Location ..
```

### Cấu hình API key (`.env`)

Để dùng OpenAI Embeddings thật, dán key vào file `.env` ở gốc repo:

```powershell
Copy-Item .env.example .env    # neu chua co
notepad .env                   # dan key vao dong OPENAI_API_KEY=
```

```dotenv
OPENAI_API_KEY=sk-...
```

`.env` **không được commit** (đã nằm trong `.gitignore`); `.env.example` là mẫu
để chia sẻ. File được nạp tự động khi import `bot.py` (xem `src/env_file.py`) nên
backend, `run_cases.py` và pytest đều thấy key — không cần set tay từng terminal.
Biến đã có sẵn trong terminal vẫn thắng file:

```powershell
$env:OPENAI_API_KEY = "..."    # tuy chon, de dan cho mot lan chay
```

Không có key (hoặc `OPENAI_API_KEY=` để trống), app vẫn chạy bằng fallback cục bộ
trên corpus để demo và hiển thị rõ chế độ này trong phản hồi
(`retrieval_mode = "local-corpus-fallback"`, kiểm tra nhanh ở `/api/health`).
Fallback không sinh câu trả lời mới; mọi trích đoạn vẫn lấy nguyên văn từ
`data/discord_qa_mock.json`. Đổi lại, nó **không làm được tìm kiếm diễn giải** —
đó là 10 case còn đỏ trong `eval/test_summary.md`.

### Chạy development

```powershell
.\start-dev.ps1
```

Script khởi động backend tại `http://127.0.0.1:8000`, frontend tại
`http://127.0.0.1:5173`, và tự dừng backend khi frontend dừng.

### Build/chạy một server

```powershell
Set-Location frontend
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn app:app --app-dir src --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`. API health ở `/api/health`, OpenAPI ở `/docs`.

### Kiểm tra

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest -q
Set-Location frontend
npm test
npm run build
```
