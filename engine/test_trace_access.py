from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from engine.http import _trace_access_allowed


class TraceAccessTests(unittest.TestCase):
    def test_localhost_trace_remains_available_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(_trace_access_allowed(None))

    def test_public_host_trace_is_denied_without_token(self):
        with patch.dict(os.environ, {"REVISE_HOST": "0.0.0.0"}, clear=True):
            self.assertFalse(_trace_access_allowed(None))

    def test_configured_token_is_required(self):
        with patch.dict(os.environ, {"REVISE_TRACE_TOKEN": "secret-token"}, clear=True):
            self.assertFalse(_trace_access_allowed(None))
            self.assertFalse(_trace_access_allowed("wrong-token"))
            self.assertTrue(_trace_access_allowed("secret-token"))

    def test_configured_token_overrides_local_default(self):
        with patch.dict(os.environ, {"REVISE_HOST": "127.0.0.1", "REVISE_TRACE_TOKEN": "secret-token"}, clear=True):
            self.assertFalse(_trace_access_allowed(None))
            self.assertTrue(_trace_access_allowed("secret-token"))


if __name__ == "__main__":
    unittest.main()
