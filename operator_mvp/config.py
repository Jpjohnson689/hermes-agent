from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path("operator.config.yaml")


@dataclass(slots=True)
class OperatorModelConfig:
    provider: str = "openai-codex"
    model: str = "gpt-5.5"
    oauth_provider: str = "openai-codex"


@dataclass(slots=True)
class OperatorDataSources:
    crm_path: Path = Path("data/crm.json")
    voice_guidelines_path: Path = Path("data/voice_guidelines.md")
    conversation_context_path: Path = Path("data/conversation_context.json")
    interaction_log_path: Path = Path("data/interactions.jsonl")


@dataclass(slots=True)
class OperatorCommunicationConfig:
    email_address: str = ""
    email_imap_host: str = ""
    email_smtp_host: str = ""
    sms_provider: str = "twilio"
    sms_from_number: str = ""


@dataclass(slots=True)
class OperatorConfig:
    business_name: str
    owner_name: str
    model: OperatorModelConfig = field(default_factory=OperatorModelConfig)
    data_sources: OperatorDataSources = field(default_factory=OperatorDataSources)
    communication: OperatorCommunicationConfig = field(default_factory=OperatorCommunicationConfig)
    base_dir: Path = Path(".")

    @property
    def crm_path(self) -> Path:
        return _resolve(self.base_dir, self.data_sources.crm_path)

    @property
    def voice_guidelines_path(self) -> Path:
        return _resolve(self.base_dir, self.data_sources.voice_guidelines_path)

    @property
    def conversation_context_path(self) -> Path:
        return _resolve(self.base_dir, self.data_sources.conversation_context_path)

    @property
    def interaction_log_path(self) -> Path:
        return _resolve(self.base_dir, self.data_sources.interaction_log_path)


def _resolve(base_dir: Path, value: Path) -> Path:
    return value if value.is_absolute() else base_dir / value


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"operator config section '{key}' must be a mapping")
    return value


def load_operator_config(path: str | Path = DEFAULT_CONFIG_PATH) -> OperatorConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Operator config not found: {config_path}. Copy operator.config.example.yaml "
            "to operator.config.yaml and update the business settings."
        )

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("operator config root must be a mapping")
    raw = _expand_env(raw)

    business_name = str(raw.get("business_name") or "").strip()
    owner_name = str(raw.get("owner_name") or "").strip()
    if not business_name:
        raise ValueError("operator config requires business_name")
    if not owner_name:
        raise ValueError("operator config requires owner_name")

    model_raw = _section(raw, "model")
    data_raw = _section(raw, "data_sources")
    comm_raw = _section(raw, "communication")

    base_dir = config_path.parent.resolve()
    return OperatorConfig(
        business_name=business_name,
        owner_name=owner_name,
        model=OperatorModelConfig(
            provider=str(model_raw.get("provider") or "openai-codex"),
            model=str(model_raw.get("model") or "gpt-5.5"),
            oauth_provider=str(model_raw.get("oauth_provider") or model_raw.get("provider") or "openai-codex"),
        ),
        data_sources=OperatorDataSources(
            crm_path=Path(str(data_raw.get("crm_path") or "data/crm.json")),
            voice_guidelines_path=Path(str(data_raw.get("voice_guidelines_path") or "data/voice_guidelines.md")),
            conversation_context_path=Path(str(data_raw.get("conversation_context_path") or "data/conversation_context.json")),
            interaction_log_path=Path(str(data_raw.get("interaction_log_path") or "data/interactions.jsonl")),
        ),
        communication=OperatorCommunicationConfig(
            email_address=str(comm_raw.get("email_address") or ""),
            email_imap_host=str(comm_raw.get("email_imap_host") or ""),
            email_smtp_host=str(comm_raw.get("email_smtp_host") or ""),
            sms_provider=str(comm_raw.get("sms_provider") or "twilio"),
            sms_from_number=str(comm_raw.get("sms_from_number") or ""),
        ),
        base_dir=base_dir,
    )
