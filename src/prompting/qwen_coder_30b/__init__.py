from abc import abstractmethod
import dataclasses
from typing import List, Optional
from code_overseeing.code_commands import CodeCommand
from core import Result
from prompting import BasePromptManager
from prompting.qwen_coder_30b.configuration import QwenCoder30bConfiguration
from prompting.qwen_coder_30b.prompts import GetCodeChangeCommandsPrompt, GetCodeChangeCommandsReprompt
import logging
import openai

from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeChangeCommandsRepromptContext, GetCodeFixCommandsPromptContext

@dataclasses.dataclass(frozen=True)
class PromptManager(BasePromptManager):
    '''
    Manages prompts to the Qwen Coder 30B API (OpenAI-compatible server).
    Attributes:
        _qwen_configuration (QwenCoder30bConfiguration): Configuration for Qwen Coder 30B API access.
        _logger (logging.Logger): Logger for logging information and errors.
    '''
    _qwen_configuration: QwenCoder30bConfiguration = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def __post_init__(self):
        object.__setattr__(self, '_qwen_configuration', QwenCoder30bConfiguration.from_dict(self._prompting_configuration.provider_config).unwrap())

    def execute_raw_prompt(self, prompt_text: str) -> Result[str]:
        try:
            client = openai.Client(
                base_url=self._qwen_configuration.url, 
                api_key=self._qwen_configuration.api_key,
                timeout=self._qwen_configuration.timeout,
                default_headers=self._qwen_configuration.headers
            )
            response = client.chat.completions.create(
                model=self._qwen_configuration.model,
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
        prompt = GetCodeChangeCommandsPrompt(self._qwen_configuration, self._logger)
        return prompt.execute(prompt_context)
    
    def execute_code_change_reprompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        self._logger.info("Preparing code change reprompt context")
        
        prompt_context = GetCodeChangeCommandsRepromptContext(
            strategic_change_description=strategic_description,
            code_file_paths=code_file_paths,
            codebase_description=self._prompting_configuration.codebase_description,
            code_command_strategy=self._prompting_configuration.code_command_strategy
        )
        prompt = GetCodeChangeCommandsReprompt(self._qwen_configuration, self._logger)
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
        prompt = GetCodeChangeCommandsReprompt(self._qwen_configuration, self._logger)
        return prompt.execute(prompt_context)
