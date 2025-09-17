import dataclasses
from enum import Enum
from fnmatch import fnmatch
import logging
from typing import List
from code_overseeing.configuration import CodeOverseerConfiguration
from core import Result, Unit
import os
import gitmatch

from prompting import GetCodeChangeCommandsPromptContext
from prompting.openai import IPromptManager

@dataclasses.dataclass(frozen=True)
class CodeOverseer:
    '''
    Manages and oversees code changes in a codebase.
    '''
    _code_overseer_configuration: CodeOverseerConfiguration
    _prompt_manager: IPromptManager
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger(__name__))

    def list_code_file_paths(self) -> Result[List[str]]:
        '''
        Lists all code file paths that are not ignored and are exclusively included in the configuration.
        Returns:
            Result[List[str]]: List of code file paths or error message
        '''
        def normalize_path(path):
            return path.replace("\\", "/")

        try:
            if not os.path.exists(self._code_overseer_configuration.code_directory_path):
                return Result.err(f"Codebase path does not exist: {self._code_overseer_configuration.code_directory_path}")
            self._logger.info("Listing code file paths")

            code_file_paths = []

            ignore_matcher = gitmatch.compile(self._code_overseer_configuration.ignore_patterns)
            include_matcher = gitmatch.compile(self._code_overseer_configuration.include_only_patterns) \
                                if self._code_overseer_configuration.include_only_patterns \
                                else None

            for root, dirs, files in os.walk(self._code_overseer_configuration.code_directory_path):
                # Filter out ignored directories
                dirs[:] = [
                    d for d in dirs
                    if not ignore_matcher.match(os.path.relpath(os.path.join(root, d), self._code_overseer_configuration.code_directory_path))
                ]

                for file in files:
                    file = file
                    rel_file_path = os.path.relpath(os.path.join(root, file), self._code_overseer_configuration.code_directory_path)

                    # Ignore files matching ignore_patterns or under node_modules/dist
                    if ignore_matcher.match(rel_file_path):
                        continue

                    # If include_only_patterns is set, only include files matching those patterns
                    if include_matcher and not include_matcher.match(rel_file_path):
                        continue
                    
                    rel_file_path = os.path.join(root, file)
                    rel_file_path = normalize_path(rel_file_path)
                    code_file_paths.append(rel_file_path)

            return Result.ok(code_file_paths)
        except Exception as e:
            return Result.err(str(e))

    def apply_code_change(self, change_strategic_description: str) -> Result[Unit]:
        '''
        Applies code changes based on a strategic description.
        Args:
            change_strategic_description (str): Strategic description of the code change
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        self._logger.info(f"Handling code change: {change_strategic_description}")

        res_codebase_file_paths = self.list_code_file_paths()
        if res_codebase_file_paths.is_err():
            return Result.err(f"Failed to list code file paths: {res_codebase_file_paths.unwrap_err()}")
        codebase_file_paths = res_codebase_file_paths.unwrap()
        
        
        res_code_change_commands = self._prompt_manager.execute_code_change_commands_prompt(
            GetCodeChangeCommandsPromptContext(
                strategic_description=change_strategic_description,
                code_file_paths=codebase_file_paths
            )
        )

        if res_code_change_commands.is_err():
            return Result.err(f"Failed to get code change commands: {res_code_change_commands.unwrap_err()}")
        code_change_commands = res_code_change_commands.unwrap()

        for command in code_change_commands:
            self._logger.info(f"Executing command: {command}")
            res_execution = command.execute(self._code_overseer_configuration.code_directory_path)
            if res_execution.is_err():
                self._logger.error(f"Failed to execute command {command}: {res_execution.unwrap_err()}")
                return Result.err(f"Failed to execute command {command}: {res_execution.unwrap_err()}")
            self._logger.info(f"Successfully executed command: {command}")
        return Result.ok(Unit())