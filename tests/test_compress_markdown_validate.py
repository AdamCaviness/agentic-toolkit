import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "skills" / "compress-markdown" / "validate.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "compress_markdown_validate", VALIDATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CompressMarkdownValidateTest(unittest.TestCase):
    def setUp(self):
        self.validator = load_validator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def validate_text(self, original, compressed):
        temp_path = Path(self.temp_dir.name)
        original_path = temp_path / "original.md"
        compressed_path = temp_path / "compressed.md"
        original_path.write_text(original)
        compressed_path.write_text(compressed)

        with redirect_stdout(io.StringIO()):
            return self.validator.validate(original_path, compressed_path)

    def test_deleted_must_directive_is_invalid_even_when_other_must_survives(self):
        self.assertFalse(
            self.validate_text(
                "You MUST run tests. You MUST not push.\n",
                "You MUST run tests.\n",
            )
        )

    def test_shortened_do_not_directive_remains_valid(self):
        self.assertTrue(
            self.validate_text(
                "You DO NOT push before review.\n",
                "DO NOT push before review.\n",
            )
        )

    def test_keyword_in_unrelated_sentence_does_not_preserve_deleted_directive(self):
        self.assertFalse(
            self.validate_text(
                "You MUST run tests. You MUST not push.\n",
                "You MUST run tests. This IMPORTANT note remains.\n",
            )
        )

    def test_keyword_in_frontmatter_does_not_preserve_deleted_directive(self):
        self.assertFalse(
            self.validate_text(
                "You MUST not push.\n",
                "---\nnote: MUST not push\n---\n",
            )
        )

    def test_all_keywords_in_same_directive_sentence_must_survive(self):
        self.assertFalse(
            self.validate_text(
                "IMPORTANT: You MUST run tests.\n",
                "IMPORTANT: run tests.\n",
            )
        )


if __name__ == "__main__":
    unittest.main()
