import dataclasses
from enum import Enum
import shutil
import logging
from typing import List
from code_overseeing.configuration import CodeOverseerConfiguration
from core import Result, Unit
import os
import gitmatch
import keypoint_notification
from prompting.openai import BasePromptManager
from prompting.prompts import GetCodeChangeCommandsPromptContext
from code_overseeing.code_commands import CodeCommand, CommandTypes

@dataclasses.dataclass(frozen=True)
class CodeOverseer:
    '''
    Manages and oversees code changes in a codebase.
    '''
    _code_overseer_configuration: CodeOverseerConfiguration
    _prompt_manager: BasePromptManager
    _logger: logging.Logger = dataclasses.field(default=logging.getLogger())

    def list_codebase_file_paths(self) -> Result[List[str]]:
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
        
    def list_staging_file_paths(self) -> Result[List[str]]:
        '''
        Lists all code file paths in the staging directory that are not ignored and are exclusively included in the configuration.
        Returns:
            Result[List[str]]: List of code file paths or error message
        '''
        def normalize_path(path):
            return path.replace("\\", "/")

        try:
            if not os.path.exists(self._code_overseer_configuration.code_staging_directory_path):
                return Result.err(f"Staging path does not exist: {self._code_overseer_configuration.code_staging_directory_path}")
            self._logger.info("Listing staging file paths")

            code_file_paths = []

            ignore_matcher = gitmatch.compile(self._code_overseer_configuration.ignore_patterns)
            include_matcher = gitmatch.compile(self._code_overseer_configuration.include_only_patterns) if self._code_overseer_configuration.include_only_patterns else None
            for root, dirs, files in os.walk(self._code_overseer_configuration.code_staging_directory_path):
                # Filter out ignored directories
                dirs[:] = [
                    d for d in dirs
                    if not ignore_matcher.match(os.path.relpath(os.path.join(root, d), self._code_overseer_configuration.code_staging_directory_path))
                ]

                for file in files:
                    file = file
                    rel_file_path = os.path.relpath(os.path.join(root, file), self._code_overseer_configuration.code_staging_directory_path)

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
        self._logger.keypoint(f"Received code change task: {change_strategic_description}", event_type=keypoint_notification.EventTypes.INFO)

        self._logger.keypoint(f"Preparing staging area for code changes...", event_type=keypoint_notification.EventTypes.INFO)
        # Copy current codebase to staging
        res_copy = self._copy_codebase_to_staging()
        if res_copy.is_err():
            return Result.err(f"Failed to copy codebase to staging: {res_copy.message}")
        self._logger.info("Successfully copied codebase to staging")

        # List code file paths in staging
        res_codebase_file_paths = self.list_staging_file_paths()
        if res_codebase_file_paths.is_err():
            return Result.err(f"Failed to list code file paths: {res_codebase_file_paths.message}")
        codebase_file_paths = res_codebase_file_paths.unwrap()

        self._logger.keypoint(f"Code is now in staging area. Starting initial prompt to get code change commands!", event_type=keypoint_notification.EventTypes.INFO)
        
        # Get code change commands from the prompt manager
        res_code_change_commands = self._prompt_manager.execute_code_change_commands_prompt(
            strategic_description=change_strategic_description,
            code_file_paths=codebase_file_paths
        )

        if res_code_change_commands.is_err():
            self._logger.error(f"Failed to get code change commands from prompt manager: {res_code_change_commands.message}")
            self._logger.keypoint(f"Failed to get code change commands from prompt!", event_type=keypoint_notification.EventTypes.FAILURE)
            return Result.err(f"Failed to get code change commands from prompt manager: {res_code_change_commands.message}")
        code_change_commands = res_code_change_commands.unwrap()
        self._logger.info(f"Received {len(code_change_commands)} code change commands from prompt manager")
        self._logger.keypoint(f"Received {len(code_change_commands)} code change commands from prompt response! Executing commands...", event_type=keypoint_notification.EventTypes.SUCCESS)

        # Execute each code change command from the primary prompt in the staging directory
        for command in code_change_commands:
            self._logger.info(f"Executing command: {command}")
            res_execution = command.execute(self._code_overseer_configuration.code_staging_directory_path)
            if res_execution.is_err():
                self._logger.error(f"Failed to execute command {command}: {res_execution.message}")
                return Result.err(f"Failed to execute command {command}: {res_execution.message}")
            self._logger.info(f"Successfully executed command: {command}")

        self._logger.keypoint(f"Successfully executed all {len(code_change_commands)} code change commands!", event_type=keypoint_notification.EventTypes.SUCCESS)

        # Execute reprompt if configured until DONE is received and execute in staging directory
        if self._code_overseer_configuration.reprompt_on_change:
            self._logger.info("Starting reprompting for additional code changes")
            self._logger.keypoint(f"Starting reprompting for additional code changes", event_type=keypoint_notification.EventTypes.INFO)
            done_received: bool = False
            reprompt_attempts: int = 0
            while not done_received:
                res_codebase_file_paths = self.list_staging_file_paths()
                if res_codebase_file_paths.is_err():
                    return Result.err(f"Failed to list code file paths: {res_codebase_file_paths.message}")
                codebase_file_paths = res_codebase_file_paths.unwrap()

                self._logger.info(f"Executing code change reprompt {reprompt_attempts + 1}")
                self._logger.keypoint(f"Executing code change reprompt no. {reprompt_attempts + 1}", event_type=keypoint_notification.EventTypes.INFO)
                res_reprompt = self._prompt_manager.execute_code_change_reprompt(
                    strategic_description=change_strategic_description,
                    code_file_paths=codebase_file_paths
                )

                if res_reprompt.is_err():
                    self._logger.error(f"Failed to get code change reprompt from prompt manager: {res_reprompt.message}")
                    self._logger.keypoint(f"Failed to get code change reprompt from prompt!", event_type=keypoint_notification.EventTypes.FAILURE)
                    return Result.err(f"Failed to get code change reprompt from prompt manager: {res_reprompt.message}")
                reprompt_commands = res_reprompt.unwrap()
                self._logger.info(f"Received {len(reprompt_commands)} reprompt commands from prompt manager")
                self._logger.keypoint(f"Received {len(reprompt_commands)} commands from prompt response! Executing commands...", event_type=keypoint_notification.EventTypes.INFO)
                
                for command in reprompt_commands:
                    self._logger.info(f"Executing reprompt command: {command}")
                    if command.command_type == CommandTypes.DONE:
                        self._logger.info("Received DONE command, finishing reprompting")
                        done_received = True
                        break

                    res_execution = command.execute(self._code_overseer_configuration.code_staging_directory_path)
                    if res_execution.is_err():
                        self._logger.error(f"Failed to execute reprompt command {command}: {res_execution.message}")
                        return Result.err(f"Failed to execute reprompt command {command}: {res_execution.message}")
                    self._logger.info(f"Successfully executed reprompt command: {command}")
                
                self._logger.info(f"Finished executing reprompt {reprompt_attempts + 1} commands")
                self._logger.keypoint(f"Successfully executed all {len(reprompt_commands)} reprompt commands!", event_type=keypoint_notification.EventTypes.SUCCESS)
                reprompt_attempts += 1

            self._logger.info(f"Finished reprompting after {reprompt_attempts} attempts")
            self._logger.keypoint(f"Finished reprompting after {reprompt_attempts} attempts", event_type=keypoint_notification.EventTypes.SUCCESS)
        
        self._logger.keypoint(f"Code changes applied successfully in staging area. Copying changes back to codebase...", event_type=keypoint_notification.EventTypes.INFO)
        # Copy staging back to codebase
        res_copy_back = self._copy_staging_to_codebase()
        if res_copy_back.is_err():
            return Result.err(f"Failed to copy staging back to codebase: {res_copy_back.message}")
        self._logger.info("Successfully copied staging back to codebase")
        
        # Remove staging directory
        res_remove_staging = self._remove_staging_directory()
        if res_remove_staging.is_err():
            return Result.err(f"Failed to remove staging directory: {res_remove_staging.message}")
        self._logger.info("Successfully removed staging directory")

        self._logger.keypoint(f"Code changes successfully applied to codebase! Your changes should be live soon!", event_type=keypoint_notification.EventTypes.SUCCESS)

        return Result.ok(Unit())

    def _copy_codebase_to_staging(self) -> Result[Unit]:
        '''
        Copies the current codebase to the staging directory.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            if os.path.exists(self._code_overseer_configuration.code_staging_directory_path):
                self._logger.info(f"Removing existing staging directory: {self._code_overseer_configuration.code_staging_directory_path}")

                shutil.rmtree(self._code_overseer_configuration.code_staging_directory_path)

            self._logger.info(f"Copying codebase from {self._code_overseer_configuration.code_directory_path} to staging directory {self._code_overseer_configuration.code_staging_directory_path}")
            # Create staging directory by copying codebase without the ignored files
            shutil.copytree(
                self._code_overseer_configuration.code_directory_path,
                self._code_overseer_configuration.code_staging_directory_path,
                ignore=CodeOverseer._create_file_filter(self._code_overseer_configuration.ignore_patterns),
            )
            # remove files that are not in include_only_patterns if set
            if self._code_overseer_configuration.include_only_patterns:
                for root, dirs, files in os.walk(self._code_overseer_configuration.code_staging_directory_path):
                    for file in files:
                        file_path = os.path.relpath(os.path.join(root, file), self._code_overseer_configuration.code_staging_directory_path)
                        include_matcher = gitmatch.compile(self._code_overseer_configuration.include_only_patterns)
                        if not include_matcher.match(file_path):
                            os.remove(os.path.join(root, file))

            return Result.ok(Unit())
        except Exception as e:
            return Result.err(f"Failed to copy codebase to staging: {e}")


    def _copy_staging_to_codebase(self) -> Result[Unit]:
        '''
        Copies the staging directory back to the codebase directory.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            self._logger.info(f"Copying staging directory from {self._code_overseer_configuration.code_staging_directory_path} to codebase directory {self._code_overseer_configuration.code_directory_path}")

            # Remove files in the staging directory that are not exclusively included
            if self._code_overseer_configuration.include_only_patterns:
                for root, dirs, files in os.walk(self._code_overseer_configuration.code_staging_directory_path):
                    for file in files:
                        file_path = os.path.relpath(os.path.join(root, file), self._code_overseer_configuration.code_staging_directory_path)
                        include_matcher = gitmatch.compile(self._code_overseer_configuration.include_only_patterns)
                        if not include_matcher.match(file_path):
                            os.remove(os.path.join(root, file))

            # Copy staging back to codebase, overwriting existing files that are not ignored
            shutil.copytree(
                self._code_overseer_configuration.code_staging_directory_path,
                self._code_overseer_configuration.code_directory_path,
                ignore=CodeOverseer._create_file_filter(self._code_overseer_configuration.ignore_patterns),
                dirs_exist_ok=True
            )
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(f"Failed to copy staging to codebase: {e}")

    def _remove_staging_directory(self) -> Result[Unit]:
        '''
        Removes the staging directory.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            if os.path.exists(self._code_overseer_configuration.code_staging_directory_path):
                self._logger.info(f"Removing staging directory: {self._code_overseer_configuration.code_staging_directory_path}")
                shutil.rmtree(self._code_overseer_configuration.code_staging_directory_path)
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(f"Failed to remove staging directory: {e}")
        
    
    @staticmethod
    def _create_file_filter(ignore_patterns: list[str]):
        return lambda dir, files: CodeOverseer._filter_files(dir, files, ignore_patterns)

    @staticmethod    
    def _filter_files(dir: str, files: list[str], ignore_patterns: list[str]) -> list[str]:
        import gitmatch
        ignore_matcher = gitmatch.compile(ignore_patterns)

        ignored = []
        for file in files:
            rel_path = os.path.relpath(os.path.join(dir, file))
            # Ignore if matches ignore_patterns
            if ignore_matcher.match(rel_path):
                ignored.append(file)
        return ignored