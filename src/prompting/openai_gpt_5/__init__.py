import dataclasses
import logging
from typing import List, Optional

import openai

from code_overseeing.code_commands import CodeCommand
from core import Result
from prompting import BasePromptManager
from prompting.openai_gpt_5.configuration import OpenAiConfiguration
from prompting.openai_gpt_5.prompts import GetCodeChangeCommandsPrompt, GetCodeChangeCommandsReprompt, GetCodeFixCommandsPrompt
from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeChangeCommandsRepromptContext, GetCodeFixCommandsPromptContext


@dataclasses.dataclass(frozen=True)
class PromptManager(BasePromptManager):
    _openai_configuration: OpenAiConfiguration = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def __post_init__(self):
        provider_config = {
            **self._prompting_configuration.provider_config,
            "Model": "gpt-5",
        }
        object.__setattr__(
            self,
            "_openai_configuration",
            OpenAiConfiguration.from_dict(provider_config).unwrap(),
        )

    def execute_raw_prompt(self, prompt_text: str) -> Result[str]:
        try:
            client = openai.OpenAI(api_key=self._openai_configuration.api_key)
            response = client.chat.completions.create(
                model=self._openai_configuration.model,
                messages=[{"role": "user", "content": prompt_text}],
            )
            return Result.ok(response.choices[0].message.content)
        except Exception as error:
            return Result.err(f"Error executing prompt: {error}")

    def execute_code_change_commands_prompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        prompt_context = GetCodeChangeCommandsPromptContext(
            strategic_change_description=strategic_description,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy,
            code_file_paths=code_file_paths,
        )
        return GetCodeChangeCommandsPrompt(self._openai_configuration, self._logger).execute(prompt_context)

    def execute_code_change_reprompt(self, strategic_description: str, code_file_paths: Optional[List[str]], reprompt_number: Optional[int] = None) -> Result[List[CodeCommand]]:
        prompt_context = GetCodeChangeCommandsRepromptContext(
            strategic_change_description=strategic_description,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy,
            code_file_paths=code_file_paths,
            reprompt_number=reprompt_number,
        )
        return GetCodeChangeCommandsReprompt(self._openai_configuration, self._logger).execute(prompt_context)

    def execute_code_fix_prompt(self, strategic_description: str, error_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        prompt_context = GetCodeFixCommandsPromptContext(
            strategic_change_description=strategic_description,
            error_description=error_description,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy,
            code_file_paths=code_file_paths,
        )
        return GetCodeFixCommandsPrompt(self._openai_configuration, self._logger).execute(prompt_context)