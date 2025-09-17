
__CODE_CHANGE_OPERATIONAL_INSTURCTION_TEXT__ = """
Give me instructions how to implement the mentioned functionalities in the form of the following commands: 
ADD [file] [at line number] [[code]] 
DELETE [file] [from number-to number]  
Provide just those commands and nothing else. 
The commands must have the [ ] chars encapsulating the parameters, including the [[ and ]] encapsulating the code through multiple lines.
The file parameter is the path to the file relative to the root of the codebase given in the context file attachment. 
When adding a new file, use line number 0 in the ADD commands. To modify a file, use the ADD and DELETE commands. 
When modifying a file, take into account that the line numbers change as you add or delete lines.
"""

from abc import abstractmethod
import dataclasses
from typing import List, Optional

from code_overseeing.code_commands import CodeCommand
from core import Result


@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsPromptContext:
    '''
    Context for generating code change commands.
    Attributes:
        strategic_description (str): Description of the desired changes.
        code_file_paths (Optional[List[str]]): List of code file paths to consider.
        operational_instructions (Optional[str]): Any operational instructions to provide.
    '''
    strategic_description: str
    code_file_paths: Optional[List[str]] = None
    operational_instructions: str = dataclasses.field(default=__CODE_CHANGE_OPERATIONAL_INSTURCTION_TEXT__)

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