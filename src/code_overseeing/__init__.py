import dataclasses
from enum import Enum
import logging
from typing import List
from code_overseeing.configuration import CodeOverseerConfiguration
from core import Result, Unit
import os

from prompting.openai import IPromptManager

@dataclasses.dataclass(frozen=True)
class CodeOverseer:
    _code_overseer_configuration: CodeOverseerConfiguration
    _prompt_manager: IPromptManager
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def list_code_file_paths(self) -> Result[List[str]]:
        '''Lists all code file paths'''
        try:
            if not os.path.exists(self._code_overseer_configuration.code_directory):
                return Result.err(f"Codebase path does not exist: {self._code_overseer_configuration.code_directory}")
            self._logger.info("Listing code file paths")

            code_file_paths = []

            for root, dirs, files in os.walk(self._code_overseer_configuration.code_directory):
                for filename in files:
                    code_file_paths.append(os.path.join(root, filename))

            return Result.ok(code_file_paths)
        except Exception as e:
            return Result.err(str(e))

    def apply_code_change(self, change_strategic_description: str) -> Result[Unit]:
        '''Handles a code change request'''
        self._logger.info(f"Handling code change: {change_strategic_description}")
        
        res_code_change_commands = self._prompt_manager.execute_code_change_commands_prompt({"description": change_strategic_description})
        
        if res_code_change_commands.is_err():
            return Result.err(f"Failed to get code change commands: {res_code_change_commands.unwrap_err()}")
        code_change_commands = res_code_change_commands.unwrap()

        for command in code_change_commands:
            self._logger.info(f"Executing command: {command}")
            res_execution = command.execute(self._code_overseer_configuration.code_directory)
            if res_execution.is_err():
                self._logger.error(f"Failed to execute command {command}: {res_execution.unwrap_err()}")
                return Result.err(f"Failed to execute command {command}: {res_execution.unwrap_err()}")
            self._logger.info(f"Successfully executed command: {command}")
        return Result.ok(Unit())