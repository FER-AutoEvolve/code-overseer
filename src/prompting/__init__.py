from abc import abstractmethod
from typing import List, Optional
from code_overseeing.code_commands import CodeCommand
from core import Result


class IPromptManager:
    '''
    Interface for managing prompts to OpenAI.
    '''
    @abstractmethod
    def execute_raw_prompt(self, prompt_text: str) -> Result[str]:
        '''
        Executes a raw prompt against the OpenAI API.
        
        Parameters:
            prompt_text (str): The prompt text to send to the API.
        Returns:
            Result[str]: The response from the API or an error message.
        '''
        pass

    @abstractmethod
    def execute_code_change_commands_prompt(self, context: dict) -> Result[List[CodeCommand]]:
        '''
        Executes a prompt to get code change commands based on the provided context.
        Parameters:
            context (dict): The context for generating code change commands.
        Returns:
            Result[List[CodeCommand]]: A list of code change commands or an error message.
        '''
        pass
