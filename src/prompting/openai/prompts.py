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
        object.__setattr__(self, '_openai_client', openai.OpenAI(api_key=self._openai_settings.api_key))

    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        
        try:
            self._logger.debug(f"Calling OpenAI API for code change commands with {len(context.code_file_paths)} code files")

            fileObjects = [self._openai_client.files.create(
                file=open(file_path, "rb"),
                purpose="fine-tune"
            ) for file_path in context.code_file_paths]


            completion = self._openai_client.chat.completions.create(
                model=self._openai_settings.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"{context.operational_instructions}"
                    },
                    {
                        "role": "user",
                        "content": f"{context.strategic_description}"
                    },
                    { # Attach the files to the chat completion request to use files in the prompt
                        "role": "user",
                        "content": [
                            {"type": "file", "file": {"file_id": file_obj.id}} for file_obj in fileObjects
                        ]
                    }
                ]
            )

            response_text = completion.choices[0].message.content

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
        '''
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




        

    