from pydantic import BaseModel, Field


class ValidationRuleChange(BaseModel):
    id: str
    active: bool
    rule_name: str | None = None


class ValidationRuleDeployRequest(BaseModel):
    changes: list[ValidationRuleChange] = Field(default_factory=list)
