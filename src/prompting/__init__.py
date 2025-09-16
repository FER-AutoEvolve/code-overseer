from abc import abstractmethod
from typing import List
from code_overseeing.code_commands import CodeCommand
from core import Result

class IGetCodeChangeCommandsPrompt:
    @abstractmethod
    def execute(self, context: dict) -> Result[List[CodeCommand]]:
        pass