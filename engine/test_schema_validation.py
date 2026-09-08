import unittest

from engine.revise.models import Mode, TaskContract
from engine.revise.profile import build_profile
from engine.revise.verifiers import JsonSchemaVerifier, run_deterministic_verifiers


class SchemaValidationTests(unittest.TestCase):
    def contract(self, schema):
        return TaskContract(
            goal="Return the requested JSON object",
            mode=Mode.BASIC,
            desired_format="json",
            output_schema=schema,
        )

    def test_profile_selects_schema_verification(self):
        profile = build_profile(self.contract({"type": "object"}))
        self.assertIn("json_schema", profile.deterministic_checks)

    def test_required_property_and_type_are_enforced(self):
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
            },
        }
        result = JsonSchemaVerifier().verify(self.contract(schema), '{"name":"Jatin","age":"20"}')
        self.assertEqual(result[0].result, "fail")
        self.assertTrue(any("age" in item for item in result[0].provenance))

    def test_valid_nested_schema_passes(self):
        schema = {
            "type": "object",
            "required": ["user", "tags"],
            "properties": {
                "user": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {"id": {"type": "integer", "minimum": 1}},
                    "additionalProperties": False,
                },
                "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            },
            "additionalProperties": False,
        }
        result = JsonSchemaVerifier().verify(
            self.contract(schema), '{"user":{"id":3},"tags":["engine","test"]}'
        )
        self.assertEqual(result[0].result, "pass")

    def test_additional_properties_can_fail(self):
        schema = {
            "type": "object",
            "properties": {"answer": {"type": "number"}},
            "required": ["answer"],
            "additionalProperties": False,
        }
        result = JsonSchemaVerifier().verify(self.contract(schema), '{"answer":42,"extra":true}')
        self.assertEqual(result[0].result, "fail")
        self.assertTrue(any("extra" in item for item in result[0].provenance))

    def test_enum_and_string_constraints_are_enforced(self):
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["ok", "error"]},
                "code": {"type": "string", "pattern": "^[A-Z]{3}$"},
            },
            "required": ["status", "code"],
        }
        result = JsonSchemaVerifier().verify(self.contract(schema), '{"status":"pending","code":"abc"}')
        self.assertEqual(result[0].result, "fail")

    def test_array_constraints_are_enforced(self):
        schema = {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 3,
            "uniqueItems": True,
        }
        result = JsonSchemaVerifier().verify(self.contract(schema), "[1, 1]")
        self.assertEqual(result[0].result, "fail")

    def test_invalid_json_fails_schema_verification(self):
        schema = {"type": "object"}
        result = JsonSchemaVerifier().verify(self.contract(schema), '{"answer":}')
        self.assertEqual(result[0].result, "fail")

    def test_registry_runs_schema_verifier(self):
        contract = self.contract({"type": "object", "required": ["answer"]})
        profile = build_profile(contract)
        evidence = run_deterministic_verifiers(contract, '{"answer":42}', profile)
        self.assertTrue(any(item.source == "deterministic.json_schema" and item.result == "pass" for item in evidence))


if __name__ == "__main__":
    unittest.main()
