# Operator

Operator is a focused AI business assistant for service business owners. It helps manage customer lifecycle work, draft customer communications in the owner's voice, identify follow-up opportunities, summarize customer history, and log interactions.

This MVP was forked from Hermes Agent and stripped down for predictable service-business workflows.

## What Operator does

- Reads a simple CRM file.
- Reads the owner's voice guidelines.
- Chooses one predictable skill for each request.
- Produces a draft or recommendation.
- Logs what happened.

Operator is intentionally not a general-purpose agent.

## Built-in skills

- `draft_customer_email`, draft an email in the owner's voice.
- `identify_followup_opportunities`, find customers worth contacting.
- `summarize_customer_history`, summarize one customer's record.
- `log_interaction`, record a customer interaction.
- `suggest_next_action`, recommend the next lifecycle step.

## Setup

### 1. Install dependencies

From the repo root:

```bash
./setup-hermes.sh
```

If the script asks you to reload your shell, run the command it prints.

### 2. Configure Operator

Copy the example config:

```bash
cp operator.config.example.yaml operator.config.yaml
```

Open `operator.config.yaml` and update:

```yaml
business_name: "Your Business Name"
owner_name: "Your Name"

data_sources:
  crm_path: "data/crm.json"
  voice_guidelines_path: "data/voice_guidelines.md"
  conversation_context_path: "data/conversation_context.json"
  interaction_log_path: "data/interactions.jsonl"
```

For email and SMS, use environment variables rather than writing secrets into the file:

```bash
export OPERATOR_EMAIL_ADDRESS="you@example.com"
export OPERATOR_EMAIL_IMAP_HOST="imap.example.com"
export OPERATOR_EMAIL_SMTP_HOST="smtp.example.com"
export OPERATOR_SMS_FROM_NUMBER="+15551234567"
```

### 3. Prepare CRM data

Edit `data/crm.json`:

```json
{
  "customers": [
    {
      "id": "maya-thompson",
      "name": "Maya Thompson",
      "email": "maya@example.com",
      "phone": "+15555551010",
      "lifecycle_stage": "past customer",
      "last_contact": "2026-04-18",
      "notes": ["Bought a premium beard oil set as a gift."],
      "preferences": ["luxury packaging", "subtle sandalwood scent"],
      "purchases": ["Signature Beard Oil Set"]
    }
  ]
}
```

### 4. Add voice guidelines

Edit `data/voice_guidelines.md` with sample emails, tone notes, and brand rules.

Example:

```markdown
- Voice: polished, concise, warm, personally attentive.
- Avoid pressure, hype, and generic ecommerce copy.
- Make recommendations feel curated and practical.
```

## Run Operator

Show status:

```bash
python -m operator_mvp.cli --config operator.config.yaml status
```

Draft an email:

```bash
python -m operator_mvp.cli --config operator.config.yaml run "draft an email to Maya Thompson about a reorder" --customer "Maya Thompson"
```

Find follow-up opportunities:

```bash
python -m operator_mvp.cli --config operator.config.yaml run "identify follow-up opportunities"
```

Summarize a customer:

```bash
python -m operator_mvp.cli --config operator.config.yaml run "summarize customer history" --customer "Marcus Hill"
```

## First Eaden test request

Command:

```bash
python -m operator_mvp.cli --config operator.config.yaml run "draft an email to Maya Thompson, a past customer, about replenishing her husband's grooming kit" --customer "Maya Thompson"
```

Expected behavior:

- Operator finds Maya in CRM.
- Operator reads Eaden's voice guidelines.
- Operator selects `draft_customer_email`.
- Operator produces a draft only.
- Operator logs the result in `data/interactions.jsonl`.

## Current authentication

The baseline Hermes fork was verified with GPT-5.5 through OpenAI Codex OAuth. The Operator MVP code path does not require a live model call for deterministic skills yet, but the config keeps the model settings for later LLM refinement.

## Safety rules

- Operator drafts external customer communications by default.
- Sending email or SMS should be added only behind explicit approval rules.
- Secrets belong in environment variables, not in `operator.config.yaml`.

## Divergence log

See `DECISIONS.md` for the implementation decisions and known tech debt.
