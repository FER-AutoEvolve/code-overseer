import dataclasses
from enum import Enum

from api_server.configuration import FastApiConfiguration
from code_overseeing import CodeOverseerConfiguration
from core import Result

class PromptingProviders(Enum):
    ''' Enumeration of supported LLM providers.'''
    OPENAI = "openai"

class CodeCommandStrategies(Enum):
    ''' Enumeration of supported code command strategies.'''
    ADD_DELETE = "add_delete"
    UPDATE_FILE = "update_file"

@dataclasses.dataclass(frozen=True)
class PromptingConfiguration:
    ''' Configuration for the prompting system.'''
    provider: PromptingProviders
    codebase_description: str
    code_command_strategy: CodeCommandStrategies
    provider_config: dict

    @staticmethod
    def from_dict(config: dict) -> Result['PromptingConfiguration']:
        ''' 
        Creates a PromptingConfiguration object from a dictionary.
        Args:
            config (dict): Dictionary containing configuration data.
        Returns:
            Result[PromptingConfiguration]: Result containing the PromptingConfiguration object or an error message.
        '''
        try:
            provider = PromptingProviders(config.get("Provider", "").lower())
            codebase_description = config.get("CodebaseDescription", "")
            code_command_strategy = CodeCommandStrategies(config.get("CodeCommandStrategy", "").lower())
            provider_config = config.get("ProviderConfig", {})
            return Result.ok(PromptingConfiguration(
                provider=provider,
                codebase_description=codebase_description,
                code_command_strategy=code_command_strategy,
                provider_config=provider_config
            ))
        except ValueError as e:
            return Result.err(f"Invalid prompting configuration: {e}")

@dataclasses.dataclass(frozen=True)
class Configuration:
    ''' Configuration for the entire application.'''
    prompting_config: PromptingConfiguration
    fast_api_config: FastApiConfiguration
    code_overseer_config: CodeOverseerConfiguration

    @staticmethod
    def from_dict(config: dict) -> Result['Configuration']:
        ''' 
        Creates a Configuration object from a dictionary.
        Args:
            config (dict): Dictionary containing configuration data.
        Returns:
            Result[Configuration]: Result containing the Configuration object or an error message.
        '''
        try:
            res_prompting_config = PromptingConfiguration.from_dict(config.get("Prompting", {}))
            res_fast_api_config = FastApiConfiguration.from_dict(config.get("FastApi", {}))
            res_code_overseer_config = CodeOverseerConfiguration.from_dict(config.get("CodeOverseer", {}))

            if res_fast_api_config.is_err():
                return Result.err(res_fast_api_config.message)
            if res_code_overseer_config.is_err():
                return Result.err(res_code_overseer_config.message)
            
            return Result.ok(Configuration(
                prompting_config=res_prompting_config.value,
                code_overseer_config=res_code_overseer_config.value,
                fast_api_config=res_fast_api_config.value,
            ))
        except ValueError as e:
            return Result.err(f"Invalid configuration: {e}")