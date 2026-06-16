import dataclasses
import logging
from typing import List, Optional

from code_overseeing.code_commands import CodeCommand
from core import Result
import openai
from prompting import BasePromptManager
from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeChangeCommandsRepromptContext, GetCodeFixCommandsPromptContext
from prompting.qwen_3_6_27B.configuration import Qwen3627bConfiguration
from prompting.qwen_3_6_27B.prompts import GetCodeChangeCommandsPrompt, GetCodeChangeCommandsReprompt, GetCodeFixCommandsPrompt


@dataclasses.dataclass(frozen=True)
class PromptManager(BasePromptManager):
    '''Manages prompts to the Qwen 3.6 27B API.'''
    _configuration: Qwen3627bConfiguration = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def __post_init__(self):
        object.__setattr__(self, '_configuration', Qwen3627bConfiguration.from_dict(self._prompting_configuration.provider_config).unwrap())

    def execute_raw_prompt(self, prompt_text: str) -> Result[str]:
        try:
            client = openai.Client(
                base_url=self._configuration.url,
                api_key=self._configuration.api_key,
                timeout=self._configuration.timeout,
                default_headers=self._configuration.headers
            )
            response = client.chat.completions.create(
                model=self._configuration.model,
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
        prompt = GetCodeChangeCommandsPrompt(self._configuration, self._logger)
        return prompt.execute(prompt_context)

    def execute_code_change_reprompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        self._logger.info("Preparing code change reprompt context")

        prompt_context = GetCodeChangeCommandsRepromptContext(
            strategic_change_description=strategic_description,
            code_file_paths=code_file_paths,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy
        )
        prompt = GetCodeChangeCommandsReprompt(self._configuration, self._logger)
        return prompt.execute(prompt_context)

    def execute_code_fix_prompt(self, strategic_description: str, error_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        self._logger.info("Preparing code fix prompt context")

        prompt_context = GetCodeFixCommandsPromptContext(
            strategic_change_description=strategic_description,
            code_file_paths=code_file_paths,
            error_description=error_description,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy
        )
        prompt = GetCodeFixCommandsPrompt(self._configuration, self._logger)
        return prompt.execute(prompt_context)