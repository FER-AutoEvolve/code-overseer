import dataclasses
import logging
from typing import List, Optional
from code_overseeing.code_commands import CodeCommand
from core import Result
from prompting import IGetCodeChangeCommandsPrompt
import openai
from configuration import OpenAiConfiguration

@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPrompt(IGetCodeChangeCommandsPrompt):
    '''Implementation of IGetCodeChangeCommandsPrompt using OpenAI API.'''
    _openai_settings: OpenAiConfiguration
    _openai_client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_openai_client', openai.OpenAI(api_key=self._openai_settings.api_key))

    def execute(self, context: dict) -> Result[List[CodeCommand]]:
        # TODO: Implementation to interact with OpenAI API and get code change commands
        return Result.ok([])  # Placeholder return

    