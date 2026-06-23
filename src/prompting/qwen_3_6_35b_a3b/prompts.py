import dataclasses
import logging
from typing import List

from code_overseeing.code_commands import CodeCommand
from configuration import CodeCommandStrategies
from core import Result
import openai
from prompting.gpt_oss_20b.prompts import _parse_response, _set_line_markers
from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeFixCommandsPromptContext, IGetCodeChangeCommandsPrompt, GetCodeChangeCommandsRepromptContext, IGetCodeChangeCommandsReprompt, IGetCodeFixCommandsPrompt
from prompting.qwen_3_6_35b_a3b.configuration import Qwen3635bA3bConfiguration

__PROVIDER_SPECIFIC_PROMPTING_INSTRUCTIONS__: str = """
DON'T provide markdown code annotations in your response.
ALWAYS provide the complete code for the file. DO NOT use comments or placeholders like // ...existing code or // ...existing imports. Output the full file content as it should appear after changes.
"""


def _extract_response_text(response: object) -> Result[str]:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return Result.ok(output_text)

    text_chunks: List[str] = []
    for item in getattr(response, "output", []) or []:
        for content_item in getattr(item, "content", []) or []:
            text_value = getattr(content_item, "text", None)
            if isinstance(text_value, str) and text_value:
                text_chunks.append(text_value)
                continue

            nested_value = getattr(text_value, "value", None)
            if isinstance(nested_value, str) and nested_value:
                text_chunks.append(nested_value)

    if text_chunks:
        return Result.ok("\n".join(text_chunks))

    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        message_content = getattr(message, "content", None)
        if isinstance(message_content, str) and message_content.strip():
            return Result.ok(message_content)
        if isinstance(message_content, list):
            message_text_chunks: List[str] = []
            for item in message_content:
                item_text = getattr(item, "text", None)
                if isinstance(item_text, str) and item_text:
                    message_text_chunks.append(item_text)
            if message_text_chunks:
                return Result.ok("\n".join(message_text_chunks))

    return Result.err("Response did not contain any readable text content")


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPrompt(IGetCodeChangeCommandsPrompt):
    '''Implementation of IGetCodeChangeCommandsPrompt using Qwen 3.6 35B A3B.'''
    _conf: Qwen3635bA3bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def __post_init__(self) -> None:
        object.__setattr__(self, '_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key,
            timeout=self._conf.timeout,
            default_headers=self._conf.headers
        ))

    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling Qwen 3.6 35B A3B API for code change commands with {len(context.code_file_paths)} code files")

            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt = f.read()
                    if context.code_command_strategy == CodeCommandStrategies.ADD_DELETE:
                        code_txt = _set_line_markers(code_txt)

                    file_data.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": f"FILE: {file_path}\n```{file_path}\n{code_txt}\n```"}
                            ]
                        }
                    )

            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction + "\n"
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble + __PROVIDER_SPECIFIC_PROMPTING_INSTRUCTIONS__
            },
            {
                "role": "user",
                "content": context.strategic_change_description
            }] + file_data

            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text_result = _extract_response_text(response)
            if response_text_result.is_err():
                return Result.err(response_text_result.message)

            response_text = response_text_result.unwrap()
            self._logger.debug("Qwen 3.6 35B A3B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE
            )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            return Result.ok(code_commands)

        except Exception as e:
            self._logger.error(f"Qwen 3.6 35B A3B API call failed: {e}")
            return Result.err(f"Qwen 3.6 35B A3B API call failed: {e}")


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsReprompt(IGetCodeChangeCommandsReprompt):
    '''Implementation of IGetCodeChangeReprompt using Qwen 3.6 35B A3B.'''
    _conf: Qwen3635bA3bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key,
            timeout=self._conf.timeout,
            default_headers=self._conf.headers
        ))

    def execute(self, context: GetCodeChangeCommandsRepromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling Qwen 3.6 35B A3B API for code change reprompt with {len(context.code_file_paths)} code files")

            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt = f.read()
                    if context.code_command_strategy == CodeCommandStrategies.ADD_DELETE:
                        code_txt = _set_line_markers(code_txt)

                    file_data.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": f"FILE: {file_path}\n```{file_path}\n{code_txt}\n```"}
                            ]
                        }
                    )

            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction + "\n"
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble + __PROVIDER_SPECIFIC_PROMPTING_INSTRUCTIONS__
            },
            {
                "role": "user",
                "content": context.strategic_change_description
            }] + file_data

            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text_result = _extract_response_text(response)
            if response_text_result.is_err():
                return Result.err(response_text_result.message)

            response_text = response_text_result.unwrap()
            self._logger.debug("Qwen 3.6 35B A3B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE
            )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            return Result.ok(code_commands)
        except Exception as e:
            self._logger.error(f"Qwen 3.6 35B A3B API call failed: {e}")
            return Result.err(f"Qwen 3.6 35B A3B API call failed: {e}")


@dataclasses.dataclass(frozen=True)
class GetCodeFixCommandsPrompt(IGetCodeFixCommandsPrompt):
    '''Implementation of IGetCodeFixCommandsPrompt using Qwen 3.6 35B A3B.'''
    _conf: Qwen3635bA3bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key,
            timeout=self._conf.timeout,
            default_headers=self._conf.headers
        ))

    def execute(self, context: GetCodeFixCommandsPromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling Qwen 3.6 35B A3B API for code fix prompt with {len(context.code_file_paths)} code files")

            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt = f.read()
                    if context.code_command_strategy == CodeCommandStrategies.ADD_DELETE:
                        code_txt = _set_line_markers(code_txt)

                    file_data.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": f"FILE: {file_path}\n```{file_path}\n{code_txt}\n```"}
                            ]
                        }
                    )

            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction + "\n"
            prompt_content = "Fix this current error:\n" + context.error_description + "\nThis is what must be implemented: \n" + context.strategic_change_description
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble + __PROVIDER_SPECIFIC_PROMPTING_INSTRUCTIONS__
            },
            {
                "role": "user",
                "content": prompt_content
            }] + file_data

            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text_result = _extract_response_text(response)
            if response_text_result.is_err():
                return Result.err(response_text_result.message)

            response_text = response_text_result.unwrap()
            self._logger.debug("Qwen 3.6 35B A3B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE
            )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            return Result.ok(code_commands)
        except Exception as e:
            self._logger.error(f"Qwen 3.6 35B A3B API call failed: {e}")
            return Result.err(f"Qwen 3.6 35B A3B API call failed: {e}")