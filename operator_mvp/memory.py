from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operator_mvp.config import OperatorConfig


@dataclass(slots=True)
class CustomerRecord:
    id: str
    name: str
    email: str = ""
    phone: str = ""
    lifecycle_stage: str = "unknown"
    last_contact: str = ""
    notes: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    purchases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomerRecord":
        return cls(
            id=str(data.get("id") or data.get("email") or data.get("name") or "unknown"),
            name=str(data.get("name") or "Unknown customer"),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or ""),
            lifecycle_stage=str(data.get("lifecycle_stage") or data.get("stage") or "unknown"),
            last_contact=str(data.get("last_contact") or ""),
            notes=_list_of_str(data.get("notes")),
            preferences=_list_of_str(data.get("preferences")),
            purchases=_list_of_str(data.get("purchases")),
            tags=_list_of_str(data.get("tags")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "lifecycle_stage": self.lifecycle_stage,
            "last_contact": self.last_contact,
            "notes": self.notes,
            "preferences": self.preferences,
            "purchases": self.purchases,
            "tags": self.tags,
        }


def _list_of_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


class OperatorMemory:
    """Flat, predictable storage for Operator MVP.

    The storage model intentionally avoids Hermes' self-improving memory and nudge
    systems. It keeps only CRM records, voice guidelines, recent context, and an
    append-only interaction log.
    """

    def __init__(self, config: OperatorConfig):
        self.config = config
        self._ensure_files()

    def _ensure_files(self) -> None:
        for path in [self.config.crm_path, self.config.conversation_context_path, self.config.interaction_log_path]:
            path.parent.mkdir(parents=True, exist_ok=True)
        self.config.voice_guidelines_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config.crm_path.exists():
            self.config.crm_path.write_text(json.dumps({"customers": []}, indent=2) + "\n", encoding="utf-8")
        if not self.config.voice_guidelines_path.exists():
            self.config.voice_guidelines_path.write_text("# Voice Guidelines\n\nAdd sample emails, tone notes, and brand voice rules here.\n", encoding="utf-8")
        if not self.config.conversation_context_path.exists():
            self.config.conversation_context_path.write_text(json.dumps({"recent": []}, indent=2) + "\n", encoding="utf-8")
        if not self.config.interaction_log_path.exists():
            self.config.interaction_log_path.write_text("", encoding="utf-8")

    def load_customers(self) -> list[CustomerRecord]:
        data = json.loads(self.config.crm_path.read_text(encoding="utf-8") or "{}")
        raw_customers = data.get("customers", []) if isinstance(data, dict) else []
        return [CustomerRecord.from_dict(item) for item in raw_customers if isinstance(item, dict)]

    def save_customers(self, customers: list[CustomerRecord]) -> None:
        self.config.crm_path.write_text(
            json.dumps({"customers": [customer.to_dict() for customer in customers]}, indent=2) + "\n",
            encoding="utf-8",
        )

    def find_customer(self, query: str) -> CustomerRecord | None:
        normalized = query.strip().lower()
        if not normalized:
            return None
        for customer in self.load_customers():
            haystack = " ".join([customer.id, customer.name, customer.email, customer.phone]).lower()
            if normalized in haystack:
                return customer
        return None

    def voice_guidelines(self) -> str:
        return self.config.voice_guidelines_path.read_text(encoding="utf-8")

    def recent_context(self) -> list[dict[str, Any]]:
        data = json.loads(self.config.conversation_context_path.read_text(encoding="utf-8") or "{}")
        recent = data.get("recent", []) if isinstance(data, dict) else []
        return [item for item in recent if isinstance(item, dict)]

    def add_recent_context(self, entry: dict[str, Any], max_items: int = 25) -> None:
        recent = self.recent_context()
        recent.append({"timestamp": _now_iso(), **entry})
        self.config.conversation_context_path.write_text(
            json.dumps({"recent": recent[-max_items:]}, indent=2) + "\n",
            encoding="utf-8",
        )

    def log_interaction(self, entry: dict[str, Any]) -> dict[str, Any]:
        record = {"timestamp": _now_iso(), **entry}
        with self.config.interaction_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def update_last_contact(self, customer_id: str, when: str | None = None) -> CustomerRecord | None:
        customers = self.load_customers()
        for customer in customers:
            if customer.id == customer_id:
                customer.last_contact = when or _now_iso()
                self.save_customers(customers)
                return customer
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
