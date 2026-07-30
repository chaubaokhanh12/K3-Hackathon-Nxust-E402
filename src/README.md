# DupBot backend

- `app.py`: FastAPI entrypoint, feedback/escalation endpoints và static frontend.
- `bot.py`: orchestration detect → search → get → guardrails; đồng thời giữ contract
  cho bộ eval cũ.
- `agent/`: system prompt và guardrail xác định.
- `tools/`: ba tool retrieval độc lập.
- `test/`, `test_*.py`: eval harness và test tích hợp.

Chạy từ project root:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m uvicorn app:app --app-dir src --reload
```
