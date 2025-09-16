import dataclasses
from enum import Enum

from api_server.configuration import FastApiConfiguration
from code_overseeing import CodeOverseerConfiguration
from core import Result
from prompting.openai.configuration import OpenAiConfiguration

class LlmProviders(Enum):
    ''' Enumeration of supported LLM providers.'''
    OPENAI = "openai"

@dataclasses.dataclass(frozen=True)
class Configuration:
    ''' Configuration for the entire application.'''
    llm_provider: LlmProviders
    llm_config: dict
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
            llm_config = config.get("Llm", {})
            llm_provider = LlmProviders(llm_config.get("Provider", "").lower())
            res_fast_api_config = FastApiConfiguration.from_dict(config.get("FastApi", {}))
            res_code_overseer_config = CodeOverseerConfiguration.from_dict(config.get("CodeOverseer", {}))
            if res_fast_api_config.is_err():
                return Result.err(res_fast_api_config.message)
            if res_code_overseer_config.is_err():
                return Result.err(res_code_overseer_config.message)
            
            return Result.ok(Configuration(
                llm_provider=llm_provider,
                llm_config=llm_config,
                code_overseer_config=res_code_overseer_config.value,
                fast_api_config=res_fast_api_config.value
            ))
        except ValueError as e:
            return Result.err(f"Invalid configuration: {e}")
        
    def get_llm_openai_config(self) -> Result[OpenAiConfiguration]:
        '''
        Retrieves the OpenAI LLM configuration if the provider is set to OpenAI.
        Returns:
            Result[OpenAiConfiguration]: Result containing the OpenAiConfiguration object or an error message.
        '''
        if self.llm_provider != LlmProviders.OPENAI:
            return Result.err(f"LLM provider {self.llm_provider} is not supported for OpenAI configuration.")
        try:
            return OpenAiConfiguration.from_dict(self.llm_config)
        except ValueError as e:
            return Result.err(f"Invalid OpenAI configuration: {e}")