from __future__ import annotations

import os
from pathlib import Path

from env_file import load_env, parse_env_text


def test_parses_comments_quotes_and_export_prefix() -> None:
    parsed = parse_env_text(
        "\n".join(
            [
                "# comment",
                "",
                "OPENAI_API_KEY=sk-abc123",
                'QUOTED="giá trị có dấu cách"',
                "export EXPORTED=yes",
                "khong_co_dau_bang",
            ]
        )
    )

    assert parsed == {
        "OPENAI_API_KEY": "sk-abc123",
        "QUOTED": "giá trị có dấu cách",
        "EXPORTED": "yes",
    }


def test_load_env_sets_missing_variable(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DUPBOT_TEST_KEY=from-file\n", encoding="utf-8")
    os.environ.pop("DUPBOT_TEST_KEY", None)

    try:
        applied = load_env(env_file)

        assert applied == {"DUPBOT_TEST_KEY": "from-file"}
        assert os.environ["DUPBOT_TEST_KEY"] == "from-file"
    finally:
        os.environ.pop("DUPBOT_TEST_KEY", None)


def test_existing_environment_wins_over_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DUPBOT_TEST_KEY=from-file\n", encoding="utf-8")
    os.environ["DUPBOT_TEST_KEY"] = "from-shell"

    try:
        assert load_env(env_file) == {}
        assert os.environ["DUPBOT_TEST_KEY"] == "from-shell"
        assert load_env(env_file, override=True) == {"DUPBOT_TEST_KEY": "from-file"}
    finally:
        os.environ.pop("DUPBOT_TEST_KEY", None)


def test_empty_placeholder_counts_as_unset(tmp_path: Path) -> None:
    """``OPENAI_API_KEY=`` chưa điền -> giữ nguyên chế độ tìm kiếm cục bộ."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=\n", encoding="utf-8")
    previous = os.environ.pop("OPENAI_API_KEY", None)

    try:
        assert load_env(env_file) == {}
        assert "OPENAI_API_KEY" not in os.environ
    finally:
        if previous is not None:
            os.environ["OPENAI_API_KEY"] = previous


def test_missing_file_is_not_an_error(tmp_path: Path) -> None:
    assert load_env(tmp_path / "khong-ton-tai.env") == {}
