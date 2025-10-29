from abc import abstractmethod
import dataclasses
from typing import List, Optional
from code_overseeing.code_commands import CodeCommand
from configuration import PromptingConfiguration
from core import Result
from prompting.prompts import GetCodeChangeCommandsPromptContext

@dataclasses.dataclass(frozen=True, init=False)
class BasePromptManager:
    '''
    Base class for managing prompts to OpenAI. Contains methods to execute raw prompts and specific code change command prompts.
    Encapsulates the prompting configuration - command strategy, codebase description, and specific provider information.
    '''
    _prompting_configuration: PromptingConfiguration
    
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
    def execute_code_change_commands_prompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        '''
        Executes a prompt to get the code change commands based on the provided context.
        Parameters:
            strategic_description (str): Description of the desired changes.
            code_file_paths (Optional[List[str]]): List of code file paths to consider.
        Returns:
            Result[List[CodeCommand]]: A list of code change commands or an error message.
        '''
        pass

    @abstractmethod
    def execute_code_change_reprompt(self, strategic_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        '''
        Executes a reprompt after code changes have been made, to determine if further changes are needed.
        Parameters:
            strategic_description (str): Description of the desired changes.
            code_file_paths (Optional[List[str]]): List of code file paths to consider. 
        Returns:
            Result[List[CodeCommand]]: A list of code change commands or an error message.
        '''
        pass
    
    @abstractmethod
    def execute_code_fix_prompt(self, strategic_description: str, error_description: str, code_file_paths: Optional[List[str]]) -> Result[List[CodeCommand]]:
        '''
        Executes a prompt for code changes to fix a code error.
        Parameters:
            strategic_description (str): Description of the desired changes.
            error_description: Description of the error to fix.
            code_file_paths (Optional[List[str]]): List of code file paths to consider. 
        Returns:
            Result[List[CodeCommand]]: A list of code change commands or an error message.
        '''
        pass
