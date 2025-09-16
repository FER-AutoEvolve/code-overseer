from abc import abstractmethod
from typing import List
from code_overseeing.code_commands import CodeCommand
from core import Result

class IGetCodeChangeCommandsPrompt:
    '''
    Interface for generating code change commands based on a given context.
    '''
    @abstractmethod
    def execute(self, context: dict) -> Result[List[CodeCommand]]:
        '''
        Executes the prompt with the given context.
        Args:
            context (dict): The context for the prompt.
        Returns:
            Result[List[CodeCommand]]: The result of the prompt execution.
        '''
        pass