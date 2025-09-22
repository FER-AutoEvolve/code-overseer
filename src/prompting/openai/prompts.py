import dataclasses
import logging
from typing import List
from code_overseeing.code_commands import CodeCommand
from core import Result
import openai
from configuration import OpenAiConfiguration
from prompting.prompts import GetCodeChangeCommandsPromptContext, IGetCodeChangeCommandsPrompt


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPrompt(IGetCodeChangeCommandsPrompt):
    '''Implementation of IGetCodeChangeCommandsPrompt using OpenAI API.'''
    _openai_settings: OpenAiConfiguration
    _openai_client: openai.OpenAI = dataclasses.field(init=False)
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def __post_init__(self) -> None:
        object.__setattr__(self, '_openai_client', openai.OpenAI(
            api_key=self._openai_settings.api_key, 
            timeout=self._openai_settings.timeout
        ))

    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        
        try:
            self._logger.debug(f"Calling OpenAI API for code change commands with {len(context.code_file_paths)} code files")

            # Upload files to OpenAI
            file_data: List[dict] = []
            for file_path in context.code_file_paths:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code_txt =  f.read()
                    code_txt = self._set_line_markers(code_txt)
                    file_data.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": f"FILE: {file_path}\n```{file_path}\n{code_txt}\n```"}
                            ]
                        }
                    )
            prompt_strategic_description = {
                        "role": "user",
                        "content": context.strategic_description
                    }

            prompt_input = [prompt_strategic_description] + file_data

            # Create prompt
            response = self._openai_client.responses.create(
                model=self._openai_settings.model,
                max_output_tokens=self._openai_settings.max_tokens,
                temperature=self._openai_settings.temperature,
                top_p=self._openai_settings.top_p,
                instructions=context.operational_instructions,
                input=prompt_input
            )

            response_text = response.output_text

            self._logger.debug("OpenAI API call successful, parsing response")
            code_commands: List[CodeCommand] = self._parse_response(response_text)
            self._logger.debug(f"Parsed {len(code_commands)} code commands")
            
            return Result.ok(code_commands)

        except Exception as e:
            self._logger.error(f"OpenAI API call failed: {e}")
            return Result.err(f"OpenAI API call failed: {e}")
        
    def _parse_response(self, response_text: str) -> List[CodeCommand]:
        '''
        Parses the response text from OpenAI into a list of CodeCommand objects using the individual command parse methods.
        Args:
            response_text (str): The raw response text from OpenAI.
        '''
        response_text = self._remove_line_markers(response_text)
        from code_overseeing.code_commands import AddCodeCommand, DeleteCodeCommand, CommandTypes, CodeCommand
        import re
        commands: List[CodeCommand] = []

        # Find all ADD commands
        add_pattern = re.compile(r"ADD\s*\[.*?\]\s*\[\d+\]\s*\[\[.*?\]\]", re.DOTALL)
        for add_match in add_pattern.finditer(response_text):
            cmd_str = add_match.group(0)
            res = AddCodeCommand.parse(cmd_str)
            if isinstance(res, AddCodeCommand):
                commands.append(res)
            elif hasattr(res, 'is_ok') and res.is_ok():
                commands.append(res.unwrap())

        # Find all DELETE commands
        delete_pattern = re.compile(r"DELETE\s*\[.*?\]\s*\[\d+-\d+\]")
        for del_match in delete_pattern.finditer(response_text):
            cmd_str = del_match.group(0)
            try:
                cmd = DeleteCodeCommand.parse(cmd_str)
                commands.append(cmd)
            except Exception:
                pass

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
