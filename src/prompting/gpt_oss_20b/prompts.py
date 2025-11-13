import dataclasses
import logging
from typing import List
from code_overseeing.code_commands import CodeCommand
from configuration import CodeCommandStrategies
from core import Result
import openai
from prompting.gpt_oss_20b.configuration import GptOss20bConfiguration
from prompting.prompts import GetCodeChangeCommandsPromptContext, GetCodeFixCommandsPromptContext, IGetCodeChangeCommandsPrompt, GetCodeChangeCommandsRepromptContext, IGetCodeChangeCommandsReprompt, IGetCodeFixCommandsPrompt


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPrompt(IGetCodeChangeCommandsPrompt):
    '''Implementation of IGetCodeChangeCommandsPrompt using GPT OSS 20B.'''
    _conf: GptOss20bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def __post_init__(self) -> None:
        object.__setattr__(self, '_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key, 
            timeout=self._conf.timeout
        ))

    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling GPT OSS 20B API for code change commands with {len(context.code_file_paths)} code files")

            # Prepare codebase files as text
            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt =  f.read()
                    # Add line markers if using ADD/DELETE strategy
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
            # The prompt preamble for the prompt instruction
            # Contains the codebase description and the operational instructions on how to provide the commands
            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction 
            #+ "Don't forget to include the angle brackets in the commands for the file path and the code. Don't use markdown code annotations."

            # The prompt input with the strategic description (user story) and the code files
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble
            },
            {
                "role": "user",
                "content": context.strategic_change_description
            }] + file_data

            # Create prompt
            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text = response.output_text

            self._logger.debug("GPT OSS 20B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE # Remove line markers if using ADD/DELETE strategy
            )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            
            return Result.ok(code_commands)

        except Exception as e:
            self._logger.error(f"GPT OSS 20B API call failed: {e}")
            return Result.err(f"GPT OSS 20B API call failed: {e}")
        

@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsReprompt(IGetCodeChangeCommandsReprompt):
    '''Implementation of IGetCodeChangeReprompt using GPT OSS 20B.'''
    _conf: GptOss20bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_gpt_oss_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key, 
            timeout=self._conf.timeout
        ))

    def execute(self, context: GetCodeChangeCommandsRepromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling GPT OSS 20B API for code change reprompt with {len(context.code_file_paths)} code files")

            # Prepare codebase files as text
            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt =  f.read()
                    # Add line markers if using ADD/DELETE strategy
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
            # The prompt preamble for the prompt instruction
            # Contains the codebase description and the operational instructions on how to provide the commands
            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction 
            #+ "Don't forget to include the angle brackets in the commands. Don't use markdown code annotations."

            # The prompt input with the strategic description (user story) and the code files
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble
            },
            {
                "role": "user",
                "content": context.strategic_change_description
            }] + file_data

            # Create prompt
            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text = response.output_text
            self._logger.debug("GPT OSS 20B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE # Remove line markers if using ADD/DELETE strategy
                )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            return Result.ok(code_commands)
        except Exception as e:
            self._logger.error(f"GPT OSS 20B API call failed: {e}")
            return Result.err(f"GPT OSS 20B API call failed: {e}")
        
@dataclasses.dataclass(frozen=True)
class GetCodeFixCommandsPrompt(IGetCodeFixCommandsPrompt):
    '''Implementation of IGetCodeFixCommandsPrompt using GPT OSS 20B API.'''
    _conf: GptOss20bConfiguration
    _client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_client', openai.OpenAI(
            base_url=self._conf.url,
            api_key=self._conf.api_key, 
            timeout=self._conf.timeout
        ))

    def execute(self, context: GetCodeFixCommandsPromptContext) -> Result[List[CodeCommand]]:
        try:
            self._logger.debug(f"Calling GPT OSS 20B API for code change reprompt with {len(context.code_file_paths)} code files")

            # Prepare codebase files as text
            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt =  f.read()
                    # Add line markers if using ADD/DELETE strategy
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
            # The prompt preamble for the prompt instruction
            # Contains the codebase description and the operational instructions on how to provide the commands
            prompt_preamble: str = context.codebase_description + "\n" + context.code_change_command_operational_instruction

            # Prompt content
            prompt_content = "Fix this current error:\n" + context.error_description \
                + "\nThis is what must be implemented: \n" + context.strategic_change_description
                

            # The prompt input with the strategic description (user story) and the code files
            prompt_input = [{
                "role": "system",
                "content": prompt_preamble
            },
            {
                "role": "user",
                "content": prompt_content
            }] + file_data

            # Create prompt
            response = self._client.responses.create(
                model=self._conf.model,
                max_output_tokens=self._conf.max_tokens,
                temperature=self._conf.temperature,
                top_p=self._conf.top_p,
                input=prompt_input
            )

            response_text = response.output_text
            self._logger.debug("GPT OSS 20B API call successful, parsing response")
            code_commands: List[CodeCommand] = _parse_response(
                response_text,
                remove_line_markers=context.code_command_strategy == CodeCommandStrategies.ADD_DELETE # Remove line markers if using ADD/DELETE strategy
                )
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            return Result.ok(code_commands)
        except Exception as e:
            self._logger.error(f"GPT OSS 20B API call failed: {e}")
            return Result.err(f"GPT OSS 20B API call failed: {e}")
        
