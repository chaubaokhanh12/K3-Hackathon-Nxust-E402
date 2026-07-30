"""Nạp biến môi trường từ file ``.env`` ở gốc repo.

Viết tay thay vì dùng ``python-dotenv`` để không thêm dependency chỉ cho 20 dòng
parse, và để `.venv` hiện tại chạy được ngay không cần cài thêm gì.

Quy tắc:

* Biến đã có trong môi trường **thắng** file ``.env`` (trừ khi ``override=True``) —
  ``$env:OPENAI_API_KEY = "..."`` trong terminal vẫn đè được file.
* Bỏ qua dòng trống, dòng ``#`` comment, tiền tố ``export ``.
* Giá trị rỗng (``OPENAI_API_KEY=``) coi như **chưa cấu hình**: không set vào
  ``os.environ``, để bot rơi về tìm kiếm cục bộ đúng như khi không có file.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

__all__ = ["ENV_FILE", "PROJECT_ROOT", "load_env", "parse_env_text"]


def parse_env_text(text: str) -> dict[str, str]:
    """Parse nội dung ``.env`` thành dict. Không đọc file, không chạm os.environ."""
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def load_env(path: Path | None = None, *, override: bool = False) -> dict[str, str]:
    """Đọc ``.env`` và set vào ``os.environ``. Trả về các biến đã set.

    An toàn khi gọi nhiều lần và khi không có file (trả về dict rỗng).
    """
    env_path = path or ENV_FILE
    try:
        text = env_path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return {}

    applied: dict[str, str] = {}
    for key, value in parse_env_text(text).items():
        if not value:  # placeholder chưa điền -> coi như chưa cấu hình
            continue
        if not override and os.environ.get(key):
            continue
        os.environ[key] = value
        applied[key] = value
    return applied
