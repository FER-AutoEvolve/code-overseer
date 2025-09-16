import pydantic.dataclasses

def to_pascal_case(s: str) -> str:
    return ''.join(word.capitalize() for word in s.split('_'))

@pydantic.dataclasses.dataclass(config={"alias_generator": to_pascal_case, "populate_by_name": True}, frozen=True)
class CodeChangeRequest:
    change_strategic_description: str