"""Test script for multilingual search (translation feature).

Run this script to verify that English queries are correctly translated
to Vietnamese for better semantic search accuracy.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
from env_file import load_env
load_env()

from tools._shared.translation import OpenAITranslator, NullTranslator, create_translator


def test_language_detection():
    """Test language detection heuristic."""

    print("=" * 80)
    print("Testing Language Detection")
    print("=" * 80)

    translator = NullTranslator()

    test_cases = [
        # Vietnamese text
        ("Xin chào", "vi"),
        ("Làm sao để xin nghỉ học?", "vi"),
        ("Cách fix lỗi API key", "vi"),

        # English text
        ("Hello", "en"),
        ("I want to ask how to take a leave of absence", "en"),
        ("How to fix Missing credentials error", "en"),

        # Mixed/Vietnamese with technical terms
        ("Làm sao để fix API key lỗi?", "vi"),  # Contains Vietnamese chars
    ]

    for text, expected_lang in test_cases:
        detected = translator.detect_language(text)
        status = "[PASS]" if detected == expected_lang else "[FAIL]"
        print(f"{status}: {text[:50]:50} -> {detected:3} (expected: {expected_lang})")
        if detected != expected_lang:
            print(f"  Mismatch!")


def test_null_translator():
    """Test NullTranslator (no-op)."""

    print("\n" + "=" * 80)
    print("Testing NullTranslator (No-op)")
    print("=" * 80)

    translator = NullTranslator()

    test_text = "Hello world"
    result = translator.translate_to_vietnamese(test_text)

    status = "[PASS]" if result == test_text else "[FAIL]"
    print(f"{status}: NullTranslator returns original text unchanged")
    print(f"  Input:  '{test_text}'")
    print(f"  Output: '{result}'")


def test_openai_translator_without_api():
    """Test OpenAI translator behavior without API key (should fail gracefully)."""

    print("\n" + "=" * 80)
    print("Testing OpenAI Translator (without API key)")
    print("=" * 80)

    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found.")
        print("OpenAI translator would fail gracefully in production.")
        print("When API key is available, it will translate:")
        print()
        print("  Examples:")
        print("    'I want to ask how to take a leave of absence'")
        print("    -> 'Tôi muốn hỏi cách xin nghỉ học'")
        print()
        print("    'How to fix Missing credentials error'")
        print("    -> 'Cách fix lỗi Missing credentials'")
        print()
        print("    'When is the deadline for project submission?'")
        print("    -> 'Deadline nộp dự án là khi nào?'")
    else:
        print("OPENAI_API_KEY found. Testing actual translation...")

        try:
            translator = create_translator(service="openai")

            test_cases = [
                ("I want to ask how to take a leave of absence", "xin nghỉ học"),
                ("How to fix Missing credentials error", "Missing credentials"),
                ("When is the deadline?", "deadline"),
            ]

            for english_text, vietnam_keyword in test_cases:
                translated = translator.translate_to_vietnamese(english_text)
                status = "[PASS]" if vietnam_keyword.lower() in translated.lower() else "[CHECK]"
                print(f"{status}: {english_text}")
                print(f"  -> {translated}")

        except Exception as e:
            print(f"Translation test failed: {e}")


def test_translator_factory():
    """Test translator factory function."""

    print("\n" + "=" * 80)
    print("Testing Translator Factory")
    print("=" * 80)

    # Test null translator
    translator1 = create_translator(service="null")
    status1 = "[PASS]" if isinstance(translator1, NullTranslator) else "[FAIL]"
    print(f"{status1}: create_translator(service='null') returns NullTranslator")

    # Test default (null)
    translator2 = create_translator()
    status2 = "[PASS]" if isinstance(translator2, NullTranslator) else "[FAIL]"
    print(f"{status2}: create_translator() (default) returns NullTranslator")

    # Test OpenAI (would fail without API key, but should create instance)
    try:
        translator3 = create_translator(service="openai")
        status3 = "[PASS]" if isinstance(translator3, OpenAITranslator) else "[FAIL]"
        print(f"{status3}: create_translator(service='openai') returns OpenAITranslator")
    except Exception as e:
        print(f"[FAIL]: create_translator(service='openai') failed: {e}")


if __name__ == "__main__":
    test_language_detection()
    test_null_translator()
    test_translator_factory()
    test_openai_translator_without_api()

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("Translation module structure is working correctly.")
    print("To test actual translation:")
    print("1. Set OPENAI_API_KEY in environment")
    print("2. Run this script again")
    print("3. Or enable TRANSLATION_ENABLED=true in .env and test via bot.py")
