from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from operator_mvp.agent import OperatorAgent
from operator_mvp.config import DEFAULT_CONFIG_PATH, load_operator_config
from operator_mvp.outbox import OperatorOutbox
from operator_mvp.setup_wizard import run_interactive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="operator", description="Operator MVP for service business owners")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to operator.config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show loaded configuration and data paths")
    sub.add_parser("init-data", help="Create missing CRM, voice, context, outbox, and log files")
    sub.add_parser("setup", help="Interactive non-technical setup for operator.config.yaml")

    run = sub.add_parser("run", help="Handle one customer lifecycle request")
    run.add_argument("request", help="Request to handle, for example: draft an email to Maya")
    run.add_argument("--customer", help="Customer name, email, or phone to match")
    run.add_argument("--skill", help="Force a specific built-in skill")
    run.add_argument("--json", action="store_true", help="Emit JSON instead of readable text")

    outbox = sub.add_parser("draft-outbox", help="Create an approval-pending email or SMS draft artifact")
    outbox.add_argument("channel", choices=["email", "sms"])
    outbox.add_argument("--to", required=True)
    outbox.add_argument("--subject", default="")
    outbox.add_argument("--body", default="")
    outbox.add_argument("--message", default="")
    outbox.add_argument("--customer-id", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "setup":
            run_interactive(args.config)
            return 0

        config = load_operator_config(args.config)
        agent = OperatorAgent(config)
        if args.command == "status":
            print(json.dumps(agent.status(), indent=2))
            return 0
        if args.command == "init-data":
            print(f"Operator data initialized under {Path(args.config).parent.resolve()}")
            return 0
        if args.command == "run":
            result = agent.handle(args.request, customer_query=args.customer, skill_name=args.skill)
            if args.json:
                print(json.dumps({"skill": result.skill, "output": result.output, "metadata": result.metadata}, indent=2))
            else:
                print(f"Skill: {result.skill}\n")
                print(result.output)
            return 0
        if args.command == "draft-outbox":
            outbox = OperatorOutbox(config)
            if args.channel == "email":
                draft = outbox.create_email_draft(
                    to=args.to,
                    subject=args.subject,
                    body=args.body,
                    customer_id=args.customer_id,
                )
            else:
                draft = outbox.create_sms_draft(
                    to=args.to,
                    message=args.message or args.body,
                    customer_id=args.customer_id,
                )
            print(json.dumps(draft, indent=2))
            return 0
    except Exception as exc:
        print(f"Operator error: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
