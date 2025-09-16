import dataclasses

from core import Result

__DEFAULT_CODE_DIRECTORY__ = "./codebase"

@dataclasses.dataclass(frozen=True)
class CodeOverseerConfiguration:
    code_directory: str

    @staticmethod
    def from_dict(settings: dict) -> Result['CodeOverseerConfiguration']:
        try:
            return Result.ok(CodeOverseerConfiguration(
                code_directory=settings.get("CodeDirectory", __DEFAULT_CODE_DIRECTORY__)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Code Overseer settings: {e}")