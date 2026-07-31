"""Test translation and save results to file to avoid Unicode encoding issues."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Load environment variables
from env_file import load_env
load_env()

from tools._shared.translation import create_translator


def test_translation_and_save():
    """Test OpenAI translation and save to file."""

    test_cases = [
        "I want to ask how to take a leave of absence",
        "How to fix Missing credentials error",
        "When is the deadline for project submission?",
        "My code is not working, can you help?",
    ]

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found")
        return False

    translator = create_translator(service="openai")

    results = []

    for english in test_cases:
        try:
            detected_lang = translator.detect_language(english)
            translated = translator.translate_to_vietnamese(english)

            results.append({
                "english": english,
                "detected_language": detected_lang,
                "vietnamese": translated,
            })

            print(f"Translated: {english[:40]}")
        except Exception as e:
            print(f"ERROR: {english[:40]} - {e}")
            results.append({
                "english": english,
                "error": str(e),
            })

    # Save to file
    output_file = "translation_results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Translation Test Results\n")
        f.write("=" * 60 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"Test {i}:\n")
            f.write(f"  English: {result['english']}\n")

            if "error" in result:
                f.write(f"  ERROR: {result['error']}\n")
            else:
                f.write(f"  Detected: {result['detected_language']}\n")
                f.write(f"  Vietnamese: {result['vietnamese']}\n")

            # Check for key Vietnamese phrases
            if "vietnamese" in result:
                viet = result["vietnamese"].lower()
                keywords_found = []
                if "nghi" in viet and "hoc" in viet:
                    keywords_found.append("nghi hoc")
                if "deadline" in viet or "han nop" in viet:
                    keywords_found.append("deadline/han nop")
                if "loi" in viet or "fix" in viet or "sua" in viet:
                    keywords_found.append("loi/fix")

                if keywords_found:
                    f.write(f"  Keywords: {', '.join(keywords_found)}\n")

            f.write("\n")

    print(f"\nResults saved to: {output_file}")
    print("Open the file to see Vietnamese translations correctly.")

    return True


if __name__ == "__main__":
    print("Testing Translation (saving to file)...\n")
    test_translation_and_save()
