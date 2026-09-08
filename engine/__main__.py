from __future__ import annotations

import argparse

from .http import serve
from .service import create_default_service
from .revise.models import Mode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or serve the Revise engine")
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--mode", choices=[m.value for m in Mode], default=Mode.BASIC.value)
    parser.add_argument("--serve", action="store_true", help="start the local HTTP engine")
    parser.add_argument("--host", default=None, help="HTTP bind host (defaults to REVISE_HOST or 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="HTTP port (defaults to REVISE_PORT or 8000)")
    args = parser.parse_args()

    if args.serve:
        serve(host=args.host, port=args.port)
        return

    if not args.prompt:
        parser.error("prompt is required unless --serve is used")

    service = create_default_service()
    response = service.handle_payload({"prompt": args.prompt, "mode": args.mode})
    print(f"decision: {response['decision']}")
    print(f"version: {response['version_id']}")
    print("\n" + (response["text"] or ""))


if __name__ == "__main__":
    main()
