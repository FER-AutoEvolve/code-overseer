from dataclasses import dataclass
from enum import Enum

from core import Result

__DEFAULT_FASTAPI_PORT__ = 8000
__DEFAULT_FASTAPI_HOST__ = "0.0.0.0"
__DEFAULT_CODE_DIRECTORY__ = "./codebase"

class LlmProviders(Enum):
    OPENAI = "openai"

@dataclass(frozen=True)
class Configuration:
    llm_provider: LlmProviders
    llm_service_settings: dict
    managed_code_directory: str
    fast_api_configuration: 'FastApiConfiguration'

    @staticmethod
    def from_dict(config: dict) -> Result['Configuration']:
        try:
            llm_provider = LlmProviders(config.get("LlmProvider", "openai").lower())
            llm_settings = config.get("LlmSettings", {})
            managed_code_directory = config.get("ManagedCodeDirectory", __DEFAULT_CODE_DIRECTORY__)
            fast_api_config = FastApiConfiguration.from_dict(config.get("FastAPI", {}))

            if fast_api_config.is_err():
                return Result.err(fast_api_config.message)

            return Result.ok(Configuration(
                llm_provider=llm_provider,
                llm_service_settings=llm_settings,
                managed_code_directory=managed_code_directory,
                fast_api_configuration=fast_api_config.value
            ))
        except ValueError as e:
            return Result.err(f"Invalid configuration: {e}")
        
@dataclass(frozen=True)
class FastApiConfiguration:
    port: int
    host: str

    @staticmethod
    def from_dict(settings: dict) -> Result['FastApiConfiguration']:
        try:
            return Result.ok(FastApiConfiguration(
                port=settings.get("Port", __DEFAULT_FASTAPI_PORT__),
                host=settings.get("Host", __DEFAULT_FASTAPI_HOST__)
            ))
        except ValueError as e:
            return Result.err(f"Invalid FastAPI settings: {e}")


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str
    model: str

    @staticmethod
    def from_dict(settings: dict) -> Result['OpenAISettings']:
        try:
            return Result.ok(OpenAISettings(
                api_key=settings.get("ApiKey", ""),
                model=settings.get("Model", "gpt-4")
            ))
        except ValueError as e:
            return Result.err(f"Invalid OpenAI settings: {e}")