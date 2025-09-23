from abc import abstractmethod
from ast import List
import dataclasses
from enum import Enum
import os
from core import Result, Unit

class CommandTypes(Enum):
    '''
    Types of code commands
    '''
    ADD = "add"
    DELETE = "delete"
    UPDATE_FILE = "update_file"

@dataclasses.dataclass
class CodeCommand:
    '''
    Base class for code commands.
    '''
    file_path: str
    command_type: CommandTypes

    @abstractmethod
    def execute(self) -> Result[Unit]:
        pass

    def __str__(self):
        return f"{self.command_type.value.upper()} ON FILE {self.file_path}"

@dataclasses.dataclass
class DeleteCodeCommand(CodeCommand):
    '''
    Command to delete a range of lines from a code file.
    '''
    from_line_number: int
    to_line_number: int
    command_type: CommandTypes = dataclasses.field(init=False, default=CommandTypes.DELETE)

    def execute(self) -> Result[Unit]:
        try:
            lines: List[str] = []
            # check if file exists, and readlines
            # if not, leave as empty lines
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as file:
                    lines = file.readlines()

            if self.from_line_number < 1 or self.to_line_number > len(lines) or self.from_line_number > self.to_line_number:
                return Result.err("Invalid line numbers")

            del lines[self.from_line_number - 1:self.to_line_number]

            with open(self.file_path, 'w') as file:
                file.writelines(lines)

            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))
        
    def __str__(self):
        return super().__str__() + f" ON LINES {self.from_line_number}-{self.to_line_number}"

    @staticmethod
    def parse(command_str: str) -> Result['DeleteCodeCommand']:
        '''
        Parses a delete command string in the format:
        DELETE [file] [from-to]
        Args:
            command_str (str): Command string
        Returns:
            Result[DeleteCodeCommand]: Parsed command object or error message
        '''
        import re
        pattern = re.compile(r"DELETE\s*\[(.*?)\]\s*\[(\d+)-(\d+)\]")
        match = pattern.match(command_str.strip())
        if not match:
            return Result.err("Invalid delete command format")
        file_path = match.group(1).strip()
        from_line = int(match.group(2).strip())
        to_line = int(match.group(3).strip())
        return Result.ok(DeleteCodeCommand(file_path, from_line, to_line))



@dataclasses.dataclass
class AddCodeCommand(CodeCommand):
    '''
    Command to add a code snippet to a code file.
    '''
    code_snippet: str
    line_number: int = None  # If None, append to the end of the file
    command_type: CommandTypes = dataclasses.field(init=False, default=CommandTypes.ADD)

    def execute(self) -> Result[Unit]:
        '''
        Executes the add code command.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            lines: List[str] = []
            # check if file exists, and readlines
            # if not, use as empty lines
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as file:
                    lines = file.readlines()

            if self.line_number is None:
                lines.append(self.code_snippet + '\n')
            else:
                if self.line_number < 0 or self.line_number > len(lines) + 1:
                    return Result.err("Invalid line number")
                lines.insert(self.line_number - 1, self.code_snippet + '\n')

            with open(self.file_path, 'w') as file:
                file.writelines(lines)

            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))
        
    def __str__(self):
        return super().__str__() + f" AT LINE {self.line_number}"
        
    @staticmethod
    def parse(command_str: str) -> Result['AddCodeCommand']:
        '''
        Parses an add command string in the format:
        ADD [file] [line_number] [[code]]
        Args:
            command_str (str): Command string
        Returns:
            Result[AddCodeCommand]: Parsed command object or error message
        '''
        import re
        pattern = re.compile(r"ADD\s*\[(.*?)\]\s*\[(\d+)\]\s*\[\[(.*?)\]\]", re.DOTALL)
        match = pattern.match(command_str.strip())
        if not match:
            return Result.err("Invalid add command format")
        file_path = match.group(1).strip()
        line_number = int(match.group(2).strip())
        code_snippet = match.group(3)
        return AddCodeCommand(file_path, code_snippet, line_number)

@dataclasses.dataclass
class UpdateFileCommand(CodeCommand):
    '''
    Command to update an entire code file with new content.
    '''
    new_content: str
    command_type: CommandTypes = dataclasses.field(init=False, default=CommandTypes.UPDATE_FILE)

    def execute(self) -> Result[Unit]:
        '''
        Executes the update file command.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            with open(self.file_path, 'w') as file:
                file.write(self.new_content)
            return Result.ok(Unit())
        except Exception as e:
            return Result.err(str(e))
        
    def __str__(self):
        return super().__str__() + " WITH NEW CONTENT"
        
    @staticmethod
    def parse(command_str: str) -> Result['UpdateFileCommand']:
        '''
        Parses an update file command string in the format:
        UPDATE_FILE [file] [[new_content]]
        Args:
            command_str (str): Command string
        Returns:
            Result[UpdateFileCommand]: Parsed command object or error message
        '''
        import re
        pattern = re.compile(r"UPDATE_FILE\s*\[(.*?)\]\s*\[\[(.*?)\]\]", re.DOTALL)
        match = pattern.match(command_str.strip())
        if not match:
            return Result.err("Invalid update file command format")
        file_path = match.group(1).strip()
        new_content = match.group(2)
        return UpdateFileCommand(file_path, new_content)

@dataclasses.dataclass(init=False)
class CommandParser:
    '''
    Helper class to parse command strings into specific CodeCommand objects.
    '''
    @staticmethod
    def parse(command_str: str) -> Result[CodeCommand]:
        '''
        Parses a command string into a specific CodeCommand object.
        Args:
            command_str (str): Command string
        Returns:
            Result[CodeCommand]: Parsed command object or error message
        '''
        try:
            parts = command_str.strip().split(' ', 2)
            if not parts:
                return Result.err("Empty command")

            command_type = parts[0].lower()
            if command_type == CommandTypes.DELETE.value:
                res_command = DeleteCodeCommand.parse(command_str)
                return res_command
            elif command_type == CommandTypes.ADD.value:
                res_command = AddCodeCommand.parse(command_str)
                return res_command
            elif command_type == CommandTypes.UPDATE_FILE.value:
                res_command = UpdateFileCommand.parse(command_str)
                return res_command
            else:
                return Result.err(f"Unknown command type: {command_type}")
        except Exception as e:
            return Result.err(str(e))