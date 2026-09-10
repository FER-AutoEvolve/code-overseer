import dataclasses
import logging
import re
from typing import List

import openai

from code_overseeing.code_commands import AddCodeCommand, CodeCommand, DeleteCodeCommand, DoneCommand, UpdateFileCommand
from configuration import CodeCommandStrategies
from core import Result
from prompting.openai.configuration import OpenAiConfiguration
from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeChangeCommandsRepromptContext, GetCodeFixCommandsPromptContext, IGetCodeChangeCommandsPrompt, IGetCodeChangeCommandsReprompt, IGetCodeFixCommandsPrompt, log_token_usage


def _create_file_data(code_file_paths: List[str], code_command_strategy: CodeCommandStrategies) -> List[dict]:
    file_data: List[dict] = []
    for file_path in code_file_paths:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            code_text = file.read()
            if code_command_strategy == CodeCommandStrategies.ADD_DELETE:
                code_text = _set_line_markers(code_text)
            file_data.append({
                "role": "user",
                "content": [{"type": "input_text", "text": f"FILE: {file_path}\n```{file_path}\n{code_text}\n```"}],
            })
    return file_data


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPrompt(IGetCodeChangeCommandsPrompt):
    _conf: OpenAiConfiguration
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())
    _client: openai.OpenAI = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_client", openai.OpenAI(api_key=self._conf.api_key, timeout=self._conf.timeout))

    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        return self._execute(context, context.strategic_change_description)

    def _execute(self, context: GetCodeChangeCommandsPromptContext | GetCodeChangeCommandsRepromptContext | GetCodeFixCommandsPromptContext, prompt_content: str) -> Result[List[CodeCommand]]:
        try:
            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                instructions=context.codebase_description + "\n" + context.code_change_command_operational_instruction,
                input=[{"role": "user", "content": prompt_content}] + _create_file_data(context.code_file_paths, context.code_command_strategy),
            )
            log_token_usage(self._logger, response, "OpenAI")
            return _parse_response(response.output_text, context.code_command_strategy == CodeCommandStrategies.ADD_DELETE)
        except Exception as error:
            self._logger.error(f"OpenAI API call failed: {error}")
            return Result.err(f"OpenAI API call failed: {error}")


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsReprompt(IGetCodeChangeCommandsReprompt):
    _conf: OpenAiConfiguration
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())
    _delegate: GetCodeChangeCommandsPrompt = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_delegate", GetCodeChangeCommandsPrompt(self._conf, self._logger))

    def execute(self, context: GetCodeChangeCommandsRepromptContext) -> Result[List[CodeCommand]]:
        return self._delegate._execute(context, context.strategic_change_description)


@dataclasses.dataclass(frozen=True)
class GetCodeFixCommandsPrompt(IGetCodeFixCommandsPrompt):
    _conf: OpenAiConfiguration
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())
    _delegate: GetCodeChangeCommandsPrompt = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_delegate", GetCodeChangeCommandsPrompt(self._conf, self._logger))

    def execute(self, context: GetCodeFixCommandsPromptContext) -> Result[List[CodeCommand]]:
        prompt_content = f"Fix this current error:\n{context.error_description}\nThis is what must be implemented: \n{context.strategic_change_description}"
        return self._delegate._execute(context, prompt_content)


def _parse_response(response_text: str, remove_line_markers: bool = False) -> Result[List[CodeCommand]]:
    if remove_line_markers:
        response_text = _remove_line_markers(response_text)

    commands: List[CodeCommand] = []
    patterns = [
        (re.compile(r"ADD\s*\[.*?\]\s*\[\d+\]\s*\[\[.*?\]\]", re.DOTALL), AddCodeCommand, "ADD"),
        (re.compile(r"DELETE\s*\[.*?\]\s*\[\d+-\d+\]"), DeleteCodeCommand, "DELETE"),
        (re.compile(r"UPDATE_FILE\s*\[.*?\]\s*\[\[.*?\]\]", re.DOTALL), UpdateFileCommand, "UPDATE_FILE"),
    ]
    for pattern, command_type, command_name in patterns:
        for match in pattern.finditer(response_text):
            command = command_type.parse(match.group(0))
            if command.is_ok():
                commands.append(command.unwrap())
            else:
                return Result.err(f"Failed to parse {command_name} command: {command.message}")

    for match in re.compile(r"DONE").finditer(response_text):
        command = DoneCommand.parse(match.group(0))
        if command.is_ok():
            commands.append(command.unwrap())
    return Result.ok(commands)


def _set_line_markers(code_text: str) -> str:
    return "\n".join(f"//LN:{index + 1} {line}" for index, line in enumerate(code_text.splitlines()))


def _remove_line_markers(code_text: str) -> str:
    return "\n".join(re.sub(r"//LN:\d+", "", line) if line.startswith("//LN:") else line for line in code_text.splitlines())