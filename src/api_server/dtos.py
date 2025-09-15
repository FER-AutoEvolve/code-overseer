from dataclasses import dataclass


@dataclass(frozen=True)
class CodeChangeRequest:
    change_strategic_description: str