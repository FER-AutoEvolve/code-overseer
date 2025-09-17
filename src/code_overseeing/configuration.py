import dataclasses
from typing import List

from core import Result

__DEFAULT_CODE_DIRECTORY_PATH__ = "./codebase"

@dataclasses.dataclass(frozen=True)
class CodeOverseerConfiguration:
    '''
    Configuration for the Code Overseer module.
    '''
    code_directory_path: str
    ignore_patterns: List[str] = dataclasses.field(default_factory=list)
    include_only_patterns: List[str] = dataclasses.field(default_factory=list)

    @staticmethod
    def from_dict(settings: dict) -> Result['CodeOverseerConfiguration']:
        '''
        Creates a CodeOverseerConfiguration from a dictionary of settings.
        Args:
            settings (dict): A dictionary containing configuration settings.
        Returns:
            Result[CodeOverseerConfiguration]: A Result object containing the configuration or an error message.
        '''
        try:
            return Result.ok(CodeOverseerConfiguration(
                code_directory_path=settings.get("CodeDirectory", __DEFAULT_CODE_DIRECTORY_PATH__)
                , ignore_patterns=settings.get("IgnorePatterns", [])
                , include_only_patterns=settings.get("IncludeOnlyPatterns", [])
            ))
        except ValueError as e:
            return Result.err(f"Invalid Code Overseer settings: {e}")