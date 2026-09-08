from __future__ import annotations

import argparse

from .service import create_default_service
from .revise.models import Mode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Revise engine request")
    parser.add_argument("prompt")
    parser.add_argument("--mode", choices=[m.value for m in Mode], default=Mode.BASIC.value)
    args = parser.parse_args()

    service = create_default_service()
    response = service.handle_payload({"prompt": args.prompt, "mode": args.mode})
    print(f"decision: {response['decision']}")
    print(f"version: {response['version_id']}")
    print("\n" + (response["text"] or ""))


if __name__ == "__main__":
    main()
