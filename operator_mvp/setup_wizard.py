from __future__ import annotations

from pathlib import Path

import yaml


def write_config(
    path: str | Path,
    *,
    business_name: str,
    owner_name: str,
    email_address: str = "",
    sms_from_number: str = "",
    crm_path: str = "data/crm.json",
    voice_guidelines_path: str = "data/voice_guidelines.md",
) -> None:
    config = {
        "business_name": business_name,
        "owner_name": owner_name,
        "model": {
            "provider": "openai-codex",
            "model": "gpt-5.5",
            "oauth_provider": "openai-codex",
        },
        "data_sources": {
            "crm_path": crm_path,
            "voice_guidelines_path": voice_guidelines_path,
            "conversation_context_path": "data/conversation_context.json",
            "interaction_log_path": "data/interactions.jsonl",
            "outbox_path": "data/outbox",
        },
        "communication": {
            "email_address": email_address,
            "email_imap_host": "${OPERATOR_EMAIL_IMAP_HOST}",
            "email_smtp_host": "${OPERATOR_EMAIL_SMTP_HOST}",
            "sms_provider": "twilio",
            "sms_from_number": sms_from_number,
        },
    }
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def run_interactive(path: str | Path = "operator.config.yaml") -> None:
    print("Operator Setup")
    print("Press Enter to leave optional fields blank.")
    business_name = input("Business name: ").strip()
    owner_name = input("Owner name: ").strip()
    if not business_name or not owner_name:
        raise SystemExit("Business name and owner name are required.")
    email_address = input("Email address for drafts: ").strip()
    sms_from_number = input("SMS from number: ").strip()
    write_config(
        path,
        business_name=business_name,
        owner_name=owner_name,
        email_address=email_address,
        sms_from_number=sms_from_number,
    )
    print(f"Saved {path}")


if __name__ == "__main__":
    run_interactive()
