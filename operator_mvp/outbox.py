from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operator_mvp.config import OperatorConfig


class OperatorOutbox:
    """Draft-only email and SMS outbox.

    MVP safety rule: this class never sends. It writes approval-pending draft
    artifacts that a human can review before any external communication.
    """

    def __init__(self, config: OperatorConfig):
        self.config = config
        self.path: Path = config.outbox_path
        self.path.mkdir(parents=True, exist_ok=True)

    def create_email_draft(self, *, to: str, subject: str, body: str, customer_id: str | None = None) -> dict[str, Any]:
        return self._write_draft(
            {
                "channel": "email",
                "to": to,
                "subject": subject,
                "body": body,
                "customer_id": customer_id,
            }
        )

    def create_sms_draft(self, *, to: str, message: str, customer_id: str | None = None) -> dict[str, Any]:
        return self._write_draft(
            {
                "channel": "sms",
                "to": to,
                "message": message,
                "customer_id": customer_id,
            }
        )

    def _write_draft(self, payload: dict[str, Any]) -> dict[str, Any]:
        draft_id = f"draft_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        record = {
            "id": draft_id,
            "status": "draft_pending_approval",
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "approval_required": True,
            "sent": False,
            **payload,
        }
        draft_path = self.path / f"{draft_id}.json"
        draft_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
