import dataclasses

from core import Result

__DEFAULT_CODE_DIRECTORY_PATH__ = "./codebase"

@dataclasses.dataclass(frozen=True)
class CodeOverseerConfiguration:
    '''
    Configuration for the Code Overseer module.
    '''
    code_directory_path: str

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
            ))
        except ValueError as e:
            return Result.err(f"Invalid Code Overseer settings: {e}")