@staticmethod
def _parse_response( response_text: str, remove_line_markers: bool = False) -> Result[List[CodeCommand]]:
    '''
    Parses the response text from GPT OSS 20B into a list of CodeCommand objects using the individual command parse methods.
    Args:
        response_text (str): The raw response text from GPT OSS 20B.
    '''
    if remove_line_markers:
        response_text = _remove_line_markers(response_text)
    from code_overseeing.code_commands import AddCodeCommand, DeleteCodeCommand, CommandTypes, CodeCommand, UpdateFileCommand, DoneCommand
    import re
    commands: List[CodeCommand] = []

    # Find all ADD commands
    add_pattern = re.compile(r"ADD\s*\[.*?\]\s*\[\d+\]\s*\[\[.*?\]\]", re.DOTALL)
    for add_match in add_pattern.finditer(response_text):
        cmd_str = add_match.group(0)
        res_cmd = AddCodeCommand.parse(cmd_str)
        if res_cmd.is_ok():
            commands.append(res_cmd.unwrap())
        else:
            return Result.err(f"Failed to parse ADD command: {res_cmd.message}")
        
    # Find all DELETE commands
    delete_pattern = re.compile(r"DELETE\s*\[.*?\]\s*\[\d+-\d+\]")
    for del_match in delete_pattern.finditer(response_text):
        cmd_str = del_match.group(0)
        res_cmd = DeleteCodeCommand.parse(cmd_str)
        if res_cmd.is_ok():
            commands.append(res_cmd.unwrap())
        else:
            return Result.err(f"Failed to parse DELETE command: {res_cmd.message}")

    # Find all UPDATE_FILE commands
    update_pattern = re.compile(r"UPDATE_FILE\s*\[.*?\]\s*\[\[.*?\]\]", re.DOTALL)
    for update_match in update_pattern.finditer(response_text):
        cmd_str = update_match.group(0)
        res_cmd = UpdateFileCommand.parse(cmd_str)
        if res_cmd.is_ok():
            commands.append(res_cmd.unwrap())
        else:
            return Result.err(f"Failed to parse UPDATE_FILE command: {res_cmd.message}")
    
    # Find all DONE commands
    done_pattern = re.compile(r"DONE")
    for done_match in done_pattern.finditer(response_text):
        cmd_str = done_match.group(0)
        res_cmd = DoneCommand.parse(cmd_str)
        if res_cmd.is_ok():
            commands.append(res_cmd.unwrap())
    return commands
    
@staticmethod
def _set_line_markers(code_txt: str) -> str:
    '''
    Sets line markers as comments in the code text for easier reference. //LN:digits+
    Args:
        code_txt (str): The original code text.
    Returns:
        str: The code text with line markers added.
    '''
    lines = code_txt.splitlines()
    marked_lines = [f"//LN:{i+1} {line}" for i, line in enumerate(lines)]
    return "\n".join(marked_lines)

@staticmethod
def _remove_line_markers(code_txt: str) -> str:
    '''
    Removes line markers from the code text.
    Args:
        code_txt (str): The code text with line markers.
    Returns:
        str: The code text without line markers.
    '''
    import re
    lines = code_txt.splitlines()
    cleaned_lines = [re.sub(r"//LN:\d+", "", line) if line.startswith("//LN:") else line for line in lines]
    return "\n".join(cleaned_lines)