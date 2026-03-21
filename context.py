"""
core/context.py

Shared dataset context passed to every agent at invocation time
via create_agent's context_schema parameter.

This is NOT agent state — it does not persist between invocations or
accumulate over time. It is the fixed facts about the dataset and the
user's domain that every agent needs to do its job correctly.

Usage:
    from context import DatasetContext

    context = DatasetContext(
        file_path="data/churn.csv",
        dataset_description="Monthly churn snapshot for Q3 2024.",
        column_descriptions={
            "churn": "1 = churned (bad), 0 = retained",
            "credits": "Billing credits — high values indicate disputes",
            "plan_type": "Subscription tier: prepaid, postpaid, enterprise",
        },
        business_rules=[
            "credits: high = bad — indicates billing disputes or failures",
            "churn: 1 = bad outcome, 0 = good",
            "arpu: higher = better",
        ]
    )

    # Pass to any agent at invocation time
    result = agent.invoke({"messages": [...]}, context=context)
"""

from typing import Optional
from pydantic import BaseModel, Field


class DatasetContext(BaseModel):
    """
    Fixed facts about the dataset shared across all agents.

    Agents receive this at runtime and use it to ground their reasoning
    in the actual data — referencing real column names, respecting business
    rules, and understanding what the data represents.
    """

    file_path: str = Field(
        description=(
            "Local file path or URL to the dataset. "
            "Examples: 'data/churn.csv', 'https://example.com/data.csv'"
        )
    )

    dataset_description: str = Field(
        description=(
            "Plain-English description of what this dataset represents. "
            "Should answer: what is being measured, over what time period, "
            "and for what population. "
            "Example: 'Monthly snapshot of active mobile subscribers as of "
            "billing cycle close, Q3 2024. Each row is one customer account.'"
        )
    )

    column_descriptions: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Mapping of column name to human-readable description. "
            "Agents use this to understand what each column means before "
            "writing code or running analysis. "
            "Example: {'churn': '1 = churned, 0 = retained', "
            "'credits': 'Billing credits — high values indicate disputes'}"
        )
    )

    business_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Domain rules that govern how metric values should be interpreted. "
            "These override any assumptions the agent might make from column "
            "names alone. Always include direction rules for key metrics. "
            "Example: ['credits: high = bad — billing disputes', "
            "'arpu: higher = better', 'churn: 1 = bad outcome']"
        )
    )

    sensitivity: Optional[str] = Field(
        default=None,
        description=(
            "Data sensitivity level: 'public', 'internal', or 'sensitive'. "
            "Agents use this to apply appropriate handling — e.g. avoiding "
            "outputting raw PII, flagging compliance concerns in the plan. "
            "Leave None if not applicable."
        )
    )

    known_issues: list[str] = Field(
        default_factory=list,
        description=(
            "Known data quality problems the agents should be aware of. "
            "Example: ['churn column has 3% nulls', "
            "'tenure_months capped at 60 — values above are truncated', "
            "'enterprise segment has only 45 records — small sample']"
        )
    )

    def to_prompt_block(self) -> str:
        """
        Render the context as a formatted string block suitable for
        injecting into a system prompt or as additional context in a
        human message.

        Useful when you need to pass context to a component that does
        not support context_schema natively.
        """
        lines = [
            "## Dataset Context",
            f"File: {self.file_path}",
            f"Description: {self.dataset_description}",
        ]

        if self.sensitivity:
            lines.append(f"Sensitivity: {self.sensitivity}")

        if self.column_descriptions:
            lines.append("\nColumn descriptions:")
            for col, desc in self.column_descriptions.items():
                lines.append(f"  - {col}: {desc}")

        if self.business_rules:
            lines.append("\nBusiness rules (treat as authoritative):")
            for rule in self.business_rules:
                lines.append(f"  - {rule}")

        if self.known_issues:
            lines.append("\nKnown data quality issues:")
            for issue in self.known_issues:
                lines.append(f"  - {issue}")

        return "\n".join(lines)