from abc import abstractmethod
import dataclasses
from typing import List

from code_overseeing.code_commands import CodeCommand
from core import Result
from prompting import IPromptManager
from prompting.openai.configuration import OpenAiConfiguration
from prompting.openai.prompts import GetCodeChangeCommandsPrompt
import logging
import openai

@dataclasses.dataclass(frozen=True)
class PromptManager(IPromptManager):
    '''
    Manages prompts to the OpenAI API.
    Attributes:
        _openai_configuration (OpenAiConfiguration): Configuration for OpenAI API access.
        _logger (logging.Logger): Logger for logging information and errors.
    '''
    _openai_configuration: OpenAiConfiguration
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def execute_raw_prompt(self, prompt_text: str) -> Result[str]:
        try:
            client = openai.OpenAI(api_key=self._openai_configuration.api_key)
            response = client.chat.completions.create(
                model=self._openai_configuration.model,
                messages=[
                    {"role": "user", "content": prompt_text}
                ]
            )
            return Result.ok(response.choices[0].message.content)
        except Exception as e:
            return Result.err(f"Error executing prompt: {e}")

    def execute_code_change_commands_prompt(self, context: dict) -> Result[List[CodeCommand]]:
        prompt = GetCodeChangeCommandsPrompt(self._openai_configuration, self._logger)
        return prompt.execute(context)