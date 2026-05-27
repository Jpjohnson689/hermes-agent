# DECISIONS.md

This file records meaningful Operator MVP divergences from Hermes Agent.

## 2026-05-27, Fork and baseline

- Forked `NousResearch/hermes-agent` into `Jpjohnson689/hermes-agent` and created branch `operator-mvp`.
- Kept the fork history intact so upstream Hermes changes can still be inspected or cherry-picked while Operator is being proven.
- Renamed the local working directory to `Operator` and changed Python package metadata from `hermes-agent` to `operator-agent`.
- Ran the Hermes setup script. `./install.sh` did not exist, so `setup-hermes.sh` was used instead. It created the virtual environment and installed dependencies from `uv.lock`.
- Baseline model verification uses OpenAI Codex OAuth with `gpt-5.5`, not Anthropic Claude API. This is intentional because Jon confirmed GPT/Codex OAuth is the available authentication path. An attempted Anthropic config produced HTTP 401 and was reverted.

## Product scope

- Operator is not a general-purpose agent. It is a focused customer lifecycle operator for service business owners.
- The MVP optimizes for predictable behavior over autonomous self-improvement.
- The first customer profile is Eaden Myles, a luxury boutique men's grooming business owner.

## Messaging integrations

- Removed gateway platform adapter files for Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost-style chat, DingTalk, Feishu, WeCom, Weixin, QQ Bot, Yuanbao, BlueBubbles, Home Assistant, API Server, webhooks, and Microsoft Graph webhooks.
- Kept only email and SMS gateway adapter files.
- Reduced the built-in `Platform` enum to `local`, `email`, and `sms`.
- Left some legacy references in large gateway support files as tech debt because removing every mention safely would exceed the 3-day MVP goal. Runtime creation of stripped built-in adapters is blocked, and adapter files are removed.

## Memory system

- Added `operator/memory.py` with flat file storage:
  - CRM data: `data/crm.json`
  - Voice guidelines: `data/voice_guidelines.md`
  - Recent conversation context: `data/conversation_context.json`
  - Interaction log: `data/interactions.jsonl`
- Did not use Hermes' self-improving memory provider for Operator MVP.
- Removed the nudge concept from the Operator loop. It adds autonomous behavior that is not necessary for Eaden's initial use case. Follow-up opportunities are handled through an explicit predictable skill instead.

## Skills

- Added `operator/skills.py` with a fixed skills library:
  - `draft_customer_email`
  - `identify_followup_opportunities`
  - `summarize_customer_history`
  - `log_interaction`
  - `suggest_next_action`
- Disabled autonomous skill creation for the Operator path by not exposing `skill_manage` or mutable skill creation in the Operator loop.
- Skills are deterministic Python functions for MVP speed and reliability. LLM-based copy refinement can be layered later behind the same skill names.

## Agent loop

- Added `operator/agent.py` implementing the required boring loop:
  1. receive input
  2. check memory
  3. select skill
  4. execute
  5. log result
- Skill selection is keyword-based for MVP predictability.
- Every run appends recent context and an interaction log record.

## Configuration layer

- Added `operator.config.example.yaml` and `operator.config.yaml`.
- Non-technical users can set:
  - business name
  - owner name
  - model/provider
  - CRM file path
  - voice guidelines file path
  - recent context path
  - email/SMS settings
- Secrets are referenced through environment variables, not committed into config.

## CLI

- Added `operator_mvp/cli.py` and an `operator` console script. The package is named `operator_mvp` to avoid colliding with Python's standard-library `operator` module.
- Commands:
  - `operator status`
  - `operator init-data`
  - `operator run "request" --customer "name"`
- Kept Hermes CLI entry points for now as compatibility scaffolding during the fork. Removing them completely is tech debt after the Operator path is stable.

## Sample data

- Added sample Eaden CRM records for Maya Thompson and Marcus Hill.
- Added voice guidelines tuned to a luxury boutique men's grooming brand.

## Tech debt

- Rename the GitHub repository from `hermes-agent` to `operator` after branch validation.
- Fully remove remaining legacy Hermes CLI and gateway references once the Operator CLI is accepted.
- Add real email and SMS send/draft integrations behind approval rules.
- Add LLM rewriting for `draft_customer_email` while preserving deterministic memory lookup, skill choice, and logging.
- Add a small non-technical desktop or web onboarding UI for `operator.config.yaml`.
