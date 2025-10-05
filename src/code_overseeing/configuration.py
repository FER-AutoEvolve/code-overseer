import dataclasses
from typing import List

from core import Result

__DEFAULT_CODE_DIRECTORY_PATH__ = "./codebase"
__DEFAULT_CODE_STAGING_DIRECTORY_PATH__ = "./codebase_staging"

@dataclasses.dataclass(frozen=True)
class CodeOverseerConfiguration:
    '''
    Configuration for the Code Overseer module.
    '''
    code_directory_path: str
    reprompt_on_change: bool = False
    ignore_patterns: List[str] = dataclasses.field(default_factory=list)
    include_only_patterns: List[str] = dataclasses.field(default_factory=list)
    code_staging_directory_path: str = dataclasses.field(default=__DEFAULT_CODE_STAGING_DIRECTORY_PATH__)

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
                , reprompt_on_change=settings.get("RepromptOnChange", False)
                , code_staging_directory_path=settings.get("CodeStagingDirectory", __DEFAULT_CODE_STAGING_DIRECTORY_PATH__)
            ))
        except ValueError as e:
            return Result.err(f"Invalid Code Overseer settings: {e}")