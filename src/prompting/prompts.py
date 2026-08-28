__CODE_CHANGE_OPERATIONAL_INSTRUCTION_ADD_DELETE_STRATEGY_TEXT__ = """
Give me instructions how to implement the mentioned functionalities in the form of the following `ADD` and `DELETE` commands: 
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
Give me instructions how to implement the mentioned functionalities in the form of the following `UPDATE_FILE` command: 
UPDATE_FILE [file] [[code]] 
The UPDATE_FILE command consists of the `UPDATE_FILE` keyword, the parameter containing the file path, and the parameter containing the updated code of the entire file. 
The commands must have the [ ] chars encapsulating the parameters, including the [[ and ]] encapsulating the code through multiple lines.
The file parameter is the path to the codebase file given in the context file attachment. 
When adding a new file, just reference the file path and the file will be created.
"""

__CODE_CHANGE_OPERATIONAL_REPROMPT_INSTRUCTION_TEXT__ = """
If you think there are no more changes needed, respond with the `DONE` command in the following format:
DONE
"""

from abc import abstractmethod
import dataclasses
import logging
from typing import Any, Dict, List, Optional

from code_overseeing.code_commands import CodeCommand
from configuration import CodeCommandStrategies
from core import Result
import experiment_notification


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
        
@dataclasses.dataclass(frozen=True)
class GetCodeChangeCommandsRepromptContext:
    '''
    Context for generating additional code change commands or concluding with DONE.
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
        chosen_code_change_instruction = \
            (__CODE_CHANGE_OPERATIONAL_INSTRUCTION_ADD_DELETE_STRATEGY_TEXT__ if self.code_command_strategy == CodeCommandStrategies.ADD_DELETE else __CODE_CHANGE_OPERATIONAL_INSTRUCTION_UPDATE_FILE_STRATEGY_TEXT__) \
            + "\n" + __CODE_CHANGE_OPERATIONAL_REPROMPT_INSTRUCTION_TEXT__
        object.__setattr__(
            self, 
           'code_change_command_operational_instruction',
            chosen_code_change_instruction
           )
        
@dataclasses.dataclass(frozen=True)
class GetCodeFixCommandsPromptContext:
    '''
    Context for generating additional code fix commands.
    Attributes:
        strategic_description (str): Description of the desired changes.
        error_description (str): The reported code error to fix.
        code_file_paths (List[str]): List of code file paths to consider.
    '''
    strategic_change_description: str
    error_description: str
    codebase_description: str
    code_command_strategy: CodeCommandStrategies
    code_file_paths: List[str] = dataclasses.field(default_factory=list)
    code_change_command_operational_instruction: str = dataclasses.field(init=False)

    def __post_init__(self):
        chosen_code_change_instruction = \
            (__CODE_CHANGE_OPERATIONAL_INSTRUCTION_ADD_DELETE_STRATEGY_TEXT__ if self.code_command_strategy == CodeCommandStrategies.ADD_DELETE else __CODE_CHANGE_OPERATIONAL_INSTRUCTION_UPDATE_FILE_STRATEGY_TEXT__) \
            + "\n" + __CODE_CHANGE_OPERATIONAL_REPROMPT_INSTRUCTION_TEXT__
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

class IGetCodeChangeCommandsReprompt:
    '''
    Interface for generating additional code change commands or concluding with DONE based on a given context.
    '''
    @abstractmethod
    def execute(self, context: GetCodeChangeCommandsRepromptContext) -> Result[List[CodeCommand]]:
        '''
        Executes the reprompt with the given context.
        Args:
            context (GetCodeRepromptContext): The context for the reprompt.
        Returns:
            Result[List[CodeCommand]]: The result of the reprompt execution.
        '''
        pass

class IGetCodeFixCommandsPrompt:
    '''
    Interface for generating additional code change commands for fixing breaking builds.
    '''
    @abstractmethod
    def execute(self, context: GetCodeFixCommandsPromptContext) -> Result[List[CodeCommand]]:
        '''
        Executes the reprompt with the given context.
        Args:
            context (GetCodeFixPromptContext): The context for the reprompt.
        Returns:
            Result[List[CodeCommand]]: The result of the reprompt execution.
        '''
        pass


def log_token_usage(logger: logging.Logger, response: object, provider_name: str) -> None:
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.debug(f"{provider_name} token usage unavailable")
        return

    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    input_details = getattr(usage, "input_tokens_details", None)
    cached_tokens = getattr(input_details, "cached_tokens", None) if input_details is not None else None

    logger.info(
        f"{provider_name} token usage: input={input_tokens}, output={output_tokens}, total={total_tokens}, cached_input={cached_tokens}"
    )


def extract_token_usage(response: object) -> Optional[Dict[str, Any]]:
    '''
    Extracts a minimal token usage payload from provider responses.
    '''
    usage = getattr(response, "usage", None)
    if usage is None:
        return None

    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    input_details = getattr(usage, "input_tokens_details", None)
    cached_tokens = getattr(input_details, "cached_tokens", None) if input_details is not None else None

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_tokens": cached_tokens,
    }


def log_prompt_event(
    logger: logging.Logger,
    event_name: str,
    payload: Optional[Dict[str, Any]] = None,
    event_type: experiment_notification.ExperimentEventTypes = experiment_notification.ExperimentEventTypes.INFO,
) -> None:
    '''
    Emits a standardized experiment event for prompt lifecycle messages.
    '''
    logger.experiment(
        experiment_notification.format_experiment_event_message(event_name, payload),
        event_type=event_type,
    )


def log_prompt_response_event(
    logger: logging.Logger,
    event_name: str,
    response: object,
    response_text: str,
    event_type: experiment_notification.ExperimentEventTypes = experiment_notification.ExperimentEventTypes.INFO,
) -> None:
    '''
    Emits a prompt response event payload containing token usage and raw response text.
    '''
    payload = {
        "tokens": extract_token_usage(response),
        "response_text": response_text,
    }
    log_prompt_event(logger, event_name, payload=payload, event_type=event_type)