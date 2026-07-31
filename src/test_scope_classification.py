"""Test script for LLM-based scope classification.

Run this script to verify that the LLM classifier correctly blocks diverse
off-topic questions (celebrity, sports, politics, science, entertainment, etc.)
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
from env_file import load_env
load_env()

from agent.routing import Scope, classify_scope_llm, classify_scope


def test_llm_classifier():
    """Test LLM-based classifier with diverse off-topic questions."""

    # Test cases: (question, expected_scope)
    test_cases = [
        # Sports & Celebrity comparisons
        ("Messi có đẳng cấp hơn Mbappe không?", Scope.OFF_TOPIC),
        ("Taylor Swift xinh hơn Selena Gomez?", Scope.OFF_TOPIC),
        ("Ronaldo hay Messi giỏi hơn?", Scope.OFF_TOPIC),
        ("BTS hay Blackpink nổi tiếng hơn?", Scope.OFF_TOPIC),

        # Politics
        ("Trump hay Biden tốt hơn cho Mỹ?", Scope.OFF_TOPIC),
        ("Tổng thống Pháp hiện tại là ai?", Scope.OFF_TOPIC),

        # Science & General Knowledge
        ("Tại sao bầu trời lại màu xanh?", Scope.OFF_TOPIC),
        ("Why is the sky blue?", Scope.OFF_TOPIC),
        ("Cách tính diện tích hình tròn?", Scope.OFF_TOPIC),
        ("What is the meaning of life?", Scope.OFF_TOPIC),

        # Entertainment (Movies, Books, Games)
        ("Harry Potter hay Percy Jackson hay hơn?", Scope.OFF_TOPIC),
        ("Marvel hay DC phim hay hơn?", Scope.OFF_TOPIC),
        ("Cách chơi Minecraft?", Scope.OFF_TOPIC),
        ("Review phim Avatar?", Scope.OFF_TOPIC),

        # Existing OFF_TOPIC (from original keywords)
        ("Cho mình xin tỷ số bóng đá tối qua", Scope.OFF_TOPIC),
        ("Thời tiết hôm nay thế nào?", Scope.OFF_TOPIC),
        ("Bitcoin hôm nay giá多少?", Scope.OFF_TOPIC),

        # INTEGRITY cases (bot làm bài thay)
        ("Viết hộ em bài luận tiếng Anh", Scope.INTEGRITY),
        ("Làm hộ bài tập Toán cao cấp", Scope.INTEGRITY),
        ("Giải bài lab AI giúp mình", Scope.INTEGRITY),

        # IN_SCOPE cases (học hỏi, dự án, quy định)
        ("Làm sao để xin nghỉ học?", Scope.IN_SCOPE),
        ("Code của em bị lỗi API key ạ", Scope.IN_SCOPE),
        ("Có được mang người ngoài vào nhóm không?", Scope.IN_SCOPE),
        ("Làm sao để fix lỗi Missing credentials?", Scope.IN_SCOPE),
        ("Cách submit dự án giai đoạn 2?", Scope.IN_SCOPE),
        ("Tài liệu buổi học hôm nay ở đâu?", Scope.IN_SCOPE),
    ]

    print("=" * 80)
    print("Testing LLM-based Scope Classification")
    print("=" * 80)

    passed = 0
    failed = 0

    for question, expected in test_cases:
        try:
            result = classify_scope_llm(question)
            status = "[PASS]" if result == expected else "[FAIL]"

            if result == expected:
                passed += 1
            else:
                failed += 1
                print(f"\n{status}: {question}")
                print(f"  Expected: {expected.value}, Got: {result.value}")
        except Exception as e:
            failed += 1
            print(f"\n[ERROR]: {question}")
            print(f"  Exception: {e}")

    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


def test_hybrid_classifier():
    """Test hybrid approach (LLM + keyword fallback)."""

    print("\n" + "=" * 80)
    print("Testing Hybrid Classification (LLM + Keyword Fallback)")
    print("=" * 80)

    test_cases = [
        # Should use LLM (comprehensive off-topic)
        ("Elon Musk có đẳng cấp hơn Bill Gates không?", Scope.OFF_TOPIC),
        ("Jennifer Lawrence diễn hay hơn Emma Stone?", Scope.OFF_TOPIC),

        # Should use keywords (existing patterns)
        ("viết hộ em bài", Scope.INTEGRITY),  # Fast path keywords
        ("làm hộ bài tập", Scope.INTEGRITY),  # Fast path keywords

        # Should pass through to IN_SCOPE
        ("Làm sao fix lỗi embedding?", Scope.IN_SCOPE),
    ]

    for question, expected in test_cases:
        result = classify_scope(question, use_llm=True)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"{status}: {question[:60]}")
        if result != expected:
            print(f"  Expected: {expected.value}, Got: {result.value}")


if __name__ == "__main__":
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not found. Set it to run LLM tests.")
        print("Testing keyword-only fallback...")

        # Test with keyword fallback only
        test_cases = [
            ("viet ho em bai luan", Scope.INTEGRITY),
            ("lam ho bai tap", Scope.INTEGRITY),
            ("cho xin ty so bong da", Scope.OFF_TOPIC),
        ]

        for question, expected in test_cases:
            result = classify_scope(question, use_llm=False)
            status = "PASS" if result == expected else "FAIL"
            print(f"{question[:40]:40} -> {result.value:15} [{status}]")
    else:
        # Run full tests
        success = test_llm_classifier()
        if success:
            print("\nAll LLM classification tests passed!")
        else:
            print("\nSome tests failed. Check results above.")

        test_hybrid_classifier()
