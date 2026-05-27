from __future__ import annotations

from dataclasses import asdict

from operator_mvp.config import OperatorConfig, load_operator_config
from operator_mvp.memory import OperatorMemory
from operator_mvp.skills import OperatorSkills, SkillResult, select_skill


class OperatorAgent:
    """Boring service-business agent loop.

    Loop: receive input -> check memory -> select skill -> execute -> log result.
    """

    def __init__(self, config: OperatorConfig):
        self.config = config
        self.memory = OperatorMemory(config)
        self.skills = OperatorSkills(self.memory)

    @classmethod
    def from_config_file(cls, path: str = "operator.config.yaml") -> "OperatorAgent":
        return cls(load_operator_config(path))

    def handle(self, request: str, customer_query: str | None = None, skill_name: str | None = None) -> SkillResult:
        customer = self.memory.find_customer(customer_query or request)
        selected_skill = skill_name or select_skill(request)
        result = self.skills.execute(selected_skill, request, customer)
        self.memory.add_recent_context(
            {
                "request": request,
                "selected_skill": selected_skill,
                "customer_id": customer.id if customer else None,
                "customer_name": customer.name if customer else None,
            }
        )
        self.memory.log_interaction(
            {
                "type": "operator_result",
                "selected_skill": selected_skill,
                "customer_id": customer.id if customer else None,
                "customer_name": customer.name if customer else None,
                "request": request,
                "result_metadata": result.metadata,
            }
        )
        return result

    def status(self) -> dict:
        return {
            "business_name": self.config.business_name,
            "owner_name": self.config.owner_name,
            "model": asdict(self.config.model),
            "skills": self.skills.names,
            "crm_path": str(self.config.crm_path),
            "voice_guidelines_path": str(self.config.voice_guidelines_path),
            "conversation_context_path": str(self.config.conversation_context_path),
            "interaction_log_path": str(self.config.interaction_log_path),
            "customers": len(self.memory.load_customers()),
        }
