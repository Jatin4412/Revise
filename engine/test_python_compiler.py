import tempfile
import unittest
from pathlib import Path

from engine.revise.models import Mode, TaskContract
from engine.revise.profile import build_profile
from engine.revise.verifiers import PythonCompileVerifier, run_deterministic_verifiers


class PythonCompilerTests(unittest.TestCase):
    def contract(self):
        return TaskContract(goal="Write a Python function", mode=Mode.BASIC)

    def test_valid_python_block_compiles(self):
        result = PythonCompileVerifier().verify(self.contract(), "```python\ndef add(a, b):\n    return a + b\n```")
        self.assertEqual(result[0].result, "pass")
        self.assertIn("compiled", result[0].provenance)

    def test_invalid_python_block_fails_compile(self):
        result = PythonCompileVerifier().verify(self.contract(), "```python\ndef add(a, b)\n    return a + b\n```")
        self.assertEqual(result[0].result, "fail")
        self.assertIn("compile_error:SyntaxError", result[0].provenance)

    def test_compile_verifier_never_executes_code(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "executed.txt"
            snippet = f"open({str(marker)!r}, 'w').write('executed')"
            result = PythonCompileVerifier().verify(self.contract(), f"```python\n{snippet}\n```")
            self.assertEqual(result[0].result, "pass")
            self.assertFalse(marker.exists())

    def test_python_profile_selects_syntax_and_compile_checks(self):
        profile = build_profile(self.contract())
        self.assertEqual(profile.deterministic_checks[:2], ("python_syntax", "python_compile"))

    def test_registry_runs_compile_verifier(self):
        profile = build_profile(self.contract())
        evidence = run_deterministic_verifiers(self.contract(), "```python\nvalue = 42\n```", profile)
        self.assertTrue(any(item.source == "deterministic.python_compile" and item.result == "pass" for item in evidence))


if __name__ == "__main__":
    unittest.main()
