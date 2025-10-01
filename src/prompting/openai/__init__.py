from abc import abstractmethod
import dataclasses
from typing import List, Optional

from code_overseeing.code_commands import CodeCommand
from configuration import PromptingConfiguration
from core import Result
from prompting import BasePromptManager
from prompting.openai.configuration import OpenAiConfiguration
from prompting.openai.prompts import GetCodeChangeCommandsPrompt, GetCodeChangeCommandsReprompt
import logging
import openai

from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeChangeCommandsRepromptContext

@dataclasses.dataclass(frozen=True)
class PromptManager(BasePromptManager):
    '''
    Manages prompts to the OpenAI API.
    Attributes:
        _openai_configuration (OpenAiConfiguration): Configuration for OpenAI API access.
        _logger (logging.Logger): Logger for logging information and errors.
    '''
    _openai_configuration: OpenAiConfiguration = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self):
        object.__setattr__(self, '_openai_configuration', OpenAiConfiguration.from_dict(self._prompting_configuration.provider_config).unwrap())

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

    def execute_code_change_commands_prompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        self._logger.info("Preparing code change commands prompt context")
        
        prompt_context = GetCodeChangeCommandsPromptContext(
            strategic_change_description=strategic_description,
            code_file_paths=code_file_paths,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy
        )
        prompt = GetCodeChangeCommandsPrompt(self._openai_configuration, self._logger)
        return prompt.execute(prompt_context)
    
    def execute_code_change_reprompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        self._logger.info("Preparing code change reprompt context")
        
        prompt_context = GetCodeChangeCommandsRepromptContext(
            strategic_change_description=strategic_description,
            code_file_paths=code_file_paths,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy
        )
        prompt = GetCodeChangeCommandsReprompt(self._openai_configuration, self._logger)
        return prompt.execute(prompt_context)