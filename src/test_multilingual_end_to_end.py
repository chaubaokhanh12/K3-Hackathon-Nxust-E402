"""End-to-end test for multilingual search via bot.py

This script tests the complete pipeline:
1. English question input
2. Translation (if enabled)
3. Topic detection
4. Semantic search
5. Bot response with suggestions
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load environment
from env_file import load_env
load_env()

from bot import answer


def test_multilingual_search():
    """Test English queries through the complete bot pipeline."""

    # Enable translation for this test
    os.environ["TRANSLATION_ENABLED"] = "true"
    os.environ["TRANSLATION_SERVICE"] = "openai"

    print("=" * 70)
    print("End-to-End Multilingual Search Test")
    print("=" * 70)
    print()

    # Test cases: English queries that should match Vietnamese threads
    test_cases = [
        {
            "question": "I want to ask how to take a leave of absence",
            "expected_keywords": ["nghi", "hoc"],
            "description": "Leave of absence inquiry"
        },
        {
            "question": "How to fix Missing credentials error with API key",
            "expected_keywords": ["api", "key", "credentials"],
            "description": "API key error"
        },
        {
            "question": "When is the deadline for project submission",
            "expected_keywords": ["deadline", "nop"],
            "description": "Deadline inquiry"
        },
        {
            "question": "Toi muoi hoi cach xin nghi hoc",  # Vietnamese (control)
            "expected_keywords": ["nghi", "hoc"],
            "description": "Vietnamese control test"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Question: {test['question']}")
        print("-" * 70)

        try:
            response = answer(test['question'])

            # Check key fields
            translation_applied = response.get('translation_applied', False)
            confidence = response.get('confidence', 'none')
            has_answer = response.get('has_answer', False)
            num_suggestions = len(response.get('suggestions', []))

            print(f"Translation applied: {translation_applied}")
            print(f"Confidence: {confidence}")
            print(f"Has answer: {has_answer}")
            print(f"Num suggestions: {num_suggestions}")

            # Check suggestions for expected keywords
            if num_suggestions > 0:
                print(f"\nTop suggestion:")
                top = response['suggestions'][0]
                print(f"  Title: {top.get('title', 'N/A')[:60]}")
                print(f"  Similarity: {top.get('similarity', 0)}%")
                print(f"  Excerpt: {top.get('excerpt', 'N/A')[:80]}...")

                # Check for keywords
                excerpt_lower = top.get('excerpt', '').lower()
                found_keywords = [kw for kw in test['expected_keywords'] if kw.lower() in excerpt_lower]
                if found_keywords:
                    print(f"  Keywords found: {found_keywords}")
            else:
                print("No suggestions found (tier NONE)")

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 70)
        print()


def test_off_topic_blocking():
    """Test that off-topic English questions are blocked."""

    print("\n" + "=" * 70)
    print("Off-Topic Blocking Test (English questions)")
    print("=" * 70)
    print()

    off_topic_tests = [
        "Is Messi better than Mbappe?",
        "Why is the sky blue?",
        "Who won the World Cup?",
    ]

    for question in off_topic_tests:
        print(f"Question: {question}")
        print("-" * 70)

        try:
            response = answer(question)
            reason = response.get('reason', 'unknown')
            headline = response.get('headline', 'N/A')

            print(f"Reason: {reason}")
            print(f"Headline: {headline}")

            if reason == 'out_of_scope':
                print("✓ Correctly blocked as out-of-scope")
            else:
                print("✗ NOT blocked - should be out_of_scope!")

        except Exception as e:
            print(f"ERROR: {e}")

        print()


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY required for translation test")
        print("Set it in .env file or environment")
        sys.exit(1)

    print("Starting end-to-end multilingual test...\n")

    test_multilingual_search()
    test_off_topic_blocking()

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)
