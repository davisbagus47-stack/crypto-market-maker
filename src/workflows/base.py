from dataclasses import dataclass


@dataclass
class WorkflowDefinition:
    key: str
    name: str
    route: str
    strategy: str
    required_fields: list[str]
    risk: str


class BaseWorkflow:
    definition: WorkflowDefinition

    def prepare_payload(self, mapped_data: dict) -> dict:
        return mapped_data

    def validate_business_rules(self, mapped_data: dict) -> list[str]:
        return []
