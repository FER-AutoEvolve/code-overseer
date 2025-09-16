from abc import abstractmethod
import dataclasses
from enum import Enum
from core import Result, Unit

class CommandTypes(Enum):
    '''
    Types of code commands
    '''
    ADD = "add"
    DELETE = "delete"

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

    def execute(self) -> Result[Unit]:
        try:
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
    def parse(command_str: str) -> 'DeleteCodeCommand':
        '''
        Parses a delete command string into a DeleteCodeCommand object.
        Args:
            command_str (str): Command string in the format "delete <file_path> <from_line> <to_line>"
        Returns:
            DeleteCodeCommand: Parsed command object
        '''
        parts = command_str.strip().split(' ')
        if len(parts) != 4 or parts[0].lower() != CommandTypes.DELETE.value:
            raise ValueError("Invalid delete command format")
        file_path = parts[1]
        from_line = int(parts[2])
        to_line = int(parts[3])
        return DeleteCodeCommand(file_path, from_line, to_line, CommandTypes.DELETE)



@dataclasses.dataclass
class AddCodeCommand(CodeCommand):
    '''
    Command to add a code snippet to a code file.
    '''
    code_snippet: str
    line_number: int = None  # If None, append to the end of the file

    def execute(self) -> Result[Unit]:
        '''
        Executes the add code command.
        Returns:
            Result[Unit]: Result indicating success or failure
        '''
        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()

            if self.line_number is None:
                lines.append(self.code_snippet + '\n')
            else:
                if self.line_number < 1 or self.line_number > len(lines) + 1:
                    return Result.failure("Invalid line number")
                lines.insert(self.line_number - 1, self.code_snippet + '\n')

            with open(self.file_path, 'w') as file:
                file.writelines(lines)

            return Result.success(Unit())
        except Exception as e:
            return Result.failure(str(e))
        
    def __str__(self):
        return super().__str__() + f" AT LINE {self.line_number}"
        
    @staticmethod
    def parse(command_str: str) -> Result['AddCodeCommand']:
        '''
        Parses an add command string into an AddCodeCommand object.
        Args:
            command_str (str): Command string in the format "add <file_path> <code_snippet> [<line_number>]"
        Returns:
            Result[AddCodeCommand]: Parsed command object or error message
        '''
        parts = command_str.strip().split(' ', 2)
        if len(parts) < 3 or parts[0].lower() != CommandTypes.ADD.value:
            return Result.failure("Invalid add command format")
        file_path = parts[1]
        code_snippet = parts[2]
        line_number = None
        if len(parts) == 4:
            line_number = int(parts[3])
        return AddCodeCommand(file_path, code_snippet, line_number, CommandTypes.ADD)


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
            else:
                return Result.err(f"Unknown command type: {command_type}")
        except Exception as e:
            return Result.err(str(e))