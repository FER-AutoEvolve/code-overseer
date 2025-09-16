import pydantic.dataclasses

def to_pascal_case(s: str) -> str:
    '''
    Converts a snake_case string to PascalCase.
    '''
    return ''.join(word.capitalize() for word in s.split('_'))

@pydantic.dataclasses.dataclass(config={"alias_generator": to_pascal_case, "populate_by_name": True}, frozen=True)
class CodeChangeRequest:
    '''
    DTO for a code change request.
    '''    
    change_strategic_description: str
    '''
    A high-level description of the code change.
    '''