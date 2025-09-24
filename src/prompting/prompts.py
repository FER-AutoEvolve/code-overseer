__CODE_CHANGE_OPERATIONAL_INSTRUCTION_ADD_DELETE_STRATEGY_TEXT__ = """
Give me instructions how to implement the mentioned functionalities in the form of the following commands: 
ADD [file] [at line number] [[code]] 
DELETE [file] [from number-to number]  
Provide just those commands and nothing else. 
The commands must have the [ ] chars encapsulating the parameters, including the [[ and ]] encapsulating the code through multiple lines.
The file parameter is the path to the codebase file given in the context file attachment. 
When adding a new file, use line number 0 in the ADD commands. To modify a file, use the ADD and DELETE commands. 
Take into account that the line numbers change as you add or delete lines. Always use the line numbers of the original file as given in the context file attachments.
Determine lines to add or delete code according to the line number markers in the code files placed as comments that look like //LN:<digits> at the beginning of each line.
Don't generate the line markers in the code changes.
"""

__CODE_CHANGE_OPERATIONAL_INSTRUCTION_UPDATE_FILE_STRATEGY_TEXT__ = """
Give me instructions how to implement the mentioned functionalities in the form of the following command: 
UPDATE_FILE [file] [[code]] 
The UPDATE_FILE command's parameters are the full file path and the updated code of the entire file. Provide just those commands and nothing else. 
The commands must have the [ ] chars encapsulating the parameters, including the [[ and ]] encapsulating the code through multiple lines.
The file parameter is the path to the codebase file given in the context file attachment. 
When adding a new file, just reference the file path and the file will be created.
"""

from abc import abstractmethod
import dataclasses
from typing import List, Optional

from code_overseeing.code_commands import CodeCommand
from configuration import CodeCommandStrategies
from core import Result


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPromptContext:
    '''
    Context for generating code change commands.
    Attributes:
        strategic_description (str): Description of the desired changes.
        code_file_paths (List[str]): List of code file paths to consider.
    '''
    strategic_change_description: str
    codebase_description: str
    code_command_strategy: CodeCommandStrategies
    code_file_paths: List[str] = dataclasses.field(default_factory=list)
    code_change_command_operational_instruction: str = dataclasses.field(init=False)

    def __post_init__(self):
        chosen_code_change_instruction = __CODE_CHANGE_OPERATIONAL_INSTRUCTION_ADD_DELETE_STRATEGY_TEXT__ if self.code_command_strategy == CodeCommandStrategies.ADD_DELETE else __CODE_CHANGE_OPERATIONAL_INSTRUCTION_UPDATE_FILE_STRATEGY_TEXT__
        object.__setattr__(
            self, 
           'code_change_command_operational_instruction',
            chosen_code_change_instruction
           )

class IGetCodeChangeCommandsPrompt:
    '''
    Interface for generating code change commands based on a given context.
    '''
    @abstractmethod
    def execute(self, context: GetCodeChangeCommandsPromptContext) -> Result[List[CodeCommand]]:
        '''
        Executes the prompt with the given context.
        Args:
            context (GetCodeChangeCommandsPromptContext): The context for the prompt.
        Returns:
            Result[List[CodeCommand]]: The result of the prompt execution.
        '''
        pass