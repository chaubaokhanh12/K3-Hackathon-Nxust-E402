"""Simple test for translation without Unicode print issues."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
from env_file import load_env
load_env()

from tools._shared.translation import OpenAITranslator, create_translator


def test_translation():
    """Test OpenAI translation with actual API calls."""

    # Test cases: (English, expected Vietnamese keyword)
    test_cases = [
        ("I want to ask how to take a leave of absence", "nghi hoc"),
        ("How to fix Missing credentials error", "credentials"),
        ("When is the deadline for project submission?", "deadline"),
    ]

    print("=" * 60)
    print("Testing OpenAI Translation")
    print("=" * 60)

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment")
        return False

    translator = create_translator(service="openai")

    passed = 0
    failed = 0

    for english, keyword in test_cases:
        try:
            translated = translator.translate_to_vietnamese(english)
            # Check if translation contains expected keyword
            if keyword.lower() in translated.lower():
                print(f"PASS: {english[:40]}")
                print(f"      -> {translated}")
                passed += 1
            else:
                print(f"CHECK: {english[:40]}")
                print(f"      Expected keyword '{keyword}' not in translation")
                print(f"      Got: {translated}")
                failed += 1
        except Exception as e:
            print(f"ERROR: {english[:40]}")
            print(f"      Exception: {e}")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


def test_language_detection():
    """Test language detection."""

    print("\n" + "=" * 60)
    print("Testing Language Detection")
    print("=" * 60)

    # Use OpenAI translator for language detection, not NullTranslator
    if not os.getenv("OPENAI_API_KEY"):
        print("SKIP: OPENAI_API_KEY not found")
        return True

    translator = create_translator(service="openai")

    # Test cases: (text, expected_language)
    test_cases = [
        ("Hello world", "en"),
        ("Xin chao", "vi"),
        ("How to fix API key", "en"),
        ("Lam sao fix loi", "vi"),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        detected = translator.detect_language(text)
        status = "PASS" if detected == expected else "FAIL"
        print(f"{status}: {text[:30]} -> {detected} (expected: {expected})")
        if detected == expected:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    print("\nRunning Translation Tests...")
    print()

    test_language_detection()

    # Only test translation if API key is available
    if os.getenv("OPENAI_API_KEY"):
        success = test_translation()
        if success:
            print("\nAll translation tests passed!")
        else:
            print("\nSome translation tests need manual review.")
    else:
        print("\nSkipping translation test (no API key)")
