from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from operator_mvp.memory import CustomerRecord, OperatorMemory
from operator_mvp.refine import refine_email_with_hermes


@dataclass(slots=True)
class SkillResult:
    skill: str
    output: str
    metadata: dict


class OperatorSkills:
    """Predictable, non-self-modifying skill library for service businesses."""

    def __init__(self, memory: OperatorMemory):
        self.memory = memory
        self._skills: dict[str, Callable[[str, CustomerRecord | None], SkillResult]] = {
            "draft_customer_email": self.draft_customer_email,
            "identify_followup_opportunities": self.identify_followup_opportunities,
            "summarize_customer_history": self.summarize_customer_history,
            "log_interaction": self.log_interaction,
            "suggest_next_action": self.suggest_next_action,
        }

    @property
    def names(self) -> list[str]:
        return list(self._skills)

    def execute(self, name: str, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        if name not in self._skills:
            raise ValueError(f"Unknown Operator skill '{name}'. Available skills: {', '.join(self.names)}")
        return self._skills[name](request, customer)

    def draft_customer_email(self, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        customer = customer or _anonymous_customer()
        guidelines = self.memory.voice_guidelines().strip()
        subject = _subject_for(customer)
        detail_lines = []
        if customer.preferences:
            detail_lines.append(f"I remembered your preferences: {', '.join(customer.preferences)}.")
        if customer.purchases:
            detail_lines.append(f"Your previous order history is top of mind: {', '.join(customer.purchases)}.")
        if customer.notes:
            detail_lines.append(f"Context I kept in mind: {'; '.join(customer.notes)}.")
        context_sentence = " ".join(detail_lines)

        body = f"Subject: {subject}\n\nHi {customer.name},\n\n"
        if customer.lifecycle_stage.lower() in {"past customer", "repeat customer", "vip"}:
            body += "I was thinking about your last order and wanted to check in personally. "
        else:
            body += "I wanted to reach out personally and make sure you are taken care of. "
        if context_sentence:
            body += context_sentence + " "
        body += (
            "If you are ready, I can help you choose the right grooming pieces for your current routine "
            "or put together a simple recommendation based on what has worked for you before.\n\n"
            "Best,\n"
            f"{self.memory.config.owner_name}\n"
            f"{self.memory.config.business_name}"
        )

        try:
            refined = refine_email_with_hermes(body, guidelines)
        except Exception as e:
            refined = body + f"\n\n[Hermes refinement failed: {e}]"

        return SkillResult(
            skill="draft_customer_email",
            output=refined + "\n\n---\nVoice guidance used:\n" + _compact(guidelines, 900),
            metadata={"customer_id": customer.id, "channel": "email", "draft_only": True},
        )

    def identify_followup_opportunities(self, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        customers = [customer] if customer else self.memory.load_customers()
        opportunities = []
        for record in customers:
            score = 0
            reasons = []
            stage = record.lifecycle_stage.lower()
            if stage in {"past customer", "vip", "repeat customer"}:
                score += 2
                reasons.append(f"stage is {record.lifecycle_stage}")
            if record.purchases:
                score += 1
                reasons.append("has prior purchase history")
            if not record.last_contact:
                score += 1
                reasons.append("no recent contact logged")
            if "vip" in [tag.lower() for tag in record.tags]:
                score += 2
                reasons.append("VIP tag")
            if score > 0:
                opportunities.append((score, record, reasons))
        opportunities.sort(key=lambda item: item[0], reverse=True)
        if not opportunities:
            text = "No follow-up opportunities found in the current CRM data."
        else:
            lines = ["Follow-up opportunities:"]
            for score, record, reasons in opportunities[:10]:
                lines.append(f"- {record.name}: priority {score}. Reason: {', '.join(reasons)}. Suggested channel: email first, SMS only for urgent or opted-in customers.")
            text = "\n".join(lines)
        return SkillResult("identify_followup_opportunities", text, {"count": len(opportunities)})

    def summarize_customer_history(self, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        if customer is None:
            return SkillResult("summarize_customer_history", "No matching customer found. Provide a customer name, email, or phone number.", {})
        lines = [
            f"Customer: {customer.name}",
            f"Stage: {customer.lifecycle_stage}",
            f"Last contact: {customer.last_contact or 'not logged'}",
            f"Email: {customer.email or 'not available'}",
            f"Phone: {customer.phone or 'not available'}",
        ]
        if customer.preferences:
            lines.append("Preferences: " + "; ".join(customer.preferences))
        if customer.purchases:
            lines.append("Purchases: " + "; ".join(customer.purchases))
        if customer.notes:
            lines.append("Notes: " + "; ".join(customer.notes))
        return SkillResult("summarize_customer_history", "\n".join(lines), {"customer_id": customer.id})

    def log_interaction(self, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        record = self.memory.log_interaction({
            "customer_id": customer.id if customer else None,
            "customer_name": customer.name if customer else None,
            "request": request,
            "source": "operator_cli",
        })
        if customer:
            self.memory.update_last_contact(customer.id, record["timestamp"])
        return SkillResult("log_interaction", f"Logged interaction at {record['timestamp']}", record)

    def suggest_next_action(self, request: str, customer: CustomerRecord | None = None) -> SkillResult:
        if customer is None:
            return SkillResult(
                "suggest_next_action",
                "Next action: identify the customer first, then summarize their history before drafting outreach.",
                {},
            )
        stage = customer.lifecycle_stage.lower()
        if stage in {"past customer", "repeat customer", "vip"}:
            action = "Draft a personal check-in email with a tailored product recommendation."
        elif stage in {"lead", "prospect"}:
            action = "Draft a short introduction and ask one low-friction preference question."
        else:
            action = "Summarize the customer record, then choose email for detailed follow-up."
        return SkillResult("suggest_next_action", f"Next action for {customer.name}: {action}", {"customer_id": customer.id})


def select_skill(request: str) -> str:
    text = request.lower()
    if any(word in text for word in ["draft", "email", "write", "reply"]):
        return "draft_customer_email"
    if any(word in text for word in ["opportun", "follow up", "follow-up", "followup"]):
        return "identify_followup_opportunities"
    if any(word in text for word in ["summarize", "summary", "history", "who is"]):
        return "summarize_customer_history"
    if any(word in text for word in ["log", "record interaction", "note this"]):
        return "log_interaction"
    return "suggest_next_action"


def _anonymous_customer() -> CustomerRecord:
    return CustomerRecord(id="unknown", name="there", lifecycle_stage="unknown")


def _subject_for(customer: CustomerRecord) -> str:
    if customer.lifecycle_stage.lower() in {"vip", "repeat customer"}:
        return "A personal recommendation for you"
    if customer.lifecycle_stage.lower() == "past customer":
        return "Checking in on your grooming routine"
    return "A quick note from your grooming team"


def _compact(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."
