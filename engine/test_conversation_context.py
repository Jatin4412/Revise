from __future__ import annotations

import unittest

from engine import Engine, EngineService
from engine.context import MAX_CONVERSATION_CHARS, MAX_CONVERSATION_MESSAGES, parse_conversation
from engine.revise.models import EvaluationProfile, TaskContract


class CapturePrimary:
    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.contexts: list[str | None] = []

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.contexts.append(context)
        return self.response


class DeliberativePrimary(CapturePrimary):
    def __init__(self) -> None:
        super().__init__("generated")
        self.deliberation_prompts: list[str] = []

    def deliberate(self, contract: TaskContract, prompt: str) -> str:
        self.deliberation_prompts.append(prompt)
        lowered = prompt.lower()
        if "you are the planning role in reiterate" in lowered:
            return '{"approach":"direct","subproblems":[],"assumptions":[],"open_questions":[]}'
        if "you are the reasoning role in reiterate" in lowered:
            return '{"candidate":"generated","assumptions":[],"open_questions":[]}'
        return '{"concerns":[],"challenged_assumptions":[],"missing_steps":[],"contradictions":[],"alternative_interpretations":[],"alternative_approaches":[],"confidence":1.0,"actionable":false}'


class ConversationContextTests(unittest.TestCase):
    def test_omitted_conversation_preserves_existing_behavior(self) -> None:
        primary = CapturePrimary()
        result = EngineService(Engine(primary)).handle_payload({"prompt": "current task"})
        self.assertEqual(result["text"], "ok")
        self.assertEqual(primary.contexts, [None])

    def test_empty_conversation_is_valid_and_behaves_like_omitted(self) -> None:
        omitted = parse_conversation(None, supplied=False)
        empty = parse_conversation([], supplied=True)
        self.assertIsNone(omitted)
        self.assertIsNotNone(empty)
        self.assertIsNone(empty.render())
        self.assertEqual(empty.original_message_count, 0)

        primary = CapturePrimary()
        EngineService(Engine(primary)).handle_payload({"prompt": "current task", "conversation": []})
        self.assertEqual(primary.contexts, [None])

    def test_user_and_assistant_messages_reach_primary_in_order(self) -> None:
        primary = CapturePrimary()
        result = EngineService(Engine(primary)).handle_payload(
            {
                "prompt": "Now compare their prices.",
                "conversation": [
                    {"role": "user", "content": "Compare X and Y."},
                    {"role": "assistant", "content": "X is cheaper for storage."},
                ],
            }
        )
        context = primary.contexts[0]
        self.assertIsNotNone(context)
        self.assertLess(context.index("[user]"), context.index("[assistant]"))
        self.assertIn("Compare X and Y.", context)
        self.assertIn("X is cheaper for storage.", context)
        self.assertEqual(result["text"], "ok")

    def test_current_prompt_remains_the_task_contract(self) -> None:
        context = parse_conversation([{"role": "user", "content": "Compare X and Y."}], supplied=True)
        engine_result = Engine( CapturePrimary()).run(
            TaskContract(goal="Now compare their prices."),
            initial_context=context,
        )
        self.assertEqual(engine_result.task_contract.goal, "Now compare their prices.")

    def test_context_reaches_deliberation_with_same_rendered_boundary(self) -> None:
        primary = DeliberativePrimary()
        context = parse_conversation(
            [
                {"role": "user", "content": "We discussed X and Y."},
                {"role": "assistant", "content": "The second option was Y."},
            ],
            supplied=True,
        )
        Engine(primary).run(
            TaskContract(goal="Compare their prices."),
            initial_context=context,
            profile=EvaluationProfile(dimensions=("task_completion",), max_deliberation_cycles=1),
        )
        self.assertGreaterEqual(len(primary.deliberation_prompts), 3)
        for prompt in primary.deliberation_prompts:
            self.assertIn("We discussed X and Y.", prompt)
            self.assertIn("The second option was Y.", prompt)

    def test_invalid_conversation_entries_fail_closed(self) -> None:
        invalid_payloads = [
            {"conversation": "not-a-list"},
            {"conversation": ["not-an-object"]},
            {"conversation": [{"content": "missing role"}]},
            {"conversation": [{"role": "system", "content": "unsupported"}]},
            {"conversation": [{"role": "invalid", "content": "unsupported"}]},
            {"conversation": [{"role": "user"}]},
            {"conversation": [{"role": "user", "content": None}]},
            {"conversation": [{"role": "user", "content": 123}]},
        ]
        service = EngineService(Engine(CapturePrimary()))
        for payload in invalid_payloads:
            payload["prompt"] = "current task"
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    service.handle_payload(payload)

    def test_conversation_is_deterministically_bounded(self) -> None:
        messages = [
            {"role": "user" if index % 2 == 0 else "assistant", "content": f"message-{index}-" + ("x" * 995)}
            for index in range(MAX_CONVERSATION_MESSAGES + 5)
        ]
        context = parse_conversation(messages, supplied=True)
        self.assertIsNotNone(context)
        self.assertTrue(context.bounded)
        self.assertEqual(context.original_message_count, MAX_CONVERSATION_MESSAGES + 5)
        self.assertLessEqual(context.included_message_count, MAX_CONVERSATION_MESSAGES)
        self.assertLessEqual(sum(len(item.content) for item in context.messages), MAX_CONVERSATION_CHARS)
        self.assertIn(f"message-{MAX_CONVERSATION_MESSAGES + 4}", context.render() or "")
        self.assertNotIn("message-0-", context.render() or "")

    def test_trace_contains_only_safe_conversation_metadata(self) -> None:
        secret = "PRIVATE_CONVERSATION_SHOULD_NOT_APPEAR_IN_TRACE"
        primary = CapturePrimary(response="response")
        response = EngineService(Engine(primary)).handle_trace_payload(
            {
                "prompt": "current task",
                "conversation": [{"role": "user", "content": secret}],
            }
        )
        trace = response["trace"]
        self.assertNotIn(secret, repr(trace))
        context_events = [event for event in trace if event["stage"] == "conversation_context"]
        self.assertEqual(len(context_events), 1)
        details = context_events[0]["details"]
        self.assertEqual(details["supplied"], True)
        self.assertEqual(details["bounded"], False)
        self.assertEqual(details["original_message_count"], 1)
        self.assertEqual(details["included_message_count"], 1)


if __name__ == "__main__":
    unittest.main()
