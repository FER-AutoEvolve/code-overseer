from dataclasses import dataclass
from enum import Enum
import logging
from core import Result, Unit

class CodeOverseer():
    def __init__(self, config: dict, logger: logging.Logger = None) -> None:
        self.config = config
        self.logger = logger

    def handle_code_change(self, change_strategic_description: str) -> Result[Unit]:
        '''Handles a code change request'''
        self.logger.info(f"Handling code change: {change_strategic_description}")
        return Result.ok(Unit())
