from __future__ import annotations

import json
from pathlib import Path

from operator_mvp.agent import OperatorAgent
from operator_mvp.config import load_operator_config
from operator_mvp.outbox import OperatorOutbox
from operator_mvp.skills import select_skill


def write_fixture(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    (tmp_path / "operator.config.yaml").write_text(
        """
business_name: Test Grooming
owner_name: Eaden Myles
data_sources:
  crm_path: data/crm.json
  voice_guidelines_path: data/voice.md
  conversation_context_path: data/context.json
  interaction_log_path: data/interactions.jsonl
  outbox_path: data/outbox
communication:
  email_address: test@example.com
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "data" / "crm.json").write_text(
        json.dumps(
            {
                "customers": [
                    {
                        "id": "maya",
                        "name": "Maya Thompson",
                        "email": "maya@example.com",
                        "lifecycle_stage": "past customer",
                        "notes": ["Gift buyer"],
                        "preferences": ["sandalwood"],
                        "purchases": ["Beard Oil"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "data" / "voice.md").write_text("Polished, concise, personal.", encoding="utf-8")
    (tmp_path / "data" / "context.json").write_text('{"recent": []}\n', encoding="utf-8")
    (tmp_path / "data" / "interactions.jsonl").write_text("", encoding="utf-8")
    return tmp_path / "operator.config.yaml"


def test_load_config_and_status(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    cfg = load_operator_config(path)
    agent = OperatorAgent(cfg)
    status = agent.status()
    assert status["business_name"] == "Test Grooming"
    assert status["customers"] == 1
    assert "draft_customer_email" in status["skills"]


def test_select_skill_is_predictable() -> None:
    assert select_skill("draft an email to Maya") == "draft_customer_email"
    assert select_skill("find follow up opportunities") == "identify_followup_opportunities"
    assert select_skill("summarize customer history") == "summarize_customer_history"


def test_draft_email_for_customer_logs_context(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    agent = OperatorAgent(load_operator_config(path))
    result = agent.handle("draft an email to Maya Thompson", customer_query="Maya")
    assert result.skill == "draft_customer_email"
    assert "Hi Maya Thompson" in result.output
    assert "Eaden Myles" in result.output
    assert "sandalwood" in result.output
    log_text = (tmp_path / "data" / "interactions.jsonl").read_text(encoding="utf-8")
    assert "draft_customer_email" in log_text


def test_outbox_creates_draft_only_email(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    cfg = load_operator_config(path)
    outbox = OperatorOutbox(cfg)

    draft = outbox.create_email_draft(
        to="maya@example.com",
        subject="Checking in",
        body="Hi Maya, this is a draft.",
        customer_id="maya",
    )

    assert draft["status"] == "draft_pending_approval"
    assert draft["channel"] == "email"
    assert draft["to"] == "maya@example.com"
    assert (tmp_path / "data" / "outbox" / f"{draft['id']}.json").exists()


def test_setup_wizard_writes_nontechnical_config(tmp_path: Path) -> None:
    from operator_mvp.setup_wizard import write_config

    config_path = tmp_path / "operator.config.yaml"
    write_config(
        config_path,
        business_name="Boutique Grooming",
        owner_name="Eaden Myles",
        email_address="eaden@example.com",
        sms_from_number="+155****4567",
    )

    cfg = load_operator_config(config_path)
    assert cfg.business_name == "Boutique Grooming"
    assert cfg.owner_name == "Eaden Myles"
    assert cfg.communication.email_address == "eaden@example.com"
